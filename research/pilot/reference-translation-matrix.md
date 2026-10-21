# Reference translation availability report (remediation, 2026-10-21)

**No reference translation has been obtained, read, licensed or attached to any passage.** This report records
what is known to exist, how it was confirmed, which source text it follows, and whether it can lawfully serve
as an independent reference.

Evidence levels:
- **CONFIRMED:** a publisher or journal page found by web search gives the bibliographic details; the book
  itself was not seen.
- **RECALLED:** general knowledge only; must be verified.

Categories:
- **A:** usable now (public domain or openly licensed modern translation).
- **B:** exists, in copyright; needs written permission.
- **C:** none suitable; commission from a specialist.
- **D:** AI draft. Never ground truth; none produced.

## 1. Priority passages (one per category)

| Slot | Passage | Modern French | English | Underlying edition of the translation | Matches our witness? | Category | Action |
|---|---|---|---|---|---|---|---|
| **FV-01** | Pernette du Guillet, opening poem, *Rymes* 1545 | none known (the original French is close to modern French but needs a modernisation reference) | **CONFIRMED:** *Complete Poems: A Bilingual Edition*, ed. Karen Simroth James, trans. Marta Rijn Finch (Toronto: Iter / CRRS, 2010; The Other Voice, Toronto Series 6; ISBN 978-0-7727-2065-8) | **Not confirmed.** The publisher's description refers to "the first edition of the Rymes" (1545), but the edition's base text must be checked in the book | to check | B (EN); C (FR) | Request permission for one poem from Iter Press; commission an FR modernisation and a second, independent literal EN version |
| **FP-01** | du Bellay, *Deffence* I.ii opening (1549) | critical editions exist (editions, not translations; RECALLED) | **CONFIRMED:** Richard Helgerson, *Joachim Du Bellay: "The Regrets," with "The Antiquities of Rome," Three Latin Elegies, and "The Defense and Enrichment of the French Language"*, bilingual edition (Philadelphia: University of Pennsylvania Press, 2006; ISBN 978-0-8122-3941-6) | **Not confirmed.** Facing-page original printed; its source text is to be read in the book's note on the text | to check | B (EN); C (FR) | Request permission from Penn Press; commission an FR modernisation and a second literal EN version |
| **LA-01** | Erasmus, *Moriae* 1512, sig. Aa iiij r | several (e.g. P. de Nolhac; RECALLED, rights status unknown) | **CONFIRMED:** Clarence H. Miller, *The Praise of Folly* (New Haven: Yale University Press, 1979) | **Confirmed (publisher/search summary):** Miller's own critical Latin text for the Amsterdam edition (ASD), collated from the 36 lifetime editions. **Not the 1512 text** | probably (the passage is in the early part of the speech), but the wording must be compared with 1512 | B (EN); C (FR) | Compare the passage wording with the ASD apparatus; request permission from Yale; commission an FR translation |
| **MX-01** | Rabelais, *Pantagruel* [1532], ch. vi | modern-French versions exist (RECALLED) | T. Urquhart (1653) is **public domain** but in early-modern English, from a later French text; Frame (1991) and Screech (2006) RECALLED, in copyright | No translation found that is based on the **1532 Nourry** text. Modern translations generally follow later or critical texts | **unlikely**: Rabelais revised the chapter in later editions | C (both) | Commission FR and EN from a Rabelais specialist working from the verified 1532 transcription |

**Ranking for acquisition** (which references can be legally obtained and independently evaluated):
1. FV-01: complete bilingual scholarly edition; short poem; a single permission request.
2. FP-01: bilingual scholarly edition; short passage.
3. LA-01: authoritative translation, but an edition mismatch must be checked.
4. MX-01: commissioning required.

Even where a published translation is licensed, the project still needs **at least one commissioned literal
reference per language**. Published translations are literary, may follow another edition, and are likely to
appear in model pretraining data (a contamination risk). Both kinds should be kept, each recorded as a separate
`ReferenceTranslation`.

## 2. Other slots (RECALLED unless marked; to verify)

| Slot | Work | Known translations | Category |
|---|---|---|---|
| FP-02 | *Heptaméron* | EN: P. A. Chilton (Penguin, 1984). Manuscript-based editions differ from Gruget 1559 | B / C |
| FP-03 | Crenne, *Songe* | none known | C |
| FP-04 | Aneau, *Alector* | none known | C |
| FP-05 | Dentière, *Epistre* | EN: M. B. McKinley (Univ. of Chicago Press, 2004) | B / C |
| FV-02 | du Bellay, *L'Olive* | partial selections | C |
| FV-03 | Ronsard, *Continuation* | selections (Penguin *Selected Poems*) | B / C |
| FV-04 | Marot, *Œuvres* 1547 | selections | C |
| FV-05 | *Marguerites* | partial | C |
| LA-02 / LA-05 | Erasmus, *Colloquia* | EN: C. R. Thompson (Chicago 1965; CWE 39–40), from the enlarged collections | B / C |
| LA-03 | Bèze, *Poemata* 1548 | EN: K. M. Summers, *A View from the Palatine* (2001) | B / C |
| LA-04 | Valla, *De libero arbitrio* | EN: C. E. Trinkaus, in *The Renaissance Philosophy of Man* (1948) | B / C |
| MX-02 | *Gargantua* | as MX-01 | B / C |
| MX-03 | Peletier, *Dialogue* | none known | C |
| MX-04 | *Moriae* (Greek proverb) | as LA-01 | B / C |
| proposed MX-05 | *Hypnérotomachie* 1546 | none known (English translations are of the Italian, not of Martin's French) | C |
| proposed LA-05 | Atrocianus, *Elegia* 1528 | none known | C |

Translation assignments for the four priority passages: `research/pilot/translation-assignments/`.
