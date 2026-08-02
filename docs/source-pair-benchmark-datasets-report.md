# Source-Pair Benchmark Datasets

This report summarizes the two portable benchmark datasets created from tracked source-pair JSONL
files: one for Google Patents chemistry text and one for EuroLex legal text.

## Source Files

Google Patents source:

- File: `benchmark_sources/google_patents_within_document_pairs_250_per_language_pair.jsonl`
- Rows: 1,769 source-target pairs.
- Shape: each row has `example_id`, `doc_id`, `language_pair`, `source_language`,
  `target_language`, `source_text`, and `target_text`.
- Language-pair coverage: seven directions have 250 rows each (`en-de`, `en-es`, `en-fr`,
  `en-zh`, `de-fr`, `fr-es`, `zh-fr`). Smaller slices are also present for `de-es` and `zh-de`.
- Terminology: not precomputed in the source-pair file. Chemistry terminology can still be added
  later by rebuilding with the Google terminology flags.

EuroLex source:

- File: `benchmark_sources/eurolex_within_document_pairs_250_per_language_pair.jsonl`
- Rows: 3,000 source-target pairs.
- Shape: aligned with the Google source-pair shape, with additional EuroVoc fields.
- Language-pair coverage: 250 rows for every ordered pair across `en`, `de`, `fr`, and `sk`.
- EuroVoc data: each row keeps `eurovoc_labels`, `eurovoc_descriptors`, and
  `eurovoc_target_terms`.
- Selection: rows are ranked per direction by exact target-language EuroVoc descriptor matches, so
  the benchmark favors terminology-rich legal text.

## Built Datasets

Google Patents benchmark:

- Dataset: `benchmark_datasets/google_patents_source_pairs_10_per_pair`
- Combined manifest:
  `benchmark_datasets/google_patents_source_pairs_10_per_pair/google-patents-9-directions-81-manifest.jsonl`
- Rows: 81.
- Directions: `de-es`, `de-fr`, `en-de`, `en-es`, `en-fr`, `en-zh`, `fr-es`, `zh-de`, `zh-fr`.
- Most directions have 10 rows. `zh-de` has only 1 row because the tracked source file only has
  one available `zh-de` pair.
- Terminology: all 81 rows include generated chemistry terminology. The manifest has 1,143 terms:
  377 `verified`, 671 `llm`, and 95 `algorithmic`.
- Verification sources: PubChem, IATE, Wikipedia/Wikidata, ChEBI, ChEMBL, MeSH RDF,
  NCI Thesaurus, and AGROVOC.

Build command:

```powershell
uv run --no-sync python scripts/build_google_patents_eval_subset.py `
  --source-pairs-jsonl benchmark_sources/google_patents_within_document_pairs_250_per_language_pair.jsonl `
  --output-dir benchmark_datasets/google_patents_source_pairs_10_per_pair `
  --limit 10 `
  --min-input-tokens 1 `
  --max-input-tokens 2048 `
  --extract-terminology `
  --terminology-model gpt-5.4-mini `
  --pubchem-terminology `
  --wikipedia-terminology `
  --iate-terminology `
  --chebi-terminology `
  --chembl-terminology `
  --mesh-terminology `
  --nci-terminology `
  --agrovoc-terminology `
  --terminology-cache data/google_patents_source_pairs_10_expanded_terminology_cache.jsonl `
  --terminology-workers 4
```

EuroLex benchmark:

- Dataset: `benchmark_datasets/eurolex_source_pairs_10_per_pair`
- Combined manifest:
  `benchmark_datasets/eurolex_source_pairs_10_per_pair/eurolex-12-directions-120-manifest.jsonl`
- Rows: 120.
- Directions: all ordered pairs across `en`, `de`, `fr`, and `sk`.
- Terminology: all 120 rows include EuroVoc-derived verified target terminology. The manifest has
  261 target-side EuroVoc terms in total.

Build command:

```powershell
uv run --no-sync python scripts/build_eurolex_eval_subset.py `
  --source-pairs-jsonl benchmark_sources/eurolex_within_document_pairs_250_per_language_pair.jsonl `
  --output-dir benchmark_datasets/eurolex_source_pairs_10_per_pair `
  --limit 10 `
  --min-input-tokens 32 `
  --max-input-tokens 1024
```

## Dataset Format

Both generated benchmark datasets use the same direction-folder architecture:

- One folder per direction, for example `en-de`.
- Each direction folder contains `source.csv`, `target.csv`, and a direction manifest.
- The dataset root contains one combined manifest.
- Manifest rows store `direction`, `source_language`, `target_language`, `source_row_id`,
  `target_row_id`, `text_field`, and optional `terminology`.

This format is consumed by `scripts/evaluate_parallel_manifest.py`.

## Google Patents Pair Quality Issues

The Google source-pair dataset is useful for exercising the benchmark pipeline, but the Spanish
directions need cleanup before they should be treated as reliable benchmark evidence.

Observed issues:

- `de-es` is likely mislabeled or corrupted. It has 10 rows, but 9 rows have source-target
  similarity above `0.99`; the target text is often German rather than Spanish. Example terms
  extracted from this direction include German spans such as `Plasmabeschichtung`,
  `Beschichtungsvorrichtung`, and `Reaktor`.
- `en-de` has one exact duplicate-style row: `within-document:abstract:en-de:AT-519409-A1`.
  The source and target are both English for that row.
- `zh-de` only has one row in the tracked source file, so it is not a meaningful 10-row direction.
- `en-es` target text is valid Spanish, but several source rows are all-caps patent abstracts. This
  interacts badly with formula/regex extraction and can produce noisy candidates such as `LA`,
  `QUE`, `PARA`, and `CON` unless regex filtering is tightened.
- Some rows contain mojibake/replacement characters such as `�`, inherited from the source export.

Recommended cleanup:

- remove or regenerate `de-es`;
- remove exact duplicate-language rows such as the affected `en-de` row;
- either drop `zh-de` from the benchmark or add more valid `zh-de` pairs;
- tighten uppercase regex filtering before using Spanish terminology scores as strong evidence.

## Metrics

General metrics available for both datasets:

- `sequence_similarity`: character/order similarity sanity check.
- `bleu`: SacreBLEU BLEU; corpus summaries use WMT-style corpus scoring.
- `chrf`: SacreBLEU chrF.
- `chrf2++`: WMT-style chrF with word bigrams.
- `comet`: reference-based COMET, loaded only when selected.
- `fsp_mqm`: optional LLM-as-judge metric, not default because it requires API calls.

Terminology metrics:

- `target_term_coverage` works when manifest terminology exists.
- EuroLex supports `target_term_coverage` directly because EuroVoc target terms are stored in the
  manifest.
- Google Patents source-pair manifests include generated chemistry terminology. Default
  `target_term_coverage` uses only `verified` terms, so rows that only have `llm` or `algorithmic`
  terms are not applicable for the default terminology score.
- `terminology_success_rate` is still available explicitly for source-conditioned terminology
  experiments, but it is not the default metric.

Example evaluation command:

```powershell
uv run --no-sync python scripts/evaluate_parallel_manifest.py `
  --dataset-dir benchmark_datasets/eurolex_source_pairs_10_per_pair `
  --strategy dry-run `
  --metric sequence_similarity `
  --metric target_term_coverage `
  --terminology-term-group verified `
  --output reports/eurolex-source-pairs-10-dry-run.jsonl
```

Validation performed:

- Google Patents dry-run evaluation completed for all 81 rows with `sequence_similarity`.
- EuroLex dry-run evaluation completed for all 120 rows with `sequence_similarity` and
  `target_term_coverage`.
- The dry-run outputs are only pipeline checks. They copy/source through the dry-run strategy and
  should not be interpreted as translation quality results.

## Model Benchmark Run

Model run configuration:

- Strategy: `openai`
- Model: `gpt-5.4-mini`
- Google output: `reports/google-patents-source-pairs-10-gpt-5.4-mini-expanded-terminology.jsonl`
- EuroLex output: `reports/eurolex-source-pairs-10-gpt-5.4-mini.jsonl`
- Google metrics: `sequence_similarity`, `bleu`, `chrf2++`, `target_term_coverage`
- EuroLex metrics: `sequence_similarity`, `bleu`, `chrf2++`, `target_term_coverage`

`bleu` and `chrf2++` below are corpus-level summaries. `sequence_similarity` and
`target_term_coverage` are averaged over rows.

Google Patents overall:

- Rows: 81.
- Corpus BLEU: 24.73.
- Corpus chrF2++: 47.23.
- Mean sequence similarity: 29.08.
- Mean verified target-term coverage: 61.90 over the 72 rows with at least one verified term.

Google Patents by direction:

- `de-es`: n=10, BLEU 9.88, chrF2++ 20.43, target-term coverage 50.00 over 4 applicable rows.
- `de-fr`: n=10, BLEU 30.99, chrF2++ 61.21, target-term coverage 73.67 over 10 applicable rows.
- `en-de`: n=10, BLEU 17.20, chrF2++ 48.46, target-term coverage 61.82 over 10 applicable rows.
- `en-es`: n=10, BLEU 2.24, chrF2++ 2.76, target-term coverage 49.93 over 10 applicable rows.
- `en-fr`: n=10, BLEU 10.79, chrF2++ 41.55, target-term coverage 41.33 over 10 applicable rows.
- `en-zh`: n=10, BLEU 3.34, chrF2++ 35.61, target-term coverage 81.06 over 10 applicable rows.
- `fr-es`: n=10, BLEU 58.69, chrF2++ 75.80, target-term coverage 72.41 over 9 applicable rows.
- `zh-de`: n=1, BLEU 0.00, chrF2++ 11.35, target-term coverage not applicable for verified terms.
- `zh-fr`: n=10, BLEU 17.69, chrF2++ 52.35, target-term coverage 58.60 over 9 applicable rows.

EuroLex overall:

- Rows: 120.
- Corpus BLEU: 66.38.
- Corpus chrF2++: 79.74.
- Mean sequence similarity: 64.66.
- Mean verified target-term coverage: 85.41.

EuroLex by direction:

- `de-en`: n=10, BLEU 64.87, chrF2++ 83.90, target-term coverage 100.00.
- `de-fr`: n=10, BLEU 59.55, chrF2++ 76.89, target-term coverage 66.42.
- `de-sk`: n=10, BLEU 53.88, chrF2++ 73.81, target-term coverage 96.67.
- `en-de`: n=10, BLEU 65.00, chrF2++ 79.07, target-term coverage 83.33.
- `en-fr`: n=10, BLEU 59.89, chrF2++ 75.25, target-term coverage 60.58.
- `en-sk`: n=10, BLEU 73.95, chrF2++ 84.46, target-term coverage 90.00.
- `fr-de`: n=10, BLEU 67.36, chrF2++ 85.32, target-term coverage 90.00.
- `fr-en`: n=10, BLEU 64.02, chrF2++ 84.73, target-term coverage 100.00.
- `fr-sk`: n=10, BLEU 58.39, chrF2++ 76.67, target-term coverage 89.17.
- `sk-de`: n=10, BLEU 64.32, chrF2++ 78.29, target-term coverage 85.00.
- `sk-en`: n=10, BLEU 79.19, chrF2++ 89.06, target-term coverage 100.00.
- `sk-fr`: n=10, BLEU 55.91, chrF2++ 73.14, target-term coverage 63.77.

Interpretation:

- EuroLex scores are much higher because the source-target pairs are close legal translations and
  the model preserves many EuroVoc terms.
- Google Patents is harder and more uneven, especially for Chinese and Spanish directions. These
  results should be read as a benchmark smoke run, not as a final model-quality claim.
- Google terminology is now present, but default terminology scoring only uses externally verified
  terms. Adding ChEBI, ChEMBL, MeSH RDF, NCI Thesaurus, and AGROVOC increased applicable Google
  rows from 59 to 72 and made `en-zh` terminology coverage measurable.

## Notes

These datasets are meant to test the benchmark pipeline and metric behavior, not to judge a specific
translation model. The source-pair JSONLs make the benchmark portable because they avoid depending
on ignored raw downloads during normal development.
