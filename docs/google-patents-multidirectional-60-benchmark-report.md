# Google Patents Multidirectional 60 Benchmark Report

## Summary

This report summarizes one benchmark run over the current multidirectional Google Patents benchmark dataset.

- Dataset: `benchmark_datasets/google_patents_eval_subset_60_multidirectional`
- Result file: `reports\google-patents-multidirectional-60-gpt-5.4-mini-all-metrics-verified.jsonl`
- Rows evaluated: 60
- Directions: `en-de`, `de-en`, `en-fr`, `fr-en`, `de-fr`, `fr-de`
- Translation model: `gpt-5.4-mini`
- Strategy: `openai`
- Terminology metric group: `verified` only

## Dataset Construction

The dataset was built from `data/chemistry_patents.ndjson`. The builder selected 10 patent records that contain English, German, and French title/abstract text. For every selected patent, it created all six translation directions among the three languages. Each direction folder contains `source.csv`, `target.csv`, and a direction-specific manifest; the root folder also contains a combined 60-row manifest.

## Terminology Extraction

Terminology is target-side only. The source text is not used for term alignment. The flow is: target/reference text -> target-only LLM candidate spans -> exact span verification -> regex/NER fallback candidates -> PubChem, IATE, and Wikipedia/Wikidata evidence -> manifest terminology rows.

Terminology groups in the combined manifest:

- `algorithmic`: 24
- `llm`: 512
- `verified`: 249

External verification counts:

- `iate`: 245
- `pubchem`: 28
- `wikipedia`: 6

Only `term_group=verified` terms were used for `target_term_coverage` in this benchmark run.

## Metrics

The run selected all implemented metrics: sequence similarity, BLEU, chrF, chrF2++, COMET, source-conditioned terminology success rate, target term coverage, and FSP/MQM. `terminology_success_rate` does not appear in row outputs because this target-only terminology dataset stores empty `source_term` values, so the source-conditioned metric has no applicable terms.

## Estimated Cost And Time

The artifacts do not store exact OpenAI token usage or wall-clock timings, so these are planning
estimates. Here, one benchmark query means one evaluated source-target row. For dataset creation,
the terminology generator is not called once per benchmark row; it is called once per unique
target/reference text plus target language and generation settings, then reused through the
terminology cache. In this 60-row multidirectional dataset, the cache contains 24
terminology-generation calls.

The estimate uses the 60-row output file, 24 cached terminology-generation calls, average source
length of about 110 tokens, average generated translation length of about 186 tokens, and an assumed
mini-model planning price of `$0.40 / 1M input tokens` and `$1.60 / 1M output tokens`. Replace those
prices with the exact account rate for precise accounting.

| Phase | What Ran | Estimated Total Time | Estimated Time / Query | Estimated API Cost | Estimated Cost / Query |
|---|---|---:|---:|---:|---:|
| Dataset creation | Local dataset selection plus 24 cached target-only terminology generations, external lookups, and manifest writing | 8-12 min | 8-12 sec amortized over 60 rows; ~20-30 sec per unique target call | ~$0.03 | ~$0.0005 amortized over 60 rows; ~$0.0013 per unique target call |
| Benchmark run | 60 translations, local/reference metrics, COMET scoring, and 60 FSP/MQM judge calls | 15-25 min | 15-25 sec | ~$0.09 | ~$0.0015 |

The dataset creation cost is low because the same target reference can be reused in multiple
directions. For example, a German reference can serve both `en-de` and `fr-de`, so its target-side
terminology only needs to be generated once. External PubChem, IATE, and Wikipedia/Wikidata lookups
do not add LLM cost, but they can add latency. The benchmark run is more expensive because each row
uses one translation call and one FSP/MQM judge call; COMET is local model inference and has runtime
cost but no API cost.

## Results By Direction

| Direction | n | BLEU | chrF | chrF2++ | Seq. Sim. | COMET | Target Term Coverage | FSP/MQM | MQM Error |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| `de-en` | 10 | 63.21 | 77.39 | 76.20 | 59.69 | 0.83 | 75.42 | 90.50 | 3.30 |
| `de-fr` | 10 | 49.89 | 69.37 | 67.36 | 56.26 | 0.81 | 88.73 | 86.20 | 4.40 |
| `en-de` | 10 | 50.61 | 76.15 | 72.97 | 57.08 | 0.85 | 73.98 | 91.65 | 3.60 |
| `en-fr` | 10 | 52.92 | 72.97 | 70.76 | 49.24 | 0.83 | 76.05 | 87.30 | 3.80 |
| `fr-de` | 10 | 48.36 | 74.72 | 71.66 | 59.18 | 0.82 | 85.74 | 88.60 | 3.10 |
| `fr-en` | 10 | 62.59 | 78.52 | 77.08 | 65.54 | 0.83 | 73.17 | 89.70 | 3.00 |

## Overall Results

- Corpus BLEU: 55.48
- Corpus chrF: 74.74
- Corpus chrF2++: 72.60
- Average sequence similarity: 57.83
- Average COMET: 0.83
- Average target term coverage, verified terms only: 78.85
- Average FSP/MQM quality score: 88.99
- Average MQM error score: 3.53

## Notes And Caveats

- The benchmark focuses on dataset and metric behavior, not on proving this model is the best translation model.
- `verified` terms are the main terminology benchmark set because they have external evidence.
- Some external matches can still be noisy, especially broad IATE matches, so spot checks remain useful.
- Target-only terminology avoids source-target alignment complexity, but source-conditioned terminology metrics are not applicable unless source terms are added later.
