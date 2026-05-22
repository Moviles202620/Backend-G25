from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.dependencies import get_db
from app.models.offer import Offer
from app.models.application import Application
from app.schemas.analytics import OfferAcceptanceRateOut, OverallInsightsOut, GpaByOfferOut, TopApplicantOut, GpaHighRateOut, ApplicationsPerSemesterOut, OfferLifecycleOut
from app.services.analytics_service import (
    get_acceptance_rate_by_offer,
    get_overall_insights,
    get_gpa_by_offer,
    get_top_applicants,
    get_gpa_high_rate,
    get_applications_per_semester,
)

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/time-to-first-application")
def time_to_first_application(db: Session = Depends(get_db)):
    """BQ7 (Santiago Reyes): Average days between job offer publication and first application.

    Iterates every offer, finds its earliest application, computes the delta in days,
    and returns the mean across all offers that have at least one application.
    """
    offers = db.query(Offer).all()

    total_days = 0.0
    offers_with_apps = 0

    for offer in offers:
        first_app = (
            db.query(Application)
            .filter(Application.offer_id == offer.id)
            .order_by(Application.created_at.asc())
            .first()
        )

        if first_app is None:
            continue

        if offer.created_at is None or first_app.created_at is None:
            continue

        # Normalize to naive datetimes so subtraction always works
        offer_ts = offer.created_at.replace(tzinfo=None)
        app_ts = first_app.created_at.replace(tzinfo=None)

        delta_seconds = abs((app_ts - offer_ts).total_seconds())
        total_days += delta_seconds / 86400.0
        offers_with_apps += 1

    avg_days = round(total_days / offers_with_apps, 2) if offers_with_apps > 0 else 0.0

    return {
        "average_days_to_first_application": avg_days,
        "offers_with_applications": offers_with_apps,
        "total_offers": len(offers),
    }


@router.get("/offer-lifecycle", response_model=OfferLifecycleOut)
def offer_lifecycle(db: Session = Depends(get_db)):
    """BQ11 (Santiago Reyes): Offer lifecycle duration statistics.

    Queries closed offers (closed_at IS NOT NULL), computes (closed_at - created_at).days
    for each, and returns average, min, max days and total count.
    """
    offers = db.query(Offer).filter(Offer.closed_at.isnot(None)).all()

    if not offers:
        return OfferLifecycleOut(average_days=0.0, min_days=0, max_days=0, total_offers=0)

    durations = []
    for offer in offers:
        closed = offer.closed_at.replace(tzinfo=None)
        created = offer.created_at.replace(tzinfo=None)
        days = abs((closed - created).days)
        durations.append(days)

    return OfferLifecycleOut(
        average_days=round(sum(durations) / len(durations), 2),
        min_days=min(durations),
        max_days=max(durations),
        total_offers=len(durations),
    )


@router.get("/acceptance-rate", response_model=list[OfferAcceptanceRateOut])
def acceptance_rate(db: Session = Depends(get_db)):
    """
    BQ3 – Returns the acceptance rate of applications for each offer.
    """
    return get_acceptance_rate_by_offer(db)


@router.get("/insights", response_model=OverallInsightsOut)
def insights(db: Session = Depends(get_db)):
    """
    Smart Offer Insights – aggregated KPIs: most/least popular offer,
    overall acceptance rate, average applications per offer.
    """
    return get_overall_insights(db)


@router.get("/gpa-by-offer", response_model=list[GpaByOfferOut])
def gpa_by_offer(db: Session = Depends(get_db)):
    """
    BQ2 – Returns the average GPA of applicants per job offer.
    Only includes offers that have at least one application.
    """
    return get_gpa_by_offer(db)


@router.get("/top-applicants", response_model=list[TopApplicantOut])
def top_applicants(
    limit: int = Query(default=10, ge=1, le=50),
    db: Session = Depends(get_db),
):
    """
    Top Applicants Leaderboard – returns the highest-GPA applicants across all offers.
    """
    return get_top_applicants(db, limit=limit)


@router.get("/gpa-high-rate", response_model=list[GpaHighRateOut])
def gpa_high_rate(db: Session = Depends(get_db)):
    """
    BQ9 (David Hernandez) – Percentage of applicants with GPA >= 4.0 per offer.
    Helps staff identify which offers attract top-performing students.
    """
    return get_gpa_high_rate(db)


@router.get("/applications-per-semester", response_model=list[ApplicationsPerSemesterOut])
def applications_per_semester(db: Session = Depends(get_db)):
    """
    BQ10 (Guillermo Hernández) – Average applications per student grouped by semester.
    Answers: how many applications does each student submit on average per semester?
    Helps the institution understand engagement patterns across academic stages.
    """
    return get_applications_per_semester(db)
