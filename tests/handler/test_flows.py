import json
import pytest
import click
from requests.exceptions import RequestException
from homelab_node_red_backup.handler import flows


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


class TestFlows:
    """Tests for homelab_node_red_backup.handler.flows.get_flows."""

    def test_get_flows_list_response(self, monkeypatch):
        """get_flows returns a dict with a 'flows' list when endpoint returns a list."""
        def fake_get(url, headers=None):
            return _Response(ok=True, payload=[{"id": "1"}])

        monkeypatch.setattr("requests.get", fake_get)
        result = flows.get_flows("http://example", None)
        assert isinstance(result, dict)
        assert "flows" in result
        assert isinstance(result["flows"], list)
        assert result["flows"][0]["id"] == "1"

    def test_get_flows_dict_response(self, monkeypatch):
        """get_flows accepts dict payload with 'flows' key and returns it unchanged."""
        def fake_get(url, headers=None):
            return _Response(ok=True, payload={"flows": [{"id": "x"}]})

        monkeypatch.setattr("requests.get", fake_get)
        result = flows.get_flows("http://example", None)
        assert result["flows"][0]["id"] == "x"

    def test_get_flows_bad_json_raises(self, monkeypatch):
        """get_flows aborts when the response body is invalid JSON."""
        def fake_get(url, headers=None):
            return _Response(ok=True, json_exc=json.JSONDecodeError("msg", "doc", 0))

        monkeypatch.setattr("requests.get", fake_get)
        with pytest.raises(click.Abort):
            flows.get_flows("http://example", None)

    def test_get_flows_non_ok_raises(self, monkeypatch):
        """get_flows aborts when HTTP response is not OK."""
        def fake_get(url, headers=None):
            return _Response(ok=False, status_code=404, text="not found")

        monkeypatch.setattr("requests.get", fake_get)
        with pytest.raises(click.Abort):
            flows.get_flows("http://example", None)

    def test_get_flows_request_exception_raises(self, monkeypatch):
        """get_flows aborts when requests.get raises a RequestException."""
        def fake_get(url, headers=None):
            raise RequestException("network")

        monkeypatch.setattr("requests.get", fake_get)
        with pytest.raises(click.Abort):
            flows.get_flows("http://example", None)

    def test_get_flows_with_jwt_header_set(self, monkeypatch):
        """get_flows includes Authorization header when jwt is provided."""
        def fake_get(url, headers=None):
            assert headers is not None and headers.get("Authorization") == "Bearer t"
            return _Response(ok=True, payload=[{"id": "1"}])

        monkeypatch.setattr("requests.get", fake_get)
        res = flows.get_flows("http://example", "t")
        assert res["flows"][0]["id"] == "1"

    def test_unexpected_flows_format_raises(self, monkeypatch):
        """get_flows aborts when payload is a dict but doesn't contain a list under 'flows'."""
        def fake_get(url, headers=None):
            return _Response(ok=True, payload={"notflows": 123})

        monkeypatch.setattr("requests.get", fake_get)
        with pytest.raises(click.Abort):
            flows.get_flows("http://example", None)