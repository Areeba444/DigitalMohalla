"""The sentence-embedding model behind IEmbed (ADR-0016; plan item A9).

`FastEmbedProvider` runs a small ONNX sentence model in the API process through the `fastembed`
library, an optional dependency (`uv sync --extra semantic`), so the deployed image stays as it is
until the team records the model chosen by ADR-0016's memory test on Render's free tier. Set
EMBEDDING_MODEL (for example BAAI/bge-small-en-v1.5, 384 dimensions) to turn it on. Without the
setting, without the library, or if the model fails to load, `get_embedder()` returns None and
search is keyword-only (FR-S-02): never an error page.
"""

import logging
from collections.abc import Sequence
from functools import lru_cache
from typing import Any

from app.config.settings import get_settings
from app.domain.search.embedding import DIMS, IEmbed, ModelUnavailable

log = logging.getLogger(__name__)


class FastEmbedProvider:
    def __init__(self, model_name: str) -> None:
        try:
            from fastembed import TextEmbedding  # optional dependency, imported only when enabled
        except ImportError as exc:
            raise ModelUnavailable("fastembed is not installed (uv sync --extra semantic)") from exc
        try:
            self._model: Any = TextEmbedding(model_name=model_name)
        except Exception as exc:  # download or load failure: keyword-only instead of an outage
            raise ModelUnavailable(f"model {model_name} could not load: {exc}") from exc
        self.model_name = model_name
        self.dims = DIMS

    def embed(self, texts: Sequence[str]) -> list[list[float]]:
        try:
            vectors = [[float(x) for x in v] for v in self._model.embed(list(texts))]
        except Exception as exc:
            raise ModelUnavailable(f"embedding failed: {exc}") from exc
        if any(len(v) != self.dims for v in vectors):
            raise ModelUnavailable(f"{self.model_name} does not give {self.dims} dimensions")
        return vectors


@lru_cache(maxsize=1)
def get_embedder() -> IEmbed | None:
    name = get_settings().embedding_model
    if not name:
        return None
    try:
        return FastEmbedProvider(name)
    except ModelUnavailable as exc:
        log.warning("meaning-based search is off: %s", exc)
        return None
