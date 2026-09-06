from typing import Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import get_current_user, get_db
from app.models.user import User
from app.schemas.animal import (
    AnimalCreate,
    AnimalListResponse,
    AnimalResponse,
    AnimalUpdate,
    HerdStatsResponse,
)
from app.schemas.common import MessageResponse
from app.schemas.sensor import SensorPairRequest
from app.services import animal_service

router = APIRouter(prefix="/animals", tags=["Animals"])


@router.get(
    "",
    response_model=AnimalListResponse,
    summary="List herd animals with search, filtering, sorting, and pagination"
)
async def list_animals(
    search: Optional[str] = Query(None, description="Search by name, tag, or breed"),
    breed: Optional[str] = Query(None, description="Filter by breed"),
    status: Optional[str] = Query(None, description="Filter by status (HEALTHY, WARNING, CRITICAL, PENDING)"),
    sort: Optional[str] = Query(None, description="Sort option: 'gender', 'name', 'tag'"),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    items, total = await animal_service.list_animals(
        db=db,
        farmer_id=current_user.id,
        search=search,
        breed=breed,
        status_filter=status,
        sort_by=sort,
        page=page,
        page_size=page_size
    )
    return AnimalListResponse(
        total=total,
        page=page,
        page_size=page_size,
        items=items
    )


@router.get("/stats", response_model=HerdStatsResponse, summary="Get summary statistics for herd")
async def get_herd_stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return await animal_service.compute_herd_stats(db, current_user.id)


@router.post(
    "",
    response_model=AnimalResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new animal in herd"
)
async def add_animal(
    data: AnimalCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return await animal_service.create_animal(db, current_user.id, data)


@router.get(
    "/{animal_id}",
    response_model=AnimalResponse,
    summary="Get animal details and latest vitals"
)
async def get_animal(
    animal_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return await animal_service.get_animal(db, current_user.id, animal_id)


@router.put(
    "/{animal_id}",
    response_model=AnimalResponse,
    summary="Update animal details"
)
async def update_animal(
    animal_id: str,
    data: AnimalUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return await animal_service.update_animal(db, current_user.id, animal_id, data)


@router.delete(
    "/{animal_id}",
    response_model=MessageResponse,
    summary="Delete an animal from herd"
)
async def delete_animal(
    animal_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    await animal_service.delete_animal(db, current_user.id, animal_id)
    return MessageResponse(message=f"Animal '{animal_id}' successfully deleted.")


@router.post(
    "/{animal_id}/pair-sensor",
    response_model=AnimalResponse,
    summary="Pair a hardware BLE sensor to an animal"
)
async def pair_sensor(
    animal_id: str,
    data: SensorPairRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return await animal_service.pair_sensor(
        db=db,
        farmer_id=current_user.id,
        animal_id=animal_id,
        sensor_id_str=data.sensor_id,
        sensor_name=data.sensor_name
    )


@router.post(
    "/{animal_id}/unpair-sensor",
    response_model=AnimalResponse,
    summary="Unpair sensor from animal"
)
async def unpair_sensor(
    animal_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return await animal_service.unpair_sensor(db, current_user.id, animal_id)
