# Balanced To-Language Rankings: Best Model

Rows rank languages, NOT models. From means translating out of a language; To means translating into it. For each metric/dataset/prompt, average supported partner-direction scores equally within each model. Then use the highest model mean as that language's native metric value. Top does not choose a different model for each direction. The best model may differ between metrics and strata.

Rank languages descending within each metric with average ties. Balance metrics within semantic and lexical families; balance terminology metrics within each term group and the three groups equally. The three family ranks have equal one-third weights. Final ties share the minimum rank (1, 1, 3).

Overall rankings require every dataset, both prompts and every active metric for each language. Within that overall eligible language cohort, rerank each stratum's metric values, then average dataset/prompt family ranks equally. Displayed overall native cells are equal-stratum means, not pooled medians or global maxima. Dataset-specific cohorts may differ. All-NA metrics are omitted, never scored zero. Coverage CSV records excluded languages and missing components.

Partner populations can differ between languages. These are descriptive supported benchmark rankings, not matched-partner comparisons, intrinsic language difficulty or statistical significance. Original model scorecards are unchanged.

[Language ranks](language_ranks.csv) | [Metric ranks](metric_rank_components.csv) | [Native scores and model values](native_metric_scores.csv) | [Coverage](coverage.csv)

## Overall: all datasets and both prompts | luna

| Rank | Language | Mixed Mean Rank | Semantic | Lexical | Terminology |
| --- | --- | --- | --- | --- | --- |
| 1 | English | 2.052 | 2.833 | 1.583 | 1.741 |
| 2 | Spanish | 2.351 | 2.267 | 2.583 | 2.204 |
| 3 | German | 2.728 | 2.333 | 2.667 | 3.185 |
| 4 | French | 2.868 | 2.567 | 3.167 | 2.870 |

Scorecard: [PNG](../../figures/languages/rankings/top/to/luna/language_rankings_overall.png) | [PDF](../../figures/languages/rankings/top/to/luna/language_rankings_overall.pdf)

Unranked due to incomplete metric/dataset coverage: Japanese, Portuguese, Russian, Chinese.

## Overall: all datasets and both prompts | original_glm

| Rank | Language | Mixed Mean Rank | Semantic | Lexical | Terminology |
| --- | --- | --- | --- | --- | --- |
| 1 | Spanish | 1.719 | 1.833 | 1.750 | 1.574 |
| 2 | German | 2.077 | 1.933 | 2.000 | 2.296 |
| 3 | French | 2.204 | 2.233 | 2.250 | 2.130 |

Scorecard: [PNG](../../figures/languages/rankings/top/to/original_glm/language_rankings_overall.png) | [PDF](../../figures/languages/rankings/top/to/original_glm/language_rankings_overall.pdf)

Unranked due to incomplete metric/dataset coverage: English, Japanese, Portuguese, Russian, Chinese.

## Chemical Patents | Few Shot | luna

| Rank | Language | Mixed Mean Rank | Semantic | Lexical | Terminology |
| --- | --- | --- | --- | --- | --- |
| 1 | Spanish | 2.702 | 2.800 | 2.750 | 2.556 |
| 2 | German | 2.757 | 3.800 | 1.250 | 3.222 |
| 3 | Russian | 3.278 | 2.000 | 3.500 | 4.333 |
| 4 | Chinese | 3.939 | 3.400 | 4.750 | 3.667 |
| 5 | English | 3.954 | 5.000 | 3.750 | 3.111 |
| 6 | French | 4.370 | 4.000 | 5.000 | 4.111 |

Scorecard: [PNG](../../figures/languages/rankings/top/to/luna/language_rankings_google_patents_few_shot.png) | [PDF](../../figures/languages/rankings/top/to/luna/language_rankings_google_patents_few_shot.pdf)

Unranked due to incomplete metric/dataset coverage: Japanese.

## Chemical Patents | Zero Shot | luna

| Rank | Language | Mixed Mean Rank | Semantic | Lexical | Terminology |
| --- | --- | --- | --- | --- | --- |
| 1 | German | 2.654 | 3.600 | 1.250 | 3.111 |
| 2 | Spanish | 2.869 | 2.800 | 3.250 | 2.556 |
| 3 | Russian | 3.370 | 2.000 | 4.000 | 4.111 |
| 4 | English | 3.620 | 5.000 | 2.750 | 3.111 |
| 5 | Chinese | 4.050 | 3.400 | 4.750 | 4.000 |
| 6 | French | 4.437 | 4.200 | 5.000 | 4.111 |

Scorecard: [PNG](../../figures/languages/rankings/top/to/luna/language_rankings_google_patents_zero_shot.png) | [PDF](../../figures/languages/rankings/top/to/luna/language_rankings_google_patents_zero_shot.pdf)

Unranked due to incomplete metric/dataset coverage: Japanese.

## JRC Articles | Few Shot | luna

| Rank | Language | Mixed Mean Rank | Semantic | Lexical | Terminology |
| --- | --- | --- | --- | --- | --- |
| 1 | English | 1.956 | 3.200 | 1.000 | 1.667 |
| 2 | Spanish | 2.561 | 2.600 | 2.750 | 2.333 |
| 3 | German | 3.159 | 2.200 | 3.500 | 3.778 |
| 4 | French | 3.467 | 3.400 | 3.000 | 4.000 |
| 5 | Portuguese | 3.857 | 3.600 | 4.750 | 3.222 |

Scorecard: [PNG](../../figures/languages/rankings/top/to/luna/language_rankings_jrc_articles_few_shot.png) | [PDF](../../figures/languages/rankings/top/to/luna/language_rankings_jrc_articles_few_shot.pdf)

## JRC Articles | Zero Shot | luna

| Rank | Language | Mixed Mean Rank | Semantic | Lexical | Terminology |
| --- | --- | --- | --- | --- | --- |
| 1 | English | 1.919 | 3.200 | 1.000 | 1.556 |
| 2 | Spanish | 2.485 | 2.400 | 2.500 | 2.556 |
| 3 | German | 2.819 | 2.400 | 2.500 | 3.556 |
| 4 | French | 3.652 | 3.400 | 4.000 | 3.556 |
| 5 | Portuguese | 4.126 | 3.600 | 5.000 | 3.778 |

Scorecard: [PNG](../../figures/languages/rankings/top/to/luna/language_rankings_jrc_articles_zero_shot.png) | [PDF](../../figures/languages/rankings/top/to/luna/language_rankings_jrc_articles_zero_shot.pdf)

## JRC Definitions | Few Shot | luna

| Rank | Language | Mixed Mean Rank | Semantic | Lexical | Terminology |
| --- | --- | --- | --- | --- | --- |
| 1 | French | 2.057 | 2.200 | 1.750 | 2.222 |
| 2 | English | 2.122 | 3.200 | 1.500 | 1.667 |
| 3 | Spanish | 3.150 | 3.200 | 3.250 | 3.000 |
| 4 | Portuguese | 3.419 | 3.200 | 3.500 | 3.556 |
| 5 | German | 4.252 | 3.200 | 5.000 | 4.556 |

Scorecard: [PNG](../../figures/languages/rankings/top/to/luna/language_rankings_jrc_definitions_few_shot.png) | [PDF](../../figures/languages/rankings/top/to/luna/language_rankings_jrc_definitions_few_shot.pdf)

## JRC Definitions | Zero Shot | luna

| Rank | Language | Mixed Mean Rank | Semantic | Lexical | Terminology |
| --- | --- | --- | --- | --- | --- |
| 1 | English | 2.115 | 3.400 | 1.500 | 1.444 |
| 2 | French | 2.343 | 2.000 | 2.250 | 2.778 |
| 3 | Spanish | 2.731 | 3.000 | 2.750 | 2.444 |
| 4 | Portuguese | 3.633 | 3.400 | 3.500 | 4.000 |
| 5 | German | 4.178 | 3.200 | 5.000 | 4.333 |

Scorecard: [PNG](../../figures/languages/rankings/top/to/luna/language_rankings_jrc_definitions_zero_shot.png) | [PDF](../../figures/languages/rankings/top/to/luna/language_rankings_jrc_definitions_zero_shot.pdf)

## Chemical Patents | Few Shot | original_glm

| Rank | Language | Mixed Mean Rank | Semantic | Lexical | Terminology |
| --- | --- | --- | --- | --- | --- |
| 1 | Spanish | 2.991 | 3.000 | 2.750 | 3.222 |
| 2 | German | 3.048 | 4.200 | 1.500 | 3.444 |
| 3 | Russian | 3.226 | 2.400 | 3.500 | 3.778 |
| 4 | Japanese | 3.280 | 3.200 | 4.750 | 1.889 |
| 5 | Chinese | 4.054 | 3.800 | 4.250 | 4.111 |
| 6 | French | 4.402 | 4.400 | 4.250 | 4.556 |

Scorecard: [PNG](../../figures/languages/rankings/top/to/original_glm/language_rankings_google_patents_few_shot.png) | [PDF](../../figures/languages/rankings/top/to/original_glm/language_rankings_google_patents_few_shot.pdf)

Unranked due to incomplete metric/dataset coverage: English.

## Chemical Patents | Zero Shot | original_glm

| Rank | Language | Mixed Mean Rank | Semantic | Lexical | Terminology |
| --- | --- | --- | --- | --- | --- |
| 1 | German | 2.898 | 4.000 | 1.250 | 3.444 |
| 2 | Spanish | 2.991 | 3.000 | 2.750 | 3.222 |
| 3 | Russian | 3.263 | 2.400 | 3.500 | 3.889 |
| 4 | Japanese | 3.409 | 3.200 | 5.250 | 1.778 |
| 5 | Chinese | 4.007 | 3.800 | 4.000 | 4.222 |
| 6 | French | 4.431 | 4.600 | 4.250 | 4.444 |

Scorecard: [PNG](../../figures/languages/rankings/top/to/original_glm/language_rankings_google_patents_zero_shot.png) | [PDF](../../figures/languages/rankings/top/to/original_glm/language_rankings_google_patents_zero_shot.pdf)

Unranked due to incomplete metric/dataset coverage: English.

## JRC Articles | Few Shot | original_glm

| Rank | Language | Mixed Mean Rank | Semantic | Lexical | Terminology |
| --- | --- | --- | --- | --- | --- |
| 1 | English | 1.919 | 3.200 | 1.000 | 1.556 |
| 2 | Spanish | 2.524 | 2.600 | 2.750 | 2.222 |
| 3 | French | 3.244 | 3.400 | 3.000 | 3.333 |
| 4 | German | 3.344 | 2.200 | 3.500 | 4.333 |
| 5 | Portuguese | 3.969 | 3.600 | 4.750 | 3.556 |

Scorecard: [PNG](../../figures/languages/rankings/top/to/original_glm/language_rankings_jrc_articles_few_shot.png) | [PDF](../../figures/languages/rankings/top/to/original_glm/language_rankings_jrc_articles_few_shot.pdf)

## JRC Articles | Zero Shot | original_glm

| Rank | Language | Mixed Mean Rank | Semantic | Lexical | Terminology |
| --- | --- | --- | --- | --- | --- |
| 1 | English | 1.844 | 3.200 | 1.000 | 1.333 |
| 2 | Spanish | 2.485 | 2.400 | 2.500 | 2.556 |
| 3 | German | 2.930 | 2.400 | 2.500 | 3.889 |
| 4 | French | 3.726 | 3.400 | 4.000 | 3.778 |
| 5 | Portuguese | 4.015 | 3.600 | 5.000 | 3.444 |

Scorecard: [PNG](../../figures/languages/rankings/top/to/original_glm/language_rankings_jrc_articles_zero_shot.png) | [PDF](../../figures/languages/rankings/top/to/original_glm/language_rankings_jrc_articles_zero_shot.pdf)

## JRC Definitions | Few Shot | original_glm

| Rank | Language | Mixed Mean Rank | Semantic | Lexical | Terminology |
| --- | --- | --- | --- | --- | --- |
| 1 | English | 2.196 | 3.200 | 1.500 | 1.889 |
| 2 | French | 2.206 | 2.200 | 1.750 | 2.667 |
| 3 | Spanish | 3.039 | 3.200 | 3.250 | 2.667 |
| 4 | Portuguese | 3.270 | 3.200 | 3.500 | 3.111 |
| 5 | German | 4.289 | 3.200 | 5.000 | 4.667 |

Scorecard: [PNG](../../figures/languages/rankings/top/to/original_glm/language_rankings_jrc_definitions_few_shot.png) | [PDF](../../figures/languages/rankings/top/to/original_glm/language_rankings_jrc_definitions_few_shot.pdf)

## JRC Definitions | Zero Shot | original_glm

| Rank | Language | Mixed Mean Rank | Semantic | Lexical | Terminology |
| --- | --- | --- | --- | --- | --- |
| 1 | English | 2.189 | 3.400 | 1.500 | 1.667 |
| 2 | French | 2.343 | 2.000 | 2.250 | 2.778 |
| 3 | Spanish | 2.694 | 3.000 | 2.750 | 2.333 |
| 4 | Portuguese | 3.633 | 3.400 | 3.500 | 4.000 |
| 5 | German | 4.141 | 3.200 | 5.000 | 4.222 |

Scorecard: [PNG](../../figures/languages/rankings/top/to/original_glm/language_rankings_jrc_definitions_zero_shot.png) | [PDF](../../figures/languages/rankings/top/to/original_glm/language_rankings_jrc_definitions_zero_shot.pdf)

