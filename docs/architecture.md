# Architecture

## Package Layout

- `chem_machine_translation.cli`: Typer-based command line interface.
- `chem_machine_translation.core`: shared domain schemas such as `Document` and
  `TranslationResult`.
- `chem_machine_translation.data`: Hugging Face and Google Patents dataset loaders.
- `chem_machine_translation.translation`: prompts, terminology layers, OpenAI agents, and
  translation strategy implementations.
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

## Agentic Translation

The `openai-agentic` strategy uses two roles:

- Translator: produces the initial target-language translation and later revisions.
- Reviewer: checks the candidate translation against the source and returns structured approval,
  issues, required changes, and rationale.

The workflow is capped at 3 review rounds by default. If the reviewer rejects a candidate, the
translator receives the source text, current translation, and required changes before revising. The
final report records whether the reviewer approved the final translation, how many rounds ran, and
the review notes.

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
