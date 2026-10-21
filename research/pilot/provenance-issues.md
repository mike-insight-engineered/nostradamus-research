# Unresolved provenance issues — Phase 2

| ID | Issue | Affects | Proposed resolution |
|---|---|---|---|
| PI-01 | Gallica pages (records and CGU) return HTTP 403 to the research environment, so the digitised copy's shelfmark was not read from the Gallica record | all Gallica witnesses | A human opens each ARK in a browser and records the "Source" shelfmark |
| PI-02 | Several BnF records list multiple physical copies; which one was digitised is unknown | FP-01, FP-03, FV-01, FV-02, FV-05, LA-04, MX-03 | Resolve via PI-01 |
| PI-03 | No USTC numbers: USTC search is client-side JavaScript | all | Manual USTC lookup; record in `catalogue_identifier` |
| PI-04 | Printer discrepancies between Wikisource metadata and BnF: *Alector* (Fradin vs "Alton"); *Heptaméron* (Benoist Prevost vs Vincent Sertenas) | FP-02, FP-04 | Check the title page and colophon in the facsimile; USTC |
| PI-05 | Dentière *Epistre*: stated imprint "Anvers, chez Martin l'empereur" probably false (record cites GLN-1329, a Geneva reference) | FP-05 | Specialist confirmation; record the stated imprint separately from the actual printer |
| PI-06 | Commons derivatives crop line ends at the gutter (Pantagruel) and reduce resolution (Gargantua) | MX-01, MX-02 | Verify against the Gallica full-resolution viewer |
| PI-07 | Ronsard *Amours* 1553 on Commons comes from Google Books via Internet Archive, not from the BnF copy cited by Wikisource | (alternate) | Use the BnF digitisation bpt6k700023 if this work is needed |
| PI-08 | Peletier and Meigret copies on Commons/IA are Ottawa microfiches of unidentified exemplars | MX-03, MX-05 | Use the Gallica direct scans (Peletier); find a direct scan for Meigret, or replace the slot |
| PI-09 | Cartier *Brief recit* on Gallica is a digitised microfilm (Omnisys, ca 1990) | excluded | Excluded from the manifest |
| PI-10 | BVH Epistemon licence conflict (CC BY-NC-SA 4.0 vs CC BY-NC-ND 2.0) and an unreachable XTF/TEI server | MX-01 (BVH TEI of the same copy exists) | Email bvh@univ-tours.fr |
| PI-11 | Valla 1526: the Wikisource text on this index is a French translation of unknown provenance; the work was composed in the 15th century | LA-04 | Do not use the Wikisource text; decide whether printing date suffices for inclusion |
| PI-12 | Same-work duplicates in the manifest: Colloquia (LA-02, LA-05); Moriae (LA-01, MX-04) | splits | Replace LA-05 and MX-04 with independent works if found; the splitter keeps same-work passages together anyway |
| PI-13 | Louise Labé, *Euvres* (1555) not found on fr.wikisource; Gallica not searchable from this environment | candidate authors | Human search of Gallica and BVH |
| PI-14 | BnF Pantagrueline Prognostication search returned a record flagged "Faux réalisé au XXe siècle" (cb46607961q), a reminder that digitised items can be modern forgeries | general | Always check catalogue notes before using a witness |
| PI-15 | The fixed-field date for Pantagruel spans 1531–1532 | MX-01 | Record as [1531/1532]; cite bibliography (e.g. New Rabelais Bibliography) once consulted |
