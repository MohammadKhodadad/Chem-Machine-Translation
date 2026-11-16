# Architecture

## Package Layout

- `chem_machine_translation.cli`: Typer-based command line interface.
- `chem_machine_translation.core`: shared domain schemas such as `Document` and
  `TranslationResult`.
- `chem_machine_translation.data`: generic Hugging Face loaders and dataset terminology generation
  utilities. Dataset-specific source-pair builders live under `scripts/`.
- `chem_machine_translation.translation`: prompts, terminology layers, provider adapters, and
  one-shot translation implementation.
- `chem_machine_translation.evaluation`: metric computation and JSONL/CSV report writers.
- `chem_machine_translation.integrations`: external service integrations such as Hugging Face
  uploads.
- `chem_machine_translation.utils`: shared helpers such as text normalization and approximate token
  counting.
- `chem_machine_translation.config`: Environment-backed runtime settings.

For the full benchmark generation flow, including source snapshots, candidate extractors, verifier
enrichment, final terminology refinement, and evaluation groups, see
`docs/benchmark-generation-pipeline.md`.

## Data Flow

1. The CLI selects one or more dataset aliases and target languages.
2. Dataset rows are streamed from Hugging Face, so large datasets do not need to be downloaded.
3. Dataset-specific fields are converted into a common `Document` object.
4. Source text is normalized and filtered to the configured token-count window.
5. Each English source document is translated into each selected target language.
6. Results are written as JSONL or CSV for manual review and later scoring.

Default target languages are French, German, Portuguese, Chinese, and Spanish.

## Evaluation Flow

[metrics.py](../src/chem_machine_translation/evaluation/metrics.py) owns metric selection and
dispatch. Ordinary `comet` passes a complete record to the official scorer without sentence
alignment; its normal encoder may truncate long inputs.
[aligned_comet.py](../src/chem_machine_translation/evaluation/aligned_comet.py) owns the two
opt-in document variants and their shared COMET token checks and block aggregation:

1. `reference_assignment_comet` embeds sentences with BGE-M3/CLS and independently solves
  reference-to-source and reference-to-candidate one-to-one assignments. Matching can cross.
2. `sentalign_comet` uses official SentAlign 2.0.0 with BGE-M3/CLS for those two pairwise alignments.
  It permits contiguous many-to-many links but preserves order. The adapter joins overlapping
  reference groups so sentence indices are not counted twice.
3. Each variant scores complete triples with COMET, penalizes incomplete blocks, and averages
  equally over its own blocks. Scoring inputs are checked before inference rather than silently
  truncated. Different group sizes imply different weighting and penalty counts.

`aligned_comet` is a compatibility name for reference assignment, not a separate algorithm.
Scorers are reused across rows by the experiment pipeline and manifest evaluator; reports retain
the selected metric names and detailed block audits. See the
[metrics guide](evaluation-metrics.md) for configuration, exact procedures, examples, and results.

[SEGALE](evaluation-metrics.md#segale) is related work, not an integrated scorer in this pipeline.
It aligns source to candidate using adaptive Vecalign selection and attaches references through
prepared source indices. That is distinct from both reference-anchored variants above.

## One-Shot Translation

The active translation path is one-shot translation. The translator builds one domain-aware prompt,
injects optional terminology instructions, and sends the request through a text-generation provider.

Translator behavior and provider backend are separate:

- `dry-run`: returns the source text unchanged for pipeline checks.
- `one-shot`: sends a single translation request through a provider.
- `openai` / `openai-compatible`: provider adapters for the OpenAI Responses API shape, including
  local or internal services exposed through an OpenAI-compatible endpoint.

Prompt domain is explicit and reproducible. Benchmark runs can use `--translation-domain chemistry`,
`legal`, `generic`, or `auto`; `auto` maps Google Patents to chemistry prompts and JRC/EuroLex to
legal prompts. When `--use-manifest-terminology` is set, selected manifest terms are injected into
the prompt. Candidate-only manifests typically use `verified`; finalized terminology manifests should
use the refiner-selected `refined` group.

## Dataset Mapping

### `dolma`

Source: `BASF-AI/dolma-chem-only-query-generated`

Initial text fields:

- `paragraph`
- `generated_query`

The generated query is included because it gives useful terminology coverage and tests whether the
strategy preserves question intent as well as chemistry content.

### `chemrxiv`

Source: `BASF-AI/ChemRxiv-Papers`

Initial text fields:

- `title`
- `abstract`

The abstract can exceed the target budget, so rows are filtered by approximate token count instead
of being truncated.

## Accuracy Considerations

Chemistry translation should be evaluated beyond generic fluency. Useful checks include:

- preservation of formulas and abbreviations such as `CO2`, `Zr/ZIF-8`, `C(sp3)-H`;
- preservation of units, values, pH, temperatures, pressures, and concentrations;
- no hallucinated reaction conditions or catalysts;
- no dropped negations or qualifiers;
- target-language readability for scientific prose.

The next step should be a small multilingual benchmark with manual review columns before running
10k documents.
