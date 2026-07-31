"""Seeds the `concepts`/`concept_prerequisites` tables from the curated
YAML taxonomy under packages/taxonomy-data/concepts/.

Run manually (`uv run python scripts/seed_taxonomy.py`) after authoring
or editing a taxonomy file, or in CI/deployment setup — deliberately
NOT run automatically on app startup, since this is curated content a
human authors and reviews (ARCHITECTURE.md: "the LLM never modifies it
directly"), not implicit runtime magic.
"""

import asyncio
import sys
from pathlib import Path

from app.core.config import get_settings
from app.core.database import async_session_factory
from app.modules.taxonomy.service import load_concepts_from_yaml, sync_concepts_for_stack


async def _seed_all(data_dir: Path) -> None:
    yaml_files = sorted(data_dir.glob("*.yaml"))
    if not yaml_files:
        print(f"No taxonomy YAML files found under {data_dir}", file=sys.stderr)
        return

    async with async_session_factory() as db:
        for path in yaml_files:
            parsed = load_concepts_from_yaml(path)
            await sync_concepts_for_stack(db, parsed)
            print(f"Seeded {len(parsed.concepts)} concept(s) for {parsed.stack} {parsed.stack_version} ({path.name})")


def main() -> None:
    settings = get_settings()
    data_dir = Path(settings.taxonomy_data_dir)
    asyncio.run(_seed_all(data_dir))


if __name__ == "__main__":
    main()
