"""Object storage client for the worker — mirrors apps/api/app/core/storage.py's
backend-selection logic (both read the same OBJECT_STORAGE_* shape of
env vars) without importing it, per the extraction-boundary rule in
settings.py.
"""

from functools import lru_cache

from object_storage import LocalObjectStorage, ObjectStorage, S3ObjectStorage

from settings import config


@lru_cache
def get_storage() -> ObjectStorage:
    if config.object_storage_backend == "s3":
        return S3ObjectStorage(
            bucket=config.object_storage_bucket,
            region=config.object_storage_region,
            endpoint_url=config.object_storage_endpoint_url,
            access_key_id=config.object_storage_access_key_id,
            secret_access_key=config.object_storage_secret_access_key,
        )
    return LocalObjectStorage(config.object_storage_local_path)
