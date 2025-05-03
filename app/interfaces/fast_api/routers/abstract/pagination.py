from typing import Type, List
from pydantic import BaseModel, Field
from fastapi import Query
from domain.abstract.entity import BaseEntity


class PageParams:
    def __init__(
            self,
            page: int = Query(1, description="Page number (starting from 1)"),
            page_size: int = Query(20, le=100, description="Number of items per page")
    ):
        self.page = page
        self.page_size = page_size


class PageDTO[T: BaseModel](BaseModel):
    count: int = Field(..., description="Total number of items")
    page: int = Field(..., description="Current page number")
    page_size: int = Field(..., description="Items per page")
    total_pages: int = Field(..., description="Total number of pages")
    results: List[T] = Field(..., description="List of results")


async def paginate[T: BaseModel](
        items: list[BaseEntity],
        schema: Type[T],
        params: PageParams,
) -> PageDTO:
    total_count = len(items)

    if params.page_size == 0:
        results = [schema.model_validate(i.to_dict()) for i in items]
        return PageDTO(
            count=total_count,
            page=1,
            page_size=0,
            total_pages=1,
            results=results,
        )

    start = (params.page - 1) * params.page_size
    end = start + params.page_size
    page_items = items[start:end]
    total_pages = (total_count + params.page_size - 1) // params.page_size

    return PageDTO(
        count=total_count,
        page=params.page,
        page_size=params.page_size,
        total_pages=total_pages,
        results=[schema.model_validate(i.to_dict()) for i in page_items],
    )
