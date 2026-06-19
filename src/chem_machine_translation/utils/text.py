from __future__ import annotations

import re

_WHITESPACE_RE = re.compile(r"\s+")


def normalize_text(text: str) -> str:
    return _WHITESPACE_RE.sub(" ", text).strip()


def approximate_token_count(text: str) -> int:
    """Count whitespace-delimited tokens without requiring tokenizer dependencies.

    This is intentionally conservative for early dataset filtering. Install the optional `tokens`
    extra later if exact model-token accounting becomes important.
    """

    normalized = normalize_text(text)
    if not normalized:
        return 0
    return len(normalized.split(" "))
