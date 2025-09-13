import os
import time
import logging
from typing import List, Optional, Tuple
from urllib.parse import urlparse

try:
    from core.models import Proxy
except Exception:
    Proxy = None  # Fallback if models not ready during migrations

import requests

logger = logging.getLogger(__name__)


def _strip_leading_at(value: str) -> str:
    return value[1:] if value and value.startswith('@') else value


def _normalize_proxy_uri(raw: str) -> Optional[str]:
    """
    Accepts formats:
      - scheme://[user:pass@]host:port
      - host:port
      - host:port:user:pass
      - with optional leading '@'
    Returns a normalized URI or None if invalid.
    Default scheme is http when missing.
    """
    if not raw:
        return None
    value = _strip_leading_at(raw.strip())
    if '://' not in value:
        # Try host:port or host:port:user:pass
        parts = value.split(':')
        if len(parts) == 2:
            host, port = parts
            return f"http://{host}:{port}"
        if len(parts) == 4:
            host, port, user, pwd = parts
            return f"http://{user}:{pwd}@{host}:{port}"
        # Unrecognized
        return None
    # Already has a scheme
    return value


class ProxyManager:
    """Centralized proxy rotation and adapters for different clients.

    Supports http, https, socks4, socks5. Credentials in Chrome are not
    guaranteed; prefer IP-allowlisted or no-auth proxies for browser flows.
    """

    def __init__(self):
        self._proxies: List[str] = []
        self._cooldowns: dict[str, float] = {}
        self._index: int = 0
        self._load()

    def _load(self):
        # Load from DB if available
        items: List[str] = []
        try:
            if Proxy is not None:
                items = [p.url for p in Proxy.objects(is_active=True)]
        except Exception:
            items = []
        # Fallback from env (comma-separated)
        if not items:
            env_val = os.environ.get('KLEIO_PROXIES', '').strip()
            if env_val:
                items = [p.strip() for p in env_val.split(',') if p.strip()]
        # Normalize and filter
        normalized: List[str] = []
        for raw in items:
            uri = _normalize_proxy_uri(raw)
            if uri:
                normalized.append(uri)
        self._proxies = normalized

    def reload(self):
        self._load()

    def get_next(self, schemes: Optional[List[str]] = None) -> Optional[str]:
        if not self._proxies:
            return None
        attempts = 0
        size = len(self._proxies)
        now = time.time()
        while attempts < size:
            proxy = self._proxies[self._index % size]
            self._index += 1
            # Filter by scheme if requested
            if schemes:
                if urlparse(proxy).scheme.lower() not in [s.lower() for s in schemes]:
                    attempts += 1
                    continue
            until_ts = self._cooldowns.get(proxy, 0)
            if now >= until_ts:
                return proxy
            attempts += 1
        return None

    def cooldown(self, proxy_url: Optional[str], minutes: int = 2, reason: str = ""):
        if not proxy_url:
            return
        try:
            self._cooldowns[proxy_url] = time.time() + minutes * 60
            if reason:
                logger.debug(f"Proxy cooldown set for {proxy_url} ({minutes}m): {reason}")
        except Exception:
            pass

    # Adapters
    def for_chrome(self) -> Optional[str]:
        # Chrome supports http/https/socks4/socks5
        return self.get_next(schemes=["http", "https", "socks4", "socks5"])

    def for_requests(self) -> requests.Session:
        sess = requests.Session()
        proxy = self.get_next()
        if proxy:
            sess.proxies = {"http": proxy, "https": proxy}
        return sess

    def for_aiohttp(self) -> Tuple[Optional[object], Optional[str]]:
        """
        Returns (connector, proxy_arg) for aiohttp.
        If socks4/5 → returns (ProxyConnector, None)
        If http/https → returns (None, proxy)
        If no proxy → (None, None)
        """
        proxy = self.get_next()
        if not proxy:
            return None, None
        scheme = urlparse(proxy).scheme.lower()
        if scheme.startswith('socks'):
            try:
                # Lazy import to avoid hard dep if not used
                from aiohttp_socks import ProxyConnector
                connector = ProxyConnector.from_url(proxy)
                return connector, None
            except Exception as e:
                logger.warning(f"aiohttp socks connector unavailable: {e}")
                return None, proxy  # fallback to http proxy arg
        return None, proxy

