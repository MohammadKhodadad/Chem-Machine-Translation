# Model Selection

The default model is `gpt-4.1-mini` because it is a practical starting point for cost-sensitive
translation batches. Before translating 10k documents, run a small comparison across target
languages and review chemistry preservation.

## Suggested Comparison

Use the same sampled documents for every candidate model:

```powershell
uv run chem-translate translate --language German --strategy openai-agentic --model gpt-4.1-mini --limit 20
uv run chem-translate translate --language German --strategy openai-agentic --model gpt-4.1 --limit 20
```

Review outputs for:

- chemical notation preservation;
- numerical/unit preservation;
- technical term consistency;
- target-language grammar;
- dropped or added details.

## When To Use Stronger Models

Use a stronger model when:

- documents contain dense reaction mechanisms or materials notation;
- translated text is user-facing or used for retrieval/evaluation labels;
- manual review finds formula changes, omissions, or paraphrasing that changes meaning.

Use `gpt-4.1-mini` when:

- the benchmark shows acceptable technical fidelity;
- translation is used for exploratory retrieval experiments;
- budget and throughput matter more than marginal fluency.
