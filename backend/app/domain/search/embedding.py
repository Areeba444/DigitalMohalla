"""Embedding port for meaning-based search (Module 4; ADR-0016; plan item A9).

`IEmbed.embed(texts)` turns texts into vectors of `dims` numbers. A listing is embedded from its
title, description and other names (`listing_text`); the SHA-256 of that text is stored with the
vector, so an edited listing is re-embedded by the backfill job and an unchanged one never is.

If no model is configured, or the model fails, the caller raises or catches `ModelUnavailable` and
search runs keyword-only (FR-S-02). The model itself is chosen by ADR-0016's memory test; until the
team records that choice, no model is configured in deployment.
"""

import hashlib
from collections.abc import Sequence
from typing import Any, Protocol

DIMS = 384  # item_embedding.embedding is vector(384) (migration 0004)


class ModelUnavailable(Exception):
    """No embedding model is configured, it could not load, or it failed on this input."""


class IEmbed(Protocol):
    model_name: str
    dims: int

    def embed(self, texts: Sequence[str]) -> list[list[float]]:
        """One unit-length vector per text; raises ModelUnavailable on failure."""
        ...


def listing_text(item: dict[str, Any]) -> str:
    """What a listing is embedded from: its words only, never its owner, place or price."""
    parts = [item.get("title") or "", item.get("description") or ""]
    if item.get("search_terms"):
        parts.append(f"Also called: {item['search_terms']}")
    return ". ".join(p.strip() for p in parts if p and p.strip())


def text_hash(text: str) -> bytes:
    return hashlib.sha256(text.encode("utf-8")).digest()


def to_pgvector(v: Sequence[float]) -> str:
    """pgvector's text form, e.g. '[0.1,0.2,...]', for a bound parameter cast to vector."""
    if len(v) != DIMS:
        raise ModelUnavailable(f"the model gave {len(v)} numbers, the schema stores {DIMS}")
    return "[" + ",".join(f"{x:.6f}" for x in v) + "]"
