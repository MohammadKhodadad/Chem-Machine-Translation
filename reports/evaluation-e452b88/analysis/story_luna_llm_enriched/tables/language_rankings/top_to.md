# Balanced To-Language Rankings: Best Model

Rows rank languages, NOT models. From means translating out of a language; To means translating into it. For each metric/dataset/prompt, average supported partner-direction scores equally within each model. Then use the highest model mean as that language's native metric value. Top does not choose a different model for each direction. The best model may differ between metrics and strata.

Rank languages descending within each metric with average ties. Balance metrics within semantic and lexical families; balance terminology metrics within each term group and the selected groups equally. The three family ranks have equal one-third weights. Final ties share the minimum rank (1, 1, 3).

Overall rankings require every dataset, both prompts and every active metric for each language. Within that overall eligible language cohort, rerank each stratum's metric values, then average dataset/prompt family ranks equally. Displayed overall native cells are equal-stratum means, not pooled medians or global maxima. Dataset-specific cohorts may differ. All-NA metrics are omitted, never scored zero. Coverage CSV records excluded languages and missing components.

Partner populations can differ between languages. These are descriptive supported benchmark rankings, not matched-partner comparisons, intrinsic language difficulty or statistical significance. Original model scorecards are unchanged.

[Language ranks](language_ranks.csv) | [Metric ranks](metric_rank_components.csv) | [Native scores and model values](native_metric_scores.csv) | [Coverage](coverage.csv)

## Overall: all datasets and both prompts | luna

| Rank | Language | Mixed Mean Rank | Semantic | Lexical | Terminology |
| --- | --- | --- | --- | --- | --- |
| 1 | English | 2.102 | 2.833 | 1.583 | 1.889 |
| 2 | Spanish | 2.228 | 2.267 | 2.583 | 1.833 |
| 3 | German | 2.815 | 2.333 | 2.667 | 3.444 |
| 4 | French | 2.856 | 2.567 | 3.167 | 2.833 |

Scorecard: [PNG](../../figures/languages/rankings/top/to/luna/language_rankings_overall.png) | [PDF](../../figures/languages/rankings/top/to/luna/language_rankings_overall.pdf)

Unranked due to incomplete metric/dataset coverage: Japanese, Portuguese, Russian, Chinese.

## Chemical Patents | Few Shot | luna

| Rank | Language | Mixed Mean Rank | Semantic | Lexical | Terminology |
| --- | --- | --- | --- | --- | --- |
| 1 | Spanish | 2.406 | 2.800 | 2.750 | 1.667 |
| 2 | German | 3.017 | 3.800 | 1.250 | 4.000 |
| 3 | Russian | 3.389 | 2.000 | 3.500 | 4.667 |
| 4 | English | 3.917 | 5.000 | 3.750 | 3.000 |
| 5 | Chinese | 3.939 | 3.400 | 4.750 | 3.667 |
| 6 | French | 4.333 | 4.000 | 5.000 | 4.000 |

Scorecard: [PNG](../../figures/languages/rankings/top/to/luna/language_rankings_google_patents_few_shot.png) | [PDF](../../figures/languages/rankings/top/to/luna/language_rankings_google_patents_few_shot.pdf)

Unranked due to incomplete metric/dataset coverage: Japanese.

## Chemical Patents | Zero Shot | luna

| Rank | Language | Mixed Mean Rank | Semantic | Lexical | Terminology |
| --- | --- | --- | --- | --- | --- |
| 1 | Spanish | 2.572 | 2.800 | 3.250 | 1.667 |
| 2 | German | 2.950 | 3.600 | 1.250 | 4.000 |
| 3 | Russian | 3.333 | 2.000 | 4.000 | 4.000 |
| 4 | English | 3.583 | 5.000 | 2.750 | 3.000 |
| 5 | Chinese | 4.161 | 3.400 | 4.750 | 4.333 |
| 6 | French | 4.400 | 4.200 | 5.000 | 4.000 |

Scorecard: [PNG](../../figures/languages/rankings/top/to/luna/language_rankings_google_patents_zero_shot.png) | [PDF](../../figures/languages/rankings/top/to/luna/language_rankings_google_patents_zero_shot.pdf)

Unranked due to incomplete metric/dataset coverage: Japanese.

## JRC Articles | Few Shot | luna

| Rank | Language | Mixed Mean Rank | Semantic | Lexical | Terminology |
| --- | --- | --- | --- | --- | --- |
| 1 | English | 2.067 | 3.200 | 1.000 | 2.000 |
| 2 | Spanish | 2.339 | 2.600 | 2.750 | 1.667 |
| 3 | German | 3.122 | 2.200 | 3.500 | 3.667 |
| 4 | French | 3.578 | 3.400 | 3.000 | 4.333 |
| 5 | Portuguese | 3.894 | 3.600 | 4.750 | 3.333 |

Scorecard: [PNG](../../figures/languages/rankings/top/to/luna/language_rankings_jrc_articles_few_shot.png) | [PDF](../../figures/languages/rankings/top/to/luna/language_rankings_jrc_articles_few_shot.pdf)

## JRC Articles | Zero Shot | luna

| Rank | Language | Mixed Mean Rank | Semantic | Lexical | Terminology |
| --- | --- | --- | --- | --- | --- |
| 1 | English | 1.956 | 3.200 | 1.000 | 1.667 |
| 2 | Spanish | 2.411 | 2.400 | 2.500 | 2.333 |
| 3 | German | 2.633 | 2.400 | 2.500 | 3.000 |
| 4 | French | 3.800 | 3.400 | 4.000 | 4.000 |
| 5 | Portuguese | 4.200 | 3.600 | 5.000 | 4.000 |

Scorecard: [PNG](../../figures/languages/rankings/top/to/luna/language_rankings_jrc_articles_zero_shot.png) | [PDF](../../figures/languages/rankings/top/to/luna/language_rankings_jrc_articles_zero_shot.pdf)

## JRC Definitions | Few Shot | luna

| Rank | Language | Mixed Mean Rank | Semantic | Lexical | Terminology |
| --- | --- | --- | --- | --- | --- |
| 1 | French | 1.872 | 2.200 | 1.750 | 1.667 |
| 2 | English | 2.122 | 3.200 | 1.500 | 1.667 |
| 3 | Spanish | 3.039 | 3.200 | 3.250 | 2.667 |
| 4 | Portuguese | 3.567 | 3.200 | 3.500 | 4.000 |
| 5 | German | 4.400 | 3.200 | 5.000 | 5.000 |

Scorecard: [PNG](../../figures/languages/rankings/top/to/luna/language_rankings_jrc_definitions_few_shot.png) | [PDF](../../figures/languages/rankings/top/to/luna/language_rankings_jrc_definitions_few_shot.pdf)

## JRC Definitions | Zero Shot | luna

| Rank | Language | Mixed Mean Rank | Semantic | Lexical | Terminology |
| --- | --- | --- | --- | --- | --- |
| 1 | French | 2.083 | 2.000 | 2.250 | 2.000 |
| 2 | English | 2.189 | 3.400 | 1.500 | 1.667 |
| 3 | Spanish | 2.694 | 3.000 | 2.750 | 2.333 |
| 4 | Portuguese | 3.856 | 3.400 | 3.500 | 4.667 |
| 5 | German | 4.178 | 3.200 | 5.000 | 4.333 |

Scorecard: [PNG](../../figures/languages/rankings/top/to/luna/language_rankings_jrc_definitions_zero_shot.png) | [PDF](../../figures/languages/rankings/top/to/luna/language_rankings_jrc_definitions_zero_shot.pdf)

