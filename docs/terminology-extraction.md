# Terminology Extraction

This project uses a target-only dataset terminology pipeline for benchmark artifacts. The goal is to
extract target-side chemistry terminology from the human/reference translation, store it in the
manifest, and let terminology metrics consume those approved target terms directly.

The dataset terminology code lives in `src/chem_machine_translation/data/terminology.py`.

## Why This Is Separate

Runtime terminology prompting and dataset terminology generation solve different problems.

Runtime prompting helps a translator preserve approved terms during a translation run. Dataset
terminology generation prepares benchmark artifacts ahead of time, using the reference translation
when it exists. That makes the benchmark terminology auditable and avoids extracting terms during
evaluation.

## Current Flow

The current dataset flow is target-side. The LLM, when enabled, is only a candidate extractor:

1. Extract target-side candidates from the reference translation.

   With `--extract-terminology`, the builder asks an LLM to return strict technical spans from the
   target/reference text. The LLM must not translate or normalize terms. It returns candidate spans
   only.

2. Verify LLM spans against the target text.

   Every LLM candidate must appear in the target/reference text. Hallucinated or rewritten terms are
   dropped before any database lookup happens.

3. Add no-LLM fallback candidates.

   The generator can also use optional chemistry NER adapters:

   - ChemDataExtractor, when installed.
   - A ChEMU/BioBERT-style Hugging Face token-classification pipeline, when `transformers` and the
     model are available.

   If those optional packages are not installed, the generator falls back to lightweight chemistry
   regexes for formulas, compact units, identifiers, and common chemistry phrase endings.

4. Deduplicate and rank terms.

   Terms are normalized with case-folding and whitespace cleanup. Higher-confidence model outputs
   outrank regex fallback terms.

5. Check external terminology sources.

   External lookup evidence is stored in `external_candidates`:

   - PubChem confirms compound names and returns synonyms.
   - IATE checks terminology records in the target language.
   - Wikipedia/Wikidata checks target-language encyclopedia labels.

   These sources are evidence only. The final `target_terms` stay anchored to spans extracted from
   the reference translation.

6. Write manifest terminology.

   The manifest row stores target-side terms in `target_terms` and `reference_candidates`. Because
   this target-only process does not align terms back to source spans, `source_term` is intentionally
   empty.

## Candidate Groups

Every manifest term has a coarse `term_group` and a detailed `source`.

- `llm`: the term was proposed by the target-only LLM and verified to appear in the reference text.
  The detailed source is usually `llm_target`.
- `algorithmic`: the term came from regex, ChemDataExtractor, ChEMU/BioBERT, or another deterministic
  or model-based extractor that is not an external terminology database.
- `verified`: the candidate has evidence from PubChem, IATE, or Wikipedia/Wikidata. This is the main
  trusted group for benchmark terminology.

The `source` field keeps detailed provenance such as `llm_target+wikipedia`,
`llm_target+iate`, `regex+pubchem`, or `chemdataextractor`. The `verified_by` field stores only the
external evidence sources, for example `["wikipedia"]` or `["pubchem", "iate"]`.

Target terminology metrics use `verified` terms by default. To include lower-trust groups during an
evaluation run, pass `--terminology-term-group llm`, `--terminology-term-group algorithmic`, and/or
`--terminology-term-group verified` to the benchmark evaluation script.

## Manifest Fields

Each manifest row can include a `terminology` list. Each term has this shape:

```json
{
  "source_term": "",
  "target_terms": ["chlorure de sodium"],
  "reference_candidates": ["chlorure de sodium"],
  "external_candidates": {
    "pubchem": ["sodium chloride", "chlorure de sodium"]
  },
  "category": "chemical",
  "source": "llm_target+pubchem",
  "term_group": "verified",
  "verified_by": ["pubchem"],
  "confidence": 0.96,
  "decision": "keep_reference",
  "reason": "LLM-proposed exact target span verified in reference text."
}
```

Important fields:

- `source_term`: empty for the current target-only benchmark pipeline.
- `reference_candidates`: target-language spans extracted from the reference translation.
- `external_candidates`: PubChem, IATE, and Wikipedia/Wikidata evidence.
- `target_terms`: final accepted target terms used by downstream metrics.
- `term_group`: coarse grouping: `llm`, `algorithmic`, or `verified`.
- `source`: detailed provenance, such as `llm_target+wikipedia`.
- `verified_by`: external sources that validated the term.
- `decision`: usually `keep_reference`; `preserve` is used for compact formulas and identifiers.
- `confidence`: extractor confidence, increased slightly when external evidence is found.

The legacy `candidates` field is still written for compatibility and mirrors
`external_candidates`.

## Preserve Logic

`preserve` is intentionally narrow. It should only apply to compact formulas, symbols, identifiers,
and numeric/unit expressions, for example:

- `Li2O`
- `SEQ ID NO: 10`
- `700 ppm`
- `55 to 65 °C`

Broad phrases should not be preserved only because they contain an abbreviation or were labeled as
identifiers.

## Benchmark Usage

The current benchmark dataset lives in:

`benchmark_datasets/google_patents_eval_subset_60_multidirectional`

It already contains target-side terminology generated with the flow above. See
`benchmark_datasets/README.md` for commands that run the benchmark with `verified`, `llm`,
`algorithmic`, or combined terminology groups.

`OPENAI_API_KEY` is required only when generating new LLM target candidates or running OpenAI
translation strategies. Metrics over existing manifest terminology can run without generating new
terminology.

## Current Quality Notes

This is simpler than the previous LLM-based source/reference/refinement flow because the LLM no
longer generates source terms, target mappings, or refinement decisions. The main tradeoff is that
source-to-target term alignment is no longer generated. Use `target_term_coverage` for terminology
benchmark scoring because it only needs approved target terms. `terminology_success_rate` is
source-conditioned and is less suitable when `source_term` is empty.

The regex fallback is intentionally conservative. For higher-quality benchmark terminology, install
or configure the chemistry NER models and keep PubChem/IATE/Wikipedia checks enabled.
