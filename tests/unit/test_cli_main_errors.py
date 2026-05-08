import pytest

from checkvsphere import CheckVsphereTimeout, VsphereConnectException
from checkvsphere import cli


def test_main_maps_timeout_to_unknown(monkeypatch, capsys):
    def raise_timeout():
        raise CheckVsphereTimeout("Timeout reached")

    monkeypatch.setattr(cli, "run", raise_timeout)

    with pytest.raises(SystemExit) as exc:
        cli.main()

    assert exc.value.code == 3
    assert "UNKNOWN - Timeout reached" in capsys.readouterr().out


def test_main_maps_connection_refused_to_critical(monkeypatch, capsys):
    def raise_connection_refused():
        raise ConnectionRefusedError("refused")

    monkeypatch.setattr(cli, "run", raise_connection_refused)

    with pytest.raises(SystemExit) as exc:
        cli.main()

    assert exc.value.code == 2
    assert "CRITICAL - Connection refused" in capsys.readouterr().out


def test_main_maps_connect_exception_to_ok(monkeypatch, capsys):
    def raise_connect_exception():
        raise VsphereConnectException("cannot connect")

    monkeypatch.setattr(cli, "run", raise_connect_exception)

    with pytest.raises(SystemExit) as exc:
        cli.main()

    assert exc.value.code == 0
    assert "Cannot connect -" in capsys.readouterr().out
