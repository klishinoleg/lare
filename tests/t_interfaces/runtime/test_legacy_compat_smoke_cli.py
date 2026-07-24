from __future__ import annotations

import json
from io import StringIO

from tests.t_infrastructure.runtime.test_legacy_compat_smoke import FakeCompatHttpClient


def test_legacy_compat_smoke_cli_outputs_safe_json() -> None:
    from interfaces.runtime import legacy_compat_smoke_cli

    stdout = StringIO()

    exit_code = legacy_compat_smoke_cli.run(
        [
            "--api-root",
            "https://lang-reader-server.ngrok.app/api/v1",
            "--tg-user-id",
            "935123456",
            "--seed",
            "cli-test",
            "--chapter-ready-attempts",
            "1",
        ],
        stdout=stdout,
        client_factory=lambda api_root: FakeCompatHttpClient(),
        sleep=lambda _: None,
    )
    payload = json.loads(stdout.getvalue())

    assert exit_code == 0
    assert payload["ok"] is True
    assert payload["api_root"] == "https://lang-reader-server.ngrok.app/api/v1"
    assert payload["summary"]["payment_success"] is True
    assert "secret-token" not in stdout.getvalue()


def test_legacy_compat_smoke_cli_exits_2_when_contract_fails() -> None:
    from interfaces.runtime import legacy_compat_smoke_cli

    stdout = StringIO()

    exit_code = legacy_compat_smoke_cli.run(
        ["--tg-user-id", "935123456", "--seed", "cli-test"],
        stdout=stdout,
        client_factory=lambda api_root: FakeCompatHttpClient(admin_guard_status=200),
        sleep=lambda _: None,
    )
    payload = json.loads(stdout.getvalue())

    assert exit_code == 2
    assert payload["ok"] is False
    assert "/users did not enforce admin guard" in payload["error_message"]
