"""Booking routes (Screen 6): create, list, view, cancel."""
from typing import Optional

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.schemas.booking import BookingCreate, BookingOut
from app.services import booking_service

router = APIRouter(prefix="/bookings", tags=["bookings"])

MANAGER_ROLES = ("asset_manager", "department_head", "admin")


def serialize(db: Session, b) -> BookingOut:
    asset = b.asset
    user = b.user
    return BookingOut(
        id=b.id,
        asset_id=b.asset_id,
        asset_tag=asset.asset_tag if asset else None,
        asset_name=asset.name if asset else None,
        user_id=b.user_id,
        user_name=user.full_name if user else None,
        start_time=b.start_time,
        end_time=b.end_time,
        purpose=b.purpose,
        status=b.status,
        created_at=b.created_at,
    )


@router.post("", response_model=BookingOut, status_code=201)
def post_booking(
    data: BookingCreate,
    db: Session = Depends(get_db),
    me: User = Depends(get_current_user),
):
    """Create a booking for a bookable asset (requester = current user)."""
    booking = booking_service.create_booking(
        db, me.id, data.asset_id, data.start_time, data.end_time, data.purpose
    )
    return serialize(db, booking)


@router.get("", response_model=list[BookingOut])
def get_bookings(
    asset_id: Optional[int] = None,
    status: Optional[str] = None,
    mine: bool = False,
    db: Session = Depends(get_db),
    me: User = Depends(get_current_user),
):
    user_id = me.id if mine else None
    return [serialize(db, b) for b in booking_service.list_bookings(
        db, asset_id=asset_id, status=status, user_id=user_id
    )]


@router.get("/{booking_id}", response_model=BookingOut)
def get_one(
    booking_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    return serialize(db, booking_service.get_booking(db, booking_id))


@router.post("/{booking_id}/cancel", response_model=BookingOut)
def cancel_booking(
    booking_id: int,
    db: Session = Depends(get_db),
    me: User = Depends(get_current_user),
):
    """Cancel a booking. Allowed by the requester or any manager."""
    is_manager = bool(me.role and me.role.name in MANAGER_ROLES)
    return serialize(db, booking_service.cancel_booking(db, booking_id, me.id, is_manager, me.id))
