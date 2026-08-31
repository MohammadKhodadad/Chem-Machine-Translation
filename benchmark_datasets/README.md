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

The chemistry runner loads `config/benchmark_generation/chemistry.toml`. The legal runner loads
`config/benchmark_generation/legal.toml`, which builds both JRC article and JRC definition
benchmarks.

Use `scripts/generate_benchmark.py --config <path>` for custom configs. The old
`scripts/build_google_patents_eval_subset.py` and `scripts/build_jrc_acquis_eval_subset.py` scripts
are retained only as advanced debugging tools.

## One-Anchor Legal Benchmark

Use the one-anchor legal config when you want a small JRC anchored benchmark with the full legal
terminology stack:

```powershell
uv run python scripts/generate_benchmark.py --config config/benchmark_generation/legal_one_anchor.toml
```

This writes one complete anchored legal case for articles and one for definitions:

- `benchmark_datasets/jrc_acquis_anchored_articles_1_anchor`
- `benchmark_datasets/jrc_acquis_anchored_definitions_1_anchor`

The config uses `anchor_limit = 1`, which selects one `anchor_id` and expands it to all 20 ordered
language directions for the configured languages. It enables the legal LLM extractor, Stanza/UD,
XLM-R/NOBI, spaCy, IATE, Wikidata, UNTERM, and the LLM refiner.

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

- Chemistry config: `iate`, `wikidata`, `pubchem`, `chebi`, `chembl`, `mesh`, `nci`, and
  `agrovoc`.
- Legal config: `iate`, `wikidata`, and `unterm`.

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
`stanza_ud_dependency+xlmr_nobi+iate`. The `verified_by` field stores external evidence sources.
