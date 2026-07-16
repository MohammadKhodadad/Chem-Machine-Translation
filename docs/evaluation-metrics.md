# Evaluation Metrics

This project computes automatic reference-based metrics for benchmark scripts such as
`scripts/evaluate_google_patents.py` and `scripts/evaluate_epo.py`. By default, benchmark scripts
compute `sequence_similarity`, BLEU, chrF2++, and COMET. Use repeated `--metric` flags to override
the default set.

The implementation lives in `src/chem_machine_translation/evaluation/metrics.py`:

```python
def compute_translation_metrics(
    prediction: str,
    reference: str,
    source: str | None = None,
    metric_names: list[str] | tuple[str, ...] | None = None,
    comet_scorer: CometScorer | None = None,
) -> dict[str, float]:
    ...
```

Each benchmark row stores these values under the `metrics` field in the JSONL report. The evaluation
scripts then print the average metric values per target language.

## Metric Groups

We separate metrics into two groups:

- **General metrics**: language-agnostic reference-overlap metrics. These are useful for comparing
  systems on the same benchmark, but they do not understand chemistry.
- **Domain-specific metrics**: chemistry- or patent-aware checks. These are intended to measure
  things like formula preservation, terminology consistency, and chemical identity.

At the moment, the codebase implements `sequence_similarity`, BLEU, chrF, chrF2++, and
reference-based COMET. Terminology accuracy is a planned integration.

## Current Status

Implemented in code:

- `sequence_similarity`: simple string-level similarity, useful as a sanity check.
- `bleu`: sentence-level SacreBLEU BLEU, useful as a standard lexical baseline.
- `chrf`: sentence-level SacreBLEU chrF, useful for morphology and character-level overlap.
- `chrf2++`: WMT-style chrF with word bigrams, now preferred over plain `chrf` in defaults.
- `comet`: reference-based COMET with `Unbabel/wmt22-comet-da`, useful for semantic MT quality.

Reviewed from the WMT25 Terminology Shared Task repository:

- `chrf2++`: WMT25 uses chrF with character n-grams and word n-grams for general MT quality.
- `term_success_rate` / `Acc`: WMT25's main terminology accuracy metric.
- `term_consistency` / `Cons.`: WMT25's terminology consistency metric.
- `FSP`: an LLM-as-judge MQM-style document evaluation metric.

Recommended next implementation for this project:

- first add terminology success rate;
- then add normalized terminology accuracy;
- later consider simplified terminology consistency;
- keep FSP/MQM as a later, expensive evaluation option.

The practical interpretation is: general metrics tell us whether the translation resembles the
reference and preserves meaning broadly; domain-specific metrics tell us whether chemistry-critical
terms, symbols, units, and identifiers survived correctly.

## General Metrics

### Sequence Similarity

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

`bleu` is computed with `sacrebleu.metrics.BLEU` using sentence-level scoring:

```python
BLEU(effective_order=True).sentence_score(prediction, [reference]).score
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

The code uses `BLEU(effective_order=True)`, so SacreBLEU adapts the effective maximum n-gram order
for sentence-level scoring when the text is too short to support all normal n-gram orders.

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
- sentence-level BLEU is noisier than corpus-level BLEU, especially on small samples.

### chrF

`chrf` is computed with `sacrebleu.metrics.CHRF` using sentence-level scoring:

```python
CHRF().sentence_score(prediction, [reference]).score
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
- it does not validate formulas, identifiers, stereochemistry, units, or reaction roles.

### chrF2++ / WMT-Style chrF

Status: **implemented** as `chrf2++`.

The WMT25 Terminology Shared Task uses chrF2++ for general MT quality. In code, their setting is:

```python
CHRF(char_order=6, word_order=2)
```

This differs from plain `CHRF()` because chrF2++ includes word n-gram overlap in addition to
character n-gram overlap.

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

Why we should add it:

- it makes our evaluation closer to WMT terminology evaluation practice;
- it is cheap to compute;
- it is a better default lexical metric than BLEU alone for German/French patent text.

### COMET

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
uv run python scripts/evaluate_epo.py `
  --metric sequence_similarity `
  --metric bleu `
  --metric chrf
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
- tested on a one-row EPO smoke run under Python `3.12`;
- project Python is constrained to `<3.13` because the COMET dependency stack is not currently
  reliable on Python `3.13` on Windows.

## Report-Level Aggregation

The benchmark scripts compute metrics per row and then average each metric by target language.

For example, `scripts/evaluate_epo.py` writes rows like:

```json
{
  "target_language": "German",
  "predicted_translation": "...",
  "ground_truth_translation": "...",
  "metrics": {
    "sequence_similarity": 46.7,
    "bleu": 46.01,
    "chrf": 72.24
  }
}
```

Then the script prints language-level means:

```text
German: n=50, bleu=46.01, chrf=72.24, sequence_similarity=46.70
```

These are simple arithmetic averages over the evaluated rows.

## Domain-Specific Metrics

Domain-specific metrics are not implemented in `compute_translation_metrics` yet. They are the
metrics we should add to evaluate chemical and patent translation behavior more directly.

Planned domain-specific metrics include:

- formula/entity preservation rate;
- terminology accuracy / terminology success rate;
- terminology consistency across documents;
- chemical name/structure validation;
- unit and numerical value preservation;
- sequence ID and identifier preservation;
- chemistry-aware human/MQM review categories.

These metrics should complement the general metrics, not replace them. BLEU, chrF, and sequence
similarity tell us how close the output is to the reference wording; domain-specific metrics tell us
whether chemically important information survived the translation.

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

Status: **not implemented yet, recommended next**.

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

For this project, a small reusable glossary matcher may be easier to integrate first.

Glossary shape:

```python
{
    "acetylsalicylic acid": ["acide acétylsalicylique"],
    "cyclooxygenase": ["cyclooxygénase"],
    "active ingredient": ["principe actif", "substance active"],
}
```

Per-term formula:

```text
source_count_t = count(source, source_term_t)
target_count_t = sum_j count(prediction, valid_target_term_tj)
matched_count_t = min(source_count_t, target_count_t)
accuracy_t = matched_count_t / source_count_t
```

where:

- `source_term_t` is the source-language glossary term;
- `valid_target_term_tj` is one accepted target-language rendering for that source term;
- `source_count_t` is how many times the source term appears in the source;
- `target_count_t` is how many accepted target terms appear in the translation;
- `matched_count_t` is clipped so extra repeated target terms do not receive extra credit.

Macro terminology accuracy over all applicable terms is:

```text
terminology_accuracy = (1 / |T_applicable|) * sum_t accuracy_t
```

where `T_applicable` is the set of glossary terms that actually appear in the source text.

If no glossary terms appear in the source, the metric should return no score for that row rather
than treating it as a failure. In reports, this can be represented as `null`, omitted, or tracked as
`applicable_terms = 0`.

Normalization:

Before matching, terms should usually be normalized:

```text
normalize(text) = NFKC(casefold(collapse_whitespace(text)))
```

The simple implementation can use conservative word-boundary matching:

```text
(?<!\w)term(?!\w)
```

This works reasonably for English, French, and German glossary terms, but languages without
whitespace-based tokenization need language-specific matching.

Useful for:

- evaluating approved chemistry terminology;
- checking whether glossary-injected terms actually appear in the output;
- comparing terminology layer variants;
- measuring terminology coverage separately from BLEU/chrF/COMET.

Why it is good:

- it directly measures the thing our terminology layer is supposed to improve;
- it is interpretable: `0.80` means roughly 80% of applicable terms were found;
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

One simple document-level version is:

```text
consistency_t = most_common_target_rendering_count_t / total_target_renderings_t
```

and macro consistency is:

```text
terminology_consistency = (1 / |T_repeated|) * sum_t consistency_t
```

where `T_repeated` is the set of source terms that occur more than once and have detected target
renderings.

The WMT25 consistency implementation is more sophisticated and heavier. It may require
language-specific normalization, alignment, and embedding-based matching. For a first chemistry
benchmark, keep terminology accuracy and terminology consistency as separate metrics rather than
combining them into one score.

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

Status: **not implemented yet**.

The WMT25 repository includes FSP, or Focus Sentence Prompting, as an additional metric. It is an
LLM-as-judge evaluation method based on MQM-style error analysis. It evaluates a focused segment
while giving the judge access to wider document context.

The scoring code produces:

- `quality_score`;
- `error_score`;
- severity-weighted errors:
  - minor errors;
  - major errors;
  - critical errors.

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

For this project, FSP/MQM should be treated as a later review metric, not a default benchmark metric.

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
- using a small sample, such as `n=5`, as a final decision.

For recent experiments, the EPO `gpt-4.1-nano` agentic benchmark used `n=100` rows, while the Google
Patents terminology smoke test used only `n=5`. The EPO numbers are therefore more meaningful, but
still need chemistry-specific checks before drawing strong product conclusions.

## Recommended Next Metrics

The research notes in `docs/paper/deep-research-report.md` recommend expanding beyond lexical
metrics. The most useful additions for this codebase would be:

- **formula/entity preservation rate**: check whether formulas, units, sequence IDs, and identifiers
  from the source are preserved in the translation;
- **terminology accuracy**: check whether approved target terms appear when their source terms are
  present;
- **terminology consistency**: check whether repeated chemistry terms are translated consistently;
- **chemistry-aware human/MQM review**: categorize errors such as formula corruption, unit changes,
  wrong chemical term, omission, hallucination, or bad patent style;
- **structure validation for chemical names**: where possible, parse source/reference/predicted
  chemical names and compare canonical structures.

Until those are implemented, BLEU, chrF, and sequence similarity should be treated as baseline
automatic metrics.
