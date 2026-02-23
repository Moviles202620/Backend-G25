from sqlalchemy.orm import Session
from app.models.application import Application, ApplicationStatus
from app.models.offer import Offer
from app.models.user import User
from app.utils.exceptions import NotFound, Forbidden


def _staff_offer_ids(db: Session, user: User) -> list[int]:
    rows = db.query(Offer.id).filter(Offer.staff_id == user.id).all()
    return [r[0] for r in rows]


def list_by_status(db: Session, user: User, status: ApplicationStatus) -> list[Application]:
    offer_ids = _staff_offer_ids(db, user)
    if not offer_ids:
        return []
    return (
        db.query(Application)
        .filter(Application.offer_id.in_(offer_ids), Application.status == status)
        .order_by(Application.id.desc())
        .all()
    )


def update_status(db: Session, user: User, application_id: int, new_status: ApplicationStatus) -> Application:
    app = db.query(Application).filter(Application.id == application_id).first()
    if not app:
        raise NotFound("Application not found")

    offer = db.query(Offer).filter(Offer.id == app.offer_id).first()
    if not offer:
        raise NotFound("Offer not found")
    if offer.staff_id != user.id:
        raise Forbidden("Not your application")

    app.status = new_status
    db.add(app)
    db.commit()
    db.refresh(app)
    return app
