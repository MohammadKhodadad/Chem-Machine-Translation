# Legal EuroLex Benchmark Setup

## Summary

We added a EuroLex/MultiEURLEX benchmark path for legal translation experiments. This is separate
from the chemistry terminology pipeline. The goal is to create legal-domain source-target pairs and
attach target-side legal terminology to the manifest before evaluation.

No translation benchmark results have been run yet for this dataset.

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

The main builder is:

```powershell
uv run --no-sync python scripts/build_eurolex_eval_subset.py
```

It can build:

- one source language into selected target languages;
- all ordered pairs among repeated `--language` values;
- term-rich subsets by requiring at least one target-language terminology match.

Generated local datasets so far:

- `data/eurolex_eval_subset_5_lang_250`
  - 5 languages: `en`, `de`, `el`, `fr`, `sk`;
  - 20 ordered directions;
  - 250 rows per direction;
  - 5,000 total pairs.
- `data/eurolex_eval_subset_4_lang_250_term_rich`
  - 4 languages: `en`, `de`, `fr`, `sk`;
  - 12 ordered directions;
  - 250 rows per direction;
  - 3,000 total pairs;
  - every row has at least one target-side EuroVoc descriptor match.
- `data/eurolex_eval_subset_4_lang_10_legal_terms`
  - 4 languages: `en`, `de`, `fr`, `sk`;
  - 12 ordered directions;
  - 10 rows per direction;
  - 120 total pairs;
  - legal LLM terminology extraction enabled.

These datasets are local only because `data/` is ignored by Git.

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

## Small Sample Check

The 10-per-pair legal terminology sample produced:

- 120 rows;
- 120 rows with terms;
- 2,586 total terms;
- 1,027 `verified` terms;
- 1,559 `llm` terms.

Verifier contribution:

- IATE: 749;
- EuroVoc: 278;
- Wikipedia/Wikidata: 4;
- UNTERM: 0 after conservative filtering.

Example legal terms:

- `Vertrag zur Gründung der Europäischen Wirtschaftsgemeinschaft` verified by IATE;
- `Amtsblatt der Europäischen Gemeinschaften` verified by IATE;
- `zolltarifliche und statistische Nomenklatur` verified by IATE;
- `VERORDNUNG (EWG) Nr. 1056/91` kept as an exact LLM term.

## Next Step

Run an actual translation benchmark over a small EuroLex subset and report the metrics separately
from the Google Patents chemistry benchmark.
