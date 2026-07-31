"""Shared object storage client (uploaded files, and — once the worker
fetches them — raw GitHub/website content). Same lazy-shared-client
shape as app/core/database.py and app/core/redis.py: constructing this
never requires the backend (MinIO/S3, or the local directory) to
already exist.
"""

from functools import lru_cache

from object_storage import LocalObjectStorage, ObjectStorage, S3ObjectStorage

from app.core.config import get_settings


@lru_cache
def _build_storage() -> ObjectStorage:
    settings = get_settings()
    if settings.object_storage_backend == "s3":
        return S3ObjectStorage(
            bucket=settings.object_storage_bucket,
            region=settings.object_storage_region,
            endpoint_url=settings.object_storage_endpoint_url,
            access_key_id=settings.object_storage_access_key_id,
            secret_access_key=settings.object_storage_secret_access_key,
        )
    return LocalObjectStorage(settings.object_storage_local_path)


async def get_storage() -> ObjectStorage:
    return _build_storage()
