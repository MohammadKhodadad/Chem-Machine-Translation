from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from collections import defaultdict
from itertools import combinations
from pathlib import Path
from shutil import copyfile
from statistics import mean, median

DATASETS = {
    "google_patents": "Chemical Patents",
    "jrc_articles": "JRC Articles",
    "jrc_definitions": "JRC Definitions",
}
SETTINGS = ("zero_shot", "few_shot")
VIEWS = ("original_glm", "luna")
CATEGORIES = ("all_terms", "externally_verified", "llm_enriched")
GENERAL = (
    "bleu",
    "chrf",
    "chrf2++",
    "bertscore",
    "bleurt",
    "comet",
    "cometkiwi_qe",
    "xcomet_xl",
    "sequence_similarity",
)
TERMINOLOGY = (
    "target_term_coverage",
    "variant_aware_target_term_coverage",
    "term_bertscore_recall",
    "terminology_success_rate",
    "variant_aware_terminology_success_rate",
)
CORPUS = {"bleu", "chrf", "chrf2++"}
RANK_FAMILIES = {
    "semantic": ("bertscore", "bleurt", "comet", "cometkiwi_qe", "xcomet_xl"),
    "lexical": ("bleu", "chrf", "chrf2++", "sequence_similarity"),
    "terminology": TERMINOLOGY,
}
LABELS = {
    "gemma_4_31b_it": "Gemma 4 31B",
    "gpt_6_luna_azure": "GPT-6 Luna",
    "granite_4_2_30b": "Granite 4.2 30B",
    "muse_glimmer_30b": "Muse Glimmer 30B",
    "nemotron_3_5_lightning_30b_a3b": "Nemotron 3.5 Lightning",
    "qwen38_27b_local": "Qwen3.8 27B",
    "tiny_aya_global": "Tiny Aya Global",
}
EXCLUDED_RUNS = frozenset(("tiny_aya_earth", "tiny_aya_fire", "tiny_aya_water"))
EXCLUDED_DIRECTIONS = {"google_patents": frozenset(("es-de", "de-es"))}
DEFAULT_THINKING_MODELS = {
    "gpt_6_luna_azure": {
        "source_url": "https://developers.openai.com/api/docs/models/gpt-6-luna",
        "evidence": "reasoning.effort defaults to medium; run overrides are unverified",
    },
    "granite_4_2_30b": {
        "source_url": "https://huggingface.co/ibm-granite/granite-4.2-30b",
        "evidence": "Thinking (default): enable_thinking=True",
    },
    "muse_glimmer_30b": {
        "source_url": (
            "https://huggingface.co/meta-models/Muse-Glimmer-30B/raw/main/chat_template.jinja"
        ),
        "evidence": "Chat template injects Reasoning strength: high when unspecified",
    },
    "nemotron_3_5_lightning_30b_a3b": {
        "source_url": ("https://huggingface.co/nvidia/NVIDIA-Nemotron-3.5-Lightning-30B-A3B-BF16"),
        "evidence": "Model card: thinking enabled (the default)",
    },
    "qwen38_27b_local": {
        "source_url": "https://huggingface.co/Qwen/Qwen3.8-27B",
        "evidence": "Model card: thinking mode is on by default",
    },
}
METRIC_LABELS = {
    "bleu": "BLEU",
    "chrf": "chrF",
    "chrf2++": "chrF++",
    "bertscore": "BERTScore F1",
    "bleurt": "BLEURT",
    "comet": "COMET",
    "cometkiwi_qe": "COMETKiwi-QE",
    "xcomet_xl": "XCOMET-XL",
    "sequence_similarity": "Sequence Similarity",
    "target_term_coverage": "Target-Term Coverage",
    "variant_aware_target_term_coverage": "Variant-Aware Coverage",
    "term_bertscore_recall": "Term BERTScore Recall",
    "terminology_success_rate": "Terminology Success Rate",
    "variant_aware_terminology_success_rate": "Variant-Aware Success Rate",
}


def population(run):
    if run.split("__", 1)[0] in EXCLUDED_RUNS:
        return "excluded"
    if "__historical_untimed" in run:
        return "historical"
    if "__native_sample" in run:
        return "native_sample"
    return "current"


def select_analysis_summary(summary):
    if population(summary["run"]) == "excluded":
        return None
    return {
        **summary,
        "dataset_settings": {
            dataset: {
                setting: {
                    **group,
                    "by_direction": {
                        direction: result
                        for direction, result in group["by_direction"].items()
                        if direction not in EXCLUDED_DIRECTIONS.get(dataset, ())
                    },
                }
                for setting, group in settings.items()
            }
            for dataset, settings in summary["dataset_settings"].items()
        },
    }


def select_analysis_points(points):
    return [
        row
        for row in points
        if population(row["run"]) != "excluded"
        and row.get("direction") not in EXCLUDED_DIRECTIONS.get(row["dataset"], ())
    ]


def write_csv(path, rows):
    fields = list(dict.fromkeys(key for row in rows for key in row))
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def metric_value(result, metric):
    section = "corpus_metrics" if metric in CORPUS else "mean_metrics"
    value = result.get(section, {}).get(metric)
    status = result.get("metric_status", {}).get(metric, {})
    if (
        not isinstance(value, (int, float))
        or not math.isfinite(value)
        or status.get("state") != "completed"
        or status.get("rows_missing", 0) != 0
        or status.get("rows_scored", 0) <= 0
    ):
        return None
    return value


def direction_macro(results, metric, directions):
    values = [metric_value(results[direction], metric) for direction in directions]
    if not values or any(value is None for value in values):
        return None
    return mean(values)


def load_summaries(root):
    manifest = json.loads((root / "download_manifest.json").read_text(encoding="utf-8"))
    if not manifest["complete"] or len(manifest["files"]) != 84:
        raise ValueError("A complete 84-summary download is required")
    summaries = {}
    details = []
    coverage = []
    provenance = []
    for entry in manifest["files"]:
        payload = (root / entry["path"]).read_bytes()
        if hashlib.sha256(payload).hexdigest() != entry["sha256"]:
            raise ValueError(f"Checksum mismatch: {entry['path']}")
        summary = json.loads(payload)
        run = summary["run"]
        if run != entry["run"]:
            raise ValueError(f"Run mismatch: {entry['path']}")
        summary = select_analysis_summary(summary)
        if summary is None:
            continue
        identity = {
            "view": entry["terminology_view"],
            "category": entry["category"],
            "run": run,
            "population": population(run),
            "model": LABELS.get(run, run),
        }
        summaries[(identity["view"], identity["category"], run)] = summary
        provenance.append(
            {
                **identity,
                "model_id": (summary["metadata"].get("model") or {}).get("model_id"),
                "source_path": entry["path"],
                "source_url": entry["source_url"],
                "sha256": entry["sha256"],
                "evaluation_signature": summary.get("evaluation_signature"),
            }
        )
        for dataset, settings in summary["dataset_settings"].items():
            for setting, group in settings.items():
                counts = [item["counts"] for item in group["by_direction"].values()]
                coverage.append(
                    {
                        **identity,
                        "dataset": dataset,
                        "setting": setting,
                        "directions": len(counts),
                        "rows_translated": sum(item["rows_translated"] for item in counts),
                        "reported_expected_rows": (
                            sum(item["rows_expected"] for item in counts)
                            if all(item.get("rows_expected") is not None for item in counts)
                            else None
                        ),
                        "reported_missing_rows": (
                            sum(item["rows_missing"] for item in counts)
                            if all(item.get("rows_missing") is not None for item in counts)
                            else None
                        ),
                        "unattributed_missing_rows": group.get("unattributed_missing_rows"),
                    }
                )
                for direction, result in group["by_direction"].items():
                    flat = {
                        **identity,
                        "dataset": dataset,
                        "setting": setting,
                        "direction": direction,
                    }
                    for section in (
                        "counts",
                        "corpus_metrics",
                        "mean_metrics",
                        "metric_counts",
                        "metric_applicable_counts",
                    ):
                        flat.update(
                            {
                                f"{section}.{key}": value
                                for key, value in result.get(section, {}).items()
                            }
                        )
                    flat.update(
                        {
                            f"status.{key}": value.get("state")
                            for key, value in result["metric_status"].items()
                        }
                    )
                    details.append(flat)
    for (view, category, run), summary in summaries.items():
        baseline = summaries[("original_glm", "all_terms", run)]
        for dataset, settings in summary["dataset_settings"].items():
            for setting, group in settings.items():
                original = baseline["dataset_settings"][dataset][setting]["by_direction"]
                if set(group["by_direction"]) != set(original):
                    raise ValueError(f"General-score direction mismatch: {view}/{category}/{run}")
                for direction, result in group["by_direction"].items():
                    for metric in GENERAL:
                        if metric_value(result, metric) != metric_value(
                            original[direction], metric
                        ):
                            raise ValueError(
                                f"General scores differ: {view}/{category}/{run}/{metric}"
                            )
    return summaries, details, coverage, provenance


def build_aggregates(summaries):
    summaries = {
        key: selected
        for key, summary in summaries.items()
        if (selected := select_analysis_summary({**summary, "run": key[2]})) is not None
    }
    runs = sorted(
        run
        for view, category, run in summaries
        if view == "original_glm" and category == "all_terms" and population(run) == "current"
    )
    if set(runs) != set(LABELS):
        raise ValueError("Unexpected current model population")
    aggregates = []
    tracks = [("original_glm", "all_terms", GENERAL)]
    tracks += [(view, category, TERMINOLOGY) for view in VIEWS for category in CATEGORIES]
    for view, category, metrics in tracks:
        for dataset in DATASETS:
            groups = {
                (run, setting): summaries[(view, category, run)]["dataset_settings"][dataset][
                    setting
                ]["by_direction"]
                for run in runs
                for setting in SETTINGS
            }
            for metric in metrics:
                supports = [
                    {
                        direction
                        for direction, result in group.items()
                        if metric_value(result, metric) is not None
                    }
                    for group in groups.values()
                ]
                common = sorted(set.intersection(*supports))
                for (run, setting), group in groups.items():
                    status = [group[direction]["metric_status"][metric] for direction in common]
                    available = [item["metric_status"].get(metric, {}) for item in group.values()]
                    aggregates.append(
                        {
                            "view": "shared_general" if metric in GENERAL else view,
                            "category": "not_applicable" if metric in GENERAL else category,
                            "dataset": dataset,
                            "setting": setting,
                            "run": run,
                            "model": LABELS[run],
                            "metric": metric,
                            "value": direction_macro(group, metric, common),
                            "statistic": "direction_macro_corpus_score"
                            if metric in CORPUS
                            else "direction_macro_segment_mean",
                            "n_directions": len(common),
                            "directions": ";".join(common),
                            "rows_scored_in_common_directions": sum(
                                item["rows_scored"] for item in status
                            ),
                            "rows_applicable_in_common_directions": sum(
                                item.get("rows_applicable", item["rows_scored"]) for item in status
                            ),
                            "available_scored_rows": sum(
                                item.get("rows_scored", 0) for item in available
                            ),
                            "available_applicable_rows": sum(
                                item.get("rows_applicable", 0) for item in available
                            ),
                            "available_directions": sum(
                                metric_value(item, metric) is not None for item in group.values()
                            ),
                        }
                    )
    return aggregates, runs


def build_metric_correlations(summaries, runs):
    import numpy as np
    from scipy.stats import pearsonr, spearmanr

    columns = [("not_applicable", metric) for metric in GENERAL] + [
        (category, metric) for category in CATEGORIES for metric in TERMINOLOGY
    ]
    rows = []
    for view in VIEWS:
        for dataset in (*DATASETS, "all_datasets"):
            datasets = tuple(DATASETS) if dataset == "all_datasets" else (dataset,)
            groups = {
                (member, category, run, setting): summaries[(view, category, run)][
                    "dataset_settings"
                ][member][setting]["by_direction"]
                for member in datasets
                for category in CATEGORIES
                for run in runs
                for setting in SETTINGS
            }
            support = {}
            for member in datasets:
                for metric in (*GENERAL, *TERMINOLOGY):
                    categories = CATEGORIES if metric in TERMINOLOGY else ("all_terms",)
                    direction_sets = [
                        {
                            direction
                            for direction, result in groups[
                                (member, category, run, setting)
                            ].items()
                            if metric_value(result, metric) is not None
                        }
                        for category in categories
                        for run in runs
                        for setting in SETTINGS
                    ]
                    support[(member, metric)] = set.intersection(*direction_sets)
            for setting in SETTINGS:
                for index, (category_x, metric_x) in enumerate(columns):
                    for category_y, metric_y in columns[index:]:
                        directions_by_dataset = {
                            member: sorted(
                                support[(member, metric_x)] & support[(member, metric_y)]
                            )
                            for member in datasets
                        }
                        complete = all(directions_by_dataset.values())
                        values = []
                        for category, metric in ((category_x, metric_x), (category_y, metric_y)):
                            source_category = (
                                "all_terms" if category == "not_applicable" else category
                            )
                            values.append(
                                [
                                    mean(
                                        direction_macro(
                                            groups[(member, source_category, run, setting)],
                                            metric,
                                            directions_by_dataset[member],
                                        )
                                        for member in datasets
                                    )
                                    if complete
                                    else None
                                    for run in runs
                                ]
                            )
                        state = "completed"
                        if not complete or len(runs) < 3:
                            state = "insufficient_support"
                        elif any(np.ptp(scores) == 0 for scores in values):
                            state = "constant_scores"
                        for method, function in (("pearson", pearsonr), ("spearman", spearmanr)):
                            coefficient = None
                            if state == "completed":
                                coefficient = float(function(*values).statistic)
                                if not math.isfinite(coefficient):
                                    coefficient = None
                            rows.append(
                                {
                                    "view": view,
                                    "dataset": dataset,
                                    "setting": setting,
                                    "method": method,
                                    "category_x": category_x,
                                    "metric_x": metric_x,
                                    "category_y": category_y,
                                    "metric_y": metric_y,
                                    "correlation": coefficient,
                                    "state": state
                                    if coefficient is not None
                                    else (state if state != "completed" else "undefined"),
                                    "n_models": len(runs) if complete else 0,
                                    "n_datasets": len(datasets),
                                    "statistic": "equal_dataset_mean_of_direction_macros"
                                    if dataset == "all_datasets"
                                    else "direction_macro",
                                    "n_directions": sum(map(len, directions_by_dataset.values())),
                                    "directions": ";".join(directions_by_dataset[datasets[0]])
                                    if len(datasets) == 1
                                    else "",
                                    "directions_by_dataset": json.dumps(directions_by_dataset),
                                    "runs": ";".join(runs),
                                }
                            )
    return rows


def select_distinct_metric_columns(correlations, count=4):
    rows = [row for row in correlations if row["dataset"] == "all_datasets"]
    contexts = {(row["view"], row["setting"], row["method"]) for row in rows}
    values = defaultdict(dict)
    for row in rows:
        if row["correlation"] is None or not math.isfinite(row["correlation"]):
            continue
        pair = tuple(
            sorted(((row["category_x"], row["metric_x"]), (row["category_y"], row["metric_y"])))
        )
        context = (row["view"], row["setting"], row["method"])
        if context in values[pair]:
            raise ValueError(f"Duplicate correlation context: {pair}/{context}")
        values[pair][context] = abs(row["correlation"])
    columns = sorted(
        pair[0]
        for pair, supported in values.items()
        if pair[0] == pair[1] and set(supported) == contexts
    )
    candidates = []
    for selected in combinations(columns, count):
        if len({metric for _, metric in selected}) != count:
            continue
        pairs = [tuple(sorted(pair)) for pair in combinations(selected, 2)]
        if any(set(values[pair]) != contexts for pair in pairs):
            continue
        scores = [value for pair in pairs for value in values[pair].values()]
        candidates.append((mean(scores), max(scores), selected))
    if not candidates:
        raise ValueError(f"No fully supported selection of {count} distinct metrics")
    score, maximum, selected = min(
        candidates,
        key=lambda candidate: (round(candidate[0], 12), round(candidate[1], 12), candidate[2]),
    )
    return [
        {
            "category": category,
            "metric": metric,
            "label": METRIC_LABELS[metric],
            "mean_absolute_correlation": score,
            "max_absolute_correlation": maximum,
            "n_contexts": len(contexts),
            "n_candidate_sets": len(candidates),
            "selection": "minimum_mean_absolute_pearson_and_spearman_all_datasets",
            "tie_break": "minimum_maximum_absolute_correlation_then_column_name",
        }
        for category, metric in selected
    ]


def build_statistic_aggregates(aggregates, points, statistic):
    if statistic not in ("median", "top"):
        raise ValueError(f"Unknown ranking statistic: {statistic}")
    fields = ("view", "category", "dataset", "setting", "run", "metric")
    groups = defaultdict(dict)
    for row in select_analysis_points(points):
        key = tuple(row[field] for field in fields)
        if row["direction"] in groups[key]:
            raise ValueError("Duplicate ranking direction score")
        value = float(row["value"])
        if not math.isfinite(value):
            raise ValueError("Ranking statistics require finite direction scores")
        groups[key][row["direction"]] = value
    result = []
    for row in aggregates:
        if population(row["run"]) == "excluded":
            continue
        key = tuple(row[field] for field in fields)
        selected = groups[key]
        directions = set(filter(None, row["directions"].split(";")))
        if set(selected) != directions or len(directions) != int(row["n_directions"]):
            raise ValueError(
                f"Ranking statistics require identical common direction support: {key}"
            )
        values = list(selected.values())
        value = (median(values) if statistic == "median" else max(values)) if values else None
        result.append(
            {
                **row,
                "value": value,
                "statistic": f"direction_{statistic}",
                "top_directions": ";".join(
                    sorted(
                        direction
                        for direction, score in selected.items()
                        if statistic == "top" and score == value
                    )
                ),
            }
        )
    return result


def build_mixed_rank_rows(aggregates, runs, *, labels=None, datasets=None, views=None):
    import numpy as np
    from scipy.stats import rankdata

    labels = LABELS if labels is None else labels
    datasets = DATASETS if datasets is None else datasets
    views = VIEWS if views is None else views
    lookup = {
        (
            row["view"],
            row["category"],
            row["dataset"],
            row["setting"],
            row["run"],
            row["metric"],
        ): row
        for row in aggregates
    }
    ranked = []
    components = []
    for view in views:
        strata = []
        for dataset in datasets:
            for setting in SETTINGS:
                records = {
                    run: {
                        "view": view,
                        "scope": "dataset_prompt",
                        "dataset": dataset,
                        "setting": setting,
                        "run": run,
                        "model": labels[run],
                        "n_strata": 1,
                    }
                    for run in runs
                }
                for family, metrics in RANK_FAMILIES.items():
                    categories = CATEGORIES if family == "terminology" else ("not_applicable",)
                    category_ranks = []
                    for category in categories:
                        metric_ranks = []
                        for metric in metrics:
                            source_view = view if family == "terminology" else "shared_general"
                            source = [
                                lookup[(source_view, category, dataset, setting, run, metric)]
                                for run in runs
                            ]
                            values = [row["value"] for row in source]
                            finite = [
                                value is not None and math.isfinite(value) for value in values
                            ]
                            if not any(finite):
                                continue
                            if not all(finite):
                                raise ValueError(
                                    f"Incomplete model support: {view}/{dataset}/{metric}"
                                )
                            ranks = rankdata(-np.asarray(values), method="average")
                            metric_ranks.append(ranks)
                            for run, row, rank in zip(runs, source, ranks, strict=True):
                                key = f"{category}.{metric}"
                                records[run][key] = row["value"]
                                records[run][f"{key}.rank"] = float(rank)
                                components.append(
                                    {
                                        **row,
                                        "view": view,
                                        "family": family,
                                        "metric_rank": float(rank),
                                    }
                                )
                        if not metric_ranks:
                            raise ValueError(
                                f"No ranked metrics: {view}/{dataset}/{family}/{category}"
                            )
                        category_ranks.append(np.mean(metric_ranks, axis=0))
                    family_ranks = np.mean(category_ranks, axis=0)
                    for run, rank in zip(runs, family_ranks, strict=True):
                        records[run][f"{family}_mean_rank"] = float(rank)
                strata.extend(records.values())
        overall = []
        for run in runs:
            selected = [row for row in strata if row["run"] == run]
            numeric_keys = [key for key in selected[0] if key.endswith("_mean_rank") or "." in key]
            if any(
                set(key for key in row if "." in key)
                != set(key for key in selected[0] if "." in key)
                for row in selected
            ):
                raise ValueError(
                    "Overall scorecard requires identical metric availability per stratum"
                )
            overall.append(
                {
                    "view": view,
                    "scope": "overall",
                    "dataset": "all_datasets",
                    "setting": "both_prompts",
                    "run": run,
                    "model": labels[run],
                    "n_strata": len(selected),
                    **{key: mean(row[key] for row in selected) for key in numeric_keys},
                }
            )
        groups = defaultdict(list)
        for row in [*strata, *overall]:
            row["mixed_mean_rank"] = mean(row[f"{family}_mean_rank"] for family in RANK_FAMILIES)
            groups[(row["scope"], row["dataset"], row["setting"])].append(row)
        for rows in groups.values():
            ranks = rankdata([round(row["mixed_mean_rank"], 12) for row in rows], method="min")
            for row, rank in zip(rows, ranks, strict=True):
                row["mixed_rank"] = int(rank)
            ranked.extend(sorted(rows, key=lambda row: (row["mixed_rank"], row["run"])))
    return ranked, components


def table_text(rows, metrics):
    lookup = {(row["run"], row["metric"]): row for row in rows}
    runs = sorted({row["run"] for row in rows})
    headers = ["Model"] + [METRIC_LABELS[metric] for metric in metrics]
    body = []
    for run in runs:
        cells = [LABELS[run]]
        for metric in metrics:
            row = lookup[(run, metric)]
            digits = (
                2
                if metric in CORPUS or (metric in TERMINOLOGY and metric != "term_bertscore_recall")
                else 3
            )
            cells.append("NA" if row["value"] is None else f"{row['value']:.{digits}f}")
        body.append(cells)
    markdown = ["| " + " | ".join(headers) + " |", "| " + " | ".join(["---"] * len(headers)) + " |"]
    markdown += ["| " + " | ".join(cells) + " |" for cells in body]
    latex = [
        "\\begin{tabular}{l" + "r" * len(metrics) + "}",
        "\\hline",
        " & ".join(headers) + r" \\",
        "\\hline",
    ]
    latex += [" & ".join(cells) + r" \\" for cells in body]
    latex += ["\\hline", "\\end{tabular}"]
    return "\n".join(markdown), "\n".join(latex)


def write_tables(output, aggregates, *, statistic=None):
    tables = output / "tables"
    if statistic is not None:
        tables = tables / "rankings" / statistic
    tables.mkdir(parents=True, exist_ok=True)
    write_csv(
        tables / "translation_quality.csv", [row for row in aggregates if row["metric"] in GENERAL]
    )
    write_csv(
        tables / "terminology.csv", [row for row in aggregates if row["metric"] in TERMINOLOGY]
    )
    groups = defaultdict(list)
    for row in aggregates:
        groups[(row["view"], row["category"], row["dataset"], row["setting"])].append(row)
    markdown = [
        "# Benchmark Performance Tables",
        "",
        "Descriptive direction-macro scores on directions shared by all selected current runs "
        "and both prompt settings within each metric/dataset/view/subset. "
        "NA means no common scored support, never zero. Counts are in the CSV files. "
        "Different rows may still contain different translation examples. No significance claims.",
        "",
    ]
    if statistic is not None:
        markdown[:4] = [
            f"# {statistic.title()} Direction-Score Tables",
            "",
            f"Native metric values use the {'median' if statistic == 'median' else 'maximum'} "
            "over the same directions shared across models and both prompts. Each direction "
            "has equal weight; this is not a per-translation statistic. NA is unavailable, "
            "not zero. See [model rankings](rankings.md) for balanced family ranks.",
            "",
        ]
    latex = ["% Descriptive direction-macro scores; NA is unavailable, not zero."]
    for (view, category, dataset, setting), rows in groups.items():
        metrics = GENERAL if view == "shared_general" else TERMINOLOGY
        title = f"{DATASETS[dataset]} / {setting.replace('_', ' ')} / {view} / {category}"
        supports = {row["metric"]: row["n_directions"] for row in rows}
        support = "; ".join(
            f"{METRIC_LABELS[metric]}: {supports[metric]} directions" for metric in metrics
        )
        md_table, tex_table = table_text(rows, metrics)
        markdown += [f"## {title}", "", support, "", md_table, ""]
        escaped_title = title.replace("_", r"\_")
        latex += [
            f"% {support}",
            "\\par\\medskip",
            f"\\noindent\\textbf{{{escaped_title}}}\\par",
            "\\noindent\\resizebox{\\linewidth}{!}{%",
            tex_table,
            "}",
            "",
        ]
    (tables / "performance.md").write_text("\n".join(markdown), encoding="utf-8")
    (tables / "performance.tex").write_text("\n".join(latex), encoding="utf-8")


def build_bubble_rows(summaries, runs, view="luna", category="all_terms"):
    metrics = ("comet", "target_term_coverage", "bleu")
    groups = {
        (run, setting): summaries[(view, category, run)]["dataset_settings"]["google_patents"][
            setting
        ]["by_direction"]
        for run in runs
        for setting in SETTINGS
    }
    supports = [
        {
            direction
            for direction, result in group.items()
            if all(metric_value(result, metric) is not None for metric in metrics)
        }
        for group in groups.values()
    ]
    common = sorted(set.intersection(*supports))
    if not common:
        raise ValueError("No common scored directions for the three bubble-chart metrics")
    rows = []
    for (run, setting), group in groups.items():
        row = {
            "run": run,
            "model": LABELS[run],
            "dataset": "google_patents",
            "setting": setting,
            "view": view,
            "category": category,
            "n_directions": len(common),
            "directions": ";".join(common),
        }
        for metric in metrics:
            row[metric] = direction_macro(group, metric, common)
            row[f"{metric}_rows_scored"] = sum(
                group[direction]["metric_status"][metric]["rows_scored"] for direction in common
            )
        rows.append(row)
    return rows


def bubble_area(bleu):
    if not math.isfinite(bleu) or bleu < 0:
        raise ValueError("Bubble area requires a finite nonnegative BLEU score")
    return 36 * bleu


def build_language_mixed_rank_rows(points, runs):
    runs = [run for run in runs if population(run) != "excluded"]
    groups = defaultdict(lambda: defaultdict(dict))
    for row in select_analysis_points(points):
        key = tuple(row[field] for field in ("view", "category", "dataset", "metric"))
        model_key = (row["run"], row["setting"])
        if row["direction"] in groups[key][model_key]:
            raise ValueError("Duplicate language ranking direction score")
        value = float(row["value"])
        if not math.isfinite(value):
            raise ValueError("Language ranking requires finite native scores")
        groups[key][model_key][row["direction"]] = value
    native = []
    for (view, category, dataset, metric), models in sorted(groups.items()):
        common = set.intersection(
            *(set(models[(run, setting)]) for run in runs for setting in SETTINGS)
        )
        for role, position in (("from", 0), ("to", 1)):
            partners = defaultdict(list)
            for direction in sorted(common):
                partners[direction.split("-")[position]].append(direction)
            for language, directions in sorted(partners.items()):
                for setting in SETTINGS:
                    values = [
                        mean(models[(run, setting)][direction] for direction in directions)
                        for run in runs
                    ]
                    for statistic in ("median", "top"):
                        value = median(values) if statistic == "median" else max(values)
                        native.append(
                            {
                                "view": view,
                                "category": category,
                                "dataset": dataset,
                                "setting": setting,
                                "metric": metric,
                                "role": role,
                                "statistic": statistic,
                                "run": language,
                                "model": LANGUAGE_LABELS.get(language, language),
                                "value": value,
                                "n_models": len(runs),
                                "n_directions": len(directions),
                                "directions": ";".join(directions),
                                "runs": ";".join(runs),
                                "model_values": json.dumps(values),
                                "top_models": ";".join(
                                    run
                                    for run, score in zip(runs, values, strict=True)
                                    if statistic == "top" and score == value
                                ),
                            }
                        )
    ranked, components, support = [], [], []
    fields = ("view", "category", "dataset", "setting", "metric")
    for statistic in ("median", "top"):
        for role in ("from", "to"):
            selected = [
                row for row in native if row["statistic"] == statistic and row["role"] == role
            ]
            for view in VIEWS:
                for scope, datasets in [
                    *(("dataset_prompt", (dataset,)) for dataset in DATASETS),
                    ("overall", tuple(DATASETS)),
                ]:
                    overall = scope == "overall"
                    expected = set()
                    for dataset in datasets:
                        for family, metrics in RANK_FAMILIES.items():
                            source_view = view if family == "terminology" else "shared_general"
                            categories = (
                                CATEGORIES if family == "terminology" else ("not_applicable",)
                            )
                            for category in categories:
                                active = [
                                    metric
                                    for metric in metrics
                                    if (source_view, category, dataset, metric) in groups
                                ]
                                if not active:
                                    raise ValueError(
                                        "Missing language rank family: "
                                        f"{view}/{dataset}/{family}/{category}"
                                    )
                                expected.update(
                                    (source_view, category, dataset, setting, metric)
                                    for setting in SETTINGS
                                    for metric in active
                                )
                    candidates = [
                        row for row in selected if tuple(row[field] for field in fields) in expected
                    ]
                    availability = defaultdict(set)
                    for row in candidates:
                        availability[row["run"]].add(tuple(row[field] for field in fields))
                    eligible = sorted(
                        language for language, keys in availability.items() if keys == expected
                    )
                    scope = "overall" if overall else "dataset_prompt"
                    for language, keys in sorted(availability.items()):
                        support.append(
                            {
                                "view": view,
                                "statistic": statistic,
                                "role": role,
                                "scope": scope,
                                "dataset": "all_datasets" if overall else datasets[0],
                                "language": language,
                                "state": "completed"
                                if language in eligible
                                else "incomplete_metric_strata",
                                "n_components": len(keys),
                                "required_components": len(expected),
                                "missing_components": json.dumps(sorted(expected - keys)),
                                "n_ranked_languages": len(eligible),
                                "n_models": len(runs),
                            }
                        )
                    if not eligible:
                        continue
                    rank_source = [row for row in candidates if row["run"] in eligible]
                    for dataset in datasets:
                        for family, metrics in RANK_FAMILIES.items():
                            source_view = view if family == "terminology" else "shared_general"
                            categories = (
                                CATEGORIES if family == "terminology" else ("not_applicable",)
                            )
                            for category in categories:
                                for metric in metrics:
                                    if (source_view, category, dataset, metric) in groups:
                                        continue
                                    rank_source.extend(
                                        {
                                            "view": source_view,
                                            "category": category,
                                            "dataset": dataset,
                                            "setting": setting,
                                            "run": language,
                                            "metric": metric,
                                            "value": None,
                                        }
                                        for setting in SETTINGS
                                        for language in eligible
                                    )
                    rows, details = build_mixed_rank_rows(
                        rank_source,
                        eligible,
                        labels={
                            language: LANGUAGE_LABELS.get(language, language)
                            for language in eligible
                        },
                        datasets=datasets,
                        views=(view,),
                    )
                    ranked.extend(
                        {
                            **row,
                            "statistic": statistic,
                            "role": role,
                            "language": row["run"],
                            "language_name": row["model"],
                            "n_models": len(runs),
                            "n_ranked_languages": len(eligible),
                        }
                        for row in rows
                        if row["scope"] == scope
                    )
                    components.extend(
                        {
                            **row,
                            "ranking_scope": scope,
                            "ranking_view": view,
                            "language": row["run"],
                            "language_name": row["model"],
                        }
                        for row in details
                    )
    return ranked, components, native, support


def build_language_direction_rows(points, runs):
    from scipy.stats import rankdata

    points = select_analysis_points(points)
    runs = [run for run in runs if population(run) != "excluded"]
    lookup = {}
    for row in points:
        value = float(row["value"])
        if not math.isfinite(value):
            raise ValueError("Language analysis requires finite native scores")
        key = tuple(
            row[field]
            for field in ("view", "dataset", "category", "metric", "run", "setting", "direction")
        )
        if key in lookup:
            raise ValueError(f"Duplicate language score: {key}")
        lookup[key] = {**row, "value": value}
    balanced, components, support = [], [], []
    for view in VIEWS:
        for dataset in DATASETS:
            blocks = []
            for family, metrics in RANK_FAMILIES.items():
                source_view = view if family == "terminology" else "shared_general"
                categories = CATEGORIES if family == "terminology" else ("not_applicable",)
                for category in categories:
                    active = []
                    for metric in metrics:
                        available = {
                            key[-1]
                            for key in lookup
                            if key[:4] == (source_view, dataset, category, metric)
                        }
                        if not available:
                            continue
                        directions = {
                            direction
                            for direction in available
                            if all(
                                (source_view, dataset, category, metric, run, setting, direction)
                                in lookup
                                for run in runs
                                for setting in SETTINGS
                            )
                        }
                        active.append((metric, directions))
                    if not active:
                        raise ValueError(
                            f"No language metrics: {view}/{dataset}/{family}/{category}"
                        )
                    blocks.extend(
                        (family, source_view, category, metric, directions)
                        for metric, directions in active
                    )
            common = sorted(set.intersection(*(block[-1] for block in blocks)))
            support.append(
                {
                    "view": view,
                    "dataset": dataset,
                    "n_models": len(runs),
                    "n_common_directions": len(common),
                    "directions": ";".join(common),
                    "n_metric_components": len(blocks),
                    "state": "completed" if len(common) >= 2 else "insufficient_common_directions",
                }
            )
            if len(common) < 2:
                continue
            pool = [(setting, direction) for setting in SETTINGS for direction in common]
            scores = defaultdict(lambda: defaultdict(lambda: defaultdict(list)))
            counts = defaultdict(list)
            for family, source_view, category, metric, _ in blocks:
                for run in runs:
                    source = [
                        lookup[(source_view, dataset, category, metric, run, setting, direction)]
                        for setting, direction in pool
                    ]
                    ranks = rankdata([-row["value"] for row in source], method="average")
                    for (setting, direction), row, rank in zip(pool, source, ranks, strict=True):
                        score = 100 * (len(pool) - float(rank)) / (len(pool) - 1)
                        scores[(run, setting, direction)][family][category].append(score)
                        counts[(run, setting, direction)].append(int(row["rows_scored"]))
                        components.append(
                            {
                                **row,
                                "view": view,
                                "family": family,
                                "direction_prompt_rank": float(rank),
                                "rank_pool_size": len(pool),
                                "rank_percentile_score": score,
                            }
                        )
            for (run, setting, direction), families in scores.items():
                family_scores = {
                    f"{family}_score": mean(mean(values) for values in categories.values())
                    for family, categories in families.items()
                }
                source_language, target_language = direction.split("-", 1)
                balanced.append(
                    {
                        "view": view,
                        "dataset": dataset,
                        "setting": setting,
                        "run": run,
                        "model": LABELS[run],
                        "direction": direction,
                        "source_language": source_language,
                        "target_language": target_language,
                        **family_scores,
                        "balanced_score": mean(family_scores.values()),
                        "n_common_directions": len(common),
                        "rank_pool_size": len(pool),
                        "min_rows_scored": min(counts[(run, setting, direction)]),
                        "max_rows_scored": max(counts[(run, setting, direction)]),
                    }
                )
    return balanced, components, support


def aggregate_language_pairs(balanced, runs):
    from scipy.stats import rankdata

    fields = ("balanced_score", "semantic_score", "lexical_score", "terminology_score")
    model_groups = defaultdict(list)
    for row in balanced:
        model_groups[(row["view"], row["dataset"], row["direction"], row["run"])].append(row)
    combined = []
    for rows in model_groups.values():
        if {row["setting"] for row in rows} != set(SETTINGS):
            raise ValueError("Language pair requires both prompt settings")
        combined.append(
            {
                **rows[0],
                "setting": "both_prompts",
                **{field: mean(row[field] for row in rows) for field in fields},
            }
        )
    overall_groups = defaultdict(list)
    for row in [*balanced, *combined]:
        overall_groups[(row["view"], row["setting"], row["direction"], row["run"])].append(row)
    overall = []
    for rows in overall_groups.values():
        if {row["dataset"] for row in rows} == set(DATASETS):
            overall.append(
                {
                    **rows[0],
                    "dataset": "all_datasets",
                    **{field: mean(row[field] for row in rows) for field in fields},
                }
            )
    groups = defaultdict(list)
    for row in [*balanced, *combined, *overall]:
        groups[(row["view"], row["dataset"], row["setting"], row["direction"])].append(row)
    pairs = []
    for rows in groups.values():
        if {row["run"] for row in rows} != set(runs) or len(rows) != len(runs):
            raise ValueError("Language pair requires identical model support")
        pairs.append(
            {
                **{
                    field: rows[0][field]
                    for field in (
                        "view",
                        "dataset",
                        "setting",
                        "direction",
                        "source_language",
                        "target_language",
                    )
                },
                **{field: mean(row[field] for row in rows) for field in fields},
                "n_models": len(runs),
                "n_datasets": len(DATASETS) if rows[0]["dataset"] == "all_datasets" else 1,
            }
        )
    strata = defaultdict(list)
    for row in pairs:
        strata[(row["view"], row["dataset"], row["setting"])].append(row)
    for rows in strata.values():
        ranks = rankdata([-round(row["balanced_score"], 12) for row in rows], method="min")
        for row, rank in zip(rows, ranks, strict=True):
            row["direction_rank"] = int(rank)
    return pairs, overall


def build_language_rankings(balanced, runs):
    from scipy.stats import rankdata

    fields = ("balanced_score", "semantic_score", "lexical_score", "terminology_score")
    languages = sorted(
        {row[field] for row in balanced for field in ("source_language", "target_language")}
    )
    results = {"from": [], "to": []}
    for role, language_field, partner_field in (
        ("from", "source_language", "target_language"),
        ("to", "target_language", "source_language"),
    ):
        lookup = defaultdict(list)
        for row in balanced:
            lookup[(row["view"], row["dataset"], row["setting"], row[language_field])].append(row)
        for view in VIEWS:
            for dataset in (*DATASETS, "all_datasets"):
                for setting in (*SETTINGS, "both_prompts"):
                    rows = []
                    datasets = list(DATASETS) if dataset == "all_datasets" else [dataset]
                    settings = list(SETTINGS) if setting == "both_prompts" else [setting]
                    for language in languages:
                        strata, partners = [], {}
                        for data in datasets:
                            for prompt in settings:
                                source = lookup[(view, data, prompt, language)]
                                if not source:
                                    continue
                                by_model = defaultdict(list)
                                for row in source:
                                    by_model[row["run"]].append(row)
                                if set(by_model) != set(runs):
                                    raise ValueError("Language ranking requires every model")
                                strata.append(
                                    {
                                        field: mean(
                                            mean(row[field] for row in group)
                                            for group in by_model.values()
                                        )
                                        for field in fields
                                    }
                                )
                                partners[data] = sorted({row[partner_field] for row in source})
                        complete = len(strata) == len(datasets) * len(settings)
                        rows.append(
                            {
                                "view": view,
                                "dataset": dataset,
                                "setting": setting,
                                "role": role,
                                "language": language,
                                "language_rank": None,
                                **{
                                    field: mean(row[field] for row in strata) if complete else None
                                    for field in fields
                                },
                                "state": "completed"
                                if complete
                                else "incomplete_dataset_prompt_support",
                                "n_models": len(runs) if strata else 0,
                                "n_strata": len(strata),
                                "required_strata": len(datasets) * len(settings),
                                "n_datasets": len(partners),
                                "partners_by_dataset": json.dumps(partners, sort_keys=True),
                            }
                        )
                    available = [row for row in rows if row["balanced_score"] is not None]
                    ranks = rankdata(
                        [-round(row["balanced_score"], 12) for row in available], method="min"
                    )
                    for row, rank in zip(available, ranks, strict=True):
                        row["language_rank"] = int(rank)
                    results[role].extend(
                        sorted(
                            rows,
                            key=lambda row: (row["language_rank"] or math.inf, row["language"]),
                        )
                    )
    return results["from"], results["to"]


LANGUAGE_LABELS = {
    "de": "German",
    "en": "English",
    "es": "Spanish",
    "fr": "French",
    "ja": "Japanese",
    "pt": "Portuguese",
    "ru": "Russian",
    "zh": "Chinese",
}


BEST_LANGUAGE_METRICS = ("comet", "chrf2++", "variant_aware_target_term_coverage")


def build_best_language_rows(points, runs):
    points = select_analysis_points(points)
    runs = [run for run in runs if population(run) != "excluded"]
    groups = defaultdict(dict)
    model_rows = []
    for row in points:
        if row["metric"] not in BEST_LANGUAGE_METRICS:
            continue
        value = float(row["value"])
        if not math.isfinite(value):
            raise ValueError("Best-language analysis requires finite native scores")
        key = tuple(row[field] for field in ("view", "dataset", "category", "metric", "direction"))
        model_key = (row["run"], row["setting"])
        if model_key in groups[key]:
            raise ValueError("Duplicate best-language model score")
        groups[key][model_key] = {**row, "value": value}
    required = {(run, setting) for run in runs for setting in SETTINGS}
    summaries = []
    for key, models in groups.items():
        if set(models) != required:
            raise ValueError(f"Best-language analysis requires every model and both prompts: {key}")
        for setting in SETTINGS:
            selected = [models[(run, setting)] for run in runs]
            model_rows.extend(selected)
            values = [row["value"] for row in selected]
            best = max(values)
            winners = [row["run"] for row in selected if row["value"] == best]
            summaries.append(
                {
                    **dict(
                        zip(
                            ("view", "dataset", "category", "metric", "direction"), key, strict=True
                        )
                    ),
                    "setting": setting,
                    "best_score": best,
                    "median_score": median(values),
                    "mean_score": mean(values),
                    "worst_score": min(values),
                    "best_minus_median": best - median(values),
                    "n_models": len(runs),
                    "best_runs": ";".join(winners),
                    "best_models": ";".join(LABELS[run] for run in winners),
                    "n_tied_best": len(winners),
                    "min_rows_scored": min(int(row["rows_scored"]) for row in selected),
                    "max_rows_scored": max(int(row["rows_scored"]) for row in selected),
                }
            )
    strata = defaultdict(list)
    for row in summaries:
        strata[
            tuple(row[field] for field in ("view", "dataset", "category", "metric", "setting"))
        ].append(row)
    from scipy.stats import rankdata

    for rows in strata.values():
        ranks = rankdata([row["best_score"] for row in rows], method="min")
        for row, rank in zip(rows, ranks, strict=True):
            row["hardest_pair_rank"] = int(rank)
    return summaries, model_rows


def write_best_language_figures(output, points, runs):
    import matplotlib.pyplot as plt
    import numpy as np
    from matplotlib.lines import Line2D

    summaries, models = build_best_language_rows(points, runs)
    (output / "tables").mkdir(parents=True, exist_ok=True)
    write_csv(output / "tables/best_language_pairs.csv", summaries)
    write_csv(output / "tables/best_language_model_points.csv", models)
    groups = defaultdict(list)
    for row in summaries:
        groups[(row["view"], row["dataset"], row["setting"])].append(row)
    model_lookup = {
        tuple(
            row[field]
            for field in ("view", "dataset", "setting", "category", "metric", "direction", "run")
        ): row["value"]
        for row in models
    }
    model_ids = {run: index + 1 for index, run in enumerate(runs)}
    colors = plt.get_cmap("tab10")
    saved = []

    def save(figure, relative):
        for extension in ("png", "pdf"):
            path = output / "figures" / f"{relative}.{extension}"
            path.parent.mkdir(parents=True, exist_ok=True)
            figure.savefig(path, dpi=160, bbox_inches="tight")
        plt.close(figure)
        saved.append(relative)

    def heatmap(axis, rows, field, limits, title, winners=False):
        languages = sorted({language for row in rows for language in row["direction"].split("-")})
        matrix = np.full((len(languages), len(languages)), np.nan)
        lookup = {row["direction"]: row for row in rows}
        for direction, row in lookup.items():
            source, target = direction.split("-", 1)
            matrix[languages.index(source), languages.index(target)] = row[field]
        cmap = plt.get_cmap("YlGnBu").with_extremes(bad="#eeeeee")
        image = axis.imshow(np.ma.masked_invalid(matrix), cmap=cmap, vmin=limits[0], vmax=limits[1])
        labels = [LANGUAGE_LABELS.get(language, language) for language in languages]
        axis.set_xticks(range(len(languages)), labels, rotation=45, ha="right", fontsize=9)
        axis.set_yticks(range(len(languages)), labels, fontsize=9)
        axis.set(xlabel="To (target language)", ylabel="From (source language)", title=title)
        metric = rows[0]["metric"]
        for source_index, source in enumerate(languages):
            for target_index, target in enumerate(languages):
                row = lookup.get(f"{source}-{target}")
                text = "NA"
                if row is not None:
                    text = f"{row[field]:.3f}" if metric == "comet" else f"{row[field]:.1f}"
                    if winners:
                        winner = min(model_ids[run] for run in row["best_runs"].split(";"))
                        text += f"\nM{winner:02d}" + ("*" if row["n_tied_best"] > 1 else "")
                red, green, blue, _ = (
                    cmap(image.norm(row[field])) if row is not None else (1, 1, 1, 1)
                )
                axis.text(
                    target_index,
                    source_index,
                    text,
                    ha="center",
                    va="center",
                    fontsize=8,
                    color="white"
                    if 0.299 * red + 0.587 * green + 0.114 * blue < 0.5
                    else "#222222",
                )
        axis.figure.colorbar(image, ax=axis, shrink=0.8, label="Native score (higher is better)")

    def legend(figure):
        figure.legend(
            handles=[
                Line2D(
                    [],
                    [],
                    marker="o",
                    linestyle="none",
                    color=colors(index),
                    label=f"M{index + 1:02d}: {LABELS[run]}",
                )
                for index, run in enumerate(runs)
            ],
            loc="lower center",
            bbox_to_anchor=(0.5, 0.055),
            ncol=min(5, len(runs)),
            frameon=False,
            fontsize=9,
        )

    for (view, dataset, setting), rows in groups.items():
        panels = sorted({(row["category"], row["metric"]) for row in rows})
        panel_rows = {
            (category, metric): sorted(
                [row for row in rows if (row["category"], row["metric"]) == (category, metric)],
                key=lambda row: (row["best_score"], row["direction"]),
            )
            for category, metric in panels
        }
        limits = {}
        for category, metric in panels:
            reference = [
                row[field]
                for row in summaries
                for field in ("best_score", "median_score")
                if (row["view"], row["dataset"], row["category"], row["metric"])
                == (view, dataset, category, metric)
            ]
            low, high = min(reference), max(reference)
            padding = (high - low) * 0.03 if high > low else max(abs(low) * 0.03, 0.01)
            limits[(category, metric)] = (low - padding, high + padding)
        context = f"{DATASETS[dataset]} | {view} | {setting.replace('_', ' ').title()}"
        figure, axes = plt.subplots(1, len(panels), figsize=(8 * len(panels), 9), squeeze=False)
        for axis, (category, metric) in zip(axes.flat, panels, strict=True):
            title = METRIC_LABELS[metric] + (
                "" if category == "not_applicable" else "\n" + category.replace("_", " ").title()
            )
            heatmap(
                axis,
                panel_rows[(category, metric)],
                "best_score",
                limits[(category, metric)],
                title,
                winners=True,
            )
        figure.suptitle(f"Best Achieved Model Score | {context}", fontsize=20, y=0.98)
        figure.subplots_adjust(top=0.85, bottom=0.26, wspace=0.4)
        legend(figure)
        figure.text(
            0.5,
            0.012,
            "Each cell selects one model's whole-direction score, not individual "
            "translations. * = tied best (lowest ID shown); all ties in CSV. NA is "
            "unavailable, not zero. Best observed on this evaluation set, not guaranteed "
            "future performance.",
            ha="center",
            fontsize=9,
        )
        save(figure, f"languages/best_models/{view}/best_{dataset}_{setting}")

        figure, axes = plt.subplots(
            len(panels), 2, figsize=(16, 7 * len(panels) + 2), squeeze=False
        )
        for axes_row, (category, metric) in zip(axes, panels, strict=True):
            for axis, field, label in zip(
                axes_row,
                ("best_score", "median_score"),
                ("Best Model", "Median Model"),
                strict=True,
            ):
                title = f"{label} | {METRIC_LABELS[metric]}" + (
                    ""
                    if category == "not_applicable"
                    else "\n" + category.replace("_", " ").title()
                )
                heatmap(
                    axis, panel_rows[(category, metric)], field, limits[(category, metric)], title
                )
        figure.suptitle(f"Best vs Typical Model Performance | {context}", fontsize=20, y=0.98)
        figure.subplots_adjust(top=0.92, bottom=0.10, hspace=0.5, wspace=0.35)
        figure.text(
            0.5,
            0.012,
            "Median is across all models; best is the whole-direction maximum. "
            "Identical native color limits for best/median and both prompts per metric "
            "and term group. Different panels need not share support. No oracle "
            "selection per translation.",
            ha="center",
            fontsize=9,
        )
        save(figure, f"languages/best_vs_median/{view}/comparison_{dataset}_{setting}")

        height = max(9, max(len(group) for group in panel_rows.values()) * 0.36 + 3)
        figure, axes = plt.subplots(
            1, len(panels), figsize=(8 * len(panels), height), squeeze=False
        )
        for axis, (category, metric) in zip(axes.flat, panels, strict=True):
            selected = panel_rows[(category, metric)]
            for index, run in enumerate(runs):
                values = [
                    model_lookup[(view, dataset, setting, category, metric, row["direction"], run)]
                    for row in selected
                ]
                axis.scatter(
                    values,
                    np.arange(len(selected)),
                    color=colors(index),
                    marker="o",
                    s=30,
                    alpha=0.85,
                    zorder=3,
                )
            axis.scatter(
                [row["best_score"] for row in selected],
                np.arange(len(selected)),
                facecolors="none",
                edgecolors="#111111",
                marker="o",
                s=100,
                linewidths=1.2,
                zorder=4,
            )
            labels = []
            for row in selected:
                source, target = row["direction"].split("-", 1)
                labels.append(
                    f"{LANGUAGE_LABELS.get(source, source)} -> "
                    f"{LANGUAGE_LABELS.get(target, target)}"
                )
            axis.set_yticks(range(len(selected)), labels, fontsize=9)
            axis.set_ylim(len(selected) - 0.5, -0.5)
            axis.set_xlabel(f"{METRIC_LABELS[metric]} (native score; higher is better)")
            axis.set_title(
                METRIC_LABELS[metric]
                + (
                    ""
                    if category == "not_applicable"
                    else "\n" + category.replace("_", " ").title()
                )
            )
            axis.grid(axis="x", color="#dddddd", linewidth=0.6)
            axis.set_axisbelow(True)
            axis.spines[["top", "right"]].set_visible(False)
        figure.suptitle(
            f"Hardest Language Pairs by Best Achieved Score | {context}", fontsize=20, y=0.98
        )
        figure.subplots_adjust(top=0.9, bottom=0.20, wspace=0.6)
        legend(figure)
        figure.text(
            0.5,
            0.012,
            "All models shown as colored circles; black ring = best score. "
            "Lowest best-case pairs appear first. Difficulty is benchmark/metric "
            "specific; small samples and test-set winner selection limit generalization.",
            ha="center",
            fontsize=9,
        )
        save(figure, f"languages/hardest_pairs/{view}/hardest_{dataset}_{setting}")
    lines = [
        "# Best Achieved Language-Pair Performance",
        "",
        "Three views: best-model heatmaps with winner IDs; best versus median heatmaps; "
        "hardest-pair plots showing every model, sorted by the whole-direction maximum.",
        "",
        "COMET and chrF++ use the shared general scores. Variant-aware terminology coverage "
        "has separate GLM/Luna views and all/external/LLM-enriched groups. All models and "
        "both prompts must have each direction. Datasets and prompt settings are never "
        "pooled. Model IDs follow the same sorted model order across all figures.",
        "",
        "Every maximum comes from one complete model-direction evaluation, not an oracle "
        "choosing different models per translation. A model can win different pairs or "
        "metrics. Exact ties retain every winner in the CSV; heatmaps show the lowest "
        "winning ID with *. Best observed scores are optimistically selected on the test "
        "set, not an independently validated deployment policy. Low scores indicate "
        "difficulty on these benchmark rows, not intrinsic language difficulty. Consult "
        "scored-row support before interpreting near-perfect small-sample results.",
        "",
        "Best and median use identical color limits, shared across prompts within each "
        "dataset/view/group/metric. Unsupported languages are omitted from the grid; "
        "missing pairs remain NA. Different metrics/groups can have different support.",
        "",
        "- [Best/median scores, winning models, ties and support]"
        "(../../tables/best_language_pairs.csv)",
        "- [All model-direction points](../../tables/best_language_model_points.csv)",
        "",
        "## Figures",
        "",
    ]
    for relative in saved:
        target = Path(relative).relative_to("languages").as_posix()
        lines.append(f"- {target}: [PNG]({target}.png) | [PDF]({target}.pdf)")
    (output / "figures/languages/best_performance.md").write_text(
        "\n".join(lines) + "\n", encoding="utf-8"
    )
    index = output / "figures/languages/README.md"
    link = "[Best-model, best/median and hardest-pair plots](best_performance.md)"
    if index.exists() and link not in index.read_text(encoding="utf-8"):
        index.write_text(
            index.read_text(encoding="utf-8").rstrip()
            + "\n\n## Best Achieved Performance\n\n"
            + link
            + "\n",
            encoding="utf-8",
        )
    return saved


def build_language_violin_rows(points, runs):
    _, models = build_best_language_rows(points, runs)
    rows = []
    for row in models:
        source, target = row["direction"].split("-", 1)
        for role, language in (("pair", row["direction"]), ("from", source), ("to", target)):
            rows.append({**row, "role": role, "language_group": language})
    groups = defaultdict(list)
    for row in rows:
        groups[
            tuple(
                row[field]
                for field in (
                    "view",
                    "dataset",
                    "setting",
                    "category",
                    "metric",
                    "role",
                    "language_group",
                )
            )
        ].append(row)
    support = []
    for key, selected in groups.items():
        values = [row["value"] for row in selected]
        directions = sorted({row["direction"] for row in selected})
        counts = [int(row["rows_scored"]) for row in selected]
        support.append(
            {
                **dict(
                    zip(
                        (
                            "view",
                            "dataset",
                            "setting",
                            "category",
                            "metric",
                            "role",
                            "language_group",
                        ),
                        key,
                        strict=True,
                    )
                ),
                "n_points": len(selected),
                "n_models": len(runs),
                "n_directions": len(directions),
                "directions": ";".join(directions),
                "mean_score": mean(values),
                "median_score": median(values),
                "minimum_score": min(values),
                "maximum_score": max(values),
                "min_rows_scored": min(counts),
                "max_rows_scored": max(counts),
            }
        )
    return rows, support


def write_language_violin_figures(output, points, runs):
    import matplotlib.pyplot as plt
    import numpy as np
    from matplotlib.lines import Line2D

    rows, support = build_language_violin_rows(points, runs)
    (output / "tables").mkdir(parents=True, exist_ok=True)
    write_csv(output / "tables/language_violin_points.csv", rows)
    write_csv(output / "tables/language_violin_support.csv", support)
    contexts = defaultdict(list)
    for row in rows:
        contexts[(row["view"], row["dataset"], row["setting"], row["role"])].append(row)
    colors = plt.get_cmap("tab10")
    model_colors = {run: colors(index) for index, run in enumerate(runs)}
    titles = {"pair": "Language Pair", "from": "Source Language", "to": "Target Language"}
    saved = []
    for (view, dataset, setting, role), selected in contexts.items():
        panels = sorted({(row["category"], row["metric"]) for row in selected})
        figure, axes = plt.subplots(1, len(panels), figsize=(12 * len(panels), 9), squeeze=False)
        for axis, (category, metric) in zip(axes.flat, panels, strict=True):
            groups = defaultdict(list)
            for row in selected:
                if (row["category"], row["metric"]) == (category, metric):
                    groups[row["language_group"]].append(row)
            labels = sorted(groups)
            for position, language in enumerate(labels):
                source = sorted(groups[language], key=lambda row: (row["direction"], row["run"]))
                values = np.asarray([row["value"] for row in source], dtype=float)
                if len(values) >= 3 and np.ptp(values) > 0:
                    violin = axis.violinplot(
                        [values],
                        positions=[position],
                        widths=0.72,
                        showmedians=True,
                        showextrema=False,
                        bw_method="scott",
                    )
                    for body in violin["bodies"]:
                        body.set_facecolor("#a1acb3")
                        body.set_edgecolor("#697680")
                        body.set_alpha(0.35)
                    violin["cmedians"].set_color("#222222")
                else:
                    axis.hlines(
                        float(np.median(values)),
                        position - 0.25,
                        position + 0.25,
                        color="#222222",
                        linewidth=1.5,
                        zorder=4,
                    )
                jitter = ((np.arange(len(values)) * 0.61803398875) % 1 - 0.5) * 0.36
                axis.scatter(
                    position + jitter,
                    values,
                    s=12,
                    color=[model_colors[row["run"]] for row in source],
                    marker="o",
                    alpha=0.8,
                    edgecolors="none",
                    zorder=3,
                )
            axis.set_xticks(
                range(len(labels)),
                [
                    language.replace("-", " -> ")
                    if role == "pair"
                    else LANGUAGE_LABELS.get(language, language)
                    for language in labels
                ],
                rotation=60 if role == "pair" else 35,
                ha="right",
                fontsize=9,
            )
            axis.set_ylabel(f"{METRIC_LABELS[metric]} (native score)")
            axis.set_xlabel(titles[role])
            axis.set_title(
                METRIC_LABELS[metric]
                + (
                    ""
                    if category == "not_applicable"
                    else "\n" + category.replace("_", " ").title()
                ),
                fontsize=13,
            )
            axis.margins(y=0.05)
            axis.grid(axis="y", color="#e0e0e0", linewidth=0.6)
            axis.set_axisbelow(True)
            axis.spines[["top", "right"]].set_visible(False)
        figure.suptitle(
            f"Performance Distributions by {titles[role]} | {DATASETS[dataset]} | "
            f"{view} | {setting.replace('_', ' ').title()}",
            fontsize=22,
            y=0.98,
        )
        figure.legend(
            handles=[
                Line2D([], [], color=colors(index), marker="o", linestyle="none", label=LABELS[run])
                for index, run in enumerate(runs)
            ],
            loc="lower center",
            bbox_to_anchor=(0.5, 0.065),
            ncol=min(5, len(runs)),
            frameon=False,
            fontsize=10,
        )
        figure.subplots_adjust(top=0.86, bottom=0.29, wspace=0.28)
        figure.text(
            0.5,
            0.013,
            "One point = one model-direction score, NOT one translation. "
            "Equal model/direction contributions; native axes fit all observations.\n"
            "Scott-bandwidth violin KDE; black line = median. Constant/sparse groups "
            "use points/median only. Partner sets and metric/term-group support may "
            "differ; no statistical inference.",
            ha="center",
            fontsize=10,
            linespacing=1.5,
        )
        relative = f"languages/violins/{role}/{view}/violin_{role}_{dataset}_{setting}"
        for extension in ("png", "pdf"):
            path = output / "figures" / f"{relative}.{extension}"
            path.parent.mkdir(parents=True, exist_ok=True)
            figure.savefig(path, dpi=160, bbox_inches="tight")
        plt.close(figure)
        saved.append(relative)
    lines = [
        "# Language Performance Violins",
        "",
        "Three collections: pair violins contain all models for each directed pair; "
        "source-language violins pool outgoing model-direction scores; target-language "
        "violins pool incoming scores. Native COMET, chrF++ and variant-aware terminology "
        "coverage are kept in separate metric/term-group panels. Datasets, annotation "
        "views and zero-/few-shot are kept separate.",
        "",
        "Every direction has every model and both prompts available. One point is one "
        f"model-direction aggregate, NOT one translation. Pair groups have {len(runs)} points; "
        f"source/target groups have {len(runs)} points per supported partner direction. "
        "Thus models "
        "and directions contribute equally; translation counts do not weight the density. "
        "chrF++ uses the direction corpus score, not a mean of segment chrF++ scores.",
        "",
        "Native axes fit observed values with 5% padding; no normalization, zero-baseline "
        "requirement or outlier clipping. Model colors and circular dots are consistent "
        "across panels. Violin shape uses Scott-bandwidth KDE; black center line is the "
        "median. Constant/sparse groups show points and median only. These are descriptive "
        "distributions, not confidence intervals or evidence of statistical significance.",
        "",
        "Partner-language and applicable-row sets can differ between languages, metrics "
        "and term groups. Missing groups are omitted, not zero-filled. Inspect the support "
        "CSV before comparing groups. Shared documents and models are not independent; "
        "small underlying translation samples and test/reference exposure can affect scores.",
        "",
        "- [Plotted native points](../../tables/language_violin_points.csv)",
        "- [Group counts, means, medians and direction/row support]"
        "(../../tables/language_violin_support.csv)",
        "",
        "## Figures",
        "",
    ]
    for relative in saved:
        target = Path(relative).relative_to("languages").as_posix()
        lines.append(f"- {target}: [PNG]({target}.png) | [PDF]({target}.pdf)")
    (output / "figures/languages/violins.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    index = output / "figures/languages/README.md"
    link = "[Pair, source-language and target-language violins](violins.md)"
    if index.exists() and link not in index.read_text(encoding="utf-8"):
        index.write_text(
            index.read_text(encoding="utf-8").rstrip()
            + "\n\n## Language Violins\n\n"
            + link
            + "\n",
            encoding="utf-8",
        )
    return saved


def model_vector_correlations(values_x, values_y):
    from scipy.stats import pearsonr, spearmanr

    state = (
        "insufficient_models"
        if len(values_x) < 3
        else "constant_scores"
        if len(set(values_x)) < 2 or len(set(values_y)) < 2
        else "completed"
    )
    return {
        "pearson": float(pearsonr(values_x, values_y)[0]) if state == "completed" else None,
        "spearman": float(spearmanr(values_x, values_y)[0]) if state == "completed" else None,
        "state": state,
    }


def build_language_correlations(points, runs):
    from itertools import combinations_with_replacement, product

    runs = [run for run in runs if population(run) != "excluded"]
    _, models = build_best_language_rows(points, runs)
    groups = defaultdict(lambda: defaultdict(list))
    for row in models:
        context = tuple(
            row[field] for field in ("view", "dataset", "setting", "category", "metric")
        )
        source, target = row["direction"].split("-")
        for role, language in (("from", source), ("to", target)):
            groups[context][(role, language, row["run"])].append(row)
    scores = []
    correlations = []
    for context, members in sorted(groups.items()):
        metadata = dict(
            zip(("view", "dataset", "setting", "category", "metric"), context, strict=True)
        )
        vectors = {}
        directions = {}
        for role, language in sorted({(role, language) for role, language, _ in members}):
            vectors[(role, language)] = []
            for run in runs:
                selected = members[(role, language, run)]
                support = sorted(row["direction"] for row in selected)
                key = (role, language)
                if key in directions and support != directions[key]:
                    raise ValueError(
                        "Language correlations require identical partner support across models"
                    )
                directions[key] = support
                value = mean(row["value"] for row in selected)
                vectors[key].append(value)
                scores.append(
                    {
                        **metadata,
                        "role": role,
                        "language": language,
                        "run": run,
                        "value": value,
                        "n_directions": len(support),
                        "directions": ";".join(support),
                    }
                )
        for role_x, role_y in (("to", "to"), ("from", "from"), ("from", "to")):
            keys_x = sorted(key for key in vectors if key[0] == role_x)
            keys_y = sorted(key for key in vectors if key[0] == role_y)
            pairs = (
                combinations_with_replacement(keys_x, 2)
                if role_x == role_y
                else product(keys_x, keys_y)
            )
            for key_x, key_y in pairs:
                values_x, values_y = vectors[key_x], vectors[key_y]
                correlations.append(
                    {
                        **metadata,
                        "role_x": role_x,
                        "language_x": key_x[1],
                        "role_y": role_y,
                        "language_y": key_y[1],
                        **model_vector_correlations(values_x, values_y),
                        "n_models": len(runs),
                        "runs": ";".join(runs),
                        "values_x": json.dumps(values_x),
                        "values_y": json.dumps(values_y),
                        "directions_x": ";".join(directions[key_x]),
                        "directions_y": ";".join(directions[key_y]),
                    }
                )
    return correlations, scores


def build_combined_language_correlations(scores, runs):
    from itertools import combinations_with_replacement, product

    runs = [run for run in runs if population(run) != "excluded"]
    required = {(dataset, setting) for dataset in DATASETS for setting in SETTINGS}
    groups = defaultdict(lambda: defaultdict(dict))
    for row in scores:
        context = (row["view"], row["category"], row["metric"])
        key = (row["role"], row["language"], row["run"])
        stratum = (row["dataset"], row["setting"])
        if stratum in groups[context][key]:
            raise ValueError("Duplicate combined language stratum")
        groups[context][key][stratum] = row
    combined, correlations = [], []
    for (view, category, metric), members in sorted(groups.items()):
        metadata = {
            "view": view,
            "category": category,
            "metric": metric,
            "dataset": "all_datasets",
            "setting": "both_prompts",
        }
        vectors, supports = {}, {}
        for role, language in sorted({(role, language) for role, language, _ in members}):
            selected = []
            for run in runs:
                strata = members[(role, language, run)]
                complete = set(strata) == required
                support = {
                    f"{dataset}/{setting}": row["directions"].split(";")
                    for (dataset, setting), row in sorted(strata.items())
                }
                row = {
                    **metadata,
                    "role": role,
                    "language": language,
                    "run": run,
                    "value": mean(float(row["value"]) for row in strata.values())
                    if complete
                    else None,
                    "state": "completed" if complete else "incomplete_strata",
                    "n_strata": len(strata),
                    "required_strata": len(required),
                    "support_by_stratum": json.dumps(support, sort_keys=True),
                }
                combined.append(row)
                selected.append(row)
            if all(row["state"] == "completed" for row in selected):
                key = (role, language)
                vectors[key] = [row["value"] for row in selected]
                supports[key] = selected[0]["support_by_stratum"]
        for role_x, role_y in (("to", "to"), ("from", "from"), ("from", "to")):
            keys_x = sorted(key for key in vectors if key[0] == role_x)
            keys_y = sorted(key for key in vectors if key[0] == role_y)
            pairs = (
                combinations_with_replacement(keys_x, 2)
                if role_x == role_y
                else product(keys_x, keys_y)
            )
            for key_x, key_y in pairs:
                values_x, values_y = vectors[key_x], vectors[key_y]
                correlations.append(
                    {
                        **metadata,
                        "role_x": role_x,
                        "language_x": key_x[1],
                        "role_y": role_y,
                        "language_y": key_y[1],
                        **model_vector_correlations(values_x, values_y),
                        "n_models": len(runs),
                        "runs": ";".join(runs),
                        "values_x": json.dumps(values_x),
                        "values_y": json.dumps(values_y),
                        "support_x_by_stratum": supports[key_x],
                        "support_y_by_stratum": supports[key_y],
                    }
                )
    return correlations, combined


def build_language_pair_correlations(points, runs):
    from itertools import combinations_with_replacement

    runs = [run for run in runs if population(run) != "excluded"]
    _, models = build_best_language_rows(points, runs)
    groups = defaultdict(lambda: defaultdict(dict))
    for row in models:
        context = tuple(
            row[field] for field in ("view", "dataset", "setting", "category", "metric")
        )
        groups[context][row["direction"]][row["run"]] = row["value"]
    correlations = []
    for context, directions in sorted(groups.items()):
        for direction_x, direction_y in combinations_with_replacement(sorted(directions), 2):
            values_x = [directions[direction_x][run] for run in runs]
            values_y = [directions[direction_y][run] for run in runs]
            correlations.append(
                {
                    **dict(
                        zip(
                            ("view", "dataset", "setting", "category", "metric"),
                            context,
                            strict=True,
                        )
                    ),
                    "direction_x": direction_x,
                    "direction_y": direction_y,
                    **model_vector_correlations(values_x, values_y),
                    "n_models": len(runs),
                    "runs": ";".join(runs),
                    "values_x": json.dumps(values_x),
                    "values_y": json.dumps(values_y),
                }
            )
    return correlations


def write_language_correlations(output, points, runs, *, combined=False):
    import matplotlib.pyplot as plt
    import numpy as np

    runs = [run for run in runs if population(run) != "excluded"]
    rows, scores = build_language_correlations(points, runs)
    if combined:
        rows, scores = build_combined_language_correlations(scores, runs)
    prefix = "combined_" if combined else ""
    folder = "correlations_combined" if combined else "correlations"
    (output / "tables").mkdir(parents=True, exist_ok=True)
    write_csv(output / "tables" / f"{prefix}language_correlations.csv", rows)
    write_csv(output / "tables" / f"{prefix}language_correlation_model_scores.csv", scores)
    groups = defaultdict(list)
    for row in rows:
        groups[(row["view"], row["dataset"], row["setting"])].append(row)
    saved = []
    for (view, dataset, setting), members in sorted(groups.items()):
        panels = sorted({(row["category"], row["metric"]) for row in members})
        for method in ("pearson", "spearman"):
            figure, axes = plt.subplots(
                len(panels), 3, figsize=(24, 7 * len(panels) + 2.5), squeeze=False
            )
            for panel_index, (category, metric) in enumerate(panels):
                for column, (role_x, role_y) in enumerate(
                    (("to", "to"), ("from", "from"), ("from", "to"))
                ):
                    selected = [
                        row
                        for row in members
                        if (row["category"], row["metric"], row["role_x"], row["role_y"])
                        == (category, metric, role_x, role_y)
                    ]
                    languages_x = sorted({row["language_x"] for row in selected})
                    languages_y = sorted({row["language_y"] for row in selected})
                    if role_x == role_y:
                        languages_x = languages_y = sorted(set(languages_x) | set(languages_y))
                    matrix = np.full((len(languages_x), len(languages_y)), np.nan)
                    for row in selected:
                        if row[method] is not None:
                            first = languages_x.index(row["language_x"])
                            second = languages_y.index(row["language_y"])
                            matrix[first, second] = row[method]
                            if role_x == role_y:
                                matrix[second, first] = row[method]
                    axis = axes[panel_index, column]
                    image = axis.imshow(
                        np.ma.masked_invalid(matrix),
                        vmin=-1,
                        vmax=1,
                        cmap=plt.get_cmap("RdBu_r").with_extremes(bad="#eeeeee"),
                    )
                    axis.set_xticks(
                        range(len(languages_y)),
                        [LANGUAGE_LABELS.get(language, language) for language in languages_y],
                        rotation=45,
                        ha="right",
                        fontsize=9,
                    )
                    axis.set_yticks(
                        range(len(languages_x)),
                        [LANGUAGE_LABELS.get(language, language) for language in languages_x],
                        fontsize=9,
                    )
                    axis.set_xlabel(
                        "To (target language)" if role_y == "to" else "From (source language)"
                    )
                    axis.set_ylabel(
                        "To (target language)" if role_x == "to" else "From (source language)"
                    )
                    title = f"{METRIC_LABELS[metric]} | {role_x.title()} vs {role_y.title()}"
                    if category != "not_applicable":
                        title += "\n" + category.replace("_", " ").title()
                    axis.set_title(title, fontsize=12, pad=12)
                    for first in range(len(languages_x)):
                        for second in range(len(languages_y)):
                            value = matrix[first, second]
                            axis.text(
                                second,
                                first,
                                f"{value:.2f}" if np.isfinite(value) else "NA",
                                ha="center",
                                va="center",
                                fontsize=9,
                                color="white"
                                if np.isfinite(value) and abs(value) > 0.65
                                else "#222222",
                            )
                    figure.colorbar(
                        image, ax=axis, shrink=0.7, label=f"{method.title()} correlation"
                    )
            figure.suptitle(
                f"Language Correlations | {DATASETS.get(dataset, 'All Three Datasets')} | {view} | "
                f"{setting.replace('_', ' ').title()} | {method.title()}",
                fontsize=20,
                y=0.98,
            )
            figure.subplots_adjust(
                top=0.9, bottom=0.22 if len(panels) == 1 else 0.17, hspace=0.65, wspace=0.5
            )
            figure.text(
                0.5,
                0.035,
                (
                    f"One observation = one of {len(runs)} models. Partner directions have equal "
                    "weight within strata; all dataset/prompt strata then have equal weight.\n"
                    if combined
                    else f"One observation = one of {len(runs)} models. "
                    "Each language score averages "
                    "its supported partner directions equally within that model.\n"
                )
                + "To = translate into a language; From = translate out of a language. "
                "Cross-role panel: rows = From; columns = To.\n"
                "Partner sets may differ between languages. Native metrics remain separate; "
                "NA = constant or fewer than three models.\n"
                "Correlations may reflect overall model strength, not isolated language ability. "
                "No significance or causal claims.",
                ha="center",
                fontsize=10,
            )
            relative = (
                f"languages/{folder}/{view}/language_correlations_{dataset}_{setting}_{method}"
            )
            for extension in ("png", "pdf"):
                path = output / "figures" / f"{relative}.{extension}"
                path.parent.mkdir(parents=True, exist_ok=True)
                figure.savefig(path, dpi=160, bbox_inches="tight")
            plt.close(figure)
            saved.append(relative)
    if combined:
        saved.extend(write_combined_language_scatter(output, rows, runs))
    lines = [
        "# Language Correlations: To and From",
        "",
        "Three panels per native metric compare To vs To, From vs From, and From vs To. "
        "Cross-role panels have source languages on rows and target languages on columns. "
        "Pearson and Spearman are shown separately, with datasets, prompts, metrics and "
        "terminology groups kept separate.",
        "",
        "Each observation is one model. For that model, To-language scores average all "
        "supported incoming directions equally; From-language scores average outgoing "
        "directions equally. Models are never pooled as translation-level samples. "
        "Scores are native means, not within-model rank percentiles. All retained models "
        "and both prompts must have scored direction support; missing data is not zero.",
        "",
        "Each language has identical partner support across models, but different languages "
        "can have different partner sets. Partners are NOT matched across languages; "
        "correlations may reflect partner composition and overall model strength. "
        "Cross-role means can share directions: English -> French contributes to both "
        "From English and To French. These are not independent ability measurements. "
        "No statistical significance, independence or causal claims are made. "
        "Constant vectors or fewer than three models give NA.",
        "",
        "[Correlations and exact model vectors](../../tables/language_correlations.csv) | "
        "[Per-model language means and direction supports]"
        "(../../tables/language_correlation_model_scores.csv)",
        "",
        "## Figures",
        "",
    ]
    if combined:
        lines = [
            "# Combined Language Correlations",
            "",
            "Each model has one combined native score for From-language performance and one "
            "for To-language performance. From German, for example, averages German -> all "
            "supported targets; From French averages French -> all supported targets. "
            "Scatter plots compare those combined model means, with German/French first.",
            "",
            "First average supported partner directions equally within each model/dataset/prompt. "
            "Then average the dataset/prompt means equally. Every dataset and both prompts are "
            "required; incomplete languages are marked in the model-score CSV and omitted from "
            "correlations, never filled with zero. Native metrics and terminology groups remain "
            "separate. Heatmaps show to-to, from-from and from-to correlations.",
            "",
            "Partner sets can differ between languages and datasets. These are averages over "
            "supported partners, not every possible language or matched partner populations. "
            "Cross-role means can share directions. Overall model strength and partner composition "
            "may drive correlations; no independence, significance or causal claims are made.",
            "",
            "[Combined correlations and model vectors]"
            "(../../tables/combined_language_correlations.csv) | "
            "[Combined model means and per-stratum supports]"
            "(../../tables/combined_language_correlation_model_scores.csv)",
            "",
            "## Figures",
            "",
        ]
    for relative in saved:
        target = Path(relative).relative_to("languages").as_posix()
        lines.append(f"- {target}: [PNG]({target}.png) | [PDF]({target}.pdf)")
    index_name = "correlations_combined.md" if combined else "correlations.md"
    index = output / "figures/languages" / index_name
    index.parent.mkdir(parents=True, exist_ok=True)
    index.write_text("\n".join(lines) + "\n", encoding="utf-8")
    main_index = output / "figures/languages/README.md"
    link = (
        "[Combined language correlations and model scatter plots](correlations_combined.md)"
        if combined
        else "[Language correlations: to-to, from-from and from-to](correlations.md)"
    )
    if main_index.exists() and link not in main_index.read_text(encoding="utf-8"):
        main_index.write_text(
            main_index.read_text(encoding="utf-8").rstrip()
            + "\n\n## Language Correlations\n\n"
            + link
            + "\n",
            encoding="utf-8",
        )
    return saved


def write_combined_language_scatter(output, rows, runs):
    import matplotlib.pyplot as plt
    from matplotlib.lines import Line2D

    groups = defaultdict(list)
    for row in rows:
        if row["role_x"] == row["role_y"] and row["language_x"] != row["language_y"]:
            groups[(row["view"], row["category"], row["metric"], row["role_x"])].append(row)
    saved = []
    for (view, category, metric, role), members in sorted(groups.items()):
        comparisons = sorted(
            members,
            key=lambda row: (
                (row["language_x"], row["language_y"]) != ("de", "fr"),
                row["language_x"],
                row["language_y"],
            ),
        )
        columns = min(3, len(comparisons))
        height = math.ceil(len(comparisons) / columns)
        figure, axes = plt.subplots(
            height, columns, figsize=(6.3 * columns, 5 * height + 3), squeeze=False
        )
        colors = plt.get_cmap("tab10")
        for axis, row in zip(axes.flat, comparisons, strict=False):
            values_x, values_y = json.loads(row["values_x"]), json.loads(row["values_y"])
            for index in range(len(runs)):
                axis.scatter(
                    values_x[index],
                    values_y[index],
                    s=65,
                    color=colors(index),
                    marker="o",
                    edgecolors="white",
                    linewidths=0.5,
                    zorder=3,
                )
            language_x = LANGUAGE_LABELS.get(row["language_x"], row["language_x"])
            language_y = LANGUAGE_LABELS.get(row["language_y"], row["language_y"])
            axis.set_xlabel(
                f"{language_x} -> all supported languages"
                if role == "from"
                else f"All supported languages -> {language_x}"
            )
            axis.set_ylabel(
                f"{language_y} -> all supported languages"
                if role == "from"
                else f"All supported languages -> {language_y}"
            )
            coefficients = (
                f"r = {row['pearson']:.2f} | rho = {row['spearman']:.2f}"
                if row["state"] == "completed"
                else "Correlation = NA"
            )
            axis.set_title(
                f"{language_x} vs {language_y}\n{coefficients} | n = {len(runs)}", fontsize=11
            )
            low, high = min(values_x + values_y), max(values_x + values_y)
            padding = 0.08 * (high - low) if high > low else max(abs(low) * 0.05, 0.01)
            limits = (low - padding, high + padding)
            axis.plot(limits, limits, linestyle="--", linewidth=0.8, color="#a1a1a1")
            axis.set(xlim=limits, ylim=limits)
            axis.grid(color="#e5e5e5", linewidth=0.6)
            axis.set_axisbelow(True)
        for axis in list(axes.flat)[len(comparisons) :]:
            axis.set_visible(False)
        figure.suptitle(
            f"Combined {'From' if role == 'from' else 'To'} Language Performance"
            f" | {METRIC_LABELS[metric]}\nAll datasets + both prompts | {view} | {category}",
            fontsize=18,
            y=0.98,
        )
        figure.legend(
            handles=[
                Line2D([], [], color=colors(index), linestyle="none", marker="o", label=LABELS[run])
                for index, run in enumerate(runs)
            ],
            loc="lower center",
            bbox_to_anchor=(0.5, 0.075),
            ncol=min(4, len(runs)),
            frameon=False,
            fontsize=9,
        )
        figure.subplots_adjust(
            top=0.8 if height == 1 else 0.85,
            bottom=0.32 if height == 1 else 0.24,
            hspace=0.55,
            wspace=0.4,
        )
        figure.text(
            0.5,
            0.015,
            "One dot = one model's combined native-score mean. Equal partner-direction "
            "weights within each dataset/prompt stratum; then equal stratum weights.\n"
            "Every language requires all datasets and both prompts. Partner sets may differ. "
            "Dashed line = equal scores, not a correlation fit.\n"
            "Correlations may reflect overall model strength or partner composition; "
            "no significance or causal claims.",
            ha="center",
            fontsize=10,
        )
        relative = f"languages/correlations_combined/{view}/combined_{role}_{category}_{metric}"
        for extension in ("png", "pdf"):
            path = output / "figures" / f"{relative}.{extension}"
            path.parent.mkdir(parents=True, exist_ok=True)
            figure.savefig(path, dpi=160, bbox_inches="tight")
        plt.close(figure)
        saved.append(relative)
    return saved


def write_language_pair_correlations(output, points, runs):
    import matplotlib.pyplot as plt
    import numpy as np
    from matplotlib.lines import Line2D

    runs = [run for run in runs if population(run) != "excluded"]
    rows = build_language_pair_correlations(points, runs)
    (output / "tables").mkdir(parents=True, exist_ok=True)
    write_csv(output / "tables/language_pair_correlations.csv", rows)
    groups = defaultdict(list)
    for row in rows:
        groups[(row["view"], row["dataset"], row["setting"])].append(row)
    saved = []

    def save(figure, relative):
        for extension in ("png", "pdf"):
            path = output / "figures" / f"{relative}.{extension}"
            path.parent.mkdir(parents=True, exist_ok=True)
            figure.savefig(path, dpi=160, bbox_inches="tight")
        plt.close(figure)
        saved.append(relative)

    for (view, dataset, setting), members in sorted(groups.items()):
        panels = sorted({(row["category"], row["metric"]) for row in members})
        figure, axes = plt.subplots(
            len(panels), 2, figsize=(21, 9 * len(panels) + 2), squeeze=False
        )
        for panel_index, (category, metric) in enumerate(panels):
            selected = [
                row for row in members if (row["category"], row["metric"]) == (category, metric)
            ]
            directions = sorted(
                {row["direction_x"] for row in selected} | {row["direction_y"] for row in selected}
            )
            for method_index, method in enumerate(("pearson", "spearman")):
                axis = axes[panel_index, method_index]
                matrix = np.full((len(directions), len(directions)), np.nan)
                for row in selected:
                    if row[method] is not None:
                        first = directions.index(row["direction_x"])
                        second = directions.index(row["direction_y"])
                        matrix[first, second] = matrix[second, first] = row[method]
                image = axis.imshow(
                    np.ma.masked_invalid(matrix),
                    vmin=-1,
                    vmax=1,
                    cmap=plt.get_cmap("RdBu_r").with_extremes(bad="#eeeeee"),
                )
                labels = [direction.replace("-", " -> ") for direction in directions]
                axis.set_xticks(range(len(labels)), labels, rotation=90, fontsize=8)
                axis.set_yticks(range(len(labels)), labels, fontsize=8)
                axis.set_xlabel("Translation direction")
                axis.set_ylabel("Translation direction")
                axis.set_title(
                    f"{METRIC_LABELS[metric]} | {method.title()}"
                    + (f" | {category}" if category != "not_applicable" else ""),
                    fontsize=12,
                )
                for first in range(len(directions)):
                    for second in range(len(directions)):
                        value = matrix[first, second]
                        axis.text(
                            second,
                            first,
                            f"{value:.2f}" if np.isfinite(value) else "NA",
                            ha="center",
                            va="center",
                            fontsize=6,
                            color="white"
                            if np.isfinite(value) and abs(value) > 0.65
                            else "#222222",
                        )
                figure.colorbar(image, ax=axis, shrink=0.75, label="Correlation across models")
        figure.suptitle(
            f"Language-Pair Correlations | {DATASETS[dataset]} | {view} | "
            f"{setting.replace('_', ' ').title()}",
            fontsize=20,
            y=0.985,
        )
        figure.subplots_adjust(top=0.94, bottom=0.12, hspace=0.4, wspace=0.35)
        figure.text(
            0.5,
            0.025,
            f"Each cell correlates native scores for two directions across {len(runs)} models. "
            "Prompts, datasets and metrics are separate.\n"
            "Positive = models stronger on one direction tend to be stronger on the other. "
            "NA = constant scores or fewer than three models.\n"
            "Descriptive associations can reflect overall model quality; not significance, "
            "causality or isolated language ability.",
            ha="center",
            fontsize=10,
        )
        save(figure, f"languages/model_pairs/{view}/pair_correlations_{dataset}_{setting}")

        comparisons = [
            row
            for row in members
            if row["metric"] == "comet"
            and row["category"] == "not_applicable"
            and row["direction_x"].split("-")[0] == row["direction_y"].split("-")[0]
            and row["direction_x"].endswith("-en")
            and row["direction_y"].endswith("-fr")
        ]
        if not comparisons:
            continue
        columns = min(3, len(comparisons))
        height = math.ceil(len(comparisons) / columns)
        figure, axes = plt.subplots(
            height, columns, figsize=(6 * columns, 5 * height + 2.5), squeeze=False
        )
        colors = plt.get_cmap("tab10")
        for axis, row in zip(axes.flat, comparisons, strict=False):
            values_x, values_y = json.loads(row["values_x"]), json.loads(row["values_y"])
            for index in range(len(runs)):
                axis.scatter(
                    values_x[index],
                    values_y[index],
                    s=65,
                    color=colors(index),
                    marker="o",
                    edgecolors="white",
                    linewidths=0.5,
                    zorder=3,
                )
            source = LANGUAGE_LABELS.get(row["direction_x"].split("-")[0], row["direction_x"])
            coefficients = (
                f"Pearson r = {row['pearson']:.2f} | Spearman rho = {row['spearman']:.2f}"
                if row["state"] == "completed"
                else "Correlation = NA"
            )
            axis.set_title(f"{source} source\n{coefficients} | n = {len(runs)}", fontsize=11)
            axis.set_xlabel(f"{source} -> English | COMET")
            axis.set_ylabel(f"{source} -> French | COMET")
            axis.margins(0.12)
            axis.grid(color="#e5e5e5", linewidth=0.6)
            axis.set_axisbelow(True)
        for axis in list(axes.flat)[len(comparisons) :]:
            axis.set_visible(False)
        figure.suptitle(
            f"To English vs To French | {DATASETS[dataset]} | {setting.replace('_', ' ').title()}",
            fontsize=20,
            y=0.97,
        )
        figure.legend(
            handles=[
                Line2D([], [], color=colors(index), linestyle="none", marker="o", label=LABELS[run])
                for index, run in enumerate(runs)
            ],
            loc="lower center",
            bbox_to_anchor=(0.5, 0.07),
            ncol=min(4, len(runs)),
            frameon=False,
            fontsize=9,
        )
        figure.subplots_adjust(top=0.82, bottom=0.25, hspace=0.55, wspace=0.4)
        figure.text(
            0.5,
            0.015,
            "One dot = one model; source language fixed within each panel. "
            "Both axes are native COMET scores, not zero-shot vs few-shot.\n"
            "These small-cohort correlations may reflect overall model strength; "
            "no significance or causal claims.",
            ha="center",
            fontsize=10,
        )
        save(figure, f"languages/model_pairs/{view}/english_vs_french_{dataset}_{setting}")
    for view in VIEWS:
        for dataset in (*DATASETS, "all_datasets"):
            for extension in ("png", "pdf"):
                (
                    output
                    / "figures"
                    / f"languages/model_pairs/{view}/model_pairs_{dataset}.{extension}"
                ).unlink(missing_ok=True)
    lines = [
        "# Language-Pair Correlations",
        "",
        "Each observation is one retained model. Native scores for two directed language "
        "pairs are correlated across the same models using Pearson and Spearman. "
        "Zero-shot and few-shot are separate, as are datasets, metrics and terminology groups. "
        "General metrics share the annotation-independent translation scores.",
        "",
        "Heatmaps cover every supported pair of directions for COMET, chrF++ and "
        "variant-aware coverage. English-versus-French COMET scatter panels hold the source "
        "language fixed: for example German -> English versus German -> French.",
        "",
        "Scores are native model-direction aggregates, not within-model language percentiles. "
        "All models and both prompts must have complete direction scores. Every model has "
        "equal weight; translation counts do not weight correlations. Constant vectors or "
        "fewer than three models produce NA, not zero. Exact model vectors are exported in "
        "[language_pair_correlations.csv](../../tables/language_pair_correlations.csv).",
        "",
        "A positive correlation can reflect overall model strength rather than a specific "
        "language relationship. Models are not independent random samples, direction rows "
        "are not matched translations, and no p-values, significance or causal claims are made.",
        "",
        "## Figures",
        "",
    ]
    for relative in saved:
        target = Path(relative).relative_to("languages").as_posix()
        lines.append(f"- {target}: [PNG]({target}.png) | [PDF]({target}.pdf)")
    path = output / "figures/languages/pair_correlations.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    index = output / "figures/languages/README.md"
    if index.exists():
        text = index.read_text(encoding="utf-8")
        text = text.replace(
            "Model-dot panels compare each model's relative language handling under zero/few-shot "
            "using that model's own shared ranking pool. They do not rank absolute model quality; "
            "consult the native-metric figures and original model scorecards for that purpose.",
            "Language-pair correlations compare native scores for different directions across "
            "models, with prompts separate. English-versus-French panels hold the source fixed.",
        )
        text = "\n".join(line for line in text.splitlines() if "model_pairs_" not in line)
        link = (
            "[Language-pair correlations and English-versus-French scatter plots]"
            "(pair_correlations.md)"
        )
        if link not in text:
            text += "\n\n## Pair Correlations\n\n" + link
        index.write_text(text.rstrip() + "\n", encoding="utf-8")
    return saved


def write_language_analysis(output, points, runs):
    import matplotlib.pyplot as plt
    import numpy as np

    balanced, components, support = build_language_direction_rows(points, runs)
    pairs, _ = aggregate_language_pairs(balanced, runs)
    source_ranks, target_ranks = build_language_rankings(balanced, runs)
    (output / "tables").mkdir(parents=True, exist_ok=True)
    for name, rows in (
        ("language_direction_model_scores", balanced),
        ("language_rank_components", components),
        ("language_direction_support", support),
        ("language_pair_scores", pairs),
        ("language_rankings_from", source_ranks),
        ("language_rankings_to", target_ranks),
    ):
        write_csv(output / "tables" / f"{name}.csv", rows)
    saved = []

    def save(figure, relative):
        for extension in ("png", "pdf"):
            path = output / "figures" / f"{relative}.{extension}"
            path.parent.mkdir(parents=True, exist_ok=True)
            figure.savefig(path, dpi=160, bbox_inches="tight")
        plt.close(figure)
        saved.append(relative)

    def heatmap(axis, values, title, limits, color_label, native=False):
        languages = sorted({language for direction in values for language in direction.split("-")})
        labels = [LANGUAGE_LABELS.get(language, language) for language in languages]
        matrix = np.full((len(languages), len(languages)), np.nan)
        for direction, value in values.items():
            source_language, target_language = direction.split("-", 1)
            matrix[languages.index(source_language), languages.index(target_language)] = value
        cmap = plt.get_cmap("YlGnBu" if native else "RdYlGn").with_extremes(bad="#eeeeee")
        image = axis.imshow(np.ma.masked_invalid(matrix), cmap=cmap, vmin=limits[0], vmax=limits[1])
        axis.set_xticks(range(len(languages)), labels, rotation=45, ha="right", fontsize=8)
        axis.set_yticks(range(len(languages)), labels, fontsize=8)
        axis.set_xlabel("To (target language)")
        axis.set_ylabel("From (source language)")
        axis.set_title(title, fontsize=11, pad=12)
        for source_index in range(len(languages)):
            for target_index in range(len(languages)):
                value = matrix[source_index, target_index]
                text = (
                    "NA"
                    if not np.isfinite(value)
                    else f"{value:.3f}"
                    if native and (max(abs(limits[0]), abs(limits[1])) <= 2)
                    else f"{value:.1f}"
                )
                red, green, blue, _ = (
                    cmap(image.norm(value)) if np.isfinite(value) else (1, 1, 1, 1)
                )
                axis.text(
                    target_index,
                    source_index,
                    text,
                    ha="center",
                    va="center",
                    fontsize=7,
                    color="white"
                    if 0.299 * red + 0.587 * green + 0.114 * blue < 0.5
                    else "#222222",
                )
        axis.figure.colorbar(image, ax=axis, shrink=0.75, label=color_label)

    raw_groups = defaultdict(list)
    for row in points:
        raw_groups[
            tuple(
                row[field]
                for field in ("view", "dataset", "category", "metric", "setting", "direction")
            )
        ].append(row)
    raw_means = {}
    for key, rows in raw_groups.items():
        if len(rows) != len(runs) or {row["run"] for row in rows} != set(runs):
            raise ValueError("Native language heatmaps require every model")
        raw_means[key] = mean(float(row["value"]) for row in rows)
    for view in ("shared_general", *VIEWS):
        candidates = (
            [("not_applicable", metric) for metric in GENERAL]
            if view == ("shared_general")
            else [(category, metric) for category in CATEGORIES for metric in TERMINOLOGY]
        )
        for dataset in DATASETS:
            panels = [
                (category, metric)
                for category, metric in candidates
                if any(key[:4] == (view, dataset, category, metric) for key in raw_means)
            ]
            if not panels:
                continue
            for setting in SETTINGS:
                figure, axes = plt.subplots(
                    math.ceil(len(panels) / 3),
                    3,
                    figsize=(24, 7 * math.ceil(len(panels) / 3)),
                    squeeze=False,
                )
                for axis, (category, metric) in zip(axes.flat, panels, strict=False):
                    values = {
                        key[-1]: value
                        for key, value in raw_means.items()
                        if key[:5] == (view, dataset, category, metric, setting)
                    }
                    reference = [
                        value
                        for key, value in raw_means.items()
                        if key[:4] == (view, dataset, category, metric)
                    ]
                    low, high = min(reference), max(reference)
                    padding = (high - low) * 0.03 if high > low else max(abs(low) * 0.03, 0.01)
                    title = METRIC_LABELS[metric] + (
                        "" if category == "not_applicable" else f" | {category}"
                    )
                    heatmap(
                        axis,
                        values,
                        title,
                        (low - padding, high + padding),
                        "All-model mean (native score)",
                        native=True,
                    )
                for axis in list(axes.flat)[len(panels) :]:
                    axis.set_visible(False)
                figure.suptitle(
                    f"Native Language Metrics | {DATASETS[dataset]} | "
                    f"{view} | {setting.replace('_', ' ').title()}",
                    fontsize=20,
                )
                figure.subplots_adjust(top=0.93, bottom=0.08, hspace=0.55, wspace=0.4)
                figure.text(
                    0.5,
                    0.015,
                    "Rows = source; columns = target. Equal model weights. "
                    "NA = unavailable, not zero. Each metric uses its own shared direction "
                    "support; color bounds are shared between prompts per panel.\n"
                    "Languages unavailable in both roles are omitted; tables retain all languages.",
                    ha="center",
                    fontsize=10,
                )
                save(figure, f"languages/native_heatmaps/{view}/native_{dataset}_{setting}")

    pair_groups = defaultdict(list)
    for row in pairs:
        pair_groups[(row["view"], row["dataset"], row["setting"])].append(row)
    for (view, dataset, setting), rows in pair_groups.items():
        figure, axis = plt.subplots(figsize=(10, 8.5))
        heatmap(
            axis,
            {row["direction"]: row["balanced_score"] for row in rows},
            f"Balanced Language Handling | {DATASETS.get(dataset, 'All Three Datasets')}\n"
            f"{view} | {setting.replace('_', ' ').title()}",
            (0, 100),
            "Balanced rank-percentile score (higher is better)",
        )
        figure.subplots_adjust(left=0.15, right=0.95, top=0.9, bottom=0.2)
        figure.text(
            0.5,
            0.025,
            "Equal semantic / lexical / terminology weights; all-model mean.\n"
            "Rank-percentile score, NOT translation accuracy. NA = incomplete support.\n"
            "Overall pairs require all three datasets; dataset and prompt weights equal.\n"
            "Languages unavailable in both roles are omitted; tables retain all languages.",
            ha="center",
            fontsize=9,
        )
        save(figure, f"languages/balanced_heatmaps/{view}/balanced_{dataset}_{setting}")

    saved.extend(write_language_pair_correlations(output, points, runs))
    saved.extend(write_language_correlations(output, points, runs))
    saved.extend(write_language_correlations(output, points, runs, combined=True))
    saved.extend(write_language_rank_reports(output, points, runs))

    methodology = [
        "# Language Performance Analysis",
        "",
        "[Chosen-style balanced language median/best-model scorecards]"
        "(../../tables/language_rankings/README.md)",
        "",
        "## Method",
        "",
        "Native heatmaps show metric-specific direction scores averaged equally across all "
        "models; rows are source languages and columns are target languages. Each panel's "
        "native color range is shared between zero-shot and few-shot.",
        "",
        "Heatmaps omit languages with no supported cell in either role for that panel. "
        "Missing pairs between retained languages remain NA; ranking tables retain all "
        "observed languages and explicitly show missing overall coverage.",
        "",
        "Balanced scores rank directions AND both prompts jointly within each model, dataset, "
        "view and metric. Higher native scores rank better; ties receive average ranks. "
        "Score = 100 * (pool size - rank) / (pool size - 1). These are relative rank "
        "percentiles, not accuracy percentages or native-score normalization.",
        "",
        "[Language-pair correlations](pair_correlations.md) compare native scores for different "
        "directions across models, with prompts separate. English-versus-French scatter panels "
        "hold the source language fixed. These replace the former zero/few-shot model-dot panels.",
        "",
        "Metrics are averaged equally within semantic and lexical families. Terminology "
        "metrics are averaged within each of the three annotation groups, then groups are "
        "averaged equally. The three families receive equal one-third weights, mirroring "
        "the balanced mixed-rank model scorecard. Universally unavailable metrics are omitted. "
        "Balanced panels use the intersection across every active component, model and both "
        "prompts; missing support is never replaced by zero.",
        "",
        "Source/target rankings first average partner directions within each model, then "
        "models equally, prompts equally, and datasets equally. Overall language ranks "
        "require every dataset/prompt stratum; overall pair panels require the same directed "
        "pair in all three datasets. Tables include all observed languages and leave "
        "incomplete aggregates unranked. Direction and language ranks use competition ranks.",
        "",
        "Partner-language sets differ, especially in the sparse patent grid. Rankings are "
        "descriptive of supported benchmark subsets, NOT partner-matched comparisons or "
        "intrinsic language difficulty. GLM/Luna supports differ and their ranks must not "
        "be compared as if populations were identical. Models, directions and datasets are "
        "not weighted by translation counts. Small direction samples, shared documents, "
        "reference overlap and few-shot exposure can affect results; no significance or "
        "leakage conclusion follows from these figures.",
        "",
        "## Data and Tables",
        "",
    ]
    for role, rows in (("from", source_ranks), ("to", target_ranks)):
        lines = [
            f"# Translation {role.title()} Language Rankings",
            "",
            "Higher balanced rank-percentile score is better; NA = incomplete support. "
            "Partner sets differ: consult the CSV and method before comparing languages.",
            "",
        ]
        for view in VIEWS:
            for dataset in ("all_datasets", *DATASETS):
                selected = [
                    row
                    for row in rows
                    if row["view"] == view
                    and row["dataset"] == dataset
                    and row["setting"] == "both_prompts"
                ]
                lines += [
                    f"## {view} | {DATASETS.get(dataset, 'All Three Datasets')}",
                    "",
                    "| Rank | Language | Balanced | Semantic | Lexical | Terminology | "
                    "Strata | Partners per Dataset |",
                    "|---|---|---|---|---|---|---|---|",
                ]
                for row in selected:
                    values = [
                        "NA" if row[field] is None else f"{row[field]:.2f}"
                        for field in (
                            "balanced_score",
                            "semantic_score",
                            "lexical_score",
                            "terminology_score",
                        )
                    ]
                    partners = json.loads(row["partners_by_dataset"])
                    counts = "; ".join(f"{data}: {len(group)}" for data, group in partners.items())
                    lines.append(
                        f"| {row['language_rank'] or 'NA'} | "
                        f"{LANGUAGE_LABELS.get(row['language'], row['language'])} | "
                        + " | ".join(values)
                        + f" | {row['n_strata']}/"
                        f"{row['required_strata']} | {counts or 'NA'} |"
                    )
                lines.append("")
        (output / f"language_rankings_{role}.md").write_text("\n".join(lines), encoding="utf-8")
        methodology.append(
            f"- [Translation {role} rankings](../../language_rankings_{role}.md) "
            f"| [CSV](../../tables/language_rankings_{role}.csv)"
        )
    for name in (
        "language_direction_model_scores",
        "language_rank_components",
        "language_direction_support",
        "language_pair_scores",
    ):
        methodology.append(f"- [{name}](../../tables/{name}.csv)")
    if (output / "figures/languages/best_performance.md").exists():
        methodology += [
            "",
            "## Best Achieved Performance",
            "",
            "[Best-model, best/median and hardest-pair plots](best_performance.md)",
        ]
    if (output / "figures/languages/violins.md").exists():
        methodology += [
            "",
            "## Language Violins",
            "",
            "[Pair, source-language and target-language violins](violins.md)",
        ]
    methodology += ["", "## Figures", ""]
    for relative in saved:
        target = Path(relative).relative_to("languages").as_posix()
        methodology.append(f"- {target}: [PNG]({target}.png) | [PDF]({target}.pdf)")
    (output / "figures/languages/README.md").write_text(
        "\n".join(methodology) + "\n", encoding="utf-8"
    )
    return saved


def build_distribution_rows(summaries, runs):
    rows = []
    for view in VIEWS:
        for dataset in DATASETS:
            groups = {
                (category, run, setting): summaries[(view, category, run)]["dataset_settings"][
                    dataset
                ][setting]["by_direction"]
                for category in CATEGORIES
                for run in runs
                for setting in SETTINGS
            }
            supports = [
                {
                    direction
                    for direction, result in group.items()
                    if all(
                        metric_value(result, metric) is not None
                        for metric in ("comet", "target_term_coverage")
                    )
                }
                for group in groups.values()
            ]
            directions = sorted(set.intersection(*supports))
            for category in CATEGORIES:
                for setting in SETTINGS:
                    for direction in directions:
                        results = [groups[(category, run, setting)][direction] for run in runs]
                        row = {
                            "view": view,
                            "dataset": dataset,
                            "category": category,
                            "setting": setting,
                            "direction": direction,
                            "n_models": len(runs),
                            "n_shared_directions": len(directions),
                        }
                        for metric in ("comet", "target_term_coverage"):
                            row[metric] = mean(metric_value(result, metric) for result in results)
                            row[f"{metric}_rows_scored"] = sum(
                                result["metric_status"][metric]["rows_scored"] for result in results
                            )
                        rows.append(row)
    return rows


def density_region(points, x_grid, y_grid, mass=0.5):
    import numpy as np
    from scipy.stats import gaussian_kde

    values = np.asarray(points, dtype=float)
    if not 0 < mass < 1:
        raise ValueError("Density mass must lie strictly between zero and one")
    if (
        values.ndim != 2
        or values.shape[1] != 2
        or len(values) < 6
        or not np.isfinite(values).all()
        or np.linalg.matrix_rank(values - values.mean(axis=0)) < 2
    ):
        return None
    try:
        estimator = gaussian_kde(values.T, bw_method="scott")
    except np.linalg.LinAlgError:
        return None
    mesh_x, mesh_y = np.meshgrid(x_grid, y_grid)
    density = estimator(np.vstack([mesh_x.ravel(), mesh_y.ravel()])).reshape(mesh_x.shape)
    cell_area = (x_grid[1] - x_grid[0]) * (y_grid[1] - y_grid[0])
    ranked = np.sort(density.ravel())[::-1]
    accumulated = np.cumsum(ranked) * cell_area
    if accumulated[-1] < mass:
        return None
    threshold = ranked[min(np.searchsorted(accumulated, mass), len(ranked) - 1)]
    return density, float(threshold)


def figure_folder(name):
    if name.startswith("translation_quality_") or name == "learned_metric_comparison":
        return Path("translation_quality")
    if name.startswith("terminology_coverage_"):
        return Path("terminology") / "overview"
    if name.startswith("quality_terminology_bubbles_"):
        return Path("bubbles") / "all_terms" / "luna"
    if name.startswith("prompting_"):
        return Path("prompting")
    if name == "translation_coverage":
        return Path("coverage")
    if name.startswith("performance_distributions_"):
        return Path("distributions")
    raise ValueError(f"Unknown figure type: {name}")


def write_figures(output, aggregates, coverage, runs, bubble_rows):
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import numpy as np
    from matplotlib.colors import LinearSegmentedColormap

    figures = output / "figures"
    figures.mkdir(parents=True, exist_ok=True)
    plt.rcParams.update(
        {
            "font.family": "DejaVu Sans",
            "font.size": 10,
            "axes.spines.top": False,
            "axes.spines.right": False,
            "axes.edgecolor": "#bcc1c0",
            "axes.labelcolor": "#303735",
            "text.color": "#202a27",
            "xtick.color": "#46534d",
            "ytick.color": "#46534d",
            "pdf.fonttype": 42,
            "savefig.facecolor": "white",
        }
    )
    lookup = {
        (
            row["view"],
            row["category"],
            row["dataset"],
            row["setting"],
            row["run"],
            row["metric"],
        ): row
        for row in aggregates
    }
    positions = np.arange(len(runs))
    colors = ("#167d8d", "#ba4934", "#9b7915")
    saved = []

    def save(figure, name, folder=None):
        relative = (figure_folder(name) if folder is None else folder) / name
        for extension in ("png", "pdf"):
            destination = figures / f"{relative.as_posix()}.{extension}"
            destination.parent.mkdir(parents=True, exist_ok=True)
            legacy = figures / f"{name}.{extension}"
            if legacy.is_file() and destination != legacy:
                legacy.replace(destination)
            figure.savefig(destination, dpi=180, bbox_inches="tight")
        plt.close(figure)
        saved.append(relative.as_posix())

    def dot_axis(axis, dataset, metric):
        for setting_index, setting in enumerate(SETTINGS):
            values = [
                lookup[("shared_general", "not_applicable", dataset, setting, run, metric)]["value"]
                for run in runs
            ]
            axis.scatter(
                [np.nan if value is None else value for value in values],
                positions + (-0.14 if setting_index == 0 else 0.14),
                s=40,
                marker="o" if setting_index == 0 else "s",
                color=colors[setting_index],
                label=setting.replace("_", " ").title(),
                zorder=3,
            )
        support = lookup[
            ("shared_general", "not_applicable", dataset, SETTINGS[0], runs[0], metric)
        ]["n_directions"]
        axis.set_title(
            f"{METRIC_LABELS[metric]} | {support} shared directions",
            loc="left",
            fontsize=11,
            pad=12,
        )
        axis.set_yticks(positions, [LABELS[run] for run in runs], fontsize=9)
        axis.invert_yaxis()
        axis.grid(axis="x", color="#e4e8e5", linewidth=0.7)
        axis.set_axisbelow(True)
        axis.set_xlabel("Direction-macro score (higher is better)", fontsize=9)
        if metric in CORPUS:
            axis.set_xlim(0, 100)
        if support == 0:
            axis.text(0.5, 0.5, "No common scored support", transform=axis.transAxes, ha="center")

    for dataset, title in DATASETS.items():
        figure, axes = plt.subplots(2, 2, figsize=(14, 11), layout="constrained")
        for axis, metric in zip(axes.flat, ("bleu", "chrf2++", "comet", "bleurt"), strict=True):
            dot_axis(axis, dataset, metric)
        figure.suptitle(f"{title}: Translation Quality", fontsize=18)
        axes[0, 0].legend(loc="lower right", fontsize=9, frameon=False)
        figure.supxlabel(
            "Shared language directions, not necessarily identical rows. "
            "No significance inference.",
            fontsize=10,
        )
        save(figure, f"translation_quality_{dataset}")

    figure, axes = plt.subplots(3, 3, figsize=(20, 16), layout="constrained")
    for dataset_index, (dataset, title) in enumerate(DATASETS.items()):
        for metric_index, metric in enumerate(("bertscore", "cometkiwi_qe", "xcomet_xl")):
            axis = axes[dataset_index, metric_index]
            dot_axis(axis, dataset, metric)
            axis.set_title(f"{title}\n{axis.get_title(loc='left')}", loc="left", fontsize=11)
    figure.suptitle("Learned Translation Metrics", fontsize=18)
    axes[0, 0].legend(loc="lower right", fontsize=8, frameon=False)
    figure.supxlabel(
        "Native metric scales; shared-direction descriptive averages, not row-paired comparisons.",
        fontsize=10,
    )
    save(figure, "learned_metric_comparison")

    category_labels = ("All terms", "Externally verified", "LLM-enriched (refined)")
    category_titles = dict(zip(CATEGORIES, category_labels, strict=True))
    for view in VIEWS:
        figure, axes = plt.subplots(2, 3, figsize=(20, 12), layout="constrained")
        for setting_index, setting in enumerate(SETTINGS):
            for dataset_index, (dataset, title) in enumerate(DATASETS.items()):
                axis = axes[setting_index, dataset_index]
                supports = []
                for category_index, category in enumerate(CATEGORIES):
                    records = [
                        lookup[(view, category, dataset, setting, run, "target_term_coverage")]
                        for run in runs
                    ]
                    values = [np.nan if row["value"] is None else row["value"] for row in records]
                    axis.scatter(
                        values,
                        positions + (category_index - 1) * 0.2,
                        s=35,
                        marker=("o", "s", "^")[category_index],
                        color=colors[category_index],
                        label=category_labels[category_index],
                        zorder=3,
                    )
                    supports.append(records[0]["n_directions"])
                axis.set_title(
                    f"{title} | {setting.replace('_', ' ')}\n"
                    f"Shared directions (all/external/refined): {'/'.join(map(str, supports))}",
                    loc="left",
                    fontsize=11,
                )
                axis.set_yticks(positions, [LABELS[run] for run in runs], fontsize=9)
                axis.invert_yaxis()
                axis.set_xlim(0, 100)
                axis.set_xlabel("Direction-macro target-term coverage (%)", fontsize=9)
                axis.grid(axis="x", color="#e4e8e5")
                axis.set_axisbelow(True)
                if not any(supports):
                    axis.text(
                        0.5,
                        0.5,
                        "No common applicable support",
                        transform=axis.transAxes,
                        ha="center",
                        fontsize=10,
                    )
        axes[0, 0].legend(
            loc="lower left", bbox_to_anchor=(0, 1.15), ncol=3, fontsize=9, frameon=False
        )
        view_label = "Original GLM" if view == "original_glm" else "Luna"
        figure.suptitle(f"Terminology Coverage: {view_label} Annotations", fontsize=18)
        figure.supxlabel(
            "Subsets and annotation views may score different rows. "
            "Missing support is not 0%. See CSV denominators.",
            fontsize=10,
        )
        save(figure, f"terminology_coverage_{view}")

    for view in VIEWS:
        for category in CATEGORIES:
            figure, axes = plt.subplots(3, 3, figsize=(21, 17), layout="constrained")
            for dataset_index, (dataset, title) in enumerate(DATASETS.items()):
                for metric_index, metric in enumerate(TERMINOLOGY[:3]):
                    axis = axes[dataset_index, metric_index]
                    support = lookup[(view, category, dataset, SETTINGS[0], runs[0], metric)][
                        "n_directions"
                    ]
                    for setting_index, setting in enumerate(SETTINGS):
                        records = [
                            lookup[(view, category, dataset, setting, run, metric)] for run in runs
                        ]
                        axis.scatter(
                            [np.nan if row["value"] is None else row["value"] for row in records],
                            positions + (-0.14 if setting_index == 0 else 0.14),
                            s=40,
                            marker="o" if setting_index == 0 else "s",
                            color=colors[setting_index],
                            label=setting.replace("_", " ").title(),
                            zorder=3,
                        )
                    axis.set_title(
                        f"{title}\n{METRIC_LABELS[metric]} | {support} shared directions",
                        loc="left",
                        fontsize=11,
                        pad=12,
                    )
                    axis.set_yticks(positions, [LABELS[run] for run in runs], fontsize=9)
                    axis.invert_yaxis()
                    axis.set_xlim(0, 1 if metric == "term_bertscore_recall" else 100)
                    axis.set_xlabel(
                        "Direction-macro recall"
                        if metric == "term_bertscore_recall"
                        else "Direction-macro coverage (%)",
                        fontsize=9,
                    )
                    axis.grid(axis="x", color="#e4e8e5", linewidth=0.7)
                    axis.set_axisbelow(True)
                    if support == 0:
                        axis.text(
                            0.5,
                            0.5,
                            "No common applicable support",
                            transform=axis.transAxes,
                            ha="center",
                            fontsize=10,
                        )
            view_label = "Original GLM" if view == "original_glm" else "Luna"
            figure.suptitle(
                f"{category_titles[category]} Terms | {view_label} Annotations",
                fontsize=18,
            )
            axes[0, 0].legend(loc="lower right", fontsize=9, frameon=False)
            figure.supxlabel(
                "Term subsets and annotation views may score different rows. "
                "No common support is NA, not zero. See CSV denominators.",
                fontsize=10,
            )
            save(
                figure,
                f"terminology_metrics_{category}_{view}",
                folder=Path("terminology") / category / view,
            )

    deltas = np.array(
        [
            [
                lookup[("shared_general", "not_applicable", dataset, "few_shot", run, "comet")][
                    "value"
                ]
                - lookup[("shared_general", "not_applicable", dataset, "zero_shot", run, "comet")][
                    "value"
                ]
                if all(
                    lookup[("shared_general", "not_applicable", dataset, setting, run, "comet")][
                        "value"
                    ]
                    is not None
                    for setting in SETTINGS
                )
                else np.nan
                for dataset in DATASETS
            ]
            for run in runs
        ]
    )
    finite = np.abs(deltas[np.isfinite(deltas)])
    limit = max(float(finite.max()) if finite.size else 0, 0.001)
    diverging = LinearSegmentedColormap.from_list("prompt_delta", ["#b54832", "#f7f7f5", "#167d8d"])
    figure, axis = plt.subplots(figsize=(11, 8), layout="constrained")
    image = axis.imshow(
        np.ma.masked_invalid(deltas), cmap=diverging, vmin=-limit, vmax=limit, aspect="auto"
    )
    axis.set_xticks(range(len(DATASETS)), list(DATASETS.values()), fontsize=10)
    axis.set_yticks(positions, [LABELS[run] for run in runs], fontsize=10)
    for row_index, column_index in np.ndindex(deltas.shape):
        value = deltas[row_index, column_index]
        axis.text(
            column_index,
            row_index,
            "NA" if not np.isfinite(value) else f"{value:+.3f}",
            ha="center",
            va="center",
            color="white" if np.isfinite(value) and abs(value) > limit * 0.6 else "#202a27",
        )
    axis.set_title("Few-Shot Minus Zero-Shot COMET", fontsize=17, pad=18)
    figure.colorbar(image, ax=axis, label="Difference in direction-macro COMET (raw units)")
    figure.supxlabel(
        "Shared directions; descriptive difference, not a row-paired treatment effect.", fontsize=10
    )
    save(figure, "prompting_comet_difference")

    group_counts = {
        (row["run"], row["dataset"], row["setting"]): row["rows_translated"]
        for row in coverage
        if row["view"] == "original_glm"
        and row["category"] == "all_terms"
        and row["population"] == "current"
    }
    columns = [(dataset, setting) for dataset in DATASETS for setting in SETTINGS]
    counts = np.array(
        [[group_counts[(run, dataset, setting)] for dataset, setting in columns] for run in runs]
    )
    relative = counts / counts.max(axis=0)
    coverage_cmap = LinearSegmentedColormap.from_list("coverage", ["#f0ece4", "#167d8d"])
    figure, axis = plt.subplots(figsize=(15, 8), layout="constrained")
    image = axis.imshow(
        relative, cmap=coverage_cmap, vmin=min(float(relative.min()), 0.99), vmax=1, aspect="auto"
    )
    axis.set_xticks(
        range(len(columns)),
        [f"{DATASETS[dataset]}\n{setting.replace('_', ' ')}" for dataset, setting in columns],
        fontsize=9,
    )
    axis.set_yticks(positions, [LABELS[run] for run in runs], fontsize=10)
    for row_index, column_index in np.ndindex(counts.shape):
        axis.text(
            column_index,
            row_index,
            f"{counts[row_index, column_index]:,}",
            ha="center",
            va="center",
            color="white" if image.norm(relative[row_index, column_index]) > 0.6 else "#202a27",
            fontsize=10,
        )
    axis.set_title("Available Translation Counts", fontsize=17, pad=18)
    figure.colorbar(image, ax=axis, label="Fraction of largest observed model group")
    figure.supxlabel(
        "Counts are not unique benchmark cases. "
        "Group maxima are not independently verified expected totals.",
        fontsize=10,
    )
    save(figure, "translation_coverage")

    palette = plt.get_cmap("tab10")
    all_x = [row["comet"] for row in bubble_rows]
    all_y = [row["target_term_coverage"] for row in bubble_rows]
    x_span = max(max(all_x) - min(all_x), 0.02)
    y_span = max(max(all_y) - min(all_y), 4)
    x_limits = (min(all_x) - x_span * 0.18, max(all_x) + x_span * 0.18)
    y_limits = (
        max(0, min(all_y) - y_span * 0.2),
        min(100, max(all_y) + y_span * 0.2),
    )
    tracks = sorted({(row["view"], row["category"], row["setting"]) for row in bubble_rows})
    for view, category, setting in tracks:
        rows = [
            row
            for row in bubble_rows
            if (row["view"], row["category"], row["setting"]) == (view, category, setting)
        ]
        figure, axis = plt.subplots(figsize=(15, 10))
        figure.subplots_adjust(left=0.1, right=0.73, bottom=0.29, top=0.86)
        axis.set_xlim(*x_limits)
        axis.set_ylim(*y_limits)
        axis.set_axisbelow(True)
        axis.grid(color="#e4e8e5", linewidth=0.7)
        for row in sorted(rows, key=lambda item: item["bleu"], reverse=True):
            color = palette(runs.index(row["run"]))
            axis.scatter(
                row["comet"],
                row["target_term_coverage"],
                s=bubble_area(row["bleu"]),
                color=color,
                alpha=0.58,
                edgecolor=color,
                linewidth=1.5,
                zorder=3,
            )
            axis.scatter(
                row["comet"],
                row["target_term_coverage"],
                s=10,
                color="#202a27",
                zorder=4,
            )
        ordered = sorted(rows, key=lambda item: item["target_term_coverage"])
        label_positions = np.linspace(
            y_limits[0] + (y_limits[1] - y_limits[0]) * 0.06,
            y_limits[1] - (y_limits[1] - y_limits[0]) * 0.06,
            len(ordered),
        )
        for row, label_y in zip(ordered, label_positions, strict=True):
            axis.annotate(
                row["model"],
                xy=(row["comet"], row["target_term_coverage"]),
                xytext=(1.03, label_y),
                textcoords=("axes fraction", "data"),
                ha="left",
                va="center",
                fontsize=11,
                annotation_clip=False,
                arrowprops={"arrowstyle": "-", "color": "#89928d", "lw": 0.75},
            )
        axis.set_xlabel("COMET | direction-macro score (higher is better)", labelpad=12)
        axis.set_ylabel("Target-term coverage (%) | direction macro", labelpad=12)
        figure.suptitle(
            f"Chemical Patents: Quality and Terminology ({setting.replace('_', ' ').title()})",
            x=0.1,
            y=0.95,
            ha="left",
            fontsize=19,
        )
        figure.text(
            0.1,
            0.9,
            f"{'Original GLM' if view == 'original_glm' else 'Luna'} | "
            f"{category_titles[category]} | {rows[0]['n_directions']} shared directions | "
            "bubble AREA proportional to BLEU",
            fontsize=11,
            color="#46534d",
        )
        handles = [
            axis.scatter(
                [],
                [],
                s=bubble_area(value),
                color="#778783",
                alpha=0.4,
                edgecolor="#46534d",
                label=str(value),
            )
            for value in (20, 40, 60)
        ]
        axis.legend(
            handles=handles,
            title="Bubble area: direction-macro corpus BLEU",
            loc="upper left",
            bbox_to_anchor=(0, -0.15),
            ncol=3,
            frameon=False,
            labelspacing=2,
            handletextpad=1.8,
            columnspacing=3,
            borderpad=1,
        )
        figure.text(
            0.1,
            0.025,
            "Same directions; metric-specific scored rows, not a row-matched comparison. "
            "Color identifies model; axes are zoomed.\n"
            "BLEU averages direction-level corpus scores; it is not pooled corpus BLEU.",
            fontsize=10,
            color="#46534d",
        )
        save(
            figure,
            f"quality_terminology_bubbles_google_patents_{setting}",
            folder=Path("bubbles") / category / view,
        )
    return saved


def write_distribution_figures(output, rows):
    import matplotlib.pyplot as plt
    import numpy as np
    from matplotlib.patches import Patch
    from matplotlib.ticker import PercentFormatter

    colors = ("#167d8d", "#ba4934", "#9b7915")
    labels = ("All terms", "Externally verified", "LLM-enriched (refined)")
    saved = []
    regions = []
    for view in VIEWS:
        for setting in SETTINGS:
            figure, axes = plt.subplots(1, 3, figsize=(21, 7.5))
            figure.subplots_adjust(left=0.06, right=0.98, bottom=0.24, top=0.8, wspace=0.3)
            for axis, (dataset, title) in zip(axes, DATASETS.items(), strict=True):
                selected = [
                    row
                    for row in rows
                    if (row["view"], row["setting"], row["dataset"]) == (view, setting, dataset)
                ]
                if not selected:
                    axis.set_title(title, loc="left")
                    axis.text(
                        0.5,
                        0.5,
                        "No common scored directions",
                        transform=axis.transAxes,
                        ha="center",
                    )
                    continue
                all_points = np.array(
                    [[row["comet"], row["target_term_coverage"]] for row in selected]
                )
                padding = np.maximum(np.std(all_points, axis=0) * 2, [0.005, 2])
                lower = all_points.min(axis=0) - padding
                upper = all_points.max(axis=0) + padding
                lower[1], upper[1] = max(lower[1], 0), min(upper[1], 100)
                x_grid = np.linspace(lower[0], upper[0], 180)
                y_grid = np.linspace(lower[1], upper[1], 180)
                for category, color in zip(CATEGORIES, colors, strict=True):
                    category_rows = [row for row in selected if row["category"] == category]
                    points = np.array(
                        [[row["comet"], row["target_term_coverage"]] for row in category_rows]
                    )
                    region = density_region(points, x_grid, y_grid)
                    if region is not None:
                        density, threshold = region
                        axis.contourf(
                            x_grid,
                            y_grid,
                            density,
                            levels=[threshold, density.max() * 1.001],
                            colors=[color],
                            alpha=0.18,
                        )
                        axis.contour(
                            x_grid,
                            y_grid,
                            density,
                            levels=[threshold],
                            colors=[color],
                            linewidths=1.1,
                            alpha=0.8,
                        )
                    axis.scatter(
                        points[:, 0],
                        points[:, 1],
                        s=29,
                        color=color,
                        alpha=0.85,
                        edgecolor="white",
                        linewidth=0.3,
                        zorder=3,
                    )
                    regions.append(
                        {
                            "view": view,
                            "dataset": dataset,
                            "setting": setting,
                            "category": category,
                            "n_direction_points": len(points),
                            "n_models_per_point": category_rows[0]["n_models"],
                            "fit_state": "fitted" if region is not None else "points_only",
                            "kde_mass": 0.5 if region is not None else None,
                            "bandwidth": "scott" if region is not None else None,
                        }
                    )
                axis.set_xlim(lower[0], upper[0])
                axis.set_ylim(lower[1], upper[1])
                axis.set_title(
                    f"{title}\n{selected[0]['n_shared_directions']} shared directions per type",
                    loc="left",
                    fontsize=12,
                    pad=12,
                )
                axis.set_xlabel("COMET | direction mean across models", fontsize=10)
                axis.set_ylabel("Target-term coverage | direction mean", fontsize=10)
                axis.yaxis.set_major_formatter(PercentFormatter(xmax=100, decimals=0))
                axis.grid(color="#d6dbd8", linestyle="--", linewidth=0.7)
                axis.set_axisbelow(True)
            view_label = "Original GLM" if view == "original_glm" else "Luna"
            figure.suptitle(
                f"Direction-Level Performance Distributions | {view_label} | "
                f"{setting.replace('_', ' ').title()}",
                x=0.06,
                y=0.97,
                ha="left",
                fontsize=19,
            )
            figure.text(
                0.06,
                0.9,
                "Each point is one language direction, averaged equally across selected models. "
                "All three term types use the same directions.",
                fontsize=11,
            )
            figure.legend(
                handles=[
                    Patch(facecolor=color, alpha=0.4, label=label)
                    for color, label in zip(colors, labels, strict=True)
                ],
                loc="lower center",
                bbox_to_anchor=(0.5, 0.07),
                ncol=3,
                frameon=False,
                title=(
                    "Shading: 50% fitted KDE mass | points-only fallback for sparse/degenerate data"
                ),
            )
            figure.text(
                0.06,
                0.018,
                "Descriptive distributions of direction averages, not individual translations. "
                "KDE uses Scott bandwidth; regions are NOT confidence intervals.\n"
                "Metric-specific scored rows may differ. Shared directions and models do not "
                "make observations independent; no significance inference.",
                fontsize=10,
            )
            relative = Path("distributions") / view / f"performance_distributions_{setting}"
            for extension in ("png", "pdf"):
                path = output / "figures" / f"{relative.as_posix()}.{extension}"
                path.parent.mkdir(parents=True, exist_ok=True)
                figure.savefig(path, dpi=180, bbox_inches="tight")
            plt.close(figure)
            saved.append(relative.as_posix())
    write_csv(output / "tables" / "distribution_regions.csv", regions)
    return saved


def show_metric_in_figure(metric, values):
    return metric not in TERMINOLOGY[3:] or any(
        value is not None and math.isfinite(value) for value in values
    )


def build_prompting_violin_rows(summaries, aggregates):
    rows = []
    for aggregate in aggregates:
        source_view = "original_glm" if aggregate["view"] == "shared_general" else aggregate["view"]
        category = "all_terms" if aggregate["view"] == "shared_general" else aggregate["category"]
        group = summaries[(source_view, category, aggregate["run"])]["dataset_settings"][
            aggregate["dataset"]
        ][aggregate["setting"]]["by_direction"]
        for direction in filter(None, aggregate["directions"].split(";")):
            value = metric_value(group[direction], aggregate["metric"])
            if value is None:
                raise ValueError(f"Unavailable violin point in common support: {direction}")
            status = group[direction]["metric_status"][aggregate["metric"]]
            rows.append(
                {
                    **{
                        key: aggregate[key]
                        for key in (
                            "view",
                            "category",
                            "dataset",
                            "setting",
                            "run",
                            "model",
                            "metric",
                        )
                    },
                    "direction": direction,
                    "value": value,
                    "rows_scored": status["rows_scored"],
                    "statistic": aggregate["statistic"],
                    "n_common_directions": aggregate["n_directions"],
                }
            )
    return rows


def normalize_prompting_violin_rows(rows):
    panels = defaultdict(list)
    for row in rows:
        if not math.isfinite(row["value"]):
            raise ValueError("Nonfinite violin score cannot be normalized")
        panels[tuple(row[key] for key in ("view", "category", "dataset", "metric"))].append(
            row["value"]
        )
    bounds = {key: (min(values), max(values)) for key, values in panels.items()}
    normalized = []
    for row in rows:
        minimum, maximum = bounds[
            tuple(row[key] for key in ("view", "category", "dataset", "metric"))
        ]
        normalized.append(
            {
                **row,
                "raw_value": row["value"],
                "value": (row["value"] - minimum) / (maximum - minimum)
                if maximum > minimum
                else 0.5,
                "normalization_min": minimum,
                "normalization_max": maximum,
                "normalization": "panel_min_max_shared_across_models_and_both_prompts",
            }
        )
    return normalized


def write_prompting_violin_figures(
    output, aggregates, runs, violin_rows, *, normalized=False, zoomed=False
):
    return write_prompting_bar_figures(
        output, aggregates, runs, violin_rows=violin_rows, normalized=normalized, zoomed=zoomed
    )


def write_prompting_bar_figures(
    output, aggregates, runs, *, violin_rows=None, normalized=False, zoomed=False
):
    import matplotlib.pyplot as plt
    import numpy as np
    from matplotlib.patches import Patch

    if normalized and violin_rows is None:
        raise ValueError("Normalization is supported only for violin figures")
    if zoomed and (normalized or violin_rows is None):
        raise ValueError("Zoomed ranges require native-score violin figures")
    lookup = {
        (
            row["view"],
            row["category"],
            row["dataset"],
            row["setting"],
            row["run"],
            row["metric"],
        ): row["value"]
        for row in aggregates
    }
    distributions = defaultdict(list)
    for row in violin_rows or []:
        distributions[
            (
                row["view"],
                row["category"],
                row["dataset"],
                row["setting"],
                row["run"],
                row["metric"],
            )
        ].append(row["value"])
    colors = ("#317b9a", "#d88738")
    category_labels = {
        "all_terms": "All terms",
        "externally_verified": "Externally verified",
        "llm_enriched": "LLM-enriched",
    }
    saved = []
    for dataset in DATASETS:
        groups = [
            ("shared_general", "general", [("not_applicable", metric) for metric in GENERAL]),
            *[
                (
                    view,
                    "terminology",
                    [(category, metric) for category in CATEGORIES for metric in TERMINOLOGY],
                )
                for view in VIEWS
            ],
        ]
        for view, family, candidates in groups:
            panels = [
                (category, metric)
                for category, metric in candidates
                if show_metric_in_figure(
                    metric,
                    (
                        lookup[(view, category, dataset, setting, run, metric)]
                        for setting in SETTINGS
                        for run in runs
                    ),
                )
            ]
            if not panels:
                continue
            rows = math.ceil(len(panels) / 3)
            figure, axes = plt.subplots(rows, 3, figsize=(26, rows * 6.8), squeeze=False)
            positions = np.arange(len(runs))
            for axis, (category, metric) in zip(axes.flat, panels, strict=False):
                for setting_index, setting in enumerate(SETTINGS):
                    values = [
                        lookup[(view, category, dataset, setting, run, metric)] for run in runs
                    ]
                    values = np.array(values, dtype=float)
                    centers = positions + (setting_index - 0.5) * 0.38
                    if violin_rows is None:
                        axis.bar(
                            centers,
                            values,
                            width=0.36,
                            color=colors[setting_index],
                            label=setting.replace("_", " ").title(),
                            zorder=3,
                        )
                    else:
                        for center, run in zip(centers, runs, strict=True):
                            points = np.asarray(
                                distributions[(view, category, dataset, setting, run, metric)],
                                dtype=float,
                            )
                            if not len(points):
                                continue
                            if len(points) >= 3 and np.ptp(points) > 0:
                                violin = axis.violinplot(
                                    [points],
                                    positions=[center],
                                    widths=0.34,
                                    showmedians=True,
                                    showextrema=False,
                                    bw_method="scott",
                                )
                                for body in violin["bodies"]:
                                    body.set_facecolor(colors[setting_index])
                                    body.set_edgecolor(colors[setting_index])
                                    body.set_alpha(0.5)
                                violin["cmedians"].set_color(colors[setting_index])
                            else:
                                axis.hlines(
                                    np.median(points),
                                    center - 0.12,
                                    center + 0.12,
                                    color=colors[setting_index],
                                    linewidth=1.8,
                                    zorder=4,
                                )
                            jitter = ((np.arange(len(points)) * 0.61803398875) % 1 - 0.5) * 0.13
                            axis.scatter(
                                center + jitter,
                                points,
                                s=5,
                                color=colors[setting_index],
                                alpha=0.65,
                                zorder=3,
                            )
                    for center, value in zip(centers, values, strict=True):
                        if not np.isfinite(value):
                            axis.text(
                                center,
                                0.025,
                                "NA",
                                transform=axis.get_xaxis_transform(),
                                rotation=90,
                                ha="center",
                                va="bottom",
                                fontsize=7,
                                color=colors[setting_index],
                            )
                axis.set_xticks(positions, [LABELS[run] for run in runs])
                axis.tick_params(axis="x", labelrotation=60, labelsize=8)
                for label in axis.get_xticklabels():
                    label.set_ha("right")
                title = METRIC_LABELS[metric]
                if family == "terminology":
                    title = f"{category_labels[category]} | {title}"
                axis.set_title(title, fontsize=12, pad=12)
                axis.set_ylabel(
                    "Normalized score (panel min-max)" if normalized else "Score (native scale)",
                    fontsize=10,
                )
                if normalized:
                    axis.set_ylim(-0.04, 1.04)
                    axis.set_yticks((0, 0.25, 0.5, 0.75, 1))
                elif zoomed:
                    axis.margins(y=0.05)
                elif violin_rows is not None:
                    axis.set_ylim(bottom=min(0, axis.get_ylim()[0]))
                axis.grid(axis="y", color="#e4e8e5", linewidth=0.7)
                axis.set_axisbelow(True)
                axis.spines[["top", "right"]].set_visible(False)
            for axis in list(axes.flat)[len(panels) :]:
                axis.set_visible(False)
            suffix = "General metrics" if family == "general" else f"Terminology | {view}"
            figure.suptitle(
                f"{'Zoomed Native Range | ' if zoomed else ''}"
                f"{'Normalized | ' if normalized else ''}"
                f"Zero-Shot vs Few-Shot {'Violins | ' if violin_rows is not None else ''}"
                f"{DATASETS[dataset]} | {suffix}",
                fontsize=21,
                y=0.985,
            )
            figure.legend(
                handles=[
                    Patch(color=color, label=setting.replace("_", " ").title())
                    for color, setting in zip(colors, SETTINGS, strict=True)
                ],
                loc="upper center",
                bbox_to_anchor=(0.5, 0.958),
                ncol=2,
                frameon=False,
                fontsize=13,
            )
            figure.subplots_adjust(
                left=0.055,
                right=0.985,
                top=0.91,
                bottom=0.14 if normalized or zoomed else 0.11,
                hspace=0.85,
                wspace=0.25,
            )
            normalization_notes = (
                "Panel min-max normalization shared across all selected models and both prompts: "
                "0 = observed minimum, 1 = observed maximum, NOT absolute quality.\n"
                "Constant panels map to 0.5. Dataset/view/term-group panels have separate bounds; "
                "normalized magnitudes are not comparable across panels.\n"
                if normalized
                else ""
            )
            figure.text(
                0.5,
                0.018,
                (
                    "Native scores unchanged; panel axes fit all observed scores with 5% padding. "
                    "Axes need not start at zero; no observations clipped.\n"
                    if zoomed
                    else ""
                )
                + normalization_notes
                + "One point = one language-direction score, NOT one translation. "
                "Identical common directions across models and both prompts per metric.\n"
                "Violin: Scott-bandwidth KDE; center line: median. Sparse/constant groups use "
                "points and median only. "
                + (
                    "No confidence or significance inference."
                    if normalized
                    else "Native scales; no confidence or significance inference."
                )
                if violin_rows is not None
                else "Native-scale scores; bar axes include zero. Equal-direction means on "
                "metric-specific directions shared across models and both prompts.\n"
                "NA is unavailable, not zero. All-NA success-rate metrics omitted. "
                "Shared directions do not establish matched rows or statistical significance.",
                ha="center",
                fontsize=11,
                linespacing=1.6,
            )
            kind = (
                "violins_zoomed"
                if zoomed
                else "violins_normalized"
                if normalized
                else ("violins" if violin_rows is not None else "bars")
            )
            relative = f"prompting/{kind}/{view}/prompting_{kind}_{family}_{dataset}"
            for extension in ("png", "pdf"):
                path = output / "figures" / f"{relative}.{extension}"
                path.parent.mkdir(parents=True, exist_ok=True)
                figure.savefig(path, dpi=180, bbox_inches="tight")
            plt.close(figure)
            saved.append(relative)
    return saved


def write_chosen_prompting_figures(output, bar_figures, *, zoomed=False):
    number = "05" if zoomed else "04"
    folder = "05_zoomed_native_violins" if zoomed else "04_zero_vs_few_shot"
    saved = []
    for relative in bar_figures:
        source = Path(relative)
        chosen = Path("chosen") / folder / source.parent.name / f"chosen_{number}_{source.name}"
        for extension in ("png", "pdf"):
            target = output / "figures" / f"{chosen.as_posix()}.{extension}"
            target.parent.mkdir(parents=True, exist_ok=True)
            copyfile(output / "figures" / f"{relative}.{extension}", target)
        saved.append(chosen.as_posix())
    if not saved:
        return saved
    index = output / "figures" / "chosen" / "README.md"
    existing = index.read_text(encoding="utf-8") if index.exists() else "# Chosen Figures\n"
    existing, _, section = existing.partition(f"\n## Chosen {number}:")
    _, separator, following = section.partition("\n## ")
    following = separator + following if separator else ""
    existing = existing.rstrip()
    lines = [
        "",
        "",
        f"## Chosen {number}: "
        + ("Zoomed Native-Score Violins" if zoomed else "Zero-Shot vs Few-Shot Metric Bars"),
        "",
        (
            "Paired zero-shot (blue) and few-shot (orange) direction-level distributions for "
            "all selected models. Three general-metric figures and six terminology figures cover "
            "all three datasets and both annotation views, with separate term-group panels. "
            "These are identical copies of the zoomed native-score violins, not new scores."
            if zoomed
            else "Models on x, native metric scores on y; "
            "zero-shot (blue) beside few-shot (orange). "
            "Three general-metric figures and six terminology figures cover all three datasets "
            "and both annotation views. All/external/LLM-enriched terminology groups have separate "
            "panels. These are identical copies of the prompting bar figures, not new scores."
        ),
        "",
        (
            "Only the y-axis range is adjusted: all observed native scores with 5% padding, "
            "shared across models and both prompts within each panel. No 0-1 normalization "
            "or clipping. Each point is one language-direction score, not one translation; "
            "the center line is the median. No confidence or significance inference."
            if zoomed
            else "Axes include zero. Unavailable scores are NA, not zero; universally unavailable "
            "success-rate metrics are omitted. Shared-direction means do not establish matched "
            "rows or statistical significance."
        ),
        "",
    ]
    for relative in saved:
        target = Path(relative).relative_to("chosen").as_posix()
        lines.append(f"- {target}: [PNG]({target}.png) | [PDF]({target}.pdf)")
    index.write_text(existing + "\n".join(lines) + "\n" + following, encoding="utf-8")
    return saved


def correlation_color_norm():
    import numpy as np
    from matplotlib.colors import FuncNorm

    def forward(values):
        return np.sign(values) * (1 - (1 - np.clip(np.abs(values), 0, 1)) ** 0.25)

    def inverse(values):
        return np.sign(values) * (1 - (1 - np.clip(np.abs(values), 0, 1)) ** 4)

    return FuncNorm((forward, inverse), vmin=-1, vmax=1, clip=True)


def write_complete_metric_figures(output, aggregates, runs, correlations):
    import matplotlib.pyplot as plt
    import numpy as np
    from scipy.stats import rankdata

    saved = []
    category_labels = {
        "not_applicable": "General",
        "all_terms": "All",
        "externally_verified": "External",
        "llm_enriched": "LLM-enriched",
    }
    lookup = {
        (
            row["view"],
            row["category"],
            row["dataset"],
            row["setting"],
            row["run"],
            row["metric"],
        ): row["value"]
        for row in aggregates
    }

    def save(figure, relative):
        for extension in ("png", "pdf"):
            path = output / "figures" / f"{relative}.{extension}"
            path.parent.mkdir(parents=True, exist_ok=True)
            figure.savefig(path, dpi=180, bbox_inches="tight")
        plt.close(figure)
        saved.append(relative)

    def score_panel(axis, view, category, dataset, setting, metrics, show_models=True):
        metrics = tuple(
            metric
            for metric in metrics
            if show_metric_in_figure(
                metric,
                (lookup[(view, category, dataset, setting, run, metric)] for run in runs),
            )
        )
        scores = np.array(
            [
                [lookup[(view, category, dataset, setting, run, metric)] for metric in metrics]
                for run in runs
            ],
            dtype=float,
        )
        ranks = np.full(scores.shape, np.nan)
        for column in range(len(metrics)):
            finite = np.isfinite(scores[:, column])
            if finite.any():
                ranks[finite, column] = (rankdata(scores[finite, column]) - 1) / max(
                    1, finite.sum() - 1
                )
        axis.imshow(np.ma.masked_invalid(ranks), cmap="YlGnBu", vmin=0, vmax=1, aspect="auto")
        for row in range(len(runs)):
            for column, metric in enumerate(metrics):
                value = scores[row, column]
                digits = (
                    2 if metric in CORPUS or metric in TERMINOLOGY[0:2] + TERMINOLOGY[3:] else 3
                )
                label = "NA" if not np.isfinite(value) else f"{value:.{digits}f}"
                axis.text(
                    column,
                    row,
                    label,
                    ha="center",
                    va="center",
                    fontsize=9,
                    color="white" if ranks[row, column] > 0.65 else "#202a27",
                )
        axis.set_xticks(
            range(len(metrics)),
            [METRIC_LABELS[metric] for metric in metrics],
            rotation=35,
            ha="right",
            fontsize=9,
        )
        axis.set_yticks(
            range(len(runs)),
            [LABELS[run] if show_models else "" for run in runs],
            fontsize=10,
        )
        axis.set_title(f"{DATASETS[dataset]} | {setting.replace('_', ' ').title()}", pad=14)
        axis.tick_params(length=0)

    for dataset in DATASETS:
        figure, axes = plt.subplots(1, 2, figsize=(24, 9))
        for axis, setting in zip(axes, SETTINGS, strict=True):
            score_panel(axis, "shared_general", "not_applicable", dataset, setting, GENERAL)
        figure.suptitle(f"All Translation-Quality Metrics | {DATASETS[dataset]}", fontsize=20)
        figure.text(
            0.5,
            0.035,
            "Cells: native-scale scores. Darker: higher model rank within each metric/prompt. "
            "Equal-direction means; metric-specific common support; NA is unavailable.",
            ha="center",
            fontsize=11,
        )
        figure.subplots_adjust(left=0.11, right=0.99, top=0.88, bottom=0.23, wspace=0.32)
        save(figure, f"all_metrics/general/all_metrics_{dataset}")
    for view in VIEWS:
        for category in CATEGORIES:
            figure, axes = plt.subplots(2, 3, figsize=(26, 15))
            for column, dataset in enumerate(DATASETS):
                for row, setting in enumerate(SETTINGS):
                    score_panel(
                        axes[row, column],
                        view,
                        category,
                        dataset,
                        setting,
                        TERMINOLOGY,
                        show_models=column == 0,
                    )
            figure.suptitle(
                f"All Terminology Metrics | {view} | {category_labels[category]} terms",
                fontsize=21,
            )
            figure.text(
                0.5,
                0.025,
                "Cells: native-scale scores. Darker: higher model rank within each metric/prompt. "
                "Metric-specific shared directions; not necessarily identical rows. "
                "NA is unavailable; all-NA success-rate metrics are omitted.",
                ha="center",
                fontsize=11,
            )
            figure.subplots_adjust(
                left=0.105, right=0.99, top=0.91, bottom=0.17, hspace=0.75, wspace=0.18
            )
            save(figure, f"all_metrics/{category}/{view}/all_terminology_metrics")

    saved += write_correlation_figures(output, runs, correlations)
    overall = [row for row in correlations if row["dataset"] == "all_datasets"]
    if overall:
        selected = select_distinct_metric_columns(overall)
        saved += write_correlation_figures(output, runs, overall, selected)
    return saved


def write_correlation_figures(output, runs, correlations, selected_columns=None):
    import matplotlib.pyplot as plt
    import numpy as np

    saved = []
    category_labels = {
        "not_applicable": "General",
        "all_terms": "All",
        "externally_verified": "External",
        "llm_enriched": "LLM-enriched",
    }
    short_labels = {
        "target_term_coverage": "Coverage",
        "variant_aware_target_term_coverage": "Variant coverage",
        "term_bertscore_recall": "Term BERTScore",
        "terminology_success_rate": "Success rate",
        "variant_aware_terminology_success_rate": "Variant success",
    }

    def save(figure, relative):
        for extension in ("png", "pdf"):
            path = output / "figures" / f"{relative}.{extension}"
            path.parent.mkdir(parents=True, exist_ok=True)
            figure.savefig(path, dpi=180, bbox_inches="tight")
        plt.close(figure)
        saved.append(relative)

    all_columns = [("not_applicable", metric) for metric in GENERAL] + [
        (category, metric) for category in CATEGORIES for metric in TERMINOLOGY
    ]
    if selected_columns is not None:
        all_columns = [(row["category"], row["metric"]) for row in selected_columns]
    grouped = defaultdict(list)
    for row in correlations:
        grouped[(row["view"], row["dataset"], row["setting"])].append(row)
    correlation_norm = correlation_color_norm()
    for (view, dataset, setting), rows in grouped.items():
        columns = [
            column
            for column in all_columns
            if show_metric_in_figure(
                column[1],
                (
                    row["correlation"]
                    for row in rows
                    if column
                    in (
                        (row["category_x"], row["metric_x"]),
                        (row["category_y"], row["metric_y"]),
                    )
                ),
            )
        ]
        column_index = {column: index for index, column in enumerate(columns)}
        labels = [
            METRIC_LABELS[metric]
            if category == "not_applicable"
            else f"{category_labels[category]} | {short_labels[metric]}"
            for category, metric in columns
        ]
        figure, axes = plt.subplots(
            1, 2, figsize=(23, 14) if selected_columns is not None else (32, 18)
        )
        for axis, method in zip(axes, ("pearson", "spearman"), strict=True):
            matrix = np.full((len(columns), len(columns)), np.nan)
            supports = []
            for row in rows:
                if (
                    row["method"] != method
                    or (row["category_x"], row["metric_x"]) not in column_index
                    or (row["category_y"], row["metric_y"]) not in column_index
                ):
                    continue
                if row["correlation"] is not None:
                    index_x = column_index[(row["category_x"], row["metric_x"])]
                    index_y = column_index[(row["category_y"], row["metric_y"])]
                    matrix[index_x, index_y] = matrix[index_y, index_x] = row["correlation"]
                    supports.append(row["n_directions"])
            image = axis.imshow(np.ma.masked_invalid(matrix), cmap="RdBu", norm=correlation_norm)
            for index_x in range(len(columns)):
                for index_y in range(len(columns)):
                    value = matrix[index_y, index_x]
                    red, green, blue, _ = image.cmap(correlation_norm(value))
                    luminance = 0.2126 * red + 0.7152 * green + 0.0722 * blue
                    axis.text(
                        index_x,
                        index_y,
                        "NA" if not np.isfinite(value) else f"{value:.3f}",
                        ha="center",
                        va="center",
                        fontsize=11 if selected_columns is not None else 7,
                        color="white" if np.isfinite(value) and luminance < 0.5 else "#202a27",
                    )
            axis.set_xticks(range(len(labels)), labels, rotation=60, ha="right", fontsize=9)
            axis.set_yticks(range(len(labels)), labels, fontsize=9)
            boundaries = [
                index + 0.5
                for index, column in enumerate(columns[:-1])
                if column[0] != columns[index + 1][0]
            ]
            for boundary in boundaries:
                axis.axhline(boundary, color="#303735", linewidth=1.6)
                axis.axvline(boundary, color="#303735", linewidth=1.6)
            support_text = f"{min(supports)}-{max(supports)}" if supports else "0"
            support_unit = (
                "dataset-direction supports" if dataset == "all_datasets" else "common directions"
            )
            axis.set_title(
                f"{method.title()} | {len(runs)} model scores per pair | "
                f"{support_text} {support_unit}",
                fontsize=16,
                pad=18,
            )
            axis.tick_params(length=0)
        title = "Four Selected Metrics" if selected_columns is not None else "Metric Correlations"
        dataset_label = DATASETS.get(dataset, "All Three Datasets (Equal Weight)")
        figure.suptitle(
            f"{title} | {dataset_label} | {view} | {setting.replace('_', ' ').title()}",
            fontsize=24,
            y=0.96,
        )
        figure.subplots_adjust(left=0.12, right=0.95, bottom=0.25, top=0.88, wspace=0.38)
        color_axis = figure.add_axes((0.965, 0.32, 0.009, 0.48))
        colorbar = figure.colorbar(
            image,
            cax=color_axis,
            ticks=(-1, -0.99, -0.95, -0.8, 0, 0.8, 0.95, 0.99, 1),
            label="Correlation (nonlinear colors; expanded near -1 and +1)",
        )
        colorbar.ax.minorticks_off()
        colorbar.ax.set_yticklabels(
            ("-1.000", "-0.990", "-0.950", "-0.800", "0.000", "0.800", "0.950", "0.990", "1.000")
        )
        selection_text = (
            "Four distinct metrics minimizing mean absolute Pearson/Spearman correlation across "
            "both prompts and annotation views; no metric-family coverage constraint.\n"
            if selected_columns is not None
            else "Blocks: general metrics | all terms | externally verified | "
            "LLM-enriched (refined). "
            "Off-diagonal blocks compare metrics across term groups.\n"
        )
        aggregation_text = (
            "All datasets: one point per model, equally averaging three dataset direction-macros; "
            "One observation per selected model, NOT pooled model/dataset points.\n"
            if dataset == "all_datasets"
            else ""
        )
        figure.text(
            0.5,
            0.065,
            selection_text
            + aggregation_text
            + "Cells: unchanged coefficients to three decimals. Colors use a shared nonlinear "
            "scale to expand differences near +/-1; colorbar ticks are actual correlations.\n"
            "Each pair uses common directions within each dataset "
            "across all models, both prompts and all three term groups for terminology metrics.\n"
            "Pairwise supports may differ; NA = unavailable or constant. "
            "All-NA success-rate metrics are omitted. "
            "Descriptive model-level correlations, not per-translation correlations "
            "or significance tests.",
            ha="center",
            fontsize=12,
            linespacing=1.7,
        )
        relative = f"correlations/{view}/metric_correlations_{dataset}_{setting}"
        if selected_columns is not None:
            relative = (
                f"correlations/selected_four/{view}/"
                f"metric_correlations_selected_four_{dataset}_{setting}"
            )
        save(figure, relative)
    return saved


def load_translation_timings(root):
    path = root / "translation_timing_manifest.json"
    if not path.exists():
        return {}
    manifest = json.loads(path.read_text(encoding="utf-8"))
    if not manifest.get("complete"):
        raise ValueError("Translation timing download is incomplete")
    summaries = {}
    for entry in manifest["files"]:
        payload = (root / entry["path"]).read_bytes()
        if hashlib.sha256(payload).hexdigest() != entry["sha256"]:
            raise ValueError(f"Translation timing checksum mismatch: {entry['run']}")
        document = json.loads(payload)
        if document.get("name") != entry["run"]:
            raise ValueError(f"Translation timing identity mismatch: {entry['run']}")
        if population(entry["run"]) == "excluded":
            continue
        document["_source_url"] = entry["source_url"]
        document["_sha256"] = entry["sha256"]
        summaries[entry["run"]] = document
    if set(summaries) != set(LABELS):
        raise ValueError("Translation timing population differs from the ranked models")
    return summaries


def estimate_token_cost(
    input_tokens, output_tokens, input_rate, output_rate, cached_tokens=0, cached_rate=None
):
    values = (input_tokens, output_tokens, input_rate, output_rate, cached_tokens)
    if any(
        not isinstance(value, (int, float)) or not math.isfinite(value) or value < 0
        for value in values
    ):
        raise ValueError("Token counts and rates must be finite and nonnegative")
    if cached_tokens > input_tokens:
        raise ValueError("Cached tokens cannot exceed total input tokens")
    if cached_tokens and (cached_rate is None or not math.isfinite(cached_rate) or cached_rate < 0):
        raise ValueError("Discounted cached tokens require a verified cache-read rate")
    uncached_cost = (input_tokens - cached_tokens) * input_rate / 1_000_000
    cached_cost = cached_tokens * (cached_rate or 0) / 1_000_000
    output_cost = output_tokens * output_rate / 1_000_000
    return {
        "input_cost_usd": uncached_cost + cached_cost,
        "cached_input_cost_usd": cached_cost,
        "output_cost_usd": output_cost,
        "total_cost_usd": uncached_cost + cached_cost + output_cost,
    }


def build_api_cost_rows(translation_summaries, pricing):
    if pricing.get("currency") != "USD" or pricing.get("rate_unit") != "per_1000000_tokens":
        raise ValueError("API pricing must specify USD per million tokens")
    rows = []
    for run in sorted(translation_summaries):
        summary = translation_summaries[run]
        quote = pricing["models"].get(run)
        if quote and quote["recorded_model"] != summary.get("model"):
            raise ValueError(f"API price does not match recorded model: {run}")
        strata = [(dataset, setting) for dataset in DATASETS for setting in SETTINGS]
        scopes = [
            ("dataset_prompt", dataset, setting, [(dataset, setting)])
            for dataset, setting in strata
        ]
        scopes.append(("overall", "all_datasets", "both_prompts", strata))
        for scope, dataset, setting, selected in scopes:
            groups = [summary["datasets"][data]["settings"][prompt] for data, prompt in selected]
            usage = {}
            for field in ("input_tokens", "output_tokens", "cached_tokens", "reasoning_tokens"):
                values = [group.get(field) for group in groups]
                if any(
                    not isinstance(value, (int, float)) or not math.isfinite(value) or value < 0
                    for value in values
                ):
                    raise ValueError(f"Incomplete token accounting: {run}/{field}")
                usage[field] = sum(values)
            if usage["cached_tokens"] > usage["input_tokens"]:
                raise ValueError(f"Cached tokens exceed input tokens: {run}")
            requests = [group.get("requests") for group in groups]
            request_count = (
                sum(requests)
                if all(
                    isinstance(value, (int, float)) and math.isfinite(value) and value >= 0
                    for value in requests
                )
                else None
            )
            scenarios = [("reference", quote)]
            if quote:
                scenarios += [
                    (item["name"], {**quote, **item, "pricing_model_id": item["name"]})
                    for item in quote.get("alternatives", [])
                ]
            for scenario, rates in scenarios:
                cost = (
                    estimate_token_cost(
                        usage["input_tokens"],
                        usage["output_tokens"],
                        rates["input_rate"],
                        rates["output_rate"],
                    )
                    if rates
                    else {
                        field: None
                        for field in (
                            "input_cost_usd",
                            "cached_input_cost_usd",
                            "output_cost_usd",
                            "total_cost_usd",
                        )
                    }
                )
                rows.append(
                    {
                        "run": run,
                        "model": LABELS[run],
                        "recorded_model": summary.get("model"),
                        "scope": scope,
                        "dataset": dataset,
                        "setting": setting,
                        "scenario": scenario,
                        "pricing_state": "estimated_no_cache_discount"
                        if rates
                        else "unpriced_no_verified_matching_offer",
                        **usage,
                        "recorded_requests": request_count,
                        "provider": rates["provider"] if rates else None,
                        "pricing_model_id": rates["pricing_model_id"] if rates else None,
                        "input_usd_per_million": rates["input_rate"] if rates else None,
                        "output_usd_per_million": rates["output_rate"] if rates else None,
                        "published_cached_input_usd_per_million": rates.get("cached_input_rate")
                        if rates
                        else None,
                        "billed_cached_tokens_assumed": 0,
                        **cost,
                        "usd_per_1000_recorded_requests": cost["total_cost_usd"]
                        * 1000
                        / request_count
                        if rates and request_count
                        else None,
                        "pricing_verified_on": pricing["verified_on"],
                        "pricing_source_url": rates["source_url"] if rates else None,
                        "usage_source_url": summary.get("_source_url"),
                        "usage_sha256": summary.get("_sha256"),
                        "cost_basis": pricing["scenario"],
                    }
                )
    return rows


def write_api_cost_report(output, rows, pricing):
    write_csv(output / "tables" / "api_cost_estimates.csv", rows)
    lines = [
        "# API Cost Estimates",
        "",
        f"Published rate snapshot checked on {pricing['verified_on']}. Currency: USD.",
        "",
        "These are counterfactual recorded-token repricing scenarios, not invoices, "
        "actual local-GPU costs, or proof of identical results if hosted elsewhere. "
        "NA means no verified matching price in the sources checked, never free inference.",
        "",
        "## Reference Scenario: No Cache Discount",
        "",
        "Cost = input tokens / 1,000,000 * input price + output tokens / 1,000,000 * output price.",
        "",
        "Token totals are summed across the three datasets and both prompts, once only. "
        "They are not multiplied by annotation views or terminology groups.",
        "",
        "| Model | Input Tokens (M) | Output Tokens (M) | Input $/M | Output $/M | "
        "Input Cost | Output Cost | Total USD |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]

    def amount(value):
        return "NA" if value is None else f"{value:.2f}"

    overall = [row for row in rows if row["scope"] == "overall"]
    for row in overall:
        if row["scenario"] != "reference":
            continue
        values = [
            row["input_tokens"] / 1e6,
            row["output_tokens"] / 1e6,
            row["input_usd_per_million"],
            row["output_usd_per_million"],
            row["input_cost_usd"],
            row["output_cost_usd"],
            row["total_cost_usd"],
        ]
        lines.append("| " + " | ".join([row["model"], *[amount(value) for value in values]]) + " |")
    lines += [
        "",
        "Rates in the CSV retain full precision; displayed monetary amounts are rounded. "
        "The reference GPT-6 Luna price assumes Azure Standard Global short context. "
        "Other priced models use the OpenRouter catalog quote, not the original deployment "
        "or necessarily the cheapest routed provider.",
        "",
        "## Azure Scenario Sensitivity",
        "",
        "Actual deployment geography and per-request context bands are not established. "
        "The alternatives below reprice all recorded tokens at each listed rate; "
        "they do not classify individual requests by context length.",
        "",
        "| Model | Scenario | Input Cost USD | Output Cost USD | Total USD |",
        "| --- | --- | ---: | ---: | ---: |",
    ]
    for row in overall:
        if row["run"] == "gpt_6_luna_azure":
            scenario = (
                row["pricing_model_id"] if row["scenario"] == "reference" else row["scenario"]
            )
            lines.append(
                f"| {row['model']} | {scenario} | {amount(row['input_cost_usd'])} | "
                f"{amount(row['output_cost_usd'])} | {amount(row['total_cost_usd'])} |"
            )
    lines += ["", "## Assumptions and Limits", ""]
    lines.extend(f"- {assumption}" for assumption in pricing["assumptions"])
    lines += [
        "- Recorded cached-token counts are exported but not deducted in the reference "
        "scenario. Cache-read list rates are retained for audit only; zero assumed billed "
        "cached tokens does not mean that no local cache was used.",
        "- Reasoning tokens are retained as metadata and not added again to output "
        "tokens. The current translation summaries report zero reasoning tokens.",
        "- Token totals and covered requests differ slightly between models. The CSV "
        "includes per-dataset/prompt values and cost per 1,000 recorded requests; "
        "this does not establish row-matched workloads.",
        "- Granite 4.2 30B and the four Tiny Aya variants remain unpriced. "
        "Aya Expanse, Granite 4.2 8B, free tiers, and different Qwen/Nemotron variants "
        "were not substituted for the recorded models.",
        "",
        "## Sources",
        "",
    ]
    lines.extend(f"- {source}" for source in pricing["sources_checked"])
    lines += [
        "",
        "[Detailed cost and usage CSV](tables/api_cost_estimates.csv)",
        "",
        "Reproduce with the pinned snapshot:",
        "",
        "```powershell",
        "uv run --no-sync python scripts/render_evaluation_results.py --api-costs-only",
        "```",
        "",
    ]
    (output / "api_cost_estimates.md").write_text("\n".join(lines), encoding="utf-8")


def build_efficiency_rows(mixed_ranks, translation_summaries):
    rows = []
    for ranked in mixed_ranks:
        summary = translation_summaries.get(ranked["run"], {})
        strata = (
            [(dataset, setting) for dataset in DATASETS for setting in SETTINGS]
            if ranked["scope"] == "overall"
            else [(ranked["dataset"], ranked["setting"])]
        )
        measurements = []
        for dataset, setting in strata:
            group = (
                summary.get("datasets", {}).get(dataset, {}).get("settings", {}).get(setting, {})
            )
            latency = group.get("timing", {}).get("latency_s", {}) or {}
            value, count = latency.get("mean"), latency.get("count", 0)
            if (
                isinstance(value, (int, float))
                and math.isfinite(value)
                and value > 0
                and isinstance(count, (int, float))
                and math.isfinite(count)
                and count > 0
            ):
                measurements.append(
                    {
                        "mean": value,
                        "count": count,
                        "requests_translated": group.get("requests_translated"),
                        "rows_translated": group.get("rows_translated"),
                    }
                )
        complete = len(measurements) == len(strata)
        counts = {}
        for field in ("requests_translated", "rows_translated"):
            values = [measurement[field] for measurement in measurements]
            counts[field] = (
                sum(values)
                if values and all(isinstance(value, (int, float)) for value in values)
                else None
            )
        rows.append(
            {
                **{
                    key: ranked[key]
                    for key in (
                        "view",
                        "scope",
                        "dataset",
                        "setting",
                        "run",
                        "model",
                        "mixed_rank",
                        "mixed_mean_rank",
                    )
                },
                "mean_latency_s": mean(item["mean"] for item in measurements) if complete else None,
                "timing_state": "completed" if complete else "missing_timing",
                "n_timing_strata": len(measurements),
                "n_expected_strata": len(strata),
                "timed_latency_requests": sum(item["count"] for item in measurements),
                **counts,
                "latency_statistic": "equal_stratum_mean_request_latency_s",
                "timing_scope": "all_timed_requests_in_original_translation_summary",
                "timing_source_url": summary.get("_source_url"),
                "timing_sha256": summary.get("_sha256"),
            }
        )
    return rows


def latency_bubble_area(seconds):
    if not isinstance(seconds, (int, float)) or not math.isfinite(seconds) or seconds <= 0:
        raise ValueError("Bubble latency must be finite and positive")
    return 8 * seconds


def build_output_token_rank_rows(efficiency, translation_summaries):
    rows = []
    for timing in efficiency:
        summary = translation_summaries.get(timing["run"], {})
        strata = (
            [(dataset, setting) for dataset in DATASETS for setting in SETTINGS]
            if timing["scope"] == "overall"
            else [(timing["dataset"], timing["setting"])]
        )
        groups = [
            summary.get("datasets", {}).get(dataset, {}).get("settings", {}).get(setting, {})
            for dataset, setting in strata
        ]
        totals = {}
        for field in ("output_tokens", "reasoning_tokens", "requests_translated"):
            values = [group.get(field) for group in groups]
            totals[field] = (
                sum(values)
                if all(
                    isinstance(value, (int, float))
                    and not isinstance(value, bool)
                    and math.isfinite(value)
                    and value >= 0
                    and float(value).is_integer()
                    for value in values
                )
                else None
            )
        thinking = DEFAULT_THINKING_MODELS.get(timing["run"])
        latency = timing["mean_latency_s"]
        valid_time = isinstance(latency, (int, float)) and math.isfinite(latency) and latency > 0
        state = (
            "not_selected_by_default_evidence"
            if thinking is None
            else "missing_output_tokens"
            if totals["output_tokens"] is None
            else "missing_latency"
            if not valid_time
            else "plotted"
        )
        rows.append(
            {
                **timing,
                "output_tokens": totals["output_tokens"],
                "reported_reasoning_tokens": totals["reasoning_tokens"],
                "token_requests_translated": totals["requests_translated"],
                "bubble_area_pt2": latency_bubble_area(latency) if valid_time else None,
                "plot_state": state,
                "selection_basis": "documented_model_default_not_verified_run_setting",
                "default_thinking_source_url": thinking["source_url"] if thinking else None,
                "default_thinking_evidence": thinking["evidence"] if thinking else None,
                "default_thinking_verified_on": "2026-11-04" if thinking else None,
                "thinking_token_inclusion": "unverified; reasoning tokens not added again",
                "token_statistic": "sum_recorded_output_tokens_across_scope_strata",
                "token_source_url": summary.get("_source_url"),
                "token_sha256": summary.get("_sha256"),
            }
        )
    return rows


def build_cost_rank_bubble_rows(efficiency, costs):
    reference = {}
    for row in costs:
        if row["scenario"] != "reference":
            continue
        key = tuple(row[field] for field in ("scope", "dataset", "setting", "run"))
        if key in reference:
            raise ValueError("Duplicate reference API price for a model/stratum")
        reference[key] = row
    rows = []
    for timing in efficiency:
        key = tuple(timing[field] for field in ("scope", "dataset", "setting", "run"))
        cost = reference.get(key, {})
        amount = cost.get("total_cost_usd")
        latency = timing["mean_latency_s"]
        valid_cost = isinstance(amount, (int, float)) and math.isfinite(amount) and amount >= 0
        valid_time = isinstance(latency, (int, float)) and math.isfinite(latency) and latency > 0
        rows.append(
            {
                **timing,
                "estimated_api_cost_usd": amount,
                "input_cost_usd": cost.get("input_cost_usd"),
                "output_cost_usd": cost.get("output_cost_usd"),
                "bubble_area_pt2": latency_bubble_area(latency) if valid_time else None,
                "plot_state": "plotted"
                if valid_cost and valid_time
                else ("unpriced" if not valid_cost else "missing_latency"),
                "pricing_scenario": "reference",
                "pricing_provider": cost.get("provider"),
                "pricing_model_id": cost.get("pricing_model_id"),
                "pricing_source_url": cost.get("pricing_source_url"),
                "pricing_verified_on": cost.get("pricing_verified_on"),
                "cost_basis": cost.get("cost_basis"),
                "cost_input_tokens": cost.get("input_tokens"),
                "cost_output_tokens": cost.get("output_tokens"),
            }
        )
    return rows


def write_cost_rank_bubble_figures(output, rows):
    return write_rank_latency_bubble_figures(output, rows, output_tokens=False)


def write_output_token_rank_figures(output, rows):
    return write_rank_latency_bubble_figures(output, rows, output_tokens=True)


def write_rank_latency_bubble_figures(output, rows, *, output_tokens):
    import matplotlib.pyplot as plt
    from adjustText import adjust_text

    number = "03"
    folder = "output_tokens" if output_tokens else "03_api_cost_vs_rank_latency"
    measure = "output_tokens" if output_tokens else "estimated_api_cost_usd"
    divisor = 1_000_000 if output_tokens else 1
    title_label = (
        "Output Tokens vs Mixed Rank" if output_tokens else "Estimated API Cost vs Mixed Rank"
    )
    grouped = defaultdict(list)
    for row in rows:
        grouped[(row["view"], row["scope"], row["dataset"], row["setting"])].append(row)
    plotted_values = [row[measure] / divisor for row in rows if row["plot_state"] == "plotted"]
    if not plotted_values:
        return []
    colors = {run: plt.get_cmap("tab10")(index) for index, run in enumerate(LABELS)}
    saved = []
    for (view, scope, dataset, setting), members in grouped.items():
        plotted = sorted(
            [row for row in members if row["plot_state"] == "plotted"],
            key=lambda row: (row["mixed_rank"], row["run"]),
        )
        if not plotted:
            continue
        figure, axis = plt.subplots(figsize=(13, 9))
        positions_x = [row[measure] / divisor for row in plotted]
        positions_y = [row["mixed_rank"] for row in plotted]
        bubbles = axis.scatter(
            positions_x,
            positions_y,
            s=[row["bubble_area_pt2"] for row in plotted],
            c=[colors[row["run"]] for row in plotted],
            alpha=0.8,
            edgecolor="white",
            linewidth=0.9,
            zorder=3,
        )
        texts = [
            axis.text(
                row[measure] / divisor,
                row["mixed_rank"],
                row["model"],
                fontsize=8.5,
                color=colors[row["run"]],
                ha="left",
                va="center",
            )
            for row in plotted
        ]
        axis.set_xlim(0, max(max(plotted_values), 1e-6) * (1.25 if output_tokens else 1.15))
        axis.set_ylim(len(LABELS) + 0.6, 0.4)
        axis.set_yticks(range(1, len(LABELS) + 1))
        axis.set_xlabel(
            "Recorded output tokens for workload (millions)"
            if output_tokens
            else "Estimated hosted-API token cost for recorded workload (USD; lower is better)"
        )
        axis.set_ylabel("Balanced mixed rank among selected models (1 = best)")
        axis.grid(color="#e4e8e5", linewidth=0.7)
        axis.set_axisbelow(True)
        legend_sizes = (20, 60, 120)
        handles = [
            axis.scatter([], [], s=latency_bubble_area(seconds), color="#83908b", alpha=0.6)
            for seconds in legend_sizes
        ]
        axis.legend(
            handles,
            [f"{seconds} s" for seconds in legend_sizes],
            title="Bubble area: observed latency\nSmaller = faster",
            loc="upper left",
            bbox_to_anchor=(1.02, 1.0),
            frameon=False,
            labelspacing=1.2,
            handlelength=4,
            handleheight=3.8,
            handletextpad=1.2,
            borderaxespad=0.4 if output_tokens else 1.5,
            fontsize=9,
            title_fontsize=9,
        )
        title = (
            "All three datasets | Zero-shot + Few-shot"
            if scope == "overall"
            else (f"{DATASETS[dataset]} | {setting.replace('_', ' ').title()}")
        )
        figure.suptitle(
            title_label if output_tokens else f"Chosen {number} | {title_label}",
            fontsize=19,
            y=0.97,
        )
        cohort_label = (
            f"{len(plotted)} default-thinking models"
            if output_tokens
            else f"{len(plotted)}/{len(members)} models priced"
        )
        figure.text(
            0.53,
            0.915,
            f"{title} | {view} | {cohort_label}",
            ha="center",
            fontsize=12,
        )
        figure.subplots_adjust(left=0.085, right=0.76, top=0.85, bottom=0.30)
        figure.canvas.draw()
        for text, row in zip(texts, plotted, strict=True):
            position_x, position_y = axis.transData.transform(
                (row[measure] / divisor, row["mixed_rank"])
            )
            offset = (math.sqrt(row["bubble_area_pt2"]) / 2 + 5) * figure.dpi / 72
            text.set_position(
                axis.transData.inverted().transform((position_x + offset, position_y))
            )
        adjust_text(
            texts,
            objects=bubbles,
            target_x=positions_x,
            target_y=positions_y,
            ax=axis,
            expand=(1.12, 1.25),
            force_text=(0.2, 0.3),
            force_static=(0.5, 0.5),
            force_pull=(0, 0),
            iter_lim=400,
            min_arrow_len=5,
            arrowprops={"arrowstyle": "-", "color": "#83908b", "lw": 0.6},
        )
        omitted = [row["model"] for row in members if row["plot_state"] != "plotted"]
        token_notes = (
            "Original generation workload before analysis exclusions; not remeasured.\n"
            "Area = 8 square points per latency second; identical token-axis and area scales "
            "across figures. Smaller bubbles mean lower observed latency.\n"
            "Recorded output totals, NOT verified thinking-inclusive counts. "
            "Reported reasoning tokens are not added again.\n"
            "Cohort: thinking enabled by default in official cards/templates; "
            "benchmark-run overrides are unverified.\n"
            "Overall tokens sum six dataset/prompt strata; latency averages their means equally. "
            "Ranks remain among all selected models, not the subset.\n"
            "Tokenizers, hardware, concurrency and workloads differ; "
            "not a row-matched or equal-budget comparison.\n"
            f"Excluded/missing: {', '.join(omitted) if omitted else 'none'}."
        )
        cost_notes = (
            "Original generation workload before analysis exclusions; not remeasured.\n"
            "Upper-left with a smaller bubble is preferable. Area = 8 square points per "
            "latency second; identical area and axis scales across figures.\n"
            "Cost: published hosted-API reference repricing of recorded input + output tokens, "
            "no cache discount; not actual bills.\n"
            "Latency: original local/API deployments, not the priced hosted offers. "
            "Hardware, concurrency and workloads differ; cost, timing and quality are not "
            "proven row-matched.\n"
            "Overall cost sums six dataset/prompt strata; overall latency averages their means "
            "equally. Ranks are retained from all selected models, "
            "not recomputed for the priced subset.\n"
            f"Unpriced/missing (not zero): {', '.join(omitted) if omitted else 'none'}."
        )
        figure.text(
            0.5,
            0.055,
            token_notes if output_tokens else cost_notes,
            ha="center",
            fontsize=9,
            linespacing=1.6,
        )
        stem = "overall" if scope == "overall" else f"{dataset}_{setting}"
        relative = (
            f"output_tokens/{view}/output_tokens_vs_rank_latency_{stem}"
            if output_tokens
            else f"chosen/{folder}/{view}/chosen_{folder}_{stem}"
        )
        for extension in ("png", "pdf"):
            path = output / "figures" / f"{relative}.{extension}"
            path.parent.mkdir(parents=True, exist_ok=True)
            figure.savefig(path, dpi=180, bbox_inches="tight")
        plt.close(figure)
        saved.append(relative)
    index = output / "figures" / ("output_tokens" if output_tokens else "chosen") / "README.md"
    token_description = (
        "X = recorded output tokens (millions); Y = selected-cohort mixed rank; "
        "bubble area = observed latency. Select models documented as thinking by default, "
        "not runs proven to use thinking. Gemma's template defaults to thinking off; "
        "Tiny Aya has no verified default-thinking evidence. The local GPT config disables "
        "thinking but is not verified as the downloaded run's original config. Output counts "
        "are not verified as thinking-inclusive; reasoning tokens are not added again. "
        "Overall tokens sum six strata; latency weights stratum means equally. Model tokenizers "
        "and recorded workloads differ. Rankings and Chosen 03 are unchanged."
    )
    description = (
        token_description
        if output_tokens
        else "X = reference hosted-API token-cost estimate; Y = selected-cohort mixed rank; "
        "bubble area = observed latency (larger means slower). Only models with a verified "
        "reference quote and latency are plotted. Cost is hypothetical hosted repricing; "
        "latency is from the original deployment, not that hosted quote. No absent price is zero."
    )
    lines = [
        "",
        f"# {title_label} (Latency Bubbles)"
        if output_tokens
        else f"## Chosen {number}: {title_label} (Latency Bubbles)",
        "",
        description,
        "",
        "[Token counts, ranks, latencies and default-thinking provenance]"
        "(../../tables/output_tokens_rank_latency.csv)"
        if output_tokens
        else "[Bubble coordinates, sizes, pricing and timing provenance]"
        "(../../tables/chosen_03_cost_rank_latency.csv)",
        "",
    ]
    if output_tokens:
        lines += ["### Default-Thinking Sources (Checked 2026-11-04)", ""]
        lines += [
            f"- [{LABELS[run]}]({details['source_url']}): {details['evidence']}"
            for run, details in DEFAULT_THINKING_MODELS.items()
        ]
        lines += ["", "### Figures", ""]
    for relative in sorted(saved, key=lambda name: (not name.endswith("_overall"), name)):
        target = (
            Path(relative).relative_to("output_tokens" if output_tokens else "chosen").as_posix()
        )
        lines.append(f"- {target}: [PNG]({target}.png) | [PDF]({target}.pdf)")
    if output_tokens:
        index.write_text("\n".join(lines).lstrip() + "\n", encoding="utf-8")
        chosen_index = output / "figures" / "chosen" / "README.md"
        if chosen_index.exists():
            existing = chosen_index.read_text(encoding="utf-8")
            before, marker, after = existing.partition("\n## Chosen 05:")
            if marker:
                following = after.find("\n## Chosen ")
                suffix = after[following:] if following >= 0 else ""
                chosen_index.write_text(before.rstrip() + "\n" + suffix, encoding="utf-8")
        return saved
    existing = index.read_text(encoding="utf-8") if index.exists() else "# Chosen Figures\n"
    before, marker, after = existing.partition(f"\n## Chosen {number}:")
    following = after.find("\n## Chosen ") if marker else -1
    suffix = after[following:] if following >= 0 else ""
    index.write_text(before.rstrip() + "\n".join(lines) + "\n" + suffix, encoding="utf-8")
    return saved


def write_efficiency_figures(output, rows):
    import matplotlib.pyplot as plt
    from adjustText import adjust_text

    grouped = defaultdict(list)
    for row in rows:
        grouped[(row["view"], row["scope"], row["dataset"], row["setting"])].append(row)
    available = [row["mean_latency_s"] for row in rows if row["mean_latency_s"] is not None]
    if not available:
        return []
    saved = []
    colors = {run: plt.get_cmap("tab10")(index) for index, run in enumerate(LABELS)}
    for (view, scope, dataset, setting), members in grouped.items():
        plotted = sorted(
            [row for row in members if row["mean_latency_s"] is not None],
            key=lambda row: (row["mixed_rank"], row["run"]),
        )
        if not plotted:
            continue
        figure, axis = plt.subplots(figsize=(13, 8))
        texts = []
        for row in plotted:
            axis.scatter(
                row["mean_latency_s"],
                row["mixed_rank"],
                s=95,
                color=colors[row["run"]],
                edgecolor="white",
                linewidth=0.8,
                zorder=3,
            )
            texts.append(
                axis.text(
                    row["mean_latency_s"],
                    row["mixed_rank"],
                    row["model"],
                    ha="left",
                    va="center",
                    fontsize=8.5,
                    color=colors[row["run"]],
                )
            )
        axis.set_xlim(0, max(available) * 1.12)
        axis.set_ylim(len(LABELS) + 0.6, 0.4)
        axis.set_yticks(range(1, len(LABELS) + 1))
        axis.set_xlabel("Observed mean translation request latency (seconds; lower is better)")
        axis.set_ylabel("Balanced mixed rank (1 = best)")
        axis.grid(color="#e4e8e5", linewidth=0.7)
        axis.set_axisbelow(True)
        title = (
            "All three datasets | Zero-shot + Few-shot"
            if scope == "overall"
            else (f"{DATASETS[dataset]} | {setting.replace('_', ' ').title()}")
        )
        figure.suptitle("Chosen 02 | Observed Latency vs Mixed Rank", fontsize=19, y=0.97)
        figure.text(0.53, 0.90, f"{title} | {view}", ha="center", fontsize=12)
        figure.subplots_adjust(left=0.085, right=0.97, top=0.84, bottom=0.24)
        adjust_text(
            texts,
            x=[row["mean_latency_s"] for row in plotted],
            y=[row["mixed_rank"] for row in plotted],
            target_x=[row["mean_latency_s"] for row in plotted],
            target_y=[row["mixed_rank"] for row in plotted],
            ax=axis,
            expand=(1.12, 1.25),
            force_text=(0.2, 0.3),
            force_static=(0.2, 0.3),
            force_pull=(0.02, 0.02),
            iter_lim=400,
            min_arrow_len=5,
            arrowprops={"arrowstyle": "-", "color": "#83908b", "lw": 0.6},
        )
        figure.text(
            0.5,
            0.055,
            "Upper-left is preferable. X: recorded generation latency, not evaluator time. "
            "Overall means weight the six dataset/prompt strata equally.\n"
            "Observed deployments differ in hardware, serving/API setup, concurrency "
            "and workloads; "
            "this is not a hardware-controlled speed comparison.\n"
            "Timing uses all recorded timed requests; quality uses metric-specific scored support "
            "and is not proven row-matched to timing. No monetary cost inferred.",
            ha="center",
            fontsize=9,
            linespacing=1.6,
        )
        stem = "overall" if scope == "overall" else f"{dataset}_{setting}"
        relative = f"chosen/02_latency_vs_mixed_rank/{view}/chosen_02_latency_vs_mixed_rank_{stem}"
        for extension in ("png", "pdf"):
            path = output / "figures" / f"{relative}.{extension}"
            path.parent.mkdir(parents=True, exist_ok=True)
            figure.savefig(path, dpi=180, bbox_inches="tight")
        plt.close(figure)
        saved.append(relative)
    index = output / "figures" / "chosen" / "README.md"
    lines = [
        "",
        "## Chosen 02: Observed Latency vs Mixed Rank",
        "",
        "Measured translation-request latency, not evaluator runtime or monetary cost. "
        "Deployments and timing/quality populations are not controlled or proven row-matched.",
        "",
    ]
    for relative in sorted(saved, key=lambda name: (not name.endswith("_overall"), name)):
        target = Path(relative).relative_to("chosen").as_posix()
        lines.append(f"- {target}: [PNG]({target}.png) | [PDF]({target}.pdf)")
    existing = index.read_text(encoding="utf-8").split("\n## Chosen 02:", 1)[0]
    index.write_text(existing + "\n".join(lines) + "\n", encoding="utf-8")
    return saved


def write_rank_statistic_reports(output, aggregates, points, runs):
    saved = []
    for statistic in ("median", "top"):
        selected = build_statistic_aggregates(aggregates, points, statistic)
        ranked, components = build_mixed_rank_rows(selected, runs)
        for row in ranked:
            row["statistic"] = f"direction_{statistic}"
        write_tables(output, selected, statistic=statistic)
        folder = output / "tables/rankings" / statistic
        write_csv(folder / "metric_scores.csv", selected)
        write_csv(folder / "model_ranks.csv", ranked)
        write_csv(folder / "rank_components.csv", components)
        groups = defaultdict(list)
        for row in ranked:
            groups[(row["view"], row["scope"], row["dataset"], row["setting"])].append(row)
        overall_note = (
            "medians, not a pooled median"
            if statistic == "median"
            else "maxima, not a global maximum"
        )
        lines = [
            f"# {'Median' if statistic == 'median' else 'Highest-Score'} Model Rankings",
            "",
            "For each metric, dataset, prompt and annotation group, summarize each model's "
            "shared direction scores using the "
            f"{'median' if statistic == 'median' else 'maximum'}. "
            "Rank models descending on those native metric values. Metric ties receive average "
            "ranks. Balance metrics within families, terminology groups equally, and semantic / "
            "lexical / terminology families equally. Lower mixed mean rank is better; final ties "
            "share the minimum rank (1, 1, 3).",
            "",
            "Overall rankings average the dataset/prompt family ranks equally; they do not "
            "rerank a pooled statistic. Overall displayed metric cells average the stratum "
            f"{overall_note}. "
            "NA metrics are omitted for every model, never scored zero. Partial model support "
            "is rejected. Original mean-based rankings and plots are unchanged.",
            "",
            "Top means the best observed direction aggregate, not the best single translation, "
            "best model, upper confidence bound or typical performance. Different metric maxima "
            "can come from different directions. CSVs preserve supports and winning directions. "
            "These are descriptive rankings, not significance claims.",
            "",
            "[Native metric tables](performance.md) | [Metric scores](metric_scores.csv) | "
            "[Model ranks](model_ranks.csv) | [Rank components](rank_components.csv)",
            "",
        ]
        for (view, scope, dataset, setting), members in sorted(
            groups.items(), key=lambda item: (item[0][1] != "overall", item[0])
        ):
            title = (
                "Overall: all datasets and both prompts"
                if scope == "overall"
                else (f"{DATASETS[dataset]} | {setting.replace('_', ' ').title()}")
            )
            lines += [
                f"## {title} | {view}",
                "",
                "| Rank | Model | Mixed Mean Rank | Semantic | Lexical | Terminology |",
                "| --- | --- | --- | --- | --- | --- |",
            ]
            for row in sorted(members, key=lambda row: (row["mixed_rank"], row["run"])):
                lines.append(
                    f"| {row['mixed_rank']} | {row['model']} | {row['mixed_mean_rank']:.3f} | "
                    f"{row['semantic_mean_rank']:.3f} | {row['lexical_mean_rank']:.3f} | "
                    f"{row['terminology_mean_rank']:.3f} |"
                )
            stem = "overall" if scope == "overall" else f"{dataset}_{setting}"
            figure = f"../../../figures/rankings/{statistic}/{view}/rankings_{statistic}_{stem}"
            lines += ["", f"Scorecard: [PNG]({figure}.png) | [PDF]({figure}.pdf)", ""]
        (folder / "rankings.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
        saved.extend(write_chosen_rank_figures(output, ranked, statistic=statistic))
    lines = [
        "# Median and Highest-Score Model Rankings",
        "",
        "Alternative direction-level summaries with the original balanced metric-family weights. "
        "They supplement, rather than replace, the mean-based Chosen 01 scorecards.",
        "",
        "- [Median-based rankings](rankings/median/rankings.md)",
        "- [Highest-score rankings](rankings/top/rankings.md)",
        "",
    ]
    (output / "tables/ranking_statistics.md").write_text("\n".join(lines), encoding="utf-8")
    return saved


def write_language_rank_reports(output, points, runs):
    ranked, components, native, support = build_language_mixed_rank_rows(points, runs)
    folder = output / "tables/language_rankings"
    folder.mkdir(parents=True, exist_ok=True)

    def language_record(row):
        language = row.get("language", row.get("run"))
        return {
            **{key: value for key, value in row.items() if key not in ("run", "model")},
            "language": language,
            "language_name": LANGUAGE_LABELS.get(language, language),
        }

    for name, rows in (
        ("language_ranks", ranked),
        ("metric_rank_components", components),
        ("native_metric_scores", native),
        ("coverage", support),
    ):
        write_csv(folder / f"{name}.csv", [language_record(row) for row in rows])
    saved = []
    for statistic in ("median", "top"):
        for role in ("from", "to"):
            selected = [
                row for row in ranked if row["statistic"] == statistic and row["role"] == role
            ]
            lines = [
                f"# Balanced {role.title()}-Language Rankings: "
                f"{'Median Across Models' if statistic == 'median' else 'Best Model'}",
                "",
                "Rows rank languages, NOT models. From means translating out of a language; "
                "To means translating into it. For each metric/dataset/prompt, average supported "
                "partner-direction scores equally within each model. Then use the "
                f"{'median across models' if statistic == 'median' else 'highest model mean'} "
                "as that language's native metric value. Top does not choose a different model "
                "for each direction. The best model may differ between metrics and strata.",
                "",
                "Rank languages descending within each metric with average ties. Balance metrics "
                "within semantic and lexical families; balance terminology metrics within each "
                "term group and the three groups equally. The three family ranks have equal "
                "one-third weights. Final ties share the minimum rank (1, 1, 3).",
                "",
                "Overall rankings require every dataset, both prompts and every active metric "
                "for each language. Within that overall eligible language cohort, rerank each "
                "stratum's metric values, then average dataset/prompt family ranks equally. "
                "Displayed overall native cells are equal-stratum means, not pooled medians or "
                "global maxima. Dataset-specific cohorts may differ. All-NA metrics are omitted, "
                "never scored zero. Coverage CSV records excluded languages "
                "and missing components.",
                "",
                "Partner populations can differ between languages. These are descriptive "
                "supported benchmark rankings, not matched-partner comparisons, "
                "intrinsic language difficulty "
                "or statistical significance. Original model scorecards are unchanged.",
                "",
                "[Language ranks](language_ranks.csv) | "
                "[Metric ranks](metric_rank_components.csv) | "
                "[Native scores and model values](native_metric_scores.csv) | "
                "[Coverage](coverage.csv)",
                "",
            ]
            groups = defaultdict(list)
            for row in selected:
                groups[(row["view"], row["scope"], row["dataset"], row["setting"])].append(row)
            for (view, scope, dataset, setting), members in sorted(
                groups.items(), key=lambda item: (item[0][1] != "overall", item[0])
            ):
                title = (
                    "Overall: all datasets and both prompts"
                    if scope == "overall"
                    else (f"{DATASETS[dataset]} | {setting.replace('_', ' ').title()}")
                )
                lines += [
                    f"## {title} | {view}",
                    "",
                    "| Rank | Language | Mixed Mean Rank | Semantic | Lexical | Terminology |",
                    "| --- | --- | --- | --- | --- | --- |",
                ]
                for row in sorted(members, key=lambda row: (row["mixed_rank"], row["language"])):
                    lines.append(
                        f"| {row['mixed_rank']} | {row['language_name']} | "
                        f"{row['mixed_mean_rank']:.3f} | "
                        f"{row['semantic_mean_rank']:.3f} | {row['lexical_mean_rank']:.3f} | "
                        f"{row['terminology_mean_rank']:.3f} |"
                    )
                stem = "overall" if scope == "overall" else f"{dataset}_{setting}"
                figure = (f"../../figures/languages/rankings/{statistic}/{role}/{view}/"
                          f"language_rankings_{stem}")
                lines += ["", f"Scorecard: [PNG]({figure}.png) | [PDF]({figure}.pdf)", ""]
                missing = [
                    row["language"]
                    for row in support
                    if row["view"] == view
                    and row["statistic"] == statistic
                    and row["role"] == role
                    and row["scope"] == scope
                    and row["dataset"] == dataset
                    and row["state"] != "completed"
                ]
                if missing:
                    lines += [
                        "Unranked due to incomplete metric/dataset coverage: "
                        + ", ".join(LANGUAGE_LABELS.get(code, code) for code in sorted(missing))
                        + ".",
                        "",
                    ]
            (folder / f"{statistic}_{role}.md").write_text(
                "\n".join(lines) + "\n", encoding="utf-8"
            )
            saved.extend(
                write_chosen_rank_figures(output, selected, statistic=statistic, language_role=role)
            )
    lines = [
        "# Balanced Language Ranking Scorecards",
        "",
        "Chosen-style semantic / lexical / terminology ranking of languages, with equal "
        "family weights. Median and best-model summaries are separate, as are From and To roles.",
        "",
        "- [Median: from languages](median_from.md)",
        "- [Median: to languages](median_to.md)",
        "- [Best model: from languages](top_from.md)",
        "- [Best model: to languages](top_to.md)",
        "",
    ]
    (folder / "README.md").write_text("\n".join(lines), encoding="utf-8")
    index = output / "figures/languages/README.md"
    link = (
        "[Balanced language median/best-model scorecards](../../tables/language_rankings/README.md)"
    )
    if index.exists() and link not in index.read_text(encoding="utf-8"):
        index.write_text(
            index.read_text(encoding="utf-8").rstrip()
            + "\n\n## Balanced Language Rankings\n\n"
            + link
            + "\n",
            encoding="utf-8",
        )
    return saved


def write_chosen_rank_figures(output, rows, *, statistic=None, language_role=None):
    import matplotlib.pyplot as plt
    import numpy as np
    from matplotlib.colors import LinearSegmentedColormap

    colors = {
        "mixed": "#303735",
        "semantic": "#167d8d",
        "lexical": "#9b7915",
        "terminology": "#ba4934",
    }
    term_labels = {
        "target_term_coverage": "Coverage",
        "variant_aware_target_term_coverage": "Variant coverage",
        "term_bertscore_recall": "Term BERTScore",
        "terminology_success_rate": "Success rate",
        "variant_aware_terminology_success_rate": "Variant success",
    }
    category_labels = {
        "all_terms": "All",
        "externally_verified": "External",
        "llm_enriched": "LLM-enriched",
    }
    grouped = defaultdict(list)
    for row in rows:
        grouped[(row["view"], row["scope"], row["dataset"], row["setting"])].append(row)
    saved = []
    for (view, scope, dataset, setting), members in grouped.items():
        members = sorted(members, key=lambda row: (row["mixed_rank"], row["run"]))
        columns = [("mixed", "mixed_rank", "Mixed rank", "rank")]
        for family, metrics in RANK_FAMILIES.items():
            columns.append((family, f"{family}_mean_rank", "Mean rank", "family"))
            categories = CATEGORIES if family == "terminology" else ("not_applicable",)
            for category in categories:
                for metric in metrics:
                    key = f"{category}.{metric}"
                    if key not in members[0]:
                        continue
                    label = (
                        f"{category_labels[category]}: {term_labels[metric]}"
                        if family == "terminology"
                        else METRIC_LABELS[metric]
                    )
                    columns.append((family, key, label, metric))
        pixels = np.ones((len(members), len(columns), 4))
        labels = []
        for row_index, row in enumerate(members):
            cell_labels = []
            for column_index, (family, key, _, kind) in enumerate(columns):
                value = row[key]
                if kind == "rank":
                    rank = row["mixed_mean_rank"]
                    text = f"{value}\n({rank:.2f})"
                elif kind == "family":
                    rank = value
                    text = f"{value:.2f}"
                else:
                    rank = row[f"{key}.rank"]
                    digits = (
                        2
                        if kind in CORPUS
                        or (family == "terminology" and kind != "term_bertscore_recall")
                        else 3
                    )
                    text = f"{value:.{digits}f}"
                strength = (len(members) - rank) / max(1, len(members) - 1)
                palette = LinearSegmentedColormap.from_list("family", ["#ffffff", colors[family]])
                pixels[row_index, column_index] = palette(float(np.clip(strength, 0, 1)))
                cell_labels.append(text)
            labels.append(cell_labels)
        figure, axis = plt.subplots(figsize=(32, 10))
        axis.imshow(pixels, aspect="auto")
        for row_index in range(len(members)):
            for column_index, (_, _, _, kind) in enumerate(columns):
                rgb = pixels[row_index, column_index, :3]
                luminance = np.dot(rgb, [0.2126, 0.7152, 0.0722])
                axis.text(
                    column_index,
                    row_index,
                    labels[row_index][column_index],
                    ha="center",
                    va="center",
                    fontsize=12 if kind == "rank" else 10,
                    fontweight="bold" if kind in {"rank", "family"} else "normal",
                    color="white" if luminance < 0.48 else "#202a27",
                )
        axis.set_xticks(
            range(len(columns)),
            [column[2] for column in columns],
            rotation=50,
            ha="right",
            fontsize=10,
        )
        axis.set_yticks(range(len(members)), [row["model"] for row in members], fontsize=12)
        for family in colors:
            indices = [index for index, column in enumerate(columns) if column[0] == family]
            axis.text(
                mean(indices),
                1.055,
                "Mixed rank" if family == "mixed" else f"{family.title()} | 1/3 weight",
                transform=axis.get_xaxis_transform(),
                ha="center",
                va="bottom",
                fontsize=14,
                fontweight="bold",
                color=colors[family],
            )
            if indices[0] > 0:
                axis.axvline(indices[0] - 0.5, color="white", linewidth=5)
        axis.set_xticks(np.arange(-0.5, len(columns)), minor=True)
        axis.set_yticks(np.arange(-0.5, len(members)), minor=True)
        axis.grid(which="minor", color="#ffffff", linewidth=0.6)
        axis.tick_params(which="both", length=0)
        title = (
            "All three datasets | Zero-shot + Few-shot"
            if scope == "overall"
            else (f"{DATASETS[dataset]} | {setting.replace('_', ' ').title()}")
        )
        figure.suptitle(
            "Chosen 01 | Balanced Mixed-Rank Scorecard"
            if statistic is None
            else f"{'Median' if statistic == 'median' else 'Highest-Score'} | "
            "Balanced Model Rankings",
            fontsize=24,
            y=0.97,
        )
        if language_role is not None:
            figure.suptitle(
                f"Balanced {language_role.title()}-Language Rankings | "
                f"{'Median Across Models' if statistic == 'median' else 'Best Model'}",
                fontsize=24,
                y=0.97,
            )
        figure.text(0.55, 0.905, f"{title} | Annotation view: {view}", ha="center", fontsize=15)
        figure.subplots_adjust(left=0.10, right=0.99, top=0.79, bottom=0.34)
        aggregation = (
            "Overall: equal weight to each dataset and prompt; metric cells average six "
            "direction-macro scores. Colors use mean per-stratum metric ranks."
            if scope == "overall"
            else "Metric cells: native-scale direction-macro scores. "
            "Colors use within-metric model ranks."
        )
        if statistic is not None:
            description = "median" if statistic == "median" else "maximum"
            aggregation = (
                f"Overall: equal dataset/prompt weights. Cells average stratum {description} "
                f"scores, NOT a pooled {description}; colors use mean per-stratum metric ranks."
                if scope == "overall"
                else f"Metric cells: {description} native score across shared language directions, "
                "NOT individual translations. Colors use within-metric model ranks."
            )
        if language_role is not None:
            description = "median across models" if statistic == "median" else "best model mean"
            aggregation = f"Cells: {description} of per-model partner-direction means. " + (
                "Overall averages stratum values and family ranks equally, using the "
                "complete-coverage language cohort."
                if scope == "overall"
                else "Colors encode metric ranks across eligible languages, not models."
            )
        cohort_note = (
            "Languages ranked; partner sets may differ. Incomplete coverage is excluded, "
            "never scored zero. "
            if language_role is not None
            else "Selected current models; metric-specific shared directions, "
            "not proven identical rows. "
        )
        figure.text(
            0.55,
            0.045,
            "Mixed rank: rank of the equally weighted semantic, lexical and terminology "
            "mean ranks. "
            "Parentheses show the mixed mean rank; lower ranks are better.\n"
            "Within each family, metrics have equal weight; terminology first balances "
            "all / external / LLM-enriched groups equally. "
            "Tied metric scores receive average ranks.\n"
            f"{aggregation}\n"
            f"{cohort_note}"
            "All-NA metrics omitted. Descriptive chosen weights, "
            "not a significance or human-validity claim.",
            ha="center",
            fontsize=11,
            linespacing=1.6,
        )
        stem = "overall" if scope == "overall" else f"{dataset}_{setting}"
        relative = f"chosen/01_balanced_mixed_rank/{view}/chosen_01_balanced_mixed_rank_{stem}"
        if statistic is not None:
            relative = f"rankings/{statistic}/{view}/rankings_{statistic}_{stem}"
        if language_role is not None:
            relative = (
                f"languages/rankings/{statistic}/{language_role}/{view}/language_rankings_{stem}"
            )
        for extension in ("png", "pdf"):
            path = output / "figures" / f"{relative}.{extension}"
            path.parent.mkdir(parents=True, exist_ok=True)
            figure.savefig(path, dpi=180, bbox_inches="tight")
        plt.close(figure)
        saved.append(relative)
    if statistic is not None:
        return saved
    chosen = output / "figures" / "chosen"
    lines = [
        "# Chosen Figures",
        "",
        "## Chosen 01: Balanced Mixed-Rank Scorecard",
        "",
        "Equal weights: semantic, lexical, terminology (one third each). "
        "Terminology averages the three term groups equally before entering the mixed rank. "
        "These are descriptive reporting weights, not learned or human-validated weights.",
        "",
        "Start with the overall scorecards; detailed versions retain each dataset/prompt.",
        "",
    ]
    for relative in sorted(saved, key=lambda name: (not name.endswith("_overall"), name)):
        target = Path(relative).relative_to("chosen").as_posix()
        lines.append(f"- {target}: [PNG]({target}.png) | [PDF]({target}.pdf)")
    (chosen / "README.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return saved


def write_readme(output, figures):
    lines = [
        "# Benchmark Tables and Figures",
        "",
        "Generated locally from all 84 checksum-verified grouped summaries. "
        "No models or metrics were rerun.",
        "",
        "Analysis cohort: Gemma, GPT-6 Luna, Granite, Muse, Nemotron, Qwen and Tiny Aya Global. "
        "Tiny Aya Earth/Fire/Water are excluded. Both es-de and de-es are excluded only from "
        "Google Patents before recomputing support, scores, ranks, correlations and plots. "
        "Original checksum-pinned summaries remain unchanged.",
        "",
        "Observed latency, token totals and estimated token costs describe the original "
        "generation workloads, which may include the excluded patent directions. They were "
        "not remeasured or reduced by an unsupported per-direction subtraction. Quality "
        "ranks use the filtered seven-model/direction cohort.",
        "",
        "Tables and CSVs retain all 14 metric slots: nine general and five terminology metrics. "
        "Twelve have numeric results. Both terminology-success-rate metrics are marked "
        "`not_applicable` in every current-run direction group because their native "
        "source/reference applicability rules select no eligible rows. Their scores and "
        "correlations are NA, not zero. Figures omit success-rate metrics when all their "
        "displayed scores or correlations are unavailable.",
        "",
        "## Tables",
        "",
        *(
            ["- [Pair, source-language and target-language violins](figures/languages/violins.md)"]
            if (output / "figures/languages/violins.md").exists()
            else []
        ),
        *(
            [
                "- [Best-model, best/median and hardest-pair analysis]"
                "(figures/languages/best_performance.md)"
            ]
            if (output / "figures/languages/best_performance.md").exists()
            else []
        ),
        *(
            [
                "- [Language figures and methodology](figures/languages/README.md)",
                "- [Translation-from language rankings](language_rankings_from.md)",
                "- [Translation-to language rankings](language_rankings_to.md)",
            ]
            if (output / "figures/languages/README.md").exists()
            else []
        ),
        *(
            [
                "- [Output tokens, ranks, latencies and default-thinking evidence]"
                "(tables/output_tokens_rank_latency.csv)"
            ]
            if (output / "tables" / "output_tokens_rank_latency.csv").exists()
            else []
        ),
        *(
            ["- [Chosen 03 cost/rank/latency bubble data](tables/chosen_03_cost_rank_latency.csv)"]
            if (output / "tables" / "chosen_03_cost_rank_latency.csv").exists()
            else []
        ),
        *(
            ["- [API cost estimates and pricing assumptions](api_cost_estimates.md)"]
            if (output / "api_cost_estimates.md").exists()
            else []
        ),
        "- [Readable performance tables](tables/performance.md)",
        *(
            ["- [Balanced language median/best-model rankings](tables/language_rankings/README.md)"]
            if (output / "tables/language_rankings/README.md").exists()
            else []
        ),
        *(
            ["- [Median and highest-score model rankings](tables/ranking_statistics.md)"]
            if (output / "tables/ranking_statistics.md").exists()
            else []
        ),
        "- [LaTeX table fragments](tables/performance.tex) (requires `graphicx`)",
        "- [Translation-quality data](tables/translation_quality.csv)",
        "- [Terminology data](tables/terminology.csv)",
        "- [All direction-level scores](tables/direction_scores.csv), "
        "including historical/native populations",
        "- [Coverage](tables/coverage.csv)",
        "- [Model provenance and source links](tables/model_provenance.csv)",
        "- [Bubble-chart coordinates, sizes, and denominators](tables/bubble_chart_data.csv)",
        "- [Distribution points and scored-row counts](tables/distribution_points.csv)",
        "- [Density-fit sample sizes and status](tables/distribution_regions.csv)",
        "- [All metric correlations and pair-specific supports](tables/metric_correlations.csv)",
        *(
            ["- [Paired violin direction-level scores](tables/prompting_violin_points.csv)"]
            if (output / "tables" / "prompting_violin_points.csv").exists()
            else []
        ),
        *(
            [
                "- [Normalized violin scores and panel bounds]"
                "(tables/prompting_violin_normalized_points.csv)"
            ]
            if (output / "tables" / "prompting_violin_normalized_points.csv").exists()
            else []
        ),
        *(
            ["- [Four least-redundant metric columns](tables/selected_metric_columns.csv)"]
            if (output / "tables" / "selected_metric_columns.csv").exists()
            else []
        ),
        "- [Chosen 01 mixed ranks and displayed scores](tables/chosen_01_mixed_ranks.csv)",
        "- [Chosen 01 per-metric rank contributions and support]"
        "(tables/chosen_01_rank_components.csv)",
        *(
            [
                "- [Chosen 02 latency, mixed ranks and timing support]"
                "(tables/chosen_02_latency_data.csv)"
            ]
            if (output / "tables" / "chosen_02_latency_data.csv").exists()
            else []
        ),
        "",
        "## Figures",
        "",
    ]
    figure_types = {
        "languages": "Language Performance: Native Metrics, Balanced Scores and Pair Correlations",
        "chosen": "Chosen Figures",
        "output_tokens": "Output Tokens vs Rank and Latency",
        "all_metrics": "All Model Scores on Every Metric",
        "correlations": "Metric Correlations Within and Across Term Groups",
        "translation_quality": "Translation Quality",
        "terminology": "Terminology Metrics",
        "bubbles": "Quality-versus-Terminology Bubble Charts",
        "distributions": "Distributions Across Language Directions",
        "prompting": "Prompting Comparisons",
        "coverage": "Coverage",
    }
    term_types = {
        "overview": "All Three Term Types Together",
        "all_terms": "All Terms",
        "externally_verified": "Externally Verified Terms",
        "llm_enriched": "LLM-Enriched Terms (Final Refined Group)",
    }
    for group, title in figure_types.items():
        selected = [name for name in figures if Path(name).parts[0] == group]
        lines += [f"### {title}", ""]
        subsets = term_types if group in {"terminology", "bubbles"} else {None: None}
        for subset, subset_title in subsets.items():
            members = [name for name in selected if subset is None or Path(name).parts[1] == subset]
            if not members:
                continue
            if subset_title:
                lines += [f"#### {subset_title}", ""]
            for name in members:
                parts = Path(name).parts
                label = Path(name).name.replace("_", " ").title()
                if group == "bubbles":
                    label = f"{parts[2]}: {label}"
                elif group in {"distributions", "correlations"}:
                    label = f"{parts[-2]}: {label}"
                elif group == "all_metrics":
                    label = f"{' / '.join(parts[1:-1])}: {label}"
                elif group == "chosen":
                    label = f"{parts[2]}: {label}"
                elif group == "prompting" and len(parts) > 2:
                    label = f"{parts[2]}: {label}"
                lines.append(f"- {label}: [PNG](figures/{name}.png) | [PDF](figures/{name}.pdf)")
            lines.append("")
    selection_path = output / "tables" / "selected_metric_columns.csv"
    if selection_path.exists():
        with selection_path.open(encoding="utf-8", newline="") as handle:
            selected = list(csv.DictReader(handle))
        if selected:
            lines += [
                "## Four Least-Redundant Metric Columns",
                "",
                "Selected from equal-dataset, model-level correlations across all three datasets, "
                "both prompts and both annotation views. Minimize the mean absolute Pearson "
                "and Spearman coefficients of all six pairs; require four different metrics "
                "and complete support in every context. Ties minimize the maximum absolute "
                "coefficient, then use column names. No metric-family coverage constraint.",
                "",
                *[f"- {row['label']} ({row['category']})" for row in selected],
                "",
                "Mean absolute correlation: "
                f"{float(selected[0]['mean_absolute_correlation']):.4f}; "
                f"maximum: {float(selected[0]['max_absolute_correlation']):.4f}. "
                f"Searched {selected[0]['n_candidate_sets']} supported sets across "
                f"{selected[0]['n_contexts']} view/prompt/method contexts. These metrics remain "
                "correlated; this descriptive shortlist does not establish independence, "
                "metric validity, or coverage of every quality aspect. This shortlist does not "
                "determine the model rankings.",
                "",
            ]
    lines += [
        "",
        "## Interpretation",
        "",
        "- Output-token bubble plots (outside the chosen collection) use recorded output "
        "tokens on x (millions), selected-cohort mixed "
        "rank on y, and latency-proportional bubble area. Only models documented as thinking "
        "by default are plotted: GPT-6 Luna, Granite 4.2, Muse Glimmer, Nemotron 3.5 Lightning "
        "and Qwen3.8. This does not verify the benchmark run's thinking mode: in particular, "
        "a local GPT configuration disables thinking and is not confirmed as the downloaded "
        "run's config. Gemma defaults to thinking off; Tiny Aya lacks verified default-thinking "
        "evidence. Output totals are NOT verified thinking-inclusive counts; reported reasoning "
        "tokens are retained, never added again. Overall tokens sum six dataset/prompt strata, "
        "while latency averages their means equally. Ranks are not recomputed for the subset. "
        "Different tokenizers, workloads and deployments prevent a row-matched, equal-budget "
        "or hardware-controlled interpretation. All token plots share axis and area scales.",
        "- All-dataset correlations first compute pair-specific shared-direction means inside "
        "each dataset, then average the three dataset means equally per model before "
        "correlating the selected model scores. They are NOT averages of correlation coefficients "
        "or pooled model/dataset correlations. Both prompts/views remain separate. Every "
        "dataset must have common scored support; otherwise the pair is NA. CSV fields retain "
        "per-dataset direction lists and total dataset-direction support counts. Single-dataset "
        "coefficients use the original method. Four-metric plots show the same global shortlist "
        "for every all-dataset context.",
        "- Zoomed native-score violins adjust only each panel's y-axis range, using all "
        "observed scores across models and both prompts with 5% padding. Scores are NOT "
        "normalized or converted to 0-1. Zero is not forced into the range, no observations "
        "are clipped, and original zero-inclusive and normalized figures remain available.",
        "- New normalized violin figures are separate from the native-score violins. "
        "Within each dataset/view/term-group/metric panel, min-max bounds are shared across "
        "all selected models, both prompts and all observed directions. The transformation is "
        "(score - panel minimum) / (panel maximum - panel minimum); constant panels map to "
        "0.5. Zero and one denote observed panel endpoints, not absolute quality. Bounds "
        "differ between panels, so normalized magnitudes must not be compared across "
        "datasets, metrics, views or term groups. Raw scores and bounds are retained in a "
        "separate CSV. Normalization preserves within-panel ordering and paired differences "
        "up to a common scale factor; KDE bandwidth and direction-level interpretation "
        "are unchanged. The original native-score figures remain available.",
        "- Paired prompting violins retain the bar figures' models, metric panels, datasets, "
        "annotation views and colors. Each point is one direction-level corpus score or "
        "segment-score mean on the same metric-specific directions shared across all models "
        "and both prompts. Every direction contributes equally, not in proportion to its "
        "number of translations. Violin shapes use Scott-bandwidth KDE, clipped to the "
        "observed range; lines show medians. Groups with fewer than three points or constant "
        "scores show points/median only. These are distributions across language directions, "
        "NOT per-translation distributions, confidence intervals or independent samples. "
        "Bar means can differ from violin medians. All report plots use the selected cohort.",
        "- Prompting bar figures show one panel per available metric with models on x and "
        "native scores on y: zero-shot on the left, few-shot on the right. All panels use "
        "zero-inclusive axes, without normalization or pooling across datasets. General "
        "metrics have one nine-panel figure per dataset; terminology figures separate both "
        "annotation views and show all/external/LLM-enriched groups in distinct panels. "
        "Scores reuse the tables' metric-specific common direction support across all models "
        "and both prompts. NA bars are labeled, not assigned zero; universally unavailable "
        "success-rate metrics are omitted. No row-paired or significance claims are implied.",
        "- Chosen 03 uses reference estimated API cost on x, the selected-cohort mixed "
        "rank on y (rank 1 at the top), and bubble area proportional to observed latency "
        "(8 square points per second; larger means slower). Only verified priced models "
        "with measured latency are plotted; others remain in the bubble CSV as unpriced "
        "or missing, not zero cost. Rankings are not recomputed for the priced subset. "
        "Cost sums recorded token charges across strata; overall latency weights the six "
        "dataset/prompt means equally. Cost is hypothetical hosted-API token repricing "
        "without cache discount, while latency comes from the original local/API "
        "deployments, NOT the priced hosted endpoints. They are not a jointly measured "
        "price/speed trade-off, hardware-controlled benchmark or row-matched comparison. "
        "The CSV retains input/output cost, latency, bubble area and source references. "
        "All Chosen 03 figures share cost-axis and area scales.",
        "- Chosen 02 plots measured mean translation-request latency against Chosen 01 mixed "
        "rank (rank 1 at the top). Original translation summary downloads are opt-in through "
        "`uv run --no-sync python scripts/download_evaluation_summaries.py --translation-timing`. "
        "Their source URLs and checksums are recorded separately. Overall latency weights "
        "the same six dataset/prompt strata equally; counts are not used as stratum weights. "
        "Missing, nonpositive or nonfinite latency is omitted, never replaced by zero. "
        "The axes describe observed deployments: hardware, hosted/API setup, concurrency, "
        "prompt/output lengths and timing coverage differ. Timing covers all recorded timed "
        "requests and is not proven row-matched to quality-scored support. This is not a "
        "hardware-normalized speed or cost comparison. No monetary cost was inferred from "
        "tokens, evaluator runtime or model size. Annotation views reuse the same timings.",
        "- Chosen 01 ranks models by an equal-weight mean of three family mean ranks: "
        "semantic (BERTScore, BLEURT, COMET, COMETKiwi, XCOMET), lexical (BLEU, chrF, chrF++, "
        "sequence similarity), and terminology. Metric scores are ranked descending within "
        "each dataset/prompt with average ranks for ties. Terminology averages metric ranks "
        "within each term group, then equally averages all/external/LLM-enriched groups. "
        "All-NA metrics are omitted for every model, never assigned a zero rank; partial "
        "model support is rejected. Final rank ties share the minimum rank (1, 1, 3). "
        "Overall scorecards average six dataset/prompt family ranks equally; original metric "
        "cells show equal-stratum native-score means, not the basis for recomputing ranks. "
        "Rank columns and darker colors indicate better/lower ranks. The first column also "
        "shows the mixed mean rank in parentheses. Rankings depend on the selected model "
        "roster and chosen weights; they are descriptive, not evidence of significance. "
        "Exact metric values, metric ranks, direction supports and denominators are exported. "
        "Overall metric availability must be consistent across strata.",
        "- Main tables/figures include seven current run identifiers. "
        "Retained historical snapshots "
        "and the 60-row native sample remain in direction/coverage/provenance exports, "
        "not the main comparisons.",
        "- For each metric/dataset/annotation-view/subset, intersect scored directions across "
        "all selected runs AND both prompting settings. "
        "Average those directions with equal weight. "
        "Actual direction lists and scored/applicable row counts are retained in the CSV files.",
        "- BLEU/chrF/chrF++ cells average direction-level corpus scores; they are NOT pooled "
        "corpus scores. Learned/terminology cells average direction-level segment means. "
        "Do not mix these with sentence-weighted means.",
        "- Shared directions do not prove identical evaluation examples. Counts vary; true "
        "row-matched comparisons, confidence intervals, bootstrap significance, and causal "
        "prompting claims cannot be obtained from these summaries alone.",
        "- Terminology supports can differ by annotation source, subset, metric, and model. "
        "All/external/refined contrasts are descriptive, not a matched-row annotation ablation. "
        "NA means no common scored support, not zero accuracy. CSV files also retain available "
        "scored/applicable counts outside the shared-direction intersection.",
        "- General metric values were checked for equality across all six annotation tracks "
        "before exporting them once. Annotation views are not translation-model conditions.",
        "- All-metrics heatmaps annotate native-scale scores; color encodes within-metric model "
        "rank, not a common score scale. All nine general metrics are shown; terminology "
        "success-rate metrics are omitted when all displayed values are unavailable. "
        "Terminology includes all three term groups and both annotation views.",
        "- Correlation matrices start from nine general and 15 terminology variables "
        "(five metrics times three groups), omitting all-NA success-rate variables. "
        "Pearson measures linear association; Spearman "
        "measures model-rank association with average ranks for ties. Each observation is one "
        "current model's direction-macro score, not a translation or language direction. "
        "Datasets, prompts and annotation views are kept separate. For each metric pair, "
        "directions are intersected across all selected models, both prompts, both metrics, and "
        "all three terminology groups for any terminology metric involved. Thus cross-group "
        "coefficients use shared direction support. Different metric pairs can use different "
        "supports; these pairwise matrices need not be positive semidefinite. Exact supports "
        "are exported. Cells show recomputed coefficients to three decimals; colors use the "
        "same signed fourth-root distance-to-endpoint scale on [-1, 1] across all figures "
        "to expand differences near +/-1. Colorbar ticks remain actual coefficients; "
        "color distances are nonlinear and do not imply effect sizes or significance. The color "
        "transform does not change computed coefficients. Constant/unavailable scores give NA. "
        "No p-values or significance claims; "
        "the models are not independent random samples and identical rows are not established.",
        "- Score scales are unchanged. Coverage percentages use 0-100; learned scores use "
        "their native scales. XCOMET span counts are available in direction exports; "
        "no paid FSP-MQM judging was run. Learned-metric plot axes may be zoomed.",
        "- Display names are shortened artifact/model labels. Exact stored model identifiers, "
        "source URLs and evaluation signatures are in model_provenance.csv; release/checkpoint "
        "identity has not been independently certified.",
        "- Coverage counts describe stored translations. Reported expected/missing totals "
        "are preserved, including unknown native-sample totals, but are not an independent "
        "completeness audit.",
        "- Terminology figures are split into all terms, externally verified terms, and "
        "LLM-enriched terms (the final `refined` group, not raw LLM candidates). Each type "
        "has separate GLM/Luna figures showing coverage, variant-aware coverage, and term "
        "BERTScore recall across the three datasets. Overview figures compare all term types. "
        "Source-conditioned terminology success rates remain available in the tables.",
        "- Bubble charts use COMET on x, the selected term subset's target coverage on y, and area "
        "proportional to BLEU (36 square points per BLEU point; no min/max size remapping). "
        "All three metrics use the same direction intersection across selected models and both "
        "prompt settings within each view/subset. Supports may differ between view/subsets; "
        "metric-specific row denominators can still differ. All bubble charts share axis limits "
        "and size scaling; neither cost nor model size is implied.",
        "- Distribution plots compare all three term subsets on directions jointly supported "
        "by every current model, both prompt settings, and both plotted metrics within each "
        "dataset/annotation view. A point is one direction's equal-model average, not one "
        "translation. Each category therefore has the same direction count. COMET can be "
        "identical across categories for the same direction because translations are unchanged.",
        "- Shading is a descriptive 50% highest-density region of a 2D Gaussian KDE using "
        "Scott bandwidth, computed on the displayed grid. At least six nondegenerate direction "
        "points are required; otherwise only points are shown. Region-fit status and sample "
        "sizes are exported. These are not confidence regions or per-translation distributions; "
        "directions and model averages are not independent replicates. No uncertainty or "
        "significance claims follow from these plots.",
        "",
        "## Reproduce",
        "",
        "```powershell",
        "uv run --no-sync python scripts/render_evaluation_results.py",
        "```",
        "",
    ]
    (output / "README.md").write_text("\n".join(lines), encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(
        description="Render tables and figures from downloaded evaluation summaries."
    )
    parser.add_argument("--input", type=Path, default=Path("reports/evaluation-e452b88"))
    parser.add_argument("--output", type=Path, default=Path("reports/evaluation-e452b88/analysis"))
    parser.add_argument(
        "--api-costs-only",
        action="store_true",
        help="Reprice recorded tokens with the pinned API pricing snapshot.",
    )
    parser.add_argument(
        "--languages-only",
        action="store_true",
        help="Render language analysis from the existing native direction-point CSV only.",
    )
    parser.add_argument(
        "--best-languages-only",
        action="store_true",
        help="Render best-model, best/median and hardest-pair plots from native direction CSV.",
    )
    parser.add_argument(
        "--language-violins-only",
        action="store_true",
        help="Render pair/source/target language violins from native direction CSV only.",
    )
    parser.add_argument(
        "--pair-correlations-only",
        action="store_true",
        help="Replace model-pair plots with native direction correlations from existing scores.",
    )
    parser.add_argument(
        "--language-correlations-only",
        action="store_true",
        help="Render to-to, from-from and from-to language correlations from existing scores.",
    )
    parser.add_argument(
        "--combined-language-correlations-only",
        action="store_true",
        help="Render combined dataset/prompt language means, correlations and model scatter plots.",
    )
    parser.add_argument(
        "--ranking-statistics-only",
        action="store_true",
        help="Render median/top model ranking tables and scorecards from existing native scores.",
    )
    parser.add_argument(
        "--language-ranking-statistics-only",
        action="store_true",
        help="Render Chosen-style median/best-model language rankings for from/to roles.",
    )
    args = parser.parse_args()
    if args.language_ranking_statistics_only:
        import matplotlib

        matplotlib.use("Agg")
        path = args.output / "tables/prompting_violin_points.csv"
        if not path.exists():
            parser.error("Generate native direction scores before ranking languages")
        with path.open(encoding="utf-8", newline="") as handle:
            points = select_analysis_points(list(csv.DictReader(handle)))
        runs = sorted({row["run"] for row in points})
        if set(runs) != set(LABELS):
            parser.error("Language rankings require the selected model cohort")
        figures = write_language_rank_reports(args.output, points, runs)
        write_readme(
            args.output,
            sorted(
                path.relative_to(args.output / "figures").with_suffix("").as_posix()
                for path in (args.output / "figures").rglob("*.png")
            ),
        )
        print(
            f"Wrote {len(figures)} balanced language scorecards; "
            f"see {args.output / 'tables/language_rankings/README.md'}"
        )
        return
    if args.ranking_statistics_only:
        import matplotlib

        matplotlib.use("Agg")
        paths = [
            args.output / "tables" / name
            for name in (
                "translation_quality.csv",
                "terminology.csv",
                "prompting_violin_points.csv",
            )
        ]
        if not all(path.exists() for path in paths):
            parser.error("Generate native metric and direction scores before ranking statistics")
        data = []
        for path in paths:
            with path.open(encoding="utf-8", newline="") as handle:
                data.append(list(csv.DictReader(handle)))
        aggregates = data[0] + data[1]
        runs = sorted({row["run"] for row in aggregates})
        if set(runs) != set(LABELS):
            parser.error("Ranking statistics require the selected model cohort")
        figures = write_rank_statistic_reports(args.output, aggregates, data[2], runs)
        write_readme(
            args.output,
            sorted(
                path.relative_to(args.output / "figures").with_suffix("").as_posix()
                for path in (args.output / "figures").rglob("*.png")
            ),
        )
        print(
            f"Wrote {len(figures)} median/top ranking scorecards; "
            f"see {args.output / 'tables/ranking_statistics.md'}"
        )
        return
    if (
        args.pair_correlations_only
        or args.language_correlations_only
        or args.combined_language_correlations_only
    ):
        import matplotlib

        matplotlib.use("Agg")
        path = args.output / "tables/prompting_violin_points.csv"
        if not path.exists():
            parser.error("Generate native direction scores before rendering correlations")
        with path.open(encoding="utf-8", newline="") as handle:
            points = select_analysis_points(list(csv.DictReader(handle)))
        runs = sorted({row["run"] for row in points})
        writer = (
            write_language_correlations
            if args.language_correlations_only or args.combined_language_correlations_only
            else write_language_pair_correlations
        )
        figures = (
            writer(args.output, points, runs, combined=True)
            if args.combined_language_correlations_only
            else writer(args.output, points, runs)
        )
        write_readme(
            args.output,
            sorted(
                path.relative_to(args.output / "figures").with_suffix("").as_posix()
                for path in (args.output / "figures").rglob("*.png")
            ),
        )
        index_name = (
            "correlations_combined.md"
            if args.combined_language_correlations_only
            else "correlations.md"
            if args.language_correlations_only
            else "pair_correlations.md"
        )
        print(
            f"Wrote {len(figures)} correlation sets; "
            f"see {args.output / 'figures/languages' / index_name}"
        )
        return
    if args.language_violins_only:
        import matplotlib

        matplotlib.use("Agg")
        path = args.output / "tables/prompting_violin_points.csv"
        if not path.exists():
            parser.error("Generate native direction scores before rendering language violins")
        with path.open(encoding="utf-8", newline="") as handle:
            points = select_analysis_points(list(csv.DictReader(handle)))
        runs = sorted({row["run"] for row in points})
        figures = write_language_violin_figures(args.output, points, runs)
        write_readme(
            args.output,
            sorted(
                path.relative_to(args.output / "figures").with_suffix("").as_posix()
                for path in (args.output / "figures").rglob("*.png")
            ),
        )
        print(
            f"Wrote {len(figures)} language violin sets; "
            f"see {args.output / 'figures/languages/violins.md'}"
        )
        return
    if args.best_languages_only:
        import matplotlib

        matplotlib.use("Agg")
        path = args.output / "tables/prompting_violin_points.csv"
        if not path.exists():
            parser.error("Generate native direction scores before rendering best-language views")
        with path.open(encoding="utf-8", newline="") as handle:
            points = select_analysis_points(list(csv.DictReader(handle)))
        runs = sorted({row["run"] for row in points})
        figures = write_best_language_figures(args.output, points, runs)
        write_readme(
            args.output,
            sorted(
                path.relative_to(args.output / "figures").with_suffix("").as_posix()
                for path in (args.output / "figures").rglob("*.png")
            ),
        )
        print(
            f"Wrote {len(figures)} best-language figure sets; "
            f"see {args.output / 'figures/languages/best_performance.md'}"
        )
        return
    if args.languages_only:
        import matplotlib

        matplotlib.use("Agg")
        path = args.output / "tables" / "prompting_violin_points.csv"
        if not path.exists():
            parser.error("Generate native direction scores before rendering language analysis")
        with path.open(encoding="utf-8", newline="") as handle:
            points = select_analysis_points(list(csv.DictReader(handle)))
        runs = sorted({row["run"] for row in points})
        figures = write_language_analysis(args.output, points, runs)
        write_readme(
            args.output,
            sorted(
                path.relative_to(args.output / "figures").with_suffix("").as_posix()
                for path in (args.output / "figures").rglob("*.png")
            ),
        )
        print(
            f"Wrote {len(figures)} language figure sets and source/target ranking tables; "
            f"see {args.output / 'figures/languages/README.md'}"
        )
        return
    if args.api_costs_only:
        timings = load_translation_timings(args.input)
        if not timings:
            parser.error("Download translation timing summaries before estimating API costs")
        pricing = json.loads((args.input / "api_pricing_snapshot.json").read_text(encoding="utf-8"))
        args.output.mkdir(parents=True, exist_ok=True)
        (args.output / "tables").mkdir(exist_ok=True)
        rows = build_api_cost_rows(timings, pricing)
        write_api_cost_report(args.output, rows, pricing)
        figures = sorted(
            path.relative_to(args.output / "figures").with_suffix("").as_posix()
            for path in (args.output / "figures").rglob("*.png")
        )
        write_readme(args.output, figures)
        print(f"Wrote {len(rows)} API cost scenarios; see {args.output / 'api_cost_estimates.md'}")
        return
    summaries, details, coverage, provenance = load_summaries(args.input)
    aggregates, runs = build_aggregates(summaries)
    write_tables(args.output, aggregates)
    write_csv(args.output / "tables" / "direction_scores.csv", details)
    write_csv(args.output / "tables" / "coverage.csv", coverage)
    write_csv(args.output / "tables" / "model_provenance.csv", provenance)
    bubble_rows = [
        row
        for view in VIEWS
        for category in CATEGORIES
        for row in build_bubble_rows(summaries, runs, view=view, category=category)
    ]
    write_csv(args.output / "tables" / "bubble_chart_data.csv", bubble_rows)
    figures = write_figures(args.output, aggregates, coverage, runs, bubble_rows)
    distribution_rows = build_distribution_rows(summaries, runs)
    write_csv(args.output / "tables" / "distribution_points.csv", distribution_rows)
    figures += write_distribution_figures(args.output, distribution_rows)
    correlations = build_metric_correlations(summaries, runs)
    write_csv(args.output / "tables" / "metric_correlations.csv", correlations)
    distinct_columns = select_distinct_metric_columns(correlations)
    write_csv(args.output / "tables" / "selected_metric_columns.csv", distinct_columns)
    figures += write_complete_metric_figures(args.output, aggregates, runs, correlations)
    bar_figures = write_prompting_bar_figures(args.output, aggregates, runs)
    figures += bar_figures
    violin_rows = build_prompting_violin_rows(summaries, aggregates)
    write_csv(args.output / "tables" / "prompting_violin_points.csv", violin_rows)
    figures += write_prompting_violin_figures(args.output, aggregates, runs, violin_rows)
    zoomed_violin_figures = write_prompting_violin_figures(
        args.output, aggregates, runs, violin_rows, zoomed=True
    )
    figures += zoomed_violin_figures
    normalized_violin_rows = normalize_prompting_violin_rows(violin_rows)
    write_csv(
        args.output / "tables" / "prompting_violin_normalized_points.csv", normalized_violin_rows
    )
    figures += write_prompting_violin_figures(
        args.output, aggregates, runs, normalized_violin_rows, normalized=True
    )
    mixed_ranks, rank_components = build_mixed_rank_rows(aggregates, runs)
    write_csv(args.output / "tables" / "chosen_01_mixed_ranks.csv", mixed_ranks)
    write_csv(args.output / "tables" / "chosen_01_rank_components.csv", rank_components)
    figures += write_chosen_rank_figures(args.output, mixed_ranks)
    figures += write_rank_statistic_reports(args.output, aggregates, violin_rows, runs)
    translation_timings = load_translation_timings(args.input)
    if translation_timings:
        efficiency = build_efficiency_rows(mixed_ranks, translation_timings)
        write_csv(args.output / "tables" / "chosen_02_latency_data.csv", efficiency)
        figures += write_efficiency_figures(args.output, efficiency)
        pricing_path = args.input / "api_pricing_snapshot.json"
        if pricing_path.exists():
            pricing = json.loads(pricing_path.read_text(encoding="utf-8"))
            api_costs = build_api_cost_rows(translation_timings, pricing)
            write_api_cost_report(args.output, api_costs, pricing)
            cost_bubbles = build_cost_rank_bubble_rows(efficiency, api_costs)
            write_csv(args.output / "tables" / "chosen_03_cost_rank_latency.csv", cost_bubbles)
            figures += write_cost_rank_bubble_figures(args.output, cost_bubbles)
            figures += write_chosen_prompting_figures(args.output, bar_figures)
            if translation_timings:
                token_bubbles = build_output_token_rank_rows(efficiency, translation_timings)
                write_csv(
                    args.output / "tables" / "output_tokens_rank_latency.csv",
                    token_bubbles,
                )
                figures += write_output_token_rank_figures(args.output, token_bubbles)
    figures += write_chosen_prompting_figures(args.output, zoomed_violin_figures, zoomed=True)
    figures += write_language_analysis(args.output, violin_rows, runs)
    figures += write_best_language_figures(args.output, violin_rows, runs)
    figures += write_language_violin_figures(args.output, violin_rows, runs)
    write_readme(args.output, figures)
    print(
        f"Validated {len(summaries)} summaries; exported {len(details)} direction groups "
        f"and {len(aggregates)} aggregate metric rows for {len(runs)} current runs."
    )
    print(
        f"Wrote {len(figures)} figures in PNG and PDF, "
        f"with a linked README at {args.output / 'README.md'}"
    )


if __name__ == "__main__":
    main()
