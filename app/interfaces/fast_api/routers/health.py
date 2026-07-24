from __future__ import annotations

from fastapi import APIRouter

router = APIRouter(tags=["runtime"])


def _ready_payload() -> dict[str, str]:
    return {
        "status": "ok",
        "service": "lazy-reader-ddd",
    }


@router.get("/ready")
async def ready_root() -> dict[str, str]:
    return _ready_payload()


@router.get("/api/v1/ready")
async def ready_api_v1() -> dict[str, str]:
    return _ready_payload()
