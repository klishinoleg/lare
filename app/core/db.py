from tortoise import Tortoise, connections
from core.config import settings


async def init_tortoise(with_schema=True):
    """
    Initialize the Tortoise ORM with the configured database.

    This function connects to the database using the URL defined in the
    settings and loads all ORM models from the specified module path.

    Args:
        with_schema (bool): If True, generates database schema based on defined models.
                            Should typically be False in production environments.
    """
    await Tortoise.init(
        db_url=settings.database_url,
        modules={"models": ["infrastructure.repository.tortoise.models"]},
    )
    if with_schema:
        await Tortoise.generate_schemas()


async def close_tortoise():
    """
    Close all open Tortoise ORM database connections.

    Should be called during application shutdown or test cleanup.
    """
    await connections.close_all()
