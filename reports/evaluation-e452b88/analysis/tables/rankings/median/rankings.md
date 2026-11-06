# Median Model Rankings

For each metric, dataset, prompt and annotation group, summarize each model's shared direction scores using the median. Rank models descending on those native metric values. Metric ties receive average ranks. Balance metrics within families, terminology groups equally, and semantic / lexical / terminology families equally. Lower mixed mean rank is better; final ties share the minimum rank (1, 1, 3).

Overall rankings average the dataset/prompt family ranks equally; they do not rerank a pooled statistic. Overall displayed metric cells average the stratum medians, not a pooled median. NA metrics are omitted for every model, never scored zero. Partial model support is rejected. Original mean-based rankings and plots are unchanged.

Top means the best observed direction aggregate, not the best single translation, best model, upper confidence bound or typical performance. Different metric maxima can come from different directions. CSVs preserve supports and winning directions. These are descriptive rankings, not significance claims.

[Native metric tables](performance.md) | [Metric scores](metric_scores.csv) | [Model ranks](model_ranks.csv) | [Rank components](rank_components.csv)

## Overall: all datasets and both prompts | luna

| Rank | Model | Mixed Mean Rank | Semantic | Lexical | Terminology |
| --- | --- | --- | --- | --- | --- |
| 1 | GPT-6 Luna | 1.500 | 1.133 | 1.958 | 1.407 |
| 2 | Muse Glimmer 30B | 2.565 | 3.300 | 2.208 | 2.185 |
| 3 | Gemma 4 31B | 2.972 | 3.167 | 2.917 | 2.833 |
| 4 | Qwen3.8 27B | 3.283 | 3.267 | 2.917 | 3.667 |
| 5 | Granite 4.2 30B | 5.166 | 4.600 | 5.417 | 5.481 |
| 6 | Nemotron 3.5 Lightning | 5.661 | 5.900 | 5.583 | 5.500 |
| 7 | Tiny Aya Global | 6.853 | 6.633 | 7.000 | 6.926 |

Scorecard: [PNG](../../../figures/rankings/median/luna/rankings_median_overall.png) | [PDF](../../../figures/rankings/median/luna/rankings_median_overall.pdf)

## Overall: all datasets and both prompts | original_glm

| Rank | Model | Mixed Mean Rank | Semantic | Lexical | Terminology |
| --- | --- | --- | --- | --- | --- |
| 1 | GPT-6 Luna | 1.450 | 1.133 | 1.958 | 1.259 |
| 2 | Muse Glimmer 30B | 2.608 | 3.300 | 2.208 | 2.315 |
| 3 | Gemma 4 31B | 2.972 | 3.167 | 2.917 | 2.833 |
| 4 | Qwen3.8 27B | 3.259 | 3.267 | 2.917 | 3.593 |
| 5 | Granite 4.2 30B | 5.209 | 4.600 | 5.417 | 5.611 |
| 6 | Nemotron 3.5 Lightning | 5.643 | 5.900 | 5.583 | 5.444 |
| 7 | Tiny Aya Global | 6.859 | 6.633 | 7.000 | 6.944 |

Scorecard: [PNG](../../../figures/rankings/median/original_glm/rankings_median_overall.png) | [PDF](../../../figures/rankings/median/original_glm/rankings_median_overall.pdf)

## Chemical Patents | Few Shot | luna

| Rank | Model | Mixed Mean Rank | Semantic | Lexical | Terminology |
| --- | --- | --- | --- | --- | --- |
| 1 | Muse Glimmer 30B | 2.207 | 3.400 | 1.000 | 2.222 |
| 2 | Gemma 4 31B | 2.276 | 2.800 | 2.250 | 1.778 |
| 3 | GPT-6 Luna | 2.511 | 1.200 | 4.000 | 2.333 |
| 4 | Qwen3.8 27B | 3.420 | 3.400 | 2.750 | 4.111 |
| 5 | Nemotron 3.5 Lightning | 5.207 | 5.400 | 5.000 | 5.222 |
| 6 | Granite 4.2 30B | 5.511 | 5.200 | 6.000 | 5.333 |
| 7 | Tiny Aya Global | 6.867 | 6.600 | 7.000 | 7.000 |

Scorecard: [PNG](../../../figures/rankings/median/luna/rankings_median_google_patents_few_shot.png) | [PDF](../../../figures/rankings/median/luna/rankings_median_google_patents_few_shot.pdf)

## Chemical Patents | Zero Shot | luna

| Rank | Model | Mixed Mean Rank | Semantic | Lexical | Terminology |
| --- | --- | --- | --- | --- | --- |
| 1 | Gemma 4 31B | 2.150 | 3.200 | 1.250 | 2.000 |
| 2 | GPT-6 Luna | 2.287 | 1.000 | 3.750 | 2.111 |
| 3 | Muse Glimmer 30B | 2.754 | 4.400 | 1.750 | 2.111 |
| 4 | Qwen3.8 27B | 3.380 | 3.000 | 3.250 | 3.889 |
| 5 | Granite 4.2 30B | 5.213 | 4.000 | 5.750 | 5.889 |
| 6 | Nemotron 3.5 Lightning | 5.350 | 5.800 | 5.250 | 5.000 |
| 7 | Tiny Aya Global | 6.867 | 6.600 | 7.000 | 7.000 |

Scorecard: [PNG](../../../figures/rankings/median/luna/rankings_median_google_patents_zero_shot.png) | [PDF](../../../figures/rankings/median/luna/rankings_median_google_patents_zero_shot.pdf)

## JRC Articles | Few Shot | luna

| Rank | Model | Mixed Mean Rank | Semantic | Lexical | Terminology |
| --- | --- | --- | --- | --- | --- |
| 1 | GPT-6 Luna | 1.067 | 1.200 | 1.000 | 1.000 |
| 2 | Muse Glimmer 30B | 2.270 | 2.200 | 2.500 | 2.111 |
| 3 | Qwen3.8 27B | 3.041 | 3.400 | 2.500 | 3.222 |
| 4 | Gemma 4 31B | 3.822 | 3.800 | 4.000 | 3.667 |
| 5 | Granite 4.2 30B | 5.261 | 5.200 | 5.250 | 5.333 |
| 6 | Nemotron 3.5 Lightning | 5.539 | 5.200 | 5.750 | 5.667 |
| 7 | Tiny Aya Global | 7.000 | 7.000 | 7.000 | 7.000 |

Scorecard: [PNG](../../../figures/rankings/median/luna/rankings_median_jrc_articles_few_shot.png) | [PDF](../../../figures/rankings/median/luna/rankings_median_jrc_articles_few_shot.pdf)

## JRC Articles | Zero Shot | luna

| Rank | Model | Mixed Mean Rank | Semantic | Lexical | Terminology |
| --- | --- | --- | --- | --- | --- |
| 1 | GPT-6 Luna | 1.133 | 1.400 | 1.000 | 1.000 |
| 2 | Muse Glimmer 30B | 2.387 | 2.800 | 2.250 | 2.111 |
| 3 | Qwen3.8 27B | 2.880 | 3.000 | 2.750 | 2.889 |
| 4 | Gemma 4 31B | 3.933 | 3.800 | 4.000 | 4.000 |
| 5 | Granite 4.2 30B | 5.270 | 4.200 | 5.500 | 6.111 |
| 6 | Nemotron 3.5 Lightning | 5.811 | 6.600 | 5.500 | 5.333 |
| 7 | Tiny Aya Global | 6.585 | 6.200 | 7.000 | 6.556 |

Scorecard: [PNG](../../../figures/rankings/median/luna/rankings_median_jrc_articles_zero_shot.png) | [PDF](../../../figures/rankings/median/luna/rankings_median_jrc_articles_zero_shot.pdf)

## JRC Definitions | Few Shot | luna

| Rank | Model | Mixed Mean Rank | Semantic | Lexical | Terminology |
| --- | --- | --- | --- | --- | --- |
| 1 | GPT-6 Luna | 1.000 | 1.000 | 1.000 | 1.000 |
| 2 | Muse Glimmer 30B | 2.617 | 3.600 | 2.250 | 2.000 |
| 3 | Gemma 4 31B | 3.183 | 2.800 | 3.750 | 3.000 |
| 4 | Qwen3.8 27B | 3.467 | 3.400 | 3.000 | 4.000 |
| 5 | Granite 4.2 30B | 4.874 | 4.400 | 5.000 | 5.222 |
| 6 | Nemotron 3.5 Lightning | 5.926 | 6.000 | 6.000 | 5.778 |
| 7 | Tiny Aya Global | 6.933 | 6.800 | 7.000 | 7.000 |

Scorecard: [PNG](../../../figures/rankings/median/luna/rankings_median_jrc_definitions_few_shot.png) | [PDF](../../../figures/rankings/median/luna/rankings_median_jrc_definitions_few_shot.pdf)

## JRC Definitions | Zero Shot | luna

| Rank | Model | Mixed Mean Rank | Semantic | Lexical | Terminology |
| --- | --- | --- | --- | --- | --- |
| 1 | GPT-6 Luna | 1.000 | 1.000 | 1.000 | 1.000 |
| 2 | Gemma 4 31B | 2.469 | 2.600 | 2.250 | 2.556 |
| 3 | Muse Glimmer 30B | 3.152 | 3.400 | 3.500 | 2.556 |
| 4 | Qwen3.8 27B | 3.513 | 3.400 | 3.250 | 3.889 |
| 5 | Granite 4.2 30B | 4.867 | 4.600 | 5.000 | 5.000 |
| 6 | Nemotron 3.5 Lightning | 6.133 | 6.400 | 6.000 | 6.000 |
| 7 | Tiny Aya Global | 6.867 | 6.600 | 7.000 | 7.000 |

Scorecard: [PNG](../../../figures/rankings/median/luna/rankings_median_jrc_definitions_zero_shot.png) | [PDF](../../../figures/rankings/median/luna/rankings_median_jrc_definitions_zero_shot.pdf)

## Chemical Patents | Few Shot | original_glm

| Rank | Model | Mixed Mean Rank | Semantic | Lexical | Terminology |
| --- | --- | --- | --- | --- | --- |
| 1 | Muse Glimmer 30B | 2.170 | 3.400 | 1.000 | 2.111 |
| 2 | GPT-6 Luna | 2.252 | 1.200 | 4.000 | 1.556 |
| 3 | Gemma 4 31B | 2.498 | 2.800 | 2.250 | 2.444 |
| 4 | Qwen3.8 27B | 3.346 | 3.400 | 2.750 | 3.889 |
| 5 | Nemotron 3.5 Lightning | 5.170 | 5.400 | 5.000 | 5.111 |
| 6 | Granite 4.2 30B | 5.696 | 5.200 | 6.000 | 5.889 |
| 7 | Tiny Aya Global | 6.867 | 6.600 | 7.000 | 7.000 |

Scorecard: [PNG](../../../figures/rankings/median/original_glm/rankings_median_google_patents_few_shot.png) | [PDF](../../../figures/rankings/median/original_glm/rankings_median_google_patents_few_shot.pdf)

## Chemical Patents | Zero Shot | original_glm

| Rank | Model | Mixed Mean Rank | Semantic | Lexical | Terminology |
| --- | --- | --- | --- | --- | --- |
| 1 | Gemma 4 31B | 1.965 | 3.200 | 1.250 | 1.444 |
| 2 | GPT-6 Luna | 2.250 | 1.000 | 3.750 | 2.000 |
| 3 | Muse Glimmer 30B | 2.939 | 4.400 | 1.750 | 2.667 |
| 4 | Qwen3.8 27B | 3.380 | 3.000 | 3.250 | 3.889 |
| 5 | Granite 4.2 30B | 5.065 | 4.000 | 5.750 | 5.444 |
| 6 | Nemotron 3.5 Lightning | 5.535 | 5.800 | 5.250 | 5.556 |
| 7 | Tiny Aya Global | 6.867 | 6.600 | 7.000 | 7.000 |

Scorecard: [PNG](../../../figures/rankings/median/original_glm/rankings_median_google_patents_zero_shot.png) | [PDF](../../../figures/rankings/median/original_glm/rankings_median_google_patents_zero_shot.pdf)

## JRC Articles | Few Shot | original_glm

| Rank | Model | Mixed Mean Rank | Semantic | Lexical | Terminology |
| --- | --- | --- | --- | --- | --- |
| 1 | GPT-6 Luna | 1.067 | 1.200 | 1.000 | 1.000 |
| 2 | Muse Glimmer 30B | 2.344 | 2.200 | 2.500 | 2.333 |
| 3 | Qwen3.8 27B | 2.930 | 3.400 | 2.500 | 2.889 |
| 4 | Gemma 4 31B | 3.859 | 3.800 | 4.000 | 3.778 |
| 5 | Granite 4.2 30B | 5.372 | 5.200 | 5.250 | 5.667 |
| 6 | Nemotron 3.5 Lightning | 5.428 | 5.200 | 5.750 | 5.333 |
| 7 | Tiny Aya Global | 7.000 | 7.000 | 7.000 | 7.000 |

Scorecard: [PNG](../../../figures/rankings/median/original_glm/rankings_median_jrc_articles_few_shot.png) | [PDF](../../../figures/rankings/median/original_glm/rankings_median_jrc_articles_few_shot.pdf)

## JRC Articles | Zero Shot | original_glm

| Rank | Model | Mixed Mean Rank | Semantic | Lexical | Terminology |
| --- | --- | --- | --- | --- | --- |
| 1 | GPT-6 Luna | 1.133 | 1.400 | 1.000 | 1.000 |
| 2 | Muse Glimmer 30B | 2.461 | 2.800 | 2.250 | 2.333 |
| 3 | Qwen3.8 27B | 2.954 | 3.000 | 2.750 | 3.111 |
| 4 | Gemma 4 31B | 3.785 | 3.800 | 4.000 | 3.556 |
| 5 | Granite 4.2 30B | 5.344 | 4.200 | 5.500 | 6.333 |
| 6 | Nemotron 3.5 Lightning | 5.700 | 6.600 | 5.500 | 5.000 |
| 7 | Tiny Aya Global | 6.622 | 6.200 | 7.000 | 6.667 |

Scorecard: [PNG](../../../figures/rankings/median/original_glm/rankings_median_jrc_articles_zero_shot.png) | [PDF](../../../figures/rankings/median/original_glm/rankings_median_jrc_articles_zero_shot.pdf)

## JRC Definitions | Few Shot | original_glm

| Rank | Model | Mixed Mean Rank | Semantic | Lexical | Terminology |
| --- | --- | --- | --- | --- | --- |
| 1 | GPT-6 Luna | 1.000 | 1.000 | 1.000 | 1.000 |
| 2 | Muse Glimmer 30B | 2.617 | 3.600 | 2.250 | 2.000 |
| 3 | Gemma 4 31B | 3.183 | 2.800 | 3.750 | 3.000 |
| 4 | Qwen3.8 27B | 3.467 | 3.400 | 3.000 | 4.000 |
| 5 | Granite 4.2 30B | 4.911 | 4.400 | 5.000 | 5.333 |
| 6 | Nemotron 3.5 Lightning | 5.889 | 6.000 | 6.000 | 5.667 |
| 7 | Tiny Aya Global | 6.933 | 6.800 | 7.000 | 7.000 |

Scorecard: [PNG](../../../figures/rankings/median/original_glm/rankings_median_jrc_definitions_few_shot.png) | [PDF](../../../figures/rankings/median/original_glm/rankings_median_jrc_definitions_few_shot.pdf)

## JRC Definitions | Zero Shot | original_glm

| Rank | Model | Mixed Mean Rank | Semantic | Lexical | Terminology |
| --- | --- | --- | --- | --- | --- |
| 1 | GPT-6 Luna | 1.000 | 1.000 | 1.000 | 1.000 |
| 2 | Gemma 4 31B | 2.543 | 2.600 | 2.250 | 2.778 |
| 3 | Muse Glimmer 30B | 3.115 | 3.400 | 3.500 | 2.444 |
| 4 | Qwen3.8 27B | 3.476 | 3.400 | 3.250 | 3.778 |
| 5 | Granite 4.2 30B | 4.867 | 4.600 | 5.000 | 5.000 |
| 6 | Nemotron 3.5 Lightning | 6.133 | 6.400 | 6.000 | 6.000 |
| 7 | Tiny Aya Global | 6.867 | 6.600 | 7.000 | 7.000 |

Scorecard: [PNG](../../../figures/rankings/median/original_glm/rankings_median_jrc_definitions_zero_shot.png) | [PDF](../../../figures/rankings/median/original_glm/rankings_median_jrc_definitions_zero_shot.pdf)

