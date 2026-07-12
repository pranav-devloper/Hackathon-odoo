"""FastAPI application entrypoint: wiring, lifespan (create tables + seed roles)."""
import os

from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

from app.config import settings
from app.database import Base, SessionLocal, engine
from app.models import user, role, otp, refresh_token  # noqa: F401  (register models)
from app.models import department, asset_category, asset, allocation, maintenance_ticket  # noqa: F401
from app.models import transfer, notification  # noqa: F401
from app.routes import auth
from app.routes import org
from app.routes import assets
from app.routes import allocations
from app.routes import notifications
from app.routes import bookings
from app.routes import maintenance
from app.routes import audits
from app.routes import reports
from app.routes import activity

# Built React SPA output (after `npm run build` in frontend/). When absent the
# API still works normally; only the SPA routes return a helpful 404.
_FRONTEND_DIST = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "frontend", "dist")
)


def seed_roles() -> None:
    """Insert the default RBAC roles if they don't exist yet.

    Four roles: Employee (internal name 'user'), Department Head, Asset Manager,
    Admin. Roles are assigned only by an Admin via the Employee Directory.
    """
    from app.models.role import Role

    defaults = [
        ("user", "Employee — standard authenticated user (default at signup)"),
        ("department_head", "Department Head — leads a department"),
        ("asset_manager", "Asset Manager — registers/allocates assets, approves requests"),
        ("admin", "Administrator with full access (org setup, role assignment)"),
    ]
    db = SessionLocal()
    try:
        for name, description in defaults:
            if not db.query(Role).filter(Role.name == name).first():
                db.add(Role(name=name, description=description))
        db.commit()
    finally:
        db.close()


def migrate() -> None:
    """Apply additive schema changes to existing dev databases.

    `create_all` only creates missing tables, so columns added to an existing
    table (e.g. MaintenanceTicket) must be added with guarded ALTERs. Safe to
    re-run: each column is only added if absent.
    """
    from sqlalchemy import inspect, text

    alters = [
        ("maintenance_tickets", "rejected_reason", "TEXT"),
        ("maintenance_tickets", "resolved_at", "DATETIME"),
        ("maintenance_tickets", "assigned_at", "DATETIME"),
        ("maintenance_tickets", "approved_by", "INTEGER"),
        ("maintenance_tickets", "photo_path", "VARCHAR(512)"),
    ]
    inspector = inspect(engine)
    existing = {c["name"] for c in inspector.get_columns("maintenance_tickets")}
    with engine.begin() as conn:
        for table, col, ddl in alters:
            if col not in existing:
                conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {col} {ddl}"))


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create tables and seed roles on startup (create_all strategy).
    Base.metadata.create_all(bind=engine)
    migrate()
    seed_roles()
    yield


app = FastAPI(title=settings.PROJECT_NAME, lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(org.router)
app.include_router(assets.router)
app.include_router(assets.dashboard_router)
app.include_router(allocations.router)
app.include_router(notifications.router)
app.include_router(bookings.router)
app.include_router(maintenance.router)
app.include_router(audits.router)
app.include_router(reports.router)
app.include_router(activity.router)


@app.get("/", tags=["root"])
async def root():
    index_html = os.path.join(_FRONTEND_DIST, "index.html")
    if os.path.isfile(index_html):
        return FileResponse(index_html)
    return {
        "status": "ok",
        "service": settings.PROJECT_NAME,
        "docs": "/docs",
        "note": "Frontend not built. Run `npm run build` in frontend/ or use `npm run dev`.",
    }


@app.get("/{full_path:path}", include_in_schema=False)
async def spa_index(full_path: str):
    """Serve the built React SPA.

    Real static assets (JS/CSS/etc.) are returned directly; any other path
    falls back to index.html so client-side routes (e.g. /profile) resolve.
    API and docs routes are never hijacked (they match earlier, or 404 here).
    """
    if full_path.startswith("auth") or full_path in ("docs", "redoc", "openapi.json"):
        raise HTTPException(status_code=404, detail="Not found")

    candidate = os.path.join(_FRONTEND_DIST, full_path)
    if os.path.isfile(candidate):
        return FileResponse(candidate)

    index_html = os.path.join(_FRONTEND_DIST, "index.html")
    if not os.path.isfile(index_html):
        raise HTTPException(
            status_code=404,
            detail="Frontend not built. Run `npm run build` in frontend/ or use `npm run dev`.",
        )
    return FileResponse(index_html)
