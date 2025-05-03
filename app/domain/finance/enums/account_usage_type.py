from enum import Enum


class AccountUsageType(str, Enum):
    AI_IMAGE = "ai_image"
    AI_DIALOG = "ai_dialog"
    AI_TRANSLATE = "ai_translate"
    AI_VOICE = "ai_voice"
    AI_WORD = "ai_word"
    AI_ARTICLE = "ai_article"
    AI_BOOK = "ai_book"
