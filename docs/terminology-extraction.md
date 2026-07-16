# Terminology Extraction

This project uses dataset-level terminology extraction to create source-to-target terminology
mappings before translation or evaluation. The mappings are stored in benchmark manifests so
translation prompts and future terminology metrics can use the same auditable data.

## Why This Is Separate

Runtime terminology prompting and dataset terminology generation solve different problems.

Runtime prompting helps a translator preserve approved terms during a translation run. Dataset
terminology generation prepares benchmark artifacts ahead of time, using the reference translation
when it exists. That makes terminology metrics more stable because they compare against documented
source and target term pairs instead of extracting terms during evaluation.

The dataset terminology code lives in `src/chem_machine_translation/data/terminology.py`.

## Current Flow

The current flow is reference-first:

1. Extract source terms with an LLM.

   The first LLM sees only the source text and extracts strict technical terms. It should not
   translate terms or infer target-language mappings. The prompt is intentionally strict: it favors
   chemistry, materials, process, method, unit, hazard, and patent-critical phrases, while rejecting
   common standalone words such as `method`, `system`, `solution`, or `temperature`.

2. Extract reference candidates with an LLM.

   If a target reference is available, a second LLM sees the source text, target reference, and
   extracted source terms. It finds exact target-language spans from the reference. These are stored
   as `reference_candidates`.

   Reference candidates are the main evidence for benchmark terminology because they come directly
   from the human/reference target text.

3. Look up external candidates.

   IATE and Wikidata are used as secondary sources. Their outputs are stored as
   `external_candidates`, not treated as final target terms by default.

   IATE is queried first because it is a terminology database. Wikidata is a fallback when IATE does
   not return a candidate. These sources are useful for validation, canonical forms, and alternate
   variants, but they can be noisy.

4. Refine and select final terms with an LLM.

   The refiner compares the reference candidates, external candidates, source text, and reference
   context. It decides which target terms should be kept for the manifest. Valid decisions are:

   - `keep_reference`: use the reference candidate.
   - `keep_external`: use an external candidate when the reference candidate is absent or noisy.
   - `keep_both`: keep both reference and external variants.
   - `update`: use a corrected contextual form.
   - `preserve`: copy the source term unchanged.
   - `drop`: remove the term as generic, unrelated, or too uncertain.

5. Apply confidence gating.

   Terms below the configured confidence threshold are removed unless they are explicitly allowed as
   lower-confidence LLM-only guidance. The builder scripts expose this through
   `--terminology-confidence-threshold` and `--terminology-max-terms`.

## Manifest Fields

Each manifest row can include a `terminology` list. Each term has this shape:

```json
{
  "source_term": "gastrointestinal tract",
  "target_terms": ["tube digestif", "tractus gastro-intestinal"],
  "reference_candidates": ["tube digestif"],
  "external_candidates": {
    "iate": ["tractus gastro-intestinal"]
  },
  "category": "other",
  "source": "reference+iate+refined",
  "confidence": 0.9,
  "decision": "keep_both",
  "reason": "Reference uses 'tube digestif'; IATE provides a valid variant."
}
```

Important fields:

- `source_term`: exact source-language span extracted from the source text.
- `reference_candidates`: target-language spans found in the reference translation.
- `external_candidates`: IATE/Wikidata candidates used for validation or variants.
- `target_terms`: final accepted target terms used by downstream consumers.
- `decision`: how the final target terms were selected.
- `confidence`: refiner confidence after context and candidate comparison.
- `reason`: short audit explanation for the decision.

The legacy `candidates` field is still written for compatibility and mirrors
`external_candidates`.

## Preserve Logic

`preserve` is intentionally narrow. It should only apply to compact formulas, symbols, identifiers,
and numeric/unit expressions, for example:

- `Li2O`
- `SEQ ID NO: 10`
- `700 ppm or less`
- `55 to 65 °C`

Broad phrases should not be preserved only because they contain an abbreviation or were labeled as
identifiers. For example, `quantitative trait locus (QTL)` should usually become a reference-backed
mapping such as `locus de caractère quantitatif (QTL)`.

## Role Of IATE And Wikidata

When a reference translation exists, IATE and Wikidata should not be the primary source of the
target term. The reference is stronger evidence because it is the benchmark target text.

External lookup is still valuable because it can:

- confirm that the reference candidate is a standard term;
- provide canonical variants without articles or inflection;
- add accepted alternate terminology;
- expose noisy candidates that the refiner can reject.

For example, `gastrointestinal tract` may map to `tube digestif` in the reference while IATE returns
`tractus gastro-intestinal`. Both can be useful variants, so the refiner can choose `keep_both`.

External lookup can also be wrong. In one smoke run, IATE returned an unrelated candidate for `cow`.
The refiner correctly kept the reference candidate and ignored the noisy external candidate.

## Builder Usage

Terminology is generated when building benchmark subsets:

```powershell
uv run --no-sync python scripts/build_google_patents_eval_subset.py `
  --source-dir data/preprocessed `
  --output-dir examples/google_patents_eval_subset_50 `
  --limit 50 `
  --language fr `
  --extract-terminology `
  --iate-terminology `
  --wikidata-terminology `
  --refine-terminology `
  --terminology-model gpt-5.4-mini `
  --terminology-workers 4
```

The EPO builder exposes the same terminology flags.

## Current Quality Notes

The reference-first flow is much stronger than using IATE/Wikidata as direct target-term sources.
Most good pairs now come from the reference, while external sources add variants and validation.

The main remaining quality issue is extraction strictness. Some extracted terms can still be too
broad, too generic, or too phrase-like for terminology metrics. The next improvement should be a
post-refinement filter that drops generic biological/common nouns and long non-term fragments unless
they are clearly chemistry-, process-, or patent-critical.
