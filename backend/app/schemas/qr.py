from typing import Optional
from pydantic import BaseModel
from app.schemas.animal import AnimalResponse


class QrLookupResponse(BaseModel):
    found: bool
    query: str
    animal: Optional[AnimalResponse] = None
