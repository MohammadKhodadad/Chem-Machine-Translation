# Chem Machine Translation

Chemistry-aware and legal/regulatory machine-translation benchmark tooling. The project builds
controlled source-target datasets, generates target-side benchmark terminology, translates with a
CLI-selectable provider, and writes comparison-ready JSONL or CSV reports.

## Goals

- Build reproducible Google Patents chemistry and JRC-Acquis legal benchmark datasets.
- Keep source and target lengths in a controlled range for fair model comparisons.
- Preserve chemical formulas, legal references, units, identifiers, named entities, and domain terms.
- Generate target-side terminology with extractor provenance and verifier evidence.
- Compare translation systems with general MT metrics plus terminology-sensitive coverage metrics.
- Use `gpt-4.1-mini` as the standard cost-sensitive LLM while keeping provider/model settings
  configurable.

## Setup

```powershell
uv sync --dev
```

Copy `.env.example` to `.env` and set `OPENAI_API_KEY` before using the OpenAI strategy.
Set `CHEM_MT_HF_TOKEN` and `CHEM_MT_HF_REPO_ID` to upload generated reports to Hugging Face.

## Standard Terminology Pipeline

The standard benchmark terminology setup is target-side and has three stages.

1. Candidate extraction uses four active extractor families:
   LLM target extractor, Stanza/UD, XLM-R/NOBI, and spaCy.
2. Verifier enrichment adds external evidence. Chemistry runs use sources such as PubChem, ChEBI,
   ChEMBL, MeSH, NCI, AGROVOC, IATE, and Wikidata. JRC/legal runs use IATE, Wikidata/Wikipedia,
   UNTERM, and any source-provided legal descriptors when available.
3. The LLM refiner selects the final benchmark terms from the candidate pool. The standard final
   cap is `n = 8` refined terms per segment.

The recommended production defaults are:

- Model: `gpt-4.1-mini`
- API mode: `responses`
- LLM max output tokens: `1024`
- Candidate pool target: about `40` candidates per segment before refinement
- Final refined terms: up to `8` terms per segment

`verified_by` is evidence for ranking, not an automatic keep decision. The refiner sees verifier
evidence and should prefer verified candidates when quality is comparable, but it can keep a strong
unverified term if it is central, complete, and translation-sensitive.

Retired/diagnostic methods such as NLTK n-grams and mSPLADE are not part of the standard pipeline.

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
  --translator one-shot `
  --provider openai `
  --model gpt-4.1-mini `
  --output-format jsonl
```

The command writes reports to `reports/` by default.
If Hugging Face upload variables are configured in `.env`, the generated report is uploaded after
it is written locally. Use `--no-upload` to skip that for a run.

Optionally inject terminology instructions from a text or markdown file:

```powershell
uv run chem-translate translate `
  --translator one-shot `
  --provider openai `
  --language German `
  --terminology-prompt data/terminology/german.md
```

When omitted, the terminology layer is empty and prompts are unchanged.

You can also ask an LLM to extract terminology from each source document before translation:

```powershell
uv run chem-translate translate `
  --translator one-shot `
  --provider openai `
  --language German `
  --extract-terminology `
  --terminology-max-terms 20
```

The extracted terms are injected as a terminology focus list. They are useful for consistency, but
they are not treated as an approved bilingual glossary unless they pass the benchmark refiner.

To enrich those extracted source terms with Wikidata candidate labels in the target language:

```powershell
uv run chem-translate translate `
  --translator one-shot `
  --provider openai `
  --language German `
  --wikidata-terminology
```

This enables LLM extraction and adds Wikidata labels when a matching entity has a target-language
label. These labels are still marked as candidates, not approved company terminology.

To use IATE first and fall back to Wikidata when IATE does not produce a target-language label:

```powershell
uv run chem-translate translate `
  --translator one-shot `
  --provider openai `
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
  --translator one-shot `
  --provider openai `
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

For the end-to-end benchmark generation pipeline, including every terminology extractor, verifier,
refiner, and evaluation group, see `docs/benchmark-generation-pipeline.md`.

The current benchmark dataset is:

`benchmark_datasets/google_patents_eval_subset_60_multidirectional`

It contains 60 Google Patents title+abstract translation pairs across English, German, and French:
`en-de`, `de-en`, `en-fr`, `fr-en`, `de-fr`, and `fr-de`.

Run a direction with:

```powershell
uv run --no-sync python scripts/evaluate_parallel_manifest.py `
  --dataset-dir benchmark_datasets/google_patents_eval_subset_60_multidirectional/en-de `
  --translator one-shot `
  --provider openai `
  --model gpt-4.1-mini `
  --metric sequence_similarity `
  --metric bleu `
  --metric chrf2++ `
  --metric target_term_coverage `
  --terminology-term-group verified `
  --max-manifest-terminology-terms 8 `
  --output reports/google-patents-en-de-verified.jsonl
```

Terminology benchmark groups:

- `refined`: final terms selected by the LLM refiner. This is the standard group for finalized
  terminology-sensitive benchmark runs.
- `verified`: externally backed terms. This remains useful for high-precision diagnostics and for
  manifests that have not yet run the refiner.
- `llm`: target-only LLM candidates that appear in the target reference text.
- `algorithmic`: deterministic extractor candidates.

The current small Google subset is candidate/verified terminology, so the example above uses
`verified`. Once a manifest has passed the final refiner stage, use `--terminology-term-group refined`
for the primary terminology-sensitive score. Repeat `--terminology-term-group` to evaluate
combinations, for example `refined` + `verified`.

## Current Translators

- `dry-run`: returns the source text unchanged. Use this to validate loading, truncation, and report generation without API cost.
- `one-shot`: single-pass translation through a configurable text-generation provider.

Providers are selected separately from translator behavior. The current provider is `openai`, which
also supports OpenAI-compatible local/internal endpoints through `OPENAI_BASE_URL` or
`--provider-base-url`.

## Model Notes

`gpt-4.1-mini` is a good first candidate for cost-sensitive batch translation. For higher-value
accuracy checks, compare it against a stronger model on a stratified sample before committing to the
full 10k-document run. The project keeps `--model` configurable so those comparisons do not require
code changes.
