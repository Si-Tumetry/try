import html
import re
import time
from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Any, Callable

import httpx

from core.ingestion.location import ParsedLocation, parse_location

API_HOST = "boards-api.greenhouse.io"
API_BASE = f"https://{API_HOST}/v1/boards"
MIN_DESCRIPTION_CHARS = 50
MAX_RESPONSE_BYTES = 2 * 1024 * 1024
REQUEST_TIMEOUT = httpx.Timeout(connect=5.0, read=15.0, write=5.0, pool=5.0)


class GreenhouseError(Exception):
    pass


class BoardNotFound(GreenhouseError):
    pass


class RateLimited(GreenhouseError):
    def __init__(self, retry_after: float | None) -> None:
        super().__init__("rate limited by Greenhouse")
        self.retry_after = retry_after


@dataclass(frozen=True)
class Draft:
    """One source record after mapping. `status` is ok, needs_review or rejected."""

    source_key: str
    external_id: str
    employer_name: str
    title: str
    department: str | None
    location_text: str
    eligible_countries: tuple[str, ...]
    unmapped_locations: tuple[str, ...]
    work_mode: str
    scope: str
    source_url: str
    updated_at: str
    expires_at: date | None
    description: str
    pay_ranges: tuple[dict[str, Any], ...] = field(default_factory=tuple)
    status: str = "ok"
    reason: str | None = None

    def to_dict(self) -> dict[str, Any]:
        out = {k: getattr(self, k) for k in self.__dataclass_fields__}
        out["expires_at"] = self.expires_at.isoformat() if self.expires_at else None
        out["eligible_countries"] = list(self.eligible_countries)
        out["unmapped_locations"] = list(self.unmapped_locations)
        out["pay_ranges"] = list(self.pay_ranges)
        return out


def html_to_text(raw: str | None) -> str:
    # Greenhouse returns entity-encoded HTML inside JSON, so decode twice.
    text = html.unescape(html.unescape(raw or ""))
    text = re.sub(r"<(br|/p|/li|/h[1-6])\s*/?>", "\n", text)
    text = re.sub(r"<[^>]+>", "", text)
    text = re.sub(r"[ \t]+", " ", text)
    return re.sub(r"\n\s*\n+", "\n\n", text).strip()


def _parse_deadline(value: str | None) -> date | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).date()
    except ValueError:
        return None


def _pay(job: dict[str, Any]) -> tuple[dict[str, Any], ...]:
    out = []
    for item in job.get("pay_input_ranges") or []:
        out.append(
            {
                "min": (item.get("min_cents") or 0) / 100,
                "max": (item.get("max_cents") or 0) / 100,
                "currency": item.get("currency_type"),
                "title": item.get("title"),
            }
        )
    return tuple(out)


def map_job(job: dict[str, Any], *, source_key: str, employer_name: str) -> Draft:
    loc_name = (job.get("location") or {}).get("name") or ""
    parsed: ParsedLocation = parse_location(loc_name)
    departments = job.get("departments") or []
    base = dict(
        source_key=source_key,
        external_id=str(job.get("id", "")),
        employer_name=employer_name,
        title=(job.get("title") or "").strip(),
        department=departments[0].get("name") if departments else None,
        location_text=loc_name,
        eligible_countries=parsed.eligible_countries,
        unmapped_locations=parsed.unmapped,
        work_mode=parsed.work_mode,
        scope=parsed.scope,
        source_url=job.get("absolute_url") or "",
        updated_at=job.get("updated_at") or "",
        expires_at=_parse_deadline(job.get("application_deadline")),
        description=html_to_text(job.get("content")),
        pay_ranges=_pay(job),
    )

    def rejected(reason: str) -> Draft:
        return Draft(**{**base, "status": "rejected", "reason": reason})

    if not base["external_id"]:
        return rejected("missing id")
    if not base["title"]:
        return rejected("missing title")
    if not base["source_url"].startswith("https://"):
        return rejected("source_url is not https")
    if len(base["description"]) < MIN_DESCRIPTION_CHARS:
        return rejected(f"description shorter than {MIN_DESCRIPTION_CHARS} characters")
    if parsed.unmapped:
        return Draft(**{**base, "status": "needs_review", "reason": "unmapped location parts"})
    return Draft(**{**base, "status": "ok"})


class GreenhouseConnector:
    """Reads public Greenhouse job boards. Only GET requests, only the allowed host, no redirects."""

    def __init__(
        self,
        *,
        user_agent: str,
        min_interval_seconds: float = 5.0,
        transport: httpx.BaseTransport | None = None,
        clock: Callable[[], float] = time.monotonic,
        sleep: Callable[[float], None] = time.sleep,
    ) -> None:
        if not user_agent or "@" not in user_agent and "http" not in user_agent.lower():
            raise ValueError("the user agent must name the product and carry a contact email or URL")
        self._user_agent = user_agent
        self._interval = min_interval_seconds
        self._clock = clock
        self._sleep = sleep
        self._last_request: float | None = None
        self._client = httpx.Client(
            timeout=REQUEST_TIMEOUT,
            follow_redirects=False,
            transport=transport,
            headers={"User-Agent": user_agent, "Accept": "application/json"},
        )

    def close(self) -> None:
        self._client.close()

    def _throttle(self) -> None:
        if self._last_request is not None:
            wait = self._interval - (self._clock() - self._last_request)
            if wait > 0:
                self._sleep(wait)
        self._last_request = self._clock()

    def _get(self, url: str) -> Any:
        if httpx.URL(url).host != API_HOST:
            raise GreenhouseError("host not on the allowlist")
        self._throttle()
        response = self._client.get(url)
        if response.status_code == 404:
            raise BoardNotFound(url)
        if response.status_code == 429:
            retry = response.headers.get("Retry-After")
            raise RateLimited(float(retry) if retry and retry.isdigit() else None)
        if response.status_code >= 400:
            raise GreenhouseError(f"HTTP {response.status_code}")
        if len(response.content) > MAX_RESPONSE_BYTES:
            raise GreenhouseError("response larger than 2 MB")
        return response.json()

    def fetch_board(self, board_token: str) -> tuple[str, list[Draft]]:
        """Returns (employer name, drafts). Rejected records are included so the run can report them."""
        if not re.fullmatch(r"[a-z0-9_-]{1,64}", board_token):
            raise GreenhouseError("invalid board token")
        board = self._get(f"{API_BASE}/{board_token}")
        employer = board.get("name") or board_token
        source_key = f"greenhouse-{board_token}"
        payload = self._get(f"{API_BASE}/{board_token}/jobs?content=true")
        drafts = [
            map_job(job, source_key=source_key, employer_name=employer)
            for job in payload.get("jobs", [])
        ]
        return employer, drafts
