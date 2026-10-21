"""Heuristic French/Latin identification by function words (with code-switch spans).

This is intentionally simple and inspectable: it counts high-frequency
function words characteristic of sixteenth-century French and of Latin, then
reports runs of consecutive Latin-marked tokens as candidate code-switches.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from ..models.enums import Language
from .segmentation import fold, tokenize

FRENCH_MARKERS = frozenset(
    [
        "le",
        "la",
        "les",
        "un",
        "une",
        "ung",
        "des",
        "du",
        "de",
        "et",
        "ou",
        "mais",
        "donc",
        "car",
        "que",
        "qui",
        "quoy",
        "dont",
        "en",
        "au",
        "aux",
        "ce",
        "cest",
        "ceste",
        "cestuy",
        "celle",
        "ces",
        "ses",
        "son",
        "sa",
        "leur",
        "nous",
        "vous",
        "ilz",
        "il",
        "elle",
        "ne",
        "pas",
        "point",
        "plus",
        "moins",
        "tres",
        "bien",
        "avec",
        "sans",
        "sur",
        "sous",
        "par",
        "pour",
        "comme",
        "si",
        "tout",
        "toute",
        "tous",
        "est",
        "estoit",
        "sont",
        "ont",
        "avoit",
        "faict",
        "dict",
        "lequel",
        "laquelle",
        "lesquelz",
        "aussi",
        "encores",
        "ja",
        "jamais",
    ]
)
LATIN_MARKERS = frozenset(
    [
        "et",
        "in",
        "est",
        "non",
        "ad",
        "cum",
        "quod",
        "qui",
        "quae",
        "quam",
        "sed",
        "ut",
        "ex",
        "de",
        "per",
        "sunt",
        "esse",
        "enim",
        "autem",
        "nam",
        "atque",
        "ac",
        "neque",
        "nec",
        "vel",
        "aut",
        "hic",
        "haec",
        "hoc",
        "ille",
        "illa",
        "illud",
        "ipse",
        "sic",
        "tamen",
        "etiam",
        "ita",
        "eius",
        "eorum",
        "nobis",
        "vobis",
        "quoque",
        "igitur",
        "ergo",
        "inter",
        "sine",
        "apud",
        "post",
        "ante",
        "sub",
        "super",
    ]
)
# Words in both lists ('et', 'de', 'qui') are ambiguous and contribute to neither.
_AMBIGUOUS = FRENCH_MARKERS & LATIN_MARKERS
_LATIN_ENDINGS = ("orum", "arum", "ibus", "itur", "untur", "atque", "que", "ae", "um", "us", "is")


@dataclass
class LanguageGuess:
    language: Language
    french_score: int
    latin_score: int
    code_switch_spans: list[str] = field(default_factory=list)
    heuristic: bool = True

    def as_dict(self) -> dict[str, object]:
        return {
            "language": str(self.language),
            "french_markers": self.french_score,
            "latin_markers": self.latin_score,
            "code_switch_spans": self.code_switch_spans,
            "method": "function-word heuristic (not authoritative)",
        }


def _latin_like(word: str) -> bool:
    w = fold(word)
    if w in _AMBIGUOUS:
        return False
    return w in LATIN_MARKERS or (
        len(w) > 4 and w.endswith(_LATIN_ENDINGS) and w not in FRENCH_MARKERS
    )


def identify(text: str, *, mixed_threshold: float = 0.2) -> LanguageGuess:
    tokens = tokenize(text)
    folded = [fold(t.text) for t in tokens]
    fr = sum(1 for w in folded if w in FRENCH_MARKERS and w not in _AMBIGUOUS)
    la = sum(1 for w in folded if w in LATIN_MARKERS and w not in _AMBIGUOUS)

    spans: list[str] = []
    run: list[str] = []
    for t in tokens:
        if _latin_like(t.text):
            run.append(t.text)
        else:
            if len(run) >= 2:
                spans.append(" ".join(run))
            run = []
    if len(run) >= 2:
        spans.append(" ".join(run))

    total = fr + la
    if total == 0:
        lang = Language.OTHER
    elif min(fr, la) / total >= mixed_threshold:
        lang = Language.MIXED
    else:
        lang = Language.MIDDLE_FRENCH if fr > la else Language.LATIN
    if lang is not Language.MIDDLE_FRENCH:
        spans = spans if lang is Language.MIXED else []
    return LanguageGuess(lang, fr, la, spans)
