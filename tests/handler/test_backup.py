import importlib
import json
import click
import pytest
from requests.exceptions import RequestException
from homelab_node_red_backup.handler import backup


class _Response:
    def __init__(self, ok=True, status_code=200, text="", payload=None, json_exc=None):
        self.ok = ok
        self.status_code = status_code
        self.text = text
        self._payload = payload
        self._json_exc = json_exc

    def json(self):
        if self._json_exc:
            raise self._json_exc
        return self._payload


class TestBackup:
    """Tests for homelab_node_red_backup.handler.backup.create_backup."""

    def test_fetches_credentials_and_respects_env(self, monkeypatch):
        """create_backup fetches credentials for node types from CREDENTIAL_NODES."""
        monkeypatch.setenv("CREDENTIAL_NODES", "my-type")
        importlib.reload(backup)

        flows = {"flows": [{"id": "n1", "type": "my-type"}]}

        def fake_get(url, headers=None):
            assert "credentials" in url
            return _Response(ok=True, payload={"secret": "s"})

        monkeypatch.setattr("requests.get", fake_get)
        res = backup.create_backup("http://example", None, flows)
        assert "credentials" in res
        assert res["credentials"]["n1"]["secret"] == "s"

    def test_get_credentials_non_ok_raises(self, monkeypatch):
        """create_backup aborts when credential endpoint returns non-OK."""
        monkeypatch.setenv("CREDENTIAL_NODES", "t1")
        importlib.reload(backup)

        flows = {"flows": [{"id": "n2", "type": "t1"}]}

        def fake_get(url, headers=None):
            return _Response(ok=False, status_code=500, text="error")

        monkeypatch.setattr("requests.get", fake_get)
        with pytest.raises(click.Abort):
            backup.create_backup("http://example", None, flows)

    def test_uses_default_env(self, monkeypatch):
        """create_backup uses default CREDENTIAL_NODES when env var unset."""
        monkeypatch.delenv("CREDENTIAL_NODES", raising=False)
        importlib.reload(backup)

        flows = {"flows": [{"id": "s1", "type": "server"}]}

        def fake_get(url, headers=None):
            assert "credentials" in url
            return _Response(ok=True, payload={"k": "v"})

        monkeypatch.setattr("requests.get", fake_get)
        res = backup.create_backup("http://example", None, flows)
        assert res["credentials"]["s1"]["k"] == "v"

    def test_json_decode_error_raises(self, monkeypatch):
        """create_backup aborts when credential response contains invalid JSON."""
        monkeypatch.setenv("CREDENTIAL_NODES", "tjson")
        importlib.reload(backup)

        flows = {"flows": [{"id": "njson", "type": "tjson"}]}

        def fake_get(url, headers=None):
            return _Response(ok=True, json_exc=json.JSONDecodeError("msg", "doc", 0))

        monkeypatch.setattr("requests.get", fake_get)
        with pytest.raises(click.Abort):
            backup.create_backup("http://example", None, flows)

    def test_accepts_list_flows(self, monkeypatch):
        """create_backup accepts flows as a list and returns expected structure."""
        flows_list = [{"id": "l1", "type": "server"}]

        def fake_get(url, headers=None):
            assert "credentials" in url
            return _Response(ok=True, payload={"cred": "v"})

        monkeypatch.setattr("requests.get", fake_get)
        res = backup.create_backup("http://example", None, flows_list)
        assert res["flows"][0]["id"] == "l1"
        assert res["credentials"]["l1"]["cred"] == "v"

    def test_jwt_sets_auth_header(self, monkeypatch):
        """create_backup sets Authorization header when jwt provided."""
        importlib.reload(backup)

        flows = {"flows": [{"id": "s2", "type": "server"}]}

        def fake_get(url, headers=None):
            assert headers is not None and "Authorization" in headers
            assert headers["Authorization"] == "Bearer mytoken"
            return _Response(ok=True, payload={"k": "v"})

        monkeypatch.setattr("requests.get", fake_get)
        res = backup.create_backup("http://example", "mytoken", flows)
        assert res["credentials"]["s2"]["k"] == "v"

    def test_invalid_flows_format_raises(self):
        """create_backup aborts when flows format is invalid."""
        with pytest.raises(click.Abort):
            backup.create_backup("http://x", None, {"notflows": 123})

    def test_invalid_fetched_flows_type_raises(self):
        """create_backup aborts when fetched flows is not a dict or list."""
        with pytest.raises(click.Abort):
            backup.create_backup("http://x", None, "not-a-structure")

    def test_missing_id_or_type_raises(self):
        """create_backup aborts when a credential node is missing id or type."""
        # default CREDENTIAL_NODES includes "server", so a node with type 'server'
        # but no 'id' should trigger the validation in _get_credentials.
        flows = {"flows": [{"type": "server"}]}
        with pytest.raises(click.Abort):
            backup.create_backup("http://x", None, flows)

    def test_invalid_node_format_raises(self, monkeypatch):
        """create_backup aborts when a flow node is not a dict (malformed flow)."""
        flows = {"flows": ["not-a-dict"]}
        messages = []
        monkeypatch.setattr("homelab_node_red_backup.handler.backup.click.echo", lambda m: messages.append(m))
        with pytest.raises(click.Abort):
            backup.create_backup("http://x", None, flows)
        assert any("Invalid flow node format" in m for m in messages)


    def test_get_credential_nodes_parses_env(self, monkeypatch):
        """get_credential_nodes parses comma-separated env var and strips parts."""
        monkeypatch.setenv("CREDENTIAL_NODES", "a, b, ,c ")
        nodes = backup.get_credential_nodes()
        assert nodes == ["a", "b", "c"]

    def test_get_credential_nodes_default_when_unset(self, monkeypatch):
        """get_credential_nodes returns defaults when env var unset."""
        monkeypatch.delenv("CREDENTIAL_NODES", raising=False)
        nodes = backup.get_credential_nodes()
        assert nodes == ["server", "telegram bot"]

    def test_request_exception_raises(self, monkeypatch):
        """create_backup aborts when requests.get raises RequestException."""
        monkeypatch.setenv("CREDENTIAL_NODES", "server")
        importlib.reload(backup)

        flows = {"flows": [{"id": "n1", "type": "server"}]}

        def fake_get(url, headers=None):
            raise RequestException("network fail")

        monkeypatch.setattr("requests.get", fake_get)
        with pytest.raises(click.Abort):
            backup.create_backup("http://x", None, flows)

    def test_get_flows_request_exception_handled(self, monkeypatch):
        """create_backup wraps RequestException from get_flows with network error message."""
        monkeypatch.setattr(
            "homelab_node_red_backup.handler.backup.get_flows",
            lambda e, j: (_ for _ in ()).throw(RequestException("net")),
        )
        messages = []
        monkeypatch.setattr("homelab_node_red_backup.handler.backup.click.echo", lambda m: messages.append(m))
        with pytest.raises(click.Abort):
            backup.create_backup("http://x", None, None)
        assert any("Network error when accessing Node-RED" in m for m in messages)

    def test_generic_exception_is_wrapped(self, monkeypatch):
        """Non-network exceptions should be wrapped and produce a generic message."""
        monkeypatch.setattr(
            "homelab_node_red_backup.handler.backup.get_flows",
            lambda e, j: (_ for _ in ()).throw(ValueError("boom")),
        )
        messages = []
        monkeypatch.setattr("homelab_node_red_backup.handler.backup.click.echo", lambda m: messages.append(m))
        with pytest.raises(click.Abort):
            backup.create_backup("http://x", None, None)
        assert any("Could not make request to Node-RED" in m for m in messages)
    def test_abort_propagates_without_generic_message(self, monkeypatch):
        """Intentional click.Abort (invalid flows) should not be re-wrapped by generic handler."""
        messages = []
        monkeypatch.setattr("homelab_node_red_backup.handler.backup.click.echo", lambda m: messages.append(m))
        with pytest.raises(click.Abort):
            backup.create_backup("http://x", None, {"notflows": 123})
        assert not any("Could not make request to Node-RED" in m for m in messages)

