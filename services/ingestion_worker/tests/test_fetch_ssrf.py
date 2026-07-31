"""Unit tests for pipeline.fetch's SSRF host validation.

Only exercises the deterministic, network-free cases (loopback/private/
link-local addresses that resolve without any real DNS lookup, or via
the local hosts file) — a "does a real public domain resolve" test
would depend on this environment actually having outbound network
access, which isn't guaranteed and isn't the security property that
matters here anyway. What matters is that private targets are blocked.
"""

import pytest

from pipeline.errors import PermanentIngestionError
from pipeline.fetch import _validate_host_resolves_to_public_ip


class TestValidateHostResolvesToPublicIp:
    @pytest.mark.parametrize(
        "host",
        [
            "127.0.0.1",
            "localhost",
            "10.0.0.1",
            "192.168.1.1",
            "169.254.169.254",  # cloud metadata endpoint — a classic SSRF target
            "::1",
        ],
    )
    async def test_blocks_private_and_loopback_targets(self, host):
        with pytest.raises(PermanentIngestionError) as exc_info:
            await _validate_host_resolves_to_public_ip(host)
        assert exc_info.value.error_code == "ssrf_blocked"

    async def test_unresolvable_host_raises_permanent_error(self):
        with pytest.raises(PermanentIngestionError) as exc_info:
            await _validate_host_resolves_to_public_ip("this-host-does-not-exist.invalid")
        assert exc_info.value.error_code == "dns_resolution_failed"
