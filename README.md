# Chem Machine Translation

Chemistry-aware document translation experiments for short scientific documents of roughly
256 tokens. The first version filters chemistry datasets to rows near that size, translates them
with a CLI-selectable strategy, and writes comparison-ready JSONL or CSV reports.

## Goals

- Translate about 10k chemistry documents across a small set of target languages.
- Translate each English source document into French, German, Portuguese, Chinese, and Spanish.
- Preserve chemical formulas, units, abbreviations, reaction conditions, citations, and named entities.
- Support multiple translation strategies behind one CLI.
- Start with `gpt-4.1-mini`, while keeping model and provider configuration easy to change.
- Compare samples from:
  - `BASF-AI/dolma-chem-only-query-generated`
  - `BASF-AI/ChemRxiv-Papers`

## Setup

```powershell
uv sync --dev
```

Copy `.env.example` to `.env` and set `OPENAI_API_KEY` before using the OpenAI strategy.
Set `CHEM_MT_HF_TOKEN` and `CHEM_MT_HF_REPO_ID` to upload generated reports to Hugging Face.

## CLI Usage

Preview sampled English source documents:

```powershell
uv run chem-translate sample
```

You can also use `uv run python -m chem_machine_translation.cli` with the same arguments.

Sampling defaults to both datasets and 10 documents per dataset between 192 and 256 approximate
whitespace tokens. To sample only one dataset:

```powershell
uv run chem-translate sample --dataset dolma
```

Run a dry-run pipeline check:

```powershell
uv run chem-translate translate --dry-run --limit 1
```

By default, each sampled English document is translated into French, German, Portuguese, Chinese,
and Spanish. Override this by passing `--language` one or more times.

Run OpenAI translation:

```powershell
uv run chem-translate translate `
  --strategy openai-agentic `
  --model gpt-4.1-mini `
  --output-format jsonl
```

The command writes reports to `reports/` by default.
If Hugging Face upload variables are configured in `.env`, the generated report is uploaded after
it is written locally. Use `--no-upload` to skip that for a run.

Optionally inject terminology instructions from a text or markdown file:

```powershell
uv run chem-translate translate `
  --strategy openai-agentic `
  --language German `
  --terminology-prompt data/terminology/german.md
```

When omitted, the terminology layer is empty and prompts are unchanged.

You can also ask an LLM to extract terminology from each source document before translation:

```powershell
uv run chem-translate translate `
  --strategy openai-agentic `
  --language German `
  --extract-terminology `
  --terminology-max-terms 20
```

The extracted terms are injected as a terminology focus list. They are useful for consistency, but
they are not treated as an approved bilingual glossary.

To enrich those extracted source terms with Wikidata candidate labels in the target language:

```powershell
uv run chem-translate translate `
  --strategy openai-agentic `
  --language German `
  --wikidata-terminology
```

This enables LLM extraction and adds Wikidata labels when a matching entity has a target-language
label. These labels are still marked as candidates, not approved company terminology.

To use IATE first and fall back to Wikidata when IATE does not produce a target-language label:

```powershell
uv run chem-translate translate `
  --strategy openai-agentic `
  --language German `
  --iate-terminology `
  --wikidata-terminology
```

The terminology layer tries IATE first, then uses Wikidata for extracted terms without an IATE
candidate.

To add an LLM refinement agent that can keep, replace, update, preserve, or drop terminology rows
before translation:

```powershell
uv run chem-translate translate `
  --strategy openai-agentic `
  --language German `
  --iate-terminology `
  --wikidata-terminology `
  --refine-terminology `
  --terminology-confidence-threshold 0.85 `
  --terminology-max-refined-terms 8
```

The refinement agent receives the full source context plus the extracted terms and candidates. Its
output is confidence-gated before it gets injected into the translator prompt. Low-confidence rows
and generic terms are dropped, while formulas, element symbols, units, and identifiers can still be
preserved exactly.

Run checks:

```powershell
uv run pytest
uv run ruff check .
```

Benchmark datasets live in `benchmark_datasets/`.

The current benchmark dataset is:

`benchmark_datasets/google_patents_eval_subset_60_multidirectional`

It contains 60 Google Patents title+abstract translation pairs across English, German, and French:
`en-de`, `de-en`, `en-fr`, `fr-en`, `de-fr`, and `fr-de`.

Run a direction with:

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

Terminology benchmark groups:

- `verified`: PubChem, IATE, or Wikipedia/Wikidata-backed terms. This is the default trusted group.
- `llm`: target-only LLM candidates verified to appear in the target reference text.
- `algorithmic`: regex/NER/algorithmic candidates.

Repeat `--terminology-term-group` to evaluate combinations, for example `verified` + `llm`.

## Current Strategies

- `dry-run`: returns the source text unchanged. Use this to validate loading, truncation, and report generation without API cost.
- `openai`: single-pass OpenAI translation with a chemistry-specific prompt.
- `openai-agentic`: translator agent plus strict chemistry reviewer agent. The reviewer approves or sends issues back for revision for up to 3 rounds by default.

## Model Notes

`gpt-4.1-mini` is a good first candidate for cost-sensitive batch translation. For higher-value
accuracy checks, compare it against a stronger model on a stratified sample before committing to the
full 10k-document run. The project keeps `--model` configurable so those comparisons do not require
code changes.
