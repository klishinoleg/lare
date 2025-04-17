from tortoise import fields
from .abstract import AbstractModel
from .mixins import TimestampMixin
from domain.auth_profile.enums import AuthProviderType


class AuthProfileModel(AbstractModel, TimestampMixin):
    """
    Tortoise ORM model for an external authentication profile (e.g. Telegram, WhatsApp).

    Links a user account to a third-party service.
    Stores provider type, unique provider user ID, and additional provider data.

    Inherits:
        AbstractModel: Tortoise base model
        TimestampMixin: Adds created_at and updated_at

    Fields:
        id (int): Primary key
        account (FK): Link to internal user account
        provider_type (str): Enum value like 'TELEGRAM'
        provider_id (str): External service user ID
        provider_data (JSON): Raw auth data
        language_code (str): Language code
    """

    id = fields.IntField(primary_key=True)
    account = fields.ForeignKeyField("models.AccountModel", related_name="auth_profiles", on_delete=fields.CASCADE)
    provider_type = fields.CharEnumField(AuthProviderType)
    provider_id = fields.CharField(max_length=255)
    provider_data = fields.JSONField()
    language_code = fields.CharField(max_length=6, null=True)

    class Meta:
        unique_together = (('provider_type', 'provider_id'),)
        table = "auth_profile"
