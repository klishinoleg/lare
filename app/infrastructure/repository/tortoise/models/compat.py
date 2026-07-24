from __future__ import annotations

from typing import TYPE_CHECKING

from tortoise import fields

from .abstract import AbstractModel
from .mixins import TimestampMixin

if TYPE_CHECKING:
    from .account import AccountModel
    from .book import BookModel
    from .chapter import ChapterModel
    from .language import LanguageModel
    from .word import WordModel
    from .word_chapter import WordChapterModel


class CompatChapterProgressModel(AbstractModel, TimestampMixin):
    if TYPE_CHECKING:
        account_id: int
        chapter_id: int

    id = fields.IntField(primary_key=True)
    account: fields.ForeignKeyRelation["AccountModel"] = fields.ForeignKeyField(
        "models.AccountModel",
        related_name="compat_chapter_progress",
        on_delete=fields.CASCADE,
    )
    chapter: fields.ForeignKeyRelation["ChapterModel"] = fields.ForeignKeyField(
        "models.ChapterModel",
        related_name="compat_progress",
        on_delete=fields.CASCADE,
    )
    percent = fields.IntField(default=0)

    class Meta:
        table = "compat_chapter_progress"
        unique_together = (("account_id", "chapter_id"),)


class CompatBookStateModel(AbstractModel, TimestampMixin):
    if TYPE_CHECKING:
        account_id: int
        book_id: int

    id = fields.IntField(primary_key=True)
    account: fields.ForeignKeyRelation["AccountModel"] = fields.ForeignKeyField(
        "models.AccountModel",
        related_name="compat_book_states",
        on_delete=fields.CASCADE,
    )
    book: fields.ForeignKeyRelation["BookModel"] = fields.ForeignKeyField(
        "models.BookModel",
        related_name="compat_states",
        on_delete=fields.CASCADE,
    )
    is_active = fields.BooleanField(default=True)

    class Meta:
        table = "compat_book_state"
        unique_together = (("account_id", "book_id"),)


class CompatTextPartModel(AbstractModel, TimestampMixin):
    if TYPE_CHECKING:
        account_id: int
        chapter_id: int
        language_id: int

    id = fields.IntField(primary_key=True)
    account: fields.ForeignKeyRelation["AccountModel"] = fields.ForeignKeyField(
        "models.AccountModel",
        related_name="compat_text_parts",
        on_delete=fields.CASCADE,
    )
    chapter: fields.ForeignKeyRelation["ChapterModel"] = fields.ForeignKeyField(
        "models.ChapterModel",
        related_name="compat_text_parts",
        on_delete=fields.CASCADE,
    )
    language: fields.ForeignKeyRelation["LanguageModel"] = fields.ForeignKeyField(
        "models.LanguageModel",
        related_name="compat_text_parts",
        on_delete=fields.CASCADE,
    )
    name = fields.TextField()
    translate = fields.TextField(null=True)
    transliteration = fields.CharField(max_length=255, null=True)
    description = fields.TextField(null=True)
    ai_voice_file = fields.CharField(max_length=255, null=True)

    class Meta:
        table = "compat_text_part"


class CompatTextPartWordModel(AbstractModel):
    if TYPE_CHECKING:
        text_part_id: int
        word_chapter_id: int

    id = fields.IntField(primary_key=True)
    text_part: fields.ForeignKeyRelation["CompatTextPartModel"] = (
        fields.ForeignKeyField(
            "models.CompatTextPartModel",
            related_name="word_links",
            on_delete=fields.CASCADE,
        )
    )
    word_chapter: fields.ForeignKeyRelation["WordChapterModel"] = (
        fields.ForeignKeyField(
            "models.WordChapterModel",
            related_name="compat_text_part_links",
            on_delete=fields.CASCADE,
        )
    )
    position = fields.IntField(default=0)

    class Meta:
        table = "compat_text_part_word"
        unique_together = (("text_part_id", "word_chapter_id"),)


class CompatPhraseModel(AbstractModel, TimestampMixin):
    if TYPE_CHECKING:
        account_id: int
        chapter_id: int
        language_id: int
        text_part_id: int | None

    id = fields.IntField(primary_key=True)
    account: fields.ForeignKeyRelation["AccountModel"] = fields.ForeignKeyField(
        "models.AccountModel",
        related_name="compat_phrases",
        on_delete=fields.CASCADE,
    )
    chapter: fields.ForeignKeyRelation["ChapterModel"] = fields.ForeignKeyField(
        "models.ChapterModel",
        related_name="compat_phrases",
        on_delete=fields.CASCADE,
    )
    language: fields.ForeignKeyRelation["LanguageModel"] = fields.ForeignKeyField(
        "models.LanguageModel",
        related_name="compat_phrases",
        on_delete=fields.CASCADE,
    )
    text_part: fields.ForeignKeyRelation["CompatTextPartModel"] | None = (
        fields.ForeignKeyField(
            "models.CompatTextPartModel",
            related_name="phrases",
            on_delete=fields.SET_NULL,
            null=True,
        )
    )
    name = fields.TextField()
    translate = fields.TextField(null=True)
    transliteration = fields.CharField(max_length=255, null=True)
    description = fields.TextField(null=True)
    ai_voice_file = fields.CharField(max_length=255, null=True)

    class Meta:
        table = "compat_phrase"


class CompatPhraseWordModel(AbstractModel):
    if TYPE_CHECKING:
        phrase_id: int
        word_chapter_id: int

    id = fields.IntField(primary_key=True)
    phrase: fields.ForeignKeyRelation["CompatPhraseModel"] = fields.ForeignKeyField(
        "models.CompatPhraseModel",
        related_name="word_links",
        on_delete=fields.CASCADE,
    )
    word_chapter: fields.ForeignKeyRelation["WordChapterModel"] = (
        fields.ForeignKeyField(
            "models.WordChapterModel",
            related_name="compat_phrase_links",
            on_delete=fields.CASCADE,
        )
    )
    position = fields.IntField(default=0)

    class Meta:
        table = "compat_phrase_word"
        unique_together = (("phrase_id", "word_chapter_id"),)


class CompatStudyPhraseModel(AbstractModel, TimestampMixin):
    if TYPE_CHECKING:
        account_id: int
        chapter_id: int | None
        word_id: int | None
        text_part_id: int | None
        phrase_id: int | None

    id = fields.IntField(primary_key=True)
    account: fields.ForeignKeyRelation["AccountModel"] = fields.ForeignKeyField(
        "models.AccountModel",
        related_name="compat_study_phrases",
        on_delete=fields.CASCADE,
    )
    chapter: fields.ForeignKeyRelation["ChapterModel"] | None = fields.ForeignKeyField(
        "models.ChapterModel",
        related_name="compat_study_phrases",
        on_delete=fields.SET_NULL,
        null=True,
    )
    word: fields.ForeignKeyRelation["WordModel"] | None = fields.ForeignKeyField(
        "models.WordModel",
        related_name="compat_study_phrases",
        on_delete=fields.CASCADE,
        null=True,
    )
    text_part: fields.ForeignKeyRelation["CompatTextPartModel"] | None = (
        fields.ForeignKeyField(
            "models.CompatTextPartModel",
            related_name="study_phrases",
            on_delete=fields.CASCADE,
            null=True,
        )
    )
    phrase: fields.ForeignKeyRelation["CompatPhraseModel"] | None = (
        fields.ForeignKeyField(
            "models.CompatPhraseModel",
            related_name="study_phrases",
            on_delete=fields.CASCADE,
            null=True,
        )
    )
    is_active = fields.BooleanField(default=True)
    audio_average = fields.FloatField(default=0)
    forward_average = fields.FloatField(default=0)
    reverse_average = fields.FloatField(default=0)
    average = fields.FloatField(default=0)
    success_logs = fields.IntField(default=0)

    class Meta:
        table = "compat_study_phrase"


class CompatStudyPhraseLogModel(AbstractModel, TimestampMixin):
    if TYPE_CHECKING:
        study_phrase_id: int

    id = fields.IntField(primary_key=True)
    study_phrase: fields.ForeignKeyRelation["CompatStudyPhraseModel"] = (
        fields.ForeignKeyField(
            "models.CompatStudyPhraseModel",
            related_name="logs",
            on_delete=fields.CASCADE,
        )
    )
    study_type = fields.CharField(max_length=20, default="forward")
    rank = fields.SmallIntField(null=True)
    is_active = fields.BooleanField(default=False)

    class Meta:
        table = "compat_study_phrase_log"


class CompatDialogModel(AbstractModel, TimestampMixin):
    if TYPE_CHECKING:
        account_id: int
        text_part_id: int

    id = fields.IntField(primary_key=True)
    account: fields.ForeignKeyRelation["AccountModel"] = fields.ForeignKeyField(
        "models.AccountModel",
        related_name="compat_dialogs",
        on_delete=fields.CASCADE,
    )
    text_part: fields.ForeignKeyRelation["CompatTextPartModel"] = (
        fields.ForeignKeyField(
            "models.CompatTextPartModel",
            related_name="dialogs",
            on_delete=fields.CASCADE,
        )
    )
    dialog = fields.JSONField(default=list)

    class Meta:
        table = "compat_dialog"
        unique_together = (("account_id", "text_part_id"),)


class CompatWordEtymologyModel(AbstractModel, TimestampMixin):
    if TYPE_CHECKING:
        word_id: int

    id = fields.IntField(primary_key=True)
    word: fields.ForeignKeyRelation["WordModel"] = fields.OneToOneField(
        "models.WordModel",
        related_name="compat_etymology",
        on_delete=fields.CASCADE,
    )
    description = fields.TextField()
    root_name = fields.CharField(max_length=100)
    root_description = fields.TextField(null=True)

    class Meta:
        table = "compat_word_etymology"


class CompatWordPartModel(AbstractModel):
    if TYPE_CHECKING:
        etymology_id: int

    id = fields.IntField(primary_key=True)
    etymology: fields.ForeignKeyRelation["CompatWordEtymologyModel"] = (
        fields.ForeignKeyField(
            "models.CompatWordEtymologyModel",
            related_name="parts",
            on_delete=fields.CASCADE,
        )
    )
    part_type = fields.CharField(max_length=32)
    name = fields.CharField(max_length=100)
    description = fields.TextField(null=True)

    class Meta:
        table = "compat_word_part"
