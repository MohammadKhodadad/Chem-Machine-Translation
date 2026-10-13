---
language:
- de
- en
- es
- fr
- ru
- zh
task_categories:
- translation
tags:
- chemistry
- patents
- terminology
- evaluation
pretty_name: Google Patents Chemistry Terminology Benchmark (4500, Luna)
---

# Google Patents Chemistry Terminology Benchmark

This repository contains the completed `google_patents_chemistry_250_luna_scratch`
benchmark: 4,500 segment pairs across 18 ordered translation directions, with 250
examples per direction. It is an evaluation resource, not model translation output.
Generation completed on 12 October 2026.

## Files and Usage

- `google-patents-18-directions-4500-pairs-manifest.jsonl`: combined manifest of
  example identifiers, language directions, source metadata, and terminology
  annotations. The manifest does not embed the paired text; use the CSV files.
- `metadata.json`: generation configuration and summary metadata.
- Each language-direction directory contains `source.csv`, `target.csv`, and a
  direction-specific 250-row manifest. Use the manifest's source/target row IDs
  to associate text and annotations. The per-direction manifests repeat the
  corresponding combined-manifest entries; do not count both as separate examples.

The directions are `de-en`, `de-fr`, `en-de`, `en-es`, `en-fr`, `en-ru`, `en-zh`,
`es-en`, `es-fr`, `fr-de`, `fr-en`, `fr-es`, `fr-ru`, `fr-zh`, `ru-en`, `ru-fr`,
`zh-en`, and `zh-fr`. Reverse directions reuse paired evidence and are not
independent patent publications.

## Provenance and Annotation

The source pipeline consumes within-publication abstract pairs documented as a
Google Patents Chemical derivative from
`BASF-AI/ai4chem-clir-google-patents-within-document-abstract-pairs`.
Terminology extraction combines domain-prompted LLM proposals, Stanza UD,
XLM-R/NOBI, and spaCy. External evidence comes from local IATE, Wikidata, and
AGROVOC. LLM curation selects exact reference spans, with candidate/refined caps
of 80/16 and the configured model identifier `gpt-6-luna`. See `metadata.json`
for the recorded generation settings.

Annotations are automatic. External support and LLM selection are not human
validation or chemical-structure verification. Reference-derived terms supplied
to a translator constitute an oracle terminology condition, not a source-only
retrieval baseline. Publication/family overlap and proprietary model pretraining
contamination have not been ruled out. Approximate lengths use whitespace counts,
which are especially limited for Chinese.

## Reproduction and Rights

Implementation and configuration:
[Chem-Machine-Translation](https://github.com/MohammadKhodadad/Chem-Machine-Translation),
`config/benchmark_generation/google_patents_chemistry_250_luna_scratch.toml`.
The generated artifacts were committed as `0aed73c`. This dataset card was added
for the Hugging Face upload after that commit.

This card does not assign a new license to the underlying patent text or external
terminology resources. Consult upstream terms before redistribution or use.