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
- Chemistry terminology is generated during the benchmark build. All rows have terminology; 72 rows
  have at least one externally verified term for default `target_term_coverage`.
- Combined manifest:
  `benchmark_datasets/google_patents_source_pairs_10_per_pair/google-patents-9-directions-81-manifest.jsonl`

Rebuild command:

```powershell
uv run --no-sync python scripts/build_google_patents_eval_subset.py `
  --source-pairs-jsonl benchmark_sources/google_patents_within_document_pairs_250_per_language_pair.jsonl `
  --output-dir benchmark_datasets/google_patents_source_pairs_10_per_pair `
  --limit 10 `
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
  --terminology-cache data/google_patents_source_pairs_10_expanded_terminology_cache.jsonl `
  --terminology-workers 4
```

`eurolex_source_pairs_10_per_pair`

- Source: `benchmark_sources/eurolex_within_document_pairs_250_per_language_pair.jsonl`
- Rows: 120 total across 12 directions.
- Directions: all ordered pairs across `en`, `de`, `fr`, and `sk`.
- Legal terminology is generated during the benchmark build. All rows have terminology; all 120 rows
  have at least one externally verified term for default `target_term_coverage`.
- Verification sources include IATE, EuroVoc, and Wikipedia/Wikidata. UNTERM is enabled as
  best-effort evidence and fails closed when the public search page does not report a positive result.
- Combined manifest:
  `benchmark_datasets/eurolex_source_pairs_10_per_pair/eurolex-12-directions-120-manifest.jsonl`

Rebuild command:

```powershell
uv run --no-sync python scripts/build_eurolex_eval_subset.py `
  --source-pairs-jsonl benchmark_sources/eurolex_within_document_pairs_250_per_language_pair.jsonl `
  --output-dir benchmark_datasets/eurolex_source_pairs_10_per_pair `
  --limit 10 `
  --min-input-tokens 32 `
  --max-input-tokens 1024 `
  --extract-legal-terms `
  --legal-terminology-model gpt-5.4-mini `
  --iate-terminology `
  --wikipedia-terminology `
  --unterm-terminology `
  --legal-terminology-workers 4 `
  --legal-terminology-cache data/eurolex_source_pairs_10_legal_terminology_cache.jsonl
```

`jrc_acquis_chunks`

- Source: `benchmark_sources/jrc_acquis_chunks_5_per_language_pair.jsonl` for the current review
  sample. The full source snapshot should use the same command with `--limit 250`.
- Languages: defaults to `en`, `es`, `de`, `fr`, and `pt`.
- Directions: all ordered pairs across the selected languages.
- Rows: controlled by the source snapshot; the current review source has 5 chunks per ordered
  direction.
- Chunking: already-aligned source-target segments are concatenated within document boundaries.
- Terminology: legal terminology can be generated from the target/reference chunk with IATE,
  Wikipedia/Wikidata, and UNTERM evidence.

Create the source-pair snapshot first:

```powershell
uv run --no-sync python scripts/create_jrc_acquis_source_pairs.py `
  --output-jsonl benchmark_sources/jrc_acquis_chunks_5_per_language_pair.jsonl `
  --metadata-output benchmark_sources/jrc_acquis_chunks_5_per_language_pair_metadata.json `
  --cache-dir data/opus_jrc_acquis `
  --language en `
  --language es `
  --language de `
  --language fr `
  --language pt `
  --limit 5 `
  --min-chunk-tokens 250 `
  --target-chunk-tokens 450 `
  --max-chunk-tokens 700 `
  --max-chunks-per-doc 1
```

Then build a benchmark dataset from that tracked source snapshot:

```powershell
uv run --no-sync python scripts/build_jrc_acquis_eval_subset.py `
  --source-pairs-jsonl benchmark_sources/jrc_acquis_chunks_5_per_language_pair.jsonl `
  --output-dir benchmark_datasets/jrc_acquis_chunks_5_per_pair `
  --language en `
  --language es `
  --language de `
  --language fr `
  --language pt `
  --limit 5 `
  --extract-legal-terms `
  --legal-terminology-model gpt-5.4-mini `
  --iate-terminology `
  --wikipedia-terminology `
  --unterm-terminology `
  --legal-terminology-workers 4 `
  --legal-terminology-cache data/jrc_acquis_legal_terminology_cache.jsonl
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
target-side EuroVoc term matches. Raw MultiEURLEX download and pair-source creation are documented
in `benchmark_sources/README.md`.

EuroVoc labels are document-level metadata keywords/descriptors. The dataset builder preserves them
in the manifest and can seed terminology from `eurovoc_target_terms`, which are already exact
target-side matches stored in the source JSONL. Pass `--no-eurovoc-terminology` to keep descriptors
as metadata only.

To add legal LLM candidates and verify them with IATE, Wikipedia/Wikidata, UNTERM, and EuroVoc
evidence, enable the legal terminology flags. EuroLex legal terminology uses only two groups: `llm`
for exact target spans proposed by the legal LLM, and `verified` for spans with external evidence.

UNTERM has no documented public API, so the code treats it as best-effort evidence and fails closed
unless the public search page reports a positive result range.

```powershell
uv run --no-sync python scripts/build_eurolex_eval_subset.py `
  --source-pairs-jsonl benchmark_sources/eurolex_within_document_pairs_250_per_language_pair.jsonl `
  --output-dir benchmark_datasets/eurolex_source_pairs_10_per_pair `
  --language en `
  --language de `
  --language fr `
  --language sk `
  --limit 10 `
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
