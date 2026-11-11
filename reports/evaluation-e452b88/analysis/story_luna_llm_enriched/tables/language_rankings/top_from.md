# Balanced From-Language Rankings: Best Model

Rows rank languages, NOT models. From means translating out of a language; To means translating into it. For each metric/dataset/prompt, average supported partner-direction scores equally within each model. Then use the highest model mean as that language's native metric value. Top does not choose a different model for each direction. The best model may differ between metrics and strata.

Rank languages descending within each metric with average ties. Balance metrics within semantic and lexical families; balance terminology metrics within each term group and the selected groups equally. The three family ranks have equal one-third weights. Final ties share the minimum rank (1, 1, 3).

Overall rankings require every dataset, both prompts and every active metric for each language. Within that overall eligible language cohort, rerank each stratum's metric values, then average dataset/prompt family ranks equally. Displayed overall native cells are equal-stratum means, not pooled medians or global maxima. Dataset-specific cohorts may differ. All-NA metrics are omitted, never scored zero. Coverage CSV records excluded languages and missing components.

Partner populations can differ between languages. These are descriptive supported benchmark rankings, not matched-partner comparisons, intrinsic language difficulty or statistical significance. Original model scorecards are unchanged.

[Language ranks](language_ranks.csv) | [Metric ranks](metric_rank_components.csv) | [Native scores and model values](native_metric_scores.csv) | [Coverage](coverage.csv)

## Overall: all datasets and both prompts | luna

| Rank | Language | Mixed Mean Rank | Semantic | Lexical | Terminology |
| --- | --- | --- | --- | --- | --- |
| 1 | French | 1.799 | 1.800 | 1.708 | 1.889 |
| 2 | Spanish | 2.014 | 2.333 | 2.042 | 1.667 |
| 3 | English | 2.657 | 2.167 | 2.917 | 2.889 |
| 4 | German | 3.530 | 3.700 | 3.333 | 3.556 |

Scorecard: [PNG](../../figures/languages/rankings/top/from/luna/language_rankings_overall.png) | [PDF](../../figures/languages/rankings/top/from/luna/language_rankings_overall.pdf)

Unranked due to incomplete metric/dataset coverage: Japanese, Portuguese, Russian, Chinese.

## Chemical Patents | Few Shot | luna

| Rank | Language | Mixed Mean Rank | Semantic | Lexical | Terminology |
| --- | --- | --- | --- | --- | --- |
| 1 | Spanish | 1.894 | 2.600 | 1.750 | 1.333 |
| 2 | French | 2.678 | 1.200 | 4.500 | 2.333 |
| 3 | German | 3.194 | 4.000 | 2.250 | 3.333 |
| 4 | English | 3.878 | 2.800 | 4.500 | 4.333 |
| 5 | Russian | 4.378 | 4.800 | 4.000 | 4.333 |
| 6 | Chinese | 4.978 | 5.600 | 4.000 | 5.333 |

Scorecard: [PNG](../../figures/languages/rankings/top/from/luna/language_rankings_google_patents_few_shot.png) | [PDF](../../figures/languages/rankings/top/from/luna/language_rankings_google_patents_few_shot.pdf)

Unranked due to incomplete metric/dataset coverage: Japanese.

## Chemical Patents | Zero Shot | luna

| Rank | Language | Mixed Mean Rank | Semantic | Lexical | Terminology |
| --- | --- | --- | --- | --- | --- |
| 1 | Spanish | 1.911 | 2.400 | 2.000 | 1.333 |
| 2 | French | 2.872 | 1.200 | 4.750 | 2.667 |
| 3 | German | 3.028 | 4.000 | 1.750 | 3.333 |
| 4 | English | 4.011 | 3.200 | 4.500 | 4.333 |
| 5 | Russian | 4.089 | 4.600 | 4.000 | 3.667 |
| 6 | Chinese | 5.089 | 5.600 | 4.000 | 5.667 |

Scorecard: [PNG](../../figures/languages/rankings/top/from/luna/language_rankings_google_patents_zero_shot.png) | [PDF](../../figures/languages/rankings/top/from/luna/language_rankings_google_patents_zero_shot.pdf)

Unranked due to incomplete metric/dataset coverage: Japanese.

## JRC Articles | Few Shot | luna

| Rank | Language | Mixed Mean Rank | Semantic | Lexical | Terminology |
| --- | --- | --- | --- | --- | --- |
| 1 | Portuguese | 1.867 | 2.600 | 1.000 | 2.000 |
| 2 | French | 2.356 | 2.400 | 2.000 | 2.667 |
| 3 | English | 2.761 | 2.200 | 3.750 | 2.333 |
| 4 | Spanish | 3.017 | 2.800 | 3.250 | 3.000 |
| 5 | German | 5.000 | 5.000 | 5.000 | 5.000 |

Scorecard: [PNG](../../figures/languages/rankings/top/from/luna/language_rankings_jrc_articles_few_shot.png) | [PDF](../../figures/languages/rankings/top/from/luna/language_rankings_jrc_articles_few_shot.pdf)

## JRC Articles | Zero Shot | luna

| Rank | Language | Mixed Mean Rank | Semantic | Lexical | Terminology |
| --- | --- | --- | --- | --- | --- |
| 1 | Portuguese | 1.956 | 2.200 | 1.000 | 2.667 |
| 2 | Spanish | 2.372 | 2.200 | 3.250 | 1.667 |
| 3 | French | 2.556 | 3.000 | 2.000 | 2.667 |
| 4 | English | 3.117 | 2.600 | 3.750 | 3.000 |
| 5 | German | 5.000 | 5.000 | 5.000 | 5.000 |

Scorecard: [PNG](../../figures/languages/rankings/top/from/luna/language_rankings_jrc_articles_zero_shot.png) | [PDF](../../figures/languages/rankings/top/from/luna/language_rankings_jrc_articles_zero_shot.pdf)

## JRC Definitions | Few Shot | luna

| Rank | Language | Mixed Mean Rank | Semantic | Lexical | Terminology |
| --- | --- | --- | --- | --- | --- |
| 1 | French | 1.822 | 2.800 | 1.000 | 1.667 |
| 2 | Portuguese | 1.972 | 2.000 | 2.250 | 1.667 |
| 3 | Spanish | 2.939 | 3.400 | 2.750 | 2.667 |
| 4 | English | 3.467 | 2.400 | 4.000 | 4.000 |
| 5 | German | 4.800 | 4.400 | 5.000 | 5.000 |

Scorecard: [PNG](../../figures/languages/rankings/top/from/luna/language_rankings_jrc_definitions_few_shot.png) | [PDF](../../figures/languages/rankings/top/from/luna/language_rankings_jrc_definitions_few_shot.pdf)

## JRC Definitions | Zero Shot | luna

| Rank | Language | Mixed Mean Rank | Semantic | Lexical | Terminology |
| --- | --- | --- | --- | --- | --- |
| 1 | French | 1.756 | 2.600 | 1.000 | 1.667 |
| 2 | Portuguese | 1.972 | 2.000 | 2.250 | 1.667 |
| 3 | Spanish | 3.006 | 3.600 | 2.750 | 2.667 |
| 4 | English | 3.400 | 2.200 | 4.000 | 4.000 |
| 5 | German | 4.867 | 4.600 | 5.000 | 5.000 |

Scorecard: [PNG](../../figures/languages/rankings/top/from/luna/language_rankings_jrc_definitions_zero_shot.png) | [PDF](../../figures/languages/rankings/top/from/luna/language_rankings_jrc_definitions_zero_shot.pdf)

