# Language Performance Violins

Three collections: pair violins contain all models for each directed pair; source-language violins pool outgoing model-direction scores; target-language violins pool incoming scores. Native COMET, chrF++ and variant-aware terminology coverage are kept in separate metric/term-group panels. Datasets, annotation views and zero-/few-shot are kept separate.

Every direction has every model and both prompts available. One point is one model-direction aggregate, NOT one translation. Pair groups have 7 points; source/target groups have 7 points per supported partner direction. Thus models and directions contribute equally; translation counts do not weight the density. chrF++ uses the direction corpus score, not a mean of segment chrF++ scores.

Native axes fit observed values with 5% padding; no normalization, zero-baseline requirement or outlier clipping. Model colors and circular dots are consistent across panels. Violin shape uses Scott-bandwidth KDE; black center line is the median. Constant/sparse groups show points and median only. These are descriptive distributions, not confidence intervals or evidence of statistical significance.

Partner-language and applicable-row sets can differ between languages, metrics and term groups. Missing groups are omitted, not zero-filled. Inspect the support CSV before comparing groups. Shared documents and models are not independent; small underlying translation samples and test/reference exposure can affect scores.

- [Plotted native points](../../tables/language_violin_points.csv)
- [Group counts, means, medians and direction/row support](../../tables/language_violin_support.csv)

## Figures

- violins/pair/shared_general/violin_pair_google_patents_zero_shot: [PNG](violins/pair/shared_general/violin_pair_google_patents_zero_shot.png) | [PDF](violins/pair/shared_general/violin_pair_google_patents_zero_shot.pdf)
- violins/from/shared_general/violin_from_google_patents_zero_shot: [PNG](violins/from/shared_general/violin_from_google_patents_zero_shot.png) | [PDF](violins/from/shared_general/violin_from_google_patents_zero_shot.pdf)
- violins/to/shared_general/violin_to_google_patents_zero_shot: [PNG](violins/to/shared_general/violin_to_google_patents_zero_shot.png) | [PDF](violins/to/shared_general/violin_to_google_patents_zero_shot.pdf)
- violins/pair/shared_general/violin_pair_google_patents_few_shot: [PNG](violins/pair/shared_general/violin_pair_google_patents_few_shot.png) | [PDF](violins/pair/shared_general/violin_pair_google_patents_few_shot.pdf)
- violins/from/shared_general/violin_from_google_patents_few_shot: [PNG](violins/from/shared_general/violin_from_google_patents_few_shot.png) | [PDF](violins/from/shared_general/violin_from_google_patents_few_shot.pdf)
- violins/to/shared_general/violin_to_google_patents_few_shot: [PNG](violins/to/shared_general/violin_to_google_patents_few_shot.png) | [PDF](violins/to/shared_general/violin_to_google_patents_few_shot.pdf)
- violins/pair/shared_general/violin_pair_jrc_articles_zero_shot: [PNG](violins/pair/shared_general/violin_pair_jrc_articles_zero_shot.png) | [PDF](violins/pair/shared_general/violin_pair_jrc_articles_zero_shot.pdf)
- violins/from/shared_general/violin_from_jrc_articles_zero_shot: [PNG](violins/from/shared_general/violin_from_jrc_articles_zero_shot.png) | [PDF](violins/from/shared_general/violin_from_jrc_articles_zero_shot.pdf)
- violins/to/shared_general/violin_to_jrc_articles_zero_shot: [PNG](violins/to/shared_general/violin_to_jrc_articles_zero_shot.png) | [PDF](violins/to/shared_general/violin_to_jrc_articles_zero_shot.pdf)
- violins/pair/shared_general/violin_pair_jrc_articles_few_shot: [PNG](violins/pair/shared_general/violin_pair_jrc_articles_few_shot.png) | [PDF](violins/pair/shared_general/violin_pair_jrc_articles_few_shot.pdf)
- violins/from/shared_general/violin_from_jrc_articles_few_shot: [PNG](violins/from/shared_general/violin_from_jrc_articles_few_shot.png) | [PDF](violins/from/shared_general/violin_from_jrc_articles_few_shot.pdf)
- violins/to/shared_general/violin_to_jrc_articles_few_shot: [PNG](violins/to/shared_general/violin_to_jrc_articles_few_shot.png) | [PDF](violins/to/shared_general/violin_to_jrc_articles_few_shot.pdf)
- violins/pair/shared_general/violin_pair_jrc_definitions_zero_shot: [PNG](violins/pair/shared_general/violin_pair_jrc_definitions_zero_shot.png) | [PDF](violins/pair/shared_general/violin_pair_jrc_definitions_zero_shot.pdf)
- violins/from/shared_general/violin_from_jrc_definitions_zero_shot: [PNG](violins/from/shared_general/violin_from_jrc_definitions_zero_shot.png) | [PDF](violins/from/shared_general/violin_from_jrc_definitions_zero_shot.pdf)
- violins/to/shared_general/violin_to_jrc_definitions_zero_shot: [PNG](violins/to/shared_general/violin_to_jrc_definitions_zero_shot.png) | [PDF](violins/to/shared_general/violin_to_jrc_definitions_zero_shot.pdf)
- violins/pair/shared_general/violin_pair_jrc_definitions_few_shot: [PNG](violins/pair/shared_general/violin_pair_jrc_definitions_few_shot.png) | [PDF](violins/pair/shared_general/violin_pair_jrc_definitions_few_shot.pdf)
- violins/from/shared_general/violin_from_jrc_definitions_few_shot: [PNG](violins/from/shared_general/violin_from_jrc_definitions_few_shot.png) | [PDF](violins/from/shared_general/violin_from_jrc_definitions_few_shot.pdf)
- violins/to/shared_general/violin_to_jrc_definitions_few_shot: [PNG](violins/to/shared_general/violin_to_jrc_definitions_few_shot.png) | [PDF](violins/to/shared_general/violin_to_jrc_definitions_few_shot.pdf)
- violins/pair/original_glm/violin_pair_google_patents_zero_shot: [PNG](violins/pair/original_glm/violin_pair_google_patents_zero_shot.png) | [PDF](violins/pair/original_glm/violin_pair_google_patents_zero_shot.pdf)
- violins/from/original_glm/violin_from_google_patents_zero_shot: [PNG](violins/from/original_glm/violin_from_google_patents_zero_shot.png) | [PDF](violins/from/original_glm/violin_from_google_patents_zero_shot.pdf)
- violins/to/original_glm/violin_to_google_patents_zero_shot: [PNG](violins/to/original_glm/violin_to_google_patents_zero_shot.png) | [PDF](violins/to/original_glm/violin_to_google_patents_zero_shot.pdf)
- violins/pair/original_glm/violin_pair_google_patents_few_shot: [PNG](violins/pair/original_glm/violin_pair_google_patents_few_shot.png) | [PDF](violins/pair/original_glm/violin_pair_google_patents_few_shot.pdf)
- violins/from/original_glm/violin_from_google_patents_few_shot: [PNG](violins/from/original_glm/violin_from_google_patents_few_shot.png) | [PDF](violins/from/original_glm/violin_from_google_patents_few_shot.pdf)
- violins/to/original_glm/violin_to_google_patents_few_shot: [PNG](violins/to/original_glm/violin_to_google_patents_few_shot.png) | [PDF](violins/to/original_glm/violin_to_google_patents_few_shot.pdf)
- violins/pair/original_glm/violin_pair_jrc_articles_zero_shot: [PNG](violins/pair/original_glm/violin_pair_jrc_articles_zero_shot.png) | [PDF](violins/pair/original_glm/violin_pair_jrc_articles_zero_shot.pdf)
- violins/from/original_glm/violin_from_jrc_articles_zero_shot: [PNG](violins/from/original_glm/violin_from_jrc_articles_zero_shot.png) | [PDF](violins/from/original_glm/violin_from_jrc_articles_zero_shot.pdf)
- violins/to/original_glm/violin_to_jrc_articles_zero_shot: [PNG](violins/to/original_glm/violin_to_jrc_articles_zero_shot.png) | [PDF](violins/to/original_glm/violin_to_jrc_articles_zero_shot.pdf)
- violins/pair/original_glm/violin_pair_jrc_articles_few_shot: [PNG](violins/pair/original_glm/violin_pair_jrc_articles_few_shot.png) | [PDF](violins/pair/original_glm/violin_pair_jrc_articles_few_shot.pdf)
- violins/from/original_glm/violin_from_jrc_articles_few_shot: [PNG](violins/from/original_glm/violin_from_jrc_articles_few_shot.png) | [PDF](violins/from/original_glm/violin_from_jrc_articles_few_shot.pdf)
- violins/to/original_glm/violin_to_jrc_articles_few_shot: [PNG](violins/to/original_glm/violin_to_jrc_articles_few_shot.png) | [PDF](violins/to/original_glm/violin_to_jrc_articles_few_shot.pdf)
- violins/pair/original_glm/violin_pair_jrc_definitions_zero_shot: [PNG](violins/pair/original_glm/violin_pair_jrc_definitions_zero_shot.png) | [PDF](violins/pair/original_glm/violin_pair_jrc_definitions_zero_shot.pdf)
- violins/from/original_glm/violin_from_jrc_definitions_zero_shot: [PNG](violins/from/original_glm/violin_from_jrc_definitions_zero_shot.png) | [PDF](violins/from/original_glm/violin_from_jrc_definitions_zero_shot.pdf)
- violins/to/original_glm/violin_to_jrc_definitions_zero_shot: [PNG](violins/to/original_glm/violin_to_jrc_definitions_zero_shot.png) | [PDF](violins/to/original_glm/violin_to_jrc_definitions_zero_shot.pdf)
- violins/pair/original_glm/violin_pair_jrc_definitions_few_shot: [PNG](violins/pair/original_glm/violin_pair_jrc_definitions_few_shot.png) | [PDF](violins/pair/original_glm/violin_pair_jrc_definitions_few_shot.pdf)
- violins/from/original_glm/violin_from_jrc_definitions_few_shot: [PNG](violins/from/original_glm/violin_from_jrc_definitions_few_shot.png) | [PDF](violins/from/original_glm/violin_from_jrc_definitions_few_shot.pdf)
- violins/to/original_glm/violin_to_jrc_definitions_few_shot: [PNG](violins/to/original_glm/violin_to_jrc_definitions_few_shot.png) | [PDF](violins/to/original_glm/violin_to_jrc_definitions_few_shot.pdf)
- violins/pair/luna/violin_pair_google_patents_zero_shot: [PNG](violins/pair/luna/violin_pair_google_patents_zero_shot.png) | [PDF](violins/pair/luna/violin_pair_google_patents_zero_shot.pdf)
- violins/from/luna/violin_from_google_patents_zero_shot: [PNG](violins/from/luna/violin_from_google_patents_zero_shot.png) | [PDF](violins/from/luna/violin_from_google_patents_zero_shot.pdf)
- violins/to/luna/violin_to_google_patents_zero_shot: [PNG](violins/to/luna/violin_to_google_patents_zero_shot.png) | [PDF](violins/to/luna/violin_to_google_patents_zero_shot.pdf)
- violins/pair/luna/violin_pair_google_patents_few_shot: [PNG](violins/pair/luna/violin_pair_google_patents_few_shot.png) | [PDF](violins/pair/luna/violin_pair_google_patents_few_shot.pdf)
- violins/from/luna/violin_from_google_patents_few_shot: [PNG](violins/from/luna/violin_from_google_patents_few_shot.png) | [PDF](violins/from/luna/violin_from_google_patents_few_shot.pdf)
- violins/to/luna/violin_to_google_patents_few_shot: [PNG](violins/to/luna/violin_to_google_patents_few_shot.png) | [PDF](violins/to/luna/violin_to_google_patents_few_shot.pdf)
- violins/pair/luna/violin_pair_jrc_articles_zero_shot: [PNG](violins/pair/luna/violin_pair_jrc_articles_zero_shot.png) | [PDF](violins/pair/luna/violin_pair_jrc_articles_zero_shot.pdf)
- violins/from/luna/violin_from_jrc_articles_zero_shot: [PNG](violins/from/luna/violin_from_jrc_articles_zero_shot.png) | [PDF](violins/from/luna/violin_from_jrc_articles_zero_shot.pdf)
- violins/to/luna/violin_to_jrc_articles_zero_shot: [PNG](violins/to/luna/violin_to_jrc_articles_zero_shot.png) | [PDF](violins/to/luna/violin_to_jrc_articles_zero_shot.pdf)
- violins/pair/luna/violin_pair_jrc_articles_few_shot: [PNG](violins/pair/luna/violin_pair_jrc_articles_few_shot.png) | [PDF](violins/pair/luna/violin_pair_jrc_articles_few_shot.pdf)
- violins/from/luna/violin_from_jrc_articles_few_shot: [PNG](violins/from/luna/violin_from_jrc_articles_few_shot.png) | [PDF](violins/from/luna/violin_from_jrc_articles_few_shot.pdf)
- violins/to/luna/violin_to_jrc_articles_few_shot: [PNG](violins/to/luna/violin_to_jrc_articles_few_shot.png) | [PDF](violins/to/luna/violin_to_jrc_articles_few_shot.pdf)
- violins/pair/luna/violin_pair_jrc_definitions_zero_shot: [PNG](violins/pair/luna/violin_pair_jrc_definitions_zero_shot.png) | [PDF](violins/pair/luna/violin_pair_jrc_definitions_zero_shot.pdf)
- violins/from/luna/violin_from_jrc_definitions_zero_shot: [PNG](violins/from/luna/violin_from_jrc_definitions_zero_shot.png) | [PDF](violins/from/luna/violin_from_jrc_definitions_zero_shot.pdf)
- violins/to/luna/violin_to_jrc_definitions_zero_shot: [PNG](violins/to/luna/violin_to_jrc_definitions_zero_shot.png) | [PDF](violins/to/luna/violin_to_jrc_definitions_zero_shot.pdf)
- violins/pair/luna/violin_pair_jrc_definitions_few_shot: [PNG](violins/pair/luna/violin_pair_jrc_definitions_few_shot.png) | [PDF](violins/pair/luna/violin_pair_jrc_definitions_few_shot.pdf)
- violins/from/luna/violin_from_jrc_definitions_few_shot: [PNG](violins/from/luna/violin_from_jrc_definitions_few_shot.png) | [PDF](violins/from/luna/violin_from_jrc_definitions_few_shot.pdf)
- violins/to/luna/violin_to_jrc_definitions_few_shot: [PNG](violins/to/luna/violin_to_jrc_definitions_few_shot.png) | [PDF](violins/to/luna/violin_to_jrc_definitions_few_shot.pdf)
