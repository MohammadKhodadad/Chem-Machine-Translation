# Google Patents Evaluation Subset

This folder contains only the Google Patents rows used for the 10-sample evaluation.

Files:

- `en.csv`: English source rows.
- `fr.csv`: French Google Patents reference rows.
- `de.csv`: German Google Patents reference rows.
- `google-patents-agentic-10-eval.jsonl`: Existing run output with predictions, references, and metrics.

Rerun the evaluation from the project root:

```powershell
uv run python scripts/evaluate_google_patents.py `
  --data-dir examples/google_patents_eval_subset `
  --strategy openai-agentic `
  --limit 10 `
  --output reports/google-patents-agentic-10-eval-rerun.jsonl
```

To avoid API calls and only verify loading/metrics:

```powershell
uv run python scripts/evaluate_google_patents.py `
  --data-dir examples/google_patents_eval_subset `
  --strategy dry-run `
  --limit 10 `
  --output reports/google-patents-dry-run-subset.jsonl
```
