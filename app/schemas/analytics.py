from pydantic import BaseModel, ConfigDict
from typing import Optional, Dict


class OfferAcceptanceRateOut(BaseModel):
    """BQ3: Acceptance rate per offer."""
    model_config = ConfigDict(from_attributes=True)

    offer_id: int
    offer_title: str
    category: Optional[str]
    total_applications: int
    accepted: int
    rejected: int
    pending: int
    acceptance_rate: float


class OverallInsightsOut(BaseModel):
    """Smart Offer Insights – aggregated KPIs."""
    total_offers: int
    total_applications: int
    overall_acceptance_rate: float
    most_popular_offer: Optional[str]
    most_popular_offer_applications: int
    least_popular_offer: Optional[str]
    least_popular_offer_applications: int
    avg_applications_per_offer: float


class GpaByOfferOut(BaseModel):
    """BQ2: Average GPA of applicants per offer."""
    model_config = ConfigDict(from_attributes=True)

    offer_id: int
    offer_title: str
    category: Optional[str]
    total_applicants: int
    average_gpa: float
    min_gpa: float
    max_gpa: float


class TopApplicantOut(BaseModel):
    """Top Applicants Leaderboard – ranked by GPA."""
    model_config = ConfigDict(from_attributes=True)

    applicant_name: str
    career: str
    semester: int
    gpa: float
    total_applications: int
    offers_applied: list[str]
    status_summary: Dict[str, int]


class GpaHighRateOut(BaseModel):
    """
    BQ9: Percentage of applicants per offer with GPA >= 4.0
    Functional scenario: Staff opens analytics -> system computes the fraction
    of high-GPA applicants per offer -> helps prioritise where top talent concentrates.
    Quality scenario (Performance): Response time < 2 s for up to 500 offers.
    """
    model_config = ConfigDict(from_attributes=True)

    offer_id: int
    offer_title: str
    category: Optional[str]
    total_applicants: int
    high_gpa_count: int
    high_gpa_percentage: float


class ApplicationsPerSemesterOut(BaseModel):
    """
    BQ10: Average number of applications submitted per student, grouped by semester.
    Functional scenario: Staff opens analytics -> system groups applications by student
    semester, counts unique students and total applications per group -> returns average
    applications per student for each semester level.
    Quality scenario (Performance): Response time < 2 s for up to 500 applications.
    """
    model_config = ConfigDict(from_attributes=True)

    semester: int
    total_applications: int
    unique_students: int
    avg_applications_per_student: float


# ── BQ13: Status Distribution ─────────────────────────────────────────────────

class StatusCountOut(BaseModel):
    """One status bucket (pending | accepted | rejected) with count and percentage."""
    status: str
    count: int
    percentage: float


class OfferStatusBreakdownOut(BaseModel):
    """Per-offer breakdown of application statuses for BQ13."""
    offer_id: int
    offer_title: str
    category: Optional[str]
    pending: int
    accepted: int
    rejected: int
    total: int


class StatusDistributionOut(BaseModel):
    """
    BQ13: Distribution of application statuses across all offers this semester.
    Functional scenario: Staff opens analytics -> system aggregates pending/accepted/rejected
    counts for the current academic semester -> shows donut chart + per-offer breakdown.
    Quality scenario (Performance): Response time < 2 s for up to 500 applications.
    """
    semester: str
    total_applications: int
    distribution: list[StatusCountOut]
    per_offer: list[OfferStatusBreakdownOut]
