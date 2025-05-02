from tortoise import models


class AbstractModel(models.Model):
    """
    Abstract base model for all ORM models using Tortoise.

    This class serves as the common base for defining database models
    and can be extended to include shared fields or behavior.

    Tortoise ORM uses the `Meta.abstract = True` marker to prevent this
    model from being created as an actual table.

    Example:
        class UserModel(AbstractModel):
            ...
    """

    class Meta:
        abstract = True
