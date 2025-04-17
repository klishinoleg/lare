from tortoise import fields
from tortoise.models import Model
from domain.access_role.enums.roles import AccessRole


class AccessRoleModel(Model):
    id = fields.IntField(primary_key=True)
    account = fields.OneToOneField("models.AccountModel", related_name="roles", on_delete=fields.CASCADE)
    role = fields.IntEnumField(AccessRole)

    class Meta:
        table = "access_role"
