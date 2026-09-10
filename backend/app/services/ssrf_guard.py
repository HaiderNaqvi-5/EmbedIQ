"""
SSRF Guard — PRD Section 6.1.1

Validates every URL (and every redirect destination) before any network connection
is opened.  All checks are applied synchronously; the module has no I/O side-effects
so it can safely be called from async Celery workers and FastAPI request handlers.
"""

import ipaddress
import socket
from urllib.parse import urlparse

# ---------------------------------------------------------------------------
# Blocked CIDR ranges
# ---------------------------------------------------------------------------
_BLOCKED_NETWORKS: list[ipaddress.IPv4Network | ipaddress.IPv6Network] = [
    # Loopback
    ipaddress.ip_network("127.0.0.0/8"),
    ipaddress.ip_network("::1/128"),
    # RFC 1918 Private IPv4
    ipaddress.ip_network("10.0.0.0/8"),
    ipaddress.ip_network("172.16.0.0/12"),
    ipaddress.ip_network("192.168.0.0/16"),
    # Link-Local
    ipaddress.ip_network("169.254.0.0/16"),
    ipaddress.ip_network("fe80::/10"),
    # Cloud Metadata endpoint (also covered by link-local, but explicit)
    ipaddress.ip_network("169.254.169.254/32"),
    # IPv6 Unique Local
    ipaddress.ip_network("fc00::/7"),
    # Unspecified / Any
    ipaddress.ip_network("0.0.0.0/8"),
    # Multicast
    ipaddress.ip_network("224.0.0.0/4"),
    ipaddress.ip_network("ff00::/8"),
]

# Hostnames that must always be rejected regardless of IP resolution
_BLOCKED_HOSTNAME_SUFFIXES: tuple[str, ...] = (
    ".internal",
    ".local",
    ".cluster.local",
    ".localhost",
)

# Protocol whitelist
_ALLOWED_SCHEMES: frozenset[str] = frozenset({"http", "https"})


# ---------------------------------------------------------------------------
# Public helpers
# ---------------------------------------------------------------------------

def validate_ip(ip: str) -> bool:
    """Return True if *ip* is safe (not in any blocked CIDR range).

    Args:
        ip: A dotted-decimal IPv4 or colon-separated IPv6 address string.

    Returns:
        True when the IP is routable and not in a blocked range.
    """
    try:
        addr = ipaddress.ip_address(ip)
    except ValueError:
        return False

    for net in _BLOCKED_NETWORKS:
        if addr in net:
            return False
    return True


def validate_url(url: str) -> str:
    """Validate *url* against the SSRF policy and return the cleaned URL.

    Performs the following checks in order:
    1. Parses the URL and validates the scheme whitelist.
    2. Rejects URLs containing embedded credentials.
    3. Rejects hostnames matching blocked suffixes.
    4. Pre-resolves DNS and rejects IPs in blocked CIDR ranges.

    Args:
        url: The raw URL string to validate.

    Returns:
        The cleaned URL (fragment stripped) if all checks pass.

    Raises:
        ValueError: With a descriptive message when any check fails.
    """
    # ------------------------------------------------------------------
    # 1. Parse
    # ------------------------------------------------------------------
    try:
        parsed = urlparse(url.strip())
    except Exception as exc:
        raise ValueError(f"Malformed URL: {exc}") from exc

    # ------------------------------------------------------------------
    # 2. Scheme whitelist
    # ------------------------------------------------------------------
    scheme = (parsed.scheme or "").lower()
    if scheme not in _ALLOWED_SCHEMES:
        raise ValueError(
            f"Disallowed URL scheme '{scheme}'. Only http and https are permitted."
        )

    # ------------------------------------------------------------------
    # 3. Reject embedded credentials  (http://user:pass@host)
    # ------------------------------------------------------------------
    if parsed.username or parsed.password:
        raise ValueError(
            "URLs with embedded credentials (user:pass@host) are not permitted."
        )

    # ------------------------------------------------------------------
    # 4. Extract and validate hostname
    # ------------------------------------------------------------------
    hostname = (parsed.hostname or "").lower().strip(".")
    if not hostname:
        raise ValueError("URL is missing a hostname.")

    # Reject internal / reserved hostnames by suffix
    for suffix in _BLOCKED_HOSTNAME_SUFFIXES:
        if hostname == suffix.lstrip(".") or hostname.endswith(suffix):
            raise ValueError(
                f"Hostname '{hostname}' matches a blocked internal suffix '{suffix}'."
            )

    # Explicitly reject the cloud metadata endpoint by name
    if hostname in {"metadata.google.internal", "169.254.169.254"}:
        raise ValueError(
            f"Hostname '{hostname}' resolves to a blocked cloud-metadata endpoint."
        )

    # ------------------------------------------------------------------
    # 5. DNS pre-resolution and CIDR validation
    # ------------------------------------------------------------------
    try:
        addr_infos = socket.getaddrinfo(hostname, None)
    except socket.gaierror as exc:
        raise ValueError(f"DNS resolution failed for '{hostname}': {exc}") from exc

    if not addr_infos:
        raise ValueError(f"DNS resolution returned no addresses for '{hostname}'.")

    for family, _type, _proto, _canonname, sockaddr in addr_infos:
        raw_ip = sockaddr[0]
        if not validate_ip(raw_ip):
            raise ValueError(
                f"Resolved IP '{raw_ip}' for hostname '{hostname}' is in a "
                "blocked private/reserved address range (SSRF protection)."
            )

    # ------------------------------------------------------------------
    # 6. Return cleaned URL (fragment stripped)
    # ------------------------------------------------------------------
    clean = parsed._replace(fragment="").geturl()
    return clean
