# Evaluation Metrics

This project computes automatic reference-based metrics for source-pair benchmark datasets using
`scripts/evaluate_parallel_manifest.py`. By default, benchmark evaluation can compute
`sequence_similarity`, BLEU, chrF2++, COMET, and `target_term_coverage`. Use repeated `--metric`
flags to override the default set.

The implementation lives in `src/chem_machine_translation/evaluation/metrics.py`:

```python
def compute_translation_metrics(
    prediction: str,
    reference: str,
    source: str | None = None,
    metric_names: list[str] | tuple[str, ...] | None = None,
    comet_scorer: CometScorer | None = None,
    terminology: list[dict[str, Any]] | None = None,
    mqm_judge: MqmJudge | None = None,
) -> dict[str, float]:
    ...
```

Each benchmark row stores these values under the `metrics` field in the JSONL report. The evaluation
scripts also print target-language summaries. For BLEU, chrF, and chrF2++, the printed summaries use
SacreBLEU corpus scoring, which is closer to WMT reporting than averaging sentence scores. Other
metrics are averaged over evaluated rows.

## Metric Groups

We separate metrics into two groups:

- **General metrics**: language-agnostic reference-overlap metrics. These are useful for comparing
  systems on the same benchmark, but they do not understand chemistry.
- **Domain-specific metrics**: chemistry- or patent-aware checks. These are intended to measure
  things like formula preservation, terminology consistency, and chemical identity.

At the moment, the codebase implements `sequence_similarity`, BLEU, chrF, chrF2++,
reference-based COMET, target-side `target_term_coverage`, source-conditioned
`terminology_success_rate`, and optional `fsp_mqm` LLM judging. The benchmark builders can generate
terminology mappings in manifest rows. Terminology consistency is not wired into
`compute_translation_metrics` yet.

Terminology metrics can filter manifest terms by `term_group`. The supported groups are `verified`,
`llm`, and `algorithmic`. The default for target terminology evaluation is `verified`, meaning terms
with PubChem, IATE, or Wikipedia/Wikidata evidence.

## Current Status

Implemented in code:

- `sequence_similarity`: simple string-level similarity, useful as a sanity check.
- `bleu`: SacreBLEU BLEU. Row reports use sentence BLEU; printed summaries use corpus BLEU.
- `chrf`: SacreBLEU chrF. Row reports use sentence chrF; printed summaries use corpus chrF.
- `chrf2++`: WMT-style chrF with word bigrams. Row reports use sentence chrF2++; printed summaries
  use corpus chrF2++.
- `comet`: reference-based COMET with `Unbabel/wmt22-comet-da`, useful for semantic MT quality.
- `target_term_coverage`: manifest-based target terminology coverage. It is included in defaults,
  but only produces a row score when manifest terminology exists for that row.
- `terminology_success_rate`: source-conditioned WMT-style terminology accuracy. It is still
  available explicitly, but is not in defaults.
- `fsp_mqm`: optional LLM-as-judge MQM-style metric. It is implemented, but not included in defaults
  because it requires extra API calls.

Reviewed from the WMT25 Terminology Shared Task repository:

- `chrf2++`: WMT25 uses chrF with character n-grams and word n-grams for general MT quality.
- `term_success_rate` / `Acc`: WMT25's main terminology accuracy metric.
- `term_consistency` / `Cons.`: WMT25's terminology consistency metric.
- `FSP`: an LLM-as-judge MQM-style document evaluation metric.

Recommended next implementation for this project:

- add simplified terminology consistency across rows/documents;
- improve FSP/MQM calibration and reporting after collecting enough judged examples.

The practical interpretation is: general metrics tell us whether the translation resembles the
reference and preserves meaning broadly; domain-specific metrics tell us whether chemistry-critical
terms, symbols, units, and identifiers survived correctly.

Current terminology data status:

- Source-pair dataset builders can generate terminology-bearing manifests from tracked
  `benchmark_sources/*.jsonl` files.
- Each manifest term can include `source_term`, final accepted `target_terms`,
  `reference_candidates`, `external_candidates`, `term_group`, `verified_by`, `category`,
  `confidence`, `decision`, and `reason`.
- The latest terminology flow is documented in `docs/terminology-extraction.md`.
- `target_term_coverage` and `terminology_success_rate` consume these manifest terms instead of
  extracting terminology during evaluation.

## General Metrics

### Sequence Similarity

Status: **implemented** as `sequence_similarity` in `compute_translation_metrics`.

`sequence_similarity` is computed with Python's `difflib.SequenceMatcher`.

It compares the predicted translation string against the reference translation string and returns a
similarity ratio between `0` and `100`.

Intuition:

- `100` means the strings are identical.
- `0` means the matcher found almost no shared sequence structure.
- Higher values mean the two strings have more similar character/order patterns.

How it works:

`SequenceMatcher` looks for matching subsequences between two strings. It rewards long shared spans
and similar ordering. In this project the raw ratio is multiplied by `100` so it appears on the same
rough scale as BLEU and chrF.

Formula:

```text
sequence_similarity = 100 * (2 * M) / T
```

where:

- `M` is the total number of matched characters across the matching blocks found by
  `SequenceMatcher`;
- `T` is the total number of characters in both strings:

```text
T = len(prediction) + len(reference)
```

So if the prediction and reference are identical, every character is matched:

```text
M = len(prediction) = len(reference)
sequence_similarity = 100
```

If the strings share little ordered character overlap, `M` is small and the score approaches `0`.

Useful for:

- catching very rough regressions;
- checking whether output is close to a known reference;
- quick dry-run sanity checks.

Limitations:

- it is not a translation metric;
- it is sensitive to word order and formatting;
- valid paraphrases can score poorly;
- copied source text can sometimes receive non-trivial scores if technical terms, formulas, and
  punctuation overlap.

### BLEU

Status: **implemented** as `bleu` in `compute_translation_metrics`.

`bleu` is computed with `sacrebleu.metrics.BLEU`. Row-level JSON reports use sentence scoring:

```python
BLEU(effective_order=True).sentence_score(prediction, [reference]).score
```

Language-level benchmark summaries use corpus scoring, which is the WMT-style way to report BLEU:

```python
BLEU(max_ngram_order=4, tokenize="13a").corpus_score(predictions, [references]).score
```

BLEU measures n-gram overlap between the prediction and the reference. An n-gram is a contiguous
sequence of tokens. For example, in `solid electrolyte battery`, the 1-grams are `solid`,
`electrolyte`, and `battery`; the 2-grams include `solid electrolyte` and `electrolyte battery`.

Formula:

```text
BLEU = BP * exp(sum_n(w_n * log(p_n)))
```

where:

- `p_n` is the modified precision for n-grams of size `n`;
- `w_n` is the weight for each n-gram order, usually equal weights;
- `BP` is the brevity penalty, which penalizes translations that are too short.

Modified n-gram precision is computed with clipped counts:

```text
p_n = sum_g min(count_prediction(g), count_reference(g)) / sum_g count_prediction(g)
```

where `g` ranges over all prediction n-grams of size `n`.

The clipping matters. If the prediction repeats a word many times, BLEU does not give unlimited
credit unless the reference also contains that word many times.

The brevity penalty is:

```text
BP = 1                         if c > r
BP = exp(1 - r / c)            if c <= r
```

where:

- `c` is the prediction length;
- `r` is the reference length.

The row-level code uses `BLEU(effective_order=True)`, so SacreBLEU adapts the effective maximum
n-gram order for sentence-level scoring when the text is too short to support all normal n-gram
orders. The printed language summary recomputes BLEU over the full list of predictions and
references using corpus-level SacreBLEU.

Intuition:

- high BLEU means the prediction uses many of the same token sequences as the reference;
- low BLEU means the prediction uses different wording or has missing/extra content;
- `effective_order=True` makes sentence-level BLEU less brittle on short texts by adapting the
  maximum n-gram order to the available sentence length.

Useful for:

- comparing systems on the same fixed benchmark;
- detecting large omissions or substantially different wording;
- producing a familiar machine translation baseline metric.

Limitations:

- BLEU rewards lexical overlap, not necessarily semantic correctness;
- a chemically correct translation can score lower if it uses a valid synonym;
- a chemically wrong translation can score higher if it shares many reference words;
- row-level sentence BLEU is noisier than corpus BLEU, especially on small samples. Use the printed
  summary for WMT-style reporting.

### chrF

Status: **implemented** as `chrf` in `compute_translation_metrics`, but not included in the default
metric set. Use it explicitly when backwards comparison with plain chrF is needed.

`chrf` is computed with `sacrebleu.metrics.CHRF`. Row-level JSON reports use sentence scoring:

```python
CHRF().sentence_score(prediction, [reference]).score
```

Language-level benchmark summaries use corpus scoring:

```python
CHRF().corpus_score(predictions, [references]).score
```

chrF compares character n-gram overlap between the prediction and the reference. Instead of only
looking at word tokens, it checks overlapping character sequences.

Formula:

```text
chrF_beta = (1 + beta^2) * (P_char * R_char) / (beta^2 * P_char + R_char)
```

where:

- `P_char` is average character n-gram precision;
- `R_char` is average character n-gram recall;
- `beta` controls the precision/recall balance.

SacreBLEU's default `CHRF()` uses character n-grams up to order `6` and `beta = 2`, which gives
recall more weight than precision.

For each character n-gram order `n`, precision and recall are:

```text
P_n = matched_character_ngrams_n / prediction_character_ngrams_n
R_n = matched_character_ngrams_n / reference_character_ngrams_n
```

Then the metric averages across character n-gram orders:

```text
P_char = average(P_1, P_2, ..., P_6)
R_char = average(R_1, R_2, ..., R_6)
```

Finally SacreBLEU reports the score on a `0` to `100` scale.

Intuition:

- high chrF means the prediction and reference share many character-level patterns;
- it is often more forgiving than BLEU when morphology or tokenization differs;
- it can capture partial matches such as related inflections or compound-word overlap.

Useful for:

- German, French, and other languages where inflection or compounds can affect token-level metrics;
- technical terms where partial string overlap matters;
- complementing BLEU with a more character-sensitive score.

Limitations:

- chrF is still based on surface overlap;
- it does not know chemistry;
- it can reward strings that look similar but mean different things;
- row-level sentence chrF is noisier than corpus chrF. Use the printed language summary for
  WMT-style reporting;
- it does not validate formulas, identifiers, stereochemistry, units, or reaction roles.

### chrF2++ / WMT-Style chrF

Status: **implemented** as `chrf2++`.

The WMT25 Terminology Shared Task uses chrF2++ for general MT quality. In code, their setting is:

```python
CHRF(char_order=6, word_order=2)
```

This differs from plain `CHRF()` because chrF2++ includes word n-gram overlap in addition to
character n-gram overlap.

Row-level JSON reports use `sentence_score`. Benchmark summaries use `corpus_score`, matching the
way WMT reports corpus-level system quality.

Project default:

```text
--metric chrf2++
```

Plain `chrf` is still available as an explicit metric for backwards comparison, but `chrf2++` is the
preferred default.

Formula:

```text
chrF++ = F_beta(P_char+word, R_char+word)
```

where precision and recall are averaged over:

- character n-grams up to order `6`;
- word n-grams up to order `2`.

Why it is good:

- WMT25 chose chrF because it works for both sentence-level and document-level translation;
- it is more robust than BLEU for morphology and compounds;
- adding word n-grams gives a little more phrase-level signal than plain chrF.

Why it is the preferred default:

- it makes our evaluation closer to WMT terminology evaluation practice;
- it is cheap to compute;
- it is a better default lexical metric than BLEU alone for German/French patent text.

### COMET

Status: **implemented** as `comet` in `compute_translation_metrics` and included in the default
metric set. It requires source text and lazy-loads the COMET model.

COMET is a learned neural machine translation metric. Unlike BLEU and chrF, it does not only compare
surface overlap. It uses a trained model to estimate translation quality from the source text,
machine translation, and optionally a human reference.

COMET is implemented through Unbabel's official Python package:

```text
unbabel-comet
```

Reference-based COMET uses source, machine translation, and reference:

```python
from comet import download_model, load_from_checkpoint

model_path = download_model("Unbabel/wmt22-comet-da")
model = load_from_checkpoint(model_path)

data = [
    {
        "src": source_text,
        "mt": predicted_translation,
        "ref": ground_truth_translation,
    }
]

result = model.predict(data, batch_size=8, gpus=0)
```

Reference-free COMETKiwi uses source and machine translation only:

```python
model_path = download_model("Unbabel/wmt22-cometkiwi-da")
```

The current code path uses reference-based COMET by default:

```text
--comet-model Unbabel/wmt22-comet-da
```

To skip COMET for a faster run, explicitly select only the cheaper metrics:

```powershell
uv run --no-sync python scripts/evaluate_parallel_manifest.py `
  --dataset-dir benchmark_datasets/jrc_acquis_articles_250_per_pair `
  --metric sequence_similarity `
  --metric bleu `
  --metric chrf2++
```

Formula:

COMET is model-based rather than a closed-form overlap metric. Conceptually, a trained model
`f_theta` maps the source, machine translation, and optional reference to a quality score:

```text
COMET_ref = f_theta(source, prediction, reference)
COMET_ref_free = f_theta(source, prediction)
```

For a benchmark with `N` evaluated rows, the system score is the arithmetic mean:

```text
COMET_system = (1 / N) * sum_i COMET_i
```

where `COMET_i` is the segment-level score for row `i`.

Useful for:

- estimating semantic adequacy beyond lexical overlap;
- comparing models when valid translations may use different wording from the reference;
- evaluating cases where BLEU or chrF penalize acceptable paraphrases.

Limitations:

- scores depend on the exact checkpoint, such as `Unbabel/wmt22-comet-da`;
- scores from different checkpoints are not directly comparable;
- runtime and dependencies are heavier than BLEU/chrF;
- COMET is not chemistry-specific and still may miss formula, structure, or terminology errors.

For reproducible experiments, record:

- COMET package version;
- exact checkpoint name;
- whether the metric is reference-based or reference-free;
- hardware setting, especially CPU vs GPU;
- batch size.

Why it is good:

- COMET gives a semantic adequacy signal that BLEU and chrF cannot provide;
- it is useful when a translation is valid but uses different wording from the reference;
- it is now implemented and end-to-end tested in this codebase.

Project status:

- implemented with `unbabel-comet`;
- default model is `Unbabel/wmt22-comet-da`;
- tested under Python `3.12`;
- project Python is constrained to `<3.13` because the COMET dependency stack is not currently
  reliable on Python `3.13` on Windows.

## Report-Level Aggregation

The benchmark scripts store metrics per row for inspection. Printed summaries are grouped by target
language.

For example, `scripts/evaluate_parallel_manifest.py` writes rows like:

```json
{
  "target_language": "German",
  "predicted_translation": "...",
  "ground_truth_translation": "...",
  "metrics": {
    "sequence_similarity": 46.7,
    "bleu": 46.01,
    "chrf2++": 72.24,
    "comet": 0.81
  }
}
```

Then the script prints language-level summaries:

```text
German: n=50, bleu=46.01, chrf2++=72.24, comet=0.81, sequence_similarity=46.70
```

For BLEU, chrF, and chrF2++, the printed summary recomputes the metric over the full language-level
corpus with SacreBLEU `corpus_score`, which is closer to WMT reporting. Sequence similarity, COMET,
target term coverage, terminology success rate, and FSP/MQM fields are averaged over the evaluated
rows.

## Domain-Specific Metrics

Some domain-specific metrics are now implemented in `compute_translation_metrics`, and the dataset
builders create the manifest terminology data needed by those metrics. These metrics should evaluate
chemical and patent translation behavior more directly.

Planned domain-specific metrics include:

- **Formula/entity preservation rate**: **not implemented**. This should check whether formulas,
  units, sequence IDs, and identifiers from the source are preserved in the translation.
- **Target terminology coverage**: **implemented** as `target_term_coverage`. It consumes manifest
  `terminology` rows and is included in defaults.
- **Source-conditioned terminology accuracy / terminology success rate**: **implemented** as
  `terminology_success_rate`. It consumes manifest `terminology` rows and can be selected
  explicitly.
- **Terminology consistency**: **not implemented**. This should check consistency across repeated
  manifest terms.
- **Chemical name/structure validation**: **not implemented**. This should compare parsed or
  canonicalized chemical identities where possible.
- **Unit and numerical value preservation**: **not implemented**. This should check quantities,
  units, temperatures, pressures, concentrations, and ranges.
- **Sequence ID and identifier preservation**: **not implemented**. This should check sequence IDs,
  CAS-like identifiers, patent identifiers, and compact symbols.
- **Chemistry-aware human/MQM review categories**: **partially implemented** as optional
  `fsp_mqm`. It provides LLM-judge quality/error scores, not a fully calibrated human review system.

These metrics should complement the general metrics, not replace them. BLEU, chrF2++, COMET, and
sequence similarity tell us how close the output is to the reference wording or meaning;
domain-specific metrics tell us whether chemically important information survived the translation.

### Target Term Coverage

Status: **implemented** as `target_term_coverage` in `compute_translation_metrics` and included in
the default metric set.

Target term coverage measures whether approved target-language terminology from the benchmark
reference appears in the generated translation. It does not require source terms, so it fits
reference-first or target-only benchmark terminology.

This is the project-specific modification to the terminology metric. WMT-style
`terminology_success_rate` is source-conditioned: first the source term must appear in the source
text, then the metric checks whether the approved target term appears in the output. Our default
`target_term_coverage` removes the source-side condition and only evaluates target-language terms
that are present in the human reference. In practice, this makes the metric usable when terminology
was extracted from the target reference or from target-language databases, and when the benchmark
does not have reliable source-term extraction.

For each manifest term `t`, the metric uses the accepted `target_terms`. Terms marked with
`decision = "drop"` are ignored. If none of the accepted target terms appear in the reference, the
term is skipped for that row.

For an applicable term:

```text
reference_count_t = sum_j count_normalized(reference, target_term_tj)
prediction_count_t = sum_j count_normalized(prediction, target_term_tj)

coverage_t = min(prediction_count_t / reference_count_t, 1)
```

Row-level target term coverage is:

```text
target_term_coverage_row = 100 * (1 / |T_row|) * sum_t coverage_t
```

This answers a simpler benchmark question than source-conditioned terminology accuracy:

```text
Of the important target-reference terms, how many did the generated translation reproduce?
```

It is useful when benchmark terminology is extracted from target references or external
target-language resources and we do not want the metric to depend on source-term extraction.

Operationally, the target-only version works like this:

1. Filter manifest terminology by `term_group`; by default only `verified` terms are evaluated.
2. Ignore dropped terms and terms without accepted `target_terms`.
3. Keep only terms whose accepted target form appears in the reference text.
4. Count normalized matches of those target forms in the prediction.
5. Cap each term's contribution at `1.0`, so repeated hallucinated terms cannot receive extra credit.

This is stricter than a pure "does any glossary term appear" check because reference absence makes a
term non-applicable for that row. It is also simpler than WMT Track 1 because it does not use
lemmatization or source-term matching.

## WMT25 Terminology Metrics Review

The WMT25 terminology repository evaluates systems with three main ranking signals:

- **General MT quality**: chrF, specifically chrF2++.
- **Terminology success rate**: reported as `Acc`.
- **Term consistency**: reported as `Cons.`.

The repository also includes an additional FSP metric for LLM-as-judge MQM-style document-level
evaluation.

For our project, the most useful part is terminology success rate. It directly answers the question:
when the source contains an approved term, did the translation contain an approved target term?

The WMT25 term consistency and FSP implementations are useful references, but they are heavier than
we need for a first chemistry benchmark.

### Terminology Accuracy

Terminology accuracy measures whether approved target-language terms appear in the translation when
their source-language terms appear in the source text.

This is a domain-specific metric because it evaluates controlled chemistry or patent terminology,
not general translation fluency.

Status: **implemented** as `terminology_success_rate` in `compute_translation_metrics`, but no longer
included in the default metric set. Use `--metric terminology_success_rate` to enable it when the
benchmark has reliable source terms. It is omitted for rows that have no accepted manifest
terminology.

There is no single standard Python package equivalent to `unbabel-comet`. The WMT25 Terminology
Shared Task repository provides research-code implementations:

```text
https://github.com/wmt-conference/wmt25-terminology
```

Relevant parts of that repository:

- `ranking/metric_track1`: sentence-level terminology accuracy;
- `ranking/metric_track2`: document-level terminology accuracy;
- `additional_metrics/term-consistency`: document terminology consistency.

The primary WMT terminology metric is often reported as terminology success rate, or `Acc`. It
measures how often applicable approved target terms are present in the system output.

WMT25 has two versions that matter for us:

- **Track 1 sentence-level metric**: uses Stanza lemmatization for English and target languages, then
  checks whether either original or lemmatized source/target terms appear.
- **Track 2 document-level metric**: uses a simpler lowercased count-based success rate over source
  and target terms.

The project implementation consumes the manifest `terminology` field directly. The glossary-like
shape per row is:

```json
{
  "terminology": [
    {
      "source_term": "gastrointestinal tract",
      "target_terms": ["tube digestif", "tractus gastro-intestinal"],
      "category": "other",
      "confidence": 0.9,
      "decision": "keep_both"
    }
  ]
}
```

The current implementation follows the WMT Track 2 idea more closely than the earlier binary
prototype. A manifest term is applicable only if:

- it is not marked with `decision = "drop"`;
- it has at least one accepted target term, or it is a `preserve` term;
- its `source_term` appears in the source text when source text is available;
- at least one accepted target term appears in the reference translation when a reference is
  available.

For an applicable term `t`, the row-level success contribution is count-based and capped:

```text
source_count_t = count_normalized(source_text, source_term_t)
prediction_count_t = sum_j count_normalized(prediction, target_term_tj)

success_t = min(prediction_count_t / source_count_t, 1)
```

where:

- `source_term_t` is the manifest source term;
- accepted target terms are `target_terms`;
- preserve terms use the source term itself as the expected target text;
- terms whose accepted target terms are absent from the reference are skipped for that row;
- terms with `decision = "drop"` should not be included in the metric.

Macro terminology success rate over a row is:

```text
term_success_rate_row = (1 / |T_row|) * sum_t success_t
```

where `T_row` is the set of accepted terminology items attached to that manifest row.

The project reports this on a `0` to `100` scale:

```text
terminology_success_rate_row = 100 * term_success_rate_row
```

For rows with no accepted terminology, the metric should return no score for that row rather than
treating it as a failure. In reports, this can be represented as `null`, omitted, or tracked as
`applicable_terms = 0`.

Normalization:

Before matching, terms should usually be normalized:

```text
normalize(text) = NFKC(casefold(collapse_whitespace(text)))
```

The current implementation uses normalized substring counts:

```text
count_normalized(text, term) = count(normalize(text), normalize(term))
```

This is closer to WMT Track 2's count-based implementation than conservative word-boundary matching.
It is still lighter than WMT Track 1 because it does not run Stanza lemmatization.

Possible report fields:

```json
{
  "terminology": {
    "applicable_terms": 10,
    "matched_terms": 8,
    "term_success_rate": 80.0,
    "missing_terms": [
      {
        "source_term": "phosphate-binder(s)",
        "target_terms": ["chélateurs du phosphate"]
      }
    ]
  }
}
```

Useful for:

- evaluating approved chemistry terminology;
- checking whether glossary-injected terms actually appear in the output;
- comparing terminology layer variants;
- measuring terminology coverage separately from BLEU/chrF/COMET.

Why it is good:

- it directly measures the thing our terminology layer is supposed to improve;
- it is interpretable: `80.0` means roughly 80% of applicable terms were found;
- it can be computed per row, per language, per glossary source, and per term category;
- it is much cheaper than LLM judging.

Limitations:

- exact matching can miss valid inflected or paraphrased terms;
- overly loose matching can produce false positives;
- the metric is only as good as the glossary;
- source/target term alignment is difficult when one source term translates to a phrase, synonym, or
  context-dependent term;
- document-level consistency requires heavier tracking than row-level accuracy.

### Terminology Consistency

Terminology consistency measures whether repeated source terms are translated consistently across a
document or corpus.

Status: **not implemented yet**.

A simple document-level version for this project is:

```text
consistency_t = most_common_target_rendering_count_t / total_target_renderings_t
```

and macro consistency is:

```text
terminology_consistency = (1 / |T_repeated|) * sum_t consistency_t
```

where `T_repeated` is the set of source terms that occur more than once and have detected target
renderings.

The WMT25 sentence-level Track 1 consistency metric is more sophisticated. It does not require a
gold target term for every source term. Instead, it builds a pseudo-reference from the system outputs:

1. Select source terms from each source sentence.
2. Align each selected source term to a candidate target term in the corresponding translation.
3. Count candidate target renderings per source term across the corpus.
4. Assign the pseudo-reference rendering as the most frequent target candidate for that source term.
5. Score each occurrence as a hit when the aligned candidate matches the pseudo-reference.
6. Macro-average hits over source terms.

In formula-like notation:

```text
candidate_counts[t, c] = number of times source term t aligned to target candidate c
pseudo_ref[t] = argmax_c candidate_counts[t, c]
hit_i,t = 1 if aligned_candidate_i,t == pseudo_ref[t] else 0
consistency = macro_average_t(mean_i(hit_i,t))
```

This is useful when there is no approved dictionary, but it depends on reliable source-term
selection and alignment. Since our benchmark manifests already contain accepted `target_terms`, the
first project implementation should be simpler:

```text
for each repeated manifest source_term:
    collect observed accepted target variants in outputs
    consistency_t = most_common_variant_count / total_matched_occurrences
```

If no accepted variant is found for a repeated term, terminology accuracy should capture that as a
miss. Consistency should focus on variation among matched renderings.

The WMT25 consistency implementation may require language-specific normalization, alignment, and
embedding-based matching. For a first chemistry benchmark, keep terminology accuracy and terminology
consistency as separate metrics rather than combining them into one score.

Why it is good:

- patent and chemistry translation often require the same technical term to be rendered consistently;
- consistency can matter even when the chosen term is not the exact reference term;
- it helps evaluate document-level behavior, not just sentence-level correctness.

Why not first:

- it needs reliable detection of target renderings;
- WMT25's version uses heavier dependencies and alignment machinery;
- for our current `context` examples, terminology success rate is a simpler and more useful first
  step.

### FSP / MQM LLM Judge

Status: **implemented** as optional metric `fsp_mqm`, but not included in the default metric set.
Use `--metric fsp_mqm` to enable it.

The WMT25 repository includes FSP, or Focus Sentence Prompting, as an additional metric. It is an
LLM-as-judge evaluation method based on MQM-style error analysis. Our implementation is a lightweight
segment-level MQM-style judge: it gives the judge the source, reference translation, and candidate
translation, then asks for a quality score and severity-labeled errors.

The scoring code produces these report metrics:

- `fsp_mqm`: quality score from `0` to `100`;
- `fsp_mqm_error_score`: severity-weighted error score;
- `fsp_mqm_minor_errors`: count of minor errors;
- `fsp_mqm_major_errors`: count of major errors;
- `fsp_mqm_critical_errors`: count of critical errors.

The default severity weights in their scoring utility are:

```text
minor = 1
major = 2
critical = 5
```

Why it is good:

- it can capture errors that lexical metrics miss;
- it can provide interpretable error categories;
- it is suitable for document-level translation review.

Why it is expensive:

- it requires LLM API calls;
- outputs need JSON parsing and validation;
- results depend on prompt, judge model, and calibration;
- it is slower and less deterministic than BLEU, chrF, COMET, or terminology accuracy.

Usage:

```powershell
uv run --no-sync python scripts/evaluate_parallel_manifest.py `
  --dataset-dir benchmark_datasets/jrc_acquis_articles_250_per_pair `
  --metric fsp_mqm `
  --fsp-mqm-model gpt-4.1-mini
```

For this project, FSP/MQM should be treated as an optional review metric, not a default benchmark
metric.

## What The General Metrics Do Not Measure

The current metrics are useful for fast comparison, but they are not enough for chemistry translation
quality.

They do not directly measure:

- preservation of chemical formulas such as `SiO2`, `CO2`, or `Al2O3`;
- preservation of element symbols, sequence IDs, CAS-like identifiers, and units;
- whether a translated chemical name maps to the same structure;
- stereochemistry, oxidation state, reaction role, or material identity;
- whether the translation is acceptable to a domain expert;
- whether terminology is consistent across a document or corpus.

This matters because chemistry translation can fail in high-risk ways while still retaining high
lexical overlap with the reference.

## How To Interpret Scores In This Project

Use the current metrics as comparative signals, not absolute truth.

Good uses:

- compare two models on the same subset;
- compare terminology vs no terminology on the same rows;
- catch obvious regressions;
- track benchmark results over time.

Risky uses:

- claiming one translation is chemically correct from BLEU/chrF alone;
- comparing scores across different datasets or different sample sizes without context;
- using a small sample as a final decision.

For recent experiments, source-pair benchmark datasets are the preferred path because they separate
portable source snapshots from terminology-bearing benchmark manifests. They still need
domain-specific metrics before drawing strong product conclusions.

## Recommended Next Metrics

The research notes in `docs/paper/deep-research-report.md` recommend expanding beyond lexical
metrics. The most useful additions for this codebase would be:

- **terminology success rate**: consume manifest `terminology` and check whether any accepted
  `target_terms` variant appears in the predicted translation;
- **formula/entity preservation rate**: check whether formulas, units, sequence IDs, and identifiers
  from the source are preserved in the translation;
- **terminology consistency**: check whether repeated manifest terms are translated consistently;
- **chemistry-aware human/MQM review**: categorize errors such as formula corruption, unit changes,
  wrong chemical term, omission, hallucination, or bad patent style;
- **structure validation for chemical names**: where possible, parse source/reference/predicted
  chemical names and compare canonical structures.

Until those are implemented, `sequence_similarity`, BLEU, chrF2++, and COMET should be treated as
general baseline automatic metrics. They are useful but not enough to prove chemistry or patent
terminology correctness.
