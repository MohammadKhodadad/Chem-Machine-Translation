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

Run checks:

```powershell
uv run pytest
uv run ruff check .
```

## Current Strategies

- `dry-run`: returns the source text unchanged. Use this to validate loading, truncation, and report generation without API cost.
- `openai`: single-pass OpenAI translation with a chemistry-specific prompt.
- `openai-agentic`: translator agent plus strict chemistry reviewer agent. The reviewer approves or sends issues back for revision for up to 3 rounds by default.

## Model Notes

`gpt-4.1-mini` is a good first candidate for cost-sensitive batch translation. For higher-value
accuracy checks, compare it against a stronger model on a stratified sample before committing to the
full 10k-document run. The project keeps `--model` configurable so those comparisons do not require
code changes.
