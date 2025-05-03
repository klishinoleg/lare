from tortoise import Tortoise, connections, BaseDBAsyncClient, ConfigurationError
from core.config import settings

MASTER_CONNECTION = "default"
SLAVE_CONNECTION = "read"


async def init_tortoise(with_schema: bool = True) -> None:
    """
    Initialize the Tortoise ORM with the configured database.

    This function connects to the database using the URL defined in the
    settings and loads all ORM models from the specified module path.

    Args:
        with_schema (bool): If True, generates database schema based on defined models.
                            Should typically be False in production environments.
    """
    await Tortoise.init(
        config={
            "connections": {
                MASTER_CONNECTION: settings.database_url,
                SLAVE_CONNECTION: settings.slave_database_url or settings.database_url
            },
            "apps": {
                "models": {
                    "models": ["infrastructure.repository.tortoise.models"],
                    "default_connection": MASTER_CONNECTION,
                }
            }
        }
    )
    if with_schema:
        await Tortoise.generate_schemas()


async def close_tortoise() -> None:
    """
    Close all open Tortoise ORM database connections.

    Should be called during application shutdown or test cleanup.
    """
    await connections.close_all()


def get_master_connection() -> BaseDBAsyncClient:
    """Returns a connection to the Master database."""
    connection = connections.get(MASTER_CONNECTION)
    if not connection:
        raise ConfigurationError("Master connection does not exist")
    return connection


def get_slave_connection() -> BaseDBAsyncClient:
    """Returns a connection to the Slave database"""
    connection = connections.get(SLAVE_CONNECTION)
    if not connection:
        raise ConfigurationError("Slave connection does not exist")
    return connection
