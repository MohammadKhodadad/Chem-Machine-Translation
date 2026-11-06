# Highest-Score Model Rankings

For each metric, dataset, prompt and annotation group, summarize each model's shared direction scores using the maximum. Rank models descending on those native metric values. Metric ties receive average ranks. Balance metrics within families, terminology groups equally, and semantic / lexical / terminology families equally. Lower mixed mean rank is better; final ties share the minimum rank (1, 1, 3).

Overall rankings average the dataset/prompt family ranks equally; they do not rerank a pooled statistic. Overall displayed metric cells average the stratum maxima, not a global maximum. NA metrics are omitted for every model, never scored zero. Partial model support is rejected. Original mean-based rankings and plots are unchanged.

Top means the best observed direction aggregate, not the best single translation, best model, upper confidence bound or typical performance. Different metric maxima can come from different directions. CSVs preserve supports and winning directions. These are descriptive rankings, not significance claims.

[Native metric tables](performance.md) | [Metric scores](metric_scores.csv) | [Model ranks](model_ranks.csv) | [Rank components](rank_components.csv)

## Overall: all datasets and both prompts | luna

| Rank | Model | Mixed Mean Rank | Semantic | Lexical | Terminology |
| --- | --- | --- | --- | --- | --- |
| 1 | GPT-6 Luna | 1.455 | 1.467 | 1.583 | 1.315 |
| 2 | Gemma 4 31B | 2.566 | 2.433 | 2.708 | 2.556 |
| 3 | Muse Glimmer 30B | 2.754 | 3.300 | 2.500 | 2.463 |
| 4 | Qwen3.8 27B | 3.321 | 3.033 | 3.208 | 3.722 |
| 5 | Granite 4.2 30B | 5.263 | 5.033 | 5.458 | 5.296 |
| 6 | Nemotron 3.5 Lightning | 5.723 | 5.867 | 5.542 | 5.759 |
| 7 | Tiny Aya Global | 6.919 | 6.867 | 7.000 | 6.889 |

Scorecard: [PNG](../../../figures/rankings/top/luna/rankings_top_overall.png) | [PDF](../../../figures/rankings/top/luna/rankings_top_overall.pdf)

## Overall: all datasets and both prompts | original_glm

| Rank | Model | Mixed Mean Rank | Semantic | Lexical | Terminology |
| --- | --- | --- | --- | --- | --- |
| 1 | GPT-6 Luna | 1.461 | 1.467 | 1.583 | 1.333 |
| 2 | Gemma 4 31B | 2.621 | 2.433 | 2.708 | 2.722 |
| 3 | Muse Glimmer 30B | 2.699 | 3.300 | 2.500 | 2.296 |
| 4 | Qwen3.8 27B | 3.365 | 3.033 | 3.208 | 3.852 |
| 5 | Granite 4.2 30B | 5.269 | 5.033 | 5.458 | 5.315 |
| 6 | Nemotron 3.5 Lightning | 5.655 | 5.867 | 5.542 | 5.556 |
| 7 | Tiny Aya Global | 6.931 | 6.867 | 7.000 | 6.926 |

Scorecard: [PNG](../../../figures/rankings/top/original_glm/rankings_top_overall.png) | [PDF](../../../figures/rankings/top/original_glm/rankings_top_overall.pdf)

## Chemical Patents | Few Shot | luna

| Rank | Model | Mixed Mean Rank | Semantic | Lexical | Terminology |
| --- | --- | --- | --- | --- | --- |
| 1 | Gemma 4 31B | 2.089 | 2.600 | 2.000 | 1.667 |
| 2 | GPT-6 Luna | 2.200 | 1.600 | 3.000 | 2.000 |
| 3 | Muse Glimmer 30B | 2.443 | 2.800 | 1.750 | 2.778 |
| 4 | Qwen3.8 27B | 3.372 | 3.200 | 3.250 | 3.667 |
| 5 | Granite 4.2 30B | 5.352 | 5.000 | 5.500 | 5.556 |
| 6 | Nemotron 3.5 Lightning | 5.544 | 5.800 | 5.500 | 5.333 |
| 7 | Tiny Aya Global | 7.000 | 7.000 | 7.000 | 7.000 |

Scorecard: [PNG](../../../figures/rankings/top/luna/rankings_top_google_patents_few_shot.png) | [PDF](../../../figures/rankings/top/luna/rankings_top_google_patents_few_shot.pdf)

## Chemical Patents | Zero Shot | luna

| Rank | Model | Mixed Mean Rank | Semantic | Lexical | Terminology |
| --- | --- | --- | --- | --- | --- |
| 1 | Gemma 4 31B | 1.976 | 2.400 | 1.750 | 1.778 |
| 2 | GPT-6 Luna | 1.996 | 1.600 | 2.500 | 1.889 |
| 3 | Muse Glimmer 30B | 3.046 | 4.000 | 2.250 | 2.889 |
| 4 | Qwen3.8 27B | 3.219 | 2.600 | 3.500 | 3.556 |
| 5 | Nemotron 3.5 Lightning | 5.393 | 5.400 | 5.000 | 5.778 |
| 6 | Granite 4.2 30B | 5.407 | 5.000 | 6.000 | 5.222 |
| 7 | Tiny Aya Global | 6.963 | 7.000 | 7.000 | 6.889 |

Scorecard: [PNG](../../../figures/rankings/top/luna/rankings_top_google_patents_zero_shot.png) | [PDF](../../../figures/rankings/top/luna/rankings_top_google_patents_zero_shot.pdf)

## JRC Articles | Few Shot | luna

| Rank | Model | Mixed Mean Rank | Semantic | Lexical | Terminology |
| --- | --- | --- | --- | --- | --- |
| 1 | GPT-6 Luna | 1.067 | 1.200 | 1.000 | 1.000 |
| 2 | Muse Glimmer 30B | 2.704 | 3.000 | 3.000 | 2.111 |
| 3 | Qwen3.8 27B | 2.963 | 3.000 | 2.000 | 3.889 |
| 4 | Gemma 4 31B | 3.267 | 2.800 | 4.000 | 3.000 |
| 5 | Nemotron 3.5 Lightning | 5.200 | 5.600 | 5.000 | 5.000 |
| 6 | Granite 4.2 30B | 5.800 | 5.400 | 6.000 | 6.000 |
| 7 | Tiny Aya Global | 7.000 | 7.000 | 7.000 | 7.000 |

Scorecard: [PNG](../../../figures/rankings/top/luna/rankings_top_jrc_articles_few_shot.png) | [PDF](../../../figures/rankings/top/luna/rankings_top_jrc_articles_few_shot.pdf)

## JRC Articles | Zero Shot | luna

| Rank | Model | Mixed Mean Rank | Semantic | Lexical | Terminology |
| --- | --- | --- | --- | --- | --- |
| 1 | GPT-6 Luna | 1.067 | 1.200 | 1.000 | 1.000 |
| 2 | Muse Glimmer 30B | 2.267 | 2.800 | 2.000 | 2.000 |
| 3 | Qwen3.8 27B | 3.337 | 3.400 | 3.500 | 3.111 |
| 4 | Gemma 4 31B | 3.396 | 2.800 | 3.500 | 3.889 |
| 5 | Granite 4.2 30B | 5.067 | 5.200 | 5.000 | 5.000 |
| 6 | Nemotron 3.5 Lightning | 6.104 | 6.200 | 6.000 | 6.111 |
| 7 | Tiny Aya Global | 6.763 | 6.400 | 7.000 | 6.889 |

Scorecard: [PNG](../../../figures/rankings/top/luna/rankings_top_jrc_articles_zero_shot.png) | [PDF](../../../figures/rankings/top/luna/rankings_top_jrc_articles_zero_shot.pdf)

## JRC Definitions | Few Shot | luna

| Rank | Model | Mixed Mean Rank | Semantic | Lexical | Terminology |
| --- | --- | --- | --- | --- | --- |
| 1 | GPT-6 Luna | 1.267 | 1.800 | 1.000 | 1.000 |
| 2 | Muse Glimmer 30B | 2.370 | 3.000 | 2.000 | 2.111 |
| 3 | Gemma 4 31B | 2.696 | 2.200 | 3.000 | 2.889 |
| 4 | Qwen3.8 27B | 3.733 | 3.200 | 4.000 | 4.000 |
| 5 | Granite 4.2 30B | 4.933 | 4.800 | 5.000 | 5.000 |
| 6 | Nemotron 3.5 Lightning | 6.000 | 6.000 | 6.000 | 6.000 |
| 7 | Tiny Aya Global | 7.000 | 7.000 | 7.000 | 7.000 |

Scorecard: [PNG](../../../figures/rankings/top/luna/rankings_top_jrc_definitions_few_shot.png) | [PDF](../../../figures/rankings/top/luna/rankings_top_jrc_definitions_few_shot.pdf)

## JRC Definitions | Zero Shot | luna

| Rank | Model | Mixed Mean Rank | Semantic | Lexical | Terminology |
| --- | --- | --- | --- | --- | --- |
| 1 | GPT-6 Luna | 1.133 | 1.400 | 1.000 | 1.000 |
| 2 | Gemma 4 31B | 1.970 | 1.800 | 2.000 | 2.111 |
| 3 | Qwen3.8 27B | 3.304 | 2.800 | 3.000 | 4.111 |
| 4 | Muse Glimmer 30B | 3.696 | 4.200 | 4.000 | 2.889 |
| 5 | Granite 4.2 30B | 5.017 | 4.800 | 5.250 | 5.000 |
| 6 | Nemotron 3.5 Lightning | 6.094 | 6.200 | 5.750 | 6.333 |
| 7 | Tiny Aya Global | 6.785 | 6.800 | 7.000 | 6.556 |

Scorecard: [PNG](../../../figures/rankings/top/luna/rankings_top_jrc_definitions_zero_shot.png) | [PDF](../../../figures/rankings/top/luna/rankings_top_jrc_definitions_zero_shot.pdf)

## Chemical Patents | Few Shot | original_glm

| Rank | Model | Mixed Mean Rank | Semantic | Lexical | Terminology |
| --- | --- | --- | --- | --- | --- |
| 1 | Muse Glimmer 30B | 2.072 | 2.800 | 1.750 | 1.667 |
| 2 | GPT-6 Luna | 2.311 | 1.600 | 3.000 | 2.333 |
| 3 | Gemma 4 31B | 2.422 | 2.600 | 2.000 | 2.667 |
| 4 | Qwen3.8 27B | 3.557 | 3.200 | 3.250 | 4.222 |
| 5 | Granite 4.2 30B | 5.130 | 5.000 | 5.500 | 4.889 |
| 6 | Nemotron 3.5 Lightning | 5.507 | 5.800 | 5.500 | 5.222 |
| 7 | Tiny Aya Global | 7.000 | 7.000 | 7.000 | 7.000 |

Scorecard: [PNG](../../../figures/rankings/top/original_glm/rankings_top_google_patents_few_shot.png) | [PDF](../../../figures/rankings/top/original_glm/rankings_top_google_patents_few_shot.pdf)

## Chemical Patents | Zero Shot | original_glm

| Rank | Model | Mixed Mean Rank | Semantic | Lexical | Terminology |
| --- | --- | --- | --- | --- | --- |
| 1 | GPT-6 Luna | 1.922 | 1.600 | 2.500 | 1.667 |
| 2 | Gemma 4 31B | 1.976 | 2.400 | 1.750 | 1.778 |
| 3 | Muse Glimmer 30B | 2.935 | 4.000 | 2.250 | 2.556 |
| 4 | Qwen3.8 27B | 3.441 | 2.600 | 3.500 | 4.222 |
| 5 | Nemotron 3.5 Lightning | 5.281 | 5.400 | 5.000 | 5.444 |
| 6 | Granite 4.2 30B | 5.519 | 5.000 | 6.000 | 5.556 |
| 7 | Tiny Aya Global | 6.926 | 7.000 | 7.000 | 6.778 |

Scorecard: [PNG](../../../figures/rankings/top/original_glm/rankings_top_google_patents_zero_shot.png) | [PDF](../../../figures/rankings/top/original_glm/rankings_top_google_patents_zero_shot.pdf)

## JRC Articles | Few Shot | original_glm

| Rank | Model | Mixed Mean Rank | Semantic | Lexical | Terminology |
| --- | --- | --- | --- | --- | --- |
| 1 | GPT-6 Luna | 1.067 | 1.200 | 1.000 | 1.000 |
| 2 | Muse Glimmer 30B | 2.741 | 3.000 | 3.000 | 2.222 |
| 3 | Qwen3.8 27B | 2.926 | 3.000 | 2.000 | 3.778 |
| 4 | Gemma 4 31B | 3.267 | 2.800 | 4.000 | 3.000 |
| 5 | Nemotron 3.5 Lightning | 5.237 | 5.600 | 5.000 | 5.111 |
| 6 | Granite 4.2 30B | 5.763 | 5.400 | 6.000 | 5.889 |
| 7 | Tiny Aya Global | 7.000 | 7.000 | 7.000 | 7.000 |

Scorecard: [PNG](../../../figures/rankings/top/original_glm/rankings_top_jrc_articles_few_shot.png) | [PDF](../../../figures/rankings/top/original_glm/rankings_top_jrc_articles_few_shot.pdf)

## JRC Articles | Zero Shot | original_glm

| Rank | Model | Mixed Mean Rank | Semantic | Lexical | Terminology |
| --- | --- | --- | --- | --- | --- |
| 1 | GPT-6 Luna | 1.067 | 1.200 | 1.000 | 1.000 |
| 2 | Muse Glimmer 30B | 2.341 | 2.800 | 2.000 | 2.222 |
| 3 | Qwen3.8 27B | 3.300 | 3.400 | 3.500 | 3.000 |
| 4 | Gemma 4 31B | 3.396 | 2.800 | 3.500 | 3.889 |
| 5 | Granite 4.2 30B | 5.178 | 5.200 | 5.000 | 5.333 |
| 6 | Nemotron 3.5 Lightning | 5.919 | 6.200 | 6.000 | 5.556 |
| 7 | Tiny Aya Global | 6.800 | 6.400 | 7.000 | 7.000 |

Scorecard: [PNG](../../../figures/rankings/top/original_glm/rankings_top_jrc_articles_zero_shot.png) | [PDF](../../../figures/rankings/top/original_glm/rankings_top_jrc_articles_zero_shot.pdf)

## JRC Definitions | Few Shot | original_glm

| Rank | Model | Mixed Mean Rank | Semantic | Lexical | Terminology |
| --- | --- | --- | --- | --- | --- |
| 1 | GPT-6 Luna | 1.267 | 1.800 | 1.000 | 1.000 |
| 2 | Muse Glimmer 30B | 2.333 | 3.000 | 2.000 | 2.000 |
| 3 | Gemma 4 31B | 2.733 | 2.200 | 3.000 | 3.000 |
| 4 | Qwen3.8 27B | 3.733 | 3.200 | 4.000 | 4.000 |
| 5 | Granite 4.2 30B | 5.007 | 4.800 | 5.000 | 5.222 |
| 6 | Nemotron 3.5 Lightning | 5.926 | 6.000 | 6.000 | 5.778 |
| 7 | Tiny Aya Global | 7.000 | 7.000 | 7.000 | 7.000 |

Scorecard: [PNG](../../../figures/rankings/top/original_glm/rankings_top_jrc_definitions_few_shot.png) | [PDF](../../../figures/rankings/top/original_glm/rankings_top_jrc_definitions_few_shot.pdf)

## JRC Definitions | Zero Shot | original_glm

| Rank | Model | Mixed Mean Rank | Semantic | Lexical | Terminology |
| --- | --- | --- | --- | --- | --- |
| 1 | GPT-6 Luna | 1.133 | 1.400 | 1.000 | 1.000 |
| 2 | Gemma 4 31B | 1.933 | 1.800 | 2.000 | 2.000 |
| 3 | Qwen3.8 27B | 3.230 | 2.800 | 3.000 | 3.889 |
| 4 | Muse Glimmer 30B | 3.770 | 4.200 | 4.000 | 3.111 |
| 5 | Granite 4.2 30B | 5.017 | 4.800 | 5.250 | 5.000 |
| 6 | Nemotron 3.5 Lightning | 6.057 | 6.200 | 5.750 | 6.222 |
| 7 | Tiny Aya Global | 6.859 | 6.800 | 7.000 | 6.778 |

Scorecard: [PNG](../../../figures/rankings/top/original_glm/rankings_top_jrc_definitions_zero_shot.png) | [PDF](../../../figures/rankings/top/original_glm/rankings_top_jrc_definitions_zero_shot.pdf)

