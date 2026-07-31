"""Tests for app.modules.progress_tracking.service — the mastery engine's
pure functions directly, plus an integration path proving the
curriculum/code_review hooks actually write through (same pattern as
test_curriculum_service.py)."""

from datetime import date

import pytest

from app.modules.auth import service as auth_service
from app.modules.curriculum import service as curriculum_service
from app.modules.progress_tracking import service as progress_service
from app.modules.progress_tracking.exceptions import QuizAnswerMismatchError, QuizNotAvailableError
from app.modules.projects import service as projects_service
from tests.taxonomy_fixtures import create_concept


class TestApplyConfidence:
    def test_positive_signal_approaches_one_asymptotically(self):
        confidence = progress_service._apply_confidence(0.5, "positive", 0.3)
        assert confidence == pytest.approx(0.5 + 0.3 * 0.5)
        assert 0 <= confidence <= 1

    def test_negative_signal_approaches_zero_asymptotically(self):
        confidence = progress_service._apply_confidence(0.5, "negative", 0.3)
        assert confidence == pytest.approx(0.5 - 0.3 * 0.5)
        assert 0 <= confidence <= 1

    def test_stays_in_bounds_at_the_extremes(self):
        assert progress_service._apply_confidence(1.0, "positive", 0.9) == pytest.approx(1.0)
        assert progress_service._apply_confidence(0.0, "negative", 0.9) == pytest.approx(0.0)


class TestResolutionStateMachine:
    def test_climbs_detected_to_mastered_as_confidence_rises(self):
        assert progress_service._next_resolution_state("detected", 0.0) == "detected"
        assert progress_service._next_resolution_state("detected", 0.2) == "practicing"
        assert progress_service._next_resolution_state("practicing", 0.5) == "improving"
        assert progress_service._next_resolution_state("improving", 0.8) == "mastered"

    def test_regression_from_mastered_lands_in_monitor_not_practicing(self):
        assert progress_service._next_resolution_state("mastered", 0.3) == "monitor"

    def test_monitor_can_recover_back_to_mastered(self):
        assert progress_service._next_resolution_state("monitor", 0.9) == "mastered"


class TestComputeStreaks:
    def test_no_activity_is_zero_and_zero(self):
        assert progress_service._compute_streaks([], date(2026, 7, 30)) == (0, 0)

    def test_consecutive_days_ending_today(self):
        dates = [date(2026, 7, 28), date(2026, 7, 29), date(2026, 7, 30)]
        current, longest = progress_service._compute_streaks(dates, date(2026, 7, 30))
        assert (current, longest) == (3, 3)

    def test_gap_breaks_current_streak_but_not_longest(self):
        dates = [date(2026, 7, 20), date(2026, 7, 21), date(2026, 7, 22), date(2026, 7, 30)]
        current, longest = progress_service._compute_streaks(dates, date(2026, 7, 30))
        assert (current, longest) == (1, 3)

    def test_streak_survives_not_having_logged_in_yet_today(self):
        # Last active yesterday — still an unbroken streak as of "now",
        # it only breaks once a full day passes with no activity at all.
        dates = [date(2026, 7, 29)]
        current, _ = progress_service._compute_streaks(dates, date(2026, 7, 30))
        assert current == 1


async def _make_user_and_project(db, email: str):
    user = await auth_service.register_user(db, email, "hunter22222", "Owner")
    project = await projects_service.create_project(db, user.id, "Test Project", None)
    return user, project


class TestMilestoneCompletionHook:
    async def test_completing_a_milestone_creates_mastery_evidence_and_activity(self, db_session):
        user, project = await _make_user_and_project(db_session, "progress1@example.com")
        await create_concept(db_session, "python.variables", severity="foundational")
        await db_session.commit()

        roadmap = await curriculum_service.generate_or_regenerate_roadmap(
            db_session,
            project_id=project.id,
            stack="python",
            stack_version="3.12",
            experience_level="beginner",
        )
        milestone = roadmap.milestones[0]

        await curriculum_service.update_milestone_status(
            db_session, project.id, milestone.id, "in_progress"
        )
        await curriculum_service.update_milestone_status(
            db_session, project.id, milestone.id, "completed"
        )

        profiles = await progress_service.list_mastery_profiles(db_session, user.id)
        assert len(profiles) == 1
        assert profiles[0].concept_id == "python.variables"
        assert profiles[0].confidence_score > 0
        assert profiles[0].resolution_state == "practicing"

        dashboard = await progress_service.get_dashboard(db_session, user.id)
        assert dashboard["milestones_completed"] == 1
        assert dashboard["streak"]["current_streak_days"] == 1


class TestQuizSubmission:
    async def test_submit_quiz_scores_and_records_evidence(self, db_session, monkeypatch):
        user, project = await _make_user_and_project(db_session, "progress2@example.com")
        await create_concept(db_session, "python.variables", severity="foundational")
        await db_session.commit()

        roadmap = await curriculum_service.generate_or_regenerate_roadmap(
            db_session,
            project_id=project.id,
            stack="python",
            stack_version="3.12",
            experience_level="beginner",
        )
        milestone = roadmap.milestones[0]
        milestone.lesson_content = {
            "explanation": "x",
            "key_points": [],
            "exercises": [],
            "quiz": [
                {"question": "q1", "options": ["a", "b"], "correct_index": 0, "explanation": ""},
                {"question": "q2", "options": ["a", "b"], "correct_index": 1, "explanation": ""},
            ],
        }
        await db_session.commit()

        attempt = await progress_service.submit_quiz(
            db_session,
            user_id=user.id,
            project_id=project.id,
            milestone_id=milestone.id,
            answers=[0, 0],
        )
        assert attempt.score == 1
        assert attempt.total == 2

        profiles = await progress_service.list_mastery_profiles(db_session, user.id)
        assert profiles[0].concept_id == "python.variables"

    async def test_wrong_answer_count_is_rejected(self, db_session):
        user, project = await _make_user_and_project(db_session, "progress3@example.com")
        await create_concept(db_session, "python.variables", severity="foundational")
        await db_session.commit()
        roadmap = await curriculum_service.generate_or_regenerate_roadmap(
            db_session,
            project_id=project.id,
            stack="python",
            stack_version="3.12",
            experience_level="beginner",
        )
        milestone = roadmap.milestones[0]
        milestone.lesson_content = {
            "explanation": "x",
            "key_points": [],
            "exercises": [],
            "quiz": [
                {"question": "q1", "options": ["a", "b"], "correct_index": 0, "explanation": ""}
            ],
        }
        await db_session.commit()

        with pytest.raises(QuizAnswerMismatchError):
            await progress_service.submit_quiz(
                db_session,
                user_id=user.id,
                project_id=project.id,
                milestone_id=milestone.id,
                answers=[0, 1],
            )

    async def test_quiz_not_available_before_content_generated(self, db_session):
        user, project = await _make_user_and_project(db_session, "progress4@example.com")
        await create_concept(db_session, "python.variables", severity="foundational")
        await db_session.commit()
        roadmap = await curriculum_service.generate_or_regenerate_roadmap(
            db_session,
            project_id=project.id,
            stack="python",
            stack_version="3.12",
            experience_level="beginner",
        )
        milestone = roadmap.milestones[0]

        with pytest.raises(QuizNotAvailableError):
            await progress_service.submit_quiz(
                db_session,
                user_id=user.id,
                project_id=project.id,
                milestone_id=milestone.id,
                answers=[0],
            )
