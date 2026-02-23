from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.dependencies import get_db, get_current_user
from app.models.user import User
from app.schemas.offer import OfferCreateIn, OfferOut
from app.services.offer_service import create_offer, get_my_offers, get_offer_detail

router = APIRouter(prefix="/offers", tags=["offers"])


@router.post("", response_model=OfferOut)
def create_offer_route(
    payload: OfferCreateIn,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return create_offer(
        db=db,
        user=current_user,
        title=payload.title,
        description=payload.description,
        category=payload.category,
        value_cop=payload.value_cop,
        duration_hours=payload.duration_hours,
        is_on_site=payload.is_on_site,
        date_time=payload.date_time,
    )


@router.get("/my", response_model=list[OfferOut])
def my_offers(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return get_my_offers(db, current_user)


@router.get("/{offer_id}", response_model=OfferOut)
def offer_detail(
    offer_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return get_offer_detail(db, current_user, offer_id)
