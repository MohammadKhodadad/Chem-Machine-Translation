# Manuscript Revision Record

## Implemented Facts

- The primary unit is a bounded segment, not a full patent or legal document.
- Google Patents exact/high snapshot: 2,750 stored pairs; the active six-language, bidirectional build selects 4,500 evaluation rows across 18 populated directions. These are selected inputs, not 4,500 successfully completed annotations or predictions.
- JRC article snapshot: 250 anchors, five languages, 20 ordered directions, 5,000 pairs. Definition data are separate. The recorded source mean is 418.6 whitespace tokens, not approximately 256.
- Both active terminology builds use candidate/refined caps of 80/16. Chemistry lookup sources are local IATE, Wikidata, AGROVOC; articles use local IATE, Wikidata, UNTERM and also import earlier GLM-labelled candidates.
- Manifest terminology injection exposes reference-derived target terms. The paper labels it an oracle intervention, not source-only retrieval.
- Coverage implements normalized substring occurrence ratios. External evidence and LLM curation are not human or chemical-structure validation.
- Original drafting banners, reference instructions, unsupported benefit claims, and diagnostic appendices are absent from the main manuscript. Results are honestly pending.

## Proposed Protocol, Not Completed Work

- Compare identical segments and models with no terminology versus oracle terminology; retain domain prompts and decoding settings across each pair.
- Use corpus BLEU/chrF++, segment COMET/BERTScore, and strict/variant-aware coverage as the primary reporting subset. This is a paper recommendation, not a change to the full default metric configuration.
- Macro-average direction means; recompute corpus overlap. Confirm the chosen runner implements this reporting rather than averaging sentence BLEU.
- Separate pilot/prompt-development data by anchor/publication; audit identifier and normalized-text duplication, then perform grouped paired resampling with reversals kept together.
- Isolate extractor, external-evidence, and curation ablations while retaining exact-span acceptance. Imported GLM candidates must be isolated when comparing extractor families.

## Unresolved Details

- Pin patent upstream revision and release provenance. The supplied Hugging Face dataset URL returned HTTP 401 during verification; public availability and upstream judge/model provenance are not established. Its citation is an artifact URL based on local documentation, not a verified publication.
- Decide whether to retain the existing JRC segment lengths or regenerate a smaller approximately 256-token snapshot. The counter is whitespace-delimited and cannot support a comparable model-token mean for Chinese; report provider-token distributions separately if needed.
- Freeze a cross-domain translation roster, immutable provider identifiers where available, exact prompt/settings manifests, and a chemistry-matched translation configuration. The existing Luna model-run file is legal; the pilot nano/mini configurations do not establish a completed no-hints comparison.
- Recover exact GLM annotation model/run provenance. Pin extractor checkpoints and language models. The NOBI model card documents English ACTER training, so multilingual extraction quality requires validation.
- Freeze IATE export date/checksum and lookup cache versions. UNTERM does not cover German/Portuguese as official UN languages; lookup failures and uncovered languages need denominators.
- Complete publication/family/anchor leakage audits, independent annotation review, judge calibration, uncertainty settings, failure reporting, and final aggregation. Do not imply these were performed.
- Specify target venue and bibliography rules. The current numeric `thebibliography` is self-contained; `latex/references.bib` contains matching entries for later venue integration and is not consumed by the current renderer.

## Citation Checks

BLEU, SacreBLEU, chrF++, COMET, OPUS, and Stanza were checked against ACL Anthology title/author records. JRC-Acquis and BERTScore were checked against their arXiv records; JRC's record also confirms the LREC 2006 venue and pages. NOBI training scope was checked against its model card. AGROVOC, Wikidata, and UNTERM descriptions were checked against official resource pages. IATE's portal supplied no readable detailed about-page content, so no unsupported release/version details are asserted. Unresolvable citation markers in the deep-research report were not treated as verified bibliography entries; its structure-validation recommendations are not claimed as implemented methods.

## Build and Page Budget

```powershell
uv run --no-sync python scripts/render_paper_tex.py --compile-pdf
```

The main paper preserves the existing A4, 11-point, one-inch-margin format and compiles to five pages including references. This leaves at least one additional page within a six-page cap; final result tables and analysis will require another pagination check. No font/margin compression was used.

The existing appendices are preserved as supplementary source material, not updated or certified as current prompts:

```powershell
uv run --no-sync python scripts/render_paper_tex.py --include-appendix --output-dir docs/paper/build/supplement --compile-pdf
```

The six-page constraint applies to the default main build, not the optional appendix-inclusive build. The supplement has not been compiled in this revision.