"""
Cap Heaven API — Python client SDK

Install: pip install requests

Quick start
-----------
    from cap_client import CapClient

    client = CapClient(api_key="sk_live_your_key_here")

    # Solve captcha
    solved = client.solve(
        captcha_sitekey="...",
        captcha_rqdata="...",
        captcha_rqtoken="...",
        proxy="user:pass@1.2.3.4:8080",
    )
    print(solved["x-captcha-key"])

    # Join server
    joined = client.join(token="DiscordToken", invite="inviteCode")
    print(joined["guild_id"])

    # Join + boost
    boosted = client.join_boost(token="DiscordToken", invite="inviteCode", proxy="...")
    print(boosted["boost_message"])
"""

from __future__ import annotations

import json
import time
from typing import Any

import requests


DEFAULT_BASE_URL = "https://capheaven.dcord.co"
DEFAULT_POLL_INTERVAL = 3.0
DEFAULT_MAX_WAIT = 600.0  # 10 minutes — matches server queue timeout
HTTP_TIMEOUT = 30.0


class CapAPIError(Exception):
    """Raised when the API returns an error or the task fails."""

    def __init__(
        self,
        message: str,
        *,
        status_code: int | None = None,
        body: Any = None,
        task_id: int | None = None,
    ):
        super().__init__(message)
        self.status_code = status_code
        self.body = body
        self.task_id = task_id


def normalize_proxy(proxy: str | None) -> str:
    proxy = (proxy or "").strip()
    if not proxy:
        return ""
    if proxy.startswith(("http://", "https://", "socks5://", "socks5h://")):
        return proxy
    return "http://" + proxy


class CapClient:
    """
    Async Tasks API client (create task + poll status until done).

    Parameters
    ----------
    api_key:
        Your Cap Heaven API key (X-API-Key header).
    base_url:
        API base URL. Default: https://capheaven.dcord.co
    poll_interval:
        Seconds between status polls. Default: 3
    max_wait:
        Max seconds to wait for a task. Default: 600 (10 min)
    """

    def __init__(
        self,
        api_key: str,
        *,
        base_url: str = DEFAULT_BASE_URL,
        poll_interval: float = DEFAULT_POLL_INTERVAL,
        max_wait: float = DEFAULT_MAX_WAIT,
        session: requests.Session | None = None,
    ):
        api_key = (api_key or "").strip()
        if not api_key:
            raise ValueError("api_key is required")

        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.poll_interval = float(poll_interval)
        self.max_wait = float(max_wait)
        self.session = session or requests.Session()

    @property
    def _headers(self) -> dict[str, str]:
        return {
            "Content-Type": "application/json",
            "X-API-Key": self.api_key,
        }

    def solve(
        self,
        *,
        captcha_sitekey: str,
        captcha_rqdata: str,
        captcha_rqtoken: str,
        proxy: str,
        **extra: Any,
    ) -> dict[str, Any]:
        """
        Solve a Discord hCaptcha challenge.

        Returns dict with at least:
            x-captcha-key, x-captcha-rqtoken, success, price_usd
        """
        body: dict[str, Any] = {
            "type": "solve",
            "captcha_sitekey": captcha_sitekey,
            "captcha_rqdata": captcha_rqdata,
            "captcha_rqtoken": captcha_rqtoken,
            "proxy": normalize_proxy(proxy),
        }
        body.update(extra)
        return self._run_task(body)

    def solve_from_discord(
        self,
        discord_captcha: str | dict[str, Any],
        *,
        proxy: str,
        **extra: Any,
    ) -> dict[str, Any]:
        """
        Solve using the raw JSON body Discord returns on captcha (HTTP 400).

        Pass the response text or parsed dict from Discord, plus your proxy.
        """
        if isinstance(discord_captcha, str):
            try:
                payload = json.loads(discord_captcha)
            except json.JSONDecodeError as exc:
                raise CapAPIError(f"Discord captcha body is not valid JSON: {exc}") from exc
        elif isinstance(discord_captcha, dict):
            payload = dict(discord_captcha)
        else:
            raise CapAPIError(f"Unexpected captcha payload type: {type(discord_captcha)}")

        payload["type"] = "solve"
        payload["proxy"] = normalize_proxy(proxy)
        payload.update(extra)
        return self._run_task(payload)

    def join(
        self,
        *,
        token: str,
        invite: str,
        proxy: str | None = None,
    ) -> dict[str, Any]:
        """
        Join a Discord server by invite code.

        Parameters
        ----------
        token:
            Discord user token.
        invite:
            Invite code or full discord.gg URL.
        proxy:
            Optional proxy (user:pass@host:port or full URL).
        """
        body: dict[str, Any] = {
            "type": "join",
            "token": token.strip(),
            "invite": _normalize_invite(invite),
            "boost": False,
        }
        proxy_url = normalize_proxy(proxy)
        if proxy_url:
            body["proxy"] = proxy_url
        return self._run_task(body)

    def join_boost(
        self,
        *,
        token: str,
        invite: str,
        proxy: str | None = None,
    ) -> dict[str, Any]:
        """
        Join a Discord server and boost it (if the account has boosts).

        Same as join(), but sets boost=true.
        """
        body: dict[str, Any] = {
            "type": "join",
            "token": token.strip(),
            "invite": _normalize_invite(invite),
            "boost": True,
        }
        proxy_url = normalize_proxy(proxy)
        if proxy_url:
            body["proxy"] = proxy_url
        return self._run_task(body)

    def create_task(self, body: dict[str, Any]) -> int:
        """POST /api/task/create — returns task_id."""
        url = f"{self.base_url}/api/task/create"
        try:
            response = self.session.post(
                url,
                json=body,
                headers=self._headers,
                timeout=HTTP_TIMEOUT,
            )
        except requests.RequestException as exc:
            raise CapAPIError(f"Request failed: {exc}") from exc

        raw = response.text or ""
        try:
            data = response.json() if raw.strip() else {}
        except json.JSONDecodeError as exc:
            raise CapAPIError(
                f"Non-JSON response (status={response.status_code}): {raw[:500]!r}",
                status_code=response.status_code,
                body=raw,
            ) from exc

        if response.status_code >= 400:
            detail = data.get("detail", data)
            raise CapAPIError(
                f"Create task failed (status={response.status_code}): {detail}",
                status_code=response.status_code,
                body=data,
            )

        task_id = data.get("task_id")
        if not task_id:
            raise CapAPIError(
                f"Create response missing task_id: {data}",
                status_code=response.status_code,
                body=data,
            )
        return int(task_id)

    def get_task_status(self, task_id: int) -> dict[str, Any]:
        """GET /api/task/status?task_id=..."""
        url = f"{self.base_url}/api/task/status"
        try:
            response = self.session.get(
                url,
                headers=self._headers,
                params={"task_id": task_id},
                timeout=HTTP_TIMEOUT,
            )
        except requests.RequestException as exc:
            raise CapAPIError(
                f"Status request failed: {exc}",
                task_id=task_id,
            ) from exc

        raw = response.text or ""
        try:
            data = response.json() if raw.strip() else {}
        except json.JSONDecodeError as exc:
            raise CapAPIError(
                f"Non-JSON status (status={response.status_code}): {raw[:500]!r}",
                status_code=response.status_code,
                body=raw,
                task_id=task_id,
            ) from exc

        if response.status_code >= 400:
            detail = data.get("detail", data)
            raise CapAPIError(
                f"Status error (status={response.status_code}): {detail}",
                status_code=response.status_code,
                body=data,
                task_id=task_id,
            )
        return data

    def wait_task(self, task_id: int) -> dict[str, Any]:
        """Poll task status until completed/failed or timeout."""
        deadline = time.monotonic() + self.max_wait
        last: dict[str, Any] | None = None

        while time.monotonic() < deadline:
            last = self.get_task_status(task_id)
            status = last.get("status")

            if status in ("completed", "failed"):
                result = last.get("result") if isinstance(last.get("result"), dict) else {}
                success = bool(last.get("success")) and bool(
                    result.get("success", last.get("success"))
                )

                if status == "completed" and success:
                    return result

                message = (
                    last.get("message")
                    or result.get("message")
                    or f"task {status}"
                )
                raise CapAPIError(
                    message,
                    status_code=last.get("http_status"),
                    body=last,
                    task_id=task_id,
                )

            time.sleep(self.poll_interval)

        raise CapAPIError(
            f"Task timed out after {self.max_wait:.0f}s",
            body=last,
            task_id=task_id,
        )

    def _run_task(self, body: dict[str, Any]) -> dict[str, Any]:
        task_id = self.create_task(body)
        return self.wait_task(task_id)


def _normalize_invite(invite: str) -> str:
    invite = (invite or "").strip()
    if not invite:
        raise ValueError("invite is required")
    if "discord.gg/" in invite:
        invite = invite.split("discord.gg/")[-1]
    if "discord.com/invite/" in invite:
        invite = invite.split("discord.com/invite/")[-1]
    return invite.split("?")[0].split("/")[0].strip()


# --- Module-level shortcuts (optional) ---

def solve(
    api_key: str,
    *,
    captcha_sitekey: str,
    captcha_rqdata: str,
    captcha_rqtoken: str,
    proxy: str,
    base_url: str = DEFAULT_BASE_URL,
    **kwargs: Any,
) -> dict[str, Any]:
    """One-shot solve without creating a CapClient instance."""
    return CapClient(api_key, base_url=base_url).solve(
        captcha_sitekey=captcha_sitekey,
        captcha_rqdata=captcha_rqdata,
        captcha_rqtoken=captcha_rqtoken,
        proxy=proxy,
        **kwargs,
    )


def join(
    api_key: str,
    *,
    token: str,
    invite: str,
    proxy: str | None = None,
    base_url: str = DEFAULT_BASE_URL,
) -> dict[str, Any]:
    """One-shot join without creating a CapClient instance."""
    return CapClient(api_key, base_url=base_url).join(
        token=token,
        invite=invite,
        proxy=proxy,
    )


def join_boost(
    api_key: str,
    *,
    token: str,
    invite: str,
    proxy: str | None = None,
    base_url: str = DEFAULT_BASE_URL,
) -> dict[str, Any]:
    """One-shot join + boost without creating a CapClient instance."""
    return CapClient(api_key, base_url=base_url).join_boost(
        token=token,
        invite=invite,
        proxy=proxy,
    )


if __name__ == "__main__":
    # Example — replace with your real API key and data
    API_KEY = "sk_live_your_key_here"

    client = CapClient(api_key=API_KEY)

    # solve example:
    # result = client.solve(
    #     captcha_sitekey="...",
    #     captcha_rqdata="...",
    #     captcha_rqtoken="...",
    #     proxy="user:pass@1.2.3.4:8080",
    # )
    # print("captcha key:", result["x-captcha-key"])

    # join example:
    # result = client.join(token="YourDiscordToken", invite="abc123")
    # print("guild:", result.get("guild_id"))

    # join + boost example:
    # result = client.join_boost(token="YourDiscordToken", invite="abc123")
    # print("boost:", result.get("boost_message"))

    print("CapClient ready — edit __main__ with your API key and uncomment examples.")
