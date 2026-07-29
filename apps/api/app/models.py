"""Model registry.

Alembic's autogenerate only sees tables whose model classes have been
imported somewhere before `Base.metadata` is inspected. Rather than have
alembic/env.py know about every module individually, each module registers
its models here — one import per module, side-effect only.
"""

from app.modules.auth import models as auth_models  # noqa: F401
