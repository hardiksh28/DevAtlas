"""Lesson Engine — router.

Assembles personalized lessons from concept metadata + docs + learner profile.

This module is a stub: the route surface will grow as the module's
responsibilities (see docs/architecture/ARCHITECTURE.md, Section 3) are
implemented. Keeping an explicit, empty-but-real router per module from
day one means every module has an identical shape — new contributors
never have to guess where a given feature's routes should live.
"""
from fastapi import APIRouter

router = APIRouter(prefix="/v1/lessons", tags=["Lesson Engine"])
