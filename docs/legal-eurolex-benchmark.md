# Legal EuroLex Benchmark Setup

## Summary

We added a EuroLex/MultiEURLEX benchmark path for legal translation experiments. This is separate
from the chemistry terminology pipeline. The goal is to create legal-domain source-target pairs and
attach target-side legal terminology to the manifest before evaluation.

The current portable benchmark dataset is
`benchmark_datasets/eurolex_source_pairs_10_per_pair`, with 120 rows across 12 ordered directions.
It is built with legal terminology enabled by default.

For the next legal benchmark iteration, use `scripts/create_jrc_acquis_source_pairs.py` first. It
builds larger source-pair chunks from OPUS JRC-Acquis aligned segments and supports `en`, `es`,
`de`, `fr`, and `pt`. Then use `scripts/build_jrc_acquis_eval_subset.py` to turn that source
snapshot into a benchmark dataset with terminology.

## Data Source

The data comes from the public MultiEURLEX archive:

- downloaded with `scripts/download_eurolex_data.py`;
- stored locally under the ignored `data/multi_eurlex` folder;
- extracted into `train.jsonl`, `dev.jsonl`, and `test.jsonl`;
- paired with `eurovoc_descriptors.json` from the upstream MultiEURLEX repository.

The downloaded archive contains English originals plus translated text streams such as `en2de`,
`en2fr`, `en2sk`, and `en2el`. The builder maps these into normal language codes like `de`, `fr`,
`sk`, and `el`.

## Dataset Builder

EuroLex follows the same two-step source-first architecture as Google Patents and JRC-Acquis:

1. `scripts/create_eurolex_source_snapshot.py` downloads/selects raw MultiEURLEX rows into a tracked
   source snapshot.
2. `scripts/create_eurolex_source_pairs.py` converts that snapshot into source-target pair JSONL.
3. `scripts/build_eurolex_eval_subset.py` consumes only the source-pair JSONL and writes
   `source.csv`, `target.csv`, and manifest files with terminology.

The current portable EuroLex benchmark is rebuilt with:

```powershell
uv run --no-sync python scripts/build_eurolex_eval_subset.py `
  --source-pairs-jsonl benchmark_sources/eurolex_within_document_pairs_250_per_language_pair.jsonl `
  --output-dir benchmark_datasets/eurolex_source_pairs_10_per_pair `
  --language en `
  --language de `
  --language fr `
  --language sk `
  --limit 10 `
  --extract-legal-terms `
  --iate-terminology `
  --wikipedia-terminology `
  --unterm-terminology
```

The newer JRC-Acquis source builder is:

```powershell
uv run --no-sync python scripts/create_jrc_acquis_source_pairs.py
```

It downloads public OPUS JRC-Acquis Moses zips into `data/opus_jrc_acquis`, reads already-aligned
source-target segments, and concatenates them into larger document-bounded chunks. The resulting
source-pair JSONL is stored under `benchmark_sources/` and can be reviewed before creating a
benchmark dataset. This avoids scraping EUR-Lex and avoids the EuroVoc-only limitation.

The matching benchmark dataset builder is:

```powershell
uv run --no-sync python scripts/build_jrc_acquis_eval_subset.py `
  --source-pairs-jsonl benchmark_sources/jrc_acquis_chunks_5_per_language_pair.jsonl
```

Generated source-first artifacts so far:

- `benchmark_sources/eurolex_4000.jsonl`
  - tracked raw-row source snapshot selected from MultiEURLEX;
  - includes `en`, `de`, `fr`, and `sk` text where available.
- `benchmark_sources/eurolex_within_document_pairs_250_per_language_pair.jsonl`
  - source-target pair snapshot built from the raw-row source;
  - 12 ordered directions;
  - 250 rows per direction;
  - 3,000 total source-target pairs.
- `benchmark_datasets/eurolex_source_pairs_10_per_pair`
  - tracked portable benchmark dataset built from
    `benchmark_sources/eurolex_within_document_pairs_250_per_language_pair.jsonl`;
  - 12 ordered directions;
  - 10 rows per direction;
  - 120 total pairs;
  - legal LLM terminology extraction and external verification enabled.
- `benchmark_sources/jrc_acquis_chunks_5_per_language_pair.jsonl`
  - review source snapshot built from OPUS JRC-Acquis aligned segments;
  - 5 languages: `en`, `es`, `de`, `fr`, `pt`;
  - 20 ordered directions;
  - 5 chunks per direction;
  - 100 total source-target chunks.

The large upstream downloads remain local only because `data/` is ignored by Git. The small source
snapshots in `benchmark_sources/` are tracked so benchmark datasets can be recreated without
redownloading raw archives.

## Legal Terminology Flow

EuroLex legal terminology uses only two groups:

- `llm`: exact target-text spans proposed by the legal LLM candidate extractor.
- `verified`: exact target-text spans with evidence from IATE, EuroVoc, Wikipedia/Wikidata, or
  conservative UNTERM lookup.

The flow is:

```text
target/reference legal text
-> legal LLM candidate spans
-> exact span check in the target text
-> external verification
-> manifest terminology
```

External sources do not introduce replacement terms. They only verify terms already found in the
target/reference text.

## Verification Sources

- **IATE**: main legal/EU terminology verifier.
- **EuroVoc**: metadata descriptor verifier. Useful, but often broad.
- **Wikipedia/Wikidata**: lightweight verifier for entities and common legal concepts.
- **UNTERM**: best-effort only. UNTERM has no documented public API, so the code fails closed unless
  the public search page reports a positive result range.

## Current Sample Check

The 10-per-pair legal terminology sample produced:

- 120 rows;
- 120 rows with terms;
- 2,571 total terms;
- 963 `verified` terms;
- 1,608 `llm` terms.

Verifier contribution:

- IATE: 702;
- EuroVoc: 261;
- Wikipedia/Wikidata: 6;
- UNTERM: 0 after conservative filtering.

Example legal terms:

- `Vertrag zur Gründung der Europäischen Wirtschaftsgemeinschaft` verified by IATE;
- `Amtsblatt der Europäischen Gemeinschaften` verified by IATE;
- `zolltarifliche und statistische Nomenklatur` verified by IATE;
- `VERORDNUNG (EWG) Nr. 1056/91` kept as an exact LLM term.

The current `gpt-5.4-mini` benchmark metrics for this dataset are reported in
`docs/source-pair-benchmark-datasets-report.md`.
