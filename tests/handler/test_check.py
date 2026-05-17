import pytest
import click
from requests.exceptions import RequestException
from homelab_node_red_backup.handler import check


class TestCheck:
    def test_data_exists_true(self, monkeypatch):
        """data_exists returns True when flows list is non-empty."""
        monkeypatch.setattr(
            "homelab_node_red_backup.handler.check.get_flows", lambda e, j: {"flows": [1]}
        )
        assert check.data_exists("http://x", None) is True

    def test_data_exists_invalid_format(self, monkeypatch):
        """data_exists raises when flows response is not a dict with 'flows'."""
        monkeypatch.setattr(
            "homelab_node_red_backup.handler.check.get_flows", lambda e, j: "bad"
        )
        with pytest.raises(click.Abort):
            check.data_exists("http://x", None)

    def test_data_exists_invalid_flows_type(self, monkeypatch):
        """data_exists raises when flows key exists but is not a list."""
        monkeypatch.setattr(
            "homelab_node_red_backup.handler.check.get_flows", lambda e, j: {"flows": "abc"}
        )
        with pytest.raises(click.Abort):
            check.data_exists("http://x", None)

    def test_data_exists_request_exception(self, monkeypatch):
        """data_exists raises on RequestException from get_flows."""
        def fake_get_flows(e, j):
            raise RequestException("net")

        monkeypatch.setattr(
            "homelab_node_red_backup.handler.check.get_flows", fake_get_flows
        )
        with pytest.raises(click.Abort):
            check.data_exists("http://x", None)

    def test_generic_exception_is_wrapped(self, monkeypatch):
        """Non-network exceptions should be wrapped with a generic abort and message."""
        messages = []
        monkeypatch.setattr("homelab_node_red_backup.handler.check.click.echo", lambda m: messages.append(m))

        def fake_get_flows(e, j):
            raise ValueError("boom")

        monkeypatch.setattr(
            "homelab_node_red_backup.handler.check.get_flows", fake_get_flows
        )
        with pytest.raises(click.Abort):
            check.data_exists("http://x", None)
        assert any("Could not make request to Node-RED" in m for m in messages)

    def test_abort_propagates_without_generic_message(self, monkeypatch):
        """Intentional click.Abort (invalid flows) should not be re-wrapped by generic handler."""
        messages = []
        monkeypatch.setattr("homelab_node_red_backup.handler.check.click.echo", lambda m: messages.append(m))

        def fake_get_flows(e, j):
            raise click.Abort()

        monkeypatch.setattr(
            "homelab_node_red_backup.handler.check.get_flows", fake_get_flows
        )

        with pytest.raises(click.Abort):
            check.data_exists("http://x", None)
        assert not any("Could not make request to Node-RED" in m for m in messages)
