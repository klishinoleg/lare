from enum import Enum


class EventTypes(Enum):
    CHAPTER_CREATE_REQUESTED = "chapter.create.requested"
    CHAPTER_TEXT_PROCESSED = "chapter.text.processed"
    CHAPTER_WORDS_SAVED = "chapter.words.saved"
    CHAPTER_CREATION_COMPLETED = "chapter.creation.completed"
    CHAPTER_CREATION_ERROR = "chapter.creation.error"
