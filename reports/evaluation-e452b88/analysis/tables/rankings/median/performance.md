# Median Direction-Score Tables

Native metric values use the median over the same directions shared across models and both prompts. Each direction has equal weight; this is not a per-translation statistic. NA is unavailable, not zero. See [model rankings](rankings.md) for balanced family ranks.

## Chemical Patents / zero shot / shared_general / not_applicable

BLEU: 22 directions; chrF: 22 directions; chrF++: 22 directions; BERTScore F1: 22 directions; BLEURT: 22 directions; COMET: 22 directions; COMETKiwi-QE: 22 directions; XCOMET-XL: 22 directions; Sequence Similarity: 22 directions

| Model | BLEU | chrF | chrF++ | BERTScore F1 | BLEURT | COMET | COMETKiwi-QE | XCOMET-XL | Sequence Similarity |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Gemma 4 31B | 48.56 | 74.00 | 71.20 | 0.939 | 0.604 | 0.869 | 0.616 | 0.168 | 42.307 |
| GPT-6 Luna | 44.53 | 72.08 | 69.18 | 0.943 | 0.614 | 0.875 | 0.629 | 0.172 | 40.849 |
| Granite 4.2 30B | 37.78 | 66.63 | 63.32 | 0.928 | 0.552 | 0.854 | 0.616 | 0.168 | 31.810 |
| Muse Glimmer 30B | 48.58 | 73.65 | 70.39 | 0.942 | 0.588 | 0.862 | 0.594 | 0.167 | 41.474 |
| Nemotron 3.5 Lightning | 39.93 | 67.24 | 63.60 | 0.928 | 0.546 | 0.848 | 0.592 | 0.168 | 31.524 |
| Qwen3.8 27B | 46.94 | 73.16 | 69.72 | 0.938 | 0.593 | 0.866 | 0.620 | 0.168 | 39.718 |
| Tiny Aya Global | 33.86 | 62.62 | 59.69 | 0.925 | 0.525 | 0.845 | 0.613 | 0.164 | 28.642 |

## Chemical Patents / few shot / shared_general / not_applicable

BLEU: 22 directions; chrF: 22 directions; chrF++: 22 directions; BERTScore F1: 22 directions; BLEURT: 22 directions; COMET: 22 directions; COMETKiwi-QE: 22 directions; XCOMET-XL: 22 directions; Sequence Similarity: 22 directions

| Model | BLEU | chrF | chrF++ | BERTScore F1 | BLEURT | COMET | COMETKiwi-QE | XCOMET-XL | Sequence Similarity |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Gemma 4 31B | 49.70 | 74.08 | 70.74 | 0.941 | 0.606 | 0.869 | 0.619 | 0.169 | 42.372 |
| GPT-6 Luna | 46.99 | 73.21 | 70.33 | 0.943 | 0.615 | 0.875 | 0.634 | 0.171 | 41.143 |
| Granite 4.2 30B | 41.79 | 67.69 | 64.77 | 0.931 | 0.557 | 0.854 | 0.615 | 0.168 | 33.539 |
| Muse Glimmer 30B | 51.00 | 74.10 | 71.13 | 0.943 | 0.601 | 0.866 | 0.604 | 0.170 | 44.741 |
| Nemotron 3.5 Lightning | 44.42 | 68.22 | 64.95 | 0.932 | 0.563 | 0.849 | 0.593 | 0.169 | 35.554 |
| Qwen3.8 27B | 50.06 | 73.88 | 70.41 | 0.942 | 0.602 | 0.868 | 0.619 | 0.166 | 42.160 |
| Tiny Aya Global | 31.96 | 60.17 | 56.10 | 0.924 | 0.527 | 0.837 | 0.606 | 0.161 | 27.241 |

## JRC Articles / zero shot / shared_general / not_applicable

BLEU: 20 directions; chrF: 20 directions; chrF++: 20 directions; BERTScore F1: 20 directions; BLEURT: 20 directions; COMET: 20 directions; COMETKiwi-QE: 20 directions; XCOMET-XL: 20 directions; Sequence Similarity: 20 directions

| Model | BLEU | chrF | chrF++ | BERTScore F1 | BLEURT | COMET | COMETKiwi-QE | XCOMET-XL | Sequence Similarity |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Gemma 4 31B | 62.47 | 79.84 | 78.00 | 0.956 | 0.563 | 0.895 | 0.647 | 0.185 | 63.106 |
| GPT-6 Luna | 70.18 | 84.56 | 82.76 | 0.967 | 0.620 | 0.902 | 0.649 | 0.186 | 69.259 |
| Granite 4.2 30B | 53.64 | 75.10 | 72.63 | 0.948 | 0.521 | 0.890 | 0.631 | 0.187 | 55.753 |
| Muse Glimmer 30B | 62.71 | 80.60 | 78.58 | 0.958 | 0.583 | 0.897 | 0.643 | 0.186 | 65.380 |
| Nemotron 3.5 Lightning | 53.90 | 74.17 | 72.06 | 0.946 | 0.514 | 0.887 | 0.605 | 0.183 | 57.180 |
| Qwen3.8 27B | 63.00 | 80.10 | 78.32 | 0.961 | 0.580 | 0.898 | 0.648 | 0.185 | 64.019 |
| Tiny Aya Global | 52.30 | 73.68 | 71.27 | 0.947 | 0.501 | 0.885 | 0.626 | 0.185 | 53.956 |

## JRC Articles / few shot / shared_general / not_applicable

BLEU: 20 directions; chrF: 20 directions; chrF++: 20 directions; BERTScore F1: 20 directions; BLEURT: 20 directions; COMET: 20 directions; COMETKiwi-QE: 20 directions; XCOMET-XL: 20 directions; Sequence Similarity: 20 directions

| Model | BLEU | chrF | chrF++ | BERTScore F1 | BLEURT | COMET | COMETKiwi-QE | XCOMET-XL | Sequence Similarity |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Gemma 4 31B | 72.20 | 84.03 | 82.88 | 0.966 | 0.619 | 0.902 | 0.638 | 0.182 | 70.991 |
| GPT-6 Luna | 73.73 | 85.85 | 84.23 | 0.970 | 0.642 | 0.904 | 0.642 | 0.183 | 73.339 |
| Granite 4.2 30B | 65.46 | 81.50 | 79.69 | 0.962 | 0.589 | 0.898 | 0.635 | 0.182 | 66.747 |
| Muse Glimmer 30B | 73.19 | 84.80 | 83.64 | 0.968 | 0.625 | 0.902 | 0.636 | 0.184 | 71.985 |
| Nemotron 3.5 Lightning | 67.37 | 80.96 | 79.63 | 0.963 | 0.596 | 0.897 | 0.627 | 0.183 | 66.498 |
| Qwen3.8 27B | 73.20 | 84.70 | 83.59 | 0.968 | 0.622 | 0.901 | 0.635 | 0.183 | 72.314 |
| Tiny Aya Global | 60.34 | 77.41 | 75.62 | 0.955 | 0.586 | 0.885 | 0.619 | 0.182 | 62.587 |

## JRC Definitions / zero shot / shared_general / not_applicable

BLEU: 20 directions; chrF: 20 directions; chrF++: 20 directions; BERTScore F1: 20 directions; BLEURT: 20 directions; COMET: 20 directions; COMETKiwi-QE: 20 directions; XCOMET-XL: 20 directions; Sequence Similarity: 20 directions

| Model | BLEU | chrF | chrF++ | BERTScore F1 | BLEURT | COMET | COMETKiwi-QE | XCOMET-XL | Sequence Similarity |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Gemma 4 31B | 47.42 | 74.91 | 72.08 | 0.946 | 0.557 | 0.893 | 0.700 | 0.196 | 35.174 |
| GPT-6 Luna | 53.24 | 78.20 | 75.54 | 0.951 | 0.601 | 0.901 | 0.708 | 0.198 | 39.993 |
| Granite 4.2 30B | 42.17 | 71.63 | 68.60 | 0.940 | 0.523 | 0.887 | 0.670 | 0.196 | 31.025 |
| Muse Glimmer 30B | 45.92 | 74.80 | 71.80 | 0.946 | 0.548 | 0.890 | 0.691 | 0.197 | 33.891 |
| Nemotron 3.5 Lightning | 39.27 | 69.93 | 66.87 | 0.937 | 0.477 | 0.879 | 0.646 | 0.195 | 29.561 |
| Qwen3.8 27B | 46.61 | 74.36 | 71.60 | 0.945 | 0.560 | 0.892 | 0.699 | 0.196 | 35.259 |
| Tiny Aya Global | 38.55 | 67.79 | 65.27 | 0.935 | 0.492 | 0.869 | 0.665 | 0.195 | 26.782 |

## JRC Definitions / few shot / shared_general / not_applicable

BLEU: 20 directions; chrF: 20 directions; chrF++: 20 directions; BERTScore F1: 20 directions; BLEURT: 20 directions; COMET: 20 directions; COMETKiwi-QE: 20 directions; XCOMET-XL: 20 directions; Sequence Similarity: 20 directions

| Model | BLEU | chrF | chrF++ | BERTScore F1 | BLEURT | COMET | COMETKiwi-QE | XCOMET-XL | Sequence Similarity |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Gemma 4 31B | 50.07 | 76.45 | 73.88 | 0.949 | 0.565 | 0.897 | 0.702 | 0.196 | 36.563 |
| GPT-6 Luna | 56.13 | 79.19 | 76.82 | 0.953 | 0.604 | 0.902 | 0.706 | 0.198 | 41.119 |
| Granite 4.2 30B | 44.98 | 73.09 | 70.30 | 0.943 | 0.537 | 0.891 | 0.681 | 0.197 | 33.054 |
| Muse Glimmer 30B | 50.82 | 76.87 | 74.40 | 0.950 | 0.570 | 0.895 | 0.696 | 0.196 | 37.825 |
| Nemotron 3.5 Lightning | 43.72 | 72.15 | 69.31 | 0.940 | 0.500 | 0.885 | 0.658 | 0.196 | 31.662 |
| Qwen3.8 27B | 50.28 | 76.31 | 73.90 | 0.948 | 0.562 | 0.896 | 0.702 | 0.196 | 37.957 |
| Tiny Aya Global | 37.10 | 67.64 | 64.81 | 0.933 | 0.467 | 0.862 | 0.664 | 0.194 | 27.463 |

## Chemical Patents / zero shot / original_glm / all_terms

Target-Term Coverage: 11 directions; Variant-Aware Coverage: 11 directions; Term BERTScore Recall: 11 directions; Terminology Success Rate: 0 directions; Variant-Aware Success Rate: 0 directions

| Model | Target-Term Coverage | Variant-Aware Coverage | Term BERTScore Recall | Terminology Success Rate | Variant-Aware Success Rate |
| --- | --- | --- | --- | --- | --- |
| Gemma 4 31B | 59.41 | 59.95 | 0.875 | NA | NA |
| GPT-6 Luna | 58.54 | 58.54 | 0.877 | NA | NA |
| Granite 4.2 30B | 37.97 | 37.99 | 0.866 | NA | NA |
| Muse Glimmer 30B | 58.61 | 59.18 | 0.873 | NA | NA |
| Nemotron 3.5 Lightning | 42.07 | 42.68 | 0.864 | NA | NA |
| Qwen3.8 27B | 54.90 | 55.23 | 0.873 | NA | NA |
| Tiny Aya Global | 33.75 | 33.77 | 0.862 | NA | NA |

## Chemical Patents / few shot / original_glm / all_terms

Target-Term Coverage: 11 directions; Variant-Aware Coverage: 11 directions; Term BERTScore Recall: 11 directions; Terminology Success Rate: 0 directions; Variant-Aware Success Rate: 0 directions

| Model | Target-Term Coverage | Variant-Aware Coverage | Term BERTScore Recall | Terminology Success Rate | Variant-Aware Success Rate |
| --- | --- | --- | --- | --- | --- |
| Gemma 4 31B | 59.47 | 59.78 | 0.875 | NA | NA |
| GPT-6 Luna | 61.49 | 61.49 | 0.878 | NA | NA |
| Granite 4.2 30B | 40.07 | 40.10 | 0.869 | NA | NA |
| Muse Glimmer 30B | 59.44 | 60.01 | 0.874 | NA | NA |
| Nemotron 3.5 Lightning | 43.90 | 44.53 | 0.870 | NA | NA |
| Qwen3.8 27B | 55.30 | 56.21 | 0.874 | NA | NA |
| Tiny Aya Global | 28.94 | 28.99 | 0.859 | NA | NA |

## JRC Articles / zero shot / original_glm / all_terms

Target-Term Coverage: 20 directions; Variant-Aware Coverage: 20 directions; Term BERTScore Recall: 20 directions; Terminology Success Rate: 0 directions; Variant-Aware Success Rate: 0 directions

| Model | Target-Term Coverage | Variant-Aware Coverage | Term BERTScore Recall | Terminology Success Rate | Variant-Aware Success Rate |
| --- | --- | --- | --- | --- | --- |
| Gemma 4 31B | 58.95 | 59.20 | 0.842 | NA | NA |
| GPT-6 Luna | 68.47 | 68.54 | 0.845 | NA | NA |
| Granite 4.2 30B | 48.39 | 48.64 | 0.837 | NA | NA |
| Muse Glimmer 30B | 64.71 | 65.31 | 0.842 | NA | NA |
| Nemotron 3.5 Lightning | 50.09 | 50.41 | 0.839 | NA | NA |
| Qwen3.8 27B | 61.35 | 61.55 | 0.843 | NA | NA |
| Tiny Aya Global | 47.11 | 47.62 | 0.838 | NA | NA |

## JRC Articles / few shot / original_glm / all_terms

Target-Term Coverage: 20 directions; Variant-Aware Coverage: 20 directions; Term BERTScore Recall: 20 directions; Terminology Success Rate: 0 directions; Variant-Aware Success Rate: 0 directions

| Model | Target-Term Coverage | Variant-Aware Coverage | Term BERTScore Recall | Terminology Success Rate | Variant-Aware Success Rate |
| --- | --- | --- | --- | --- | --- |
| Gemma 4 31B | 73.35 | 73.66 | 0.844 | NA | NA |
| GPT-6 Luna | 74.85 | 75.02 | 0.846 | NA | NA |
| Granite 4.2 30B | 66.82 | 67.00 | 0.843 | NA | NA |
| Muse Glimmer 30B | 74.16 | 74.29 | 0.845 | NA | NA |
| Nemotron 3.5 Lightning | 67.32 | 67.65 | 0.844 | NA | NA |
| Qwen3.8 27B | 73.54 | 73.66 | 0.844 | NA | NA |
| Tiny Aya Global | 62.35 | 62.53 | 0.842 | NA | NA |

## JRC Definitions / zero shot / original_glm / all_terms

Target-Term Coverage: 20 directions; Variant-Aware Coverage: 20 directions; Term BERTScore Recall: 20 directions; Terminology Success Rate: 0 directions; Variant-Aware Success Rate: 0 directions

| Model | Target-Term Coverage | Variant-Aware Coverage | Term BERTScore Recall | Terminology Success Rate | Variant-Aware Success Rate |
| --- | --- | --- | --- | --- | --- |
| Gemma 4 31B | 48.19 | 48.72 | 0.842 | NA | NA |
| GPT-6 Luna | 55.18 | 55.84 | 0.844 | NA | NA |
| Granite 4.2 30B | 40.73 | 41.33 | 0.840 | NA | NA |
| Muse Glimmer 30B | 49.36 | 49.85 | 0.841 | NA | NA |
| Nemotron 3.5 Lightning | 40.62 | 41.20 | 0.838 | NA | NA |
| Qwen3.8 27B | 46.53 | 47.23 | 0.841 | NA | NA |
| Tiny Aya Global | 38.89 | 39.39 | 0.837 | NA | NA |

## JRC Definitions / few shot / original_glm / all_terms

Target-Term Coverage: 20 directions; Variant-Aware Coverage: 20 directions; Term BERTScore Recall: 20 directions; Terminology Success Rate: 0 directions; Variant-Aware Success Rate: 0 directions

| Model | Target-Term Coverage | Variant-Aware Coverage | Term BERTScore Recall | Terminology Success Rate | Variant-Aware Success Rate |
| --- | --- | --- | --- | --- | --- |
| Gemma 4 31B | 49.91 | 50.31 | 0.843 | NA | NA |
| GPT-6 Luna | 58.45 | 58.80 | 0.845 | NA | NA |
| Granite 4.2 30B | 42.82 | 43.29 | 0.840 | NA | NA |
| Muse Glimmer 30B | 52.03 | 52.39 | 0.843 | NA | NA |
| Nemotron 3.5 Lightning | 43.10 | 43.55 | 0.840 | NA | NA |
| Qwen3.8 27B | 49.35 | 49.88 | 0.842 | NA | NA |
| Tiny Aya Global | 37.64 | 38.00 | 0.837 | NA | NA |

## Chemical Patents / zero shot / original_glm / externally_verified

Target-Term Coverage: 11 directions; Variant-Aware Coverage: 11 directions; Term BERTScore Recall: 11 directions; Terminology Success Rate: 0 directions; Variant-Aware Success Rate: 0 directions

| Model | Target-Term Coverage | Variant-Aware Coverage | Term BERTScore Recall | Terminology Success Rate | Variant-Aware Success Rate |
| --- | --- | --- | --- | --- | --- |
| Gemma 4 31B | 86.30 | 87.83 | 0.849 | NA | NA |
| GPT-6 Luna | 85.82 | 87.79 | 0.849 | NA | NA |
| Granite 4.2 30B | 79.83 | 81.87 | 0.847 | NA | NA |
| Muse Glimmer 30B | 84.55 | 86.64 | 0.850 | NA | NA |
| Nemotron 3.5 Lightning | 79.31 | 79.31 | 0.847 | NA | NA |
| Qwen3.8 27B | 84.02 | 84.88 | 0.848 | NA | NA |
| Tiny Aya Global | 72.03 | 76.67 | 0.845 | NA | NA |

## Chemical Patents / few shot / original_glm / externally_verified

Target-Term Coverage: 11 directions; Variant-Aware Coverage: 11 directions; Term BERTScore Recall: 11 directions; Terminology Success Rate: 0 directions; Variant-Aware Success Rate: 0 directions

| Model | Target-Term Coverage | Variant-Aware Coverage | Term BERTScore Recall | Terminology Success Rate | Variant-Aware Success Rate |
| --- | --- | --- | --- | --- | --- |
| Gemma 4 31B | 85.69 | 86.61 | 0.849 | NA | NA |
| GPT-6 Luna | 85.62 | 86.43 | 0.849 | NA | NA |
| Granite 4.2 30B | 78.95 | 79.01 | 0.847 | NA | NA |
| Muse Glimmer 30B | 86.18 | 87.77 | 0.849 | NA | NA |
| Nemotron 3.5 Lightning | 81.35 | 81.80 | 0.847 | NA | NA |
| Qwen3.8 27B | 84.63 | 85.63 | 0.849 | NA | NA |
| Tiny Aya Global | 64.04 | 64.96 | 0.844 | NA | NA |

## JRC Articles / zero shot / original_glm / externally_verified

Target-Term Coverage: 20 directions; Variant-Aware Coverage: 20 directions; Term BERTScore Recall: 20 directions; Terminology Success Rate: 0 directions; Variant-Aware Success Rate: 0 directions

| Model | Target-Term Coverage | Variant-Aware Coverage | Term BERTScore Recall | Terminology Success Rate | Variant-Aware Success Rate |
| --- | --- | --- | --- | --- | --- |
| Gemma 4 31B | 74.89 | 77.63 | 0.865 | NA | NA |
| GPT-6 Luna | 84.51 | 85.92 | 0.868 | NA | NA |
| Granite 4.2 30B | 58.02 | 58.97 | 0.863 | NA | NA |
| Muse Glimmer 30B | 82.18 | 82.98 | 0.866 | NA | NA |
| Nemotron 3.5 Lightning | 62.98 | 65.05 | 0.864 | NA | NA |
| Qwen3.8 27B | 77.86 | 79.54 | 0.865 | NA | NA |
| Tiny Aya Global | 59.11 | 60.37 | 0.861 | NA | NA |

## JRC Articles / few shot / original_glm / externally_verified

Target-Term Coverage: 20 directions; Variant-Aware Coverage: 20 directions; Term BERTScore Recall: 20 directions; Terminology Success Rate: 0 directions; Variant-Aware Success Rate: 0 directions

| Model | Target-Term Coverage | Variant-Aware Coverage | Term BERTScore Recall | Terminology Success Rate | Variant-Aware Success Rate |
| --- | --- | --- | --- | --- | --- |
| Gemma 4 31B | 84.05 | 85.37 | 0.867 | NA | NA |
| GPT-6 Luna | 86.82 | 88.18 | 0.868 | NA | NA |
| Granite 4.2 30B | 80.14 | 81.88 | 0.866 | NA | NA |
| Muse Glimmer 30B | 85.02 | 86.46 | 0.867 | NA | NA |
| Nemotron 3.5 Lightning | 79.87 | 81.18 | 0.866 | NA | NA |
| Qwen3.8 27B | 85.95 | 86.51 | 0.867 | NA | NA |
| Tiny Aya Global | 74.76 | 75.40 | 0.865 | NA | NA |

## JRC Definitions / zero shot / original_glm / externally_verified

Target-Term Coverage: 20 directions; Variant-Aware Coverage: 20 directions; Term BERTScore Recall: 20 directions; Terminology Success Rate: 0 directions; Variant-Aware Success Rate: 0 directions

| Model | Target-Term Coverage | Variant-Aware Coverage | Term BERTScore Recall | Terminology Success Rate | Variant-Aware Success Rate |
| --- | --- | --- | --- | --- | --- |
| Gemma 4 31B | 72.24 | 74.41 | 0.865 | NA | NA |
| GPT-6 Luna | 78.66 | 81.29 | 0.868 | NA | NA |
| Granite 4.2 30B | 63.86 | 65.75 | 0.862 | NA | NA |
| Muse Glimmer 30B | 73.07 | 75.04 | 0.865 | NA | NA |
| Nemotron 3.5 Lightning | 60.58 | 62.57 | 0.861 | NA | NA |
| Qwen3.8 27B | 69.44 | 70.95 | 0.864 | NA | NA |
| Tiny Aya Global | 58.15 | 59.74 | 0.859 | NA | NA |

## JRC Definitions / few shot / original_glm / externally_verified

Target-Term Coverage: 20 directions; Variant-Aware Coverage: 20 directions; Term BERTScore Recall: 20 directions; Terminology Success Rate: 0 directions; Variant-Aware Success Rate: 0 directions

| Model | Target-Term Coverage | Variant-Aware Coverage | Term BERTScore Recall | Terminology Success Rate | Variant-Aware Success Rate |
| --- | --- | --- | --- | --- | --- |
| Gemma 4 31B | 73.73 | 75.26 | 0.866 | NA | NA |
| GPT-6 Luna | 82.14 | 83.37 | 0.869 | NA | NA |
| Granite 4.2 30B | 66.26 | 67.82 | 0.863 | NA | NA |
| Muse Glimmer 30B | 76.16 | 77.50 | 0.867 | NA | NA |
| Nemotron 3.5 Lightning | 63.72 | 65.25 | 0.863 | NA | NA |
| Qwen3.8 27B | 73.06 | 74.62 | 0.865 | NA | NA |
| Tiny Aya Global | 54.71 | 56.39 | 0.859 | NA | NA |

## Chemical Patents / zero shot / original_glm / llm_enriched

Target-Term Coverage: 11 directions; Variant-Aware Coverage: 11 directions; Term BERTScore Recall: 11 directions; Terminology Success Rate: 0 directions; Variant-Aware Success Rate: 0 directions

| Model | Target-Term Coverage | Variant-Aware Coverage | Term BERTScore Recall | Terminology Success Rate | Variant-Aware Success Rate |
| --- | --- | --- | --- | --- | --- |
| Gemma 4 31B | 57.13 | 57.92 | 0.881 | NA | NA |
| GPT-6 Luna | 56.20 | 56.67 | 0.882 | NA | NA |
| Granite 4.2 30B | 31.89 | 31.92 | 0.872 | NA | NA |
| Muse Glimmer 30B | 55.01 | 55.05 | 0.880 | NA | NA |
| Nemotron 3.5 Lightning | 38.72 | 39.45 | 0.871 | NA | NA |
| Qwen3.8 27B | 51.19 | 52.76 | 0.878 | NA | NA |
| Tiny Aya Global | 28.20 | 28.23 | 0.870 | NA | NA |

## Chemical Patents / few shot / original_glm / llm_enriched

Target-Term Coverage: 11 directions; Variant-Aware Coverage: 11 directions; Term BERTScore Recall: 11 directions; Terminology Success Rate: 0 directions; Variant-Aware Success Rate: 0 directions

| Model | Target-Term Coverage | Variant-Aware Coverage | Term BERTScore Recall | Terminology Success Rate | Variant-Aware Success Rate |
| --- | --- | --- | --- | --- | --- |
| Gemma 4 31B | 56.88 | 57.59 | 0.882 | NA | NA |
| GPT-6 Luna | 58.36 | 58.36 | 0.883 | NA | NA |
| Granite 4.2 30B | 33.77 | 33.79 | 0.873 | NA | NA |
| Muse Glimmer 30B | 57.14 | 57.92 | 0.881 | NA | NA |
| Nemotron 3.5 Lightning | 40.38 | 41.16 | 0.875 | NA | NA |
| Qwen3.8 27B | 51.71 | 52.74 | 0.879 | NA | NA |
| Tiny Aya Global | 23.68 | 23.68 | 0.864 | NA | NA |

## JRC Articles / zero shot / original_glm / llm_enriched

Target-Term Coverage: 20 directions; Variant-Aware Coverage: 20 directions; Term BERTScore Recall: 20 directions; Terminology Success Rate: 0 directions; Variant-Aware Success Rate: 0 directions

| Model | Target-Term Coverage | Variant-Aware Coverage | Term BERTScore Recall | Terminology Success Rate | Variant-Aware Success Rate |
| --- | --- | --- | --- | --- | --- |
| Gemma 4 31B | 55.79 | 56.79 | 0.897 | NA | NA |
| GPT-6 Luna | 68.32 | 68.83 | 0.900 | NA | NA |
| Granite 4.2 30B | 40.50 | 41.57 | 0.891 | NA | NA |
| Muse Glimmer 30B | 61.66 | 61.86 | 0.896 | NA | NA |
| Nemotron 3.5 Lightning | 42.51 | 43.60 | 0.893 | NA | NA |
| Qwen3.8 27B | 55.20 | 55.72 | 0.896 | NA | NA |
| Tiny Aya Global | 37.05 | 37.91 | 0.891 | NA | NA |

## JRC Articles / few shot / original_glm / llm_enriched

Target-Term Coverage: 20 directions; Variant-Aware Coverage: 20 directions; Term BERTScore Recall: 20 directions; Terminology Success Rate: 0 directions; Variant-Aware Success Rate: 0 directions

| Model | Target-Term Coverage | Variant-Aware Coverage | Term BERTScore Recall | Terminology Success Rate | Variant-Aware Success Rate |
| --- | --- | --- | --- | --- | --- |
| Gemma 4 31B | 77.44 | 77.93 | 0.900 | NA | NA |
| GPT-6 Luna | 80.11 | 80.47 | 0.900 | NA | NA |
| Granite 4.2 30B | 69.38 | 69.69 | 0.898 | NA | NA |
| Muse Glimmer 30B | 78.36 | 78.71 | 0.900 | NA | NA |
| Nemotron 3.5 Lightning | 68.72 | 69.94 | 0.898 | NA | NA |
| Qwen3.8 27B | 78.34 | 78.96 | 0.899 | NA | NA |
| Tiny Aya Global | 65.10 | 65.75 | 0.896 | NA | NA |

## JRC Definitions / zero shot / original_glm / llm_enriched

Target-Term Coverage: 20 directions; Variant-Aware Coverage: 20 directions; Term BERTScore Recall: 20 directions; Terminology Success Rate: 0 directions; Variant-Aware Success Rate: 0 directions

| Model | Target-Term Coverage | Variant-Aware Coverage | Term BERTScore Recall | Terminology Success Rate | Variant-Aware Success Rate |
| --- | --- | --- | --- | --- | --- |
| Gemma 4 31B | 59.25 | 60.70 | 0.884 | NA | NA |
| GPT-6 Luna | 67.09 | 68.49 | 0.887 | NA | NA |
| Granite 4.2 30B | 48.96 | 50.27 | 0.882 | NA | NA |
| Muse Glimmer 30B | 63.11 | 64.44 | 0.883 | NA | NA |
| Nemotron 3.5 Lightning | 46.18 | 47.08 | 0.881 | NA | NA |
| Qwen3.8 27B | 55.08 | 56.42 | 0.884 | NA | NA |
| Tiny Aya Global | 45.25 | 46.10 | 0.878 | NA | NA |

## JRC Definitions / few shot / original_glm / llm_enriched

Target-Term Coverage: 20 directions; Variant-Aware Coverage: 20 directions; Term BERTScore Recall: 20 directions; Terminology Success Rate: 0 directions; Variant-Aware Success Rate: 0 directions

| Model | Target-Term Coverage | Variant-Aware Coverage | Term BERTScore Recall | Terminology Success Rate | Variant-Aware Success Rate |
| --- | --- | --- | --- | --- | --- |
| Gemma 4 31B | 64.37 | 64.98 | 0.886 | NA | NA |
| GPT-6 Luna | 70.11 | 71.01 | 0.888 | NA | NA |
| Granite 4.2 30B | 53.10 | 54.22 | 0.883 | NA | NA |
| Muse Glimmer 30B | 65.86 | 66.98 | 0.886 | NA | NA |
| Nemotron 3.5 Lightning | 51.71 | 52.75 | 0.882 | NA | NA |
| Qwen3.8 27B | 60.73 | 61.69 | 0.885 | NA | NA |
| Tiny Aya Global | 43.75 | 44.53 | 0.877 | NA | NA |

## Chemical Patents / zero shot / luna / all_terms

Target-Term Coverage: 18 directions; Variant-Aware Coverage: 18 directions; Term BERTScore Recall: 18 directions; Terminology Success Rate: 0 directions; Variant-Aware Success Rate: 0 directions

| Model | Target-Term Coverage | Variant-Aware Coverage | Term BERTScore Recall | Terminology Success Rate | Variant-Aware Success Rate |
| --- | --- | --- | --- | --- | --- |
| Gemma 4 31B | 46.38 | 46.39 | 0.852 | NA | NA |
| GPT-6 Luna | 46.57 | 46.92 | 0.850 | NA | NA |
| Granite 4.2 30B | 34.10 | 34.65 | 0.845 | NA | NA |
| Muse Glimmer 30B | 45.57 | 45.85 | 0.852 | NA | NA |
| Nemotron 3.5 Lightning | 36.86 | 37.35 | 0.847 | NA | NA |
| Qwen3.8 27B | 43.54 | 43.94 | 0.849 | NA | NA |
| Tiny Aya Global | 30.91 | 31.28 | 0.844 | NA | NA |

## Chemical Patents / few shot / luna / all_terms

Target-Term Coverage: 18 directions; Variant-Aware Coverage: 18 directions; Term BERTScore Recall: 18 directions; Terminology Success Rate: 0 directions; Variant-Aware Success Rate: 0 directions

| Model | Target-Term Coverage | Variant-Aware Coverage | Term BERTScore Recall | Terminology Success Rate | Variant-Aware Success Rate |
| --- | --- | --- | --- | --- | --- |
| Gemma 4 31B | 47.72 | 47.95 | 0.852 | NA | NA |
| GPT-6 Luna | 46.76 | 47.01 | 0.851 | NA | NA |
| Granite 4.2 30B | 36.03 | 36.29 | 0.845 | NA | NA |
| Muse Glimmer 30B | 47.27 | 47.68 | 0.852 | NA | NA |
| Nemotron 3.5 Lightning | 39.04 | 39.53 | 0.849 | NA | NA |
| Qwen3.8 27B | 45.36 | 45.82 | 0.851 | NA | NA |
| Tiny Aya Global | 29.91 | 30.15 | 0.844 | NA | NA |

## JRC Articles / zero shot / luna / all_terms

Target-Term Coverage: 20 directions; Variant-Aware Coverage: 20 directions; Term BERTScore Recall: 20 directions; Terminology Success Rate: 0 directions; Variant-Aware Success Rate: 0 directions

| Model | Target-Term Coverage | Variant-Aware Coverage | Term BERTScore Recall | Terminology Success Rate | Variant-Aware Success Rate |
| --- | --- | --- | --- | --- | --- |
| Gemma 4 31B | 65.04 | 66.98 | 0.848 | NA | NA |
| GPT-6 Luna | 72.28 | 73.14 | 0.852 | NA | NA |
| Granite 4.2 30B | 54.10 | 55.65 | 0.844 | NA | NA |
| Muse Glimmer 30B | 68.38 | 69.72 | 0.848 | NA | NA |
| Nemotron 3.5 Lightning | 53.95 | 55.30 | 0.845 | NA | NA |
| Qwen3.8 27B | 67.28 | 68.26 | 0.849 | NA | NA |
| Tiny Aya Global | 53.91 | 56.45 | 0.843 | NA | NA |

## JRC Articles / few shot / luna / all_terms

Target-Term Coverage: 20 directions; Variant-Aware Coverage: 20 directions; Term BERTScore Recall: 20 directions; Terminology Success Rate: 0 directions; Variant-Aware Success Rate: 0 directions

| Model | Target-Term Coverage | Variant-Aware Coverage | Term BERTScore Recall | Terminology Success Rate | Variant-Aware Success Rate |
| --- | --- | --- | --- | --- | --- |
| Gemma 4 31B | 75.96 | 76.73 | 0.851 | NA | NA |
| GPT-6 Luna | 78.14 | 78.88 | 0.853 | NA | NA |
| Granite 4.2 30B | 71.32 | 72.19 | 0.849 | NA | NA |
| Muse Glimmer 30B | 77.45 | 77.97 | 0.852 | NA | NA |
| Nemotron 3.5 Lightning | 69.20 | 70.49 | 0.849 | NA | NA |
| Qwen3.8 27B | 76.96 | 77.45 | 0.850 | NA | NA |
| Tiny Aya Global | 65.65 | 66.85 | 0.847 | NA | NA |

## JRC Definitions / zero shot / luna / all_terms

Target-Term Coverage: 20 directions; Variant-Aware Coverage: 20 directions; Term BERTScore Recall: 20 directions; Terminology Success Rate: 0 directions; Variant-Aware Success Rate: 0 directions

| Model | Target-Term Coverage | Variant-Aware Coverage | Term BERTScore Recall | Terminology Success Rate | Variant-Aware Success Rate |
| --- | --- | --- | --- | --- | --- |
| Gemma 4 31B | 64.53 | 67.04 | 0.842 | NA | NA |
| GPT-6 Luna | 69.16 | 71.13 | 0.844 | NA | NA |
| Granite 4.2 30B | 56.99 | 59.25 | 0.840 | NA | NA |
| Muse Glimmer 30B | 64.71 | 66.57 | 0.841 | NA | NA |
| Nemotron 3.5 Lightning | 56.50 | 58.51 | 0.838 | NA | NA |
| Qwen3.8 27B | 61.46 | 63.46 | 0.842 | NA | NA |
| Tiny Aya Global | 54.45 | 56.61 | 0.838 | NA | NA |

## JRC Definitions / few shot / luna / all_terms

Target-Term Coverage: 20 directions; Variant-Aware Coverage: 20 directions; Term BERTScore Recall: 20 directions; Terminology Success Rate: 0 directions; Variant-Aware Success Rate: 0 directions

| Model | Target-Term Coverage | Variant-Aware Coverage | Term BERTScore Recall | Terminology Success Rate | Variant-Aware Success Rate |
| --- | --- | --- | --- | --- | --- |
| Gemma 4 31B | 66.21 | 68.41 | 0.843 | NA | NA |
| GPT-6 Luna | 71.23 | 72.99 | 0.845 | NA | NA |
| Granite 4.2 30B | 58.92 | 61.19 | 0.841 | NA | NA |
| Muse Glimmer 30B | 67.61 | 69.68 | 0.844 | NA | NA |
| Nemotron 3.5 Lightning | 58.85 | 60.95 | 0.841 | NA | NA |
| Qwen3.8 27B | 64.93 | 67.02 | 0.843 | NA | NA |
| Tiny Aya Global | 52.82 | 54.91 | 0.838 | NA | NA |

## Chemical Patents / zero shot / luna / externally_verified

Target-Term Coverage: 17 directions; Variant-Aware Coverage: 17 directions; Term BERTScore Recall: 17 directions; Terminology Success Rate: 0 directions; Variant-Aware Success Rate: 0 directions

| Model | Target-Term Coverage | Variant-Aware Coverage | Term BERTScore Recall | Terminology Success Rate | Variant-Aware Success Rate |
| --- | --- | --- | --- | --- | --- |
| Gemma 4 31B | 82.97 | 86.08 | 0.849 | NA | NA |
| GPT-6 Luna | 82.45 | 85.07 | 0.850 | NA | NA |
| Granite 4.2 30B | 71.62 | 75.67 | 0.848 | NA | NA |
| Muse Glimmer 30B | 82.62 | 85.51 | 0.849 | NA | NA |
| Nemotron 3.5 Lightning | 71.38 | 76.79 | 0.849 | NA | NA |
| Qwen3.8 27B | 81.81 | 84.56 | 0.849 | NA | NA |
| Tiny Aya Global | 68.25 | 70.48 | 0.847 | NA | NA |

## Chemical Patents / few shot / luna / externally_verified

Target-Term Coverage: 17 directions; Variant-Aware Coverage: 17 directions; Term BERTScore Recall: 17 directions; Terminology Success Rate: 0 directions; Variant-Aware Success Rate: 0 directions

| Model | Target-Term Coverage | Variant-Aware Coverage | Term BERTScore Recall | Terminology Success Rate | Variant-Aware Success Rate |
| --- | --- | --- | --- | --- | --- |
| Gemma 4 31B | 82.98 | 86.39 | 0.849 | NA | NA |
| GPT-6 Luna | 82.65 | 85.80 | 0.850 | NA | NA |
| Granite 4.2 30B | 72.67 | 77.66 | 0.849 | NA | NA |
| Muse Glimmer 30B | 82.54 | 85.04 | 0.850 | NA | NA |
| Nemotron 3.5 Lightning | 75.08 | 75.52 | 0.849 | NA | NA |
| Qwen3.8 27B | 82.20 | 85.01 | 0.849 | NA | NA |
| Tiny Aya Global | 67.06 | 68.09 | 0.846 | NA | NA |

## JRC Articles / zero shot / luna / externally_verified

Target-Term Coverage: 20 directions; Variant-Aware Coverage: 20 directions; Term BERTScore Recall: 20 directions; Terminology Success Rate: 0 directions; Variant-Aware Success Rate: 0 directions

| Model | Target-Term Coverage | Variant-Aware Coverage | Term BERTScore Recall | Terminology Success Rate | Variant-Aware Success Rate |
| --- | --- | --- | --- | --- | --- |
| Gemma 4 31B | 78.15 | 81.73 | 0.839 | NA | NA |
| GPT-6 Luna | 84.06 | 87.45 | 0.841 | NA | NA |
| Granite 4.2 30B | 67.36 | 69.79 | 0.836 | NA | NA |
| Muse Glimmer 30B | 81.12 | 83.98 | 0.840 | NA | NA |
| Nemotron 3.5 Lightning | 68.27 | 72.60 | 0.837 | NA | NA |
| Qwen3.8 27B | 80.27 | 83.26 | 0.839 | NA | NA |
| Tiny Aya Global | 67.99 | 71.78 | 0.835 | NA | NA |

## JRC Articles / few shot / luna / externally_verified

Target-Term Coverage: 20 directions; Variant-Aware Coverage: 20 directions; Term BERTScore Recall: 20 directions; Terminology Success Rate: 0 directions; Variant-Aware Success Rate: 0 directions

| Model | Target-Term Coverage | Variant-Aware Coverage | Term BERTScore Recall | Terminology Success Rate | Variant-Aware Success Rate |
| --- | --- | --- | --- | --- | --- |
| Gemma 4 31B | 83.90 | 85.84 | 0.840 | NA | NA |
| GPT-6 Luna | 87.54 | 89.69 | 0.842 | NA | NA |
| Granite 4.2 30B | 80.49 | 83.12 | 0.839 | NA | NA |
| Muse Glimmer 30B | 85.43 | 87.60 | 0.840 | NA | NA |
| Nemotron 3.5 Lightning | 80.38 | 83.11 | 0.840 | NA | NA |
| Qwen3.8 27B | 86.01 | 87.26 | 0.840 | NA | NA |
| Tiny Aya Global | 76.09 | 78.92 | 0.838 | NA | NA |

## JRC Definitions / zero shot / luna / externally_verified

Target-Term Coverage: 20 directions; Variant-Aware Coverage: 20 directions; Term BERTScore Recall: 20 directions; Terminology Success Rate: 0 directions; Variant-Aware Success Rate: 0 directions

| Model | Target-Term Coverage | Variant-Aware Coverage | Term BERTScore Recall | Terminology Success Rate | Variant-Aware Success Rate |
| --- | --- | --- | --- | --- | --- |
| Gemma 4 31B | 75.34 | 78.33 | 0.835 | NA | NA |
| GPT-6 Luna | 80.16 | 82.97 | 0.836 | NA | NA |
| Granite 4.2 30B | 68.89 | 72.56 | 0.833 | NA | NA |
| Muse Glimmer 30B | 75.74 | 78.67 | 0.835 | NA | NA |
| Nemotron 3.5 Lightning | 67.15 | 71.07 | 0.832 | NA | NA |
| Qwen3.8 27B | 73.21 | 76.66 | 0.834 | NA | NA |
| Tiny Aya Global | 66.25 | 70.13 | 0.829 | NA | NA |

## JRC Definitions / few shot / luna / externally_verified

Target-Term Coverage: 20 directions; Variant-Aware Coverage: 20 directions; Term BERTScore Recall: 20 directions; Terminology Success Rate: 0 directions; Variant-Aware Success Rate: 0 directions

| Model | Target-Term Coverage | Variant-Aware Coverage | Term BERTScore Recall | Terminology Success Rate | Variant-Aware Success Rate |
| --- | --- | --- | --- | --- | --- |
| Gemma 4 31B | 76.84 | 79.60 | 0.835 | NA | NA |
| GPT-6 Luna | 81.11 | 83.56 | 0.837 | NA | NA |
| Granite 4.2 30B | 70.51 | 73.91 | 0.834 | NA | NA |
| Muse Glimmer 30B | 77.89 | 80.47 | 0.835 | NA | NA |
| Nemotron 3.5 Lightning | 68.51 | 72.47 | 0.832 | NA | NA |
| Qwen3.8 27B | 75.86 | 78.99 | 0.835 | NA | NA |
| Tiny Aya Global | 64.25 | 67.74 | 0.829 | NA | NA |

## Chemical Patents / zero shot / luna / llm_enriched

Target-Term Coverage: 18 directions; Variant-Aware Coverage: 18 directions; Term BERTScore Recall: 18 directions; Terminology Success Rate: 0 directions; Variant-Aware Success Rate: 0 directions

| Model | Target-Term Coverage | Variant-Aware Coverage | Term BERTScore Recall | Terminology Success Rate | Variant-Aware Success Rate |
| --- | --- | --- | --- | --- | --- |
| Gemma 4 31B | 58.14 | 59.08 | 0.873 | NA | NA |
| GPT-6 Luna | 54.58 | 55.77 | 0.873 | NA | NA |
| Granite 4.2 30B | 43.59 | 44.51 | 0.870 | NA | NA |
| Muse Glimmer 30B | 56.24 | 57.39 | 0.873 | NA | NA |
| Nemotron 3.5 Lightning | 43.71 | 44.65 | 0.870 | NA | NA |
| Qwen3.8 27B | 53.02 | 54.11 | 0.872 | NA | NA |
| Tiny Aya Global | 36.27 | 36.95 | 0.868 | NA | NA |

## Chemical Patents / few shot / luna / llm_enriched

Target-Term Coverage: 18 directions; Variant-Aware Coverage: 18 directions; Term BERTScore Recall: 18 directions; Terminology Success Rate: 0 directions; Variant-Aware Success Rate: 0 directions

| Model | Target-Term Coverage | Variant-Aware Coverage | Term BERTScore Recall | Terminology Success Rate | Variant-Aware Success Rate |
| --- | --- | --- | --- | --- | --- |
| Gemma 4 31B | 58.14 | 58.91 | 0.873 | NA | NA |
| GPT-6 Luna | 56.53 | 57.99 | 0.874 | NA | NA |
| Granite 4.2 30B | 44.59 | 46.05 | 0.871 | NA | NA |
| Muse Glimmer 30B | 56.89 | 57.97 | 0.873 | NA | NA |
| Nemotron 3.5 Lightning | 44.18 | 45.18 | 0.871 | NA | NA |
| Qwen3.8 27B | 54.34 | 55.25 | 0.872 | NA | NA |
| Tiny Aya Global | 34.62 | 35.33 | 0.866 | NA | NA |

## JRC Articles / zero shot / luna / llm_enriched

Target-Term Coverage: 20 directions; Variant-Aware Coverage: 20 directions; Term BERTScore Recall: 20 directions; Terminology Success Rate: 0 directions; Variant-Aware Success Rate: 0 directions

| Model | Target-Term Coverage | Variant-Aware Coverage | Term BERTScore Recall | Terminology Success Rate | Variant-Aware Success Rate |
| --- | --- | --- | --- | --- | --- |
| Gemma 4 31B | 48.11 | 51.34 | 0.894 | NA | NA |
| GPT-6 Luna | 60.59 | 61.21 | 0.898 | NA | NA |
| Granite 4.2 30B | 38.45 | 39.87 | 0.890 | NA | NA |
| Muse Glimmer 30B | 55.85 | 56.82 | 0.895 | NA | NA |
| Nemotron 3.5 Lightning | 39.54 | 41.25 | 0.892 | NA | NA |
| Qwen3.8 27B | 51.26 | 52.38 | 0.894 | NA | NA |
| Tiny Aya Global | 35.18 | 38.04 | 0.889 | NA | NA |

## JRC Articles / few shot / luna / llm_enriched

Target-Term Coverage: 20 directions; Variant-Aware Coverage: 20 directions; Term BERTScore Recall: 20 directions; Terminology Success Rate: 0 directions; Variant-Aware Success Rate: 0 directions

| Model | Target-Term Coverage | Variant-Aware Coverage | Term BERTScore Recall | Terminology Success Rate | Variant-Aware Success Rate |
| --- | --- | --- | --- | --- | --- |
| Gemma 4 31B | 69.82 | 70.98 | 0.897 | NA | NA |
| GPT-6 Luna | 76.12 | 76.78 | 0.899 | NA | NA |
| Granite 4.2 30B | 62.22 | 63.20 | 0.895 | NA | NA |
| Muse Glimmer 30B | 71.25 | 72.01 | 0.897 | NA | NA |
| Nemotron 3.5 Lightning | 61.47 | 62.39 | 0.895 | NA | NA |
| Qwen3.8 27B | 71.02 | 71.70 | 0.896 | NA | NA |
| Tiny Aya Global | 57.20 | 58.16 | 0.893 | NA | NA |

## JRC Definitions / zero shot / luna / llm_enriched

Target-Term Coverage: 20 directions; Variant-Aware Coverage: 20 directions; Term BERTScore Recall: 20 directions; Terminology Success Rate: 0 directions; Variant-Aware Success Rate: 0 directions

| Model | Target-Term Coverage | Variant-Aware Coverage | Term BERTScore Recall | Terminology Success Rate | Variant-Aware Success Rate |
| --- | --- | --- | --- | --- | --- |
| Gemma 4 31B | 52.80 | 54.74 | 0.883 | NA | NA |
| GPT-6 Luna | 57.75 | 59.83 | 0.885 | NA | NA |
| Granite 4.2 30B | 42.34 | 44.62 | 0.880 | NA | NA |
| Muse Glimmer 30B | 54.48 | 56.52 | 0.882 | NA | NA |
| Nemotron 3.5 Lightning | 41.03 | 43.29 | 0.880 | NA | NA |
| Qwen3.8 27B | 47.94 | 49.81 | 0.882 | NA | NA |
| Tiny Aya Global | 40.68 | 43.07 | 0.876 | NA | NA |

## JRC Definitions / few shot / luna / llm_enriched

Target-Term Coverage: 20 directions; Variant-Aware Coverage: 20 directions; Term BERTScore Recall: 20 directions; Terminology Success Rate: 0 directions; Variant-Aware Success Rate: 0 directions

| Model | Target-Term Coverage | Variant-Aware Coverage | Term BERTScore Recall | Terminology Success Rate | Variant-Aware Success Rate |
| --- | --- | --- | --- | --- | --- |
| Gemma 4 31B | 55.54 | 57.63 | 0.884 | NA | NA |
| GPT-6 Luna | 62.01 | 63.25 | 0.886 | NA | NA |
| Granite 4.2 30B | 45.49 | 47.66 | 0.881 | NA | NA |
| Muse Glimmer 30B | 56.87 | 58.84 | 0.884 | NA | NA |
| Nemotron 3.5 Lightning | 46.27 | 48.64 | 0.880 | NA | NA |
| Qwen3.8 27B | 53.91 | 55.80 | 0.883 | NA | NA |
| Tiny Aya Global | 38.70 | 40.77 | 0.876 | NA | NA |
