from typing import TYPE_CHECKING
from tortoise import fields
from infrastructure.repository.tortoise.models.abstract import AbstractModel

if TYPE_CHECKING:
    from .segment import SegmentModel


class SegmentVoiceModel(AbstractModel):
    """
    Links a segment to a voice audio file path.
    """

    if TYPE_CHECKING:
        segment_id: int

    id = fields.IntField(primary_key=True)
    segment: fields.ForeignKeyRelation["SegmentModel"] = fields.OneToOneField(
        "models.SegmentModel",
        related_name="voice",
        on_delete=fields.CASCADE
    )
    file_path = fields.CharField(max_length=255)

    class Meta:
        table = "segment_voice"
