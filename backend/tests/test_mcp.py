import json
import socket
import threading
import time
from contextlib import asynccontextmanager

import httpx
import pytest
import uvicorn
from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client

from core.actor import Actor
from core.services.audit import InMemoryAuditSink
from core.services.talent import TalentService
from mcp_server.asgi import create_asgi_app
from mcp_server.auth import StaticTokenStore
from tests.fakes import HashingEmbedder
from tests.fixtures import AS_OF, build_store

EXPECTED_TOOLS = {
    "search_talent",
    "score_candidate",
    "get_profile",
    "search_opportunities",
    "get_skill_gap",
    "list_skills",
}

TOKENS = {
    "tok-employer": Actor(
        user_id="u-emp1", role="employer",
        scopes=frozenset({"read:candidates", "read:public"}), door="mcp",
    ),
    "tok-youth": Actor(user_id="u-ada", role="youth", scopes=frozenset({"read:public"}), door="mcp"),
    "tok-noscope": Actor(user_id="u-emp1", role="employer", scopes=frozenset(), door="mcp"),
}


def _free_port() -> int:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


@pytest.fixture
def server_url():
    embedder = HashingEmbedder()
    service = TalentService(
        store=build_store(embedder),
        audit=InMemoryAuditSink(),
        embedder=embedder,
        llm=None,
        clock=lambda: AS_OF,
    )
    app = create_asgi_app(service, StaticTokenStore(TOKENS))
    port = _free_port()
    server = uvicorn.Server(
        uvicorn.Config(app, host="127.0.0.1", port=port, log_level="warning", lifespan="on")
    )
    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()
    deadline = time.monotonic() + 15
    while not server.started and time.monotonic() < deadline:
        time.sleep(0.05)
    assert server.started, "test server failed to start"
    yield f"http://127.0.0.1:{port}/mcp"
    server.should_exit = True
    thread.join(timeout=10)


@asynccontextmanager
async def mcp_session(url: str, token: str):
    headers = {"Authorization": f"Bearer {token}"}
    async with httpx.AsyncClient(headers=headers) as http:
        async with streamable_http_client(url, http_client=http) as (read, write, _):
            async with ClientSession(read, write) as session:
                await session.initialize()
                yield session


def _payload(result):
    if result.structuredContent is not None:
        return result.structuredContent
    return json.loads(result.content[0].text)


def _error_text(result) -> str:
    return " ".join(block.text for block in result.content if hasattr(block, "text"))


async def test_request_without_token_is_rejected(server_url):
    async with httpx.AsyncClient() as client:
        response = await client.post(server_url, json={})
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "unauthenticated"
    assert response.headers["www-authenticate"].startswith("Bearer")


async def test_request_with_unknown_token_is_rejected(server_url):
    async with httpx.AsyncClient() as client:
        response = await client.post(
            server_url, json={}, headers={"Authorization": "Bearer tok-forged"}
        )
    assert response.status_code == 401


async def test_exactly_the_six_read_tools_are_exposed(server_url):
    async with mcp_session(server_url, "tok-employer") as session:
        listing = await session.list_tools()
    names = {tool.name for tool in listing.tools}
    assert names == EXPECTED_TOOLS


async def test_employer_search_over_mcp_returns_ranked_results(server_url):
    async with mcp_session(server_url, "tok-employer") as session:
        result = await session.call_tool(
            "search_talent", {"query": "python developer", "country": "NG", "min_score": 0}
        )
    assert not result.isError
    payload = _payload(result)
    assert [r["profile_id"] for r in payload["results"]] == ["p-ada"]
    assert payload["results"][0]["breakdown"]["scoring_version"] == "v1"


async def test_actor_from_token_controls_access(server_url):
    async with mcp_session(server_url, "tok-youth") as session:
        result = await session.call_tool("search_talent", {"query": "python developer", "country": "NG"})
    assert result.isError
    assert "missing scope" in _error_text(result)


async def test_token_without_scope_is_denied(server_url):
    async with mcp_session(server_url, "tok-noscope") as session:
        result = await session.call_tool("search_talent", {"query": "python developer"})
    assert result.isError


async def test_public_profile_over_mcp_is_limited_to_consented_fields(server_url):
    async with mcp_session(server_url, "tok-youth") as session:
        result = await session.call_tool("get_profile", {"profile_id": "p-wanjiru"})
    assert not result.isError
    payload = _payload(result)
    assert payload["untrusted_text"] == {"headline": "Python and SQL analyst in Nairobi"}
    assert payload["untrusted"] is True


async def test_unconsented_profile_is_not_found_over_mcp(server_url):
    async with mcp_session(server_url, "tok-employer") as session:
        result = await session.call_tool("score_candidate", {"profile_id": "p-thandi", "query": "python"})
    assert result.isError
    assert "not found" in _error_text(result)


async def test_out_of_range_input_is_a_tool_error(server_url):
    async with mcp_session(server_url, "tok-employer") as session:
        result = await session.call_tool("search_talent", {"query": "python", "min_score": 101})
    assert result.isError
    assert "min_score" in _error_text(result)


async def test_wrong_argument_type_is_a_tool_error(server_url):
    async with mcp_session(server_url, "tok-employer") as session:
        result = await session.call_tool("search_talent", {"query": "python", "limit": "ten"})
    assert result.isError


async def test_youth_opportunities_over_mcp(server_url):
    async with mcp_session(server_url, "tok-youth") as session:
        result = await session.call_tool("search_opportunities", {"profile_id": "p-ada", "min_score": 0})
    assert not result.isError
    assert [r["listing_id"] for r in _payload(result)["results"]] == ["l-backend"]


async def test_list_skills_over_mcp_needs_no_candidate_scope(server_url):
    async with mcp_session(server_url, "tok-youth") as session:
        result = await session.call_tool("list_skills", {"query": "sql"})
    assert not result.isError
    assert [s["slug"] for s in _payload(result)["skills"]] == ["sql"]
