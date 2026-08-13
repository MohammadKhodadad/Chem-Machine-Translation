# JRC-Acquis Benchmark Setup

## Summary

JRC-Acquis is the preferred legal benchmark source when we need larger multilingual chunks than the
older EuroLex/MultiEURLEX setup. The source-first flow is:

1. Build source-pair JSONL files from OPUS JRC-Acquis aligned segment files.
2. Review source quality directly from those JSONL files.
3. Build benchmark datasets from the selected source JSONL with legal terminology in the manifest.
4. Evaluate with `scripts/evaluate_parallel_manifest.py`.

For a Mermaid diagram of this flow, see `docs/jrc-acquis-pipeline.md`.

The current tracked JRC sources cover `en`, `es`, `de`, `fr`, and `pt`.

## Data Source

The source is OPUS JRC-Acquis v3.0 Moses format:

- public OPUS files under `https://object.pouta.csc.fi/OPUS-JRC-Acquis/v3.0/moses`;
- one zip per unordered language pair, such as `JRC-Acquis.de-en.txt.zip`;
- source and target text files with aligned lines;
- XML alignment metadata used to recover document IDs.

We do not scrape EUR-Lex. OPUS already provides aligned segment pairs, and the source builder
concatenates those aligned segments into larger document-bounded chunks.

## Source Files

Current tracked exploration sources:

- `benchmark_sources/jrc_acquis_anchored_articles_250_per_language_pair.jsonl`
  - preferred anchored article/provision-focused legal chunks;
  - 5,000 source-target pairs;
  - 20 ordered directions;
  - 250 chunks per direction;
  - 250 document anchors, each expanded to all ordered language pairs.
- `benchmark_sources/jrc_acquis_anchored_definitions_250_per_language_pair.jsonl`
  - preferred anchored definition-containing legal chunks;
  - 5,000 source-target pairs;
  - 20 ordered directions;
  - 250 chunks per direction;
  - 250 document anchors, each expanded to all ordered language pairs.
- `benchmark_sources/jrc_acquis_articles_250_per_language_pair.jsonl`
  - original pairwise article/provision-focused legal chunks.
- `benchmark_sources/jrc_acquis_definitions_250_per_language_pair.jsonl`
  - original pairwise definition-containing legal chunks.

Each row stores `source_text`, `target_text`, `doc_id`, `language_pair`, language codes,
approximate token counts, `segment_count`, and `section_type`.

## Source Builder

Use `scripts/create_jrc_acquis_source_pairs.py`.

Preferred anchored article source:

```powershell
uv run --no-sync python scripts/create_jrc_acquis_source_pairs.py `
  --output-jsonl benchmark_sources/jrc_acquis_anchored_articles_250_per_language_pair.jsonl `
  --metadata-output benchmark_sources/jrc_acquis_anchored_articles_250_per_language_pair_metadata.json `
  --cache-dir data/opus_jrc_acquis `
  --language en `
  --language es `
  --language de `
  --language fr `
  --language pt `
  --limit 250 `
  --min-chunk-tokens 250 `
  --target-chunk-tokens 450 `
  --max-chunk-tokens 700 `
  --section-type article `
  --selection-mode anchored `
  --anchor-language en `
  --anchor-search-multiplier 20 `
  --clean-legacy-markup `
  --quality-mode strict
```

Preferred anchored definition source:

```powershell
uv run --no-sync python scripts/create_jrc_acquis_source_pairs.py `
  --output-jsonl benchmark_sources/jrc_acquis_anchored_definitions_250_per_language_pair.jsonl `
  --metadata-output benchmark_sources/jrc_acquis_anchored_definitions_250_per_language_pair_metadata.json `
  --cache-dir data/opus_jrc_acquis `
  --language en `
  --language es `
  --language de `
  --language fr `
  --language pt `
  --limit 250 `
  --min-chunk-tokens 250 `
  --target-chunk-tokens 450 `
  --max-chunk-tokens 700 `
  --section-type definition `
  --selection-mode anchored `
  --anchor-language en `
  --anchor-search-multiplier 20 `
  --clean-legacy-markup `
  --quality-mode strict
```

`--selection-mode pairwise` keeps the original behavior where each ordered direction is selected
independently. `--selection-mode anchored` first finds documents present across all selected
language pairs, then expands each selected document anchor to all ordered directions. For five
languages, `--limit 250` means 250 anchors and 5,000 source-target rows.

`--section-type all` can be used for a generic unfiltered source.

Use `--quality-mode strict` for benchmark-ready sources. It rejects residual markup, control
characters, all-caps blocks, obvious list-continuation starts, bare-date starts, and incomplete
trailing fragments. It does not perform language identification.

Both preferred anchored article and definition snapshots are regenerated with the same preprocessing
gate:

- `--clean-legacy-markup` removes legacy OPUS/JRC inline tags before text normalization.
- `--quality-mode strict` applies the benchmark-quality noise and boundary filters.
- Language coverage is still inherited from the OPUS bilingual file structure; no full language
  identifier is run in strict mode.

## What Gets Selected

The builder reads aligned OPUS segments in file order, filters unusable segment pairs, and joins
adjacent pairs from the same document. It does not cross document boundaries.

In anchored mode, document selection is doc-first:

1. Find document IDs that appear across all selected unordered language pairs.
2. Keep a common document pool ordered by the anchor language.
3. Build one chunk per selected document for each unordered language pair.
4. Emit both directions for that pair by swapping source and target.

This guarantees that every selected anchor has all 20 ordered directions and that each reverse row
is an exact source/target swap.

Current chunk settings:

- minimum chunk size: 250 source tokens;
- target chunk size: 450 source tokens;
- maximum chunk size: 700 source tokens;
- minimum segment size: 3 tokens per side;
- maximum segment size: 180 tokens per side;
- maximum source/target token ratio: 3.0;
- maximum chunks per document per ordered direction: 1.

The article filter selects chunks with article markers near the start, such as `Article 11`,
`Artikel 11`, `Artículo 11`, or `Artigo 11`. The definition filter selects chunks containing
explicit legal-definition wording such as “For the purposes of this Convention” or “shall mean”.

## Quality Check

The automated quality check on both anchored 250-per-pair sources found:

- no empty source/target rows;
- no corrupt replacement characters;
- no identical source/target pairs;
- no source/target token ratio above 2.0;
- no residual HTML/XML-like tags;
- no bad-start or bad-end rows under the strict boundary heuristic;
- no high-uppercase source rows;
- exactly 250 rows for every ordered direction;
- exactly 250 anchors per source;
- no incomplete anchors;
- no reverse-pair mismatches.

Concrete anchored audit results:

- `jrc_acquis_anchored_articles_250_per_language_pair.jsonl`
  - rows: 5,000;
  - directions: 20, with 250 rows each;
  - anchors: 250;
  - mean source tokens: 418.6.
- `jrc_acquis_anchored_definitions_250_per_language_pair.jsonl`
  - rows: 5,000;
  - directions: 20, with 250 rows each;
  - anchors: 250;
  - mean source tokens: 487.9.

Manual samples looked aligned and suitable for legal translation evaluation. Article chunks are the
stronger source for immediate benchmarking because they mostly contain operative legal provisions.
Definition chunks are usable, but they should be treated as definition-containing rather than
definition-only: some chunks include preamble or surrounding legal context before the definition
phrase appears. Strict mode removes obvious boundary and formatting problems, but manual spot
checks are still useful before publishing final benchmark results.

## Benchmark Dataset Builder

Use `scripts/build_jrc_acquis_eval_subset.py` to turn either source JSONL into a benchmark dataset:

```powershell
uv run --no-sync python scripts/build_jrc_acquis_eval_subset.py `
  --source-pairs-jsonl benchmark_sources/jrc_acquis_anchored_articles_250_per_language_pair.jsonl `
  --output-dir benchmark_datasets/jrc_acquis_anchored_articles_250_per_pair `
  --language en `
  --language es `
  --language de `
  --language fr `
  --language pt `
  --limit 250 `
  --extract-legal-terms `
  --legal-terminology-model gpt-5.4-mini `
  --iate-terminology `
  --wikipedia-terminology `
  --unterm-terminology `
  --legal-terminology-workers 4 `
  --legal-terminology-cache data/jrc_acquis_legal_terminology_cache.jsonl
```

The benchmark builder writes direction folders with `source.csv`, `target.csv`, and manifest files.
Legal terminology is generated from the target/reference side and can be verified with IATE,
Wikipedia/Wikidata, and UNTERM evidence.

Evaluate a direction with the legal prompt and verified manifest terminology:

```powershell
uv run --no-sync python scripts/evaluate_parallel_manifest.py `
  --dataset-dir benchmark_datasets/jrc_acquis_anchored_articles_250_per_pair/en-es `
  --translator one-shot `
  --provider openai `
  --model gpt-5.4-mini `
  --translation-domain legal `
  --use-manifest-terminology `
  --terminology-term-group verified `
  --metric sequence_similarity `
  --metric bleu `
  --metric chrf2++ `
  --metric target_term_coverage `
  --output reports/jrc-acquis-articles-en-es.jsonl
```

## Known Caveats

- JRC-Acquis is legal text, not patent text. It has articles, recitals, annexes, protocols, and
  final provisions, but no patent-style claims or abstracts.
- OPUS alignment is generally good, but title and preamble boundaries can still be awkward.
- The current definition source contains definition phrases, but chunks are not trimmed to begin at
  the definition marker.
- These source files are for source-quality exploration first. Build smaller benchmark datasets from
  them before running expensive terminology generation or model evaluation.
