import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.api.v1.dependencies import get_current_user, require_mod
from app.models.user import User
from app.models.report import Report
from app.schemas.report import ReportCreate, ReportResponse

router = APIRouter(prefix="/reports", tags=["reports"])


@router.post("", response_model=ReportResponse, status_code=status.HTTP_201_CREATED)
async def create_report(
    body: ReportCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if body.reported_id == current_user.id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot report yourself")

    reported = await db.get(User, body.reported_id)
    if not reported:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    report = Report(
        reporter_id=current_user.id,
        reported_id=body.reported_id,
        reason=body.reason,
        description=body.description,
    )
    db.add(report)
    await db.commit()
    await db.refresh(report)
    return report


@router.get("", response_model=list[ReportResponse])
async def list_reports(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_mod),
):
    result = await db.execute(select(Report).order_by(Report.created_at.desc()))
    return result.scalars().all()


@router.patch("/{report_id}/resolve", response_model=ReportResponse)
async def resolve_report(
    report_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_mod),
):
    report = await db.get(Report, report_id)
    if not report:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not found")
    if report.is_resolved:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Report already resolved")

    report.is_resolved = True
    await db.commit()
    await db.refresh(report)
    return report