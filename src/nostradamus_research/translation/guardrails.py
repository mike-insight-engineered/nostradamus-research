"""Detection of speculative or prophetic interpretation in translation output.

Translation (QC2) must not smuggle in interpretation (QC3). This module flags
— it never silently removes — output language suggestive of prophecy,
prediction or identification with later historical events, *unless* the same
term is already present in the source text.
"""

from __future__ import annotations

import re

from ..linguistics.segmentation import fold, tokenize


def folded_words(text: str) -> set[str]:
    return {fold(t.text) for t in tokenize(text)}


_INTERPRETIVE_PATTERNS: dict[str, re.Pattern[str]] = {
    "prophecy_language": re.compile(
        r"\b(prophec\w*|prophes\w*|prophéti\w*|prédi\w*|predict\w*|foretell\w*|foretold|presag\w*|"
        r"fulfil+ment|accompli\w* de la prophétie)\b",
        re.IGNORECASE,
    ),
    "future_event_reference": re.compile(
        r"\b(will come to pass|in the future|this refers to|ceci désigne|this foresees|"
        r"announces the (?:coming|arrival)|refers to the (?:french revolution|world war))\b",
        re.IGNORECASE,
    ),
    "later_historical_figure": re.compile(
        r"\b(napol[eé]on|hitler|kennedy|louis xvi|world war|guerre mondiale|révolution française|"
        r"french revolution|9/11|11 septembre)\b",
        re.IGNORECASE,
    ),
    "interpretive_gloss": re.compile(
        r"\b(i\.e\.|that is to say,? the|c'est-à-dire le|symboli[sz]\w*|allegor\w*|code[ds]? for|"
        r"anagram for|anagramme de)\b",
        re.IGNORECASE,
    ),
}


def speculative_flags(output: str | None, source_text: str) -> list[str]:
    if not output:
        return []
    source_words = folded_words(source_text)
    flags: list[str] = []
    for name, rx in _INTERPRETIVE_PATTERNS.items():
        for m in rx.finditer(output):
            term = m.group(0)
            if not (folded_words(term) <= source_words):
                flags.append(f"{name}: {term!r}")
                break
    return flags
