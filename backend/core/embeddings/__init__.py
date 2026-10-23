from core.embeddings.bge import EmbeddingDimensionMismatch, SentenceTransformerEmbedder
from core.ports import Embedder
from core.settings import Settings


def build_embedder(settings: Settings) -> Embedder | None:
    """None when embeddings are off. Search then uses keywords only."""
    if settings.embedding_provider == "none":
        return None
    return SentenceTransformerEmbedder(settings.embedding_model, settings.embedding_dim)


__all__ = ["EmbeddingDimensionMismatch", "SentenceTransformerEmbedder", "build_embedder"]
