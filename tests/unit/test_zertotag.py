import types

import pytest
from monplugin import Status

from checkvsphere.vcmd import zertotag


class DummyParser:
    def __init__(self, args):
        self.args = args

    def add_optional_arguments(self, *args):
        pass

    def add_custom_argument(self, *args, **kwargs):
        pass

    def get_args(self):
        return self.args


class FakeResponse:
    def __init__(self, value=None, status_code=200):
        self.value = value
        self.status_code = status_code

    def json(self):
        return {'value': self.value}


class FakeSession:
    def __init__(self, responses):
        self.responses = responses
        self.headers = {}
        self.verify = None
        self.calls = []

    def get(self, url, **kwargs):
        self.calls.append(('get', url, kwargs))
        return self.responses.pop(0)

    def post(self, url, **kwargs):
        self.calls.append(('post', url, kwargs))
        return self.responses.pop(0)


def make_args(**overrides):
    defaults = {
        'host': 'vcenter.example.com',
        'port': 8443,
        'user': 'monitor@example.com',
        'password': 'secret',
        'disable_ssl_verification': False,
        'vihost': None,
        'allowed': [],
        'banned': [],
        'match_method': 'search',
        'include_powered_off': False,
    }
    defaults.update(overrides)
    return types.SimpleNamespace(**defaults)


def vm(vm_id, name, power_state='poweredOn', template=False):
    return {
        'obj': types.SimpleNamespace(obj=types.SimpleNamespace(_moId=vm_id)),
        'props': {
            'name': name,
            'runtime.powerState': power_state,
            'config.template': template,
        },
    }


def configure_run(monkeypatch, args, vms, session):
    monkeypatch.setattr(zertotag.cli, 'Parser', lambda: DummyParser(args))
    monkeypatch.setattr(
        zertotag.service_instance,
        'connect',
        lambda _args: types.SimpleNamespace(content=types.SimpleNamespace(rootFolder=object())),
    )
    monkeypatch.setattr(zertotag, 'find_entity_views', lambda *args, **kwargs: vms)
    monkeypatch.setattr(zertotag.requests, 'Session', lambda: session)


def successful_responses(protected_objects, category_name=zertotag.ZERTOTAG_CATEGORY):
    return [
        FakeResponse('session-token'),
        FakeResponse(['similar-category', 'zerto-category']),
        FakeResponse({'name': 'Zerto - Other'}),
        FakeResponse({'name': category_name}),
        FakeResponse(['tag-1', 'tag-2']),
        FakeResponse([
            {'tag_id': 'tag-1', 'object_ids': protected_objects},
            {'tag_id': 'tag-2', 'object_ids': []},
        ]),
    ]


def test_zertotag_uses_exact_category_and_bulk_associations(monkeypatch, capsys):
    args = make_args(banned=['^ignored$'])
    session = FakeSession(successful_responses([
        {'type': 'VirtualMachine', 'id': 'vm-protected'},
        {'type': 'HostSystem', 'id': 'host-1'},
    ]))
    configure_run(
        monkeypatch,
        args,
        [
            vm('vm-protected', 'protected'),
            vm('vm-missing', 'missing'),
            vm('vm-off', 'powered-off', power_state='poweredOff'),
            vm('vm-template', 'template', template=True),
            vm('vm-ignored', 'ignored'),
        ],
        session,
    )

    with pytest.raises(SystemExit) as exc:
        zertotag.run()

    assert exc.value.code == Status.CRITICAL.value
    output = capsys.readouterr().out
    assert 'missing is missing Zerto tag' in output
    assert "'vms'=2.0" in output
    assert "'tagged_vms'=1.0" in output
    assert "'missing_vms'=1.0" in output
    assert "'offline_vms'=1.0" in output
    assert "'ignored_vms'=1.0" in output
    assert "'template_vms'=1.0" in output
    assert "'discovered_vms'=5.0" in output
    assert "'rest_api_calls'=6.0" in output
    assert 'powered-off' not in output
    assert session.verify is True
    assert all(':8443/' in call[1] for call in session.calls)
    assert session.calls[-1][2]['json'] == {'tag_ids': ['tag-1', 'tag-2']}
    assert all('timeout' not in call[2] for call in session.calls)


def test_zertotag_can_include_powered_off_vms(monkeypatch, capsys):
    args = make_args(include_powered_off=True)
    session = FakeSession(successful_responses([]))
    configure_run(
        monkeypatch,
        args,
        [vm('vm-off', 'powered-off', power_state='poweredOff')],
        session,
    )

    with pytest.raises(SystemExit) as exc:
        zertotag.run()

    assert exc.value.code == Status.CRITICAL.value
    assert 'powered-off is missing Zerto tag' in capsys.readouterr().out


def test_zertotag_accepts_en_dash_category_name(monkeypatch, capsys):
    args = make_args()
    session = FakeSession(successful_responses(
        [{'type': 'VirtualMachine', 'id': 'vm-protected'}],
        'Zerto \u2013 Protection Automation',
    ))
    configure_run(monkeypatch, args, [vm('vm-protected', 'protected')], session)

    with pytest.raises(SystemExit) as exc:
        zertotag.run()

    assert exc.value.code == Status.OK.value
    assert 'no VMs missing Zerto tags' in capsys.readouterr().out


def test_zertotag_reports_tagging_api_errors_as_unknown(monkeypatch, capsys):
    args = make_args(disable_ssl_verification=True)
    session = FakeSession([
        FakeResponse('session-token'),
        FakeResponse(status_code=403),
    ])
    configure_run(monkeypatch, args, [vm('vm-missing', 'missing')], session)

    with pytest.raises(SystemExit) as exc:
        zertotag.run()

    assert exc.value.code == Status.UNKNOWN.value
    output = capsys.readouterr().out
    assert 'Unable to query vCenter tagging API' in output
    assert 'missing Zerto tag' not in output
    assert session.verify is False


def test_zertotag_reports_missing_required_category_as_critical(monkeypatch, capsys):
    args = make_args()
    session = FakeSession([
        FakeResponse('session-token'),
        FakeResponse(['other-category']),
        FakeResponse({'name': 'Zerto - Other'}),
    ])
    configure_run(monkeypatch, args, [vm('vm-missing', 'missing')], session)

    with pytest.raises(SystemExit) as exc:
        zertotag.run()

    assert exc.value.code == Status.CRITICAL.value
    assert zertotag.ZERTOTAG_CATEGORY in capsys.readouterr().out


def test_zertotag_uses_configured_ca_bundle(monkeypatch):
    monkeypatch.setenv('SSL_CA_FILE', '/etc/ssl/vcenter-ca.pem')
    monkeypatch.setenv('SSL_CA_PATH', '/etc/ssl/certs')

    assert zertotag.get_session_verify(make_args()) == '/etc/ssl/vcenter-ca.pem'
