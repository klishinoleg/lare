from __future__ import annotations

import urllib.error
from typing import Any

from infrastructure.runtime.legacy_compat_smoke import (
    HttpResponse,
    UrllibJsonHttpClient,
    run_legacy_compat_smoke,
)


class FakeCompatHttpClient:
    def __init__(self, *, admin_guard_status: int = 403) -> None:
        self.admin_guard_status = admin_guard_status
        self.calls: list[tuple[str, str, str | None]] = []
        self.bill_id = 55
        self.bonus_seen = False

    def request(
        self,
        method: str,
        path: str,
        *,
        body: dict[str, Any] | None = None,
        token: str | None = None,
        allow_statuses: tuple[int, ...] = (),
    ) -> HttpResponse:
        self.calls.append((method, path, token))
        if method == "POST" and path == "/telegram/update/":
            return self._telegram_response(body or {})
        if method == "POST" and path == "/account/telegram_auth/":
            return HttpResponse(
                status=200,
                data={"token": "secret-token", "account": {"id": 101}},
            )
        if method == "GET" and path == "/language/":
            return HttpResponse(status=200, data=[{"id": 1, "name": "English"}])
        if method == "POST" and path == "/book/":
            return HttpResponse(status=200, data={"id": 202})
        if method == "POST" and path == "/book/202/add_chapter/":
            return HttpResponse(status=200, data={"chapters": [{"id": 303}]})
        if method == "GET" and path == "/chapter/303/":
            return HttpResponse(
                status=200,
                data={
                    "id": 303,
                    "is_ready": True,
                    "content": [
                        {"name": "receiver"},
                        {"name": "task", "w": 404},
                        {"name": "rating"},
                        {"name": "reset"},
                        {"name": "payment"},
                        {"name": "words"},
                        {"name": "parsed"},
                        {"name": "async"},
                    ],
                },
            )
        if method == "POST" and path == "/study_phrase/":
            return HttpResponse(status=200, data={"id": 505})
        if method == "GET" and path == "/study_phrase/505/":
            return HttpResponse(
                status=200,
                data={"id": 505, "success_logs": 1, "average": 4.0},
            )
        if method == "POST" and path == "/transaction/send_tg_payment/":
            return HttpResponse(
                status=200,
                data={
                    "success": True,
                    "bill_id": self.bill_id,
                    "invoice_payload": str(self.bill_id),
                },
            )
        if method == "GET" and path == "/transaction/?transaction_type=payment":
            return HttpResponse(
                status=200,
                data={
                    "count": 1,
                    "results": [{"id": 1, "bill_id": self.bill_id}],
                },
            )
        if method == "GET" and path == "/account/load/":
            return HttpResponse(status=200, data={"id": 101, "credits": 117})
        raise AssertionError(f"Unexpected request: {method} {path}")

    def _telegram_response(self, body: dict[str, Any]) -> HttpResponse:
        message = body.get("message") or {}
        callback_query = body.get("callback_query") or {}
        pre_checkout = body.get("pre_checkout_query")
        text = message.get("text")
        callback_data = callback_query.get("data")

        if text == "/start":
            return HttpResponse(
                status=200,
                data={
                    "success": True,
                    "handled": "start",
                    "account_id": 101,
                    "is_new": False,
                    "keyboard": [[{"text": "Open WebApp"}]],
                    "web_app_url": "https://lang-reader.ngrok.app/",
                },
            )
        if text == "/start_bonus":
            already_bonus = self.bonus_seen
            self.bonus_seen = True
            return HttpResponse(
                status=200,
                data={
                    "success": not already_bonus,
                    "handled": "start_bonus",
                    "credits_amount": 100,
                },
            )
        if text in {"/users", "/stats"}:
            return HttpResponse(status=self.admin_guard_status, data={"detail": "guard"})
        if text == "/task" or callback_data == "action_1":
            return HttpResponse(
                status=200,
                data={
                    "success": True,
                    "handled": "study_task_created",
                    "study_phrase_id": 505,
                    "log_id": 606,
                    "keyboard": [[{"callback_data": "study_phrase_606_4"}]],
                },
            )
        if callback_data == "study_phrase_606_4":
            return HttpResponse(
                status=200,
                data={"success": True, "handled": "study_phrase_rating", "rank": 4},
            )
        if text == "/reset_tasks":
            return HttpResponse(
                status=200,
                data={"success": True, "handled": "study_tasks_reset", "count": 1},
            )
        if callback_data == "action_4":
            return HttpResponse(
                status=200,
                data={"success": True, "handled": "study_task_deleted"},
            )
        if pre_checkout:
            return HttpResponse(
                status=200,
                data={"success": True, "handled": "pre_checkout", "bill_id": self.bill_id},
            )
        if message.get("successful_payment"):
            return HttpResponse(
                status=200,
                data={
                    "success": True,
                    "handled": "successful_payment",
                    "bill_id": self.bill_id,
                },
            )
        raise AssertionError(f"Unexpected Telegram update: {body}")


def test_legacy_compat_smoke_runs_frontend_critical_contract() -> None:
    client = FakeCompatHttpClient()

    result = run_legacy_compat_smoke(
        client=client,
        api_root="https://lang-reader-server.ngrok.app/api/v1",
        tg_user_id=935123456,
        seed="test-seed",
        chapter_ready_attempts=1,
        sleep=lambda _: None,
    )

    assert result.ok is True
    assert result.summary["account_id"] == 101
    assert result.summary["chapter_id"] == 303
    assert result.summary["bill_id"] == 55
    assert result.summary["payment_success"] is True
    assert ("POST", "/transaction/send_tg_payment/", "secret-token") in client.calls
    assert "secret-token" not in str(result.to_dict())


def test_legacy_compat_smoke_fails_when_admin_guard_is_not_enforced() -> None:
    result = run_legacy_compat_smoke(
        client=FakeCompatHttpClient(admin_guard_status=200),
        api_root="https://lang-reader-server.ngrok.app/api/v1",
        tg_user_id=935123456,
        seed="test-seed",
        chapter_ready_attempts=1,
        sleep=lambda _: None,
    )

    assert result.ok is False
    assert result.error_message is not None
    assert "/users did not enforce admin guard" in result.error_message
    assert result.steps[-1].name == "start_bonus_and_admin_guards"
    assert result.steps[-1].ok is False


def test_urllib_json_http_client_retries_transient_network_errors(monkeypatch) -> None:
    from infrastructure.runtime import legacy_compat_smoke

    class FakeResponse:
        status = 200

        def __enter__(self) -> FakeResponse:
            return self

        def __exit__(self, exc_type, exc, tb) -> bool:
            return False

        def read(self) -> bytes:
            return b'{"ok": true}'

    calls: list[str] = []

    def fake_urlopen(request, *, timeout: int):
        calls.append(request.full_url)
        if len(calls) == 1:
            raise urllib.error.URLError(
                TimeoutError("_ssl.c:993: The handshake operation timed out"),
            )
        assert timeout == 7
        return FakeResponse()

    monkeypatch.setattr(legacy_compat_smoke.urllib.request, "urlopen", fake_urlopen)

    client = UrllibJsonHttpClient(
        "https://lang-reader-server.ngrok.app/api/v1",
        timeout_seconds=7,
        retry_attempts=2,
        retry_delay_seconds=0,
    )

    response = client.request("GET", "/ready")

    assert response == HttpResponse(status=200, data={"ok": True})
    assert calls == [
        "https://lang-reader-server.ngrok.app/api/v1/ready",
        "https://lang-reader-server.ngrok.app/api/v1/ready",
    ]
