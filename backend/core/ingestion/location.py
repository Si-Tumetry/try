import re
from dataclasses import dataclass

from core.config import SUPPORTED_COUNTRIES

COUNTRY_NAMES = {
    "Nigeria": "NG", "South Africa": "ZA", "Kenya": "KE", "Ghana": "GH",
    "Spain": "ES", "Poland": "PL", "Portugal": "PT", "United Kingdom": "GB",
    "Pakistan": "PK", "India": "IN", "Congo": "CD", "Democratic Republic of Congo": "CD",
    "Egypt": "EG", "Morocco": "MA", "Uganda": "UG", "Rwanda": "RW", "Tanzania": "TZ",
    "Ethiopia": "ET", "Senegal": "SN", "Cote d'Ivoire": "CI", "Côte d'Ivoire": "CI",
    "United States": "US", "Canada": "CA", "Germany": "DE", "France": "FR",
    "Netherlands": "NL", "Malaysia": "MY", "China": "CN", "Australia": "AU", "Sweden": "SE",
    "Japan": "JP", "Norway": "NO",
}

CITY_COUNTRIES = {
    "London": "GB", "Bangalore": "IN", "Lagos": "NG", "Nairobi": "KE", "Accra": "GH",
    "Kinshasa": "CD", "Cape Town": "ZA", "Capetown": "ZA", "Johannesburg": "ZA",
    "Pretoria": "ZA", "Durban": "ZA", "Kuala Lumpur": "MY", "Shanghai": "CN",
    "Shenzhen": "CN", "Madrid": "ES", "Porto": "PT", "Sydney": "AU", "Stockholm": "SE",
    "Oslo": "NO", "Tokyo": "JP", "New York": "US", "Columbus": "US", "Seattle": "US",
    "Santa Barbara": "US", "Victoria, BC": "CA",
}

US_STATE = re.compile(r"\b(OH|WA|CA|NY|Ohio|Washington|California|New York)\b")
SOUTH_AFRICA_ABBREV = re.compile(r"\bSA\b")

_NAME_PATTERNS = [
    (re.compile(r"\b" + re.escape(name) + r"\b"), code) for name, code in COUNTRY_NAMES.items()
]
_CITY_PATTERNS = [
    (re.compile(r"\b" + re.escape(city) + r"\b"), code) for city, code in CITY_COUNTRIES.items()
]


@dataclass(frozen=True)
class ParsedLocation:
    eligible_countries: tuple[str, ...]
    unmapped: tuple[str, ...]
    work_mode: str
    scope: str


def _match_segment(segment: str) -> set[str]:
    found: set[str] = set()
    for pattern, code in _NAME_PATTERNS + _CITY_PATTERNS:
        if pattern.search(segment):
            found.add(code)
    if SOUTH_AFRICA_ABBREV.search(segment) and "Cape Town" in segment:
        found.add("ZA")
    if US_STATE.search(segment):
        found.add("US")
    return found


def parse_location(text: str | None) -> ParsedLocation:
    """Split a free-text location into countries, a work mode and a regional scope.

    A segment that names no known country is kept in `unmapped` and the listing goes to review.
    The word "Remote" alone names no country, so it leaves eligibility unspecified.
    """
    countries: set[str] = set()
    unmapped: list[str] = []
    modes: set[str] = set()
    for raw in (text or "").split(";"):
        segment = raw.strip()
        if not segment:
            continue
        is_remote = segment.lower().startswith("remote")
        modes.add("remote" if is_remote else "onsite_or_hybrid")
        matched = _match_segment(segment)
        countries |= matched
        if not matched and segment.lower() != "remote":
            unmapped.append(segment)

    if not modes:
        work_mode = "unspecified"
    elif modes == {"remote"}:
        work_mode = "remote"
    else:
        work_mode = "onsite_or_hybrid"

    ordered = tuple(sorted(countries))
    in_region = bool(countries & SUPPORTED_COUNTRIES)
    if in_region:
        scope = "remote_in_region" if work_mode == "remote" else "in_region"
    elif countries:
        scope = "remote_outside_region" if work_mode == "remote" else "outside_region"
    else:
        scope = "unspecified"
    return ParsedLocation(
        eligible_countries=ordered,
        unmapped=tuple(unmapped),
        work_mode=work_mode,
        scope=scope,
    )
