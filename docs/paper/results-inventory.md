# Benchmark Results Inventory

Inspected on 2026-11-03. Run reference: `e452b8821ea80ce896ae512a5728f0c2268e4e46`.

All 84 summaries are now downloaded locally. Generated tables, figures, coverage data, and interpretation notes are indexed in [the local analysis README](../../reports/evaluation-e452b88/analysis/README.md).

## Where the scores are

The supplied [Drive run folder](https://drive.google.com/drive/folders/1AdqKt8Qr8riI3J1fzpX1uCrZlpl2EnHZ) contains evaluation artifacts. The model-performance inputs are the per-run `summary.json` files, not the top-level logs or status files.

| Terminology view | Subset | Drive folder |
| --- | --- | --- |
| Original GLM | All terms | [all_terms](https://drive.google.com/drive/folders/1M8UdpWpL2heLEdcRXJ2AuK_0KmDu3J4g) |
| Original GLM | Externally enriched or verified | [externally_verified](https://drive.google.com/drive/folders/1K56pWHMIhwPyr88p0VN3VTf3xp-7N9uQ) |
| Original GLM | LLM-refined terms | [llm_enriched](https://drive.google.com/drive/folders/1cIatPRGnj77koWnMQodCUtDR8NFugj5o) |
| Luna | All terms | [luna_terms/all_terms](https://drive.google.com/drive/folders/1QoJzY--vDVxAooJrOk36sNbSGfusNj5i) |
| Luna | Externally enriched or verified | [luna_terms/externally_verified](https://drive.google.com/drive/folders/1EMQQUesGvayRFuvgB-4B35SOUiKlqaa3) |
| Luna | LLM-refined terms | [luna_terms/llm_enriched](https://drive.google.com/drive/folders/1VUmQ2XUizwagQyPI0rdyLp7tpCB2dMJ4) |

Within each subset, navigate to `<run>/summary.json`. Main runs have dataset subfolders named `google_patents`, `jrc_articles`, and `jrc_definitions`. The native sample instead uses `parallel_manifest`.

Directly inspected examples:

- [Gemma, original GLM, all terms: summary.json](https://drive.google.com/file/d/1qBwv78C6auTyVOWCfOVvzWqLGo4NevcR/view)
- [Gemma, original GLM, external terms: summary.json](https://drive.google.com/file/d/1AZQI6o2bvtLth6941SpGRfmiKEkHvxi1/view)
- [GPT-5.4-mini native sample, original GLM, all terms: summary.json](https://drive.google.com/file/d/1jBhhjIFS1Sh3XU-OzPEYvg4KLYT0-hUM/view)

These are machine-readable JSON downloads, available through `https://drive.google.com/uc?export=download&id=<file-id>`.

## Completion evidence

The [run status](https://drive.google.com/file/d/1-p_gbKIaByZYDW82PdW_kXqQystGS7vT/view) reports `stage = complete`, an empty top-level error list, and 84 summaries checked. The [delivery verification](https://drive.google.com/file/d/1DLXAgnuRi2HFrnQPEMGUzN9r_lL31wph/view), dated 2026-10-25, reports:

- Two terminology-source views, three subsets per view, and 14 execution snapshots per subset: 84 summaries in total.
- 753,225 available translation-row occurrences per view, reused across terminology subsets. Do not treat these as unique benchmark examples or independent experiments.
- All 14 non-paid metric families completed or not applicable.
- Shared general-metric values identical across terminology views/subsets.
- 348,732 strictly matched Luna row occurrences, substantially fewer than all stored translations.
- Paid judging held: `fsp_mqm` was **not run**.

These are producer-reported validation results, not an independent audit of every raw row. All 84 summaries have since been downloaded and checked for JSON structure, identity, size, and local checksum integrity. The analysis renderer additionally checks general-score equality across the six annotation tracks; raw per-translation records have not been independently audited.

## Runs and populations

The original GLM subset folders and Luna all-terms folder each list these ten current run identifiers:

`gemma_4_31b_it`, `gpt_6_luna_azure`, `granite_4_2_30b`, `muse_glimmer_30b`, `nemotron_3_5_lightning_30b_a3b`, `qwen38_27b_local`, `tiny_aya_earth`, `tiny_aya_fire`, `tiny_aya_global`, `tiny_aya_water`.

These are artifact identifiers, not independently verified checkpoint names or model-release claims. Resolve exact checkpoints and prompting provenance before choosing publication labels.

Keep the other four snapshots separate:

- `qwen38_27b_local__historical_untimed`
- `tiny_aya_earth__historical_untimed`
- `tiny_aya_global__historical_untimed`
- `google-patents-multidirectional-60-gpt-5_4-mini-all-metrics-verified__native_sample`

The native sample is not a full-benchmark competitor. Its inspected `de-en` slice has ten translations and unknown expected/missing counts (`null`), whereas the inspected Gemma patent `few_shot/de-en` slice has 933 expected and translated rows. Historical snapshots must not be averaged into their current counterparts.

## Summary schema

For a direction-level result, read:

```text
dataset_settings[dataset][setting].by_direction[direction]
    corpus_metrics
    mean_metrics
    counts
    metric_counts
    metric_applicable_counts
    metric_status
```

Observed dataset names: `google_patents`, `jrc_articles`, `jrc_definitions`; native sample: `parallel_manifest`. Observed setting labels include `few_shot` and native `openai`. Do not equate native adapter labels with matched prompting conditions.

Use `corpus_metrics` for corpus BLEU, chrF, and chrF++. `mean_metrics` contains means of segment scores, including another BLEU/chrF family: those are different statistics. For example, Gemma original-GLM/all-terms patent `few_shot/de-en` has corpus BLEU **57.81834142978617**, versus mean segment BLEU **56.82970025652675**, on 933 translated rows.

Other inspected mean-metric keys include BERTScore precision/recall/F1 (`bertscore`), BLEURT, COMET, COMETKiwi-QE, XCOMET-XL, terminology coverage and term BERTScore recall. Read applicability/status before interpreting absent scores; absence is not zero. Preserve raw score scales unless a table explicitly documents rescaling.

Top-level `metadata` includes requested metrics, metric specifications/status, errors, coverage warnings, model details, input provenance, evaluation identity, and raw artifact paths. Retain the source/evaluation signatures for reproducibility.

## Terminology semantics and comparability

The [run request](https://drive.google.com/file/d/1qYch6dDQvef2X9EBoHU_wMOw39Cdj5ql/view) explicitly defines the subsets:

| Artifact subset | Selector | Meaning |
| --- | --- | --- |
| `all_terms` | Empty list | All groups, including unrecognized groups; not the default verified-only selection. |
| `externally_verified` | `["verified"]` | Upstream verified-stage terms; not an expert-validated gold set and not every term with verifier evidence. |
| `llm_enriched` | `["refined"]` | Final LLM-refiner selections, not the raw `llm` extraction group. |

The two source views rescore unchanged translations. They are **annotation alternatives**, not two translation-model conditions. Luna accepts source identity, direction, and exact source/reference text matches; mismatches and eight text-only fallbacks are excluded, with no GLM fallback. Therefore, terminology tables need scored/applicable row counts and a common-row policy for comparisons. General scores must not be duplicated as independent observations just because the terminology view or subset changes.

In the inspected original-GLM Gemma patent `few_shot/de-en` result, terminology applicability is zero, even though all 933 general-metric rows are scored. A missing terminology score here must be shown as not applicable, not as 0% accuracy or an evaluator failure.

## Existing reports and table inputs

The delivery record points to a separate producer-side report tree:

```text
reports/evaluation-e452b88/INDEX.md
reports/evaluation-e452b88/original_glm/{all_terms,externally_verified,llm_enriched}.md
reports/evaluation-e452b88/luna/{all_terms,externally_verified,llm_enriched}.md
```

These report paths are not local workspace files, and their contents were not found or read in the supplied Drive root. The supplied folder is the artifact tree; its summaries remain the verified machine-readable starting point.

Recommended paper-table layout:

1. Translation quality: current model runs by dataset and matched prompting condition; corpus BLEU/chrF++ plus selected learned metrics. Show coverage, and define direction averaging explicitly.
2. Terminology: separate panels for original GLM versus Luna and all/external/refined subsets, including applicable/scored counts. Require matched rows before presenting annotation-source deltas.
3. Coverage appendix: language directions, expected/translated/missing rows, per-metric applicability/completion, historical runs, and the native sample.

Before ranking models, reconcile all summaries and model provenance; verify matching evaluation populations and any missing translations. Do not average corpus BLEU across directions and label it pooled corpus BLEU, or silently mix sentence-weighted and direction-macro averages. No final ranking or complete paper table has been produced by this inventory.