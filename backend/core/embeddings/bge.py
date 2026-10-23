from collections.abc import Callable
from typing import Any

from core.errors import DependencyUnavailable, YppError


class EmbeddingDimensionMismatch(YppError):
    """The model's output size differs from EMBEDDING_DIM. A configuration error, so it is never hidden."""

    code = "internal_error"


def _default_factory(model_name: str, device: str) -> Any:
    from sentence_transformers import SentenceTransformer

    return SentenceTransformer(model_name, device=device)


class SentenceTransformerEmbedder:
    """Local embedding model (default BAAI/bge-m3). Loads on first use, checks the dimension once,
    and returns unit-length vectors so cosine similarity equals the dot product (TECHNICAL.md section 16.1)."""

    def __init__(
        self,
        model_name: str,
        expected_dim: int,
        *,
        device: str = "cpu",
        factory: Callable[[str, str], Any] = _default_factory,
    ) -> None:
        self._model_name = model_name
        self._expected_dim = expected_dim
        self._device = device
        self._factory = factory
        self._model: Any = None

    def _load(self) -> Any:
        if self._model is not None:
            return self._model
        try:
            model = self._factory(self._model_name, self._device)
            probe = model.encode(["dimension check"], normalize_embeddings=True)
        except Exception as exc:
            raise DependencyUnavailable("embedding model could not be loaded") from exc
        size = len(probe[0])
        if size != self._expected_dim:
            raise EmbeddingDimensionMismatch(
                f"{self._model_name} produces {size} dimensions but EMBEDDING_DIM is {self._expected_dim}"
            )
        self._model = model
        return model

    def embed(self, text: str) -> tuple[float, ...]:
        model = self._load()
        try:
            vector = model.encode([text], normalize_embeddings=True)[0]
        except Exception as exc:
            raise DependencyUnavailable("embedding failed") from exc
        return tuple(float(x) for x in vector)
