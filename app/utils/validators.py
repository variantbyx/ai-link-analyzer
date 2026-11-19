from urllib.parse import urlsplit
import asyncio
import ipaddress
import socket
import httpcore
import httpx
from httpcore._backends.anyio import AnyIOBackend


async def validate_url(url: str) -> str:
    """
    Validate target URL structure and upfront DNS resolution:
    - HTTP and HTTPS schemes only.
    - Standard web ports only (80, 443).
    - Disallows embedded credentials.
    - Rejects localhost and loopback hostnames.
    - Resolves hostnames and rejects private/reserved/link-local IPv4 & IPv6.
    """
    try:
        parsed = urlsplit(url.strip())

        if parsed.scheme not in ("http", "https"):
            raise ValueError("Only HTTP and HTTPS URLs are allowed.")

        if not parsed.hostname:
            raise ValueError("Invalid URL: hostname is missing.")

        if parsed.username or parsed.password:
            raise ValueError("URLs containing credentials are not allowed.")

        if parsed.port and parsed.port not in (80, 443):
            raise ValueError("Only ports 80 and 443 are allowed.")

        hostname = parsed.hostname.rstrip(".").lower()

        if hostname == "localhost" or hostname.endswith(".localhost"):
            raise ValueError("Localhost URLs are not allowed.")

        # Resolve the hostname to IP addresses
        try:
            loop = asyncio.get_running_loop()
            results = await loop.getaddrinfo(
                hostname,
                parsed.port or (443 if parsed.scheme == "https" else 80),
                type=socket.SOCK_STREAM
            )
        except socket.gaierror:
            raise ValueError("Unable to resolve website hostname.")

        if not results:
            raise ValueError("Website hostname has no valid IP address.")

        # Reject private, loopback, reserved and other non-public IPs
        for result in results:
            ip = ipaddress.ip_address(result[4][0])
            if not ip.is_global:
                raise ValueError("Private or non-public IP addresses are not allowed.")

        return url.strip()

    except ValueError:
        raise
    except Exception:
        raise ValueError("Invalid website URL.")


class SSRFSafeNetworkBackend(httpcore.AsyncNetworkBackend):
    """
    Anti-DNS-Rebinding & TOCTOU-safe network backend for HTTPX.
    
    Prevents Time-of-Check to Time-of-Use (TOCTOU) DNS rebinding attacks:
    At the exact moment of TCP socket creation, this backend:
    1. Resolves the destination hostname asynchronously.
    2. Validates that EVERY resolved IP address is globally routable.
    3. Rejects private, loopback (127.0.0.1, ::1), link-local (169.254.169.254, fe80::/10),
       unique local (fc00::/7), multicast, and reserved addresses.
    4. Connects the TCP socket directly to the validated IP address, guaranteeing
       the connection uses the identical IP that was validated.
    5. Preserves the host parameter for TLS SNI and HTTP Host header verification.
    """
    def __init__(self):
        self._inner = AnyIOBackend()

    async def connect_tcp(
        self,
        host: str,
        port: int,
        timeout: float | None = None,
        local_address: str | None = None,
        socket_options = None
    ) -> httpcore.AsyncNetworkStream:
        if port not in (80, 443):
            raise ValueError(f"Port {port} is not allowed. Only ports 80 and 443 are supported.")

        clean_host = host.rstrip(".").lower()
        if clean_host == "localhost" or clean_host.endswith(".localhost"):
            raise ValueError("Connection to localhost is prohibited.")

        loop = asyncio.get_running_loop()
        try:
            addrinfo = await loop.getaddrinfo(clean_host, port, type=socket.SOCK_STREAM)
        except socket.gaierror:
            raise ValueError(f"Unable to resolve website hostname: {clean_host}")

        if not addrinfo:
            raise ValueError(f"No IP addresses resolved for hostname: {clean_host}")

        # Enforce that ALL returned IPs are globally routable
        for entry in addrinfo:
            ip = ipaddress.ip_address(entry[4][0])
            if not ip.is_global:
                raise ValueError(
                    f"SSRF Protection: Connection to non-public IP address ({ip}) is prohibited."
                )

        # Pin the TCP connection directly to the first validated global IP
        validated_ip = addrinfo[0][4][0]
        return await self._inner.connect_tcp(
            validated_ip,
            port,
            timeout=timeout,
            local_address=local_address,
            socket_options=socket_options
        )


def create_ssrf_safe_transport() -> httpx.AsyncHTTPTransport:
    """
    Constructs an AsyncHTTPTransport wired with SSRFSafeNetworkBackend
    for DNS-rebinding-safe outbound HTTP requests.
    """
    transport = httpx.AsyncHTTPTransport()
    transport._pool._network_backend = SSRFSafeNetworkBackend()
    return transport
