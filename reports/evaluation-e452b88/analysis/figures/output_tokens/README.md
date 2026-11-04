# Output Tokens vs Mixed Rank (Latency Bubbles)

X = recorded output tokens (millions); Y = existing ten-model mixed rank; bubble area = observed latency. Select models documented as thinking by default, not runs proven to use thinking. Gemma's template defaults to thinking off; Tiny Aya has no verified default-thinking evidence. The local GPT config disables thinking but is not verified as the downloaded run's original config. Output counts are not verified as thinking-inclusive; reasoning tokens are not added again. Overall tokens sum six strata; latency weights stratum means equally. Model tokenizers and recorded workloads differ. Rankings and Chosen 03 are unchanged.

[Token counts, ranks, latencies and default-thinking provenance](../../tables/output_tokens_rank_latency.csv)

### Default-Thinking Sources (Checked 2026-11-04)

- [GPT-6 Luna](https://developers.openai.com/api/docs/models/gpt-6-luna): reasoning.effort defaults to medium; run overrides are unverified
- [Granite 4.2 30B](https://huggingface.co/ibm-granite/granite-4.2-30b): Thinking (default): enable_thinking=True
- [Muse Glimmer 30B](https://huggingface.co/meta-models/Muse-Glimmer-30B/raw/main/chat_template.jinja): Chat template injects Reasoning strength: high when unspecified
- [Nemotron 3.5 Lightning](https://huggingface.co/nvidia/NVIDIA-Nemotron-3.5-Lightning-30B-A3B-BF16): Model card: thinking enabled (the default)
- [Qwen3.8 27B](https://huggingface.co/Qwen/Qwen3.8-27B): Model card: thinking mode is on by default

### Figures

- luna/output_tokens_vs_rank_latency_overall: [PNG](luna/output_tokens_vs_rank_latency_overall.png) | [PDF](luna/output_tokens_vs_rank_latency_overall.pdf)
- original_glm/output_tokens_vs_rank_latency_overall: [PNG](original_glm/output_tokens_vs_rank_latency_overall.png) | [PDF](original_glm/output_tokens_vs_rank_latency_overall.pdf)
- luna/output_tokens_vs_rank_latency_google_patents_few_shot: [PNG](luna/output_tokens_vs_rank_latency_google_patents_few_shot.png) | [PDF](luna/output_tokens_vs_rank_latency_google_patents_few_shot.pdf)
- luna/output_tokens_vs_rank_latency_google_patents_zero_shot: [PNG](luna/output_tokens_vs_rank_latency_google_patents_zero_shot.png) | [PDF](luna/output_tokens_vs_rank_latency_google_patents_zero_shot.pdf)
- luna/output_tokens_vs_rank_latency_jrc_articles_few_shot: [PNG](luna/output_tokens_vs_rank_latency_jrc_articles_few_shot.png) | [PDF](luna/output_tokens_vs_rank_latency_jrc_articles_few_shot.pdf)
- luna/output_tokens_vs_rank_latency_jrc_articles_zero_shot: [PNG](luna/output_tokens_vs_rank_latency_jrc_articles_zero_shot.png) | [PDF](luna/output_tokens_vs_rank_latency_jrc_articles_zero_shot.pdf)
- luna/output_tokens_vs_rank_latency_jrc_definitions_few_shot: [PNG](luna/output_tokens_vs_rank_latency_jrc_definitions_few_shot.png) | [PDF](luna/output_tokens_vs_rank_latency_jrc_definitions_few_shot.pdf)
- luna/output_tokens_vs_rank_latency_jrc_definitions_zero_shot: [PNG](luna/output_tokens_vs_rank_latency_jrc_definitions_zero_shot.png) | [PDF](luna/output_tokens_vs_rank_latency_jrc_definitions_zero_shot.pdf)
- original_glm/output_tokens_vs_rank_latency_google_patents_few_shot: [PNG](original_glm/output_tokens_vs_rank_latency_google_patents_few_shot.png) | [PDF](original_glm/output_tokens_vs_rank_latency_google_patents_few_shot.pdf)
- original_glm/output_tokens_vs_rank_latency_google_patents_zero_shot: [PNG](original_glm/output_tokens_vs_rank_latency_google_patents_zero_shot.png) | [PDF](original_glm/output_tokens_vs_rank_latency_google_patents_zero_shot.pdf)
- original_glm/output_tokens_vs_rank_latency_jrc_articles_few_shot: [PNG](original_glm/output_tokens_vs_rank_latency_jrc_articles_few_shot.png) | [PDF](original_glm/output_tokens_vs_rank_latency_jrc_articles_few_shot.pdf)
- original_glm/output_tokens_vs_rank_latency_jrc_articles_zero_shot: [PNG](original_glm/output_tokens_vs_rank_latency_jrc_articles_zero_shot.png) | [PDF](original_glm/output_tokens_vs_rank_latency_jrc_articles_zero_shot.pdf)
- original_glm/output_tokens_vs_rank_latency_jrc_definitions_few_shot: [PNG](original_glm/output_tokens_vs_rank_latency_jrc_definitions_few_shot.png) | [PDF](original_glm/output_tokens_vs_rank_latency_jrc_definitions_few_shot.pdf)
- original_glm/output_tokens_vs_rank_latency_jrc_definitions_zero_shot: [PNG](original_glm/output_tokens_vs_rank_latency_jrc_definitions_zero_shot.png) | [PDF](original_glm/output_tokens_vs_rank_latency_jrc_definitions_zero_shot.pdf)
