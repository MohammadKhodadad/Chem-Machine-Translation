# Google Patents Evaluation Subset 300

This folder contains a portable English-to-target Google Patents evaluation subset generated from
`data/chemistry_patents.ndjson`. Each selected pair has both an English title and abstract and a
target-language title and abstract.

Run all commands below from the project root.

Composition:

- French: 50 examples.
- German: 50 examples.
- Spanish: 50 examples.
- Portuguese: 50 examples.
- Dutch: 50 examples.
- Chinese: 50 examples.

The subset has 300 English-to-target evaluation pairs in total. `en.csv` contains 293 unique English
source rows because some source patents include more than one target-language localization.

Files:

- `en.csv`: English source rows.
- `fr.csv`, `de.csv`, `es.csv`, `pt.csv`, `nl.csv`, `zh.csv`: target-language reference rows.
- `google-patents-subset-300-manifest.jsonl`: exact selected source/target pairs, including
  `family_id`, `publication_number`, language, source token count, and selection rule.

## Setup

Install dependencies:

```powershell
uv sync --dev
```

For the real OpenAI evaluation, copy `.env.example` to `.env` and set `OPENAI_API_KEY`.
No API key is needed for the dry run.

## Run The Evaluation

Rerun the full 300-example agentic evaluation:

```powershell
uv run python scripts/evaluate_google_patents.py `
  --data-dir examples/google_patents_eval_subset_300 `
  --strategy openai-agentic `
  --limit 50 `
  --min-input-tokens 128 `
  --max-input-tokens 384 `
  --output reports/google-patents-agentic-300-eval-rerun.jsonl
```

The command writes predictions, Google Patents references, per-row metrics, and review metadata to
`reports/google-patents-agentic-300-eval-rerun.jsonl`.

## Dry Run

To verify loading and metric generation without API calls, run:

```powershell
uv run python scripts/evaluate_google_patents.py `
  --data-dir examples/google_patents_eval_subset_300 `
  --strategy dry-run `
  --limit 50 `
  --min-input-tokens 128 `
  --max-input-tokens 384 `
  --output reports/google-patents-dry-run-subset-300.jsonl
```

Expected dry-run shape:

- 300 evaluated rows total.
- `n=50` for each of Chinese, Dutch, French, German, Portuguese, and Spanish.
