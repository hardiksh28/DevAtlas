"""Progress & Weakness Tracking Service — service layer. Function-based,
`db` first arg — same convention as every other module.

Three things live here:

1. **The mastery engine** (`_apply_confidence` / `_next_resolution_state`)
   — a small, deterministic, non-LLM update rule. ARCHITECTURE.md is
   explicit that curriculum sequencing must stay deterministic; the same
   reasoning applies here — whether a concept is "mastered" must never
   depend on an LLM's mood, only on the structured evidence (quiz score,
   review score, milestone completion) other modules report in.

2. **Evidence/activity hooks** (`record_milestone_completion`,
   `record_review_evidence`) — the write side of ARCHITECTURE.md
   Section 4's "RE->>PT: Report concept evidence" data-flow edge.
   Called from curriculum.service.update_milestone_status and
   code_review.service.submit_review, inside their existing
   transaction (these functions flush but never commit — the caller's
   own `db.commit()` is what persists the evidence atomically with the
   state change that produced it).

3. **Reads** (`list_mastery_profiles`, `get_dashboard`, `submit_quiz`) —
   the analytics/API surface. `get_dashboard` deliberately reads
   curriculum's and code_review's models directly (never their
   service.py) to avoid a curriculum/code_review <-> progress_tracking
   import cycle, the same "read the shared model directly" convention
   mentoring.service and code_review.service already use for milestone
   lookups.
"""

import uuid
from collections import defaultdict
from datetime import UTC, date, datetime, timedelta
from itertools import pairwise

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.code_review.models import CodeReview
from app.modules.curriculum.models import Milestone, Roadmap
from app.modules.progress_tracking.exceptions import (
    MilestoneNotFoundError,
    QuizAnswerMismatchError,
    QuizNotAvailableError,
)
from app.modules.progress_tracking.models import (
    ActivityEvent,
    MasteryEvidence,
    MasteryProfile,
    QuizAttempt,
)
from app.modules.projects.models import Project

# --- Mastery engine tuning. Plain module constants, not Settings
# fields — same "no product signal yet that these need tuning without a
# deploy" reasoning as code_review.service's _MAX_COMMENTS_BY_LEVEL.
MASTERY_THRESHOLD = 0.75
IMPROVING_THRESHOLD = 0.4
POSITIVE_FRACTION_THRESHOLD = 0.6
MILESTONE_EVIDENCE_WEIGHT = 0.3
REVIEW_EVIDENCE_WEIGHT_SCALE = 0.3
QUIZ_EVIDENCE_WEIGHT_SCALE = 0.4

_DASHBOARD_LIST_LIMIT = 5
_ACTIVITY_CHART_DAYS = 30


def _now() -> datetime:
    return datetime.now(UTC)


def _apply_confidence(confidence: float, signal: str, weight: float) -> float:
    """Asymptotic update: positive evidence closes the gap to 1.0 by
    `weight`; negative evidence closes the gap to 0.0 by `weight`. Never
    leaves [0, 1] given confidence/weight already in [0, 1] — no
    clamping needed. Diminishing-returns-by-construction: a learner who's
    already at 0.9 needs the same *kind* of evidence to reach 0.95 that
    someone at 0.2 needed to reach 0.6, matching how mastery actually
    behaves (each of the last few percent is harder-won than the first)."""
    if signal == "positive":
        return confidence + weight * (1 - confidence)
    return confidence - weight * confidence


def _next_resolution_state(previous_state: str, confidence: float) -> str:
    """Reversible state machine — see models.py's RESOLUTION_STATES
    docstring. `monitor` is only reachable by regressing out of
    `mastered`, never on the way up."""
    was_mastered = previous_state in ("mastered", "monitor")
    if confidence >= MASTERY_THRESHOLD:
        return "mastered"
    if was_mastered:
        return "monitor"
    if confidence >= IMPROVING_THRESHOLD:
        return "improving"
    if previous_state == "detected" and confidence <= 0:
        return "detected"
    return "practicing"


def _evidence_signal_and_weight(fraction: float, weight_scale: float) -> tuple[str, float]:
    """Shared by quiz and review scoring: a fraction (0-1) becomes a
    signal + magnitude, scaled so a barely-passing/failing result moves
    confidence less than a clear pass/fail."""
    if fraction >= POSITIVE_FRACTION_THRESHOLD:
        return "positive", weight_scale * fraction
    return "negative", weight_scale * (1 - fraction)


async def _get_or_create_profile(db: AsyncSession, user_id: uuid.UUID, concept_id: str) -> MasteryProfile:
    result = await db.execute(
        select(MasteryProfile).where(
            MasteryProfile.user_id == user_id, MasteryProfile.concept_id == concept_id
        )
    )
    profile = result.scalar_one_or_none()
    if profile is None:
        profile = MasteryProfile(user_id=user_id, concept_id=concept_id)
        db.add(profile)
        await db.flush()
    return profile


async def _apply_evidence(
    db: AsyncSession,
    *,
    user_id: uuid.UUID,
    concept_id: str,
    source: str,
    signal: str,
    weight: float,
) -> MasteryProfile:
    profile = await _get_or_create_profile(db, user_id, concept_id)
    profile.confidence_score = _apply_confidence(profile.confidence_score, signal, weight)
    profile.resolution_state = _next_resolution_state(profile.resolution_state, profile.confidence_score)
    profile.updated_at = _now()
    db.add(MasteryEvidence(profile_id=profile.id, source=source, signal=signal, weight=weight))
    return profile


def _record_activity(
    db: AsyncSession,
    *,
    user_id: uuid.UUID,
    project_id: uuid.UUID | None,
    event_type: str,
    duration_seconds: int | None = None,
    metadata: dict | None = None,
) -> None:
    db.add(
        ActivityEvent(
            user_id=user_id,
            project_id=project_id,
            event_type=event_type,
            duration_seconds=duration_seconds,
            event_metadata=metadata or {},
        )
    )


# --- Public hooks: called from other modules' service layers, inside
# their own transaction (no commit here — see module docstring).


async def record_milestone_completion(
    db: AsyncSession,
    *,
    user_id: uuid.UUID,
    project_id: uuid.UUID,
    concept_id: str,
    duration_seconds: int | None,
) -> None:
    await _apply_evidence(
        db,
        user_id=user_id,
        concept_id=concept_id,
        source="milestone",
        signal="positive",
        weight=MILESTONE_EVIDENCE_WEIGHT,
    )
    _record_activity(
        db,
        user_id=user_id,
        project_id=project_id,
        event_type="milestone_completed",
        duration_seconds=duration_seconds,
    )


async def record_review_evidence(
    db: AsyncSession,
    *,
    user_id: uuid.UUID,
    project_id: uuid.UUID,
    milestone_id: uuid.UUID | None,
    overall_score: int,
) -> None:
    if milestone_id is not None:
        milestone = await db.get(Milestone, milestone_id)
        if milestone is not None:
            signal, weight = _evidence_signal_and_weight(
                overall_score / 100, REVIEW_EVIDENCE_WEIGHT_SCALE
            )
            await _apply_evidence(
                db,
                user_id=user_id,
                concept_id=milestone.concept_id,
                source="code_review",
                signal=signal,
                weight=weight,
            )
    _record_activity(
        db,
        user_id=user_id,
        project_id=project_id,
        event_type="code_review_submitted",
        metadata={"overall_score": overall_score},
    )


# --- Reads / API surface.


async def list_mastery_profiles(db: AsyncSession, user_id: uuid.UUID) -> list[MasteryProfile]:
    result = await db.execute(
        select(MasteryProfile)
        .where(MasteryProfile.user_id == user_id)
        .order_by(MasteryProfile.confidence_score)
    )
    return list(result.scalars().all())


async def _get_milestone_for_project(
    db: AsyncSession, project_id: uuid.UUID, milestone_id: uuid.UUID
) -> Milestone:
    # Same query shape as curriculum.service.get_milestone — copied
    # rather than imported, to avoid a curriculum.service <->
    # progress_tracking.service import cycle (curriculum.service already
    # imports this module for record_milestone_completion).
    result = await db.execute(
        select(Milestone)
        .join(Roadmap, Milestone.roadmap_id == Roadmap.id)
        .where(Milestone.id == milestone_id, Roadmap.project_id == project_id)
    )
    milestone = result.scalar_one_or_none()
    if milestone is None:
        raise MilestoneNotFoundError()
    return milestone


async def submit_quiz(
    db: AsyncSession,
    *,
    user_id: uuid.UUID,
    project_id: uuid.UUID,
    milestone_id: uuid.UUID,
    answers: list[int],
) -> QuizAttempt:
    milestone = await _get_milestone_for_project(db, project_id, milestone_id)
    quiz = (milestone.lesson_content or {}).get("quiz") or []
    if not quiz:
        raise QuizNotAvailableError()
    if len(answers) != len(quiz):
        raise QuizAnswerMismatchError()

    score = sum(1 for given, question in zip(answers, quiz) if given == question["correct_index"])
    total = len(quiz)

    attempt = QuizAttempt(user_id=user_id, milestone_id=milestone_id, score=score, total=total, answers=answers)
    db.add(attempt)
    await db.flush()

    signal, weight = _evidence_signal_and_weight(score / total, QUIZ_EVIDENCE_WEIGHT_SCALE)
    await _apply_evidence(
        db, user_id=user_id, concept_id=milestone.concept_id, source="quiz", signal=signal, weight=weight
    )
    _record_activity(
        db,
        user_id=user_id,
        project_id=project_id,
        event_type="quiz_submitted",
        metadata={"score": score, "total": total},
    )

    await db.commit()
    await db.refresh(attempt)
    return attempt


def _compute_streaks(activity_dates: list[date], today: date) -> tuple[int, int]:
    """Pure — see test_progress_tracking_service.py. `activity_dates` must
    be sorted ascending, distinct calendar dates (UTC — see
    ActivityEvent.occurred_at; a real per-user timezone is a later
    refinement, not something a streak needs to be useful today)."""
    if not activity_dates:
        return 0, 0

    longest = run = 1
    for previous, current in pairwise(activity_dates):
        run = run + 1 if (current - previous).days == 1 else 1
        longest = max(longest, run)

    date_set = set(activity_dates)
    cursor = today if today in date_set else today - timedelta(days=1)
    current_streak = 0
    while cursor in date_set:
        current_streak += 1
        cursor -= timedelta(days=1)

    return current_streak, longest


async def get_dashboard(db: AsyncSession, user_id: uuid.UUID) -> dict:
    events_result = await db.execute(
        select(ActivityEvent.occurred_at, ActivityEvent.duration_seconds)
        .where(ActivityEvent.user_id == user_id)
        .order_by(ActivityEvent.occurred_at)
    )
    by_day: dict[date, list[int]] = defaultdict(lambda: [0, 0])
    for occurred_at, duration_seconds in events_result.all():
        bucket = by_day[occurred_at.date()]
        bucket[0] += 1
        bucket[1] += duration_seconds or 0

    activity_dates = sorted(by_day)
    today = _now().date()
    current_streak, longest_streak = _compute_streaks(activity_dates, today)

    cutoff = today - timedelta(days=_ACTIVITY_CHART_DAYS - 1)
    activity_by_day = [
        {"activity_date": d, "event_count": counts[0], "duration_seconds": counts[1]}
        for d, counts in sorted(by_day.items())
        if d >= cutoff
    ]
    total_time_spent_seconds = sum(counts[1] for counts in by_day.values())

    milestones_completed = (
        await db.scalar(
            select(func.count())
            .select_from(Milestone)
            .join(Roadmap, Milestone.roadmap_id == Roadmap.id)
            .join(Project, Roadmap.project_id == Project.id)
            .where(Project.owner_id == user_id, Milestone.status == "completed")
        )
        or 0
    )

    quizzes_taken, avg_quiz_fraction = (
        await db.execute(
            select(func.count(QuizAttempt.id), func.avg(QuizAttempt.score * 1.0 / QuizAttempt.total)).where(
                QuizAttempt.user_id == user_id
            )
        )
    ).one()

    code_reviews_submitted, avg_review_score = (
        await db.execute(
            select(func.count(CodeReview.id), func.avg(CodeReview.overall_score))
            .join(Project, CodeReview.project_id == Project.id)
            .where(Project.owner_id == user_id)
        )
    ).one()

    profiles = await list_mastery_profiles(db, user_id)
    weak_concepts = [
        p for p in profiles if p.resolution_state in ("detected", "practicing", "monitor")
    ][:_DASHBOARD_LIST_LIMIT]
    strengths = sorted(
        (p for p in profiles if p.resolution_state == "mastered"),
        key=lambda p: p.confidence_score,
        reverse=True,
    )[:_DASHBOARD_LIST_LIMIT]

    return {
        "streak": {
            "current_streak_days": current_streak,
            "longest_streak_days": longest_streak,
            "last_active_date": activity_dates[-1] if activity_dates else None,
        },
        "milestones_completed": milestones_completed,
        "total_time_spent_seconds": total_time_spent_seconds,
        "quizzes_taken": quizzes_taken or 0,
        "average_quiz_score_pct": round(avg_quiz_fraction * 100, 1) if avg_quiz_fraction is not None else None,
        "code_reviews_submitted": code_reviews_submitted or 0,
        "average_review_score": round(avg_review_score, 1) if avg_review_score is not None else None,
        "weak_concepts": weak_concepts,
        "strengths": strengths,
        "activity_by_day": activity_by_day,
    }
