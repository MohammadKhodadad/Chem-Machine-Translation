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

## Experimental Neural/Embedding Candidate Path

The neural comparison script is separate from the production terminology pipeline. It is for
experimentation only.

The script is:

```text
scripts/compare_neural_candidate_extractors.py
```

It currently supports three optional methods:

- `xlmr-nobi`: XLM-R token classification with NOBI-style nested term labels, using a Hugging Face
  checkpoint when available.
- `xlmr-span-embedding`: enumerates exact spans and ranks them with multilingual Transformer
  embeddings.
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

Current status: the script includes an `xlmr-nobi` runner, but the tested Hugging Face checkpoint
did not finish downloading/loading in the current Windows environment during the timed test run.
So we do not yet have a quality result for this method.

Run command:

```bash
uv run --no-sync python scripts/compare_neural_candidate_extractors.py \
  --methods xlmr-nobi \
  --text "The formulation contains sodium chloride solution and thermal decomposition products." \
  --language en \
  --max-candidates 10
```

### XLM-R Span Embedding Baseline

This method is not a trained ATE model. It is a baseline to test whether multilingual embeddings
alone can rank candidate spans.

It works like this:

1. Enumerate all exact word spans up to a configurable length.
2. Encode the full text with a multilingual Transformer.
3. Pool contextual embeddings for each span.
4. Score each span against the sentence/document embedding.
5. Return the top ranked spans.

This is useful as an experiment, but it is not enough as a serious candidate extractor.

Smoke test result:

```text
contains sodium chloride solution and thermal
formulation contains sodium chloride solution and
The formulation contains sodium chloride solution
chloride solution and thermal decomposition products
```

This result is too broad and fragment-like. It confirms that plain embedding similarity is not the
right scoring objective for terminology extraction. Embeddings can represent text meaning, but they
do not by themselves learn term boundaries.

Run command:

```bash
uv run --no-sync python scripts/compare_neural_candidate_extractors.py \
  --methods xlmr-span-embedding \
  --span-model sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2 \
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

## Recommendation

For now, use Stanza/UD as the default non-LLM candidate generator.

Do not use plain embedding-span ranking as the main extractor. The first tests show that it
captures semantic centrality, not terminology boundaries.

The best next neural direction is not unsupervised embeddings. It is a trained multilingual span
classifier or a working XLM-R/NOBI checkpoint:

```text
candidate spans -> multilingual encoder -> trained termhood score -> low threshold -> verifier
```

That architecture matches the benchmark requirement better than BIO tagging and much better than
plain embedding similarity, because it can keep nested exact spans and optimize directly for
candidate recall.
