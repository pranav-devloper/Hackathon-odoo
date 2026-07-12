"""Reports & analytics routes (Screen 9)."""
from fastapi import APIRouter, Depends, Response
from fastapi.responses import PlainTextResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.services import report_service

router = APIRouter(prefix="/reports", tags=["reports"])


@router.get("/summary")
def get_summary(db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    return report_service.summary(db)


@router.get("/export", response_class=PlainTextResponse)
def export(section: str = "all", db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    csv_text = report_service.export_csv(db, section)
    return Response(content=csv_text, media_type="text/csv",
                    headers={"Content-Disposition": "attachment; filename=assetflow-report.csv"})
