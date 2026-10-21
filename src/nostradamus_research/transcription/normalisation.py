"""Explicit, recorded, opt-in normalisation of historical spelling.

Safeguards (tested):

* the input (diplomatic) string is never mutated — a new normalised string is
  returned alongside a list of every individual change;
* only character-level substitutions within words are made: punctuation,
  word order and word boundaries are never touched;
* rules that involve editorial judgement (u/v, i/j, nasal tildes, ``&``) are
  never in a default rule set and must be requested by name;
* there is no "modernise" rule — lexical modernisation is translation, not
  normalisation.
"""

from __future__ import annotations

import re
from collections.abc import Callable, Iterable
from dataclasses import dataclass, field


@dataclass(frozen=True)
class Change:
    rule: str
    position: int
    original: str
    replacement: str


@dataclass(frozen=True)
class NormalisationResult:
    original: str
    normalised: str
    rules: tuple[str, ...]
    changes: tuple[Change, ...] = field(default_factory=tuple)

    @property
    def changed(self) -> bool:
        return self.original != self.normalised


@dataclass(frozen=True)
class Rule:
    name: str
    description: str
    editorial: bool  # True if the rule embodies a judgement an editor must sign off
    apply: Callable[[str], list[tuple[int, str, str]]]  # -> [(pos, old, new)]


def _char_map(mapping: dict[str, str]) -> Callable[[str], list[tuple[int, str, str]]]:
    def apply(text: str) -> list[tuple[int, str, str]]:
        return [(i, ch, mapping[ch]) for i, ch in enumerate(text) if ch in mapping]

    return apply


def _regex(
    pattern: str, repl: Callable[[re.Match[str]], str]
) -> Callable[[str], list[tuple[int, str, str]]]:
    rx = re.compile(pattern)

    def apply(text: str) -> list[tuple[int, str, str]]:
        return [(m.start(), m.group(0), repl(m)) for m in rx.finditer(text)]

    return apply


_VOWELS = "aeiouyàâéèêëîïôöùûüAEIOUY"

RULES: dict[str, Rule] = {
    "long_s": Rule("long_s", "ſ → s", False, _char_map({"ſ": "s"})),
    "ligatures_ae_oe": Rule(
        "ligatures_ae_oe",
        "æ → ae, Æ → AE (Latin); œ is kept as it remains in modern French",
        False,
        _char_map({"æ": "ae", "Æ": "AE"}),
    ),
    "u_v_consonantal": Rule(
        "u_v_consonantal",
        "intervocalic 'u' → 'v' (e.g. 'auoir' → 'avoir'); editorial",
        True,
        _regex(rf"(?<=[{_VOWELS}])u(?=[{_VOWELS}])", lambda m: "v"),
    ),
    "v_u_initial_vowel": Rule(
        "v_u_initial_vowel",
        "word-initial 'v' before a consonant → 'u' (e.g. 'vn' → 'un'); editorial",
        True,
        _regex(rf"(?<![\w])v(?=[^\W{_VOWELS}])", lambda m: "u"),
    ),
    "i_j_initial": Rule(
        "i_j_initial",
        "word-initial 'i' before a vowel → 'j' (e.g. 'iamais' → 'jamais'); editorial",
        True,
        _regex(rf"(?<![\w])i(?=[{_VOWELS}])", lambda m: "j"),
    ),
    "nasal_tilde": Rule(
        "nasal_tilde",
        "precomposed tilde vowel → vowel + m before b/p/m, else vowel + n "
        "(e.g. 'cõme' → 'comme', 'mõde' → 'monde'); editorial: always check the expansion",
        True,
        _regex(
            r"[ãẽĩõũ](?=([bpm])?)",
            lambda m: (
                {"ã": "a", "ẽ": "e", "ĩ": "i", "õ": "o", "ũ": "u"}[m.group(0)[0]]
                + ("m" if m.group(1) else "n")
            ),
        ),
    ),
    "ampersand": Rule("ampersand", "& → et; editorial", True, _char_map({"&": "et"})),
}

DEFAULT_SAFE_RULES = tuple(name for name, r in RULES.items() if not r.editorial)


class NormalisationError(ValueError):
    pass


def _words(text: str) -> list[str]:
    return re.findall(r"\S+", text)


def _punctuation(text: str) -> list[str]:
    return re.findall(r"[^\w\s&]", text)


def normalise(text: str, rules: Iterable[str]) -> NormalisationResult:
    """Apply named rules in order; return the new text plus a full change log."""
    names = tuple(rules)
    unknown = [n for n in names if n not in RULES]
    if unknown:
        raise NormalisationError(
            f"unknown normalisation rule(s): {unknown}; known: {sorted(RULES)}"
        )
    current = text
    changes: list[Change] = []
    for name in names:
        edits = RULES[name].apply(current)
        if not edits:
            continue
        out: list[str] = []
        last = 0
        for pos, old, new in edits:
            out.append(current[last:pos])
            out.append(new)
            last = pos + len(old)
            changes.append(Change(name, pos, old, new))
        out.append(current[last:])
        current = "".join(out)
    check_safeguards(text, current)
    return NormalisationResult(text, current, names, tuple(changes))


def check_safeguards(original: str, normalised: str) -> None:
    """Raise if normalisation altered word count/boundaries or punctuation."""
    if len(_words(original)) != len(_words(normalised)):
        raise NormalisationError("normalisation changed the number of words")
    if _punctuation(original) != _punctuation(normalised):
        raise NormalisationError("normalisation altered punctuation")
