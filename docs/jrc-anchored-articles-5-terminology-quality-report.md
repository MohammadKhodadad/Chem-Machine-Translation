# JRC Anchored Articles Terminology Quality Report

This report reviews the small anchored JRC-Acquis article dataset built with non-LLM terminology
generation and all available external verifier sources.

Dataset reviewed:

```text
benchmark_datasets/jrc_acquis_anchored_articles_5_all_non_llm_terms/
```

Combined manifest:

```text
benchmark_datasets/jrc_acquis_anchored_articles_5_all_non_llm_terms/jrc-acquis-20-directions-100-manifest.jsonl
```

## Executive Summary

The article dataset is structurally good, but the terminology layer is medium quality and still too
noisy for final terminology-sensitive benchmark use.

Numerical highlights:

- 100 manifest rows across 20 ordered language directions.
- 1,919 terminology records.
- 697 verified records, which is 36.3% of all terminology records.
- 1,222 algorithmic-only records, which is 63.7%.
- 95 of 100 rows hit the 20-term cap.
- 1,150 terms, or 59.9%, were found by multiple candidate extractor tags.
- 303 terms, or 15.8%, had multiple verifier tags.
- 109 terms, or 5.7%, had both multiple extractor tags and multiple verifier tags.
- 1,919 of 1,919 target terms appeared in the target/reference text.
- 1,919 of 1,919 terminology records had empty `source_term`.

Quality judgment:

- Dataset text/alignment quality: good.
- Language consistency: good in reviewed samples.
- Target-term exact-span validity: good.
- Terminology usefulness: mixed.
- Final benchmark readiness for terminology-sensitive evaluation: not yet.

The main issue is not alignment or language mismatch. The issue is term quality: many good legal and
technical terms are present, but noisy headings, numbering fragments, table-of-contents spans,
generic verified words, and target-only terms remain.

## Pipeline Overview

The full article path is:

```text
OPUS/JRC-Acquis aligned segments
  -> anchored source JSONL
  -> benchmark dataset builder
  -> unique target chunk extraction
  -> candidate extractors
  -> duplicate/provenance merge
  -> external verifier evidence
  -> manifest terminology
  -> benchmark evaluation
```

In the source creation step, JRC documents are selected only when all required languages are
available. Each selected document is expanded to every ordered language pair. This gives true
bidirectionality: if `en-es` exists for an anchored chunk, `es-en` exists as the exact reverse.

In the dataset creation step, the builder writes `source.csv`, `target.csv`, and manifest files per
direction. For anchored datasets, repeated target chunks are deduplicated before terminology
generation. With five languages, the same target-language chunk can be reused across four incoming
source-language directions.

Terminology generation is target-side:

```text
target/reference text
  -> Stanza/UD candidates
  -> optional XLM-R/NOBI candidates
  -> merge duplicate candidate tags
  -> external verifier checks
  -> verified/algorithmic term records
```

The current terminology records are therefore exact target/reference spans. They are useful for
target-term coverage, but they are not yet complete bilingual terminology pairs because `source_term`
is still empty.

## Build Settings

The dataset was built from the anchored article source with 5 rows per ordered language direction.
It includes 20 directions across English, German, French, Spanish, and Portuguese.

Terminology settings:

- LLM extraction: disabled.
- Candidate extractors: Stanza/UD and XLM-R/NOBI.
- Verifier sources: PubChem, ChEBI, ChEMBL, MeSH, NCI Thesaurus, AGROVOC, IATE,
  Wikipedia/Wikidata, and UNTERM.
- Stanza/NOBI generation used 2 worker processes.

## Extraction Steps

1. Source rows are read from the anchored JRC article source JSONL.
2. Each row is converted into `source.csv`, `target.csv`, and manifest records.
3. Repeated anchored target chunks are deduplicated by `(target_language_code, target_text)`.
4. Stanza/UD extracts target-side terminology candidates from exact target/reference spans.
5. XLM-R/NOBI adds neural token-classification candidates when enabled.
6. Duplicate candidate terms are merged, preserving all extractor tags.
7. External verifier sources are queried for each candidate.
8. Verified terms are marked with `term_group = "verified"` and `verified_by`.
9. Final terminology records are attached to the manifest.

## Candidate Extractors

Stanza/UD is the broad deterministic extractor. It parses target/reference text with Universal
Dependencies and proposes noun-headed spans, relaxed content n-grams, and proper-name sequences. It
has good recall, but can produce generic legal boilerplate and formatting fragments.

XLM-R/NOBI is the neural extractor. It uses an XLM-R token-classification checkpoint with NOBI-style
labels for nested automatic term extraction. It tends to find cleaner salient entities and domain
nouns, but recall is lower and the current checkpoint is strongest on English.

External verifiers do not create candidates by themselves. They add evidence to candidates from the
extractors. A term can keep multiple source tags, for example:

```text
stanza_ud_dependency+xlmr_nobi+pubchem+chebi
```

## Dataset Shape

- Manifest rows: 100.
- Directions: 20.
- Rows per direction: 5.
- Total terminology records: 1,919.
- Terms per row:
  - minimum: 1.
  - median: 20.
  - mean: 19.19.
  - maximum: 20.
  - 95 of 100 rows hit the 20-term cap.

Term groups:

- `algorithmic`: 1,222.
- `verified`: 697.

Review coverage:

- Full combined manifest was used for aggregate counts.
- 40 rows and 800 terminology records were reviewed for term quality across target languages.
- 30 rows across all 20 directions were reviewed for text/alignment and terminology-in-context
  quality.

## Provenance Coverage

Candidate extractor tags:

- `stanza_ud_ngram`: 1,258 terms.
- `stanza_ud_dependency`: 1,197 terms.
- `xlmr_nobi`: 537 terms.
- `stanza_ud_proper_name`: 271 terms.
- `llm_target`: 0 terms.

Verifier tags:

- `iate`: 613 terms.
- `agrovoc`: 282 terms.
- `wikipedia`: 198 terms.
- `mesh`: 66 terms.
- `nci`: 31 terms.
- `pubchem`: 5 terms.
- `chebi`: 1 term.
- `chembl`: 0 terms.
- `unterm`: 0 terms.

Multi-source coverage:

- Terms with multiple candidate extractor tags: 1,150 of 1,919.
- Terms with multiple verifier tags: 303 of 1,919.
- Terms with both multiple candidate and multiple verifier tags: 109 of 1,919.

Example verified records:

```json
{
  "target_terms": ["European Economic Community"],
  "source": "stanza_ud_dependency+stanza_ud_ngram+xlmr_nobi+iate+wikipedia",
  "term_group": "verified",
  "verified_by": ["iate", "wikipedia"]
}
```

```json
{
  "target_terms": ["control measures"],
  "source": "stanza_ud_dependency+stanza_ud_ngram+agrovoc+iate",
  "term_group": "verified",
  "verified_by": ["agrovoc", "iate"]
}
```

Example algorithmic record:

```json
{
  "target_terms": ["blood-grouping reagents"],
  "source": "stanza_ud_dependency+xlmr_nobi",
  "term_group": "algorithmic",
  "verified_by": []
}
```

## Term Quality Review

The dataset contains many useful legal, institutional, and technical terms.

Good examples:

- English: `European Economic Community`, `controlled substances`, `blood-grouping reagents`,
  `ozone depletion`, `European Monitoring Centre on Racism and Xenophobia`.
- German: `Europäische Wirtschaftsgemeinschaft`, `Verwaltungskonto`, `Sonderkonto`,
  `Rat der Europäischen Union`, `Ozonschicht`.
- French: `Communauté économique européenne`, `protocole additionnel`,
  `substances réglementées`, `Conseil international du jute`, `Tétrachlorure de carbone`.
- Spanish: `Comunidad Económica Europea`, `Consejo internacional del yute`,
  `Cuenta administrativa`, `capa de ozono`, `sustancia de transición`.
- Portuguese: `Comunidade Económica Europeia`, `Protocolo Adicional`,
  `Conselho Internacional da Juta`, `tetracloreto de carbono`.

Questionable examples:

- English: `Protocol`, `Council`, `payment`, `account`, `technology`, `technical`.
- German: `Zahlung`, `Endziel`, `technische`, `Europarats`.
- French: `production`, `consommation`, `comptes`, `spécial`, `général`.
- Spanish: `Adicional`, `General`, `industrial`, `cuentas`, `YUTE`.
- Portuguese: `Adicional`, `industrial`, `contas`, `JUTA`, `Grupo I`.

Bad or noisy examples:

- `notification o communication`.
- `acceptance o objection`.
- `following the date`.
- `Definitions 1`.
- `CAPÍTULO II DEFINICIONES`.
- `Aufgaben des Rates .................... Artikel`.
- `K. Article`.
- `Nº 10`.
- `droits d`.
- `Conseil d`.

## Dataset Text Quality

The underlying article rows are generally aligned and usable:

- No obvious wrong-language rows were found in the reviewed sample.
- Reverse-pair consistency was clean in aggregate checks.
- Source/target size ratios looked reasonable.
- Target terms all appeared in target/reference text.

The main caveat is that terminology records are target-side candidates. `source_term` is empty for
all reviewed terminology records, so the dataset currently evaluates target/reference term coverage,
not fully aligned bilingual source-to-target terminology transfer.

## Main Issues

1. Verified does not always mean useful. Sources like IATE, AGROVOC, Wikipedia, MeSH, and NCI can
   verify broad words such as `Council`, `payment`, `industrial`, or `production`.
2. Stanza/UD provides recall, but it also introduces headings, table-of-contents fragments, article
   numbering, date fragments, and generic noun phrases.
3. XLM-R/NOBI produces cleaner candidates, but fewer of them.
4. The 20-term cap is often reached. The cap is not too low by itself; the ranking/filtering before
   the cap needs improvement.
5. Some JRC article chunks contain table-of-contents or legal-structure material. The parallel text is
   aligned, but not always ideal for terminology-sensitive evaluation.

## Recommendations

Before using this as a terminology-sensitive benchmark, improve term filtering and ranking:

1. Populate `source_term` by aligning target terms back to the source side where possible.
2. Down-rank generic single-token terms unless they are strong acronyms, formulas, or exact named
   entities.
3. Reject terms that look like headings, table-of-contents fragments, article references, isolated
   numbering, or partial spans ending in function words.
4. Prefer verified multiword terms over verified single-word generic terms.
5. Give a ranking bonus when both Stanza/UD and XLM-R/NOBI find the same term.
6. Treat external verifier matches as evidence, not automatic quality.
7. Consider a stricter legal/JRC stoplist for boilerplate terms such as `Protocol`, `Council`,
   `General`, `Adicional`, `payment`, and `account` unless supported by stronger context.
8. Increase document diversity after the filtering is improved. The 5-record anchored test is useful
   for controlled inspection, but too small and repetitive for final benchmark conclusions.

## Overall Assessment

The article dataset itself is structurally usable and aligned. The terminology layer is promising but
too noisy for final terminology-sensitive evaluation without additional filtering. The best immediate
next step is not adding more extractors; it is improving term ranking and filtering while preserving
the current provenance tags.
