from typing import Any, Generic, List, Optional, TypeVar
from pydantic import BaseModel, Field

DataT = TypeVar("DataT")


class ErrorDetail(BaseModel):
    code: str = Field(..., description="Machine-readable error code")
    message: str = Field(..., description="Human-readable error description")
    details: Optional[Any] = Field(None, description="Granular error details or validation list")


class ErrorResponse(BaseModel):
    success: bool = Field(False, description="Operation status indicator")
    error: ErrorDetail
    request_id: Optional[str] = Field(None, description="Unique correlation ID for tracing")


class ApiResponse(BaseModel, Generic[DataT]):
    success: bool = Field(True, description="Operation status indicator")
    data: DataT
    request_id: Optional[str] = Field(None, description="Unique correlation ID for tracing")


class PaginationMeta(BaseModel):
    page: int = Field(..., description="Current page number (1-indexed)")
    page_size: int = Field(..., description="Items per page")
    total: int = Field(..., description="Total matching items count")
    total_pages: int = Field(..., description="Total pages available")


class PaginatedResponse(BaseModel, Generic[DataT]):
    success: bool = Field(True, description="Operation status indicator")
    data: List[DataT]
    pagination: PaginationMeta
    request_id: Optional[str] = Field(None, description="Unique correlation ID for tracing")


class PaginationParams(BaseModel):
    page: int = Field(1, ge=1, description="Page number (1-indexed)")
    page_size: int = Field(20, ge=1, le=100, description="Items per page")
