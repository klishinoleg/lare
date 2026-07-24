from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from infrastructure.runtime.telegram_receiver_preflight import (
    ApiFactory,
    HttpxTelegramBotApi,
    TelegramBotApi,
)


@dataclass(frozen=True)
class TelegramReceiverSwitchConfig:
    token: str
    desired_webhook_url: str
    bot_api_base_url: str = "https://api.telegram.org"
    apply: bool = False
    confirm_receiver_switch: bool = False
    drop_pending_updates: bool = False


@dataclass(frozen=True)
class TelegramReceiverSwitchResult:
    ok: bool
    token_present: bool
    apply_requested: bool
    applied: bool
    desired_webhook_url: str
    current_webhook_url: str | None
    action: str
    drop_pending_updates: bool
    issues: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


async def run_telegram_receiver_switch(
    config: TelegramReceiverSwitchConfig,
    *,
    api_factory: ApiFactory | None = None,
) -> TelegramReceiverSwitchResult:
    token = config.token.strip()
    desired_url = _normalize_webhook_url(config.desired_webhook_url)
    if not token:
        return _result(
            ok=False,
            token_present=False,
            apply_requested=config.apply,
            applied=False,
            desired_webhook_url=desired_url,
            current_webhook_url=None,
            action="none",
            drop_pending_updates=config.drop_pending_updates,
            issues=("token_missing",),
        )

    api = _make_api(
        token=token,
        bot_api_base_url=config.bot_api_base_url,
        api_factory=api_factory,
    )
    try:
        webhook_info = await api.get_webhook_info()
    except Exception:  # noqa: BLE001
        return _result(
            ok=False,
            token_present=True,
            apply_requested=config.apply,
            applied=False,
            desired_webhook_url=desired_url,
            current_webhook_url=None,
            action="set_webhook",
            drop_pending_updates=config.drop_pending_updates,
            issues=("get_webhook_info_failed",),
        )

    webhook_result = webhook_info.get("result") if isinstance(webhook_info.get("result"), dict) else {}
    current_url = _normalize_webhook_url(str(webhook_result.get("url") or ""))
    if current_url == desired_url:
        return _result(
            ok=True,
            token_present=True,
            apply_requested=config.apply,
            applied=False,
            desired_webhook_url=desired_url,
            current_webhook_url=current_url,
            action="none",
            drop_pending_updates=config.drop_pending_updates,
            issues=(),
        )

    if not config.apply:
        return _result(
            ok=False,
            token_present=True,
            apply_requested=False,
            applied=False,
            desired_webhook_url=desired_url,
            current_webhook_url=current_url or None,
            action="set_webhook",
            drop_pending_updates=config.drop_pending_updates,
            issues=("apply_required",),
        )

    if not config.confirm_receiver_switch:
        return _result(
            ok=False,
            token_present=True,
            apply_requested=True,
            applied=False,
            desired_webhook_url=desired_url,
            current_webhook_url=current_url or None,
            action="set_webhook",
            drop_pending_updates=config.drop_pending_updates,
            issues=("confirmation_required",),
        )

    try:
        response = await api.set_webhook(
            url=desired_url,
            drop_pending_updates=config.drop_pending_updates,
        )
    except Exception:  # noqa: BLE001
        return _result(
            ok=False,
            token_present=True,
            apply_requested=True,
            applied=False,
            desired_webhook_url=desired_url,
            current_webhook_url=current_url or None,
            action="set_webhook",
            drop_pending_updates=config.drop_pending_updates,
            issues=("set_webhook_failed",),
        )

    ok = bool(response.get("ok"))
    return _result(
        ok=ok,
        token_present=True,
        apply_requested=True,
        applied=ok,
        desired_webhook_url=desired_url,
        current_webhook_url=current_url or None,
        action="set_webhook",
        drop_pending_updates=config.drop_pending_updates,
        issues=() if ok else ("set_webhook_rejected",),
    )


def _make_api(
    *,
    token: str,
    bot_api_base_url: str,
    api_factory: ApiFactory | None,
) -> TelegramBotApi:
    if api_factory is not None:
        return api_factory(token)
    return HttpxTelegramBotApi(token=token, base_url=bot_api_base_url)


def _result(
    *,
    ok: bool,
    token_present: bool,
    apply_requested: bool,
    applied: bool,
    desired_webhook_url: str,
    current_webhook_url: str | None,
    action: str,
    drop_pending_updates: bool,
    issues: tuple[str, ...],
) -> TelegramReceiverSwitchResult:
    return TelegramReceiverSwitchResult(
        ok=ok,
        token_present=token_present,
        apply_requested=apply_requested,
        applied=applied,
        desired_webhook_url=desired_webhook_url,
        current_webhook_url=current_webhook_url,
        action=action,
        drop_pending_updates=drop_pending_updates,
        issues=issues,
    )


def _normalize_webhook_url(value: str) -> str:
    clean = value.strip()
    if not clean:
        return ""
    return f"{clean.rstrip('/')}/"
