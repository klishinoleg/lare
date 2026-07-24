from __future__ import annotations

import json
from io import StringIO

from tests.t_infrastructure.runtime.test_reader_actions_smoke import (
    FakeReaderActionsHttpClient,
    fake_upload_fetcher,
)


def test_reader_actions_smoke_cli_outputs_safe_json() -> None:
    from interfaces.runtime import reader_actions_smoke_cli

    stdout = StringIO()

    exit_code = reader_actions_smoke_cli.run(
        [
            "--api-root",
            "https://lang-reader-server.ngrok.app/api/v1",
            "--tg-user-id",
            "992123456",
            "--seed",
            "cli-test",
            "--chapter-ready-attempts",
            "1",
            "--check-upload-files",
        ],
        stdout=stdout,
        client_factory=lambda api_root: FakeReaderActionsHttpClient(),
        sleep=lambda _: None,
        upload_fetcher=fake_upload_fetcher,
    )
    payload = json.loads(stdout.getvalue())

    assert exit_code == 0
    assert payload["ok"] is True
    assert payload["summary"]["text_part_id"] == 40
    assert payload["summary"]["phrase_id"] == 60
    assert payload["summary"]["study_id"] == 80
    assert payload["summary"]["upload_checks"]["word"]["status"] == 200
    assert "reader-secret-token" not in stdout.getvalue()


def test_reader_actions_smoke_cli_exits_2_when_contract_fails() -> None:
    from interfaces.runtime import reader_actions_smoke_cli

    stdout = StringIO()

    exit_code = reader_actions_smoke_cli.run(
        ["--tg-user-id", "992123456", "--seed", "cli-test"],
        stdout=stdout,
        client_factory=lambda api_root: FakeReaderActionsHttpClient(
            dialog_has_assistant=False,
        ),
        sleep=lambda _: None,
    )
    payload = json.loads(stdout.getvalue())

    assert exit_code == 2
    assert payload["ok"] is False
    assert "Dialog send contract failed" in payload["error_message"]
