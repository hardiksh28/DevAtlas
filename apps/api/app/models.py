"""Model registry.

Alembic's autogenerate only sees tables whose model classes have been
imported somewhere before `Base.metadata` is inspected. Rather than have
alembic/env.py know about every module individually, each module registers
its models here — one import per module, side-effect only.
"""

from app.modules.auth import models as auth_models  # noqa: F401
from app.modules.build_plan import models as build_plan_models  # noqa: F401
from app.modules.code_review import models as code_review_models  # noqa: F401
from app.modules.curriculum import models as curriculum_models  # noqa: F401
from app.modules.knowledge import models as knowledge_models  # noqa: F401
from app.modules.mentoring import models as mentoring_models  # noqa: F401
from app.modules.progress_tracking import models as progress_tracking_models  # noqa: F401
from app.modules.projects import models as projects_models  # noqa: F401
from app.modules.repo_ingestion import models as repo_ingestion_models  # noqa: F401
from app.modules.taxonomy import models as taxonomy_models  # noqa: F401
from app.modules.visuals import models as visuals_models  # noqa: F401
from app.modules.workspace import models as workspace_models  # noqa: F401
