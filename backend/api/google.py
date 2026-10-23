"""Google sign-in (OpenID Connect, authorization code flow with PKCE).

The browser is sent to Google, Google sends it back with a one-time code, and the server exchanges
that code for an ID token. The ID token is verified with Google's own library, which checks the
signature against Google's published keys, the issuer, the audience and the expiry. The nonce is
checked here, so a token issued for another sign-in cannot be replayed.
"""

import base64
import hashlib
import secrets
from dataclasses import dataclass
from typing import Protocol
from urllib.parse import urlencode

import httpx
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token as google_id_token

from core.errors import DependencyUnavailable, YppError

AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
TOKEN_URL = "https://oauth2.googleapis.com/token"
VALID_ISSUERS = frozenset({"accounts.google.com", "https://accounts.google.com"})


class SignInFailed(YppError):
    code = "unauthenticated"


@dataclass(frozen=True)
class GoogleIdentity:
    subject: str
    name: str | None


class GoogleOIDC(Protocol):
    def authorization_url(self, *, state: str, nonce: str, code_challenge: str, redirect_uri: str) -> str: ...

    def exchange_code(self, *, code: str, code_verifier: str, redirect_uri: str) -> str: ...

    def verify_id_token(self, token: str, *, nonce: str) -> GoogleIdentity: ...


def code_challenge(verifier: str) -> str:
    digest = hashlib.sha256(verifier.encode("ascii")).digest()
    return base64.urlsafe_b64encode(digest).rstrip(b"=").decode("ascii")


def new_secret(size: int = 32) -> str:
    return secrets.token_urlsafe(size)


class GoogleOAuth:
    """The real Google client. Needs GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET (docs/DEPLOYMENT.md)."""

    def __init__(self, client_id: str, client_secret: str, *, http: httpx.Client | None = None) -> None:
        self._client_id = client_id
        self._client_secret = client_secret
        self._http = http or httpx.Client(timeout=10.0)
        self._requests = google_requests.Request()

    def authorization_url(self, *, state: str, nonce: str, code_challenge: str, redirect_uri: str) -> str:
        query = urlencode(
            {
                "client_id": self._client_id,
                "redirect_uri": redirect_uri,
                "response_type": "code",
                "scope": "openid profile",
                "state": state,
                "nonce": nonce,
                "code_challenge": code_challenge,
                "code_challenge_method": "S256",
                "prompt": "select_account",
            }
        )
        return f"{AUTH_URL}?{query}"

    def exchange_code(self, *, code: str, code_verifier: str, redirect_uri: str) -> str:
        try:
            response = self._http.post(
                TOKEN_URL,
                data={
                    "code": code,
                    "client_id": self._client_id,
                    "client_secret": self._client_secret,
                    "redirect_uri": redirect_uri,
                    "grant_type": "authorization_code",
                    "code_verifier": code_verifier,
                },
            )
        except httpx.HTTPError as exc:
            raise DependencyUnavailable("Google sign-in is unreachable. Try again") from exc
        if response.status_code != 200 or "id_token" not in response.json():
            raise SignInFailed("Google did not confirm your sign-in")
        return response.json()["id_token"]

    def verify_id_token(self, token: str, *, nonce: str) -> GoogleIdentity:
        try:
            claims = google_id_token.verify_oauth2_token(token, self._requests, audience=self._client_id)
        except ValueError as exc:
            raise SignInFailed("Google's sign-in token could not be verified") from exc
        if claims.get("iss") not in VALID_ISSUERS:
            raise SignInFailed("Google's sign-in token came from an unexpected issuer")
        if not secrets.compare_digest(str(claims.get("nonce", "")), nonce):
            raise SignInFailed("Google's sign-in token does not belong to this sign-in")
        subject = claims.get("sub")
        if not subject:
            raise SignInFailed("Google's sign-in token has no account id")
        return GoogleIdentity(subject=str(subject), name=claims.get("name"))
