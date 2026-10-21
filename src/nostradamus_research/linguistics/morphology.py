"""Surface-level morphological and orthographic hints.

These are pattern-based *flags for attention*, e.g. a pre-reform spelling with
etymological consonants (``faict``, ``escript``) or a Latin inflectional
ending. They do not assign analyses and are never presented as findings.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from ..models.enums import Language
from .segmentation import tokenize


@dataclass(frozen=True)
class MorphHint:
    form: str
    hint: str


_FRENCH_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"^.*ſ.*$"), "contains long s (ſ); typographic, not lexical"),
    (
        re.compile(r"^(?i:es)[ct].+$"),
        "possible pre-consonantal 's' spelling (es- + consonant, cf. modern é-)",
    ),
    (re.compile(r"^.+(?i:ct)$"), "possible etymological -ct spelling (cf. faict/faire)"),
    (
        re.compile(r"^.+(?i:oit|oient)$"),
        "possible imperfect/conditional in -oit/-oient (modern -ait/-aient)",
    ),
    (re.compile(r"^.+(?i:ez)$"), "-ez ending: past participle plural or 2pl verb; check context"),
    (re.compile(r"^(?i:ung|vng)$"), "'ung' = indefinite article/numeral 'un'"),
    (re.compile(r"^.*[ãẽĩõũ].*$"), "nasal tilde abbreviation (omitted n/m)"),
    (re.compile(r"^.*[a-zA-Z]u[aeiou].*$"), "u may represent consonantal v"),
]
_LATIN_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"^.+(?i:orum|arum)$"), "genitive plural ending"),
    (re.compile(r"^.+(?i:ibus)$"), "dative/ablative plural ending"),
    (re.compile(r"^.+(?i:tur|ntur)$"), "passive/deponent verb ending"),
    (re.compile(r"^.+(?i:isse|isset|issent)$"), "perfect infinitive / pluperfect subjunctive"),
    (re.compile(r"^.+(?i:que)$"), "possible enclitic -que ('and') or relative form"),
    (re.compile(r"^.*[æœ].*$"), "ligature æ/œ (diphthong ae/oe)"),
]


def hints(text: str, language: Language) -> list[MorphHint]:
    patterns: list[tuple[re.Pattern[str], str]] = []
    if language in (Language.MIDDLE_FRENCH, Language.MIXED, Language.OCCITAN):
        patterns += _FRENCH_PATTERNS
    if language in (Language.LATIN, Language.MIXED):
        patterns += _LATIN_PATTERNS
    out: list[MorphHint] = []
    seen: set[tuple[str, str]] = set()
    for tok in tokenize(text):
        for rx, hint in patterns:
            if rx.match(tok.text) and (tok.text, hint) not in seen:
                seen.add((tok.text, hint))
                out.append(MorphHint(tok.text, hint))
    return out
