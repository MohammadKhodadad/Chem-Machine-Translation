# Google Patents Multidirectional Eval Subset 60

This benchmark dataset contains 10 aligned patent title+abstract examples for each direction among
English, German, and French.

## Contents

Directions:

- `en-de`
- `de-en`
- `en-fr`
- `fr-en`
- `de-fr`
- `fr-de`

Each direction folder contains:

- `source.csv`
- `target.csv`
- `google-patents-<direction>-10-manifest.jsonl`

The combined manifest is:

`google-patents-multidirectional-60-manifest.jsonl`

## Terminology

Terminology was generated from the target/reference text with target-only LLM candidate extraction
plus PubChem, IATE, and Wikipedia/Wikidata evidence.

Term groups:

- `verified`: externally backed by PubChem, IATE, or Wikipedia/Wikidata.
- `llm`: proposed by the target-only LLM and verified to exist in the target text.
- `algorithmic`: regex/NER/algorithmic extraction.

Generated terminology summary:

- Total terminology rows: 785
- `verified`: 249
- `llm`: 512
- `algorithmic`: 24

## Run A Benchmark

Use the generic parallel-manifest evaluator for each direction folder.

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

By default, terminology evaluation should use `verified`. Add more `--terminology-term-group` flags
for broader diagnostics:

```powershell
--terminology-term-group verified `
--terminology-term-group llm `
--terminology-term-group algorithmic
```
