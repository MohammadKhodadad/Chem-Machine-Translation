# Benchmark Source Snapshots

This folder tracks only the preferred anchored JRC-Acquis source-pair snapshots used to
recreate benchmark datasets.

## JRC-Acquis / OPUS

The JRC-Acquis sources are source-pair snapshots built from public OPUS JRC-Acquis v3.0 Moses
aligned segment zips.

`scripts/create_jrc_acquis_source_pairs.py` downloads pair zips into the ignored
`data/opus_jrc_acquis` cache, then concatenates already-aligned segment pairs within document
boundaries and writes a portable source JSONL plus metadata. Use `--section-type article` or
`--section-type definition` to create separate benchmark sources for operative articles and
definition-heavy text.

The script supports two selection modes:

- `pairwise`: the original mode. Each ordered direction is selected independently.
- `anchored`: the preferred benchmark mode. The script first finds documents present across all
  selected language pairs, picks document anchors, then creates every ordered pair for each anchor.
  Reverse rows are exact source/target swaps from the same unordered pair chunk.

This path is preferred when we need `en`, `es`, `de`, `fr`, and `pt` legal benchmark data with
larger chunks and without relying on EuroVoc labels.

Retained sources:

- `jrc_acquis_anchored_articles_250_per_language_pair.jsonl`: 5,000 anchored article/provision
  chunks generated with strict text-quality filtering.
- `jrc_acquis_anchored_articles_250_per_language_pair_metadata.json`: anchored article source
  metadata.
- `jrc_acquis_anchored_definitions_250_per_language_pair.jsonl`: 5,000 anchored definition chunks
  generated with legacy markup cleanup and strict text-quality filtering.
- `jrc_acquis_anchored_definitions_250_per_language_pair_metadata.json`: anchored definition source
  metadata.
- Languages: `en`, `es`, `de`, `fr`, and `pt`.
- Directions: all 20 ordered pairs, 250 chunks per direction.

Create the preferred anchored article-focused source:

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

Create the preferred anchored definition-focused source:

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

`--limit 250` in anchored mode means 250 document anchors. Because each anchor expands to all 20
ordered directions, this produces 250 rows per direction and 5,000 rows total.

`--quality-mode strict` rejects residual markup, control characters, all-caps blocks, obvious
list-continuation starts, bare-date starts, and incomplete trailing fragments. It does not perform
language identification.

Both preferred anchored article and definition snapshots use `--clean-legacy-markup` plus
`--quality-mode strict`. The first step removes legacy OPUS/JRC inline tags before normalization;
the second step applies benchmark-quality noise and boundary filters.
