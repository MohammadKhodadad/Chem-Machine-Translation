# Google Patents Evaluation Subset

This folder contains a portable Google Patents evaluation subset. It is large enough to run a
100-example rerun without requiring the full local `data/` directory.

Files:

- `en.csv`: English source rows.
- `fr.csv`: French Google Patents reference rows.
- `de.csv`: German Google Patents reference rows.
- `google-patents-subset-100-manifest.jsonl`: Exact source/target row IDs selected for the
  100-example subset.
- `google-patents-agentic-10-eval.jsonl`: Existing smaller run output with predictions,
  references, and metrics.

Rerun the 100-example evaluation from the project root:

```powershell
uv run python scripts/evaluate_google_patents.py `
  --data-dir examples/google_patents_eval_subset `
  --strategy openai-agentic `
  --limit 100 `
  --min-input-tokens 128 `
  --max-input-tokens 384 `
  --output reports/google-patents-agentic-100-eval-rerun.jsonl
```

To avoid API calls and only verify loading/metrics:

```powershell
uv run python scripts/evaluate_google_patents.py `
  --data-dir examples/google_patents_eval_subset `
  --strategy dry-run `
  --limit 100 `
  --min-input-tokens 128 `
  --max-input-tokens 384 `
  --output reports/google-patents-dry-run-subset-100.jsonl
```

Current subset composition under the `128-384` token window:

- French: 85 examples.
- German: 15 examples.
- Portuguese, Spanish, and Chinese are not included because this local export has too few aligned
  English rows by `publication_number`.
