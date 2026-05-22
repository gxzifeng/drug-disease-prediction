"""Unified response models."""
from typing import Any, Generic, Optional, TypeVar
from pydantic import BaseModel

T = TypeVar("T")


class ResponseModel(BaseModel, Generic[T]):
    """Standard API response envelope."""
    code: int = 200
    message: str = "Success"
    data: Optional[T] = None


class PaginatedResponse(BaseModel, Generic[T]):
    """Paginated response model."""
    items: list[T]
    total: int
    page: int
    page_size: int
    pages: int


class ErrorDetail(BaseModel):
    """Error detail model."""
    field: Optional[str] = None
    message: str


class ErrorResponse(BaseModel):
    """Error response model."""
    code: int
    message: str
    errors: Optional[list[ErrorDetail]] = None
