"""Minimal TEI P5 export/import for passages.

Export produces a small TEI document with a ``teiHeader`` (title, source
description) and two ``<ab>`` layers: ``type="diplomatic"`` and, if present,
``type="normalised"``. Import reads the diplomatic layer back *exactly*,
preferring ``<abbr>``/``<orig>``/``<sic>`` over ``<expan>``/``<reg>``/``<corr>``
inside ``<choice>`` so that editorial expansions never leak into the diplomatic
text.
"""

from __future__ import annotations

import xml.etree.ElementTree as ET

from ..models.passage import Passage

TEI_NS = "http://www.tei-c.org/ns/1.0"
_T = f"{{{TEI_NS}}}"
ET.register_namespace("", TEI_NS)

_DIPLOMATIC_CHOICE = {"abbr", "orig", "sic"}
_EDITORIAL_CHOICE = {"expan", "reg", "corr"}


def passage_to_tei(p: Passage) -> str:
    tei = ET.Element(f"{_T}TEI")
    header = ET.SubElement(tei, f"{_T}teiHeader")
    fdesc = ET.SubElement(header, f"{_T}fileDesc")
    tstmt = ET.SubElement(fdesc, f"{_T}titleStmt")
    ET.SubElement(tstmt, f"{_T}title").text = f"Passage {p.passage_id}"
    if p.author:
        ET.SubElement(tstmt, f"{_T}author").text = p.author
    pub = ET.SubElement(fdesc, f"{_T}publicationStmt")
    ET.SubElement(
        pub, f"{_T}p"
    ).text = f"Research transcription; data_origin={p.data_origin}; status={p.verification_status}"
    sdesc = ET.SubElement(fdesc, f"{_T}sourceDesc")
    bibl = ET.SubElement(sdesc, f"{_T}bibl")
    ET.SubElement(bibl, f"{_T}idno", {"type": "source"}).text = p.source_id
    ET.SubElement(bibl, f"{_T}idno", {"type": "work"}).text = p.work_id
    if p.witness_id:
        ET.SubElement(bibl, f"{_T}idno", {"type": "witness"}).text = p.witness_id
    if p.locator:
        ET.SubElement(bibl, f"{_T}citedRange").text = p.locator
    if p.date_text:
        ET.SubElement(bibl, f"{_T}date").text = p.date_text
    text = ET.SubElement(tei, f"{_T}text")
    body = ET.SubElement(text, f"{_T}body")
    dip = ET.SubElement(
        body,
        f"{_T}ab",
        {"type": "diplomatic", "{http://www.w3.org/XML/1998/namespace}lang": str(p.language)},
    )
    dip.text = p.diplomatic_transcription
    if p.normalised_reading is not None:
        norm = ET.SubElement(
            body, f"{_T}ab", {"type": "normalised", "ana": " ".join(p.normalisation_rules)}
        )
        norm.text = p.normalised_reading
    ET.indent(tei)
    return ET.tostring(tei, encoding="unicode", xml_declaration=False)


def _diplomatic_text(el: ET.Element) -> str:
    parts: list[str] = [el.text or ""]
    for child in el:
        tag = child.tag.removeprefix(_T)
        if tag == "choice":
            for opt in child:
                if opt.tag.removeprefix(_T) in _DIPLOMATIC_CHOICE:
                    parts.append(_diplomatic_text(opt))
                    break
        elif tag in _EDITORIAL_CHOICE or tag == "note":
            pass
        elif tag == "lb":
            parts.append("\n")
        else:
            parts.append(_diplomatic_text(child))
        parts.append(child.tail or "")
    return "".join(parts)


def diplomatic_text_from_tei(xml: str) -> str:
    """Extract the diplomatic layer from TEI. Raises ValueError if absent."""
    root = ET.fromstring(xml)
    for ab in root.iter(f"{_T}ab"):
        if ab.get("type") == "diplomatic":
            return _diplomatic_text(ab)
    raise ValueError("TEI document has no <ab type='diplomatic'> element")
