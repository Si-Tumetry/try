import math
import os

import pytest

from core.embeddings import EmbeddingDimensionMismatch, SentenceTransformerEmbedder, build_embedder
from core.errors import DependencyUnavailable
from core.settings import Settings


class StubModel:
    def __init__(self, dim=8, fail=False):
        self.dim = dim
        self.fail = fail
        self.calls = 0

    def encode(self, texts, normalize_embeddings=True):
        self.calls += 1
        if self.fail:
            raise RuntimeError("out of memory")
        out = []
        for text in texts:
            vec = [float((len(text) + i) % 7 + 1) for i in range(self.dim)]
            norm = math.sqrt(sum(x * x for x in vec))
            out.append([x / norm for x in vec])
        return out


def _factory(model):
    loads = []

    def factory(name, device):
        loads.append((name, device))
        return model

    factory.loads = loads
    return factory


def test_model_loads_lazily_on_first_embed():
    factory = _factory(StubModel(dim=8))
    embedder = SentenceTransformerEmbedder("stub", 8, factory=factory)
    assert factory.loads == []
    embedder.embed("python developer")
    assert factory.loads == [("stub", "cpu")]


def test_vectors_are_unit_length_and_have_the_configured_size():
    embedder = SentenceTransformerEmbedder("stub", 8, factory=_factory(StubModel(dim=8)))
    vec = embedder.embed("data entry clerk in Accra")
    assert len(vec) == 8
    assert math.isclose(sum(x * x for x in vec), 1.0, rel_tol=1e-9)


def test_model_is_loaded_once_and_reused():
    model = StubModel(dim=8)
    factory = _factory(model)
    embedder = SentenceTransformerEmbedder("stub", 8, factory=factory)
    embedder.embed("one")
    embedder.embed("two")
    assert len(factory.loads) == 1
    assert model.calls == 3  # one dimension probe and two embeddings


def test_model_that_cannot_load_is_reported_as_unavailable():
    def broken(name, device):
        raise OSError("model files missing")

    embedder = SentenceTransformerEmbedder("stub", 8, factory=broken)
    with pytest.raises(DependencyUnavailable):
        embedder.embed("anything")


def test_dimension_mismatch_is_a_hard_configuration_error():
    embedder = SentenceTransformerEmbedder("stub", 1024, factory=_factory(StubModel(dim=8)))
    with pytest.raises(EmbeddingDimensionMismatch, match="EMBEDDING_DIM is 1024"):
        embedder.embed("anything")


def test_encoding_failure_is_reported_as_unavailable():
    embedder = SentenceTransformerEmbedder("stub", 8, factory=_factory(StubModel(dim=8)))
    embedder.embed("warm up")
    embedder._model.fail = True
    with pytest.raises(DependencyUnavailable):
        embedder.embed("next")


def test_provider_none_builds_no_embedder():
    assert build_embedder(Settings.from_env({"EMBEDDING_PROVIDER": "none"})) is None


def test_default_provider_builds_the_bge_m3_adapter():
    embedder = build_embedder(Settings.from_env({}))
    assert isinstance(embedder, SentenceTransformerEmbedder)
    assert embedder._model_name == "BAAI/bge-m3"
    assert embedder._expected_dim == 1024


@pytest.mark.skipif(
    os.environ.get("YPP_TEST_REAL_MODEL") != "1",
    reason="set YPP_TEST_REAL_MODEL=1 to load the real BAAI/bge-m3 model (about 2 GB, needs network once)",
)
def test_real_model_produces_1024_dimensions_and_ranks_related_text_higher():
    embedder = SentenceTransformerEmbedder("BAAI/bge-m3", 1024)
    query = embedder.embed("Python developer who builds APIs")
    related = embedder.embed("Backend engineer writing Python web services")
    unrelated = embedder.embed("Fresh cassava harvest from the farm")
    assert len(query) == 1024

    def dot(a, b):
        return sum(x * y for x, y in zip(a, b))

    assert dot(query, related) > dot(query, unrelated)
