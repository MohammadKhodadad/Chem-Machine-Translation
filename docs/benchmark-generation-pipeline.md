# Benchmark Generation Pipeline

This document describes the full benchmark generation pipeline: source-pair creation, dataset
manifest writing, terminology candidate extraction, verifier enrichment, LLM refinement, and
evaluation-time terminology groups.

The short command reference is in `benchmark_datasets/README.md`. This document explains what each
part of those commands does and how the terminology objects move through the system.

## High-Level Flow

Benchmark generation has four main stages.

1. Create or reuse a source-pair snapshot in `benchmark_sources/`.
2. Build benchmark-ready direction folders in `benchmark_datasets/`.
3. Generate target-side terminology candidates and verifier evidence for each target/reference
   segment.
4. Run the final LLM refiner when the benchmark needs the final `refined` terminology group.

The pipeline is target-side for benchmark terminology. Candidate extractors read the target/reference
text and return exact spans that appear in that text. They do not translate source terms during
benchmark generation.

The standard terminology setup is:

- Broad candidate pool: up to `40` terms per segment.
- Final refined pool: up to `8` terms per segment.
- Default LLM: `gpt-4.1-mini`.
- Default API mode: `responses`.
- Default max output tokens for terminology calls: `1024`.
- Temperature: `0.0` in the LLM call code.

## Source-Pair Snapshots

Source-pair snapshots are portable JSONL files under `benchmark_sources/`. They are the stable input
to benchmark dataset builders.

Google Patents uses `scripts/create_google_patents_source_pairs.py` to create source-target patent
pairs, usually from title and abstract text within the same patent family or document context.

JRC-Acquis uses `scripts/create_jrc_acquis_source_pairs.py`. That script downloads or reuses OPUS
JRC-Acquis data, aligns document segments, chunks them within document boundaries, and writes
language-pair JSONL rows. It supports:

- `--section-type article` for operative legal provisions.
- `--section-type definition` for definition-heavy passages.
- `--selection-mode anchored` for shared document anchors and exact reverse rows.
- `--clean-legacy-markup` to remove legacy markup noise.
- `--quality-mode strict` to keep cleaner aligned chunks.

The current JRC source snapshots are:

- `benchmark_sources/jrc_acquis_anchored_articles_250_per_language_pair.jsonl`
- `benchmark_sources/jrc_acquis_anchored_definitions_250_per_language_pair.jsonl`

## Dataset Builders

Dataset builders consume a source-pair JSONL snapshot and write benchmark direction folders. Each
direction folder contains:

- `source.csv`
- `target.csv`
- one direction-specific `*-manifest.jsonl`

The builders also write a combined manifest at the output root.

The main builder scripts are:

- `scripts/build_google_patents_eval_subset.py`
- `scripts/build_jrc_acquis_eval_subset.py`

Each manifest row stores dataset metadata, source/target language metadata, token counts, row IDs,
and a `terminology` array. During construction the builders keep internal `_source_text` and
`_target_text` fields in memory; those private fields are removed before writing the final manifest.

## Terminology Object Schema

Terminology entries are represented by `DatasetTerminologyTerm` in
`src/chem_machine_translation/data/terminology.py`.

Important fields:

- `source_term`: source-side term when available. Benchmark target-side extraction usually leaves
  this empty.
- `target_terms`: exact target/reference spans selected as terminology.
- `reference_candidates`: fallback reference-side candidates.
- `category`: coarse domain category such as `chemical`, `material`, `legal_act`, or
  `defined_term`.
- `source`: provenance string. Multiple sources are joined with `+`, for example
  `stanza_ud_dependency+xlmr_nobi+iate`.
- `term_group`: evaluation group, usually `llm`, `algorithmic`, `verified`, or `refined`.
- `verified_by`: external evidence sources that matched the term, such as `iate` or `pubchem`.
- `confidence`: extractor confidence adjusted by verifier evidence.
- `decision`: preservation/refinement decision such as `preserve`, `translate`, or `keep_refined`.
- `reason`: short human-readable explanation.
- `candidates`: external synonym or label evidence collected from verifier APIs.

The code deduplicates terms by normalized target surface. When duplicates are merged, provenance and
verifier evidence are unioned rather than discarded.

## Candidate Extractor Families

The standard candidate stage combines four extractor families.

### LLM Chemistry Extractor

Class: `LLMTargetCandidateExtractor`

Used by Google Patents when `--extract-terminology` is passed.

This extractor sends the target/reference text to the LLM and asks for exact technical spans only.
It is chemistry and patent oriented. It looks for chemical names, compounds, materials, formulas,
reagents, solvents, polymers, proteins, process names, assay terms, analytical terms, properties,
hazards, identifiers, and technically meaningful units.

The parser accepts only terms that:

- appear as exact spans in the target/reference text;
- are returned as valid JSON;
- have a recognized category and confidence;
- are not rewritten, lemmatized, translated, or invented.

Output terms use:

- `source`: `llm_target`
- `term_group`: `llm`

### LLM Legal Extractor

Class: `LLMLegalCandidateExtractor`

Used by JRC-Acquis when `--extract-legal-terms` is passed.

This extractor is tuned for legal and institutional terminology. It looks for legal instruments,
institutions, committees, agencies, programmes, funds, procedures, rights, obligations, restrictions,
sanctions, remedies, legal effects, regulatory domains, and explicitly defined terms.

It rejects dates, article numbers alone, paragraph references alone, personal names, signatures,
whole clauses, generic single words, and ordinary administrative prose.

Output terms use:

- `source`: `legal_llm`
- `term_group`: `llm`

### Stanza/UD Extractor

Class: `TargetTerminologyExtractor`

Google uses this extractor by default inside `DatasetTerminologyGenerator` unless
`--no-stanza-extractor` is passed. JRC uses it when `--extract-stanza-terms` is passed.

The extractor lazily loads a Stanza pipeline for the target language with:

```text
tokenize,pos,lemma,depparse
```

It then builds three candidate streams.

Dependency candidates use noun-like Universal Dependencies heads. The extractor expands heads with
dependency relations such as modifiers, compounds, names, appositions, flat names, numeric modifiers,
and selected nominal relations. These candidates use:

- `source`: `stanza_ud_dependency`
- confidence around `0.72`

Relaxed n-gram candidates scan sentence windows of one to six words. They reject windows with verbs,
auxiliaries, punctuation-like dependencies, poor boundaries, and spans without content words. These
candidates use:

- `source`: `stanza_ud_ngram`
- confidence derived from content-word count, capped below the dependency candidates

Proper-name candidates collect runs of proper nouns with at least two tokens. These candidates use:

- `source`: `stanza_ud_proper_name`
- confidence around `0.70`

All Stanza candidates are cleaned and exact-span checked before becoming manifest terms. The
extractor rejects noisy punctuation, malformed separators, citation-like fragments, date fragments,
and many short generic fragments.

### XLM-R/NOBI Extractor

Class: `XLMRNOBITerminologyExtractor`

Enabled with `--use-nobi-extractor`.

The default model is:

```text
tthhanh/xlm-ate-nobi-en-nes
```

The extractor uses a Hugging Face token-classification pipeline with no aggregation strategy. It
maps the model labels into BIO-style term spans, handles subword continuations, and decodes contiguous
terminology spans from the target/reference text.

The implementation truncates input to the first `4000` characters. It does not route by target
language; the model is loaded once and applied to the supplied text.

Output terms use:

- `source`: `xlmr_nobi`
- `term_group`: `algorithmic`

### spaCy Extractor

Class: `SpaCyTerminologyExtractor`

Enabled with `--use-spacy-extractor`.

The spaCy extractor is an exact-span extractor. It uses trained spaCy linguistic annotations when a
language model is available, and falls back to a blank spaCy pipeline when possible.

Default language model mapping:

- German: `de_core_news_sm`
- English: `en_core_web_sm`
- Spanish: `es_core_news_sm`
- French: `fr_core_news_sm`
- Japanese: `ja_core_news_sm`
- Portuguese: `pt_core_news_sm`
- Russian: `ru_core_news_sm`
- Chinese: `zh_core_web_sm`

If `--spacy-model` is provided, that model is loaded instead of the language default. The input is
truncated to the first `4000` characters.

The spaCy extractor has three internal components.

Named-entity terms read `doc.ents`, trim non-content boundary tokens, clean the surface form, and
keep candidates that have at least one content token. These candidates use:

- `source`: `spacy_entity`
- confidence base around `0.78`

Noun-chunk terms read `doc.noun_chunks` when the loaded pipeline supports noun chunks. Languages or
blank pipelines without noun chunks fail closed and simply return no noun-chunk terms. These
candidates use:

- `source`: `spacy_noun_chunk`
- confidence base around `0.72`

Token n-gram terms use sentence-scoped contiguous runs of candidate tokens. With POS tags, the
extractor considers windows up to five tokens. Without POS tags, it limits windows to three tokens.
It rejects stopword boundaries, punctuation boundaries, windows without content, and POS patterns
that do not look terminology-like. These candidates use:

- `source`: `spacy_ngram`

The spaCy extractor is useful as a broad deterministic recall source, especially when named entities
or noun chunks capture domain phrases missed by the LLM or Stanza paths.

## Verifier And Enrichment Sources

Verifiers do not create the initial span. They check whether an extracted target-side candidate has
external evidence, then append provenance and synonyms or labels.

If a verifier matches:

- its name is appended to `source`;
- its name is added to `verified_by`;
- matching labels or synonyms are stored in `candidates`;
- confidence increases by `0.05` per verifier source, capped at `1.0`;
- `term_group` becomes `verified`.

### Chemistry Verifiers

Google Patents chemistry builds can use these verifier flags:

- `--iate-terminology`: IATE same-language terminology lookup.
- `--wikidata-terminology`: Wikidata label lookup. Stored as `wikipedia` in term evidence for
  historical naming compatibility.
- `--pubchem-terminology`: PubChem compound synonym lookup.
- `--chebi-terminology`: ChEBI synonym lookup through the EBI API.
- `--chembl-terminology`: ChEMBL molecule and synonym lookup.
- `--mesh-terminology`: MeSH descriptor lookup through the NLM API.
- `--nci-terminology`: NCI Thesaurus lookup through EVS REST.
- `--agrovoc-terminology`: AGROVOC multilingual label lookup through Skosmos.

### Legal Verifiers

JRC legal builds normally use:

- `--iate-terminology`: IATE same-language legal terminology lookup.
- `--wikipedia-terminology`: Wikidata label lookup, stored as `wikipedia`.
- `--unterm-terminology`: UNTERM public search-page evidence.

There is also EuroVoc descriptor matching support in the legal terminology code. The current JRC
builder passes an empty descriptor map, so EuroVoc is not part of the standard JRC command unless
that metadata is supplied.

## Generator Orchestration

### Google Patents

Google uses `DatasetTerminologyGenerator`.

When the standard command is used, the generator runs:

1. LLM chemistry extraction from the target/reference text.
2. Stanza/UD extraction.
3. XLM-R/NOBI extraction.
4. spaCy extraction.
5. Deduplication and broad cap to `--terminology-max-terms 40`.
6. External chemistry verifier enrichment.
7. Ranking through `select_dataset_terms`.
8. Cache write when `--terminology-cache` is supplied.

The relevant flags are:

- `--extract-terminology`
- `--terminology-model gpt-4.1-mini`
- `--terminology-max-terms 40`
- `--use-nobi-extractor`
- `--use-spacy-extractor`
- `--terminology-workers`
- chemistry verifier flags

### JRC-Acquis

JRC uses a split flow because the legal LLM extractor and deterministic target extractors are run as
separate stages.

First, `LegalTerminologyGenerator` runs when `--extract-legal-terms` is set:

1. LLM legal extraction from the target/reference text.
2. IATE, Wikidata, UNTERM, and optional EuroVoc evidence.
3. Ranking through `select_legal_terms`.

Then, `DatasetTerminologyGenerator` runs when `--extract-stanza-terms` is set:

1. Stanza/UD extraction.
2. Optional XLM-R/NOBI extraction.
3. Optional spaCy extraction.
4. External evidence enrichment.
5. Ranking through `select_dataset_terms`.

The builder then merges the legal and algorithmic results with `deduplicate_terms`.

The JRC builder also caches deterministic target-term extraction by target language and target text,
which matters because anchored JRC rows can reuse the same target chunk across directions.

The article and definition benchmark commands differ only in the source JSONL and output directory.
The terminology pipeline is the same for both.

## LLM Refiner

Class: `LLMTerminologyRefiner`

The refiner is the final selection stage. It receives the full target/reference text and the existing
candidate pool. It must select from provided candidate IDs only. It cannot invent new terms, rewrite
terms, or repair spans.

Domain routing:

- `chemistry` and `google_patents` use the chemistry refiner prompt and append
  `llm_refiner_chem` to `source`.
- `jrc` and `legal` use the legal refiner prompt and append `llm_refiner_jrc` to `source`.

The standard refiner target is:

```text
max_terms = 8
```

The refiner is allowed to return fewer than eight terms when fewer candidates are truly useful. It
should prefer externally verified terms when quality is comparable, but it can keep an unverified
term when the term is central and translation-sensitive.

The parser validates every refined item:

- the candidate ID must exist;
- the selected target term must match the original candidate term;
- the term must still appear exactly in the target/reference text;
- the returned quality score must pass the prompt threshold.

Accepted refined terms use:

- `term_group`: `refined`
- `decision`: `keep_refined`
- `source`: original provenance plus the refiner tag

At the time of writing, the main dataset builder commands create candidate and verified manifests.
The final refiner stage is available through scripts such as `scripts/refine_final_four_terms.py` and
the audit tooling, but it is not yet a single integrated full-dataset builder flag.

## Evaluation Terminology Groups

Terminology metrics support these groups:

- `llm`: target-side LLM extractor candidates.
- `algorithmic`: deterministic candidates from Stanza/UD, XLM-R/NOBI, or spaCy.
- `verified`: candidates with external verifier evidence.
- `refined`: final LLM-refiner-selected terms.

The default terminology metric group is `verified`, which is appropriate for candidate-only
manifests. Final benchmark scoring should use `refined` after the refiner stage has been applied.

For candidate-only manifests:

```powershell
uv run --no-sync python scripts/evaluate_parallel_manifest.py `
  --dataset-dir benchmark_datasets/<dataset>/<direction> `
  --metric target_term_coverage `
  --terminology-term-group verified `
  --max-manifest-terminology-terms 8
```

For finalized refiner manifests:

```powershell
uv run --no-sync python scripts/evaluate_parallel_manifest.py `
  --dataset-dir benchmark_datasets/<dataset>/<direction> `
  --metric target_term_coverage `
  --terminology-term-group refined `
  --max-manifest-terminology-terms 8
```

## Standard Build Commands

The copy-paste commands live in `benchmark_datasets/README.md`.

Use the Google Patents command there for chemistry benchmarks. It enables the LLM chemistry
extractor, Stanza/UD, XLM-R/NOBI, spaCy, and the chemistry verifier set.

Use the JRC article or definition commands there for legal benchmarks. Both enable the legal LLM
extractor, Stanza/UD, XLM-R/NOBI, spaCy, and the legal verifier set.

## Important Implementation Files

- `scripts/create_google_patents_source_pairs.py`: builds Google source-pair snapshots.
- `scripts/create_jrc_acquis_source_pairs.py`: builds JRC article and definition source-pair
  snapshots.
- `scripts/build_google_patents_eval_subset.py`: builds Google benchmark manifests and terminology.
- `scripts/build_jrc_acquis_eval_subset.py`: builds JRC benchmark manifests and terminology.
- `src/chem_machine_translation/data/terminology.py`: terminology schema, extractors, verifiers,
  generators, deduplication, and LLM refiner.
- `src/chem_machine_translation/evaluation/metrics.py`: terminology group filtering and coverage
  metrics.
- `src/chem_machine_translation/translation/terminology.py`: translation-time terminology injection
  and source-side extraction. This is related, but separate from benchmark manifest generation.

