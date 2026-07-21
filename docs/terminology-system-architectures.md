# Terminology-Aware MT System Architectures

This note summarizes architecture ideas from the WMT terminology systems excerpt and translates them
into design options for this project. The goal is not to copy a participant system directly, but to
identify reusable patterns for chemistry and patent translation.

## Main Architecture Patterns

### Prompt-Only Terminology Guidance

Some systems use an LLM with terminology constraints written directly into the prompt. The simplest
version provides the source text plus a glossary or explanatory term instructions. The organizer
baseline used this style with GPT-4.1-nano and a long prompt containing the sentence or document and
the terminology dictionary.

Useful idea for us:

- Keep a lightweight fallback mode where extracted/refined terminology is injected into the
  translation prompt as explicit instructions.
- This is easy to run, but it can degrade when the glossary is large or noisy.

### LLM Pipeline With Preprocessing And Postprocessing

The Erlendur system used a modular LLM pipeline: extract key terms and idioms, match them against
bilingual dictionaries or user glossaries, translate, and then optionally postprocess the output.
This is close to our current direction.

Useful idea for us:

- Treat terminology as a separate pipeline stage rather than burying it inside translation.
- Keep preprocessing, terminology extraction, external lookup, reference matching, translation, and
  review as separable modules.
- Let users provide their own glossary in addition to generated terminology.

### Reference-First Terminology Generation

Several systems build terminology dictionaries from development data or aligned corpora. The WMT
consistency algorithm also relies on source-term selection, alignment to target terms, and
pseudo-reference choice from repeated candidate alignments.

Useful idea for us:

- For benchmark datasets, continue generating terminology ahead of evaluation.
- Use the reference translation as the strongest evidence for target terms.
- Use IATE/Wikidata as validation or variant evidence, not as the primary target term when a
  reference exists.

### NMT Plus LLM Postediting

DuTerm uses a two-stage approach: a terminology-aware NMT model generates a constrained translation,
then GPT-4o post-edits for fluency while preserving terms.

Useful idea for us:

- Generate a first draft with a cheaper or more controllable model.
- Run a stronger LLM post-editor whose explicit job is: improve fluency, do not violate accepted
  terminology.
- This can reduce cost while keeping terminology control.

### Terminology-Aware Fine-Tuning

Several systems fine-tune NMT or LLM models on terminology-rich data. DuTerm tags source and target
terms in synthetic parallel sentences. Laniqo uses code-switched prompts and LoRA fine-tuning.
Multitan and CurTermNLLB also use in-domain or glossary-enriched fine-tuning.

Useful idea for us:

- If we later train a smaller open model, generate synthetic chemistry/patent sentence pairs with
  tagged terms.
- Include both normal examples and terminology-constrained examples.
- Fine-tuning is heavier than prompt engineering, so it should come after we trust our terminology
  extraction pipeline.

### Preference Optimization With Terminology Rewards

Barcelona Supercomputing Center, CommandA-WMT, BIT, and Lingua Custodia use preference optimization
or reinforcement learning. The common idea is to reward outputs that preserve correct terminology,
sometimes combined with general translation quality rewards.

Useful idea for us:

- A future model-training path could combine a semantic quality reward with a terminology adherence
  reward.
- For now, the same idea can be used at inference time: generate multiple candidates, score each by
  general MT quality and terminology accuracy, then choose the best one.

### Multi-Candidate Decoding And Reranking

IRB-MT/MeGuMa and Laniqo generate multiple translation candidates or revisions and select using a
mix of general quality and terminology metrics. MeGuMa uses translation and revision phases, then
selects from all candidates using MetricX and terminology accuracy. Laniqo uses Pareto-style
ranking between overall quality and term accuracy.

Useful idea for us:

- Add a `generate -> revise -> rerank` strategy.
- Score candidates with COMET/chrF2++ for quality and terminology success rate for term adherence.
- Pick a candidate on a Pareto frontier instead of optimizing only one score.

### Code-Switched Term Injection

Laniqo replaces selected source terms with target-language terminology inside the source sentence or
prompt. This creates a code-switched source that nudges the model toward using the required target
terms.

Useful idea for us:

- For LLM prompting, test a mode that shows both the original source and a term-marked/code-switched
  source.
- This may help terms appear in the output, but it risks making the prompt less natural and should
  be tested carefully.

### Structured Local Terminology Context

STITCH focuses on avoiding overly large terminology context. It injects local terminology
information during generation and removes terminology that has already been integrated.

Useful idea for us:

- For long patent documents, do not pass the entire terminology dictionary into every prompt.
- Select local terms relevant to the current paragraph, claim, or segment.
- Track which terms have already been used so the prompt stays small and focused.

## Architecture Ideas For This Project

### Near-Term Architecture

The strongest next design for this repo is an inference-time pipeline:

1. Build or load dataset terminology from the manifest.
2. Select only terms relevant to the current source segment.
3. Translate with a terminology section in the prompt.
4. Review the translation for adequacy and terminology adherence.
5. If terminology is missing or wrong, revise once with explicit corrections.
6. Record the terminology section, review notes, and metrics in the report.

Why this fits us:

- It builds on the current dataset terminology module.
- It does not require model fine-tuning.
- It makes term behavior auditable in reports.

### Better Candidate Selection

Add multi-candidate generation and reranking:

1. Generate two or more translations with different prompts or temperatures.
2. Optionally generate a revision for each candidate.
3. Score each candidate with general metrics such as COMET or chrF2++.
4. Score each candidate with terminology success rate once implemented.
5. Select the best candidate using a weighted score or Pareto rule.

This mirrors MeGuMa and Laniqo, but can be implemented without training new models.

### Terminology-Aware Review Agent

The review agent should inspect:

- whether all required target terms appear;
- whether forbidden or wrong variants appear;
- whether preserved formulas, identifiers, and units remain intact;
- whether enforcing the term made the translation ungrammatical.

The output should be structured:

```json
{
  "approved": false,
  "missing_terms": ["target term"],
  "wrong_terms": [{"source_term": "...", "observed": "...", "expected": "..."}],
  "required_changes": ["Use ... for ..."],
  "rationale": "..."
}
```

### Local Context For Long Documents

For patent descriptions and claims, terminology should be local:

1. Split the document into paragraphs or claim units.
2. Retrieve terms whose source spans appear in that segment.
3. Include only those terms in the prompt.
4. Keep document-level memory for already established translations.

This avoids the common failure mode where a large glossary overwhelms the model.

### Synthetic Data Path

If we later train a small model:

1. Use the dataset terminology generator to create high-confidence term pairs.
2. Generate synthetic chemistry/patent sentence pairs containing those terms.
3. Tag source and target terms during training.
4. Fine-tune an open model with LoRA or a small NMT model.
5. Evaluate with chrF2++, COMET, terminology accuracy, and terminology consistency.

This follows the DuTerm, Laniqo, CurTermNLLB, and Multitan pattern.

## Recommended Roadmap

### Step 1: Implement Terminology Metrics

Implement terminology success rate first. For each manifest term, check whether at least one
accepted `target_terms` variant appears in the model output after normalization. This gives us a
direct measurement of whether terminology prompting is working.

### Step 2: Add Translation Reranking

Once terminology success rate exists, add a candidate selector:

```text
final_score = quality_score + lambda * terminology_score
```

Where `quality_score` can be COMET or another quality metric, and `terminology_score` is terminology
success rate. A Pareto-style selector can also be used when quality and terminology disagree.

### Step 3: Add Terminology-Aware Revision

If a candidate is fluent but misses terms, run a revision prompt that only fixes terminology and
forbids unnecessary rewriting.

### Step 4: Add Local Term Retrieval

For long documents, retrieve segment-level terminology instead of injecting every known term.

### Step 5: Consider Fine-Tuning

Only after the terminology extraction and metrics are reliable, consider synthetic data generation
and fine-tuning. Training before the terminology data is clean would amplify noise.

## Design Takeaways

- Prompt-only glossary injection is useful but not enough.
- The best systems combine terminology extraction, constrained prompting, revision, and candidate
  selection.
- External dictionaries are helpful, but noisy; reference-derived or context-derived candidates are
  stronger when available.
- Multi-metric selection is a practical way to balance fluency and terminology adherence.
- For long documents, local terminology context is safer than a giant global glossary.
- Fine-tuning and preference optimization are promising later, but inference-time reranking is the
  fastest next architecture improvement for this project.
