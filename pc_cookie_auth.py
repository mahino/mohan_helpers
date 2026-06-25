#!/usr/bin/env python3
"""Shared Prism cookie auth helpers for scripts in this folder."""

from __future__ import annotations

import base64
import random
import time
from typing import Any

import requests


RETRY_HTTP_CODES = frozenset({401, 429})
BACKOFF_BASE_SEC = 0.8


def _basic_auth_header(user: str, password: str) -> str:
    token = base64.b64encode(f"{user}:{password}".encode("utf-8")).decode("ascii")
    return f"Basic {token}"


class PrismCookieClient:
    """requests.Session wrapper with periodic cookie refresh + retry."""

    def __init__(
        self,
        *,
        session: requests.Session,
        base_url: str,
        username: str,
        password: str,
        verify_ssl: bool,
        timeout_sec: int,
        refresh_sec: int = 300,
    ) -> None:
        self.session = session
        self.base_url = base_url.rstrip("/")
        self.username = username
        self.password = password
        self.verify_ssl = verify_ssl
        self.timeout_sec = timeout_sec
        self.refresh_sec = refresh_sec
        self._last_refresh_ts = 0.0

    def ensure_fresh_cookie(self, *, force: bool = False) -> None:
        now = time.time()
        if not force and (now - self._last_refresh_ts) < self.refresh_sec:
            return

        auth_header = _basic_auth_header(self.username, self.password)
        probe_urls = (
            f"{self.base_url}/api/nutanix/v3/users/me",
            f"{self.base_url}/api/nutanix/v3/versions",
        )
        last_exc: Exception | None = None
        for probe in probe_urls:
            try:
                resp = self.session.get(
                    probe,
                    headers={"Authorization": auth_header},
                    timeout=self.timeout_sec,
                    verify=self.verify_ssl,
                )
                if resp.status_code == 200:
                    self._last_refresh_ts = time.time()
                    return
                if resp.status_code >= 500:
                    resp.raise_for_status()
            except requests.RequestException as exc:
                last_exc = exc
        if last_exc:
            raise RuntimeError("failed to refresh Prism cookie session") from last_exc
        raise RuntimeError("failed to refresh Prism cookie session")

    def request(self, method: str, url: str, *, timeout: int | None = None, **kwargs: Any) -> requests.Response:
        eff_timeout = timeout if timeout is not None else self.timeout_sec
        auth_header = _basic_auth_header(self.username, self.password)
        # Lazy strategy: do not bootstrap cookies on every call.
        # Only refresh/bootstrap when we see retry-worthy auth/throttle responses.
        resp = self.session.request(method, url, timeout=eff_timeout, verify=self.verify_ssl, **kwargs)
        if resp.status_code not in RETRY_HTTP_CODES:
            return resp

        if resp.status_code == 429:
            backoff = BACKOFF_BASE_SEC * (1.0 + random.random() * 0.25)
            time.sleep(backoff)

        def _request_with_basic() -> requests.Response:
            merged_headers = dict(kwargs.get("headers") or {})
            merged_headers["Authorization"] = auth_header
            retry_kwargs = dict(kwargs)
            retry_kwargs["headers"] = merged_headers
            return self.session.request(
                method,
                url,
                timeout=eff_timeout,
                verify=self.verify_ssl,
                **retry_kwargs,
            )

        try:
            self.ensure_fresh_cookie(force=True)
            retry_resp = self.session.request(
                method,
                url,
                timeout=eff_timeout,
                verify=self.verify_ssl,
                **kwargs,
            )
            # Probe endpoints may succeed but cookie still may not be accepted
            # for the target endpoint. Force one Basic-auth retry for 401.
            if retry_resp.status_code == 401:
                return _request_with_basic()
            return retry_resp
        except RuntimeError:
            return _request_with_basic()

