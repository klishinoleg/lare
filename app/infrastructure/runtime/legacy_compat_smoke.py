from __future__ import annotations

import json
import random
import time
import urllib.error
import urllib.request
from collections.abc import Callable, Sequence
from dataclasses import asdict, dataclass
from typing import Any, Protocol


@dataclass(frozen=True)
class HttpResponse:
    status: int
    data: Any


class JsonHttpClient(Protocol):
    def request(
        self,
        method: str,
        path: str,
        *,
        body: dict[str, Any] | None = None,
        token: str | None = None,
        allow_statuses: tuple[int, ...] = (),
    ) -> HttpResponse:
        raise NotImplementedError


@dataclass(frozen=True)
class SmokeStep:
    name: str
    ok: bool
    error_message: str | None = None


@dataclass(frozen=True)
class LegacyCompatSmokeResult:
    ok: bool
    api_root: str
    tg_user_id: int
    steps: tuple[SmokeStep, ...]
    summary: dict[str, Any]
    error_message: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "api_root": self.api_root,
            "tg_user_id": self.tg_user_id,
            "steps": [asdict(step) for step in self.steps],
            "summary": self.summary,
            "error_message": self.error_message,
        }


class UrllibJsonHttpClient:
    def __init__(
        self,
        api_root: str,
        timeout_seconds: int = 20,
        retry_attempts: int = 2,
        retry_delay_seconds: float = 0.5,
    ) -> None:
        self._api_root = api_root.rstrip("/")
        self._timeout_seconds = timeout_seconds
        self._retry_attempts = max(0, retry_attempts)
        self._retry_delay_seconds = max(0.0, retry_delay_seconds)
        self._ngrok_headers = (
            {"ngrok-skip-browser-warning": "true"}
            if "ngrok.app" in self._api_root
            else {}
        )

    def request(
        self,
        method: str,
        path: str,
        *,
        body: dict[str, Any] | None = None,
        token: str | None = None,
        allow_statuses: tuple[int, ...] = (),
    ) -> HttpResponse:
        request_body = None if body is None else json.dumps(body).encode("utf-8")
        headers = {
            **self._ngrok_headers,
            "accept": "application/json",
            "content-type": "application/json",
        }
        if token:
            headers["authorization"] = f"Token {token}"
        request = urllib.request.Request(
            f"{self._api_root}{path}",
            data=request_body,
            headers=headers,
            method=method,
        )
        for attempt in range(self._retry_attempts + 1):
            try:
                with urllib.request.urlopen(request, timeout=self._timeout_seconds) as response:
                    return HttpResponse(
                        status=int(response.status),
                        data=_parse_response_body(response.read()),
                    )
            except urllib.error.HTTPError as exc:
                data = _parse_response_body(exc.read())
                if exc.code in allow_statuses:
                    return HttpResponse(status=int(exc.code), data=data)
                raise RuntimeError(f"{method} {path} -> {exc.code}: {data}") from exc
            except urllib.error.URLError:
                if attempt >= self._retry_attempts:
                    raise
                if self._retry_delay_seconds:
                    time.sleep(self._retry_delay_seconds)
        raise RuntimeError(f"{method} {path} did not return a response")


def run_legacy_compat_smoke(
    *,
    client: JsonHttpClient,
    api_root: str,
    tg_user_id: int | None = None,
    seed: str | None = None,
    chapter_ready_attempts: int = 80,
    chapter_ready_delay_seconds: float = 1.5,
    sleep: Callable[[float], object] = time.sleep,
) -> LegacyCompatSmokeResult:
    effective_tg_user_id = tg_user_id or 935000000 + random.randint(0, 999999)
    effective_seed = seed or f"{effective_tg_user_id}_{int(time.time() * 1000)}"
    steps: list[SmokeStep] = []
    summary: dict[str, Any] = {}
    token: str | None = None

    def step(name: str, action: Callable[[], Any]) -> Any:
        try:
            value = action()
        except Exception as exc:
            steps.append(SmokeStep(name=name, ok=False, error_message=str(exc)))
            raise
        steps.append(SmokeStep(name=name, ok=True))
        return value

    try:
        start, repeated_start = step(
            "telegram_start",
            lambda: _check_telegram_start(client, effective_tg_user_id),
        )
        summary["start_account_id"] = start["account_id"]
        summary["repeated_start_is_new"] = repeated_start.get("is_new")

        auth = step(
            "telegram_auth",
            lambda: _check_telegram_auth(client, effective_tg_user_id, start),
        )
        token = auth["token"]
        summary["account_id"] = auth["account"]["id"]

        bonus, admin_statuses = step(
            "start_bonus_and_admin_guards",
            lambda: _check_bonus_and_admin_guards(client, effective_tg_user_id),
        )
        summary["bonus_credits"] = bonus.get("credits_amount")
        summary["admin_guard_statuses"] = admin_statuses

        book, chapter = step(
            "book_and_evented_chapter",
            lambda: _check_book_and_chapter(
                client,
                token,
                effective_seed,
                chapter_ready_attempts,
                chapter_ready_delay_seconds,
                sleep,
            ),
        )
        summary["book_id"] = book["id"]
        summary["chapter_id"] = chapter["id"]

        study, task, reset = step(
            "study_task_rating_reset",
            lambda: _check_study_task_rating_reset(
                client,
                token,
                effective_tg_user_id,
                chapter,
            ),
        )
        summary["study_id"] = study["id"]
        summary["rated_log_id"] = task["log_id"]
        summary["reset_count"] = reset["count"]

        bill, payment, payments = step(
            "stars_payment",
            lambda: _check_stars_payment(
                client,
                token,
                effective_tg_user_id,
                effective_seed,
            ),
        )
        summary["bill_id"] = bill["bill_id"]
        summary["payment_success"] = payment["success"]
        summary["payment_transaction_count"] = payments.get("count")

        account = step(
            "account_balance",
            lambda: client.request("GET", "/account/load/", token=token).data,
        )
        summary["account_credits"] = account.get("credits")
    except Exception as exc:
        return LegacyCompatSmokeResult(
            ok=False,
            api_root=api_root.rstrip("/"),
            tg_user_id=effective_tg_user_id,
            steps=tuple(steps),
            summary=summary,
            error_message=str(exc),
        )

    return LegacyCompatSmokeResult(
        ok=True,
        api_root=api_root.rstrip("/"),
        tg_user_id=effective_tg_user_id,
        steps=tuple(steps),
        summary=summary,
    )


def _check_telegram_start(
    client: JsonHttpClient,
    tg_user_id: int,
) -> tuple[dict[str, Any], dict[str, Any]]:
    start = client.request(
        "POST",
        "/telegram/update/",
        body=_message_update(994100000 + (tg_user_id % 100000), tg_user_id, "/start"),
    ).data
    _require(
        start.get("success") is True and start.get("handled") == "start",
        f"Unexpected /start payload: {start}",
    )
    _require(start.get("account_id"), f"/start did not return account id: {start}")
    _require(
        isinstance(start.get("keyboard"), list) and start.get("web_app_url"),
        f"/start did not return WebApp keyboard: {start}",
    )

    repeated = client.request(
        "POST",
        "/telegram/update/",
        body=_message_update(994200000 + (tg_user_id % 100000), tg_user_id, "/start"),
    ).data
    _require(
        repeated.get("handled") == "start"
        and repeated.get("account_id") == start["account_id"]
        and repeated.get("is_new") is False,
        f"Repeated /start did not reuse Telegram account: {repeated}",
    )
    return start, repeated


def _check_telegram_auth(
    client: JsonHttpClient,
    tg_user_id: int,
    start: dict[str, Any],
) -> dict[str, Any]:
    auth = client.request(
        "POST",
        "/account/telegram_auth/",
        body={"auth_data": {"user": _tg_user(tg_user_id)}},
    ).data
    _require(auth.get("token"), f"telegram_auth did not return token: {auth}")
    _require(
        auth.get("account", {}).get("id") == start["account_id"],
        f"telegram_auth account mismatch: start={start['account_id']}, auth={auth.get('account')}",
    )
    return auth


def _check_bonus_and_admin_guards(
    client: JsonHttpClient,
    tg_user_id: int,
) -> tuple[dict[str, Any], dict[str, int]]:
    bonus = client.request(
        "POST",
        "/telegram/update/",
        body=_message_update(994300000 + (tg_user_id % 100000), tg_user_id, "/start_bonus"),
    ).data
    _require(
        bonus.get("handled") == "start_bonus"
        and bonus.get("success") is True
        and bonus.get("credits_amount", 0) > 0,
        f"First /start_bonus did not grant credits: {bonus}",
    )
    repeated_bonus = client.request(
        "POST",
        "/telegram/update/",
        body=_message_update(994400000 + (tg_user_id % 100000), tg_user_id, "/start_bonus"),
    ).data
    _require(
        repeated_bonus.get("handled") == "start_bonus"
        and repeated_bonus.get("success") is False,
        f"Repeated /start_bonus did not stay idempotent: {repeated_bonus}",
    )
    users = client.request(
        "POST",
        "/telegram/update/",
        body=_message_update(994500000 + (tg_user_id % 100000), tg_user_id, "/users"),
        allow_statuses=(403,),
    )
    _require(
        users.status == 403,
        f"/users did not enforce admin guard: status={users.status}, data={users.data}",
    )
    stats = client.request(
        "POST",
        "/telegram/update/",
        body=_message_update(994600000 + (tg_user_id % 100000), tg_user_id, "/stats"),
        allow_statuses=(403,),
    )
    _require(
        stats.status == 403,
        f"/stats did not enforce admin guard: status={stats.status}, data={stats.data}",
    )
    return bonus, {"users": users.status, "stats": stats.status}


def _check_book_and_chapter(
    client: JsonHttpClient,
    token: str,
    seed: str,
    chapter_ready_attempts: int,
    chapter_ready_delay_seconds: float,
    sleep: Callable[[float], object],
) -> tuple[dict[str, Any], dict[str, Any]]:
    languages = client.request("GET", "/language/", token=token).data
    language = _first_item(languages)
    _require(language and language.get("id"), f"No language available: {languages}")
    book = client.request(
        "POST",
        "/book/",
        token=token,
        body={
            "name": f"Legacy compat smoke {seed}",
            "language": language["id"],
            "description": "Compatibility smoke",
        },
    ).data
    _require(book.get("id"), f"Book create failed: {book}")

    chapter_created = client.request(
        "POST",
        f"/book/{book['id']}/add_chapter/",
        token=token,
        body={
            "name": "Legacy compat smoke chapter",
            "text": (
                "receiver task rating reset payment words are parsed by async "
                "workers for public telegram smoke"
            ),
        },
    ).data
    chapter_id = _first_item(chapter_created.get("chapters") or {}).get("id")
    _require(chapter_id, f"Chapter create failed: {chapter_created}")
    chapter = _wait_for_ready_chapter(
        client,
        token,
        int(chapter_id),
        chapter_ready_attempts,
        chapter_ready_delay_seconds,
        sleep,
    )
    return book, chapter


def _check_study_task_rating_reset(
    client: JsonHttpClient,
    token: str,
    tg_user_id: int,
    chapter: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    task_word = next(
        (
            item
            for item in chapter.get("content", [])
            if item.get("name") == "task" and item.get("w")
        ),
        None,
    ) or next((item for item in chapter.get("content", []) if item.get("w")), None)
    _require(task_word and task_word.get("w"), f"Ready chapter has no word token: {chapter}")

    study = client.request(
        "POST",
        "/study_phrase/",
        token=token,
        body={
            "chapter_id": chapter["id"],
            "word_id": task_word["w"],
            "is_active": True,
        },
    ).data
    _require(study.get("id"), f"Study phrase create failed: {study}")

    task = client.request(
        "POST",
        "/telegram/update/",
        body=_message_update(994700000 + (tg_user_id % 100000), tg_user_id, "/task"),
    ).data
    _require(
        task.get("success") is True
        and task.get("handled") == "study_task_created"
        and task.get("study_phrase_id") == study["id"]
        and task.get("log_id"),
        f"Telegram /task did not create study task: {task}",
    )
    keyboard = task.get("keyboard") or []
    _require(
        keyboard
        and any(
            item.get("callback_data") == f"study_phrase_{task['log_id']}_4"
            for row in keyboard
            for item in row
        ),
        f"Study task keyboard does not expose rating callbacks: {keyboard}",
    )

    rating = client.request(
        "POST",
        "/telegram/update/",
        body=_callback_update(
            994800000 + (tg_user_id % 100000),
            tg_user_id,
            f"study_phrase_{task['log_id']}_4",
        ),
    ).data
    _require(
        rating.get("success") is True
        and rating.get("handled") == "study_phrase_rating"
        and rating.get("rank") == 4,
        f"Study rating callback failed: {rating}",
    )
    study_after_rating = client.request(
        "GET",
        f"/study_phrase/{study['id']}/",
        token=token,
    ).data
    _require(
        study_after_rating.get("success_logs", 0) >= 1
        and float(study_after_rating.get("average", 0)) >= 4,
        f"Study phrase did not persist rating: {study_after_rating}",
    )

    action_task = client.request(
        "POST",
        "/telegram/update/",
        body=_callback_update(994900000 + (tg_user_id % 100000), tg_user_id, "action_1"),
    ).data
    _require(
        action_task.get("success") is True
        and action_task.get("handled") == "study_task_created"
        and action_task.get("log_id"),
        f"Telegram action_1 did not create study task: {action_task}",
    )
    reset = client.request(
        "POST",
        "/telegram/update/",
        body=_message_update(995000000 + (tg_user_id % 100000), tg_user_id, "/reset_tasks"),
    ).data
    _require(
        reset.get("success") is True
        and reset.get("handled") == "study_tasks_reset"
        and reset.get("count", 0) >= 1,
        f"Telegram /reset_tasks did not remove pending task: {reset}",
    )
    delete_action = client.request(
        "POST",
        "/telegram/update/",
        body=_callback_update(995100000 + (tg_user_id % 100000), tg_user_id, "action_4"),
    ).data
    _require(
        delete_action.get("handled") == "study_task_deleted",
        f"Telegram action_4 failed: {delete_action}",
    )
    return study, task, reset


def _check_stars_payment(
    client: JsonHttpClient,
    token: str,
    tg_user_id: int,
    seed: str,
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    bill = client.request(
        "POST",
        "/transaction/send_tg_payment/",
        token=token,
        body={"cost": 17},
    ).data
    _require(
        bill.get("success") is True
        and bill.get("bill_id")
        and bill.get("invoice_payload") == str(bill["bill_id"]),
        f"Bill create failed: {bill}",
    )
    pre_checkout = client.request(
        "POST",
        "/telegram/update/",
        body={
            "update_id": 995200000 + (tg_user_id % 100000),
            "pre_checkout_query": {
                "id": f"compat-precheckout-{seed}",
                "from": _tg_user(tg_user_id),
                "currency": "XTR",
                "total_amount": 17,
                "invoice_payload": str(bill["bill_id"]),
            },
        },
    ).data
    _require(
        pre_checkout.get("handled") == "pre_checkout"
        and pre_checkout.get("bill_id") == bill["bill_id"],
        f"Pre-checkout handler failed: {pre_checkout}",
    )
    payment = client.request(
        "POST",
        "/telegram/update/",
        body=_message_update(
            995300000 + (tg_user_id % 100000),
            tg_user_id,
            None,
            {
                "successful_payment": {
                    "currency": "XTR",
                    "total_amount": 17,
                    "invoice_payload": str(bill["bill_id"]),
                    "telegram_payment_charge_id": f"compat-charge-{seed}",
                    "provider_payment_charge_id": f"compat-provider-{seed}",
                },
            },
        ),
    ).data
    _require(
        payment.get("success") is True
        and payment.get("handled") == "successful_payment"
        and payment.get("bill_id") == bill["bill_id"],
        f"Successful payment handler failed: {payment}",
    )

    payments = client.request(
        "GET",
        "/transaction/?transaction_type=payment",
        token=token,
    ).data
    payment_items = payments.get("results") or []
    _require(
        any(
            item.get("bill_id") == bill["bill_id"]
            or item.get("payment_data", {}).get("invoice_payload") == str(bill["bill_id"])
            for item in payment_items
        ),
        f"Payment transaction list misses bill {bill['bill_id']}: {payments}",
    )
    return bill, payment, payments


def _wait_for_ready_chapter(
    client: JsonHttpClient,
    token: str,
    chapter_id: int,
    attempts: int,
    delay_seconds: float,
    sleep: Callable[[float], object],
) -> dict[str, Any]:
    latest: dict[str, Any] | None = None
    for attempt in range(attempts):
        latest = client.request("GET", f"/chapter/{chapter_id}/", token=token).data
        if (
            latest.get("is_ready") is True
            and isinstance(latest.get("content"), list)
            and len(latest["content"]) >= 6
        ):
            return latest
        if attempt + 1 < attempts:
            sleep(delay_seconds)
    raise RuntimeError(f"Chapter {chapter_id} was not ready: {latest}")


def _message_update(
    update_id: int,
    tg_user_id: int,
    text: str | None,
    extra_message: dict[str, Any] | None = None,
) -> dict[str, Any]:
    message = {
        "message_id": update_id % 100000,
        "date": 1,
        "chat": {"id": tg_user_id, "type": "private"},
        "from": _tg_user(tg_user_id),
        **({"text": text} if text else {}),
        **(extra_message or {}),
    }
    return {"update_id": update_id, "message": message}


def _callback_update(update_id: int, tg_user_id: int, data: str) -> dict[str, Any]:
    return {
        "update_id": update_id,
        "callback_query": {
            "id": f"compat-callback-{tg_user_id}-{update_id}",
            "from": _tg_user(tg_user_id),
            "message": {
                "message_id": update_id % 100000,
                "date": 1,
                "chat": {"id": tg_user_id, "type": "private"},
            },
            "data": data,
        },
    }


def _tg_user(tg_user_id: int) -> dict[str, Any]:
    return {
        "id": tg_user_id,
        "is_bot": False,
        "first_name": "Compat",
        "last_name": "Smoke",
        "username": f"compat_{tg_user_id}",
        "language_code": "en",
    }


def _first_item(value: Any) -> dict[str, Any]:
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        return value[0] if value else {}
    if isinstance(value, dict):
        results = value.get("results")
        if isinstance(results, list) and results:
            return results[0]
    return {}


def _parse_response_body(body: bytes) -> Any:
    if not body:
        return None
    text = body.decode("utf-8")
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return text


def _require(value: bool, message: str) -> None:
    if not value:
        raise RuntimeError(message)
