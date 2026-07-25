# Google Patents 20-Query Benchmark Report

This is a short report for the 20-query Google Patents benchmark and its evaluation artifacts. The
goal is to inspect whether the benchmark terminology and metrics are useful, not to judge the
translation model used to generate test outputs.

## Metrics

The run used all implemented metrics:

- `sequence_similarity`: character/order similarity against the reference.
- `bleu`: SacreBLEU lexical n-gram overlap.
- `chrf`: SacreBLEU character F-score.
- `chrf2++`: WMT-style chrF with character n-grams and word bigrams.
- `comet`: reference-based COMET semantic MT quality score.
- `terminology_success_rate`: WMT-inspired count-based check against manifest terminology.
- `fsp_mqm`: optional LLM-as-judge MQM-style quality score, with severity-weighted error counts.

For BLEU, chrF, and chrF2++, the benchmark summary uses corpus-level SacreBLEU scoring.

## Dataset

Dataset: `examples/google_patents_eval_subset_20`

This subset contains aligned Google Patents-style patent contexts for English to French evaluation.
Each query is a patent title plus abstract-like context with a human French reference translation.

- Number of evaluated queries: `20`
- Source language: English
- Target language: French
- Text field: `context`
- Report file: `reports/google-patents-20-gpt41-nano-all-metrics.jsonl`
- Manifest file: `examples/google_patents_eval_subset_20/google-patents-subset-20-manifest.jsonl`

## Sample

Source ID: `EP-4633361-A1`

Source title:

```text
Quantitative trait loci associated with shoot architecture in cannabis
```

Reference title:

```text
Loci de traits quantitatifs associés à une architecture de pousse dans le cannabis
```

Example test output title:

```text
QTLs associés à l'architecture de la tige chez le cannabis
```

This sample shows what the benchmark is meant to catch: the generated output can be compared against
the reference terminology for `Quantitative trait loci`, regardless of whether the model itself is
the focus of the experiment.

## Terminology Generation Flow

The dataset terminology is generated before translation/evaluation:

1. A target-only LLM proposes strict technical spans from the human reference.
2. The code verifies that each proposed span appears in the target/reference text.
3. Regex/NER fallback captures compact formulas, identifiers, numeric units, and common chemistry
   terms.
4. PubChem, IATE, and Wikipedia/Wikidata provide external lookup evidence where available.
5. Final target-side terms are stored in the manifest row and consumed by `target_term_coverage`.

In this benchmark, the terminology manifest is the important artifact. The generated translation is
only used as input for the metrics.

## Terminology Examples

The 20-query manifest contains `214` accepted terminology entries, about `10.7` per row.

Decision counts:

- `keep_reference`: `172`
- `keep_both`: `26`
- `preserve`: `13`
- `update`: `3`

Examples:

- `Cannabis spp.` -> `Cannabis spp.` (`preserve`)
- `QTL` -> `QTL` (`preserve`)
- `marker assisted selection` -> `sélection assistée par marqueur`, `sélection assistée par marqueurs`
- `linoleic acid residues` -> `résidus d'acide linoléique`
- `C18:0` -> `C18:0`
- `phosphate-binder(s)` -> `chélateurs du phosphate`
- `grape juice` -> `jus de raisin`
- `alcohol-free wine` -> `vin sans alcool`, `vin désalcoolisé`

## Issues Seen In The Data

The lowest terminology scores were:

- `EP-4633580-A1`: `33.33`
- `EP-4633612-A1`: `36.36`
- `EP-4633577-A1`: `45.45`
- `EP-4633426-A2`: `50.00`
- `EP-4633576-A1`: `50.00`

Benchmark issues observed:

- Exact terminology scoring may miss acceptable variants. For example, singular/plural or wording
  differences can reduce `terminology_success_rate` even when the benchmark should arguably count the
  term as satisfied. This means the benchmark can under-score a system for using a valid variant that
  is not listed in `target_terms`. Examples include spacing or morphology differences such as
  `C18:0` vs `C18 : 0`, or near-equivalent French formulations for technical noun phrases.
- Some expected French terms are very reference-specific, such as `composition de cuir chevelu
  claire` for `clear scalp composition`. This means the terminology manifest may sometimes learn the
  exact wording of one reference instead of a reusable terminology mapping. It is useful for matching
  that reference, but weaker as a general benchmark term because another correct French translation
  might choose a different phrase.
- Drug or chemical names can have multiple valid written forms while the benchmark currently stores a
  narrow target form, for example `Netupitant` vs `nétupitant`. This matters because chemical and
  drug names often differ by accents, capitalization, Greek letters, hyphens, or typography. The
  benchmark should either store these variants explicitly or normalize them before scoring.
- A few extracted terms are still broad or not chemistry-specific enough, such as `drive unit`,
  `connection device`, or `specific markers`. These are not necessarily wrong, but they are weaker
  benchmark terms because they measure broad patent wording rather than chemistry terminology. If too
  many broad terms are included, the terminology metric becomes less focused on the chemistry signal.
- Some patent/mechanical terms appear in the Google Patents sample, so the benchmark is not purely
  chemical even though many rows are chemistry-heavy. For example, `EP-4633426-A2` is about an
  assembly, a container, and a drive unit. This is still useful for patent translation, but it means
  the subset should be labeled as mixed patent-domain text rather than a pure chemistry benchmark.

## Test Run Results

Command summary:

```powershell
uv run --no-sync python scripts/evaluate_google_patents.py `
  --data-dir examples/google_patents_eval_subset_20 `
  --output reports/google-patents-20-gpt41-nano-all-metrics.jsonl `
  --language fr `
  --limit 20 `
  --strategy openai `
  --model gpt-4.1-nano `
  --min-input-tokens 128 `
  --max-input-tokens 384 `
  --metric sequence_similarity `
  --metric bleu `
  --metric chrf `
  --metric chrf2++ `
  --metric comet `
  --metric terminology_success_rate `
  --metric fsp_mqm `
  --fsp-mqm-model gpt-4.1-mini `
  --fsp-mqm-timeout 180 `
  --comet-batch-size 4
```

Overall French results for `20` queries:

- BLEU: `57.29`
- chrF: `79.29`
- chrF2++: `77.03`
- COMET: `0.86`
- FSP/MQM quality: `92.80`
- FSP/MQM error score: `3.50`
- FSP/MQM minor errors: `2.80`
- FSP/MQM major errors: `0.35`
- FSP/MQM critical errors: `0.00`
- Sequence similarity: `44.92`
- Terminology success rate: `61.11`

Interpretation: the run successfully exercises the benchmark across overlap metrics, semantic
metrics, terminology metrics, and MQM-style judging. The key benchmark signal is that terminology
success is much lower than COMET/MQM, which suggests the terminology benchmark is measuring a
separate and stricter property than general translation quality.

## Benchmark Analysis And Things To Improve

The main benchmark gap is terminology quality. If the benchmark terminology is noisy, too narrow, or
too broad, then `terminology_success_rate` will be difficult to interpret. The priority should be to
improve the manifest terminology itself before using the benchmark for model comparison.

Terminology generation should also improve. Some terms are still too broad, some target forms are too
reference-specific, and some valid variants are penalized by exact matching. The refiner should be
stricter about generic patent phrases and better at keeping multiple acceptable French variants.

External terminology sources should be expanded. IATE helped on some European technical terms, but it
is not enough for chemistry-heavy patents. Useful additions would include PubChem, ChEBI, MeSH,
Wikidata, CAS-like identifier handling where available, and domain glossaries from patent or
regulatory sources. These should be used as validation and candidate providers, not blindly trusted.

The terminology metric should also become more forgiving without becoming loose. It should recognize
accent/spacing variants, singular/plural variants, hyphenation differences, and equivalent chemical
notation such as `C18:0` vs `C18 : 0`. This would make the score closer to real terminology quality
instead of only exact string reuse.

The benchmark should also expose more audit fields. For each row, it would be useful to report the
number of applicable terms, matched terms, missing terms, and skipped terms. This would make it much
easier to debug whether a low terminology score comes from bad output, bad target variants, or a weak
manifest term.

Finally, the benchmark should be expanded beyond 20 French rows. The next useful benchmark-building
step is to generate larger terminology-bearing subsets across more target languages, then manually
audit a small sample of terms per language before trusting the metric at scale.
