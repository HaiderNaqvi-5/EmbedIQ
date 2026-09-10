"""
Comprehensive SSRF Guard Tests (PRD AT-002)
=============================================
Tests for app/services/ssrf_guard.py covering all blocked CIDR ranges,
hostname suffixes, scheme validation, credential rejection, and DNS resolution.
"""

import pytest
from app.services.ssrf_guard import validate_url, validate_ip


# ---------------------------------------------------------------------------
# validate_ip() unit tests
# ---------------------------------------------------------------------------

class TestValidateIP:
    def test_loopback_v4_rejected(self):
        assert validate_ip("127.0.0.1") is False
        assert validate_ip("127.0.0.255") is False
        assert validate_ip("127.255.255.255") is False

    def test_loopback_v6_rejected(self):
        assert validate_ip("::1") is False

    def test_rfc1918_10_rejected(self):
        assert validate_ip("10.0.0.1") is False
        assert validate_ip("10.255.255.255") is False

    def test_rfc1918_172_rejected(self):
        assert validate_ip("172.16.0.1") is False
        assert validate_ip("172.31.255.255") is False

    def test_rfc1918_192_rejected(self):
        assert validate_ip("192.168.0.1") is False
        assert validate_ip("192.168.255.255") is False

    def test_link_local_v4_rejected(self):
        assert validate_ip("169.254.0.1") is False
        assert validate_ip("169.254.255.255") is False

    def test_link_local_v6_rejected(self):
        assert validate_ip("fe80::1") is False

    def test_cloud_metadata_rejected(self):
        assert validate_ip("169.254.169.254") is False

    def test_ipv6_ula_rejected(self):
        assert validate_ip("fc00::1") is False
        assert validate_ip("fd00::1") is False

    def test_multicast_v4_rejected(self):
        assert validate_ip("224.0.0.1") is False
        assert validate_ip("239.255.255.255") is False

    def test_multicast_v6_rejected(self):
        assert validate_ip("ff02::1") is False

    def test_unspecified_v4_rejected(self):
        assert validate_ip("0.0.0.0") is False

    def test_invalid_ip_returns_false(self):
        assert validate_ip("not-an-ip") is False
        assert validate_ip("") is False

    def test_public_ip_accepted(self):
        assert validate_ip("8.8.8.8") is True
        assert validate_ip("1.1.1.1") is True
        assert validate_ip("203.0.113.1") is True


# ---------------------------------------------------------------------------
# validate_url() — scheme validation
# ---------------------------------------------------------------------------

class TestURLSchemeValidation:
    def test_ftp_rejected(self):
        with pytest.raises(ValueError, match="scheme"):
            validate_url("ftp://files.example.com/data")

    def test_file_rejected(self):
        with pytest.raises(ValueError, match="scheme"):
            validate_url("file:///etc/passwd")

    def test_data_rejected(self):
        with pytest.raises(ValueError, match="scheme"):
            validate_url("data:text/html,<script>alert(1)</script>")

    def test_javascript_rejected(self):
        with pytest.raises(ValueError, match="scheme"):
            validate_url("javascript:alert(1)")

    def test_mailto_rejected(self):
        with pytest.raises(ValueError, match="scheme"):
            validate_url("mailto:user@example.com")

    def test_http_accepted(self):
        result = validate_url("http://example.com")
        assert result.startswith("http://")

    def test_https_accepted(self):
        result = validate_url("https://example.com")
        assert result.startswith("https://")


# ---------------------------------------------------------------------------
# validate_url() — embedded credentials
# ---------------------------------------------------------------------------

class TestCredentialRejection:
    def test_basic_auth_rejected(self):
        with pytest.raises(ValueError, match="credentials"):
            validate_url("http://user:pass@example.com/")

    def test_username_only_rejected(self):
        with pytest.raises(ValueError, match="credentials"):
            validate_url("http://admin@example.com/")

    def test_password_only_rejected(self):
        with pytest.raises(ValueError, match="credentials"):
            validate_url("http://:secret@example.com/")


# ---------------------------------------------------------------------------
# validate_url() — hostname suffix blocking
# ---------------------------------------------------------------------------

class TestHostnameSuffixBlocking:
    def test_internal_suffix_rejected(self):
        with pytest.raises(ValueError, match="blocked"):
            validate_url("http://backend.internal/api")

    def test_local_suffix_rejected(self):
        with pytest.raises(ValueError, match="blocked"):
            validate_url("http://service.local/health")

    def test_cluster_local_rejected(self):
        with pytest.raises(ValueError, match="blocked"):
            validate_url("http://pod.cluster.local:8080/")

    def test_localhost_suffix_rejected(self):
        with pytest.raises(ValueError, match="blocked"):
            validate_url("http://myhost.localhost/")

    def test_cloud_metadata_hostname_rejected(self):
        with pytest.raises(ValueError, match="metadata"):
            validate_url("http://metadata.google.internal/latest/meta-data/")


# ---------------------------------------------------------------------------
# validate_url() — DNS resolution blocking
# ---------------------------------------------------------------------------

class TestDNSResolutionBlocking:
    def test_localhost_ip_rejected(self):
        with pytest.raises(ValueError, match="blocked"):
            validate_url("http://127.0.0.1:8080/admin")

    def test_private_ip_rejected(self):
        with pytest.raises(ValueError, match="blocked"):
            validate_url("http://192.168.1.1/internal")

    def test_cloud_metadata_ip_rejected(self):
        with pytest.raises(ValueError, match="blocked"):
            validate_url("http://169.254.169.254/latest/meta-data/")

    def test_nonexistent_domain_fails(self):
        with pytest.raises(ValueError, match="DNS resolution"):
            validate_url("http://this-domain-definitely-does-not-exist-xyz123.com/")


# ---------------------------------------------------------------------------
# validate_url() — valid public URLs
# ---------------------------------------------------------------------------

class TestValidPublicURLs:
    def test_example_com_passes(self):
        result = validate_url("https://example.com")
        assert result.startswith("https://")

    def test_httpbin_passes(self):
        result = validate_url("https://httpbin.org/get")
        assert result.startswith("https://")

    def test_fragment_stripped(self):
        result = validate_url("https://example.com/page#section")
        assert "#" not in result

    def test_malformed_url_rejected(self):
        with pytest.raises(ValueError):
            validate_url("not-a-url")

    def test_empty_hostname_rejected(self):
        with pytest.raises(ValueError, match="hostname"):
            validate_url("https://")


# ---------------------------------------------------------------------------
# validate_url() — redirect target re-validation scenario
# ---------------------------------------------------------------------------

class TestRedirectReValidation:
    def test_redirect_to_private_ip_would_fail(self):
        """Simulates validating a redirect destination that resolves to a private IP."""
        with pytest.raises(ValueError, match="blocked"):
            validate_url("http://10.0.0.1/redirected")
