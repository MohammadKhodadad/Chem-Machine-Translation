# Benchmark Datasets

This folder contains benchmark-ready datasets built from portable source snapshots in
`benchmark_sources/`.

Use this README for the dataset build commands. Use `benchmark_sources/README.md` when you need to
recreate the source-pair JSONL snapshots themselves.

For the full benchmark generation flow and component details, see
`docs/benchmark-generation-pipeline.md`.

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

- LLM extractor: `--extract-terminology` for Google Patents, `--extract-legal-terms` for JRC.
- Stanza/UD: enabled by default inside the terminology generator; for JRC pass
  `--extract-stanza-terms`.
- XLM-R/NOBI: `--use-nobi-extractor`.
- spaCy: `--use-spacy-extractor`.

Standard verifier flags:

- Google Patents chemistry: `--iate-terminology`, `--wikidata-terminology`,
  `--pubchem-terminology`, `--chebi-terminology`, `--chembl-terminology`,
  `--mesh-terminology`, `--nci-terminology`, and `--agrovoc-terminology`.
- JRC legal: `--iate-terminology`, `--wikipedia-terminology`, and `--unterm-terminology`.

## Google Patents Chemistry

Build the 250-row-per-pair Google Patents benchmark from the tracked source snapshot:

```powershell
uv run --no-sync python scripts/build_google_patents_eval_subset.py `
  --source-pairs-jsonl benchmark_sources/google_patents_within_document_pairs_250_per_language_pair.jsonl `
  --output-dir benchmark_datasets/google_patents_within_document_pairs_250_per_pair `
  --language de `
  --language en `
  --language es `
  --language fr `
  --language ru `
  --language zh `
  --limit 250 `
  --extract-terminology `
  --terminology-model gpt-4.1-mini `
  --terminology-max-terms 40 `
  --use-nobi-extractor `
  --use-spacy-extractor `
  --terminology-workers 2 `
  --iate-terminology `
  --wikidata-terminology `
  --pubchem-terminology `
  --chebi-terminology `
  --chembl-terminology `
  --mesh-terminology `
  --nci-terminology `
  --agrovoc-terminology
```

`--extract-terminology` enables the LLM target extractor. The standard command also keeps the
deterministic Stanza/UD extractor, then adds XLM-R/NOBI and spaCy explicitly.

## JRC-Acquis Articles

Build the 250-row-per-pair JRC article/provision benchmark:

```powershell
uv run --no-sync python scripts/build_jrc_acquis_eval_subset.py `
  --source-pairs-jsonl benchmark_sources/jrc_acquis_anchored_articles_250_per_language_pair.jsonl `
  --output-dir benchmark_datasets/jrc_acquis_anchored_articles_250_per_pair `
  --language en `
  --language es `
  --language de `
  --language fr `
  --language pt `
  --limit 250 `
  --extract-legal-terms `
  --legal-terminology-model gpt-4.1-mini `
  --legal-terminology-max-terms 40 `
  --legal-terminology-workers 2 `
  --extract-stanza-terms `
  --stanza-terminology-max-terms 40 `
  --stanza-terminology-workers 2 `
  --use-nobi-extractor `
  --use-spacy-extractor `
  --iate-terminology `
  --wikipedia-terminology `
  --unterm-terminology
```

## JRC-Acquis Definitions

Build the 250-row-per-pair JRC definition-heavy benchmark:

```powershell
uv run --no-sync python scripts/build_jrc_acquis_eval_subset.py `
  --source-pairs-jsonl benchmark_sources/jrc_acquis_anchored_definitions_250_per_language_pair.jsonl `
  --output-dir benchmark_datasets/jrc_acquis_anchored_definitions_250_per_pair `
  --language en `
  --language es `
  --language de `
  --language fr `
  --language pt `
  --limit 250 `
  --extract-legal-terms `
  --legal-terminology-model gpt-4.1-mini `
  --legal-terminology-max-terms 40 `
  --legal-terminology-workers 2 `
  --extract-stanza-terms `
  --stanza-terminology-max-terms 40 `
  --stanza-terminology-workers 2 `
  --use-nobi-extractor `
  --use-spacy-extractor `
  --iate-terminology `
  --wikipedia-terminology `
  --unterm-terminology
```

The article and definition commands differ only in `--source-pairs-jsonl` and `--output-dir`.

## Refiner And Evaluation Groups

The build commands above create candidate/verified terminology manifests. The standard final
benchmark terminology is the refiner-selected `refined` group with `n = 8` terms per segment.

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
