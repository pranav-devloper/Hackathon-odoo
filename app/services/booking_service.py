"""Booking business logic (Screen 6): create with overlap conflict check, list, cancel."""
from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.asset import Asset
from app.models.booking import Booking
from app.models.user import User


def _utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def create_booking(
    db: Session,
    user_id: int,
    asset_id: int,
    start_time: datetime,
    end_time: datetime,
    purpose: str | None = None,
) -> Booking:
    if end_time <= start_time:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="End time must be after start time",
        )

    asset = db.query(Asset).filter(Asset.id == asset_id).first()
    if not asset:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Asset not found")
    if not asset.is_bookable:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This asset is not bookable",
        )

    # Overlap check: any non-cancelled booking for the same asset that intersects.
    conflict = (
        db.query(Booking)
        .filter(
            Booking.asset_id == asset_id,
            Booking.status != "cancelled",
            Booking.start_time < end_time,
            Booking.end_time > start_time,
        )
        .first()
    )
    if conflict:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Resource already booked for the selected time slot",
        )

    booking = Booking(
        asset_id=asset_id,
        user_id=user_id,
        start_time=start_time,
        end_time=end_time,
        purpose=purpose,
        status="upcoming",
    )
    db.add(booking)
    db.commit()
    db.refresh(booking)
    return booking


def list_bookings(
    db: Session,
    asset_id: int | None = None,
    status: str | None = None,
    user_id: int | None = None,
    upcoming_only: bool = False,
) -> list[Booking]:
    q = db.query(Booking)
    if asset_id is not None:
        q = q.filter(Booking.asset_id == asset_id)
    if status:
        q = q.filter(Booking.status == status)
    if user_id is not None:
        q = q.filter(Booking.user_id == user_id)
    if upcoming_only:
        q = q.filter(Booking.status == "upcoming")
    return q.order_by(Booking.start_time.desc()).all()


def get_booking(db: Session, booking_id: int) -> Booking:
    booking = db.query(Booking).filter(Booking.id == booking_id).first()
    if not booking:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Booking not found")
    return booking


def cancel_booking(db: Session, booking_id: int, user_id: int, is_manager: bool) -> Booking:
    booking = get_booking(db, booking_id)
    if booking.status == "cancelled":
        return booking
    if not is_manager and booking.user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to cancel this booking",
        )
    booking.status = "cancelled"
    db.commit()
    db.refresh(booking)
    return booking


def count_active(db: Session) -> int:
    return db.query(Booking).filter(Booking.status == "upcoming").count()
