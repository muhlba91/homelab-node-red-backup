import click
import pytest
from requests.exceptions import RequestException
from homelab_node_red_backup.handler import restore


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


class TestRestore:
    def test_accepts_dict(self, monkeypatch):
        def fake_post(url, json=None, headers=None):
            return _Response(ok=True)

        monkeypatch.setattr("requests.post", fake_post)
        restore.restore_backup("http://example", None, {"flows": []})

    def test_invalid_json_raises(self):
        with pytest.raises(click.Abort):
            restore.restore_backup("http://example", None, "not-a-json")

    def test_parsed_json_not_object_or_array_raises(self):
        """restore_backup aborts when parsed JSON is not an object or array (e.g., a string)."""
        import json as _json
        # a valid JSON string that parses to a string, not an object/array
        with pytest.raises(click.Abort):
            restore.restore_backup("http://example", None, _json.dumps("a string"))

    def test_abort_propagates_without_generic_message(self, monkeypatch):
        """Intentional click.Abort (invalid JSON/format) should not be re-wrapped by generic handler."""
        messages = []
        monkeypatch.setattr("homelab_node_red_backup.handler.restore.click.echo", lambda m: messages.append(m))
        with pytest.raises(click.Abort):
            # invalid JSON causes an intentional abort inside restore_backup
            restore.restore_backup("http://example", None, "not-a-json")
        assert not any("Could not make request to Node-RED" in m for m in messages)

    def test_generic_exception_is_wrapped(self, monkeypatch):
        """Non-network exceptions should be wrapped with a generic abort and message."""
        messages = []
        monkeypatch.setattr("homelab_node_red_backup.handler.restore.click.echo", lambda m: messages.append(m))

        def fake_post(url, json=None, headers=None):
            raise ValueError("unexpected")

        monkeypatch.setattr("requests.post", fake_post)
        with pytest.raises(click.Abort):
            restore.restore_backup("http://example", None, {"flows": []})
        assert any("Could not make request to Node-RED" in m for m in messages)

    def test_post_non_ok_raises(self, monkeypatch):
        def fake_post(url, json=None, headers=None):
            return _Response(ok=False, status_code=500, text="err")

        monkeypatch.setattr("requests.post", fake_post)
        with pytest.raises(click.Abort):
            restore.restore_backup("http://example", None, {"flows": []})

    def test_request_exception_raises(self, monkeypatch):
        def fake_post(url, json=None, headers=None):
            raise RequestException("boom")

        monkeypatch.setattr("requests.post", fake_post)
        with pytest.raises(click.Abort):
            restore.restore_backup("http://example", None, {"flows": []})

    def test_jwt_sets_header(self, monkeypatch):
        def fake_post(url, json=None, headers=None):
            assert headers is not None and headers.get("Authorization") == "Bearer tok"
            return _Response(ok=True)

        monkeypatch.setattr("requests.post", fake_post)
        restore.restore_backup("http://example", "tok", {"flows": []})