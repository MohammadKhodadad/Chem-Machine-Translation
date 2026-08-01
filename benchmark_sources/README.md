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
  --max-input-tokens 2048
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
  --max-input-tokens 1024
```
