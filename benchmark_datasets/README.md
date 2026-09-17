# Benchmark Datasets

This folder contains benchmark-ready datasets built from portable source snapshots in
`benchmark_sources/`.

Use this README for the dataset build commands. Use `benchmark_sources/README.md` when you need to
recreate the source-pair JSONL snapshots themselves.

For the full benchmark generation flow and component details, see
`docs/benchmark-generation-pipeline.md`.

## Standard Commands

Use the config-driven runners for standard benchmark generation:

```powershell
uv run python scripts/generate_chemistry_benchmark.py
uv run python scripts/generate_legal_benchmark.py
```

The chemistry runner loads `config/benchmark_generation/chemistry.toml`, which uses
`mode = "per_direction"` and `bidirectional = true`. The legal runner loads
`config/benchmark_generation/legal.toml`, which uses `mode = "anchored"` and builds JRC article and
JRC definition benchmarks from 250 anchored legal cases.

Use `scripts/generate_benchmark.py --config <path>` for custom configs. The old
`scripts/build_google_patents_eval_subset.py` and `scripts/build_jrc_acquis_eval_subset.py` scripts
are retained only as advanced debugging tools.

## Checkpointed Resume

Config-driven benchmark generation is stage-based and resumable. Standard configs enable:

```toml
[checkpoint]
enabled = true
work_dir = "benchmark_work"
resume = true
run_id = "auto"
```

Intermediate selected rows, candidate-extraction results, external-evidence records, curated terms, and final
manifest rows are written under `benchmark_work/`, which is ignored by Git. If a run stops after
candidate extraction or external evidence enrichment, rerunning the same command continues from the
latest reusable checkpoint.

The final benchmark outputs remain clean under `benchmark_datasets/`; checkpoint files are only
internal build artifacts.

To continue after an interrupted run, rerun the same command. Completed checkpoint stages are reused
when their stage hash still matches the current config and inputs.

To force one stage to rerun, keep earlier stages reusable and set that stage to `false`. For example,
to reuse selected rows and candidate extraction but rerun external evidence enrichment:

```toml
[checkpoint.reuse]
selection = true
candidate_extraction = true
external_evidence_enrichment = false
llm_curation = true
manifest = true
```

The pipeline will still continue through LLM terminology curation, final manifest writing, and metadata after the
forced stage. A developer-only `start_at` / `stop_after` mode is not implemented yet.

## End-To-End Experiment Command

Use experiment configs when you want to generate or reuse a benchmark, run models, score outputs, and
write aggregate reports in one pipeline:

```powershell
uv run python scripts/run_benchmark_experiment.py --config config/experiments/legal_one_anchor_smoke.toml
```

The experiment layer composes benchmark configs, model-run configs, evaluation configs, and output
settings. It writes predictions, scores, `summary.json`, and `summary.md` under `runs/<experiment>/`.

## JRC Legal Benchmark

Use the standard legal runner when you want the 250-anchor JRC benchmark with the full legal
terminology stack:

```powershell
uv run python scripts/generate_legal_benchmark.py
```

This writes 250 anchored legal cases for articles and 250 for definitions:

- `benchmark_datasets/jrc_acquis_anchored_articles_250_anchors`
- `benchmark_datasets/jrc_acquis_anchored_definitions_250_anchors`

The config uses `mode = "anchored"` and `anchor_limit = 250`, which selects 250 `anchor_id` values
and expands each one to the ordered language directions available for the configured languages. It
enables the legal LLM extractor, Stanza/UD, XLM-R/NOBI, spaCy, local IATE, Wikidata, UNTERM, and the
LLM refiner.

For the smaller one-anchor report/smoke dataset, run:

```powershell
uv run python scripts/generate_benchmark.py --config config/benchmark_generation/legal_one_anchor.toml
```

## Metadata

Each config-driven build writes `metadata.json` in the benchmark output directory. It summarizes:

- row, direction, and anchor counts;
- source/target token percentiles;
- candidate, refined, and verified-refined term count percentiles;
- term-count bucket percentages, such as how many rows have `0`, `1-2`, `3-5`, or `6-8` terms;
- the same statistics overall, by direction, by source language, and by target language.

To add or refresh metadata for an already-generated benchmark without rerunning extraction:

```powershell
uv run python scripts/write_benchmark_metadata.py --config config/benchmark_generation/legal_one_anchor.toml
```

## Length Filtering

Length selection primarily happens when source snapshots are created in `benchmark_sources/`.
The standard benchmark configs do not set `min_input_tokens` or `max_input_tokens`; they consume the
already-selected source snapshots. JRC anchored configs use anchor completeness as the controlling
selection rule.

## Standard Terminology Configuration

The standard benchmark terminology pipeline is target-side. It stores a broad candidate pool first,
then a final LLM refiner should select up to `n = 8` terms per segment.

Standard LLM settings:

- Model: `gpt-4.1-mini`
- API mode: `responses`
- Max output tokens: `1024`
- Temperature: `0.0` in code

Standard candidate cap:

- Use `40` candidates before refinement.
- Use `8` final refined terms after refinement.

Standard extractor families:

- Chemistry config: `llm_chemistry`, `stanza_ud`, `xlmr_nobi`, and `spacy`.
- Legal config: `llm_legal`, `stanza_ud`, `xlmr_nobi`, and `spacy`.

Standard verifier sources:

- Chemistry config: `local_iate`, `wikidata`, `pubchem`, `chebi`, `chembl`, `mesh`, `nci`, and
  `agrovoc`.
- Legal config: `local_iate`, `wikidata`, and `unterm`.

`local_iate` reads official IATE exports from `data/iate/` by default. That directory is ignored by
Git; download the CSV locally and place it there before running standard configs.

Recommended: run the index-building script before benchmark generation:

```powershell
uv run python scripts/build_local_iate_index.py `
  --input data/iate/IATE_export.csv `
  --output data/iate/iate.sqlite
```

When `data/iate/iate.sqlite` exists, `local_iate` uses fast local SQLite lookups. If the index is
missing, `local_iate` will try to build it automatically the first time it is used. If automatic
indexing fails, it falls back to the raw local CSV export, which is much slower and can use a lot
more RAM.

The exact standard choices live in:

- `config/benchmark_generation/chemistry.toml`
- `config/benchmark_generation/legal.toml`

## Refiner And Evaluation Groups

The config-driven benchmark pipeline creates candidate/verified terminology and then appends the
refiner-selected `refined` group with `n = 8` terms per segment.

Terminology groups:

- `refined`: final terms selected by the LLM refiner.
- `verified`: candidate has external verifier evidence.
- `llm`: target-side LLM candidate that appears in the target/reference text.
- `algorithmic`: deterministic extractor candidate from Stanza/UD, XLM-R/NOBI, or spaCy.

Use `--terminology-term-group verified` for candidate-only manifests. Use
`--terminology-term-group refined --max-manifest-terminology-terms 8` once the final refiner stage
has been applied.

The detailed `source` field keeps candidate and verifier provenance, such as
`stanza_ud_dependency+xlmr_nobi+local_iate`. The `verified_by` field stores external evidence
sources.
