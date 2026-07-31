"""SSRF-safe HTTP fetch — the one place this pipeline makes an outbound
request to a URL that ultimately traces back to something a user typed
(a GitHub repo URL, a documentation website URL, and every link
discovered while crawling one).

apps/api/app/modules/knowledge/validation.py already rejects obviously
unsafe hosts at submission time, but that check is necessarily cheap
(no DNS resolution in a request handler) and happens once, before any
redirect chain exists. This is the real enforcement point: it resolves
and validates the IP of *every* hop — the root URL, every redirect
Location, and (for website crawls) every discovered link — immediately
before each individual request, which is what actually defeats DNS
rebinding (a hostname can resolve to a public IP when submitted and a
private one moments later, or a redirect can point anywhere).
"""

import asyncio
import ipaddress
import socket
from urllib.parse import urljoin, urlparse

import httpx

from pipeline.errors import PermanentIngestionError, RetryableIngestionError

_MAX_REDIRECTS = 5
USER_AGENT = "DevAtlasIngestionBot/1.0 (+documentation ingestion; see project settings)"
_REDIRECT_CODES = (301, 302, 303, 307, 308)


async def _validate_host_resolves_to_public_ip(hostname: str) -> None:
    try:
        infos = await asyncio.to_thread(socket.getaddrinfo, hostname, None)
    except socket.gaierror as exc:
        raise PermanentIngestionError(
            f"Could not resolve host: {hostname}", error_code="dns_resolution_failed"
        ) from exc

    for info in infos:
        ip = ipaddress.ip_address(info[4][0])
        if not ip.is_global:
            raise PermanentIngestionError(
                f"Refusing to fetch '{hostname}': resolves to a non-public address ({ip}).",
                error_code="ssrf_blocked",
            )


async def safe_get(
    client: httpx.AsyncClient, url: str, *, max_bytes: int, headers: dict[str, str] | None = None
) -> bytes:
    """Fetches `url`, following redirects manually (never
    `follow_redirects=True`) so each hop gets its own host validation.
    Streams the response body, aborting the instant it exceeds
    `max_bytes` rather than buffering an unbounded body in memory."""
    current_url = url
    for _ in range(_MAX_REDIRECTS + 1):
        parsed = urlparse(current_url)
        if parsed.scheme not in ("http", "https"):
            raise PermanentIngestionError(
                f"Unsupported URL scheme: {parsed.scheme!r}", error_code="invalid_scheme"
            )
        if not parsed.hostname:
            raise PermanentIngestionError("URL is missing a host.", error_code="invalid_url")
        await _validate_host_resolves_to_public_ip(parsed.hostname)

        try:
            async with client.stream(
                "GET",
                current_url,
                headers={"User-Agent": USER_AGENT, **(headers or {})},
                follow_redirects=False,
            ) as response:
                if response.status_code in _REDIRECT_CODES:
                    location = response.headers.get("location")
                    if not location:
                        raise PermanentIngestionError(
                            "Redirect response had no Location header.", error_code="invalid_redirect"
                        )
                    current_url = urljoin(current_url, location)
                    continue
                if response.status_code == 404:
                    raise PermanentIngestionError(f"Not found: {current_url}", error_code="not_found")
                if response.status_code >= 500:
                    raise RetryableIngestionError(
                        f"Upstream error {response.status_code} for {current_url}",
                        error_code="upstream_error",
                    )
                if response.status_code in (403, 429):
                    # Rate-limited (GitHub API quota, crawled site's own
                    # rate limiting), not a permanent rejection — let
                    # arq's retry/backoff take over instead of failing
                    # the job outright on a response that will likely
                    # succeed on the next try.
                    raise RetryableIngestionError(
                        f"Rate limited ({response.status_code}) fetching {current_url}",
                        error_code="rate_limited",
                    )
                if response.status_code >= 400:
                    raise PermanentIngestionError(
                        f"HTTP {response.status_code} for {current_url}", error_code="http_error"
                    )

                chunks: list[bytes] = []
                total = 0
                async for chunk in response.aiter_bytes():
                    total += len(chunk)
                    if total > max_bytes:
                        raise PermanentIngestionError(
                            f"Response exceeded the {max_bytes}-byte limit: {current_url}",
                            error_code="response_too_large",
                        )
                    chunks.append(chunk)
                return b"".join(chunks)
        except httpx.TimeoutException as exc:
            raise RetryableIngestionError(
                f"Timed out fetching {current_url}", error_code="timeout"
            ) from exc
        except httpx.TransportError as exc:
            raise RetryableIngestionError(
                f"Network error fetching {current_url}: {exc}", error_code="network_error"
            ) from exc

    raise PermanentIngestionError(
        f"Too many redirects starting from {url}", error_code="too_many_redirects"
    )
