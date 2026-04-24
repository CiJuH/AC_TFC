import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.api.v1.dependencies import get_current_user
from app.models.user import User
from app.models.visit import Visit
from app.models.review import Review
from app.schemas.review import ReviewCreate, ReviewResponse

router = APIRouter(prefix="/reviews", tags=["reviews"])


@router.post("", response_model=ReviewResponse, status_code=status.HTTP_201_CREATED)
async def create_review(
    body: ReviewCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    visit = await db.get(Visit, body.visit_id)
    if not visit:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Visit not found")

    # Only the visitor can review (reviewing the host)
    if visit.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only the visitor can leave a review")

    # Visit must be completed
    if visit.left_at is None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Visit has not ended yet")

    # One review per visit
    result = await db.execute(select(Review).where(Review.visit_id == body.visit_id))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Visit already has a review")

    review = Review(
        visit_id=body.visit_id,
        reviewer_id=current_user.id,
        reviewed_id=body.reviewed_id,
        rating=body.rating,
        comment=body.comment,
    )
    db.add(review)
    await db.flush()  # persist review so it's included in the avg query

    # Recalculate host rating
    avg_result = await db.execute(
        select(func.avg(Review.rating)).where(Review.reviewed_id == body.reviewed_id)
    )
    host = await db.get(User, body.reviewed_id)
    if host:
        avg = avg_result.scalar()
        host.rating = float(avg) if avg is not None else 0.0

    await db.commit()
    await db.refresh(review)
    return review


@router.get("/{review_id}", response_model=ReviewResponse)
async def get_review(review_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    review = await db.get(Review, review_id)
    if not review:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Review not found")
    return review


@router.get("/visit/{visit_id}", response_model=ReviewResponse)
async def get_review_by_visit(visit_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Review).where(Review.visit_id == visit_id))
    review = result.scalar_one_or_none()
    if not review:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No review for this visit")
    return review


@router.get("/user/{user_id}", response_model=list[ReviewResponse])
async def get_reviews_for_user(user_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    """All reviews received by a user (host rating history)."""
    result = await db.execute(
        select(Review).where(Review.reviewed_id == user_id).order_by(Review.created_at.desc())
    )
    return result.scalars().all()