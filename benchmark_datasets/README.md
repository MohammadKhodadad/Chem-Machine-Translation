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
