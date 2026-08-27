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

Terminology was generated from the target/reference text. The standard chemistry configuration uses
four candidate extractor families: LLM target extraction, Stanza/UD, XLM-R/NOBI, and spaCy. The
verifier layer can add PubChem, ChEBI, ChEMBL, MeSH, NCI, AGROVOC, IATE, and Wikidata evidence.

For final benchmark runs, the target configuration is a candidate pool of about `40` terms followed
by LLM refinement to at most `n = 8` final `refined` terms per segment.

Term groups:

- `verified`: externally backed by PubChem, IATE, or Wikipedia/Wikidata.
- `llm`: proposed by the target-only LLM and verified to exist in the target text.
- `algorithmic`: regex/NER/algorithmic extraction.
- `refined`: selected by the final LLM refiner.

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
  --translator one-shot `
  --provider openai `
  --model gpt-4.1-mini `
  --translation-domain chemistry `
  --use-manifest-terminology `
  --metric sequence_similarity `
  --metric bleu `
  --metric chrf2++ `
  --metric target_term_coverage `
  --terminology-term-group verified `
  --max-manifest-terminology-terms 8 `
  --output reports/google-patents-en-de-verified.jsonl
```

This 60-row subset is candidate/verified terminology, so the example uses `verified`. Final
benchmark runs should use `refined` once the refiner has been applied. Add more
`--terminology-term-group` flags for broader diagnostics:

```powershell
--terminology-term-group refined `
--terminology-term-group verified `
--terminology-term-group llm `
--terminology-term-group algorithmic
```
