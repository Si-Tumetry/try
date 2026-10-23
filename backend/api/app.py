import uuid
from collections.abc import Awaitable, Callable

from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import JSONResponse, Response
from starlette.routing import Route
from starlette.types import ASGIApp

from api.auth import SessionTokens
from api.security import SecurityHeaders
from core.actor import Actor
from core.cv.extract import MAX_CV_BYTES
from core.errors import ValidationFailed, YppError
from core.services.profiles import YOUTH_SCOPES, ProfileService
from core.services.talent import TalentService


class Unauthenticated(YppError):
    code = "unauthenticated"


STATUS_BY_CODE = {
    "unauthenticated": 401,
    "forbidden": 403,
    "not_found": 404,
    "validation_error": 422,
    "dependency_unavailable": 503,
}
MAX_PAGE = 50
DEFAULT_PAGE = 20

Handler = Callable[[Request], Awaitable[Response]]


def _error(code: str, message: str, status: int) -> JSONResponse:
    return JSONResponse({"error": {"code": code, "message": message}}, status_code=status)


def _handled(fn: Handler) -> Handler:
    async def wrapper(request: Request) -> Response:
        try:
            return await fn(request)
        except YppError as exc:
            status = STATUS_BY_CODE.get(exc.code, 500)
            message = str(exc) if status != 500 else "something went wrong"
            return _error(exc.code if status != 500 else "internal_error", message, status)

    return wrapper


def create_app(*, talent: TalentService, profiles: ProfileService, tokens: SessionTokens) -> ASGIApp:
    def actor_for(request: Request) -> tuple[Actor, str]:
        header = request.headers.get("authorization", "")
        scheme, _, token = header.partition(" ")
        token = token.strip()
        actor = tokens.resolve(token) if scheme.lower() == "bearer" and token else None
        if actor is None:
            raise Unauthenticated("sign in again. Your session is missing or has expired")
        return actor, token

    async def create_profile(request: Request) -> Response:
        form = await _form(request)
        cv_name, cv_bytes = await _cv(form)
        actor = Actor(
            user_id=f"youth:{uuid.uuid4()}",
            role="youth",
            scopes=YOUTH_SCOPES,
            door="rest",
            request_id=str(uuid.uuid4()),
        )
        profile = profiles.create_profile(
            actor,
            cv_filename=cv_name,
            cv_bytes=cv_bytes,
            country=_text(form, "country", required=True),
            availability=_text(form, "availability"),
            searchable=_flag(form, "searchable"),
            consent=_flag(form, "consent"),
        )
        token = tokens.issue(actor)
        return JSONResponse({"token": token, "profile": profile}, status_code=201)

    async def get_profile(request: Request) -> Response:
        actor, _ = actor_for(request)
        return JSONResponse({"profile": profiles.get_profile(actor)})

    async def update_profile(request: Request) -> Response:
        actor, _ = actor_for(request)
        form = await _form(request)
        cv_name, cv_bytes = await _cv(form, required=False)
        profile = profiles.update_profile(
            actor,
            country=_text(form, "country", required=True),
            availability=_text(form, "availability"),
            searchable=_flag(form, "searchable"),
            cv_filename=cv_name,
            cv_bytes=cv_bytes,
        )
        return JSONResponse({"profile": profile})

    async def delete_profile(request: Request) -> Response:
        actor, token = actor_for(request)
        profiles.delete_profile(actor)
        tokens.revoke(token)
        return Response(status_code=204)

    async def matches(request: Request) -> Response:
        actor, _ = actor_for(request)
        profile_id = profiles.profile_id_for(actor)
        result = talent.search_opportunities(
            actor,
            profile_id,
            min_score=_int_param(request, "min_score", default=None, lo=0, hi=100),
            limit=_int_param(request, "limit", default=DEFAULT_PAGE, lo=1, hi=MAX_PAGE),
            cursor=request.query_params.get("cursor") or None,
        )
        return JSONResponse(result)

    async def skill_gap(request: Request) -> Response:
        actor, _ = actor_for(request)
        profile_id = profiles.profile_id_for(actor)
        listing_id = request.path_params["listing_id"]
        return JSONResponse(talent.get_skill_gap(actor, listing_id, profile_id))

    async def health(_: Request) -> Response:
        return JSONResponse({"status": "ok"})

    routes = [
        Route("/v1/health", _handled(health), methods=["GET"]),
        Route("/v1/profiles", _handled(create_profile), methods=["POST"]),
        Route("/v1/me/profile", _handled(get_profile), methods=["GET"]),
        Route("/v1/me/profile", _handled(update_profile), methods=["PUT"]),
        Route("/v1/me/profile", _handled(delete_profile), methods=["DELETE"]),
        Route("/v1/me/matches", _handled(matches), methods=["GET"]),
        Route("/v1/me/matches/{listing_id:path}", _handled(skill_gap), methods=["GET"]),
    ]
    return SecurityHeaders(Starlette(routes=routes))


async def _form(request: Request):
    content_type = request.headers.get("content-type", "")
    if "multipart/form-data" not in content_type and "application/x-www-form-urlencoded" not in content_type:
        raise ValidationFailed("send the profile as a form")
    if int(request.headers.get("content-length") or 0) > MAX_CV_BYTES + 64 * 1024:
        raise ValidationFailed("the CV must be 5 MB or smaller")
    return await request.form()


async def _cv(form, *, required: bool = True) -> tuple[str | None, bytes | None]:
    upload = form.get("cv")
    if upload is None or not getattr(upload, "filename", None):
        if required:
            raise ValidationFailed("attach your CV")
        return None, None
    data = await upload.read(MAX_CV_BYTES + 1)
    if len(data) > MAX_CV_BYTES:
        raise ValidationFailed("the CV must be 5 MB or smaller")
    return upload.filename, data


def _text(form, name: str, *, required: bool = False) -> str | None:
    value = form.get(name)
    if isinstance(value, str) and value.strip():
        return value.strip()
    if required:
        raise ValidationFailed(f"{name} is required")
    return None


def _flag(form, name: str) -> bool:
    return str(form.get(name, "")).strip().lower() in {"true", "1", "on", "yes"}


def _int_param(request: Request, name: str, *, default: int | None, lo: int, hi: int) -> int | None:
    raw = request.query_params.get(name)
    if raw is None or raw == "":
        return default
    try:
        value = int(raw)
    except ValueError as exc:
        raise ValidationFailed(f"{name} must be a whole number") from exc
    if not lo <= value <= hi:
        raise ValidationFailed(f"{name} must be from {lo} to {hi}")
    return value
