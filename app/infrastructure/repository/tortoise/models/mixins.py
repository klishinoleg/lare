from tortoise import fields


class TimestampMixin:
    """
    Mixin for automatically tracking creation and update timestamps.

    Fields:
        created_at (datetime): Timestamp when the record was first created.
        updated_at (datetime): Timestamp when the record was last updated.
    """
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)


class WithActiveMixin:
    """
    Mixin to add an 'is_active' flag for soft deletion or status management.

    Fields:
        is_active (bool): Indicates whether the record is active.
                          Useful for soft-deletion logic.
    """
    is_active = fields.BooleanField(default=True)
