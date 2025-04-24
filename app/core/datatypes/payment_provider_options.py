from pydantic import BaseModel
from aiogram.types import LabeledPrice


class TelegramStatsProviderOptions(BaseModel):
    chat_id: int
    title: str
    description: str
    prices: list[LabeledPrice]
