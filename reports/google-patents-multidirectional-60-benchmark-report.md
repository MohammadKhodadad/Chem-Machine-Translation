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
