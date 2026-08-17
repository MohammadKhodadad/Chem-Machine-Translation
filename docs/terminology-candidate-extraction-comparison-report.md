# Terminology Candidate Extraction Comparison Report

This report compares the candidate extraction methods tested for the benchmark terminology
pipeline. The objective was to remove non-deterministic LLM candidate generation where possible,
while preserving high recall and exact target-side spans.

## Scope

The tests focused on candidate generation only, plus one follow-up verifier trial:

- deterministic Stanza/Universal Dependencies extraction;
- XLM-R/NOBI checkpoint loading;
- GLiNER-style open extraction availability;
- Stanza candidates followed by external verification, without LLM extraction.

The external verifier trial used the public verifier clients already available in the project:
PubChem, ChEBI, ChEMBL, MeSH, NCI Thesaurus, AGROVOC, IATE, Wikidata/Wikipedia, and UNTERM.

## Method 1: Stanza/UD Candidate Extraction

The production non-LLM candidate path was changed to use a Stanza-based Universal Dependencies
pipeline. The older non-LLM methods were removed from the active extraction path:

- ChemDataExtractor;
- ChemBERTa/ChemU-style token classification;
- hardcoded chemistry phrase regexes.

The new extractor uses language-generic syntax signals:

- noun-headed dependency spans;
- relaxed content n-grams;
- proper-name sequences.

It keeps exact spans from the target/reference text and does not use language-specific chemical
word lists.

### Chemistry Smoke Test

Input:

```text
The formulation contains sodium chloride solution and thermal decomposition products.
```

Observed candidates included:

```text
thermal decomposition products | stanza_ud_dependency | 0.72
sodium chloride solution | stanza_ud_dependency | 0.72
thermal decomposition | stanza_ud_dependency | 0.72
sodium chloride | stanza_ud_ngram | 0.55
```

Assessment: good candidate recall for the chemistry-style sentence. It recovered nested spans such
as `sodium chloride solution` and `sodium chloride`.

### JRC Anchored Articles Trial

A larger candidate-only run was started on the anchored JRC article source and paused for review.

Completed written output before pausing:

- Directions: `6`
- Rows: `1500`
- Terms: `15000`
- Terms per row: `10`
- Sources: all `stanza_ud_dependency`

Completed directions:

- `de-en`
- `de-es`
- `de-fr`
- `de-pt`
- `en-de`
- `en-es`

Observed JRC candidates included:

```text
Secretary-General of the Council of Europe
Contracting Party to the Agreement
Member States of the European Economic Community
containment, recovery, recycling or destruction of controlled substances
following the procedures in Article 10 of the Convention
```

Assessment: technically successful and high-recall, but too broad for legal/JRC articles without a
ranking or verification step. The method finds plausible legal noun phrases, but not all are useful
benchmark terminology.

## Method 2: XLM-R + NOBI

The neural comparison script supports an XLM-R/NOBI extractor using a Hugging Face token
classification checkpoint:

```text
tthhanh/xlm-ate-nobi-en-nes
```

Status: evaluated successfully after explicitly downloading the checkpoint weights. The model card
indicates the checkpoint was trained on English ACTER data, so multilingual behavior is cross-lingual
rather than fully supervised for every target language.

Assessment: promising as a precision-oriented extractor. It produced cleaner but lower-recall spans
than Stanza/UD in the five-language JRC sample run.

## Method 3: GLiNER-Style Extraction

The neural comparison script also supports GLiNER-style open extraction.

Status: not evaluated because the package is not installed:

```text
No module named 'gliner'
```

Assessment: useful to try later as an additional recall generator, but it should not be treated as
the primary ATE method without boundary-quality testing.

## Method 4: Stanza/UD + External Verification, No LLM

The JRC builder was extended so Stanza candidates can be sent through external verifiers without
enabling LLM terminology extraction.

The tested command used:

```text
Stanza/UD candidates
  -> PubChem
  -> ChEBI
  -> ChEMBL
  -> MeSH
  -> NCI Thesaurus
  -> AGROVOC
  -> IATE
  -> Wikidata/Wikipedia
  -> UNTERM
```

The first attempts exposed network robustness issues from public APIs:

- MeSH closed the connection without response.
- ChEMBL raised an SSL read error.

The verifier clients were updated to fail closed on these low-level network errors instead of
crashing the dataset build.

### Partial Verified Result

A 5-per-language-pair run was started and stopped after confirming the flow worked. The first
completed direction was:

```text
de-en
```

For that direction:

- Rows: `5`
- Terms: `50`
- Verified terms: `1`
- Algorithmic-only terms: `49`
- Verified source found: `wikipedia`

Example verified term:

```text
MEMBER STATES OF THE COUNCIL OF EUROPE | stanza_ud_dependency+wikipedia | verified
```

Assessment: the full non-LLM flow works, but verification coverage was low on the first completed
JRC direction. The main reason appears to be candidate quality: Stanza/UD produced broad legal noun
phrases, and most did not exactly verify against the configured public sources.

## Span-Based Methods Not Kept

Two additional span-based architectures were checked:

- Feature-less End-to-End Nested Term Extraction.
- BINDER-style contrastive span/type extraction.

Feature-less Nested ATE is conceptually a close match for our candidate-harvesting need, but the
public implementation is training code rather than a ready multilingual checkpoint. BINDER has public
training/evaluation code, and a biomedical-patent Hugging Face checkpoint was found, but a quick load
test produced newly initialized weights and poor token-level outputs such as `contains` and `The`.

Decision: do not keep either as a current extractor. They are worth revisiting only after training or
obtaining a proper checkpoint.

## Recommendation

For now:

1. Keep Stanza/UD as the default deterministic non-LLM candidate generator.
2. Always pair it with external verification for benchmark terminology.
3. Use XLM-R/NOBI as a precision-oriented auxiliary extractor.
4. Treat GLiNER, BINDER, or a trained multilingual span classifier as future neural extractor
   candidates only when a usable checkpoint is available.

The strongest next architecture is still:

```text
candidate spans -> multilingual encoder -> trained termhood score -> low threshold -> verifiers
```

That would preserve exact nested spans while avoiding the broad-span problem seen in plain Stanza/UD
while improving multilingual recall beyond the current English-trained NOBI checkpoint.
