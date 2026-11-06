# API Cost Estimates

Published rate snapshot checked on 2026-11-03. Currency: USD.

These are counterfactual recorded-token repricing scenarios, not invoices, actual local-GPU costs, or proof of identical results if hosted elsewhere. NA means no verified matching price in the sources checked, never free inference.

## Reference Scenario: No Cache Discount

Cost = input tokens / 1,000,000 * input price + output tokens / 1,000,000 * output price.

Token totals are summed across the three datasets and both prompts, once only. They are not multiplied by annotation views or terminology groups.

| Model | Input Tokens (M) | Output Tokens (M) | Input $/M | Output $/M | Input Cost | Output Cost | Total USD |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Gemma 4 31B | 152.50 | 36.53 | 0.20 | 0.40 | 30.50 | 14.61 | 45.11 |
| GPT-6 Luna | 150.93 | 36.12 | 0.10 | 0.50 | 15.09 | 18.06 | 33.15 |
| Granite 4.2 30B | 179.81 | 43.53 | NA | NA | NA | NA | NA |
| Muse Glimmer 30B | 145.46 | 40.56 | 0.30 | 1.20 | 43.64 | 48.68 | 92.31 |
| Nemotron 3.5 Lightning | 160.80 | 38.07 | 0.07 | 0.20 | 11.26 | 7.61 | 18.87 |
| Qwen3.8 27B | 155.38 | 37.09 | 0.15 | 1.88 | 23.31 | 69.54 | 92.85 |
| Tiny Aya Global | 168.90 | 39.30 | NA | NA | NA | NA | NA |

Rates in the CSV retain full precision; displayed monetary amounts are rounded. The reference GPT-6 Luna price assumes Azure Standard Global short context. Other priced models use the OpenRouter catalog quote, not the original deployment or necessarily the cheapest routed provider.

## Azure Scenario Sensitivity

Actual deployment geography and per-request context bands are not established. The alternatives below reprice all recorded tokens at each listed rate; they do not classify individual requests by context length.

| Model | Scenario | Input Cost USD | Output Cost USD | Total USD |
| --- | --- | ---: | ---: | ---: |
| GPT-6 Luna | GPT-6 Luna Standard Global short context | 15.09 | 18.06 | 33.15 |
| GPT-6 Luna | Azure Standard Data Zone short context | 16.60 | 19.87 | 36.47 |
| GPT-6 Luna | Azure Standard Global long context | 30.19 | 27.09 | 57.27 |
| GPT-6 Luna | Azure Standard Data Zone long context | 33.20 | 29.80 | 63.00 |

## Assumptions and Limits

- Published current list prices, not historical invoices or negotiated prices.
- All recorded input tokens are charged at the normal input rate; local prefix-cache hits are not assumed portable to hosted billing.
- No separate billable cache-write operations, tools, per-request charges, taxes, platform-credit fees or discounts are assumed.
- Token totals are reused as recorded; hosted replay, identical tokenization, output length, precision and checkpoint weights are not established.
- Azure Global short-context Standard is a reference scenario, not a verified deployment configuration.
- OpenRouter catalog quotes are routing-dependent, not a cheapest-provider search or a quote for the original local deployment.
- Recorded cached-token counts are exported but not deducted in the reference scenario. Cache-read list rates are retained for audit only; zero assumed billed cached tokens does not mean that no local cache was used.
- Reasoning tokens are retained as metadata and not added again to output tokens. The current translation summaries report zero reasoning tokens.
- Token totals and covered requests differ slightly between models. The CSV includes per-dataset/prompt values and cost per 1,000 recorded requests; this does not establish row-matched workloads.
- Granite 4.2 30B and the four Tiny Aya variants remain unpriced. Aya Expanse, Granite 4.2 8B, free tiers, and different Qwen/Nemotron variants were not substituted for the recorded models.

## Sources

- https://azure.microsoft.com/en-us/pricing/details/cognitive-services/openai-service/
- https://openai.com/api/pricing/
- https://openrouter.ai/api/v1/models
- https://cohere.com/pricing

[Detailed cost and usage CSV](tables/api_cost_estimates.csv)

Reproduce with the pinned snapshot:

```powershell
uv run --no-sync python scripts/render_evaluation_results.py --api-costs-only
```
