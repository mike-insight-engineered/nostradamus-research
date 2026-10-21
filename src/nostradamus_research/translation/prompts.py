"""Versioned prompt templates.

Each template file carries YAML front matter (``template_id``, ``version``,
``task``) followed by ``[system]`` and ``[user]`` sections. Placeholders use
``{{name}}``; rendering fails if any placeholder is left unfilled. The SHA-256
of the full file is recorded in every experiment manifest.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from importlib import resources
from pathlib import Path

import yaml

from ..models.experiment import PromptTemplateRef
from ..utils.hashing import sha256_text

_PLACEHOLDER = re.compile(r"\{\{(\w+)\}\}")
_SECTION = re.compile(r"^\[(system|user)\]\s*$", re.MULTILINE)


class PromptError(ValueError):
    pass


@dataclass(frozen=True)
class PromptTemplate:
    template_id: str
    version: str
    task: str
    description: str
    system: str
    user: str
    sha256: str

    @property
    def placeholders(self) -> set[str]:
        return set(_PLACEHOLDER.findall(self.system)) | set(_PLACEHOLDER.findall(self.user))

    def ref(self) -> PromptTemplateRef:
        return PromptTemplateRef(
            template_id=self.template_id, version=self.version, sha256=self.sha256
        )

    def render(self, **values: str) -> tuple[str, str]:
        missing = self.placeholders - set(values)
        if missing:
            raise PromptError(f"template {self.template_id}: missing values for {sorted(missing)}")

        def sub(text: str) -> str:
            return _PLACEHOLDER.sub(lambda m: values[m.group(1)], text)

        return sub(self.system), sub(self.user)


def parse_template(text: str, origin: str = "<string>") -> PromptTemplate:
    if not text.startswith("---"):
        raise PromptError(f"{origin}: missing front matter")
    try:
        _, front, body = text.split("---", 2)
    except ValueError as exc:
        raise PromptError(f"{origin}: malformed front matter") from exc
    meta = yaml.safe_load(front) or {}
    for key in ("template_id", "version", "task"):
        if key not in meta:
            raise PromptError(f"{origin}: front matter lacks {key!r}")
    parts = _SECTION.split(body)
    sections = dict(zip(parts[1::2], parts[2::2], strict=True))
    if set(sections) != {"system", "user"}:
        raise PromptError(f"{origin}: needs exactly one [system] and one [user] section")
    return PromptTemplate(
        template_id=str(meta["template_id"]),
        version=str(meta["version"]),
        task=str(meta["task"]),
        description=str(meta.get("description", "")),
        system=sections["system"].strip(),
        user=sections["user"].strip(),
        sha256=sha256_text(text),
    )


class PromptLibrary:
    def __init__(self, templates: dict[str, PromptTemplate]):
        self.templates = templates

    @classmethod
    def load(cls, directory: Path | None = None) -> PromptLibrary:
        templates: dict[str, PromptTemplate] = {}
        if directory is not None:
            files = [
                (p.name, p.read_text(encoding="utf-8")) for p in sorted(directory.glob("*.md"))
            ]
        else:
            pkg = resources.files("nostradamus_research.translation") / "prompt_templates"
            files = [
                (f.name, f.read_text(encoding="utf-8"))
                for f in sorted(pkg.iterdir(), key=lambda f: f.name)
                if f.name.endswith(".md")
            ]
        for name, text in files:
            t = parse_template(text, name)
            if t.template_id in templates:
                raise PromptError(f"duplicate template_id {t.template_id}")
            templates[t.template_id] = t
        return cls(templates)

    def get(self, template_id: str, expected_version: str | None = None) -> PromptTemplate:
        if template_id not in self.templates:
            raise PromptError(f"unknown prompt template {template_id!r}")
        t = self.templates[template_id]
        if expected_version is not None and t.version != expected_version:
            raise PromptError(
                f"prompt template {template_id} is version {t.version} but configuration pins "
                f"{expected_version}; update config/translation.yaml deliberately"
            )
        return t
