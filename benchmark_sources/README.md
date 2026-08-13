# Benchmark Source Snapshots

This folder contains small tracked raw snapshots used to recreate benchmark datasets.

## Google Patents

- `google_patents_within_document_pairs_250_per_language_pair.jsonl`: source-target pairs
  selected within the same Google Patents document.
- `google_patents_within_document_pairs_250_per_language_pair_metadata.json`: row counts,
  language-pair counts, and schema metadata.
- Rows: 1,769 total.
- Main language pairs: `en-de`, `en-es`, `en-fr`, `en-zh`, `de-fr`, `fr-es`, and `zh-fr`
  have 250 rows each. The file also contains smaller `de-es` and `zh-de` slices.

Example benchmark rebuild command:

```powershell
uv run --no-sync python scripts/build_google_patents_eval_subset.py `
  --source-pairs-jsonl benchmark_sources/google_patents_within_document_pairs_250_per_language_pair.jsonl `
  --output-dir benchmark_datasets/google_patents_from_source_pairs `
  --limit 250 `
  --min-input-tokens 1 `
  --max-input-tokens 2048 `
  --extract-terminology `
  --terminology-model gpt-5.4-mini `
  --pubchem-terminology `
  --wikipedia-terminology `
  --iate-terminology `
  --chebi-terminology `
  --chembl-terminology `
  --mesh-terminology `
  --nci-terminology `
  --agrovoc-terminology `
  --terminology-cache data/google_patents_source_pairs_expanded_terminology_cache.jsonl `
  --terminology-workers 4
```

## EuroLex

- `eurolex_4000.jsonl`: 4,000 selected MultiEURLEX rows with `en`, `de`, `fr`, and `sk` text.
- `eurovoc_descriptors_subset.json`: EuroVoc descriptors needed by those rows.
- `eurolex_4000_metadata.json`: selection metadata for the snapshot.
- `eurolex_within_document_pairs_250_per_language_pair.jsonl`: source-target pairs selected
  from the row snapshot.
- `eurolex_within_document_pairs_250_per_language_pair_metadata.json`: row counts,
  language-pair counts, and schema metadata for the pair source.
- Source archive: `nlpaueb/multi_eurlex/multi_eurlex_translated.zip`.
- Selection: rows with all four languages, 32-1024 approximate tokens per language, ranked by exact EuroVoc descriptor matches in target text.
- Pair rows: 3,000 total, 250 per ordered pair across `en`, `de`, `fr`, and `sk`.
- Pair selection: same EuroLex document, ranked per direction by target-language EuroVoc
  descriptor matches. Pair rows keep `eurovoc_labels`, `eurovoc_descriptors`, and
  `eurovoc_target_terms`.

Recreate the tracked snapshot from the full ignored download:

```powershell
uv run --no-sync python scripts/create_eurolex_source_snapshot.py `
  --source-jsonl data/multi_eurlex/train.jsonl `
  --descriptor-json data/multi_eurlex/eurovoc_descriptors.json `
  --output-dir benchmark_sources `
  --limit 4000 `
  --language en `
  --language de `
  --language fr `
  --language sk `
  --min-input-tokens 32 `
  --max-input-tokens 1024
```

Recreate the tracked pair source from the row snapshot:

```powershell
uv run --no-sync python scripts/create_eurolex_source_pairs.py `
  --source-jsonl benchmark_sources/eurolex_4000.jsonl `
  --descriptor-json benchmark_sources/eurovoc_descriptors_subset.json `
  --output-jsonl benchmark_sources/eurolex_within_document_pairs_250_per_language_pair.jsonl `
  --metadata-output benchmark_sources/eurolex_within_document_pairs_250_per_language_pair_metadata.json `
  --limit 250 `
  --language en `
  --language de `
  --language fr `
  --language sk `
  --min-input-tokens 32 `
  --max-input-tokens 1024
```

Example benchmark rebuild command:

```powershell
uv run --no-sync python scripts/build_eurolex_eval_subset.py `
  --source-pairs-jsonl benchmark_sources/eurolex_within_document_pairs_250_per_language_pair.jsonl `
  --output-dir benchmark_datasets/eurolex_from_source_pairs `
  --limit 250 `
  --min-input-tokens 32 `
  --max-input-tokens 1024 `
  --extract-legal-terms `
  --legal-terminology-model gpt-5.4-mini `
  --iate-terminology `
  --wikipedia-terminology `
  --unterm-terminology `
  --legal-terminology-workers 4 `
  --legal-terminology-cache data/eurolex_legal_terminology_cache.jsonl
```

## JRC-Acquis / OPUS

The JRC-Acquis sources are source-pair snapshots built from public OPUS JRC-Acquis v3.0 Moses
aligned segment zips.

For the full source-to-dataset pipeline diagram, see `docs/jrc-acquis-pipeline.md`.

`scripts/create_jrc_acquis_source_pairs.py` downloads pair zips into the ignored
`data/opus_jrc_acquis` cache, then concatenates already-aligned segment pairs within document
boundaries and writes a portable source JSONL plus metadata. Use `--section-type article` or
`--section-type definition` to create separate benchmark sources for operative articles and
definition-heavy text.

The script supports two selection modes:

- `pairwise`: the original mode. Each ordered direction is selected independently.
- `anchored`: the preferred benchmark mode. The script first finds documents present across all
  selected language pairs, picks document anchors, then creates every ordered pair for each anchor.
  Reverse rows are exact source/target swaps from the same unordered pair chunk.

This path is preferred when we need `en`, `es`, `de`, `fr`, and `pt` legal benchmark data with
larger chunks and without relying on EuroVoc labels.

Current exploration sources:

- `jrc_acquis_articles_250_per_language_pair.jsonl`: 5,000 pairwise article/provision-focused
  chunks.
- `jrc_acquis_articles_250_per_language_pair_metadata.json`: pairwise article source metadata.
- `jrc_acquis_definitions_250_per_language_pair.jsonl`: 5,000 pairwise definition-focused chunks.
- `jrc_acquis_definitions_250_per_language_pair_metadata.json`: pairwise definition source
  metadata.
- `jrc_acquis_anchored_articles_250_per_language_pair.jsonl`: 5,000 anchored article/provision
  chunks generated with strict text-quality filtering.
- `jrc_acquis_anchored_articles_250_per_language_pair_metadata.json`: anchored article source
  metadata.
- `jrc_acquis_anchored_definitions_250_per_language_pair.jsonl`: 5,000 anchored definition chunks
  generated with legacy markup cleanup and strict text-quality filtering.
- `jrc_acquis_anchored_definitions_250_per_language_pair_metadata.json`: anchored definition source
  metadata.
- Languages: `en`, `es`, `de`, `fr`, and `pt`.
- Directions: all 20 ordered pairs, 250 chunks per direction.

Create the preferred anchored article-focused source:

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

Create the preferred anchored definition-focused source:

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

`--limit 250` in anchored mode means 250 document anchors. Because each anchor expands to all 20
ordered directions, this produces 250 rows per direction and 5,000 rows total.

`--quality-mode strict` rejects residual markup, control characters, all-caps blocks, obvious
list-continuation starts, bare-date starts, and incomplete trailing fragments. It does not perform
language identification.

Both preferred anchored article and definition snapshots use `--clean-legacy-markup` plus
`--quality-mode strict`. The first step removes legacy OPUS/JRC inline tags before normalization;
the second step applies benchmark-quality noise and boundary filters.

Create the original pairwise article-focused source:

```powershell
uv run --no-sync python scripts/create_jrc_acquis_source_pairs.py `
  --output-jsonl benchmark_sources/jrc_acquis_articles_250_per_language_pair.jsonl `
  --metadata-output benchmark_sources/jrc_acquis_articles_250_per_language_pair_metadata.json `
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
  --max-chunks-per-doc 1
```

Create the definition-focused source:

```powershell
uv run --no-sync python scripts/create_jrc_acquis_source_pairs.py `
  --output-jsonl benchmark_sources/jrc_acquis_definitions_250_per_language_pair.jsonl `
  --metadata-output benchmark_sources/jrc_acquis_definitions_250_per_language_pair_metadata.json `
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
  --max-chunks-per-doc 1
```

To create a generic unfiltered source snapshot, use the same command with `--section-type all` and
change the output file name to `jrc_acquis_chunks_250_per_language_pair.jsonl`.
