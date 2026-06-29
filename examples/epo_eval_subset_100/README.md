# EPO Evaluation Subset 100

This folder contains a portable English-to-target EPO evaluation subset generated from
`data/EPO.csv`. Each selected publication has aligned English, French, and German rows with
non-empty `context` text.

Run all commands below from the project root.

Composition:

- French: 50 examples.
- German: 50 examples.

The subset has 100 English-to-target evaluation pairs in total. `en.csv` contains 50 unique English
source rows because each selected source publication has both French and German reference rows.

Files:

- `en.csv`: English source rows.
- `fr.csv`, `de.csv`: target-language reference rows.
- `epo-subset-100-manifest.jsonl`: exact selected source/target pairs, including publication
  number, language, source token count, IPC codes, and selection rule.

## Setup

Install dependencies:

```powershell
uv sync --dev
```

For the real OpenAI evaluation, copy `.env.example` to `.env` and set `OPENAI_API_KEY`.
No API key is needed for the dry run.

## Run The Evaluation

Rerun the full 100-example dry-run evaluation:

```powershell
uv run python scripts/evaluate_epo.py `
  --data-dir examples/epo_eval_subset_100 `
  --strategy dry-run `
  --limit 50 `
  --min-input-tokens 128 `
  --max-input-tokens 384 `
  --output reports/epo-dry-run-subset-100.jsonl
```

Run an agentic evaluation:

```powershell
uv run python scripts/evaluate_epo.py `
  --data-dir examples/epo_eval_subset_100 `
  --strategy openai-agentic `
  --limit 50 `
  --min-input-tokens 128 `
  --max-input-tokens 384 `
  --output reports/epo-agentic-subset-100.jsonl
```

The command writes predictions, EPO references, per-row metrics, review metadata, and any injected
`terminology_section` to the output JSONL report.

## Terminology Pipeline Evaluation

To run the same evaluation with LLM-extracted terminology, IATE candidate labels first, Wikidata as
backup, and confidence-gated refinement:

```powershell
uv run python scripts/evaluate_epo.py `
  --data-dir examples/epo_eval_subset_100 `
  --strategy openai-agentic `
  --language German `
  --limit 5 `
  --min-input-tokens 128 `
  --max-input-tokens 384 `
  --iate-terminology `
  --wikidata-terminology `
  --refine-terminology `
  --terminology-confidence-threshold 0.85 `
  --terminology-max-refined-terms 8 `
  --output reports/epo-agentic-terminology-refined-de-5.jsonl
```

## Dry Run Shape

Expected dry-run shape:

- 100 evaluated rows total.
- `n=50` for French.
- `n=50` for German.
- Very low lexical scores are expected for dry run, because the source English text is copied as the
  prediction.
