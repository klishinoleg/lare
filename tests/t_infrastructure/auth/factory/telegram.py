from datetime import datetime, timedelta
from random import randint

import factory
from aiogram.types import User, Chat, Message
from faker import Faker
import json
import hmac
import hashlib
from urllib.parse import quote
from core.config import settings
from infrastructure.auth.dtos.telegram import TelegramWebAppInitDTO, TelegramProviderDataDTO

fake = Faker()


class WebAppUserDTOFactory(factory.Factory):
    class Meta:
        model = User

    id = factory.LazyFunction(lambda: randint(1000000, 9999999))
    first_name = factory.Faker("first_name")
    last_name = factory.Faker("last_name")
    username = factory.Faker("user_name")
    is_bot = False
    language_code = "en"
    is_premium = factory.Iterator([True, False])
    # added_to_attachment_menu = factory.Iterator([True, False])
    allows_write_to_pm = factory.Iterator([True, False])
    photo_url = factory.Faker("image_url")


class WebAppChatDTOFactory(factory.Factory):
    class Meta:
        model = Chat

    id = factory.Sequence(lambda n: 10000000 + n)
    type = factory.Iterator(["group", "supergroup", "channel"])
    title = factory.Faker("company")
    username = factory.Faker("user_name")
    photo_url = factory.Faker("image_url")


class MessageFactory(factory.Factory):
    class Meta:
        model = Message

    message_id = factory.Sequence(lambda n: 10000000 + n)
    text = ""
    chat = factory.SubFactory(WebAppChatDTOFactory),
    from_user = factory.SubFactory(WebAppUserDTOFactory)
    date = datetime.now()


def get_message_from_factory(text: str, user: User | None = None, chat: Chat | None = None) -> Message:
    return MessageFactory.build(text=text, chat=chat, from_user=user)


class TelegramWebAppInitDTOFactory(factory.Factory):
    class Meta:
        model = TelegramWebAppInitDTO

    query_id = factory.Faker("uuid4")
    user = factory.SubFactory(WebAppUserDTOFactory)
    # receiver = factory.SubFactory(WebAppUserDTOFactory)
    # chat = factory.SubFactory(WebAppChatDTOFactory)
    # chat_type = factory.Iterator(["private"])
    # chat_instance = factory.Faker("uuid4")
    # start_param = "startabc"
    # can_send_after = factory.LazyFunction(lambda: fake.random_int(min=1, max=30))
    auth_date = factory.LazyFunction(
        lambda: str(int(fake.date_time_between(start_date=datetime.now() - timedelta(days=30)).timestamp())))
    hash = "testhash"
    signature = "testsignature"


def create_fake_telegram_provider_data(user_id: int | None = None) -> TelegramProviderDataDTO:
    """
    Generates a query string and HMAC hash for Telegram WebApp login flow,
    from a structured DTO. Returns full init_data and raw object.
    """
    kwargs = {}
    if user_id is not None:
        kwargs['user__id'] = user_id
    init_data_unsafe: TelegramWebAppInitDTO = TelegramWebAppInitDTOFactory(**kwargs)
    raw_data = {
        k: v for k, v in init_data_unsafe.model_dump(exclude_none=True, exclude={"hash", "signature"}).items()
    }

    # Serialize nested objects
    for key in ["user", "receiver", "chat"]:
        if key in raw_data and isinstance(raw_data[key], dict):
            raw_data[key] = json.dumps(raw_data[key], separators=(",", ":"))

    # Create data_check_string (for hashing)
    data_check_string = "\n".join(f"{k}={raw_data[k]}" for k in sorted(raw_data))

    # Compute HMAC hash
    secret_key = hmac.new(b"WebAppData", settings.tg_bot_token.encode(), hashlib.sha256).digest()
    hash_value = hmac.new(secret_key, msg=data_check_string.encode(), digestmod=hashlib.sha256).hexdigest()

    # Assemble init_data query string (URL-encoded)
    init_data_parts = [f"{k}={quote(str(v), safe='')}" for k, v in sorted(raw_data.items())]
    init_data_parts.append(f"hash={hash_value}")
    init_data = "&".join(init_data_parts)
    init_data_unsafe.hash = hash_value

    return TelegramProviderDataDTO(
        init_data=init_data,
        init_data_unsafe=init_data_unsafe,
    )
