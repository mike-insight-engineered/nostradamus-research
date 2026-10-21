# Historical language resources

Status of each resource as of 2026-10-21. **Nothing below has been accessed or verified for this
project yet.** Descriptions reflect general knowledge and must be confirmed (see the registry
`outstanding_work`).

| Resource | Use in this project | Registry | Access / rights (to confirm) |
|---|---|---|---|
| Bibliothèques Virtuelles Humanistes (CESR, Tours), incl. Epistemon | Facsimiles; TEI transcriptions of Renaissance French texts | `RES-BVH-EPISTEMON` | Openly viewable; licence for reuse unconfirmed |
| Gallica (BnF) | Facsimiles of early editions; ARK identifiers | `RES-GALLICA` | Published conditions of use; current terms unconfirmed |
| BnF Catalogue général | Edition/exemplar identification | `RES-BNF-CATALOGUE` | Catalogue metadata |
| USTC | Edition identification, printers, dates | `RES-USTC` | Catalogue metadata |
| Dictionnaire du Moyen Français (ATILF) | Period senses (chiefly pre-1500; corroborate for sixteenth century) | `RES-DMF-ATILF` | Online; terms unconfirmed |
| Huguet, *Dictionnaire … du seizième siècle* | Principal sixteenth-century sense reference | `RES-HUGUET` | Print; digital access and rights unconfirmed |
| Godefroy | Older French senses | `RES-GODEFROY` | Likely public domain; digitisation terms unconfirmed |
| Cotgrave (1611) | Near-contemporary French→English glosses | `RES-COTGRAVE-1611` | Public domain by age |
| Estienne, *Dictionaire francoislatin* (1549) | Contemporary French↔Latin equivalents | `RES-ESTIENNE-1549` | Public domain by age |
| Nicot, *Thresor* (1606) | French with Latin equivalents | `RES-NICOT-1606` | Public domain by age |
| Frantext (ATILF) | Period usages / concordances | `RES-FRANTEXT` | Subscription understood; licence unconfirmed |
| Perseus | Latin lexica and morphology | `RES-PERSEUS` | Per-text licences; mainly classical Latin |
| CAMENA | Neo-Latin texts | `RES-CAMENA` | URL and terms to confirm |
| Du Cange, *Glossarium* | Post-classical Latin | `RES-DU-CANGE` | Online edition to locate |

## How resources enter the pipelines

Only through `data/annotations/lexical_evidence.jsonl`, one entry per consulted sense, with full
citation, locator, rights status and a named verifier. Pipelines C and D cite only these entries, and
abstain from evidence-dependent claims when none match. **The store is currently empty.**

## Still to identify (with a specialist)

- Historical grammars of sixteenth-century French and of Neo-Latin.
- Occitan/Provençal lexical resources relevant to Provence (for Milestone 2).
- Resources on astrological, classical and biblical reference in Renaissance texts.
