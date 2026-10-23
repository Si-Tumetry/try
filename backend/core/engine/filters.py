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


def passes_listing_filters(listing: Listing, country: str | None) -> bool:
    if listing.deleted or listing.status != "active":
        return False
    return country is None or listing.country == country
