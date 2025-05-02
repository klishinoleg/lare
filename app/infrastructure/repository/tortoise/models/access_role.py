from __future__ import annotations

from tortoise import fields
from tortoise.models import Model
from typing import TYPE_CHECKING

from domain.access_role.enums.roles import AccessRole

if TYPE_CHECKING:
    from .account import AccountModel


class AccessRoleModel(Model):
    """
    ORM model representing a user's global access role.
    """

    if TYPE_CHECKING:
        account_id: int

    id = fields.IntField(primary_key=True)
    account: fields.OneToOneRelation["AccountModel"] = fields.OneToOneField(
        "models.AccountModel",
        related_name="roles",
        on_delete=fields.CASCADE,
    )
    role = fields.IntEnumField(AccessRole)

    class Meta:
        table = "access_role"
