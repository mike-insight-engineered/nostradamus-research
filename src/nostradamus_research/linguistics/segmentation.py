"""Word and clause segmentation that preserves the original character spans."""

from __future__ import annotations

import re
from dataclasses import dataclass

# Words include letters, long s, apostrophes inside words and combining marks.
_WORD = re.compile(r"[^\W\d_](?:[^\W\d_]|['’̀-ͯ])*", re.UNICODE)
_CLAUSE_BREAK = re.compile(r"[.;:!?¶]+|,(?=\s)|\n+|/")


@dataclass(frozen=True)
class Token:
    text: str
    start: int
    end: int


def tokenize(text: str) -> list[Token]:
    return [Token(m.group(0), m.start(), m.end()) for m in _WORD.finditer(text)]


def fold(token: str) -> str:
    """Lookup key for a token: long s → s, lower case, strip elision apostrophes."""
    t = token.replace("ſ", "s").casefold()
    return t.split("'")[-1].split("’")[-1] if ("'" in t or "’" in t) else t


def clauses(text: str) -> list[str]:
    """Split at strong punctuation, comma+space, line breaks and virgules (/)."""
    parts = [p.strip() for p in _CLAUSE_BREAK.split(text)]
    return [p for p in parts if p]


def word_count(text: str) -> int:
    return len(tokenize(text))
