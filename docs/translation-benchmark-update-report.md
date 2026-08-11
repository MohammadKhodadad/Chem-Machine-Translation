# Translation Benchmark Update Report

## Executive Summary

The benchmark pipeline was updated in three connected areas:

- JRC-Acquis is now handled as a source-first legal translation benchmark with larger aligned chunks
  and a preferred anchored selection mode.
- Translation prompts are now domain-aware, with separate chemistry, legal, and generic prompt
  policies.
- Benchmark evaluation now uses a single provider-backed one-shot translator that can switch between
  OpenAI, OpenAI-compatible hosted APIs, and local/internal model servers.

The result is a cleaner architecture: datasets are built from explicit source-pair JSONL files,
terminology is stored in benchmark manifests, and translation model/provider selection is controlled
from the benchmark runner instead of being hardcoded into separate translation strategies.

## JRC-Acquis Data Update

JRC-Acquis was added as the preferred legal benchmark source for larger multilingual chunks. It
replaces the earlier EuroLex/MultiEURLEX direction for this use case because JRC-Acquis provides
sentence-aligned parallel legal text through OPUS.

Current supported JRC languages are:

- English: `en`
- Spanish: `es`
- German: `de`
- French: `fr`
- Portuguese: `pt`

The important design decision is that we do not directly scrape or align EUR-Lex pages ourselves.
Instead, the source builder uses OPUS JRC-Acquis Moses files, where aligned source and target segment
files already contain corresponding lines. The builder then concatenates adjacent aligned segments
from the same document into larger chunks.

The JRC source-first flow is:

1. Build source-pair JSONL files from OPUS aligned segment files.
2. Inspect source quality directly from the JSONL snapshot.
3. Build benchmark datasets from the source JSONL.
4. Generate legal terminology into the benchmark manifest.
5. Run evaluation with the generic parallel-manifest evaluator.

The source builder supports two modes:

- `pairwise`: each ordered direction is selected independently.
- `anchored`: documents are selected first, then every selected document anchor is expanded into all
  ordered language pairs.

Anchored mode is preferred for benchmark presentation because every anchor has all 20 ordered
directions and reverse rows are exact source/target swaps.

Current tracked anchored JRC source snapshots:

- `benchmark_sources/jrc_acquis_anchored_articles_250_per_language_pair.jsonl`
- `benchmark_sources/jrc_acquis_anchored_definitions_250_per_language_pair.jsonl`

Each anchored source contains 250 document anchors. With five languages, each anchor expands into 20
ordered directions, for 5,000 source-target pairs per source type. Picking 25 anchors would create
25 rows per direction; to get 250 rows per direction, we pick 250 anchors.

The chunking settings are designed to avoid very short benchmark examples:

- minimum source chunk size: 250 approximate tokens;
- target source chunk size: 450 approximate tokens;
- maximum source chunk size: 700 approximate tokens;
- minimum segment size: 3 tokens per side;
- maximum segment size: 180 tokens per side;
- maximum source/target token ratio: 3.0;
- maximum chunks per document per ordered direction: 1.

Two section types are supported:

- `article`: provision-focused chunks where article markers appear near the start, such as
  `Article 11`, `Artikel 11`, `Articulo 11`, or `Artigo 11`.
- `definition`: chunks containing explicit legal-definition wording, such as "for the purposes of
  this Regulation" or "shall mean".

The quality check on the anchored 250-per-pair article and definition sources found no empty rows,
no corrupt replacement characters, no identical source/target pairs, no source/target token ratio
above 2.0, exactly 250 rows for each ordered direction, 250 complete anchors per source, and zero
reverse-pair mismatches. Manual samples looked aligned and appropriate for legal translation
evaluation. Article chunks are the stronger immediate benchmark source; definition chunks are useful
but may include surrounding legal context before the definition phrase. Some older JRC text contains
historical OCR/normalization artifacts, which should be noted in final benchmark reporting.

Anchored audit snapshot:

- Articles: 5,000 rows, 20 directions, 250 anchors, 250 rows per direction, mean source length
  427.6 approximate tokens.
- Definitions: 5,000 rows, 20 directions, 250 anchors, 250 rows per direction, mean source length
  484.8 approximate tokens.

### Anchored Word Coverage

The anchored files cover all five languages evenly as source languages. Because every direction has
its reverse row, total source-word coverage and total target-word coverage are identical within each
source file.

Article source coverage:

- rows: 5,000;
- anchors: 250;
- ordered directions: 20;
- rows per direction: 250;
- total source words: 2,138,058;
- total target words: 2,138,058;
- source words per row: min 251, mean 427.6, median 448.0, max 777;
- source-language mean words:
  - `de`: 392.3;
  - `en`: 423.5;
  - `es`: 459.9;
  - `fr`: 424.0;
  - `pt`: 438.4.

Definition source coverage:

- rows: 5,000;
- anchors: 250;
- ordered directions: 20;
- rows per direction: 250;
- total source words: 2,424,153;
- total target words: 2,424,153;
- source words per row: min 254, mean 484.8, median 471.0, max 783;
- source-language mean words:
  - `de`: 462.8;
  - `en`: 481.6;
  - `es`: 518.2;
  - `fr`: 488.5;
  - `pt`: 473.1.

### My Quality Evaluation

The anchored JRC sources are now suitable for benchmark dataset creation. Structurally, they are
much stronger than the earlier pairwise-only sources because every selected anchor has all 20
language directions and every reverse direction is an exact source/target swap. This makes
direction-level comparisons easier to explain and audit.

The article source is the best first choice for translation benchmarking. It contains operative EU
legal provisions with obligations, dates, article references, committees, customs duties, annexes,
and procedural language. These chunks test whether a translation system preserves legal effect and
cross-references.

The definition source is useful as a terminology-heavy legal benchmark. It contains explicit
definition patterns such as "the term ... shall mean", "for the purposes of this Convention", and
language-specific equivalents. It is valuable for terminology coverage, but it is not
definition-only: some chunks include titles, preambles, or surrounding context before the definition
section.

Known data-quality caveats:

- Some older JRC texts contain historical normalization/OCR artifacts, especially missing accents,
  all-caps source text, spacing around punctuation, and occasional misspellings.
- Chunk boundaries are document-bounded but not section-perfect; article chunks can start in the
  middle of a provision and definition chunks can include surrounding legal context.
- For non-English language pairs such as `de-fr` or `pt-es`, the row is a direct OPUS bilingual
  chunk for that unordered pair, not a translation generated through English. This is good for
  evaluation quality. The reverse row is then created by exact swapping.

Overall judgment: use the anchored article source as the primary legal benchmark source, and use
the anchored definition source as a secondary terminology-focused legal benchmark source.

### Detailed Source Quality Tests

I ran additional quality tests over both anchored JSONL files.

Language and direction coverage:

- Both files have 5,000 rows.
- Both files have 250 document anchors.
- Both files cover all 20 ordered language directions.
- Every direction has exactly 250 rows.
- Each language appears exactly 1,000 times as a source language and 1,000 times as a target
  language in each file.
- No anchors are incomplete.
- No reverse-pair mismatches were found.

Duplicate checks:

- Article source:
  - exact duplicate rows: 0;
  - duplicate source text within the same direction: 0.
- Definition source:
  - exact duplicate rows: 0;
  - duplicate source text within the same direction: 0.

Near-duplicate checks:

- Article source:
  - near-duplicate source pairs within the same direction: 6;
  - examples include closely related documents such as `jrc22000A0411_01` and
    `jrc22000A0411_02`, and repeated legal wording across `jrc21987A0207_03` and
    `jrc21987A0207_06`.
- Definition source:
  - near-duplicate source pairs within the same direction: 12;
  - examples include related document parts such as `jrc22006A0622_02` and
    `jrc22006A0622_03`.

These near duplicates look like real legal boilerplate or adjacent related instruments rather than
accidental duplicated rows. They are acceptable for a legal benchmark, but if the goal is maximum
topic diversity, we can add an optional near-duplicate filter later.

Noise checks:

- Article source:
  - empty rows: 0;
  - identical source/target rows: 0;
  - replacement-character rows: 0;
  - HTML/XML-tag-like rows: 0;
  - control-character rows: 0;
  - rows with source/target word ratio above 2.0: 0;
  - high-uppercase source rows: 4 English-source rows, all from the same historical all-caps
    document anchor.
- Definition source:
  - empty rows: 0;
  - identical source/target rows: 0;
  - replacement-character rows: 0;
  - control-character rows: 0;
  - rows with source/target word ratio above 2.0: 0;
  - HTML/XML-tag-like rows: 10, all caused by legacy OPUS markup such as
    `<(BLK0)LA ORG="CCF">EN</(BLK0)LA>` in document `jrc31985D0377`;
  - high-uppercase source rows: 24 German-source rows, 28 English-source rows, and 28
    French-source rows.

Language hint checks:

- No rows were flagged by the lightweight language-hint heuristic.
- This check used common function words per source language and is only a sanity check, not a full
  language identifier.

My quality conclusion from the deeper audit:

- The anchored article source is clean enough to use as the primary legal benchmark source now.
- The anchored definition source is useful and structurally valid, but before using it for a final
  presentation benchmark I would either remove the `jrc31985D0377` markup rows or add a small text
  cleanup step for legacy OPUS markup.
- The near-duplicate rate is low in both files and mostly reflects normal legal repetition.
- The high-uppercase rows are not alignment failures; they are source-format artifacts in older
  legal texts.

## Prompt Updates

The translation prompts were changed from one chemistry-specific prompt into explicit domain
profiles:

- `chemistry`: used for Google Patents and chemistry-heavy benchmark runs.
- `legal`: used for JRC-Acquis and EuroLex-style legal benchmark runs.
- `generic`: fallback for other parallel data.

The chemistry prompt preserves chemical formulas, reaction notation, element symbols, material and
protein names, registry-like identifiers, units, numeric values, citations, and mechanistic meaning.
It also tells the translator to follow approved terminology instructions when they are supplied.

The legal prompt preserves legal effect, obligations, prohibitions, permissions, conditions,
exceptions, scope, legal citations, article and paragraph references, document identifiers,
institution names, numbers, dates, currencies, and defined terms. It also blocks rewriting behavior:
the model should translate, not modernize, summarize, fix, or simplify the legal text.

The generic prompt keeps the same one-shot discipline for non-specialized datasets: translate the
source accurately, preserve identifiers and formatting cues, and follow approved terminology when
provided.

The benchmark runner now supports:

```powershell
--translation-domain chemistry
--translation-domain legal
--translation-domain generic
--translation-domain auto
```

`auto` maps Google Patents and patent datasets to chemistry, and maps JRC/EuroLex/Acquis datasets to
legal.

## Provider-Based One-Shot Translation

The translation strategy layer was simplified. The previous `openai` and `openai-agentic` strategy
classes were removed, along with the agentic review/revision module. The only real translation
strategy is now:

- `one-shot`: build one prompt, inject optional terminology, send one request to a provider.

The dry-run path remains:

- `dry-run`: return the source text unchanged for loading, metrics, and report checks.

Model execution is now handled by providers:

- `TextGenerationProvider`: small protocol with one `generate(...)` method.
- `OpenAIResponsesProvider`: provider implementation using `OpenAI(...).responses.create(...)`.
- OpenAI-compatible local/internal endpoints are supported through `OPENAI_BASE_URL` or
  `--provider-base-url`.

This keeps the benchmark runner stable while allowing model/backend changes through CLI options.

Example OpenAI-compatible local model setup:

```powershell
$env:OPENAI_BASE_URL="http://localhost:8000/v1"
$env:OPENAI_API_KEY="local"

uv run --no-sync python scripts/evaluate_parallel_manifest.py `
  --dataset-dir benchmark_datasets/jrc_acquis_anchored_articles_250_per_pair/en-es `
  --translator one-shot `
  --provider openai `
  --model local-model-name `
  --translation-domain legal `
  --output reports/jrc-local-model-en-es.jsonl
```

## Manifest Terminology In Evaluation

Benchmark terminology is no longer only an evaluation artifact. It can also be injected into the
translation prompt.

The new manifest-backed terminology layer reads `manifest_row["terminology"]`, filters terms by
`term_group`, and creates approved target-language terminology instructions for the translator.

Default behavior remains conservative:

- terminology metrics default to `verified`;
- prompt injection only happens when `--use-manifest-terminology` is explicitly set;
- the default injected terminology group is also `verified`.

Supported terminology groups remain:

- `verified`: terms backed by external sources or strict verification.
- `llm`: LLM-generated target candidates verified as text spans.
- `algorithmic`: regex/NER/algorithmic candidates.

Example terminology-aware JRC evaluation:

```powershell
uv run --no-sync python scripts/evaluate_parallel_manifest.py `
  --dataset-dir benchmark_datasets/jrc_acquis_anchored_articles_250_per_pair/en-es `
  --translator one-shot `
  --provider openai `
  --model gpt-5.4-mini `
  --translation-domain legal `
  --use-manifest-terminology `
  --terminology-term-group verified `
  --metric sequence_similarity `
  --metric bleu `
  --metric chrf2++ `
  --metric target_term_coverage `
  --output reports/jrc-acquis-articles-en-es.jsonl
```

## Evaluation Workflow

The benchmark evaluator remains `scripts/evaluate_parallel_manifest.py`. It supports both direction
folders and multidirectional root datasets that follow the common benchmark layout:

- `source.csv`
- `target.csv`
- `*manifest.jsonl`

Each manifest row points to the source and target rows, stores language direction metadata, and can
include terminology used by both translation prompt injection and terminology metrics.

The evaluator now controls:

- translator mode: `--translator dry-run|one-shot`;
- provider: `--provider openai|openai-compatible`;
- model: `--model`;
- provider endpoint: `--provider-base-url`;
- request timeout: `--provider-timeout`;
- prompt domain: `--translation-domain chemistry|legal|generic|auto`;
- manifest terminology prompt injection: `--use-manifest-terminology`;
- terminology group filtering: repeated `--terminology-term-group`;
- metrics: repeated `--metric`.

The output schema remains mostly stable. It still records the translation strategy field for
backward compatibility, and now also records the provider when one-shot translation is used.

Supported metrics include:

- `sequence_similarity`;
- `bleu`;
- `chrf2++`;
- `comet`;
- `target_term_coverage`;
- `terminology_success_rate`;
- `fsp_mqm`.

COMET and FSP/MQM remain optional heavier metrics. BLEU, chrF2++, sequence similarity, and
target-term coverage are better for fast iteration.

## What This Enables

This update makes the benchmark system more consistent and easier to present:

- JRC data handling is explicit and reproducible.
- Legal and chemistry translation are separated at the prompt level.
- Translation behavior is separated from model/provider backend.
- OpenAI-compatible local or internal models can be plugged in without changing benchmark code.
- Manifest terminology can be tested as both an input intervention and an output metric.
- The system avoids maintaining multiple overlapping translation strategies.

## Current Caveats

- Local/internal models currently need to expose an OpenAI-compatible HTTP API. A native Hugging Face
  in-process provider has not been implemented.
- `TranslationResult` still keeps some legacy output fields such as `approved` and `review_rounds`
  for schema stability, even though the agentic reviewer path has been removed.
- JRC definition chunks are definition-containing, not necessarily definition-only.
- Article chunks are recommended as the first legal benchmark source for model evaluation.

## Recommended Next Step

Run a small legal one-shot evaluation on JRC article chunks with verified manifest terminology, then
compare it against a dry-run and one local/internal model endpoint if available.
