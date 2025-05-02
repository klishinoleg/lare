import hmac
import hashlib
from urllib.parse import unquote

from core.config import settings
from infrastructure.auth.dtos.telegram import TelegramProviderDataDTO


def validate_telegram_init_data(provider_data: TelegramProviderDataDTO) -> bool:
    """Validate Telegram WebApp init data."""
    init_data = provider_data.init_data
    vals = {k: unquote(v) for k, v in [s.split("=", 1) for s in init_data.split("&")]}
    data_check_string = "\n".join(f"{k}={v}" for k, v in sorted(vals.items()) if k != "hash")

    secret_key = hmac.new("WebAppData".encode(), settings.tg_bot_token.encode(), hashlib.sha256).digest()
    h = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256)
    return h.hexdigest() == vals["hash"]
