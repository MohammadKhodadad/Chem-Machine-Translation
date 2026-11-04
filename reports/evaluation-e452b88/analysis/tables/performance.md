# Benchmark Performance Tables

Descriptive direction-macro scores on directions shared by all ten current runs and both prompt settings within each metric/dataset/view/subset. NA means no common scored support, never zero. Counts are in the CSV files. Different rows may still contain different translation examples. No significance claims.

## Chemical Patents / zero shot / shared_general / not_applicable

BLEU: 24 directions; chrF: 24 directions; chrF++: 24 directions; BERTScore F1: 24 directions; BLEURT: 24 directions; COMET: 24 directions; COMETKiwi-QE: 24 directions; XCOMET-XL: 24 directions; Sequence Similarity: 24 directions

| Model | BLEU | chrF | chrF++ | BERTScore F1 | BLEURT | COMET | COMETKiwi-QE | XCOMET-XL | Sequence Similarity |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Gemma 4 31B | 44.52 | 67.96 | 64.69 | 0.940 | 0.567 | 0.851 | 0.599 | 0.247 | 40.472 |
| GPT-6 Luna | 41.78 | 67.62 | 63.72 | 0.941 | 0.576 | 0.858 | 0.614 | 0.252 | 39.714 |
| Granite 4.2 30B | 35.20 | 61.91 | 58.11 | 0.930 | 0.533 | 0.844 | 0.604 | 0.245 | 32.985 |
| Muse Glimmer 30B | 43.51 | 68.05 | 64.35 | 0.939 | 0.547 | 0.846 | 0.590 | 0.246 | 40.150 |
| Nemotron 3.5 Lightning | 36.60 | 62.14 | 58.35 | 0.929 | 0.521 | 0.835 | 0.584 | 0.241 | 34.195 |
| Qwen3.8 27B | 40.87 | 67.58 | 63.55 | 0.938 | 0.562 | 0.852 | 0.606 | 0.248 | 39.203 |
| Tiny Aya Earth | 33.10 | 58.24 | 54.86 | 0.924 | 0.514 | 0.832 | 0.595 | 0.238 | 30.543 |
| Tiny Aya Fire | 33.39 | 59.09 | 55.54 | 0.925 | 0.518 | 0.834 | 0.596 | 0.237 | 31.623 |
| Tiny Aya Global | 32.57 | 58.07 | 54.64 | 0.924 | 0.514 | 0.831 | 0.598 | 0.237 | 30.926 |
| Tiny Aya Water | 32.83 | 58.31 | 54.84 | 0.924 | 0.516 | 0.832 | 0.599 | 0.238 | 30.804 |

## Chemical Patents / few shot / shared_general / not_applicable

BLEU: 24 directions; chrF: 24 directions; chrF++: 24 directions; BERTScore F1: 24 directions; BLEURT: 24 directions; COMET: 24 directions; COMETKiwi-QE: 24 directions; XCOMET-XL: 24 directions; Sequence Similarity: 24 directions

| Model | BLEU | chrF | chrF++ | BERTScore F1 | BLEURT | COMET | COMETKiwi-QE | XCOMET-XL | Sequence Similarity |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Gemma 4 31B | 44.91 | 69.64 | 66.06 | 0.941 | 0.572 | 0.855 | 0.604 | 0.251 | 42.174 |
| GPT-6 Luna | 43.06 | 69.31 | 65.76 | 0.942 | 0.579 | 0.860 | 0.616 | 0.253 | 41.604 |
| Granite 4.2 30B | 38.21 | 63.46 | 60.23 | 0.932 | 0.539 | 0.845 | 0.599 | 0.244 | 35.270 |
| Muse Glimmer 30B | 46.16 | 70.74 | 67.30 | 0.944 | 0.577 | 0.858 | 0.594 | 0.250 | 44.721 |
| Nemotron 3.5 Lightning | 41.20 | 65.33 | 62.40 | 0.935 | 0.542 | 0.848 | 0.585 | 0.241 | 37.870 |
| Qwen3.8 27B | 44.11 | 69.42 | 65.85 | 0.941 | 0.570 | 0.855 | 0.603 | 0.247 | 41.870 |
| Tiny Aya Earth | 35.08 | 57.56 | 54.99 | 0.922 | 0.521 | 0.826 | 0.586 | 0.239 | 32.044 |
| Tiny Aya Fire | 34.51 | 57.48 | 54.79 | 0.924 | 0.520 | 0.829 | 0.591 | 0.237 | 31.681 |
| Tiny Aya Global | 35.50 | 58.18 | 55.60 | 0.923 | 0.525 | 0.830 | 0.588 | 0.244 | 32.607 |
| Tiny Aya Water | 35.86 | 58.82 | 56.16 | 0.924 | 0.529 | 0.833 | 0.591 | 0.245 | 33.123 |

## JRC Articles / zero shot / shared_general / not_applicable

BLEU: 20 directions; chrF: 20 directions; chrF++: 20 directions; BERTScore F1: 20 directions; BLEURT: 20 directions; COMET: 20 directions; COMETKiwi-QE: 20 directions; XCOMET-XL: 20 directions; Sequence Similarity: 20 directions

| Model | BLEU | chrF | chrF++ | BERTScore F1 | BLEURT | COMET | COMETKiwi-QE | XCOMET-XL | Sequence Similarity |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Gemma 4 31B | 61.95 | 79.51 | 77.55 | 0.955 | 0.561 | 0.896 | 0.583 | 0.187 | 61.648 |
| GPT-6 Luna | 69.74 | 84.41 | 82.71 | 0.967 | 0.628 | 0.903 | 0.590 | 0.188 | 70.295 |
| Granite 4.2 30B | 54.05 | 74.64 | 72.36 | 0.947 | 0.502 | 0.888 | 0.573 | 0.186 | 54.565 |
| Muse Glimmer 30B | 63.23 | 79.65 | 77.83 | 0.957 | 0.573 | 0.888 | 0.581 | 0.187 | 63.989 |
| Nemotron 3.5 Lightning | 52.57 | 73.83 | 71.64 | 0.946 | 0.496 | 0.884 | 0.556 | 0.185 | 55.234 |
| Qwen3.8 27B | 63.67 | 80.54 | 78.77 | 0.959 | 0.582 | 0.897 | 0.588 | 0.188 | 64.105 |
| Tiny Aya Earth | 49.12 | 71.38 | 69.28 | 0.943 | 0.487 | 0.883 | 0.568 | 0.184 | 51.781 |
| Tiny Aya Fire | 50.68 | 72.36 | 70.30 | 0.943 | 0.497 | 0.883 | 0.570 | 0.186 | 52.566 |
| Tiny Aya Global | 50.52 | 71.47 | 69.43 | 0.944 | 0.492 | 0.884 | 0.572 | 0.185 | 51.882 |
| Tiny Aya Water | 48.62 | 70.92 | 68.85 | 0.943 | 0.488 | 0.883 | 0.571 | 0.184 | 51.695 |

## JRC Articles / few shot / shared_general / not_applicable

BLEU: 20 directions; chrF: 20 directions; chrF++: 20 directions; BERTScore F1: 20 directions; BLEURT: 20 directions; COMET: 20 directions; COMETKiwi-QE: 20 directions; XCOMET-XL: 20 directions; Sequence Similarity: 20 directions

| Model | BLEU | chrF | chrF++ | BERTScore F1 | BLEURT | COMET | COMETKiwi-QE | XCOMET-XL | Sequence Similarity |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Gemma 4 31B | 72.39 | 84.28 | 82.98 | 0.967 | 0.626 | 0.902 | 0.580 | 0.186 | 70.982 |
| GPT-6 Luna | 74.81 | 86.44 | 85.08 | 0.971 | 0.651 | 0.906 | 0.586 | 0.187 | 74.102 |
| Granite 4.2 30B | 66.65 | 80.92 | 79.39 | 0.961 | 0.596 | 0.898 | 0.577 | 0.185 | 66.549 |
| Muse Glimmer 30B | 73.98 | 85.15 | 83.96 | 0.968 | 0.635 | 0.903 | 0.577 | 0.186 | 72.701 |
| Nemotron 3.5 Lightning | 67.63 | 81.05 | 79.64 | 0.962 | 0.597 | 0.896 | 0.568 | 0.185 | 66.909 |
| Qwen3.8 27B | 73.32 | 84.81 | 83.64 | 0.968 | 0.630 | 0.902 | 0.579 | 0.185 | 72.069 |
| Tiny Aya Earth | 59.00 | 75.88 | 74.33 | 0.953 | 0.560 | 0.883 | 0.565 | 0.183 | 60.209 |
| Tiny Aya Fire | 59.77 | 76.54 | 75.06 | 0.954 | 0.566 | 0.884 | 0.565 | 0.183 | 61.144 |
| Tiny Aya Global | 58.57 | 75.21 | 73.64 | 0.951 | 0.557 | 0.881 | 0.562 | 0.183 | 59.690 |
| Tiny Aya Water | 58.72 | 75.68 | 74.12 | 0.952 | 0.562 | 0.882 | 0.564 | 0.182 | 60.031 |

## JRC Definitions / zero shot / shared_general / not_applicable

BLEU: 20 directions; chrF: 20 directions; chrF++: 20 directions; BERTScore F1: 20 directions; BLEURT: 20 directions; COMET: 20 directions; COMETKiwi-QE: 20 directions; XCOMET-XL: 20 directions; Sequence Similarity: 20 directions

| Model | BLEU | chrF | chrF++ | BERTScore F1 | BLEURT | COMET | COMETKiwi-QE | XCOMET-XL | Sequence Similarity |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Gemma 4 31B | 45.93 | 74.51 | 71.49 | 0.942 | 0.520 | 0.893 | 0.642 | 0.200 | 33.962 |
| GPT-6 Luna | 51.57 | 77.86 | 75.00 | 0.950 | 0.566 | 0.900 | 0.651 | 0.201 | 38.499 |
| Granite 4.2 30B | 40.27 | 70.63 | 67.42 | 0.935 | 0.478 | 0.884 | 0.628 | 0.199 | 29.376 |
| Muse Glimmer 30B | 44.30 | 73.21 | 70.18 | 0.940 | 0.513 | 0.881 | 0.632 | 0.200 | 33.115 |
| Nemotron 3.5 Lightning | 37.48 | 68.25 | 64.88 | 0.931 | 0.453 | 0.871 | 0.601 | 0.198 | 27.923 |
| Qwen3.8 27B | 44.82 | 73.72 | 70.68 | 0.942 | 0.517 | 0.892 | 0.644 | 0.199 | 33.606 |
| Tiny Aya Earth | 35.62 | 66.73 | 63.62 | 0.929 | 0.457 | 0.873 | 0.624 | 0.197 | 26.813 |
| Tiny Aya Fire | 37.04 | 67.78 | 64.70 | 0.931 | 0.464 | 0.877 | 0.625 | 0.198 | 27.302 |
| Tiny Aya Global | 35.14 | 66.23 | 63.11 | 0.928 | 0.452 | 0.871 | 0.623 | 0.196 | 26.332 |
| Tiny Aya Water | 35.88 | 66.70 | 63.58 | 0.929 | 0.454 | 0.873 | 0.625 | 0.198 | 26.595 |

## JRC Definitions / few shot / shared_general / not_applicable

BLEU: 20 directions; chrF: 20 directions; chrF++: 20 directions; BERTScore F1: 20 directions; BLEURT: 20 directions; COMET: 20 directions; COMETKiwi-QE: 20 directions; XCOMET-XL: 20 directions; Sequence Similarity: 20 directions

| Model | BLEU | chrF | chrF++ | BERTScore F1 | BLEURT | COMET | COMETKiwi-QE | XCOMET-XL | Sequence Similarity |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Gemma 4 31B | 48.78 | 75.69 | 72.88 | 0.946 | 0.537 | 0.898 | 0.646 | 0.200 | 35.882 |
| GPT-6 Luna | 54.25 | 78.86 | 76.22 | 0.952 | 0.577 | 0.902 | 0.653 | 0.200 | 40.274 |
| Granite 4.2 30B | 43.36 | 71.89 | 68.93 | 0.939 | 0.499 | 0.889 | 0.634 | 0.199 | 31.426 |
| Muse Glimmer 30B | 50.29 | 76.42 | 73.73 | 0.947 | 0.543 | 0.897 | 0.638 | 0.199 | 37.323 |
| Nemotron 3.5 Lightning | 41.67 | 69.89 | 66.92 | 0.934 | 0.474 | 0.877 | 0.611 | 0.198 | 30.624 |
| Qwen3.8 27B | 48.62 | 75.35 | 72.68 | 0.945 | 0.532 | 0.896 | 0.646 | 0.199 | 36.155 |
| Tiny Aya Earth | 33.80 | 62.10 | 59.19 | 0.922 | 0.441 | 0.852 | 0.620 | 0.195 | 25.434 |
| Tiny Aya Fire | 34.26 | 62.82 | 59.94 | 0.924 | 0.446 | 0.854 | 0.620 | 0.195 | 25.964 |
| Tiny Aya Global | 32.56 | 60.90 | 57.96 | 0.920 | 0.431 | 0.844 | 0.615 | 0.194 | 24.704 |
| Tiny Aya Water | 33.96 | 62.20 | 59.29 | 0.922 | 0.439 | 0.851 | 0.619 | 0.196 | 25.411 |

## Chemical Patents / zero shot / original_glm / all_terms

Target-Term Coverage: 12 directions; Variant-Aware Coverage: 12 directions; Term BERTScore Recall: 12 directions; Terminology Success Rate: 0 directions; Variant-Aware Success Rate: 0 directions

| Model | Target-Term Coverage | Variant-Aware Coverage | Term BERTScore Recall | Terminology Success Rate | Variant-Aware Success Rate |
| --- | --- | --- | --- | --- | --- |
| Gemma 4 31B | 53.58 | 54.55 | 0.869 | NA | NA |
| GPT-6 Luna | 53.44 | 54.41 | 0.870 | NA | NA |
| Granite 4.2 30B | 37.24 | 38.21 | 0.863 | NA | NA |
| Muse Glimmer 30B | 52.18 | 53.14 | 0.869 | NA | NA |
| Nemotron 3.5 Lightning | 37.80 | 38.78 | 0.862 | NA | NA |
| Qwen3.8 27B | 48.93 | 49.90 | 0.867 | NA | NA |
| Tiny Aya Earth | 33.33 | 34.31 | 0.859 | NA | NA |
| Tiny Aya Fire | 34.28 | 35.26 | 0.860 | NA | NA |
| Tiny Aya Global | 33.76 | 34.74 | 0.860 | NA | NA |
| Tiny Aya Water | 34.15 | 35.12 | 0.860 | NA | NA |

## Chemical Patents / few shot / original_glm / all_terms

Target-Term Coverage: 12 directions; Variant-Aware Coverage: 12 directions; Term BERTScore Recall: 12 directions; Terminology Success Rate: 0 directions; Variant-Aware Success Rate: 0 directions

| Model | Target-Term Coverage | Variant-Aware Coverage | Term BERTScore Recall | Terminology Success Rate | Variant-Aware Success Rate |
| --- | --- | --- | --- | --- | --- |
| Gemma 4 31B | 53.82 | 54.78 | 0.869 | NA | NA |
| GPT-6 Luna | 55.09 | 56.05 | 0.870 | NA | NA |
| Granite 4.2 30B | 38.63 | 39.59 | 0.863 | NA | NA |
| Muse Glimmer 30B | 56.09 | 57.05 | 0.871 | NA | NA |
| Nemotron 3.5 Lightning | 42.57 | 43.54 | 0.866 | NA | NA |
| Qwen3.8 27B | 50.44 | 51.40 | 0.868 | NA | NA |
| Tiny Aya Earth | 34.64 | 35.57 | 0.859 | NA | NA |
| Tiny Aya Fire | 33.40 | 34.34 | 0.859 | NA | NA |
| Tiny Aya Global | 35.94 | 36.88 | 0.861 | NA | NA |
| Tiny Aya Water | 36.65 | 37.58 | 0.862 | NA | NA |

## JRC Articles / zero shot / original_glm / all_terms

Target-Term Coverage: 20 directions; Variant-Aware Coverage: 20 directions; Term BERTScore Recall: 20 directions; Terminology Success Rate: 0 directions; Variant-Aware Success Rate: 0 directions

| Model | Target-Term Coverage | Variant-Aware Coverage | Term BERTScore Recall | Terminology Success Rate | Variant-Aware Success Rate |
| --- | --- | --- | --- | --- | --- |
| Gemma 4 31B | 57.61 | 57.97 | 0.841 | NA | NA |
| GPT-6 Luna | 70.94 | 71.15 | 0.845 | NA | NA |
| Granite 4.2 30B | 46.34 | 46.72 | 0.837 | NA | NA |
| Muse Glimmer 30B | 61.71 | 62.02 | 0.841 | NA | NA |
| Nemotron 3.5 Lightning | 46.36 | 46.99 | 0.838 | NA | NA |
| Qwen3.8 27B | 59.09 | 59.37 | 0.842 | NA | NA |
| Tiny Aya Earth | 43.11 | 43.57 | 0.836 | NA | NA |
| Tiny Aya Fire | 44.78 | 45.23 | 0.836 | NA | NA |
| Tiny Aya Global | 42.86 | 43.34 | 0.836 | NA | NA |
| Tiny Aya Water | 42.80 | 43.26 | 0.836 | NA | NA |

## JRC Articles / few shot / original_glm / all_terms

Target-Term Coverage: 20 directions; Variant-Aware Coverage: 20 directions; Term BERTScore Recall: 20 directions; Terminology Success Rate: 0 directions; Variant-Aware Success Rate: 0 directions

| Model | Target-Term Coverage | Variant-Aware Coverage | Term BERTScore Recall | Terminology Success Rate | Variant-Aware Success Rate |
| --- | --- | --- | --- | --- | --- |
| Gemma 4 31B | 71.99 | 72.31 | 0.844 | NA | NA |
| GPT-6 Luna | 76.50 | 76.71 | 0.846 | NA | NA |
| Granite 4.2 30B | 65.43 | 65.75 | 0.843 | NA | NA |
| Muse Glimmer 30B | 73.26 | 73.52 | 0.845 | NA | NA |
| Nemotron 3.5 Lightning | 65.51 | 65.81 | 0.843 | NA | NA |
| Qwen3.8 27B | 72.77 | 73.03 | 0.844 | NA | NA |
| Tiny Aya Earth | 59.10 | 59.37 | 0.840 | NA | NA |
| Tiny Aya Fire | 60.35 | 60.62 | 0.840 | NA | NA |
| Tiny Aya Global | 58.18 | 58.44 | 0.840 | NA | NA |
| Tiny Aya Water | 58.93 | 59.20 | 0.840 | NA | NA |

## JRC Definitions / zero shot / original_glm / all_terms

Target-Term Coverage: 20 directions; Variant-Aware Coverage: 20 directions; Term BERTScore Recall: 20 directions; Terminology Success Rate: 0 directions; Variant-Aware Success Rate: 0 directions

| Model | Target-Term Coverage | Variant-Aware Coverage | Term BERTScore Recall | Terminology Success Rate | Variant-Aware Success Rate |
| --- | --- | --- | --- | --- | --- |
| Gemma 4 31B | 46.74 | 47.25 | 0.839 | NA | NA |
| GPT-6 Luna | 54.58 | 55.08 | 0.842 | NA | NA |
| Granite 4.2 30B | 38.68 | 39.12 | 0.836 | NA | NA |
| Muse Glimmer 30B | 46.96 | 47.42 | 0.838 | NA | NA |
| Nemotron 3.5 Lightning | 36.33 | 36.81 | 0.835 | NA | NA |
| Qwen3.8 27B | 44.81 | 45.32 | 0.838 | NA | NA |
| Tiny Aya Earth | 35.13 | 35.63 | 0.833 | NA | NA |
| Tiny Aya Fire | 36.18 | 36.66 | 0.834 | NA | NA |
| Tiny Aya Global | 34.60 | 35.09 | 0.833 | NA | NA |
| Tiny Aya Water | 34.94 | 35.43 | 0.833 | NA | NA |

## JRC Definitions / few shot / original_glm / all_terms

Target-Term Coverage: 20 directions; Variant-Aware Coverage: 20 directions; Term BERTScore Recall: 20 directions; Terminology Success Rate: 0 directions; Variant-Aware Success Rate: 0 directions

| Model | Target-Term Coverage | Variant-Aware Coverage | Term BERTScore Recall | Terminology Success Rate | Variant-Aware Success Rate |
| --- | --- | --- | --- | --- | --- |
| Gemma 4 31B | 48.71 | 49.15 | 0.840 | NA | NA |
| GPT-6 Luna | 56.74 | 57.15 | 0.843 | NA | NA |
| Granite 4.2 30B | 40.79 | 41.22 | 0.837 | NA | NA |
| Muse Glimmer 30B | 50.64 | 51.04 | 0.841 | NA | NA |
| Nemotron 3.5 Lightning | 39.92 | 40.31 | 0.836 | NA | NA |
| Qwen3.8 27B | 47.45 | 47.88 | 0.839 | NA | NA |
| Tiny Aya Earth | 32.21 | 32.58 | 0.831 | NA | NA |
| Tiny Aya Fire | 33.21 | 33.58 | 0.831 | NA | NA |
| Tiny Aya Global | 30.79 | 31.15 | 0.830 | NA | NA |
| Tiny Aya Water | 32.16 | 32.53 | 0.831 | NA | NA |

## Chemical Patents / zero shot / original_glm / externally_verified

Target-Term Coverage: 12 directions; Variant-Aware Coverage: 12 directions; Term BERTScore Recall: 12 directions; Terminology Success Rate: 0 directions; Variant-Aware Success Rate: 0 directions

| Model | Target-Term Coverage | Variant-Aware Coverage | Term BERTScore Recall | Terminology Success Rate | Variant-Aware Success Rate |
| --- | --- | --- | --- | --- | --- |
| Gemma 4 31B | 77.86 | 87.57 | 0.835 | NA | NA |
| GPT-6 Luna | 76.35 | 86.08 | 0.835 | NA | NA |
| Granite 4.2 30B | 69.92 | 79.76 | 0.833 | NA | NA |
| Muse Glimmer 30B | 77.31 | 86.95 | 0.835 | NA | NA |
| Nemotron 3.5 Lightning | 70.09 | 79.86 | 0.833 | NA | NA |
| Qwen3.8 27B | 74.92 | 84.67 | 0.834 | NA | NA |
| Tiny Aya Earth | 67.10 | 76.87 | 0.832 | NA | NA |
| Tiny Aya Fire | 66.62 | 76.32 | 0.832 | NA | NA |
| Tiny Aya Global | 66.15 | 75.91 | 0.832 | NA | NA |
| Tiny Aya Water | 66.31 | 76.07 | 0.832 | NA | NA |

## Chemical Patents / few shot / original_glm / externally_verified

Target-Term Coverage: 12 directions; Variant-Aware Coverage: 12 directions; Term BERTScore Recall: 12 directions; Terminology Success Rate: 0 directions; Variant-Aware Success Rate: 0 directions

| Model | Target-Term Coverage | Variant-Aware Coverage | Term BERTScore Recall | Terminology Success Rate | Variant-Aware Success Rate |
| --- | --- | --- | --- | --- | --- |
| Gemma 4 31B | 77.45 | 87.14 | 0.835 | NA | NA |
| GPT-6 Luna | 77.06 | 86.76 | 0.835 | NA | NA |
| Granite 4.2 30B | 70.22 | 79.97 | 0.833 | NA | NA |
| Muse Glimmer 30B | 77.48 | 87.13 | 0.835 | NA | NA |
| Nemotron 3.5 Lightning | 70.84 | 80.42 | 0.833 | NA | NA |
| Qwen3.8 27B | 75.61 | 85.25 | 0.834 | NA | NA |
| Tiny Aya Earth | 58.93 | 68.58 | 0.831 | NA | NA |
| Tiny Aya Fire | 60.66 | 70.28 | 0.831 | NA | NA |
| Tiny Aya Global | 57.81 | 67.46 | 0.830 | NA | NA |
| Tiny Aya Water | 58.83 | 68.42 | 0.831 | NA | NA |

## JRC Articles / zero shot / original_glm / externally_verified

Target-Term Coverage: 20 directions; Variant-Aware Coverage: 20 directions; Term BERTScore Recall: 20 directions; Terminology Success Rate: 0 directions; Variant-Aware Success Rate: 0 directions

| Model | Target-Term Coverage | Variant-Aware Coverage | Term BERTScore Recall | Terminology Success Rate | Variant-Aware Success Rate |
| --- | --- | --- | --- | --- | --- |
| Gemma 4 31B | 71.66 | 73.10 | 0.866 | NA | NA |
| GPT-6 Luna | 82.54 | 83.33 | 0.870 | NA | NA |
| Granite 4.2 30B | 57.92 | 59.20 | 0.862 | NA | NA |
| Muse Glimmer 30B | 74.14 | 75.20 | 0.866 | NA | NA |
| Nemotron 3.5 Lightning | 59.06 | 60.80 | 0.863 | NA | NA |
| Qwen3.8 27B | 71.64 | 72.70 | 0.867 | NA | NA |
| Tiny Aya Earth | 55.71 | 57.11 | 0.861 | NA | NA |
| Tiny Aya Fire | 56.59 | 57.99 | 0.861 | NA | NA |
| Tiny Aya Global | 55.13 | 56.65 | 0.861 | NA | NA |
| Tiny Aya Water | 55.36 | 56.77 | 0.861 | NA | NA |

## JRC Articles / few shot / original_glm / externally_verified

Target-Term Coverage: 20 directions; Variant-Aware Coverage: 20 directions; Term BERTScore Recall: 20 directions; Terminology Success Rate: 0 directions; Variant-Aware Success Rate: 0 directions

| Model | Target-Term Coverage | Variant-Aware Coverage | Term BERTScore Recall | Terminology Success Rate | Variant-Aware Success Rate |
| --- | --- | --- | --- | --- | --- |
| Gemma 4 31B | 82.49 | 83.60 | 0.870 | NA | NA |
| GPT-6 Luna | 85.84 | 86.54 | 0.871 | NA | NA |
| Granite 4.2 30B | 76.97 | 78.08 | 0.868 | NA | NA |
| Muse Glimmer 30B | 82.89 | 83.75 | 0.870 | NA | NA |
| Nemotron 3.5 Lightning | 76.73 | 77.73 | 0.868 | NA | NA |
| Qwen3.8 27B | 83.67 | 84.56 | 0.869 | NA | NA |
| Tiny Aya Earth | 70.94 | 71.90 | 0.866 | NA | NA |
| Tiny Aya Fire | 72.66 | 73.63 | 0.867 | NA | NA |
| Tiny Aya Global | 70.57 | 71.52 | 0.866 | NA | NA |
| Tiny Aya Water | 71.01 | 71.98 | 0.866 | NA | NA |

## JRC Definitions / zero shot / original_glm / externally_verified

Target-Term Coverage: 20 directions; Variant-Aware Coverage: 20 directions; Term BERTScore Recall: 20 directions; Terminology Success Rate: 0 directions; Variant-Aware Success Rate: 0 directions

| Model | Target-Term Coverage | Variant-Aware Coverage | Term BERTScore Recall | Terminology Success Rate | Variant-Aware Success Rate |
| --- | --- | --- | --- | --- | --- |
| Gemma 4 31B | 69.38 | 71.20 | 0.865 | NA | NA |
| GPT-6 Luna | 79.07 | 80.89 | 0.868 | NA | NA |
| Granite 4.2 30B | 60.58 | 62.21 | 0.862 | NA | NA |
| Muse Glimmer 30B | 70.50 | 72.20 | 0.863 | NA | NA |
| Nemotron 3.5 Lightning | 57.25 | 59.02 | 0.861 | NA | NA |
| Qwen3.8 27B | 67.48 | 69.34 | 0.864 | NA | NA |
| Tiny Aya Earth | 55.14 | 57.00 | 0.859 | NA | NA |
| Tiny Aya Fire | 56.89 | 58.60 | 0.860 | NA | NA |
| Tiny Aya Global | 54.39 | 56.24 | 0.858 | NA | NA |
| Tiny Aya Water | 54.97 | 56.83 | 0.859 | NA | NA |

## JRC Definitions / few shot / original_glm / externally_verified

Target-Term Coverage: 20 directions; Variant-Aware Coverage: 20 directions; Term BERTScore Recall: 20 directions; Terminology Success Rate: 0 directions; Variant-Aware Success Rate: 0 directions

| Model | Target-Term Coverage | Variant-Aware Coverage | Term BERTScore Recall | Terminology Success Rate | Variant-Aware Success Rate |
| --- | --- | --- | --- | --- | --- |
| Gemma 4 31B | 71.62 | 73.18 | 0.866 | NA | NA |
| GPT-6 Luna | 80.67 | 82.12 | 0.868 | NA | NA |
| Granite 4.2 30B | 62.54 | 64.10 | 0.863 | NA | NA |
| Muse Glimmer 30B | 74.13 | 75.59 | 0.866 | NA | NA |
| Nemotron 3.5 Lightning | 60.84 | 62.26 | 0.862 | NA | NA |
| Qwen3.8 27B | 70.06 | 71.61 | 0.865 | NA | NA |
| Tiny Aya Earth | 49.92 | 51.24 | 0.857 | NA | NA |
| Tiny Aya Fire | 51.65 | 52.97 | 0.857 | NA | NA |
| Tiny Aya Global | 47.49 | 48.77 | 0.856 | NA | NA |
| Tiny Aya Water | 49.93 | 51.27 | 0.857 | NA | NA |

## Chemical Patents / zero shot / original_glm / llm_enriched

Target-Term Coverage: 12 directions; Variant-Aware Coverage: 12 directions; Term BERTScore Recall: 12 directions; Terminology Success Rate: 0 directions; Variant-Aware Success Rate: 0 directions

| Model | Target-Term Coverage | Variant-Aware Coverage | Term BERTScore Recall | Terminology Success Rate | Variant-Aware Success Rate |
| --- | --- | --- | --- | --- | --- |
| Gemma 4 31B | 51.10 | 52.17 | 0.873 | NA | NA |
| GPT-6 Luna | 51.39 | 52.46 | 0.874 | NA | NA |
| Granite 4.2 30B | 33.45 | 34.51 | 0.867 | NA | NA |
| Muse Glimmer 30B | 49.68 | 50.73 | 0.873 | NA | NA |
| Nemotron 3.5 Lightning | 34.33 | 35.38 | 0.866 | NA | NA |
| Qwen3.8 27B | 45.98 | 47.03 | 0.872 | NA | NA |
| Tiny Aya Earth | 29.35 | 30.41 | 0.864 | NA | NA |
| Tiny Aya Fire | 30.14 | 31.21 | 0.865 | NA | NA |
| Tiny Aya Global | 29.67 | 30.74 | 0.864 | NA | NA |
| Tiny Aya Water | 30.11 | 31.17 | 0.864 | NA | NA |

## Chemical Patents / few shot / original_glm / llm_enriched

Target-Term Coverage: 12 directions; Variant-Aware Coverage: 12 directions; Term BERTScore Recall: 12 directions; Terminology Success Rate: 0 directions; Variant-Aware Success Rate: 0 directions

| Model | Target-Term Coverage | Variant-Aware Coverage | Term BERTScore Recall | Terminology Success Rate | Variant-Aware Success Rate |
| --- | --- | --- | --- | --- | --- |
| Gemma 4 31B | 51.37 | 52.42 | 0.874 | NA | NA |
| GPT-6 Luna | 53.02 | 54.08 | 0.875 | NA | NA |
| Granite 4.2 30B | 34.63 | 35.69 | 0.867 | NA | NA |
| Muse Glimmer 30B | 53.43 | 54.47 | 0.875 | NA | NA |
| Nemotron 3.5 Lightning | 38.51 | 39.57 | 0.869 | NA | NA |
| Qwen3.8 27B | 47.32 | 48.37 | 0.872 | NA | NA |
| Tiny Aya Earth | 30.74 | 31.76 | 0.864 | NA | NA |
| Tiny Aya Fire | 29.20 | 30.21 | 0.863 | NA | NA |
| Tiny Aya Global | 32.08 | 33.10 | 0.865 | NA | NA |
| Tiny Aya Water | 32.69 | 33.70 | 0.866 | NA | NA |

## JRC Articles / zero shot / original_glm / llm_enriched

Target-Term Coverage: 20 directions; Variant-Aware Coverage: 20 directions; Term BERTScore Recall: 20 directions; Terminology Success Rate: 0 directions; Variant-Aware Success Rate: 0 directions

| Model | Target-Term Coverage | Variant-Aware Coverage | Term BERTScore Recall | Terminology Success Rate | Variant-Aware Success Rate |
| --- | --- | --- | --- | --- | --- |
| Gemma 4 31B | 57.23 | 57.76 | 0.896 | NA | NA |
| GPT-6 Luna | 68.49 | 68.81 | 0.899 | NA | NA |
| Granite 4.2 30B | 42.86 | 43.59 | 0.892 | NA | NA |
| Muse Glimmer 30B | 61.39 | 61.96 | 0.895 | NA | NA |
| Nemotron 3.5 Lightning | 44.02 | 45.50 | 0.892 | NA | NA |
| Qwen3.8 27B | 57.38 | 57.82 | 0.896 | NA | NA |
| Tiny Aya Earth | 40.65 | 41.72 | 0.890 | NA | NA |
| Tiny Aya Fire | 43.07 | 44.11 | 0.890 | NA | NA |
| Tiny Aya Global | 40.47 | 41.52 | 0.891 | NA | NA |
| Tiny Aya Water | 39.88 | 40.96 | 0.890 | NA | NA |

## JRC Articles / few shot / original_glm / llm_enriched

Target-Term Coverage: 20 directions; Variant-Aware Coverage: 20 directions; Term BERTScore Recall: 20 directions; Terminology Success Rate: 0 directions; Variant-Aware Success Rate: 0 directions

| Model | Target-Term Coverage | Variant-Aware Coverage | Term BERTScore Recall | Terminology Success Rate | Variant-Aware Success Rate |
| --- | --- | --- | --- | --- | --- |
| Gemma 4 31B | 78.06 | 78.81 | 0.899 | NA | NA |
| GPT-6 Luna | 77.83 | 78.28 | 0.901 | NA | NA |
| Granite 4.2 30B | 69.76 | 70.43 | 0.898 | NA | NA |
| Muse Glimmer 30B | 78.02 | 78.59 | 0.900 | NA | NA |
| Nemotron 3.5 Lightning | 69.76 | 70.39 | 0.898 | NA | NA |
| Qwen3.8 27B | 79.42 | 79.98 | 0.899 | NA | NA |
| Tiny Aya Earth | 63.96 | 64.51 | 0.896 | NA | NA |
| Tiny Aya Fire | 65.61 | 66.21 | 0.896 | NA | NA |
| Tiny Aya Global | 63.17 | 63.73 | 0.895 | NA | NA |
| Tiny Aya Water | 64.07 | 64.61 | 0.896 | NA | NA |

## JRC Definitions / zero shot / original_glm / llm_enriched

Target-Term Coverage: 20 directions; Variant-Aware Coverage: 20 directions; Term BERTScore Recall: 20 directions; Terminology Success Rate: 0 directions; Variant-Aware Success Rate: 0 directions

| Model | Target-Term Coverage | Variant-Aware Coverage | Term BERTScore Recall | Terminology Success Rate | Variant-Aware Success Rate |
| --- | --- | --- | --- | --- | --- |
| Gemma 4 31B | 58.35 | 59.53 | 0.883 | NA | NA |
| GPT-6 Luna | 67.81 | 68.99 | 0.887 | NA | NA |
| Granite 4.2 30B | 45.86 | 46.82 | 0.880 | NA | NA |
| Muse Glimmer 30B | 59.99 | 61.01 | 0.882 | NA | NA |
| Nemotron 3.5 Lightning | 43.52 | 44.53 | 0.879 | NA | NA |
| Qwen3.8 27B | 55.57 | 56.74 | 0.882 | NA | NA |
| Tiny Aya Earth | 41.58 | 42.61 | 0.877 | NA | NA |
| Tiny Aya Fire | 43.45 | 44.47 | 0.878 | NA | NA |
| Tiny Aya Global | 41.03 | 42.01 | 0.877 | NA | NA |
| Tiny Aya Water | 41.33 | 42.34 | 0.877 | NA | NA |

## JRC Definitions / few shot / original_glm / llm_enriched

Target-Term Coverage: 20 directions; Variant-Aware Coverage: 20 directions; Term BERTScore Recall: 20 directions; Terminology Success Rate: 0 directions; Variant-Aware Success Rate: 0 directions

| Model | Target-Term Coverage | Variant-Aware Coverage | Term BERTScore Recall | Terminology Success Rate | Variant-Aware Success Rate |
| --- | --- | --- | --- | --- | --- |
| Gemma 4 31B | 61.39 | 62.40 | 0.884 | NA | NA |
| GPT-6 Luna | 70.87 | 71.82 | 0.887 | NA | NA |
| Granite 4.2 30B | 50.00 | 50.90 | 0.881 | NA | NA |
| Muse Glimmer 30B | 64.59 | 65.50 | 0.885 | NA | NA |
| Nemotron 3.5 Lightning | 49.56 | 50.40 | 0.880 | NA | NA |
| Qwen3.8 27B | 59.74 | 60.72 | 0.883 | NA | NA |
| Tiny Aya Earth | 38.72 | 39.54 | 0.875 | NA | NA |
| Tiny Aya Fire | 40.32 | 41.13 | 0.875 | NA | NA |
| Tiny Aya Global | 36.52 | 37.30 | 0.873 | NA | NA |
| Tiny Aya Water | 38.36 | 39.18 | 0.874 | NA | NA |

## Chemical Patents / zero shot / luna / all_terms

Target-Term Coverage: 18 directions; Variant-Aware Coverage: 18 directions; Term BERTScore Recall: 18 directions; Terminology Success Rate: 0 directions; Variant-Aware Success Rate: 0 directions

| Model | Target-Term Coverage | Variant-Aware Coverage | Term BERTScore Recall | Terminology Success Rate | Variant-Aware Success Rate |
| --- | --- | --- | --- | --- | --- |
| Gemma 4 31B | 46.72 | 47.05 | 0.852 | NA | NA |
| GPT-6 Luna | 44.91 | 45.25 | 0.852 | NA | NA |
| Granite 4.2 30B | 35.04 | 35.42 | 0.845 | NA | NA |
| Muse Glimmer 30B | 45.92 | 46.25 | 0.852 | NA | NA |
| Nemotron 3.5 Lightning | 35.95 | 36.34 | 0.846 | NA | NA |
| Qwen3.8 27B | 42.88 | 43.23 | 0.849 | NA | NA |
| Tiny Aya Earth | 32.57 | 32.97 | 0.843 | NA | NA |
| Tiny Aya Fire | 33.16 | 33.55 | 0.844 | NA | NA |
| Tiny Aya Global | 32.12 | 32.52 | 0.843 | NA | NA |
| Tiny Aya Water | 32.44 | 32.83 | 0.843 | NA | NA |

## Chemical Patents / few shot / luna / all_terms

Target-Term Coverage: 18 directions; Variant-Aware Coverage: 18 directions; Term BERTScore Recall: 18 directions; Terminology Success Rate: 0 directions; Variant-Aware Success Rate: 0 directions

| Model | Target-Term Coverage | Variant-Aware Coverage | Term BERTScore Recall | Terminology Success Rate | Variant-Aware Success Rate |
| --- | --- | --- | --- | --- | --- |
| Gemma 4 31B | 47.09 | 47.42 | 0.852 | NA | NA |
| GPT-6 Luna | 46.55 | 46.89 | 0.853 | NA | NA |
| Granite 4.2 30B | 36.80 | 37.18 | 0.846 | NA | NA |
| Muse Glimmer 30B | 47.44 | 47.76 | 0.852 | NA | NA |
| Nemotron 3.5 Lightning | 39.08 | 39.44 | 0.849 | NA | NA |
| Qwen3.8 27B | 45.39 | 45.72 | 0.850 | NA | NA |
| Tiny Aya Earth | 32.21 | 32.59 | 0.844 | NA | NA |
| Tiny Aya Fire | 32.90 | 33.29 | 0.844 | NA | NA |
| Tiny Aya Global | 31.55 | 31.94 | 0.843 | NA | NA |
| Tiny Aya Water | 32.16 | 32.54 | 0.843 | NA | NA |

## JRC Articles / zero shot / luna / all_terms

Target-Term Coverage: 20 directions; Variant-Aware Coverage: 20 directions; Term BERTScore Recall: 20 directions; Terminology Success Rate: 0 directions; Variant-Aware Success Rate: 0 directions

| Model | Target-Term Coverage | Variant-Aware Coverage | Term BERTScore Recall | Terminology Success Rate | Variant-Aware Success Rate |
| --- | --- | --- | --- | --- | --- |
| Gemma 4 31B | 63.06 | 64.31 | 0.848 | NA | NA |
| GPT-6 Luna | 74.12 | 75.28 | 0.851 | NA | NA |
| Granite 4.2 30B | 52.97 | 54.45 | 0.844 | NA | NA |
| Muse Glimmer 30B | 66.25 | 67.20 | 0.847 | NA | NA |
| Nemotron 3.5 Lightning | 53.17 | 54.66 | 0.845 | NA | NA |
| Qwen3.8 27B | 64.76 | 65.80 | 0.848 | NA | NA |
| Tiny Aya Earth | 50.09 | 52.11 | 0.843 | NA | NA |
| Tiny Aya Fire | 51.70 | 53.61 | 0.843 | NA | NA |
| Tiny Aya Global | 50.02 | 52.02 | 0.843 | NA | NA |
| Tiny Aya Water | 49.86 | 51.89 | 0.842 | NA | NA |

## JRC Articles / few shot / luna / all_terms

Target-Term Coverage: 20 directions; Variant-Aware Coverage: 20 directions; Term BERTScore Recall: 20 directions; Terminology Success Rate: 0 directions; Variant-Aware Success Rate: 0 directions

| Model | Target-Term Coverage | Variant-Aware Coverage | Term BERTScore Recall | Terminology Success Rate | Variant-Aware Success Rate |
| --- | --- | --- | --- | --- | --- |
| Gemma 4 31B | 74.88 | 75.75 | 0.851 | NA | NA |
| GPT-6 Luna | 78.75 | 79.71 | 0.852 | NA | NA |
| Granite 4.2 30B | 68.95 | 69.91 | 0.849 | NA | NA |
| Muse Glimmer 30B | 76.09 | 76.84 | 0.851 | NA | NA |
| Nemotron 3.5 Lightning | 68.96 | 69.90 | 0.849 | NA | NA |
| Qwen3.8 27B | 75.41 | 76.09 | 0.851 | NA | NA |
| Tiny Aya Earth | 62.51 | 63.73 | 0.846 | NA | NA |
| Tiny Aya Fire | 63.87 | 65.05 | 0.846 | NA | NA |
| Tiny Aya Global | 61.72 | 62.97 | 0.846 | NA | NA |
| Tiny Aya Water | 62.43 | 63.65 | 0.846 | NA | NA |

## JRC Definitions / zero shot / luna / all_terms

Target-Term Coverage: 20 directions; Variant-Aware Coverage: 20 directions; Term BERTScore Recall: 20 directions; Terminology Success Rate: 0 directions; Variant-Aware Success Rate: 0 directions

| Model | Target-Term Coverage | Variant-Aware Coverage | Term BERTScore Recall | Terminology Success Rate | Variant-Aware Success Rate |
| --- | --- | --- | --- | --- | --- |
| Gemma 4 31B | 61.55 | 63.61 | 0.841 | NA | NA |
| GPT-6 Luna | 68.05 | 69.73 | 0.843 | NA | NA |
| Granite 4.2 30B | 53.84 | 56.33 | 0.838 | NA | NA |
| Muse Glimmer 30B | 61.70 | 63.66 | 0.840 | NA | NA |
| Nemotron 3.5 Lightning | 51.00 | 53.62 | 0.837 | NA | NA |
| Qwen3.8 27B | 59.80 | 61.99 | 0.840 | NA | NA |
| Tiny Aya Earth | 50.41 | 53.04 | 0.835 | NA | NA |
| Tiny Aya Fire | 51.65 | 54.23 | 0.836 | NA | NA |
| Tiny Aya Global | 49.78 | 52.44 | 0.835 | NA | NA |
| Tiny Aya Water | 50.20 | 52.84 | 0.835 | NA | NA |

## JRC Definitions / few shot / luna / all_terms

Target-Term Coverage: 20 directions; Variant-Aware Coverage: 20 directions; Term BERTScore Recall: 20 directions; Terminology Success Rate: 0 directions; Variant-Aware Success Rate: 0 directions

| Model | Target-Term Coverage | Variant-Aware Coverage | Term BERTScore Recall | Terminology Success Rate | Variant-Aware Success Rate |
| --- | --- | --- | --- | --- | --- |
| Gemma 4 31B | 63.41 | 65.38 | 0.842 | NA | NA |
| GPT-6 Luna | 69.82 | 71.38 | 0.844 | NA | NA |
| Granite 4.2 30B | 56.12 | 58.48 | 0.839 | NA | NA |
| Muse Glimmer 30B | 65.41 | 67.24 | 0.842 | NA | NA |
| Nemotron 3.5 Lightning | 54.52 | 56.92 | 0.838 | NA | NA |
| Qwen3.8 27B | 62.48 | 64.48 | 0.841 | NA | NA |
| Tiny Aya Earth | 45.92 | 48.51 | 0.833 | NA | NA |
| Tiny Aya Fire | 47.19 | 49.73 | 0.834 | NA | NA |
| Tiny Aya Global | 44.22 | 46.85 | 0.832 | NA | NA |
| Tiny Aya Water | 45.98 | 48.56 | 0.833 | NA | NA |

## Chemical Patents / zero shot / luna / externally_verified

Target-Term Coverage: 17 directions; Variant-Aware Coverage: 17 directions; Term BERTScore Recall: 17 directions; Terminology Success Rate: 0 directions; Variant-Aware Success Rate: 0 directions

| Model | Target-Term Coverage | Variant-Aware Coverage | Term BERTScore Recall | Terminology Success Rate | Variant-Aware Success Rate |
| --- | --- | --- | --- | --- | --- |
| Gemma 4 31B | 81.98 | 84.57 | 0.854 | NA | NA |
| GPT-6 Luna | 79.80 | 82.44 | 0.855 | NA | NA |
| Granite 4.2 30B | 71.84 | 74.93 | 0.853 | NA | NA |
| Muse Glimmer 30B | 81.19 | 83.81 | 0.855 | NA | NA |
| Nemotron 3.5 Lightning | 71.36 | 74.42 | 0.853 | NA | NA |
| Qwen3.8 27B | 78.92 | 81.57 | 0.854 | NA | NA |
| Tiny Aya Earth | 69.87 | 73.07 | 0.852 | NA | NA |
| Tiny Aya Fire | 69.93 | 73.11 | 0.852 | NA | NA |
| Tiny Aya Global | 68.39 | 71.61 | 0.851 | NA | NA |
| Tiny Aya Water | 69.21 | 72.40 | 0.852 | NA | NA |

## Chemical Patents / few shot / luna / externally_verified

Target-Term Coverage: 17 directions; Variant-Aware Coverage: 17 directions; Term BERTScore Recall: 17 directions; Terminology Success Rate: 0 directions; Variant-Aware Success Rate: 0 directions

| Model | Target-Term Coverage | Variant-Aware Coverage | Term BERTScore Recall | Terminology Success Rate | Variant-Aware Success Rate |
| --- | --- | --- | --- | --- | --- |
| Gemma 4 31B | 82.19 | 84.79 | 0.855 | NA | NA |
| GPT-6 Luna | 81.56 | 84.15 | 0.855 | NA | NA |
| Granite 4.2 30B | 73.09 | 76.15 | 0.853 | NA | NA |
| Muse Glimmer 30B | 81.52 | 84.06 | 0.855 | NA | NA |
| Nemotron 3.5 Lightning | 74.04 | 76.95 | 0.853 | NA | NA |
| Qwen3.8 27B | 79.95 | 82.49 | 0.854 | NA | NA |
| Tiny Aya Earth | 67.14 | 70.20 | 0.851 | NA | NA |
| Tiny Aya Fire | 67.84 | 71.10 | 0.851 | NA | NA |
| Tiny Aya Global | 65.74 | 68.95 | 0.851 | NA | NA |
| Tiny Aya Water | 67.37 | 70.47 | 0.851 | NA | NA |

## JRC Articles / zero shot / luna / externally_verified

Target-Term Coverage: 20 directions; Variant-Aware Coverage: 20 directions; Term BERTScore Recall: 20 directions; Terminology Success Rate: 0 directions; Variant-Aware Success Rate: 0 directions

| Model | Target-Term Coverage | Variant-Aware Coverage | Term BERTScore Recall | Terminology Success Rate | Variant-Aware Success Rate |
| --- | --- | --- | --- | --- | --- |
| Gemma 4 31B | 76.31 | 79.64 | 0.841 | NA | NA |
| GPT-6 Luna | 85.64 | 88.36 | 0.844 | NA | NA |
| Granite 4.2 30B | 66.99 | 70.73 | 0.838 | NA | NA |
| Muse Glimmer 30B | 78.92 | 81.52 | 0.841 | NA | NA |
| Nemotron 3.5 Lightning | 67.12 | 70.76 | 0.838 | NA | NA |
| Qwen3.8 27B | 77.94 | 80.83 | 0.842 | NA | NA |
| Tiny Aya Earth | 64.13 | 68.91 | 0.837 | NA | NA |
| Tiny Aya Fire | 64.90 | 69.57 | 0.837 | NA | NA |
| Tiny Aya Global | 63.85 | 68.64 | 0.837 | NA | NA |
| Tiny Aya Water | 63.91 | 68.74 | 0.837 | NA | NA |

## JRC Articles / few shot / luna / externally_verified

Target-Term Coverage: 20 directions; Variant-Aware Coverage: 20 directions; Term BERTScore Recall: 20 directions; Terminology Success Rate: 0 directions; Variant-Aware Success Rate: 0 directions

| Model | Target-Term Coverage | Variant-Aware Coverage | Term BERTScore Recall | Terminology Success Rate | Variant-Aware Success Rate |
| --- | --- | --- | --- | --- | --- |
| Gemma 4 31B | 83.97 | 86.32 | 0.844 | NA | NA |
| GPT-6 Luna | 87.91 | 90.05 | 0.845 | NA | NA |
| Granite 4.2 30B | 79.06 | 81.59 | 0.842 | NA | NA |
| Muse Glimmer 30B | 85.37 | 87.31 | 0.844 | NA | NA |
| Nemotron 3.5 Lightning | 79.28 | 81.87 | 0.843 | NA | NA |
| Qwen3.8 27B | 84.89 | 86.70 | 0.843 | NA | NA |
| Tiny Aya Earth | 73.42 | 76.59 | 0.840 | NA | NA |
| Tiny Aya Fire | 74.63 | 77.72 | 0.841 | NA | NA |
| Tiny Aya Global | 72.78 | 76.04 | 0.840 | NA | NA |
| Tiny Aya Water | 73.34 | 76.54 | 0.840 | NA | NA |

## JRC Definitions / zero shot / luna / externally_verified

Target-Term Coverage: 20 directions; Variant-Aware Coverage: 20 directions; Term BERTScore Recall: 20 directions; Terminology Success Rate: 0 directions; Variant-Aware Success Rate: 0 directions

| Model | Target-Term Coverage | Variant-Aware Coverage | Term BERTScore Recall | Terminology Success Rate | Variant-Aware Success Rate |
| --- | --- | --- | --- | --- | --- |
| Gemma 4 31B | 73.37 | 77.01 | 0.834 | NA | NA |
| GPT-6 Luna | 79.81 | 82.68 | 0.837 | NA | NA |
| Granite 4.2 30B | 66.31 | 70.80 | 0.832 | NA | NA |
| Muse Glimmer 30B | 73.20 | 76.62 | 0.833 | NA | NA |
| Nemotron 3.5 Lightning | 63.06 | 67.83 | 0.831 | NA | NA |
| Qwen3.8 27B | 72.06 | 75.90 | 0.834 | NA | NA |
| Tiny Aya Earth | 62.43 | 67.22 | 0.830 | NA | NA |
| Tiny Aya Fire | 63.66 | 68.42 | 0.830 | NA | NA |
| Tiny Aya Global | 61.79 | 66.65 | 0.829 | NA | NA |
| Tiny Aya Water | 62.21 | 67.05 | 0.830 | NA | NA |

## JRC Definitions / few shot / luna / externally_verified

Target-Term Coverage: 20 directions; Variant-Aware Coverage: 20 directions; Term BERTScore Recall: 20 directions; Terminology Success Rate: 0 directions; Variant-Aware Success Rate: 0 directions

| Model | Target-Term Coverage | Variant-Aware Coverage | Term BERTScore Recall | Terminology Success Rate | Variant-Aware Success Rate |
| --- | --- | --- | --- | --- | --- |
| Gemma 4 31B | 74.74 | 78.20 | 0.836 | NA | NA |
| GPT-6 Luna | 80.54 | 83.25 | 0.837 | NA | NA |
| Granite 4.2 30B | 67.99 | 72.23 | 0.833 | NA | NA |
| Muse Glimmer 30B | 76.31 | 79.53 | 0.836 | NA | NA |
| Nemotron 3.5 Lightning | 65.67 | 70.03 | 0.832 | NA | NA |
| Qwen3.8 27B | 73.90 | 77.44 | 0.835 | NA | NA |
| Tiny Aya Earth | 56.24 | 60.90 | 0.828 | NA | NA |
| Tiny Aya Fire | 57.63 | 62.26 | 0.828 | NA | NA |
| Tiny Aya Global | 54.25 | 58.97 | 0.827 | NA | NA |
| Tiny Aya Water | 56.36 | 61.04 | 0.828 | NA | NA |

## Chemical Patents / zero shot / luna / llm_enriched

Target-Term Coverage: 18 directions; Variant-Aware Coverage: 18 directions; Term BERTScore Recall: 18 directions; Terminology Success Rate: 0 directions; Variant-Aware Success Rate: 0 directions

| Model | Target-Term Coverage | Variant-Aware Coverage | Term BERTScore Recall | Terminology Success Rate | Variant-Aware Success Rate |
| --- | --- | --- | --- | --- | --- |
| Gemma 4 31B | 56.83 | 57.70 | 0.876 | NA | NA |
| GPT-6 Luna | 55.65 | 56.48 | 0.876 | NA | NA |
| Granite 4.2 30B | 42.72 | 43.59 | 0.870 | NA | NA |
| Muse Glimmer 30B | 55.53 | 56.31 | 0.875 | NA | NA |
| Nemotron 3.5 Lightning | 43.49 | 44.42 | 0.870 | NA | NA |
| Qwen3.8 27B | 52.64 | 53.52 | 0.874 | NA | NA |
| Tiny Aya Earth | 38.79 | 39.78 | 0.868 | NA | NA |
| Tiny Aya Fire | 39.52 | 40.48 | 0.868 | NA | NA |
| Tiny Aya Global | 38.25 | 39.24 | 0.867 | NA | NA |
| Tiny Aya Water | 38.89 | 39.87 | 0.868 | NA | NA |

## Chemical Patents / few shot / luna / llm_enriched

Target-Term Coverage: 18 directions; Variant-Aware Coverage: 18 directions; Term BERTScore Recall: 18 directions; Terminology Success Rate: 0 directions; Variant-Aware Success Rate: 0 directions

| Model | Target-Term Coverage | Variant-Aware Coverage | Term BERTScore Recall | Terminology Success Rate | Variant-Aware Success Rate |
| --- | --- | --- | --- | --- | --- |
| Gemma 4 31B | 57.18 | 58.04 | 0.875 | NA | NA |
| GPT-6 Luna | 57.25 | 58.07 | 0.876 | NA | NA |
| Granite 4.2 30B | 43.86 | 44.75 | 0.870 | NA | NA |
| Muse Glimmer 30B | 56.93 | 57.71 | 0.876 | NA | NA |
| Nemotron 3.5 Lightning | 44.91 | 45.82 | 0.871 | NA | NA |
| Qwen3.8 27B | 54.44 | 55.25 | 0.874 | NA | NA |
| Tiny Aya Earth | 36.92 | 37.89 | 0.867 | NA | NA |
| Tiny Aya Fire | 37.95 | 38.93 | 0.868 | NA | NA |
| Tiny Aya Global | 36.31 | 37.25 | 0.867 | NA | NA |
| Tiny Aya Water | 36.97 | 37.89 | 0.867 | NA | NA |

## JRC Articles / zero shot / luna / llm_enriched

Target-Term Coverage: 20 directions; Variant-Aware Coverage: 20 directions; Term BERTScore Recall: 20 directions; Terminology Success Rate: 0 directions; Variant-Aware Success Rate: 0 directions

| Model | Target-Term Coverage | Variant-Aware Coverage | Term BERTScore Recall | Terminology Success Rate | Variant-Aware Success Rate |
| --- | --- | --- | --- | --- | --- |
| Gemma 4 31B | 51.65 | 53.10 | 0.893 | NA | NA |
| GPT-6 Luna | 64.68 | 66.42 | 0.897 | NA | NA |
| Granite 4.2 30B | 39.97 | 41.42 | 0.890 | NA | NA |
| Muse Glimmer 30B | 57.00 | 57.76 | 0.892 | NA | NA |
| Nemotron 3.5 Lightning | 40.44 | 41.95 | 0.890 | NA | NA |
| Qwen3.8 27B | 53.03 | 53.98 | 0.894 | NA | NA |
| Tiny Aya Earth | 37.90 | 40.69 | 0.888 | NA | NA |
| Tiny Aya Fire | 40.29 | 42.72 | 0.888 | NA | NA |
| Tiny Aya Global | 37.93 | 40.52 | 0.889 | NA | NA |
| Tiny Aya Water | 37.42 | 40.19 | 0.888 | NA | NA |

## JRC Articles / few shot / luna / llm_enriched

Target-Term Coverage: 20 directions; Variant-Aware Coverage: 20 directions; Term BERTScore Recall: 20 directions; Terminology Success Rate: 0 directions; Variant-Aware Success Rate: 0 directions

| Model | Target-Term Coverage | Variant-Aware Coverage | Term BERTScore Recall | Terminology Success Rate | Variant-Aware Success Rate |
| --- | --- | --- | --- | --- | --- |
| Gemma 4 31B | 71.27 | 72.12 | 0.897 | NA | NA |
| GPT-6 Luna | 74.24 | 75.79 | 0.899 | NA | NA |
| Granite 4.2 30B | 62.68 | 63.60 | 0.895 | NA | NA |
| Muse Glimmer 30B | 72.24 | 72.96 | 0.897 | NA | NA |
| Nemotron 3.5 Lightning | 61.81 | 62.67 | 0.895 | NA | NA |
| Qwen3.8 27B | 71.93 | 72.68 | 0.896 | NA | NA |
| Tiny Aya Earth | 56.05 | 57.18 | 0.892 | NA | NA |
| Tiny Aya Fire | 57.78 | 58.93 | 0.892 | NA | NA |
| Tiny Aya Global | 54.87 | 55.97 | 0.892 | NA | NA |
| Tiny Aya Water | 55.83 | 56.95 | 0.892 | NA | NA |

## JRC Definitions / zero shot / luna / llm_enriched

Target-Term Coverage: 20 directions; Variant-Aware Coverage: 20 directions; Term BERTScore Recall: 20 directions; Terminology Success Rate: 0 directions; Variant-Aware Success Rate: 0 directions

| Model | Target-Term Coverage | Variant-Aware Coverage | Term BERTScore Recall | Terminology Success Rate | Variant-Aware Success Rate |
| --- | --- | --- | --- | --- | --- |
| Gemma 4 31B | 50.44 | 52.49 | 0.880 | NA | NA |
| GPT-6 Luna | 58.77 | 60.62 | 0.884 | NA | NA |
| Granite 4.2 30B | 39.95 | 42.13 | 0.877 | NA | NA |
| Muse Glimmer 30B | 51.34 | 53.31 | 0.879 | NA | NA |
| Nemotron 3.5 Lightning | 37.74 | 39.99 | 0.876 | NA | NA |
| Qwen3.8 27B | 47.67 | 49.88 | 0.880 | NA | NA |
| Tiny Aya Earth | 36.73 | 38.99 | 0.874 | NA | NA |
| Tiny Aya Fire | 38.00 | 40.19 | 0.875 | NA | NA |
| Tiny Aya Global | 36.09 | 38.33 | 0.874 | NA | NA |
| Tiny Aya Water | 36.56 | 38.80 | 0.874 | NA | NA |

## JRC Definitions / few shot / luna / llm_enriched

Target-Term Coverage: 20 directions; Variant-Aware Coverage: 20 directions; Term BERTScore Recall: 20 directions; Terminology Success Rate: 0 directions; Variant-Aware Success Rate: 0 directions

| Model | Target-Term Coverage | Variant-Aware Coverage | Term BERTScore Recall | Terminology Success Rate | Variant-Aware Success Rate |
| --- | --- | --- | --- | --- | --- |
| Gemma 4 31B | 52.96 | 54.88 | 0.882 | NA | NA |
| GPT-6 Luna | 61.87 | 63.48 | 0.884 | NA | NA |
| Granite 4.2 30B | 43.23 | 45.32 | 0.878 | NA | NA |
| Muse Glimmer 30B | 55.71 | 57.50 | 0.882 | NA | NA |
| Nemotron 3.5 Lightning | 42.57 | 44.67 | 0.877 | NA | NA |
| Qwen3.8 27B | 51.62 | 53.60 | 0.881 | NA | NA |
| Tiny Aya Earth | 33.65 | 35.80 | 0.872 | NA | NA |
| Tiny Aya Fire | 34.99 | 37.08 | 0.872 | NA | NA |
| Tiny Aya Global | 32.06 | 34.22 | 0.870 | NA | NA |
| Tiny Aya Water | 33.55 | 35.71 | 0.872 | NA | NA |
