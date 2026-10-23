import hashlib
import math

from core.errors import DependencyUnavailable
from core.text import tokens


class HashingEmbedder:
    """Deterministic bag-of-words embedder. Texts that share words get high cosine similarity."""

    def __init__(self, dim: int = 64) -> None:
        self.dim = dim
        self.calls = 0

    def embed(self, text: str) -> tuple[float, ...]:
        self.calls += 1
        vec = [0.0] * self.dim
        for token in tokens(text):
            digest = hashlib.blake2b(token.encode("utf-8"), digest_size=8).digest()
            index = int.from_bytes(digest[:4], "big") % self.dim
            sign = 1.0 if digest[4] & 1 else -1.0
            vec[index] += sign
        norm = math.sqrt(sum(x * x for x in vec))
        if norm == 0.0:
            return tuple(vec)
        return tuple(x / norm for x in vec)


class FailingEmbedder:
    def embed(self, text: str) -> tuple[float, ...]:
        raise DependencyUnavailable("embedding service down")


class ScriptedLLM:
    """Returns queued replies in order. A queued Exception is raised instead."""

    def __init__(self, replies: list[str | Exception]) -> None:
        self._replies = list(replies)
        self.calls: list[tuple[str, str]] = []

    def complete(self, system: str, user: str) -> str:
        self.calls.append((system, user))
        if not self._replies:
            raise AssertionError("ScriptedLLM ran out of replies")
        reply = self._replies.pop(0)
        if isinstance(reply, Exception):
            raise reply
        return reply


class FailingLLM:
    def complete(self, system: str, user: str) -> str:
        raise DependencyUnavailable("llm down")
