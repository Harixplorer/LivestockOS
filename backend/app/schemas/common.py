from typing import Any, List, Optional
from pydantic import BaseModel, Field


class ErrorFieldDetail(BaseModel):
    field: Optional[str] = None
    message: str


class ErrorResponse(BaseModel):
    status_code: int
    message: str
    errors: Optional[List[ErrorFieldDetail]] = None


class MessageResponse(BaseModel):
    message: str
    success: bool = True
