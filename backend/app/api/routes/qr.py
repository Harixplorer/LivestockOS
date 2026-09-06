from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.api.deps import get_current_user, get_db
from app.models.animal import Animal
from app.models.user import User
from app.schemas.qr import QrLookupResponse
from app.services.animal_service import attach_vitals

router = APIRouter(prefix="/qr", tags=["QR Code Identification"])


@router.get("/lookup", response_model=QrLookupResponse, summary="Lookup animal from tag ID or QR scan")
async def lookup_qr(
    query: str = Query(..., min_length=1, description="Tag ID, Animal ID, or QR payload string"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    clean_q = query.strip()
    # Check if query is formatted QR payload e.g. LIVESTOCKOS|animal-001|TAG-1001|Gauri|...
    parts = clean_q.split("|")
    extracted_id = parts[1] if len(parts) >= 3 and parts[0] == "LIVESTOCKOS" else None

    stmt = select(Animal).where(
        Animal.farmer_id == current_user.id,
        or_(
            Animal.id == clean_q,
            Animal.tag_id == clean_q,
            Animal.id == extracted_id if extracted_id else False,
            Animal.qr_code_payload == clean_q,
        )
    )
    result = await db.execute(stmt)
    animal = result.scalars().first()

    if not animal:
        return QrLookupResponse(found=False, query=clean_q, animal=None)

    animal_resp = await attach_vitals(db, animal)
    return QrLookupResponse(found=True, query=clean_q, animal=animal_resp)
