from typing import TYPE_CHECKING
from tortoise import fields
from infrastructure.repository.tortoise.models.abstract import AbstractModel
from infrastructure.repository.tortoise.models.mixins import WithActiveMixin

if TYPE_CHECKING:
    from domain.finance.enums.account_usage_type import AccountUsageType


class AiModelModel(AbstractModel, WithActiveMixin):
    """
    Represents available AI models with their pricing configuration.
    """

    id = fields.IntField(primary_key=True)
    name = fields.CharField(max_length=100)
    model = fields.CharField(max_length=30, unique=True)
    input_cost = fields.DecimalField(max_digits=10, decimal_places=5)
    output_cost = fields.DecimalField(max_digits=10, decimal_places=5, null=True)
    kef = fields.IntField(default=1)
    allow_to: list["AccountUsageType"] = fields.JSONField(default=list)

    class Meta:
        table = "ai_model"
