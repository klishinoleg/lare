from fastapi import FastAPI, status
from starlette.requests import Request
from starlette.responses import JSONResponse

from domain.abstract import DomainValidationException, EntityNotFoundException


def register_exception_handler(app: FastAPI):
    """
    Register global exception handlers for domain-level exceptions in the FastAPI application.

    This function attaches custom handlers for domain-specific exceptions such as:
    - DomainValidationException: Triggers on business validation failures (e.g., duplicate username).
    - EntityNotFoundException: Triggers when a requested resource (e.g., Account) is not found.

    These handlers transform exceptions into structured JSON error responses
    compatible with FastAPI's validation format.

    Args:
        app (FastAPI): The FastAPI application instance to bind the handlers to.
    """

    @app.exception_handler(DomainValidationException)
    async def exception_handler(request: Request, exc: DomainValidationException):
        """
        Handle domain validation exceptions (422).

        Returns:
            JSONResponse: A response with field-level validation error details.
        """
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={"detail": [
                {
                    "loc": ["body", exc.field],
                    "msg": exc.message,
                    "type": type(exc).__name__
                }
            ]},
        )

    @app.exception_handler(EntityNotFoundException)
    async def not_fount_handler(request: Request, exc: EntityNotFoundException):
        """
        Handle entity not found exceptions (404).

        Returns:
            JSONResponse: A minimal response indicating the type of missing entity.
        """
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"detail": [
                {
                    "type": type(exc).__name__
                }
            ]},
        )
