from __future__ import annotations

from collections.abc import Callable
from dataclasses import asdict, dataclass
from typing import Any, Protocol

import httpx


class TelegramBotApi(Protocol):
    async def get_me(self) -> dict[str, Any]:
        ...

    async def get_webhook_info(self) -> dict[str, Any]:
        ...

    async def set_webhook(
        self,
        *,
        url: str,
        drop_pending_updates: bool,
    ) -> dict[str, Any]:
        ...


@dataclass(frozen=True)
class TelegramReceiverPreflightConfig:
    token: str
    desired_webhook_url: str
    bot_api_base_url: str = "https://api.telegram.org"


@dataclass(frozen=True)
class TelegramReceiverPreflightResult:
    ok: bool
    token_present: bool
    desired_webhook_url: str
    current_webhook_url: str | None
    receiver_ready: bool
    bot_id: int | None
    bot_username: str | None
    pending_update_count: int | None
    last_error_message_present: bool
    issues: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


ApiFactory = Callable[[str], TelegramBotApi]


class HttpxTelegramBotApi:
    def __init__(
        self,
        *,
        token: str,
        base_url: str = "https://api.telegram.org",
        http_client: httpx.AsyncClient | None = None,
    ) -> None:
        self._token = token
        self._base_url = base_url.rstrip("/")
        self._http_client = http_client

    async def get_me(self) -> dict[str, Any]:
        return await self._get("getMe")

    async def get_webhook_info(self) -> dict[str, Any]:
        return await self._get("getWebhookInfo")

    async def set_webhook(
        self,
        *,
        url: str,
        drop_pending_updates: bool,
    ) -> dict[str, Any]:
        return await self._post(
            "setWebhook",
            json={
                "url": url,
                "drop_pending_updates": drop_pending_updates,
            },
        )

    async def _get(self, method: str) -> dict[str, Any]:
        url = f"{self._base_url}/bot{self._token}/{method}"
        if self._http_client is not None:
            response = await self._http_client.get(url)
        else:
            async with httpx.AsyncClient(timeout=20) as client:
                response = await client.get(url)
        response.raise_for_status()
        data = response.json()
        return data if isinstance(data, dict) else {"ok": False}

    async def _post(self, method: str, *, json: dict[str, Any]) -> dict[str, Any]:
        url = f"{self._base_url}/bot{self._token}/{method}"
        if self._http_client is not None:
            response = await self._http_client.post(url, json=json)
        else:
            async with httpx.AsyncClient(timeout=20) as client:
                response = await client.post(url, json=json)
        response.raise_for_status()
        data = response.json()
        return data if isinstance(data, dict) else {"ok": False}


async def run_telegram_receiver_preflight(
    config: TelegramReceiverPreflightConfig,
    *,
    api_factory: ApiFactory | None = None,
) -> TelegramReceiverPreflightResult:
    token = config.token.strip()
    desired_url = _normalize_webhook_url(config.desired_webhook_url)
    if not token:
        return TelegramReceiverPreflightResult(
            ok=False,
            token_present=False,
            desired_webhook_url=desired_url,
            current_webhook_url=None,
            receiver_ready=False,
            bot_id=None,
            bot_username=None,
            pending_update_count=None,
            last_error_message_present=False,
            issues=("token_missing",),
        )

    factory = api_factory or (
        lambda value: HttpxTelegramBotApi(
            token=value,
            base_url=config.bot_api_base_url,
        )
    )
    api = factory(token)
    issues: list[str] = []

    try:
        me = await api.get_me()
    except Exception:  # noqa: BLE001
        return _api_failure(desired_url=desired_url, issue="get_me_failed")

    try:
        webhook = await api.get_webhook_info()
    except Exception:  # noqa: BLE001
        return _api_failure(desired_url=desired_url, issue="get_webhook_info_failed")

    me_result = me.get("result") if isinstance(me.get("result"), dict) else {}
    webhook_result = webhook.get("result") if isinstance(webhook.get("result"), dict) else {}
    current_url = _normalize_webhook_url(str(webhook_result.get("url") or ""))
    receiver_ready = bool(current_url and current_url == desired_url)
    if not receiver_ready:
        issues.append("webhook_mismatch")

    pending_update_count = _safe_int(webhook_result.get("pending_update_count"))
    last_error_message = str(webhook_result.get("last_error_message") or "").strip()
    if last_error_message:
        issues.append("webhook_last_error_present")

    return TelegramReceiverPreflightResult(
        ok=not issues,
        token_present=True,
        desired_webhook_url=desired_url,
        current_webhook_url=current_url or None,
        receiver_ready=receiver_ready,
        bot_id=_safe_int(me_result.get("id")),
        bot_username=str(me_result.get("username") or "") or None,
        pending_update_count=pending_update_count,
        last_error_message_present=bool(last_error_message),
        issues=tuple(issues),
    )


def _api_failure(*, desired_url: str, issue: str) -> TelegramReceiverPreflightResult:
    return TelegramReceiverPreflightResult(
        ok=False,
        token_present=True,
        desired_webhook_url=desired_url,
        current_webhook_url=None,
        receiver_ready=False,
        bot_id=None,
        bot_username=None,
        pending_update_count=None,
        last_error_message_present=False,
        issues=(issue,),
    )


def _normalize_webhook_url(value: str) -> str:
    clean = value.strip()
    if not clean:
        return ""
    return f"{clean.rstrip('/')}/"


def _safe_int(value: object) -> int | None:
    try:
        return int(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return None
