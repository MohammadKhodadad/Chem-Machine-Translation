# Benchmark Datasets

This folder contains benchmark-ready datasets. The retained tracked source snapshots are the
anchored JRC-Acquis article and definition sources in `benchmark_sources/`.

## JRC-Acquis Anchored Sources

- Sources:
  `benchmark_sources/jrc_acquis_anchored_articles_250_per_language_pair.jsonl` for operative legal
  provisions and `benchmark_sources/jrc_acquis_anchored_definitions_250_per_language_pair.jsonl`
  for definition-heavy passages.
- Languages: defaults to `en`, `es`, `de`, `fr`, and `pt`.
- Directions: all ordered pairs across the selected languages.
- Rows: controlled by the source snapshot; the current anchored sources have 250 chunks per ordered
  direction from 250 document anchors.
- Chunking: already-aligned source-target segments are concatenated within document boundaries.
  Anchored mode emits exact reverse rows by swapping source/target for each unordered pair chunk.
- Terminology: legal terminology can be generated from the target/reference chunk with IATE,
  Wikipedia/Wikidata, and UNTERM evidence.

Create the anchored article source-pair snapshot:

```powershell
uv run --no-sync python scripts/create_jrc_acquis_source_pairs.py `
  --output-jsonl benchmark_sources/jrc_acquis_anchored_articles_250_per_language_pair.jsonl `
  --metadata-output benchmark_sources/jrc_acquis_anchored_articles_250_per_language_pair_metadata.json `
  --cache-dir data/opus_jrc_acquis `
  --language en `
  --language es `
  --language de `
  --language fr `
  --language pt `
  --limit 250 `
  --min-chunk-tokens 250 `
  --target-chunk-tokens 450 `
  --max-chunk-tokens 700 `
  --section-type article `
  --selection-mode anchored `
  --anchor-language en `
  --anchor-search-multiplier 20 `
  --clean-legacy-markup `
  --quality-mode strict
```

Create the anchored definition source-pair snapshot:

```powershell
uv run --no-sync python scripts/create_jrc_acquis_source_pairs.py `
  --output-jsonl benchmark_sources/jrc_acquis_anchored_definitions_250_per_language_pair.jsonl `
  --metadata-output benchmark_sources/jrc_acquis_anchored_definitions_250_per_language_pair_metadata.json `
  --cache-dir data/opus_jrc_acquis `
  --language en `
  --language es `
  --language de `
  --language fr `
  --language pt `
  --limit 250 `
  --min-chunk-tokens 250 `
  --target-chunk-tokens 450 `
  --max-chunk-tokens 700 `
  --section-type definition `
  --selection-mode anchored `
  --anchor-language en `
  --anchor-search-multiplier 20 `
  --clean-legacy-markup `
  --quality-mode strict
```

Build a benchmark dataset from either tracked source snapshot:

```powershell
uv run --no-sync python scripts/build_jrc_acquis_eval_subset.py `
  --source-pairs-jsonl benchmark_sources/jrc_acquis_anchored_articles_250_per_language_pair.jsonl `
  --output-dir benchmark_datasets/jrc_acquis_anchored_articles_250_per_pair `
  --language en `
  --language es `
  --language de `
  --language fr `
  --language pt `
  --limit 250 `
  --extract-stanza-terms `
  --use-nobi-extractor `
  --stanza-terminology-workers 2 `
  --iate-terminology `
  --wikipedia-terminology `
  --unterm-terminology `
  --pubchem-terminology `
  --chebi-terminology `
  --chembl-terminology `
  --mesh-terminology `
  --nci-terminology `
  --agrovoc-terminology
```

The JRC builder shows progress bars and reuses terminology for repeated anchored target chunks.
`--stanza-terminology-workers` parallelizes unique target chunk extraction with separate worker
processes. Use modest values when `--use-nobi-extractor` or many public verifier sources are enabled.

## Terminology Groups

Each manifest terminology item has a coarse `term_group` and detailed provenance.

- `verified`: candidate has PubChem, IATE, or Wikipedia/Wikidata evidence. This is the default
  benchmark terminology group.
- `llm`: target-only LLM candidate that was verified to appear in the target/reference text, but has
  no external database evidence.
- `algorithmic`: Stanza/UD, XLM-R/NOBI, or other non-database extractor output.

The detailed `source` field keeps all candidate and verifier provenance, such as
`stanza_ud_dependency+xlmr_nobi+iate`. The `verified_by` field stores just the external evidence
sources.
