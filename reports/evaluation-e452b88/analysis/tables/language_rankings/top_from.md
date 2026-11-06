# Balanced From-Language Rankings: Best Model

Rows rank languages, NOT models. From means translating out of a language; To means translating into it. For each metric/dataset/prompt, average supported partner-direction scores equally within each model. Then use the highest model mean as that language's native metric value. Top does not choose a different model for each direction. The best model may differ between metrics and strata.

Rank languages descending within each metric with average ties. Balance metrics within semantic and lexical families; balance terminology metrics within each term group and the three groups equally. The three family ranks have equal one-third weights. Final ties share the minimum rank (1, 1, 3).

Overall rankings require every dataset, both prompts and every active metric for each language. Within that overall eligible language cohort, rerank each stratum's metric values, then average dataset/prompt family ranks equally. Displayed overall native cells are equal-stratum means, not pooled medians or global maxima. Dataset-specific cohorts may differ. All-NA metrics are omitted, never scored zero. Coverage CSV records excluded languages and missing components.

Partner populations can differ between languages. These are descriptive supported benchmark rankings, not matched-partner comparisons, intrinsic language difficulty or statistical significance. Original model scorecards are unchanged.

[Language ranks](language_ranks.csv) | [Metric ranks](metric_rank_components.csv) | [Native scores and model values](native_metric_scores.csv) | [Coverage](coverage.csv)

## Overall: all datasets and both prompts | luna

| Rank | Language | Mixed Mean Rank | Semantic | Lexical | Terminology |
| --- | --- | --- | --- | --- | --- |
| 1 | French | 1.818 | 1.800 | 1.708 | 1.944 |
| 2 | Spanish | 2.144 | 2.333 | 2.042 | 2.056 |
| 3 | English | 2.602 | 2.167 | 2.917 | 2.722 |
| 4 | German | 3.437 | 3.700 | 3.333 | 3.278 |

Scorecard: [PNG](../../figures/languages/rankings/top/from/luna/language_rankings_overall.png) | [PDF](../../figures/languages/rankings/top/from/luna/language_rankings_overall.pdf)

Unranked due to incomplete metric/dataset coverage: Japanese, Portuguese, Russian, Chinese.

## Overall: all datasets and both prompts | original_glm

| Rank | Language | Mixed Mean Rank | Semantic | Lexical | Terminology |
| --- | --- | --- | --- | --- | --- |
| 1 | French | 1.449 | 1.467 | 1.417 | 1.463 |
| 2 | English | 1.934 | 1.700 | 2.083 | 2.019 |
| 3 | German | 2.617 | 2.833 | 2.500 | 2.519 |

Scorecard: [PNG](../../figures/languages/rankings/top/from/original_glm/language_rankings_overall.png) | [PDF](../../figures/languages/rankings/top/from/original_glm/language_rankings_overall.pdf)

Unranked due to incomplete metric/dataset coverage: Spanish, Japanese, Portuguese, Russian, Chinese.

## Chemical Patents | Few Shot | luna

| Rank | Language | Mixed Mean Rank | Semantic | Lexical | Terminology |
| --- | --- | --- | --- | --- | --- |
| 1 | Spanish | 2.154 | 2.600 | 1.750 | 2.111 |
| 2 | French | 2.604 | 1.200 | 4.500 | 2.111 |
| 3 | German | 3.120 | 4.000 | 2.250 | 3.111 |
| 4 | English | 3.693 | 2.800 | 4.500 | 3.778 |
| 5 | Russian | 4.526 | 4.800 | 4.000 | 4.778 |
| 6 | Chinese | 4.904 | 5.600 | 4.000 | 5.111 |

Scorecard: [PNG](../../figures/languages/rankings/top/from/luna/language_rankings_google_patents_few_shot.png) | [PDF](../../figures/languages/rankings/top/from/luna/language_rankings_google_patents_few_shot.pdf)

Unranked due to incomplete metric/dataset coverage: Japanese.

## Chemical Patents | Zero Shot | luna

| Rank | Language | Mixed Mean Rank | Semantic | Lexical | Terminology |
| --- | --- | --- | --- | --- | --- |
| 1 | Spanish | 2.170 | 2.400 | 2.000 | 2.111 |
| 2 | French | 2.724 | 1.200 | 4.750 | 2.222 |
| 3 | German | 2.954 | 4.000 | 1.750 | 3.111 |
| 4 | English | 3.826 | 3.200 | 4.500 | 3.778 |
| 5 | Russian | 4.311 | 4.600 | 4.000 | 4.333 |
| 6 | Chinese | 5.015 | 5.600 | 4.000 | 5.444 |

Scorecard: [PNG](../../figures/languages/rankings/top/from/luna/language_rankings_google_patents_zero_shot.png) | [PDF](../../figures/languages/rankings/top/from/luna/language_rankings_google_patents_zero_shot.pdf)

Unranked due to incomplete metric/dataset coverage: Japanese.

## JRC Articles | Few Shot | luna

| Rank | Language | Mixed Mean Rank | Semantic | Lexical | Terminology |
| --- | --- | --- | --- | --- | --- |
| 1 | Portuguese | 1.904 | 2.600 | 1.000 | 2.111 |
| 2 | English | 2.576 | 2.200 | 3.750 | 1.778 |
| 3 | French | 2.615 | 2.400 | 2.000 | 3.444 |
| 4 | Spanish | 3.165 | 2.800 | 3.250 | 3.444 |
| 5 | German | 4.741 | 5.000 | 5.000 | 4.222 |

Scorecard: [PNG](../../figures/languages/rankings/top/from/luna/language_rankings_jrc_articles_few_shot.png) | [PDF](../../figures/languages/rankings/top/from/luna/language_rankings_jrc_articles_few_shot.pdf)

## JRC Articles | Zero Shot | luna

| Rank | Language | Mixed Mean Rank | Semantic | Lexical | Terminology |
| --- | --- | --- | --- | --- | --- |
| 1 | Portuguese | 1.733 | 2.200 | 1.000 | 2.000 |
| 2 | Spanish | 2.631 | 2.200 | 3.250 | 2.444 |
| 3 | French | 2.704 | 3.000 | 2.000 | 3.111 |
| 4 | English | 3.154 | 2.600 | 3.750 | 3.111 |
| 5 | German | 4.778 | 5.000 | 5.000 | 4.333 |

Scorecard: [PNG](../../figures/languages/rankings/top/from/luna/language_rankings_jrc_articles_zero_shot.png) | [PDF](../../figures/languages/rankings/top/from/luna/language_rankings_jrc_articles_zero_shot.pdf)

## JRC Definitions | Few Shot | luna

| Rank | Language | Mixed Mean Rank | Semantic | Lexical | Terminology |
| --- | --- | --- | --- | --- | --- |
| 1 | French | 1.748 | 2.800 | 1.000 | 1.444 |
| 2 | Portuguese | 2.009 | 2.000 | 2.250 | 1.778 |
| 3 | Spanish | 2.976 | 3.400 | 2.750 | 2.778 |
| 4 | English | 3.541 | 2.400 | 4.000 | 4.222 |
| 5 | German | 4.726 | 4.400 | 5.000 | 4.778 |

Scorecard: [PNG](../../figures/languages/rankings/top/from/luna/language_rankings_jrc_definitions_few_shot.png) | [PDF](../../figures/languages/rankings/top/from/luna/language_rankings_jrc_definitions_few_shot.pdf)

## JRC Definitions | Zero Shot | luna

| Rank | Language | Mixed Mean Rank | Semantic | Lexical | Terminology |
| --- | --- | --- | --- | --- | --- |
| 1 | French | 1.681 | 2.600 | 1.000 | 1.444 |
| 2 | Portuguese | 2.009 | 2.000 | 2.250 | 1.778 |
| 3 | Spanish | 3.043 | 3.600 | 2.750 | 2.778 |
| 4 | English | 3.474 | 2.200 | 4.000 | 4.222 |
| 5 | German | 4.793 | 4.600 | 5.000 | 4.778 |

Scorecard: [PNG](../../figures/languages/rankings/top/from/luna/language_rankings_jrc_definitions_zero_shot.png) | [PDF](../../figures/languages/rankings/top/from/luna/language_rankings_jrc_definitions_zero_shot.pdf)

## Chemical Patents | Few Shot | original_glm

| Rank | Language | Mixed Mean Rank | Semantic | Lexical | Terminology |
| --- | --- | --- | --- | --- | --- |
| 1 | French | 1.815 | 1.000 | 3.000 | 1.444 |
| 2 | German | 2.463 | 3.000 | 1.500 | 2.889 |
| 3 | English | 2.548 | 2.200 | 3.000 | 2.444 |
| 4 | Chinese | 3.174 | 3.800 | 2.500 | 3.222 |

Scorecard: [PNG](../../figures/languages/rankings/top/from/original_glm/language_rankings_google_patents_few_shot.png) | [PDF](../../figures/languages/rankings/top/from/original_glm/language_rankings_google_patents_few_shot.pdf)

Unranked due to incomplete metric/dataset coverage: Spanish, Japanese, Russian.

## Chemical Patents | Zero Shot | original_glm

| Rank | Language | Mixed Mean Rank | Semantic | Lexical | Terminology |
| --- | --- | --- | --- | --- | --- |
| 1 | French | 1.778 | 1.000 | 3.000 | 1.333 |
| 2 | German | 2.396 | 2.800 | 1.500 | 2.889 |
| 3 | English | 2.652 | 2.400 | 3.000 | 2.556 |
| 4 | Chinese | 3.174 | 3.800 | 2.500 | 3.222 |

Scorecard: [PNG](../../figures/languages/rankings/top/from/original_glm/language_rankings_google_patents_zero_shot.png) | [PDF](../../figures/languages/rankings/top/from/original_glm/language_rankings_google_patents_zero_shot.pdf)

Unranked due to incomplete metric/dataset coverage: Spanish, Japanese, Russian.

## JRC Articles | Few Shot | original_glm

| Rank | Language | Mixed Mean Rank | Semantic | Lexical | Terminology |
| --- | --- | --- | --- | --- | --- |
| 1 | Portuguese | 1.867 | 2.600 | 1.000 | 2.000 |
| 2 | French | 2.467 | 2.400 | 2.000 | 3.000 |
| 3 | English | 2.761 | 2.200 | 3.750 | 2.333 |
| 4 | Spanish | 3.461 | 2.800 | 3.250 | 4.333 |
| 5 | German | 4.444 | 5.000 | 5.000 | 3.333 |

Scorecard: [PNG](../../figures/languages/rankings/top/from/original_glm/language_rankings_jrc_articles_few_shot.png) | [PDF](../../figures/languages/rankings/top/from/original_glm/language_rankings_jrc_articles_few_shot.pdf)

## JRC Articles | Zero Shot | original_glm

| Rank | Language | Mixed Mean Rank | Semantic | Lexical | Terminology |
| --- | --- | --- | --- | --- | --- |
| 1 | Portuguese | 1.696 | 2.200 | 1.000 | 1.889 |
| 2 | Spanish | 2.780 | 2.200 | 3.250 | 2.889 |
| 3 | French | 2.889 | 3.000 | 2.000 | 3.667 |
| 4 | English | 3.154 | 2.600 | 3.750 | 3.111 |
| 5 | German | 4.481 | 5.000 | 5.000 | 3.444 |

Scorecard: [PNG](../../figures/languages/rankings/top/from/original_glm/language_rankings_jrc_articles_zero_shot.png) | [PDF](../../figures/languages/rankings/top/from/original_glm/language_rankings_jrc_articles_zero_shot.pdf)

## JRC Definitions | Few Shot | original_glm

| Rank | Language | Mixed Mean Rank | Semantic | Lexical | Terminology |
| --- | --- | --- | --- | --- | --- |
| 1 | French | 1.859 | 2.800 | 1.000 | 1.778 |
| 2 | Portuguese | 1.935 | 2.000 | 2.250 | 1.556 |
| 3 | Spanish | 2.976 | 3.400 | 2.750 | 2.778 |
| 4 | English | 3.467 | 2.400 | 4.000 | 4.000 |
| 5 | German | 4.763 | 4.400 | 5.000 | 4.889 |

Scorecard: [PNG](../../figures/languages/rankings/top/from/original_glm/language_rankings_jrc_definitions_few_shot.png) | [PDF](../../figures/languages/rankings/top/from/original_glm/language_rankings_jrc_definitions_few_shot.pdf)

## JRC Definitions | Zero Shot | original_glm

| Rank | Language | Mixed Mean Rank | Semantic | Lexical | Terminology |
| --- | --- | --- | --- | --- | --- |
| 1 | French | 1.756 | 2.600 | 1.000 | 1.667 |
| 2 | Portuguese | 1.898 | 2.000 | 2.250 | 1.444 |
| 3 | Spanish | 3.080 | 3.600 | 2.750 | 2.889 |
| 4 | English | 3.400 | 2.200 | 4.000 | 4.000 |
| 5 | German | 4.867 | 4.600 | 5.000 | 5.000 |

Scorecard: [PNG](../../figures/languages/rankings/top/from/original_glm/language_rankings_jrc_definitions_zero_shot.png) | [PDF](../../figures/languages/rankings/top/from/original_glm/language_rankings_jrc_definitions_zero_shot.pdf)

