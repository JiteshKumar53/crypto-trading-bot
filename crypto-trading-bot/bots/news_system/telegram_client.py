"""
Telegram Bot API client.

Only sendMessage and getMe are needed. Messages are sent as HTML because the
Bot API's MarkdownV2 requires escaping a large punctuation set that appears
constantly in headlines.
"""

import html
import os
import time
from typing import Any, Dict, List, Optional

import requests

# Overridable so tests can point at a mock, and so a self-hosted Bot API
# server can be used instead of Telegram's public endpoint.
API_BASE = os.environ.get("TELEGRAM_API_BASE", "https://api.telegram.org").rstrip("/")
# Hard Bot API limit. The configured max_message_chars must stay under this.
TELEGRAM_MAX_CHARS = 4096


class TelegramError(Exception):
    """Raised when Telegram rejects a request in a way retrying will not fix."""


def escape(text: str) -> str:
    """Escape the three characters that are special in Telegram's HTML mode."""
    return html.escape(text or "", quote=False)


def split_message(text: str, limit: int) -> List[str]:
    """
    Split a message into chunks under `limit`, breaking on blank lines first,
    then single newlines, and only hard-splitting a line that is itself too
    long. Keeps HTML tags intact because splits never land inside a line.
    """
    limit = min(limit, TELEGRAM_MAX_CHARS)
    if len(text) <= limit:
        return [text] if text else []

    chunks: List[str] = []
    current = ""

    for block in text.split("\n\n"):
        candidate = f"{current}\n\n{block}" if current else block
        if len(candidate) <= limit:
            current = candidate
            continue

        if current:
            chunks.append(current)
            current = ""

        if len(block) <= limit:
            current = block
            continue

        # Block alone exceeds the limit — fall back to line-level packing.
        for line in block.split("\n"):
            candidate = f"{current}\n{line}" if current else line
            if len(candidate) <= limit:
                current = candidate
                continue
            if current:
                chunks.append(current)
                current = ""
            while len(line) > limit:
                chunks.append(line[:limit])
                line = line[limit:]
            current = line

    if current:
        chunks.append(current)

    return chunks


class TelegramClient:
    """Thin sender with retry/backoff and Telegram's rate-limit handling."""

    def __init__(
        self,
        token: str,
        chat_id: str,
        timeout: int = 15,
        retries: int = 3,
        disable_preview: bool = True,
        max_chars: int = 3800,
        dry_run: bool = False,
        logger=None,
    ):
        self.token = token
        self.chat_id = chat_id
        self.timeout = timeout
        self.retries = max(1, retries)
        self.disable_preview = disable_preview
        self.max_chars = min(max_chars, TELEGRAM_MAX_CHARS)
        self.dry_run = dry_run
        self.logger = logger

    def _log(self, message: str) -> None:
        if self.logger:
            self.logger(message)

    def _url(self, method: str) -> str:
        return f"{API_BASE}/bot{self.token}/{method}"

    def describe_target(self) -> str:
        """Endpoint summary for logs, with the token redacted."""
        return f"{API_BASE} chat={self.chat_id}"

    def get_me(self) -> Dict[str, Any]:
        """Verify the token. Used by `--mode test`."""
        response = requests.get(self._url("getMe"), timeout=self.timeout)
        payload = response.json()
        if not payload.get("ok"):
            raise TelegramError(f"getMe failed: {payload.get('description', response.text)}")
        return payload["result"]

    def get_updates(self) -> List[Dict[str, Any]]:
        """
        Fetch recent updates. Used by `--mode chatid` to discover which chats
        the bot can post to.

        Only works while no webhook is set and only covers roughly the last 24
        hours of messages, which is why the caller prompts the user to send a
        message first.
        """
        response = requests.get(
            self._url("getUpdates"), params={"timeout": 0}, timeout=self.timeout
        )
        payload = _safe_json(response)
        if not payload.get("ok"):
            raise TelegramError(
                f"getUpdates failed: {payload.get('description', response.text[:200])}"
            )
        return payload.get("result", [])

    def send(self, text: str, silent: bool = False) -> bool:
        """
        Send `text`, splitting it across messages when needed.

        Returns True only if every chunk was accepted.
        """
        chunks = split_message(text, self.max_chars)
        if not chunks:
            return True

        for index, chunk in enumerate(chunks):
            if not self._send_chunk(chunk, silent):
                return False
            if index < len(chunks) - 1:
                # Telegram throttles bursts to a chat; pace consecutive chunks.
                time.sleep(1)

        return True

    def _send_chunk(self, text: str, silent: bool) -> bool:
        if self.dry_run:
            self._log(f"DRY RUN — would send {len(text)} chars:\n{text}")
            return True

        payload = {
            "chat_id": self.chat_id,
            "text": text,
            "parse_mode": "HTML",
            "disable_web_page_preview": self.disable_preview,
            "disable_notification": silent,
        }

        for attempt in range(self.retries):
            try:
                response = requests.post(
                    self._url("sendMessage"), json=payload, timeout=self.timeout
                )
                body = _safe_json(response)

                if response.status_code == 200 and body.get("ok"):
                    return True

                if response.status_code == 429:
                    wait = int(body.get("parameters", {}).get("retry_after", 5))
                    self._log(f"TELEGRAM rate limited, waiting {wait}s")
                    time.sleep(wait)
                    continue

                description = body.get("description", response.text[:200])
                # 400/401/403 mean a bad token, chat id or malformed HTML.
                # Retrying identical content cannot fix any of those.
                if response.status_code in (400, 401, 403, 404):
                    raise TelegramError(
                        f"Telegram rejected the message ({response.status_code}): {description}"
                    )
                self._log(f"TELEGRAM error {response.status_code}: {description}")
            except requests.RequestException as exc:
                self._log(f"TELEGRAM network error: {exc}")

            if attempt < self.retries - 1:
                time.sleep(2 ** attempt)

        return False


def _safe_json(response) -> Dict[str, Any]:
    """Telegram returns JSON on every documented path, but proxies may not."""
    try:
        data = response.json()
        return data if isinstance(data, dict) else {}
    except ValueError:
        return {}
