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

## Data Flow

1. The CLI selects one or more dataset aliases and target languages.
2. Dataset rows are streamed from Hugging Face, so large datasets do not need to be downloaded.
3. Dataset-specific fields are converted into a common `Document` object.
4. Source text is normalized and filtered to the configured token-count window.
5. Each English source document is translated into each selected target language.
6. Results are written as JSONL or CSV for manual review and later scoring.

Default target languages are French, German, Portuguese, Chinese, and Spanish.

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
the prompt. The default terminology group remains `verified`.

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
