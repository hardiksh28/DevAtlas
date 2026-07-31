"""S3-compatible ObjectStorage — the production backend, and also what
local dev talks to via the docker-compose `minio` service (S3-API-
compatible; only `endpoint_url` differs from real AWS S3, which is what
makes local dev a faithful rehearsal of the production path instead of
a different code path entirely).

A fresh client per call rather than one held open for the instance's
lifetime — aioboto3 clients are async context managers tied to the
session's connector, and this keeps the interface trivially safe to
share across concurrent arq jobs without a pooling story to get wrong.
"""

from botocore.config import Config
from botocore.exceptions import ClientError

import aioboto3


class S3ObjectStorage:
    def __init__(
        self,
        *,
        bucket: str,
        region: str,
        endpoint_url: str | None = None,
        access_key_id: str | None = None,
        secret_access_key: str | None = None,
    ) -> None:
        self._bucket = bucket
        self._session = aioboto3.Session()
        self._client_kwargs = {
            "region_name": region,
            "endpoint_url": endpoint_url,
            "aws_access_key_id": access_key_id,
            "aws_secret_access_key": secret_access_key,
            # Transient network errors are exactly the ingestion
            # pipeline's dominant failure mode (large files, many small
            # GitHub/website fetches) — retry inside the S3 client
            # rather than making every call site reimplement backoff.
            "config": Config(retries={"max_attempts": 3, "mode": "standard"}),
        }

    async def put(self, key: str, data: bytes, content_type: str) -> None:
        async with self._session.client("s3", **self._client_kwargs) as s3:
            await s3.put_object(Bucket=self._bucket, Key=key, Body=data, ContentType=content_type)

    async def get(self, key: str) -> bytes:
        async with self._session.client("s3", **self._client_kwargs) as s3:
            response = await s3.get_object(Bucket=self._bucket, Key=key)
            async with response["Body"] as stream:
                return await stream.read()

    async def delete(self, key: str) -> None:
        async with self._session.client("s3", **self._client_kwargs) as s3:
            await s3.delete_object(Bucket=self._bucket, Key=key)

    async def exists(self, key: str) -> bool:
        async with self._session.client("s3", **self._client_kwargs) as s3:
            try:
                await s3.head_object(Bucket=self._bucket, Key=key)
            except ClientError as exc:
                if exc.response.get("Error", {}).get("Code") in ("404", "NoSuchKey"):
                    return False
                raise
            return True
