from tortoise import fields
from .abstract import AbstractModel
from .mixins import WithActiveMixin, TimestampMixin


class AccountModel(AbstractModel, WithActiveMixin, TimestampMixin):
    """
    Tortoise ORM model representing a user account in the database.

    This model maps directly to the `account` table and stores information
    related to user credentials and balance. It also includes mixins for
    soft deletion and timestamp tracking.

    Inherits:
        AbstractModel: Base class for all ORM models.
        WithActiveMixin: Adds `is_active` field.
        TimestampMixin: Adds `created_at` and `updated_at` fields.

    Fields:
        id (int): Primary key.
        username (str): Unique username for the account.
        email (str | None): Email address (optional).
        credits (float): Balance of credits associated with the account.
        public_name (str | None): Optional public display name.
    """

    id = fields.IntField(primary_key=True)
    username = fields.CharField(max_length=100, unique=True)
    email = fields.CharField(max_length=255, null=True)
    credits = fields.FloatField(default=0.0)
    public_name = fields.CharField(max_length=255, null=True)

    class Meta:
        table = "account"
