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

The manifest can also include a structured `terminology` list per source-target row. These mappings
are generated before evaluation and are intended for terminology accuracy metrics, separate from
translation-time prompt injection.

## Setup

Install dependencies:

```powershell
uv sync --dev
```

For the real OpenAI evaluation, copy `.env.example` to `.env` and set `OPENAI_API_KEY`.
No API key is needed for the dry run.

## Run The Evaluation

Regenerate the subset from preprocessed language CSVs:

```powershell
uv run python scripts/build_google_patents_eval_subset.py `
  --source-dir data/preprocessed `
  --output-dir examples/google_patents_eval_subset_300 `
  --limit 50 `
  --min-input-tokens 128 `
  --max-input-tokens 384
```

To add terminology mappings during subset generation, include:

```powershell
  --extract-terminology `
  --pubchem-terminology `
  --iate-terminology `
  --wikipedia-terminology `
  --terminology-cache reports/google-patents-terminology-cache.jsonl
```

`--extract-terminology` uses an LLM only to propose target-reference spans. The builder verifies
that each span appears in the target text before PubChem, IATE, or Wikipedia/Wikidata checks.

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

## Terminology Pipeline Evaluation

The benchmark manifest can contain target-side terminology extracted during subset generation. The
evaluation scripts consume those manifest terms for terminology metrics such as
`target_term_coverage`.

Runtime translation terminology prompting is still available separately:

```powershell
uv run python scripts/evaluate_google_patents.py `
  --data-dir examples/google_patents_eval_subset_300 `
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
  --output reports/google-patents-agentic-terminology-refined-de-5.jsonl
```

The command writes any injected `terminology_section` for each evaluated row so runtime prompt
terminology can be audited alongside the prediction and metrics.

Recent smoke-test result for German with `--limit 5`:

- Output: `reports/google-patents-agentic-terminology-refined-de-5.jsonl`
- Rows: 5
- BLEU: 45.44
- chrF: 76.19
- Sequence similarity: 28.28

The terminology layer preserves element symbols such as `Mo`, `W`, `V`, `Cu`, and `Sb` without
external lookup, uses IATE for available terminology candidates, and only uses Wikidata as backup
when the Wikidata source label exactly matches the extracted source term.

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
