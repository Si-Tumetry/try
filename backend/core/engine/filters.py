from core.config import AVAILABILITY_RANK
from core.domain import Candidate, Listing, Requirement


def passes_candidate_filters(cand: Candidate, req: Requirement) -> bool:
    """Mirrors the hard-filter WHERE clause in TECHNICAL.md §5.2."""
    if cand.deleted or cand.suspended or cand.status != "active" or not cand.searchable:
        return False
    if req.country and cand.country != req.country:
        return False
    if req.availability:
        if cand.availability is None:
            return False
        if AVAILABILITY_RANK[cand.availability] > AVAILABILITY_RANK[req.availability]:
            return False
    return True


IN_COUNTRY_SCOPES = frozenset({"in_region", "remote_in_region"})


def passes_listing_filters(listing: Listing, country: str | None, *, include_global: bool = False) -> bool:
    """Default youth view: listings open to applicants in `country` (TECHNICAL.md §14.19).

    `include_global` shows every active listing, including ones outside the applicant's country.
    Listings awaiting review are never shown.
    """
    if listing.deleted or listing.status != "active" or listing.needs_review:
        return False
    if include_global:
        return True
    if country is None:
        return False
    return country in listing.eligible_countries and listing.scope in IN_COUNTRY_SCOPES
