# Action Items

This file turns the research notes in `docs/paper/deep-research-report.md` into concrete next
steps for the translation benchmark and system design.

## Metrics To Add

### Immediate Metrics

- Add `chrf++` alongside the current `chrf` score so reports can capture character-level overlap
  with word n-gram context.
- Add protected-span preservation rate for formulas, CAS numbers, identifiers, units, temperatures,
  concentrations, pH values, and markup tags.
- Add numeric/unit preservation checks that compare values and unit strings between the source and
  translated output.
- Add chemical-token preservation checks for formulas and compact notations such as `CO2`,
  `Zr/ZIF-8`, `C(sp3)-H`, SMILES-like strings, and InChI-like strings.
- Add terminology consistency checks against a small project glossary for high-value chemistry terms.

### Next Metrics

- Add entity-level precision, recall, and F1 for chemical names, reaction roles, conditions, yields,
  and hazard phrases.
- Add reference-based semantic metrics such as COMET or MetricX for runs that have gold references.
- Add reference-free quality estimation, preferably xCOMET or a reviewer-model score, for large
  translation batches without references.
- Add omission/addition counts from the reviewer output so agentic runs can be compared beyond the
  final approval flag.
- Add per-language metric summaries to detect languages where chemistry fidelity drops.

### Chemistry-Specific Metrics

- Add OPSIN parse rate for translated systematic chemical names when the target language or output
  convention keeps IUPAC-style names parseable.
- Add canonical SMILES exact match for spans that can be parsed before and after translation.
- Add standard InChI exact match for structure-level equivalence.
- Add round-trip structure fidelity for notation-heavy examples.
- Add a stereochemistry audit for chiral markers, E/Z notation, R/S notation, and related tokens.

## Architecture And Solution Options

### Baseline Translation Strategies

- Keep `one-shot` as the simple provider-backed LLM baseline.
- Keep provider selection separate from translation behavior so OpenAI-compatible local/internal
  endpoints can be evaluated with the same runner.
- Add a classic encoder-decoder MT baseline so LLM outputs can be compared against a conventional
  translation model.
- Add a dry-run or copy baseline to validate metric behavior on protected spans.

### Retrieval-Augmented Translation

- Add a retrieval layer that can provide top matching examples from prior translations, patents, or
  scientific abstracts.
- Inject retrieved examples into the translator prompt as few-shot demonstrations.
- Add a glossary source for approved chemical terms, hazard phrases, and domain-specific wording.
- Record retrieved example IDs and glossary terms in each output row for auditability.

### Branch-Aware Chemical Pipeline

- Segment each document into prose, chemical names, chemical notation, tables, and protected spans.
- Route prose through the MT or LLM translator.
- Preserve or canonicalize formal notation such as SMILES, InChI, formulas, and CAS numbers.
- Send chemical names through glossary-aware translation and optional OPSIN validation.
- Preserve table structure, section numbering, citations, formulas, units, and markup exactly.

### Structure-Aware Validation

- Add post-translation validators for protected spans, numeric values, formulas, and units.
- Add optional RDKit canonicalization for SMILES-like spans.
- Add optional OPSIN validation for systematic chemical names.
- Add an error report that lists failed spans and the reason each failed.
- Route failed high-risk spans back into the reviewer or mark them for human review.

### Reranking And Review

- Generate multiple candidate translations for difficult documents.
- Score candidates with a combined metric that includes protected-span preservation, glossary
  compliance, semantic quality, and reviewer approval.
- Add a reranker step that chooses the best candidate before final review.
- Store reviewer findings as structured categories: terminology, nomenclature, structure,
  stereochemistry, units, role/event, regulatory wording, omission, and addition.

### Fine-Tuning And Adaptation

- Build a small benchmark split before any fine-tuning work.
- Start with prompt and retrieval improvements before LoRA or PEFT adaptation.
- If fine-tuning is needed, train on in-domain patent, article, or SDS examples with protected-span
  policies already applied.
- Evaluate fine-tuned models against the same baseline sample across all target languages.

## Suggested Implementation Order

1. Extend `metrics.py` with protected-span, numeric/unit, and chemical-token preservation checks.
2. Add metric columns to JSONL/CSV comparison outputs.
3. Build a 50-100 document multilingual benchmark with manual review columns.
4. Add glossary injection to the OpenAI prompt path.
5. Add retrieval-augmented examples for patent and scientific prose.
6. Add optional structure validation with OPSIN, RDKit, and InChI.
7. Add candidate reranking for high-risk or low-confidence translations.
8. Compare one-shot provider-backed LLMs, retrieval-augmented variants, encoder-decoder baselines,
   and fine-tuned systems on the same benchmark.

## Open Decisions

- Decide whether chemistry parsers such as RDKit and OPSIN should be required dependencies or
  optional extras.
- Decide the first target document class: patents, research abstracts, or safety data sheets.
- Decide whether references will be manually translated, sourced from existing corpora, or omitted
  for reference-free evaluation.
- Decide the first glossary source: internal terms, WIPO Pearl, corpus-mined terms, or a small
  manually curated starter glossary.
