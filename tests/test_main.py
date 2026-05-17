import json
import pytest
from homelab_node_red_backup import __main__ as main_mod


class TestMain:
    def test_check_command_exit_codes_returns_zero_when_data_exists(self, monkeypatch):
        monkeypatch.setattr("homelab_node_red_backup.__main__.data_exists", lambda e, j: True)
        with pytest.raises(SystemExit) as exc:
            main_mod.check.callback("http://x", None)
        assert exc.value.code == 0

    def test_check_command_exit_codes_returns_one_when_no_data(self, monkeypatch):
        monkeypatch.setattr("homelab_node_red_backup.__main__.data_exists", lambda e, j: False)
        with pytest.raises(SystemExit) as exc:
            main_mod.check.callback("http://x", None)
        assert exc.value.code == 1

    def test_backup_writes_file(self, monkeypatch, tmp_path):
        fake_backup = {"flows": []}
        monkeypatch.setattr("homelab_node_red_backup.__main__.create_backup", lambda e, j: fake_backup)

        out = tmp_path / "out.json"
        main_mod.backup.callback("http://x", str(out), None)

        with open(out, "r") as f:
            data = json.load(f)
        assert data == fake_backup

    def test_restore_reads_file_and_calls_restore(self, monkeypatch, tmp_path):
        obj = {"flows": [{"id": "n"}]}
        file = tmp_path / "in.json"
        file.write_text(json.dumps(obj))

        called = {}

        def fake_restore(endpoint, jwt, flows):
            called['args'] = (endpoint, jwt, flows)

        monkeypatch.setattr("homelab_node_red_backup.__main__.restore_backup", fake_restore)
        main_mod.restore.callback("http://x", str(file), None)
        assert called['args'][2] == obj

    def test_auto_calls_create_backup_when_data_exists(self, monkeypatch, tmp_path):
        flows = {"flows": [{"id": "n"}]}
        monkeypatch.setattr("homelab_node_red_backup.__main__.get_flows", lambda e, j: flows)
        monkeypatch.setattr("homelab_node_red_backup.__main__.data_exists", lambda e, j, f=flows: True)

        called = {}
        monkeypatch.setattr("homelab_node_red_backup.__main__.create_backup", lambda e, j, f=None: called.setdefault('created', True))

        out = tmp_path / "auto.json"
        main_mod.auto.callback("http://x", str(out), None)
        assert 'created' in called

    def test_auto_calls_restore_when_no_data(self, monkeypatch, tmp_path):
        flows = {"flows": []}
        monkeypatch.setattr("homelab_node_red_backup.__main__.get_flows", lambda e, j: flows)
        monkeypatch.setattr("homelab_node_red_backup.__main__.data_exists", lambda e, j, f=flows: False)

        obj = {"flows": [{"id": "x"}]}
        inp = tmp_path / "inp.json"
        inp.write_text(json.dumps(obj))

        called = {}

        def fake_restore(endpoint, jwt, flows_arg):
            called['restored'] = flows_arg

        monkeypatch.setattr("homelab_node_red_backup.__main__.restore_backup", fake_restore)
        main_mod.auto.callback("http://x", str(inp), None)
        assert called['restored'] == obj
