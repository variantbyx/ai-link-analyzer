from urllib.parse import urlsplit
import asyncio
import ipaddress
import socket

async def validate_url(url: str) -> str:
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

        # Resolve the hostname to IP addresses.
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

        # Reject private, loopback, reserved and other non-public IPs.
        for result in results:
            ip = ipaddress.ip_address(result[4][0])

            if not ip.is_global:
                raise ValueError("Private or non-public IP addresses are not allowed.")

        return url.strip()

    except ValueError:
        raise

    except Exception:
        raise ValueError("Invalid website URL.")
