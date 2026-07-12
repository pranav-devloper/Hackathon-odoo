"""Booking business logic (Screen 6): create with overlap conflict check, list, cancel."""
from datetime import datetime, timedelta, timezone

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.asset import Asset
from app.models.booking import Booking
from app.models.user import User
from app.services import notification_service


def _utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _overlap_conflict(db: Session, asset_id: int, start: datetime, end: datetime, exclude_id: int | None = None) -> Booking | None:
    """Find a non-cancelled booking for the same asset that intersects [start, end)."""
    q = db.query(Booking).filter(
        Booking.asset_id == asset_id,
        Booking.status != "cancelled",
        Booking.start_time < end,
        Booking.end_time > start,
    )
    if exclude_id is not None:
        q = q.filter(Booking.id != exclude_id)
    return q.first()


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
    conflict = _overlap_conflict(db, asset_id, start_time, end_time)
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

    # Notify the requester (best-effort) that the slot is reserved.
    notification_service.notify(
        db, user_id, "booking_created",
        f"Booking confirmed for {asset.asset_tag} ({asset.name}) "
        f"{start_time.strftime('%Y-%m-%d %H:%M')}–{end_time.strftime('%H:%M')}.",
        commit=False,
    )
    db.commit()
    return booking


def list_bookings(
    db: Session,
    asset_id: int | None = None,
    status: str | None = None,
    user_id: int | None = None,
    upcoming_only: bool = False,
) -> list[Booking]:
    # Keep derived statuses (ongoing / completed) in sync before listing.
    refresh_statuses(db)
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


def refresh_statuses(db: Session) -> None:
    """Advance booking statuses based on the current time.

    upcoming -> ongoing (started, not finished) -> completed (finished).
    Cancelled bookings are left untouched.
    """
    now = _utcnow()
    changed = False
    for b in db.query(Booking).filter(Booking.status.in_(["upcoming", "ongoing"])).all():
        if b.end_time <= now:
            b.status = "completed"
            changed = True
        elif b.start_time <= now:
            b.status = "ongoing"
            changed = True
    if changed:
        db.commit()


def scan_reminders(db: Session, lead_minutes: int = 60) -> int:
    """Notify requesters about bookings starting within the next `lead_minutes`.

    Idempotent: dedupes per booking with a "[B<id>]" marker so each slot only
    generates one reminder. Returns the number of reminders sent.
    """
    now = _utcnow()
    horizon = now + timedelta(minutes=lead_minutes)
    due = (
        db.query(Booking)
        .filter(
            Booking.status == "upcoming",
            Booking.start_time > now,
            Booking.start_time <= horizon,
        )
        .all()
    )
    sent = 0
    for b in due:
        marker = f"[B{b.id}]"
        exists = (
            db.query(notification_service.Notification)
            .filter(
                notification_service.Notification.type == "booking_reminder",
                notification_service.Notification.message.contains(marker),
            )
            .first()
        )
        if exists:
            continue
        asset = db.query(Asset).filter(Asset.id == b.asset_id).first()
        tag = asset.asset_tag if asset else f"#{b.asset_id}"
        msg = (
            f"{marker} Reminder: your booking for {tag} starts at "
            f"{b.start_time.strftime('%Y-%m-%d %H:%M')}."
        )
        notification_service.notify(db, b.user_id, "booking_reminder", msg, commit=False)
        sent += 1
    if sent:
        db.commit()
    return sent


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


def reschedule_booking(
    db: Session,
    booking_id: int,
    user_id: int,
    is_manager: bool,
    new_start: datetime,
    new_end: datetime,
) -> Booking:
    """Move a booking to a new time slot, re-validating the overlap rule.

    Only the requester or a manager may reschedule, and only upcoming bookings.
    The booking's own row is excluded from the overlap check.
    """
    booking = get_booking(db, booking_id)
    if booking.status != "upcoming":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only upcoming bookings can be rescheduled",
        )
    if not is_manager and booking.user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to reschedule this booking",
        )
    if new_end <= new_start:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="End time must be after start time",
        )
    # Prevent rescheduling into the past.
    if new_start <= _utcnow():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="New start time must be in the future",
        )

    conflict = _overlap_conflict(db, booking.asset_id, new_start, new_end, exclude_id=booking.id)
    if conflict:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Resource already booked for the selected time slot",
        )

    booking.start_time = new_start
    booking.end_time = new_end
    db.commit()
    db.refresh(booking)

    asset = db.query(Asset).filter(Asset.id == booking.asset_id).first()
    tag = asset.asset_tag if asset else f"#{booking.asset_id}"
    notification_service.notify(
        db, booking.user_id, "booking_rescheduled",
        f"Booking for {tag} rescheduled to "
        f"{new_start.strftime('%Y-%m-%d %H:%M')}–{new_end.strftime('%H:%M')}.",
        commit=False,
    )
    db.commit()
    return booking


def count_active(db: Session) -> int:
    # Active = still in the future or currently in progress (not cancelled/done).
    return (
        db.query(Booking)
        .filter(Booking.status.in_(["upcoming", "ongoing"]))
        .count()
    )
