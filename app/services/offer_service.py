from sqlalchemy.orm import Session
from app.models.offer import Offer
from app.models.user import User
from app.utils.exceptions import NotFound, Forbidden


def create_offer(
    db: Session,
    user: User,
    title: str,
    description: str,
    category: str | None,
    value_cop: int,
    duration_hours: int,
    is_on_site: bool,
    date_time,
) -> Offer:
    offer = Offer(
        staff_id=user.id,
        title=title,
        description=description,
        category=category,
        value_cop=value_cop,
        duration_hours=duration_hours,
        is_on_site=is_on_site,
        date_time=date_time,
    )
    db.add(offer)
    db.commit()
    db.refresh(offer)
    return offer


def get_my_offers(db: Session, user: User) -> list[Offer]:
    return db.query(Offer).filter(Offer.staff_id == user.id).order_by(Offer.id.desc()).all()


def get_offer_detail(db: Session, user: User, offer_id: int) -> Offer:
    offer = db.query(Offer).filter(Offer.id == offer_id).first()
    if not offer:
        raise NotFound("Offer not found")
    if offer.staff_id != user.id:
        raise Forbidden("Not your offer")
    return offer
