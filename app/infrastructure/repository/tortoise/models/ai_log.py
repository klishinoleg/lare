from typing import TYPE_CHECKING
from tortoise import fields

from domain.finance.enums.account_usage_type import AccountUsageType
from infrastructure.repository.tortoise.models.abstract import AbstractModel

if TYPE_CHECKING:
    from .language import LanguageModel
    from .account import AccountModel
    from .ai_model import AiModelModel


class AiLogModel(AbstractModel):
    """
    ORM model to log AI request/response pairs.
    """

    if TYPE_CHECKING:
        ai_model_id: AiModelModel
    
    id = fields.IntField(primary_key=True)
    ai_request = fields.TextField()
    ai_response = fields.TextField()
    ai_type = fields.CharField(max_length=64)
    ai_model: fields.ForeignKeyRelation["AiModelModel"] = fields.ForeignKeyField(
        "models.AiModelModel", related_name="logs", on_delete=fields.CASCADE
    )
    file_path = fields.CharField(max_length=255, null=True)

    source_language: fields.ForeignKeyRelation["LanguageModel"] = fields.ForeignKeyField(
        "models.LanguageModel", related_name="ai_logs_source", on_delete=fields.CASCADE
    )
    target_language: fields.ForeignKeyRelation["LanguageModel"] | None = fields.ForeignKeyField(
        "models.LanguageModel", related_name="ai_logs_target", null=True, on_delete=fields.SET_NULL
    )

    usage_type = fields.CharEnumField(enum_type=AccountUsageType)
    account: fields.ForeignKeyRelation["AccountModel"] = fields.ForeignKeyField(
        "models.AccountModel", related_name="ai_logs", on_delete=fields.CASCADE
    )
    hash_str = fields.CharField(max_length=255, index=True)

    class Meta:
        table = "ai_log"
        unique_together = (("hash_str", "usage_type", "ai_type"),)
