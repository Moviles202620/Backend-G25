from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func as sql_func

from app.models.offer import Offer
from app.models.application import Application, ApplicationStatus
from app.models.user import User
from collections import defaultdict


def get_acceptance_rate_by_offer(db: Session) -> list[dict]:
    """
    BQ3 – Acceptance rate per offer.
    Uses a single joined query for performance (quality scenario: < 2 s).
    """
    rows = (
        db.query(
            Offer.id,
            Offer.title,
            Offer.category,
            sql_func.count(Application.id).label("total"),
            sql_func.count(
                sql_func.nullif(Application.status != ApplicationStatus.accepted, True)
            ).label("accepted"),
            sql_func.count(
                sql_func.nullif(Application.status != ApplicationStatus.rejected, True)
            ).label("rejected"),
            sql_func.count(
                sql_func.nullif(Application.status != ApplicationStatus.pending, True)
            ).label("pending"),
        )
        .outerjoin(Application, Application.offer_id == Offer.id)
        .group_by(Offer.id, Offer.title, Offer.category)
        .order_by(Offer.id.desc())
        .all()
    )

    results = []
    for row in rows:
        total = row.total
        accepted = row.accepted
        rate = round((accepted / total) * 100, 2) if total > 0 else 0.0
        results.append(
            {
                "offer_id": row.id,
                "offer_title": row.title,
                "category": row.category,
                "total_applications": total,
                "accepted": accepted,
                "rejected": row.rejected,
                "pending": row.pending,
                "acceptance_rate": rate,
            }
        )
    return results


def get_gpa_by_offer(db: Session) -> list[dict]:
    """
    BQ2 – Average GPA of applicants per offer.
    Uses a single joined query for performance (quality scenario: < 2 s).
    Only includes offers that have at least one application.
    """
    rows = (
        db.query(
            Offer.id,
            Offer.title,
            Offer.category,
            sql_func.count(Application.id).label("total"),
            sql_func.avg(Application.gpa).label("avg_gpa"),
            sql_func.min(Application.gpa).label("min_gpa"),
            sql_func.max(Application.gpa).label("max_gpa"),
        )
        .join(Application, Application.offer_id == Offer.id)
        .group_by(Offer.id, Offer.title, Offer.category)
        .order_by(sql_func.avg(Application.gpa).desc())
        .all()
    )

    results = []
    for row in rows:
        results.append(
            {
                "offer_id": row.id,
                "offer_title": row.title,
                "category": row.category,
                "total_applicants": row.total,
                "average_gpa": round(float(row.avg_gpa), 2),
                "min_gpa": round(float(row.min_gpa), 2),
                "max_gpa": round(float(row.max_gpa), 2),
            }
        )
    return results


def get_top_applicants(db: Session, limit: int = 10) -> list[dict]:
    """
    Top Applicants Leaderboard – ranks candidates by GPA across all offers.
    Functional scenario: Staff opens leaderboard -> system queries all applications,
    deduplicates by applicant name, ranks by GPA descending.
    """
    rows = (
        db.query(Application)
        .order_by(Application.gpa.desc())
        .all()
    )

    # Deduplicate by applicant_name, keeping the one with highest GPA first
    seen: dict[str, dict] = {}
    for app in rows:
        name = app.applicant_name
        if name not in seen:
            seen[name] = {
                "applicant_name": name,
                "career": app.career,
                "semester": app.semester,
                "gpa": app.gpa,
                "total_applications": 0,
                "offers_applied": [],
                "status_summary": {"accepted": 0, "rejected": 0, "pending": 0},
            }
        entry = seen[name]
        entry["total_applications"] += 1
        if app.offer_title not in entry["offers_applied"]:
            entry["offers_applied"].append(app.offer_title)
        entry["status_summary"][app.status.value] += 1

    ranked = sorted(seen.values(), key=lambda x: x["gpa"], reverse=True)
    return ranked[:limit]


def get_gpa_high_rate(db: Session) -> list[dict]:
    """
    BQ9 – Percentage of applicants with GPA >= 4.0 per offer.
    David Hernandez – Sprint 3
    """
    rows = (
        db.query(
            Offer.id,
            Offer.title,
            Offer.category,
            sql_func.count(Application.id).label("total"),
            sql_func.count(
                sql_func.nullif(Application.gpa < 4.0, True)
            ).label("high_gpa"),
        )
        .join(Application, Application.offer_id == Offer.id)
        .group_by(Offer.id, Offer.title, Offer.category)
        .order_by(
            sql_func.count(
                sql_func.nullif(Application.gpa < 4.0, True)
            ).desc()
        )
        .all()
    )

    results = []
    for row in rows:
        total = row.total or 0
        high = row.high_gpa or 0
        pct = round((high / total) * 100, 2) if total > 0 else 0.0
        results.append({
            "offer_id": row.id,
            "offer_title": row.title,
            "category": row.category,
            "total_applicants": total,
            "high_gpa_count": high,
            "high_gpa_percentage": pct,
        })
    return results


def get_applications_per_semester(db: Session) -> list[dict]:
    """
    BQ10 – Average applications per student grouped by semester.
    Guillermo Hernández – Sprint 3.
    Groups applications by the applicant's semester, counts total applications
    and unique students per group, then computes the average.
    """
    rows = (
        db.query(
            Application.semester,
            sql_func.count(Application.id).label("total_applications"),
            sql_func.count(sql_func.distinct(Application.applicant_name)).label("unique_students"),
        )
        .group_by(Application.semester)
        .order_by(Application.semester.asc())
        .all()
    )

    results = []
    for row in rows:
        avg = round(row.total_applications / row.unique_students, 2) if row.unique_students > 0 else 0.0
        results.append({
            "semester": row.semester,
            "total_applications": row.total_applications,
            "unique_students": row.unique_students,
            "avg_applications_per_student": avg,
        })
    return results


def _semester_range(semester: str | None) -> tuple[str, datetime, datetime]:
    """
    BQ13 helper – compute the academic semester label and its [start, end) range.

    Uniandes academic calendar:
      Semester 1: January 1 – June 30  (months 1-6)
      Semester 2: July 1 – December 31 (months 7-12)

    Args:
        semester: None (use server date) or a string like "2026-1" / "2026-2".

    Returns:
        (label, start_datetime, end_datetime) where the range is [start, end).
    """
    if semester is None:
        now = datetime.now()
        year = now.year
        sem = 1 if now.month <= 6 else 2
    else:
        try:
            parts = semester.split("-")
            year = int(parts[0])
            sem = int(parts[1])
        except (IndexError, ValueError):
            now = datetime.now()
            year = now.year
            sem = 1 if now.month <= 6 else 2

    label = f"{year}-{sem}"
    if sem == 1:
        start = datetime(year, 1, 1)
        end = datetime(year, 7, 1)
    else:
        start = datetime(year, 7, 1)
        end = datetime(year + 1, 1, 1)

    return label, start, end


def get_status_distribution(db: Session, semester: str | None = None) -> dict:
    """
    BQ13 (David Hernandez) – Distribution of application statuses this semester.

    Functional scenario: Staff opens analytics -> system aggregates pending/accepted/rejected
    counts for the current academic semester -> returns donut chart data + per-offer breakdown.
    Quality scenario (Performance): Response time < 2 s for up to 500 applications.
    """
    label, start, end = _semester_range(semester)

    # ── All applications in the semester window ───────────────────────────────
    apps = (
        db.query(Application)
        .join(Offer, Offer.id == Application.offer_id)
        .filter(Application.created_at >= start, Application.created_at < end)
        .all()
    )

    total = len(apps)

    # ── Global distribution ───────────────────────────────────────────────────
    counts: dict[str, int] = {"pending": 0, "accepted": 0, "rejected": 0}
    for app in apps:
        counts[app.status.value] += 1

    distribution = []
    for status_name in ("pending", "accepted", "rejected"):
        cnt = counts[status_name]
        pct = round((cnt / total) * 100, 1) if total > 0 else 0.0
        distribution.append({"status": status_name, "count": cnt, "percentage": pct})

    # ── Per-offer breakdown ───────────────────────────────────────────────────
    offer_buckets: dict[int, dict] = {}
    for app in apps:
        oid = app.offer_id
        if oid not in offer_buckets:
            offer_buckets[oid] = {
                "offer_id": oid,
                "offer_title": app.offer_title or "",
                "category": None,
                "pending": 0,
                "accepted": 0,
                "rejected": 0,
                "total": 0,
            }
        offer_buckets[oid][app.status.value] += 1
        offer_buckets[oid]["total"] += 1

    # Enrich with category from Offer table
    if offer_buckets:
        offer_rows = (
            db.query(Offer.id, Offer.category)
            .filter(Offer.id.in_(list(offer_buckets.keys())))
            .all()
        )
        for row in offer_rows:
            if row.id in offer_buckets:
                offer_buckets[row.id]["category"] = row.category

    per_offer = sorted(offer_buckets.values(), key=lambda x: x["total"], reverse=True)

    return {
        "semester": label,
        "total_applications": total,
        "distribution": distribution,
        "per_offer": per_offer,
    }


def get_staff_activity(db: Session, days: int = 30) -> list[dict]:
    """
    BQ17 (Guillermo Hernández) – Staff ranked by offer-creation rate in the last N days.

    Functional scenario: Staff opens the analytics leaderboard -> system counts offers
    created by each staff member within the last `days` days -> returns a ranked list
    so administrators can identify the most active offer publishers.
    Quality scenario (Performance): Response time < 2 s for up to 100 staff members.

    Algorithm:
      1. Load all users with role='staff'.
      2. Run two aggregation queries (recent window + all-time) using `.in_()` for
         bulk lookup — avoids N+1 queries.
      3. Merge into a ranked list sorted by offers_in_window descending.
    """
    staff = db.query(User).filter(User.role == "staff").all()
    if not staff:
        return []

    staff_ids = [s.id for s in staff]

    # Count offers created within the window
    cutoff = datetime.now() - timedelta(days=days)
    recent_rows = (
        db.query(
            Offer.staff_id,
            sql_func.count(Offer.id).label("cnt"),
        )
        .filter(Offer.staff_id.in_(staff_ids), Offer.created_at >= cutoff)
        .group_by(Offer.staff_id)
        .all()
    )
    recent_map: dict[int, int] = {r.staff_id: r.cnt for r in recent_rows}

    # Count all-time offers per staff
    total_rows = (
        db.query(
            Offer.staff_id,
            sql_func.count(Offer.id).label("cnt"),
        )
        .filter(Offer.staff_id.in_(staff_ids))
        .group_by(Offer.staff_id)
        .all()
    )
    total_map: dict[int, int] = {r.staff_id: r.cnt for r in total_rows}

    results = [
        {
            "staff_id": s.id,
            "staff_name": s.name,
            "department": s.department,
            "offers_in_window": recent_map.get(s.id, 0),
            "total_offers": total_map.get(s.id, 0),
        }
        for s in staff
    ]

    results.sort(key=lambda x: x["offers_in_window"], reverse=True)
    return results


def get_overall_insights(db: Session) -> dict:
    """
    Smart insights – aggregated KPIs across all offers.
    Functional scenario: single endpoint returns everything the dashboard needs.
    """
    offers = db.query(Offer).all()
    if not offers:
        return {
            "total_offers": 0,
            "total_applications": 0,
            "overall_acceptance_rate": 0.0,
            "most_popular_offer": None,
            "most_popular_offer_applications": 0,
            "least_popular_offer": None,
            "least_popular_offer_applications": 0,
            "avg_applications_per_offer": 0.0,
        }

    offer_ids = [o.id for o in offers]
    offer_map = {o.id: o.title for o in offers}

    app_counts = (
        db.query(
            Application.offer_id,
            sql_func.count(Application.id).label("total"),
            sql_func.count(
                sql_func.nullif(Application.status != ApplicationStatus.accepted, True)
            ).label("accepted"),
        )
        .filter(Application.offer_id.in_(offer_ids))
        .group_by(Application.offer_id)
        .all()
    )

    total_apps = 0
    total_accepted = 0
    counts_by_offer: dict[int, int] = {oid: 0 for oid in offer_ids}

    for row in app_counts:
        counts_by_offer[row.offer_id] = row.total
        total_apps += row.total
        total_accepted += row.accepted

    overall_rate = round((total_accepted / total_apps) * 100, 2) if total_apps > 0 else 0.0
    avg_apps = round(total_apps / len(offers), 2)

    most_popular_id = max(counts_by_offer, key=counts_by_offer.get)
    least_popular_id = min(counts_by_offer, key=counts_by_offer.get)

    return {
        "total_offers": len(offers),
        "total_applications": total_apps,
        "overall_acceptance_rate": overall_rate,
        "most_popular_offer": offer_map[most_popular_id],
        "most_popular_offer_applications": counts_by_offer[most_popular_id],
        "least_popular_offer": offer_map[least_popular_id],
        "least_popular_offer_applications": counts_by_offer[least_popular_id],
        "avg_applications_per_offer": avg_apps,
    }