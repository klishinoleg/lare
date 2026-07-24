from enum import Enum


class TextActionsTypes(str, Enum):
    TRANSLATE = "TRANSLATE"
    VOICE = "VOICE"


class TextTranslateTypes(str, Enum):
    FULL = "FULL"
    TEXT = "TEXT"
    WORDS = "WORDS"
