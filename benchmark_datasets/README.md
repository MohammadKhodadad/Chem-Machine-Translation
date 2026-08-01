# Benchmark Datasets

This folder contains benchmark-ready datasets, not small usage examples.

## Current Dataset

`google_patents_eval_subset_60_multidirectional`

- Source: `data/chemistry_patents.ndjson`
- Text field: title + abstract combined into `context`
- Languages: English, German, French
- Directions: `en-de`, `de-en`, `en-fr`, `fr-en`, `de-fr`, `fr-de`
- Rows: 10 per direction, 60 total
- Combined manifest:
  `benchmark_datasets/google_patents_eval_subset_60_multidirectional/google-patents-multidirectional-60-manifest.jsonl`

Each direction folder contains:

- `source.csv`
- `target.csv`
- `google-patents-<direction>-10-manifest.jsonl`

## Source-Pair Benchmark Datasets

`google_patents_source_pairs_10_per_pair`

- Source: `benchmark_sources/google_patents_within_document_pairs_250_per_language_pair.jsonl`
- Rows: 81 total across 9 directions.
- Directions: `de-es`, `de-fr`, `en-de`, `en-es`, `en-fr`, `en-zh`, `fr-es`, `zh-de`,
  and `zh-fr`.
- Most directions have 10 rows. `zh-de` has 1 row because the tracked source file only contains
  one `zh-de` pair.
- Combined manifest:
  `benchmark_datasets/google_patents_source_pairs_10_per_pair/google-patents-9-directions-81-manifest.jsonl`

Rebuild command:

```powershell
uv run --no-sync python scripts/build_google_patents_eval_subset.py `
  --source-pairs-jsonl benchmark_sources/google_patents_within_document_pairs_250_per_language_pair.jsonl `
  --output-dir benchmark_datasets/google_patents_source_pairs_10_per_pair `
  --limit 10 `
  --min-input-tokens 1 `
  --max-input-tokens 2048
```

`eurolex_source_pairs_10_per_pair`

- Source: `benchmark_sources/eurolex_within_document_pairs_250_per_language_pair.jsonl`
- Rows: 120 total across 12 directions.
- Directions: all ordered pairs across `en`, `de`, `fr`, and `sk`.
- EuroVoc terminology is included from exact target-side EuroVoc descriptor matches.
- Combined manifest:
  `benchmark_datasets/eurolex_source_pairs_10_per_pair/eurolex-12-directions-120-manifest.jsonl`

Rebuild command:

```powershell
uv run --no-sync python scripts/build_eurolex_eval_subset.py `
  --source-pairs-jsonl benchmark_sources/eurolex_within_document_pairs_250_per_language_pair.jsonl `
  --output-dir benchmark_datasets/eurolex_source_pairs_10_per_pair `
  --limit 10 `
  --min-input-tokens 32 `
  --max-input-tokens 1024
```

## Terminology Groups

Each manifest terminology item has a coarse `term_group` and detailed provenance.

- `verified`: candidate has PubChem, IATE, or Wikipedia/Wikidata evidence. This is the default
  benchmark terminology group.
- `llm`: target-only LLM candidate that was verified to appear in the target/reference text, but has
  no external database evidence.
- `algorithmic`: regex, NER, or other non-database extractor output.

The detailed `source` field keeps provenance such as `llm_target+iate`, `regex+pubchem`, or
`llm_target+wikipedia`. The `verified_by` field stores just the external evidence sources.

## Run A Direction

Use `scripts/evaluate_parallel_manifest.py` for direction folders.

Verified terminology only:

```powershell
uv run --no-sync python scripts/evaluate_parallel_manifest.py `
  --dataset-dir benchmark_datasets/google_patents_eval_subset_60_multidirectional/en-de `
  --strategy openai `
  --model gpt-5.4-mini `
  --metric sequence_similarity `
  --metric bleu `
  --metric chrf2++ `
  --metric target_term_coverage `
  --terminology-term-group verified `
  --output reports/google-patents-en-de-verified.jsonl
```

LLM-only terminology:

```powershell
uv run --no-sync python scripts/evaluate_parallel_manifest.py `
  --dataset-dir benchmark_datasets/google_patents_eval_subset_60_multidirectional/en-de `
  --strategy openai `
  --model gpt-5.4-mini `
  --metric target_term_coverage `
  --terminology-term-group llm `
  --output reports/google-patents-en-de-llm-terms.jsonl
```

Algorithmic-only terminology:

```powershell
uv run --no-sync python scripts/evaluate_parallel_manifest.py `
  --dataset-dir benchmark_datasets/google_patents_eval_subset_60_multidirectional/en-de `
  --strategy openai `
  --model gpt-5.4-mini `
  --metric target_term_coverage `
  --terminology-term-group algorithmic `
  --output reports/google-patents-en-de-algorithmic-terms.jsonl
```

All terminology groups:

```powershell
uv run --no-sync python scripts/evaluate_parallel_manifest.py `
  --dataset-dir benchmark_datasets/google_patents_eval_subset_60_multidirectional/en-de `
  --strategy openai `
  --model gpt-5.4-mini `
  --metric target_term_coverage `
  --terminology-term-group verified `
  --terminology-term-group llm `
  --terminology-term-group algorithmic `
  --output reports/google-patents-en-de-all-terms.jsonl
```

## Notes

The default target terminology evaluation group is `verified`. Include `llm` or `algorithmic` only
when you want broader, lower-trust diagnostic coverage.

## Build Google Patents From Source Pairs

The tracked source file
`benchmark_sources/google_patents_within_document_pairs_250_per_language_pair.jsonl` already
contains source-target patent pairs. Use `--source-pairs-jsonl` to convert it into benchmark
direction folders with `source.csv`, `target.csv`, and manifest files:

```powershell
uv run --no-sync python scripts/build_google_patents_eval_subset.py `
  --source-pairs-jsonl benchmark_sources/google_patents_within_document_pairs_250_per_language_pair.jsonl `
  --output-dir benchmark_datasets/google_patents_from_source_pairs `
  --limit 250 `
  --min-input-tokens 1 `
  --max-input-tokens 2048
```

Add `--extract-terminology` plus the desired database flags when you want the generated manifest
to include benchmark terminology.

## Build A EuroLex Dataset

For portable benchmark recreation, use the tracked EuroLex source-pair snapshot:

```powershell
uv run --no-sync python scripts/build_eurolex_eval_subset.py `
  --source-pairs-jsonl benchmark_sources/eurolex_within_document_pairs_250_per_language_pair.jsonl `
  --output-dir benchmark_datasets/eurolex_from_source_pairs `
  --limit 250 `
  --min-input-tokens 32 `
  --max-input-tokens 1024
```

The source-pair snapshot contains 3,000 rows: 250 per ordered pair across `en`, `de`, `fr`,
and `sk`. Each pair stores `source_text`, `target_text`, EuroVoc labels/descriptors, and exact
target-side EuroVoc term matches. Use the ignored `data/` download only when you want to
regenerate a different source snapshot or build from the full archive.

Use `scripts/download_eurolex_data.py` to download the public MultiEURLEX archive and EuroVoc
descriptor map into the ignored `data/` folder:

```powershell
uv run --no-sync python scripts/download_eurolex_data.py `
  --output-dir data/multi_eurlex
```

Then use `scripts/build_eurolex_eval_subset.py` for local MultiEURLEX/EuroLex JSONL exports. The
script expects rows with the standard MultiEURLEX shape: `celex_id`, multilingual `text`, and
`eurovoc_concepts` or `labels`.

EuroVoc labels are document-level metadata keywords/descriptors. They are not guaranteed to appear
as literal spans inside the source or target text. The builder preserves them in the manifest as
`eurovoc_labels` and `eurovoc_descriptors`. If a descriptor map is provided, descriptor terms are
added to terminology only when the target-language descriptor appears exactly in the target/reference
text. Pass `--no-eurovoc-terminology` to keep descriptors as metadata only.

Example:

```powershell
uv run --no-sync python scripts/build_eurolex_eval_subset.py `
  --source-jsonl data/multi_eurlex/train.jsonl `
  --descriptor-json data/multi_eurlex/eurovoc_descriptors.json `
  --output-dir benchmark_datasets/eurolex_eval_subset_generated `
  --source-language en `
  --target-language de `
  --target-language fr `
  --limit 50
```

For a larger all-pairs dataset, repeat `--language`. This creates every ordered pair among the
selected languages, with `--limit` rows per direction:

```powershell
uv run --no-sync python scripts/build_eurolex_eval_subset.py `
  --source-jsonl data/multi_eurlex/train.jsonl `
  --descriptor-json data/multi_eurlex/eurovoc_descriptors.json `
  --output-dir benchmark_datasets/eurolex_eval_subset_5_lang_250 `
  --language en `
  --language de `
  --language fr `
  --language el `
  --language sk `
  --limit 250
```

For a terminology-focused EuroLex benchmark, require at least one target-language EuroVoc descriptor
match and rank candidates by the number of matched target terms:

```powershell
uv run --no-sync python scripts/build_eurolex_eval_subset.py `
  --source-jsonl data/multi_eurlex/train.jsonl `
  --descriptor-json data/multi_eurlex/eurovoc_descriptors.json `
  --output-dir data/eurolex_eval_subset_4_lang_250_term_rich `
  --language en `
  --language de `
  --language fr `
  --language sk `
  --limit 250 `
  --min-target-terms 1 `
  --rank-by-target-terms
```

To add legal LLM candidates and verify them with IATE, Wikipedia/Wikidata, UNTERM, and EuroVoc
evidence, enable the legal terminology flags. EuroLex legal terminology uses only two groups:
`llm` for exact target spans proposed by the legal LLM, and `verified` for spans with external
evidence.

UNTERM has no documented public API, so the code treats it as best-effort evidence and fails closed
unless the public search page reports a positive result range.

```powershell
uv run --no-sync python scripts/build_eurolex_eval_subset.py `
  --source-jsonl data/multi_eurlex/train.jsonl `
  --descriptor-json data/multi_eurlex/eurovoc_descriptors.json `
  --output-dir data/eurolex_eval_subset_4_lang_10_legal_terms `
  --language en `
  --language de `
  --language fr `
  --language sk `
  --limit 10 `
  --min-target-terms 1 `
  --rank-by-target-terms `
  --extract-legal-terms `
  --legal-terminology-model gpt-5.4-mini `
  --iate-terminology `
  --wikipedia-terminology `
  --unterm-terminology `
  --legal-terminology-workers 4 `
  --legal-terminology-cache data/eurolex_legal_terminology_cache.jsonl
```
