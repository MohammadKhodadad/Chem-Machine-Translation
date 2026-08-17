# Terminology Candidate Extraction Methods

This document summarizes the two candidate-extraction directions currently being tested for
benchmark dataset creation. The goal is not final terminology validation. The goal is high-recall
target-side candidate spans that can later be verified by PubChem, ChEBI, ChEMBL, MeSH, NCI,
AGROVOC, IATE, Wikidata/Wikipedia, or other knowledge sources.

## Current Production Candidate Path: Stanza/UD

The current non-LLM candidate extractor is a Stanza-based Universal Dependencies pipeline.

It replaces the older non-LLM extractors:

- ChemDataExtractor.
- ChemBERTa/ChemU-style token classification.
- Hardcoded chemistry phrase regexes.

The LLM target-side extractor is still available and unchanged. When LLM extraction is enabled,
LLM candidates and Stanza/UD candidates are unioned, deduplicated, and then sent through the
external verification sources.

### How It Works

For each target/reference text:

1. Normalize the target language into a Stanza language code.
2. Run Stanza `tokenize,pos,lemma,depparse`.
3. Generate candidate spans from language-generic Universal Dependencies signals:
   - noun-headed dependency spans;
   - relaxed content n-grams up to six tokens;
   - proper-name sequences.
4. Keep exact text spans from the reference text.
5. Deduplicate candidates by normalized surface form.
6. Pass candidates to the external terminology verifiers when those verifiers are enabled.

This is intentionally not chemistry-specific. It does not depend on lists such as `acid`,
`chloride`, `polymer`, or language-specific chemical suffixes. That makes it more portable across
the supported languages, though it also means precision depends heavily on the later verifier step.

### Strengths

- Multilingual as long as a Stanza model exists for the language.
- Produces exact spans from the target/reference text.
- Can emit nested candidates such as:
  - `sodium chloride solution`;
  - `sodium chloride`;
  - `chloride solution`.
- Does not require an LLM.
- Does not require domain dictionaries for candidate generation.
- Works as a high-recall candidate generator before verification.

### Limitations

- It is syntax-driven, not termhood-trained.
- It can include generic noun phrases, especially in legal/JRC text.
- It needs Stanza models downloaded for each language.
- It does not know chemistry or legal terminology by itself.

### Smoke Test Result

Input:

```text
The formulation contains sodium chloride solution and thermal decomposition products.
```

The integrated extractor produced candidates including:

```text
thermal decomposition products | stanza_ud_dependency | 0.72
sodium chloride solution | stanza_ud_dependency | 0.72
thermal decomposition | stanza_ud_dependency | 0.72
sodium chloride | stanza_ud_ngram | 0.55
```

This is a good fit for our current goal: generate plausible spans first, then let external sources
decide which candidates should become benchmark terminology.

### Script

The standalone test script is:

```bash
uv run --no-sync python scripts/compare_deterministic_candidate_extractors.py \
  --text "The formulation contains sodium chloride solution and thermal decomposition products." \
  --language en \
  --max-candidates 15
```

It can also run on source JSONL rows:

```bash
uv run --no-sync python scripts/compare_deterministic_candidate_extractors.py \
  --source-jsonl benchmark_sources/jrc_acquis_anchored_articles_250_per_language_pair.jsonl \
  --limit 2 \
  --max-candidates 15
```

## Experimental Neural Candidate Path

The neural comparison script is separate from the production terminology pipeline. It is for
experimentation only.

The script is:

```text
scripts/compare_neural_candidate_extractors.py
```

It currently supports two optional methods:

- `xlmr-nobi`: XLM-R token classification with NOBI-style nested term labels, using a Hugging Face
  checkpoint when available.
- `gliner`: GLiNER-style open extraction when the `gliner` package and model are installed.

### XLM-R + NOBI

NOBI is more relevant than plain BIO for this project because it is designed to recover nested
terms that ordinary BIO labeling tends to collapse.

For example, BIO may return only:

```text
aqueous sodium chloride solution
```

NOBI-style extraction can better support nested outputs such as:

```text
aqueous sodium chloride solution
sodium chloride solution
sodium chloride
```

This matches our benchmark need: high recall and nested exact spans before verification.

Current status: the `xlmr-nobi` runner loads successfully after downloading the checkpoint weights.
It produced cleaner but lower-recall spans than Stanza/UD on the five-language JRC sample run.

Run command:

```bash
uv run --no-sync python scripts/compare_neural_candidate_extractors.py \
  --methods xlmr-nobi \
  --text "The formulation contains sodium chloride solution and thermal decomposition products." \
  --language en \
  --max-candidates 10
```

### GLiNER-Style Extraction

GLiNER-style models are attractive because they can extract spans for open labels such as:

```text
technical term
chemical term
legal term
scientific concept
```

However, this is closer to open NER than automatic term extraction. It may help recall, but it
should not be the core terminology extractor unless tests show strong term-boundary behavior.

Current status: the script supports GLiNER, but the package is not installed in the current
environment. The test reported:

```text
No module named 'gliner'
```

Run command:

```bash
uv run --no-sync python scripts/compare_neural_candidate_extractors.py \
  --methods gliner \
  --text "The formulation contains sodium chloride solution and thermal decomposition products." \
  --language en \
  --max-candidates 10
```

### Feature-Less Nested ATE and BINDER

Feature-less End-to-End Nested Term Extraction and BINDER are both strong architecture candidates
for this project because they operate over spans and can represent nested terms. They were checked as
possible additions, but they are not kept as runnable methods right now:

- Feature-less Nested ATE has public training code, but no ready multilingual checkpoint for direct
  testing on our samples.
- BINDER has public training/evaluation code. A biomedical-patent Hugging Face checkpoint was tested
  as a quick feasibility check, but it loaded with newly initialized weights in this environment and
  produced poor token-level outputs such as `contains` and `The`.

Both should be revisited only with a correctly trained/exported checkpoint, preferably trained from
verified or silver-labeled terminology spans.

## Recommendation

For now, use Stanza/UD as the default non-LLM candidate generator.

Use XLM-R/NOBI as a precision-oriented auxiliary extractor. The best next neural direction beyond
the current NOBI checkpoint is a trained multilingual span classifier:

```text
candidate spans -> multilingual encoder -> trained termhood score -> low threshold -> verifier
```

That architecture matches the benchmark requirement better than BIO tagging because it can keep
nested exact spans and optimize directly for candidate recall.
