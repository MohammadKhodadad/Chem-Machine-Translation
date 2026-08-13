# JRC-Acquis Source-to-Dataset Pipeline

This diagram shows the current JRC-Acquis benchmark build flow, starting from the public OPUS/JRC
source files and ending with benchmark datasets that include terminology metadata.

```mermaid
flowchart TD
    A["OPUS JRC-Acquis v3.0<br/>Moses aligned segment ZIP files"] --> B["Source creation script<br/>scripts/create_jrc_acquis_source_pairs.py"]

    B --> C["Download language-pair ZIPs<br/>data/opus_jrc_acquis cache"]
    C --> D["Read aligned bilingual segments<br/>within OPUS document boundaries"]
    D --> E["Normalize text<br/>collapse whitespace and clean base text"]
    E --> F["Optional legacy markup cleanup<br/>--clean-legacy-markup"]
    F --> G["Section filtering<br/>--section-type article or definition"]
    G --> H["Strict quality gate<br/>--quality-mode strict"]

    H --> I{"Selection mode"}
    I -->|pairwise| J["Pairwise source rows<br/>each direction selected independently"]
    I -->|anchored| K["Anchored source rows<br/>pick common documents across all languages"]

    K --> L["Create unordered pair chunks<br/>one chunk per selected document and language pair"]
    L --> M["Emit both ordered directions<br/>reverse rows are exact source/target swaps"]

    J --> N["Benchmark source JSONL<br/>benchmark_sources/jrc_acquis_*"]
    M --> N
    N --> O["Source metadata JSON<br/>counts, languages, chunk settings, quality mode"]

    N --> P["Dataset creation script<br/>scripts/build_jrc_acquis_eval_subset.py"]
    P --> Q["Load source pairs<br/>filter languages and length limits"]
    Q --> R["Attach document metadata<br/>source, doc_id, section_type, anchor_id"]
    R --> S["Extract terminology<br/>legal/chemistry vocab sources when enabled"]
    S --> T["Write benchmark dataset<br/>benchmark_datasets/jrc_acquis_*"]
    T --> U["Evaluate translations<br/>BLEU, chrF2++, sequence similarity, terminology coverage"]
```

## Source Creation

The source creation step produces portable source-pair JSONL files in `benchmark_sources/`. For the
preferred anchored JRC sources, the script:

- downloads OPUS JRC-Acquis v3.0 Moses aligned ZIP files;
- reads already-aligned bilingual segments;
- keeps chunks inside document boundaries;
- applies `--clean-legacy-markup` to remove legacy OPUS/JRC inline tags;
- applies `--quality-mode strict` to reject residual markup, control characters, replacement
  characters, all-caps blocks, bad starts, and bad endings;
- selects either `article` or `definition` text with `--section-type`;
- in anchored mode, selects common documents across all languages and emits exact reverse pairs.

## Dataset Creation

The dataset creation step starts from the source JSONL, not from OPUS directly. It creates benchmark
datasets by:

- selecting the requested language pairs and row limit;
- preserving source-pair metadata such as `doc_id`, `anchor_id`, and `section_type`;
- extracting terminology when enabled;
- writing benchmark-ready examples and manifests under `benchmark_datasets/`.

This separation keeps raw source construction reproducible while allowing dataset-level terminology
and evaluation settings to evolve independently.
