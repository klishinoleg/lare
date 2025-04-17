from tortoise import fields
from .abstract import AbstractModel


class WordChapterModel(AbstractModel):
    """
    ORM model linking a word to a specific chapter and position.
    """
    id = fields.IntField(primary_key=True)
    name = fields.CharField(max_length=255)
    word = fields.ForeignKeyField("models.WordModel", related_name="words_uses", on_delete=fields.CASCADE)
    chapter = fields.ForeignKeyField("models.ChapterModel", related_name="chapter_words", on_delete=fields.CASCADE)
    position = fields.IntField()
    n = fields.IntField(default=0)
    phrase = fields.ForeignKeyField("models.PhraseModel", related_name="phrase_words", on_delete=fields.SET_NULL,
                                    null=True)
    segment = fields.ForeignKeyField("models.SegmentModel", related_name="segment_words", on_delete=fields.SET_NULL,
                                     null=True)

    class Meta:
        table = "word_chapter"
