import importlib.util
from pathlib import Path

import matplotlib
import pytest

matplotlib.use("Agg")

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "render_evaluation_results.py"
SPEC = importlib.util.spec_from_file_location("render_evaluation_results", SCRIPT)
renderer = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(renderer)


def result(value, rows=1):
    metrics = (*renderer.GENERAL, *renderer.TERMINOLOGY)
    return {
        "corpus_metrics": {metric: value for metric in renderer.CORPUS},
        "mean_metrics": {metric: value for metric in metrics},
        "metric_status": {
            metric: {"state": "completed", "rows_scored": rows, "rows_missing": 0}
            for metric in metrics
        },
    }


def test_direction_macro_is_not_sentence_weighted():
    groups = {"de-en": result(0, rows=1), "en-de": result(100, rows=99)}
    assert renderer.direction_macro(groups, "bleu", list(groups)) == 50


def test_bleu_uses_corpus_not_segment_mean():
    group = result(42)
    group["mean_metrics"]["bleu"] = 19
    assert renderer.metric_value(group, "bleu") == 42


@pytest.mark.parametrize("state", ["not_applicable", "not_run", "failed"])
def test_unavailable_metric_is_not_zero(state):
    group = result(0)
    group["metric_status"]["bleu"]["state"] = state
    assert renderer.metric_value(group, "bleu") is None


def test_partial_or_nonfinite_metric_is_not_complete():
    group = result(42)
    group["metric_status"]["bleu"]["rows_missing"] = 1
    assert renderer.metric_value(group, "bleu") is None
    group = result(float("nan"))
    assert renderer.metric_value(group, "bleu") is None


def test_empty_direction_support_is_not_zero():
    assert renderer.direction_macro({}, "bleu", []) is None


def test_common_support_intersects_models_and_prompt_settings():
    summaries = {}
    for view in renderer.VIEWS:
        for category in renderer.CATEGORIES:
            for run in renderer.LABELS:
                summaries[(view, category, run)] = {
                    "dataset_settings": {
                        dataset: {
                            setting: {"by_direction": {"de-en": result(20), "en-de": result(80)}}
                            for setting in renderer.SETTINGS
                        }
                        for dataset in renderer.DATASETS
                    }
                }
    first_run = next(iter(renderer.LABELS))
    del summaries[("original_glm", "all_terms", first_run)]["dataset_settings"]["google_patents"][
        "few_shot"
    ]["by_direction"]["de-en"]
    aggregates, runs = renderer.build_aggregates(summaries)
    selected = [
        row
        for row in aggregates
        if row["view"] == "shared_general" and row["dataset"] == "google_patents"
    ]
    assert len(runs) == len(renderer.LABELS)
    assert len(selected) == len(renderer.LABELS) * 2 * len(renderer.GENERAL)
    assert all(row["directions"] == "en-de" and row["value"] == 80 for row in selected)


def test_analysis_exclusions_keep_global_and_only_remove_patent_spanish_german():
    assert len(renderer.LABELS) == 7
    assert "tiny_aya_global" in renderer.LABELS
    assert renderer.EXCLUDED_RUNS.isdisjoint(renderer.LABELS)
    original = {
        "run": "tiny_aya_global",
        "dataset_settings": {
            dataset: {
                "zero_shot": {
                    "by_direction": {"de-es": result(99), "es-de": result(100), "en-de": result(40)}
                }
            }
            for dataset in renderer.DATASETS
        },
    }
    selected = renderer.select_analysis_summary(original)
    assert set(selected["dataset_settings"]["google_patents"]["zero_shot"]["by_direction"]) == {
        "en-de"
    }
    for dataset in ("jrc_articles", "jrc_definitions"):
        assert len(selected["dataset_settings"][dataset]["zero_shot"]["by_direction"]) == 3
    assert len(original["dataset_settings"]["google_patents"]["zero_shot"]["by_direction"]) == 3
    for run in renderer.EXCLUDED_RUNS:
        assert renderer.select_analysis_summary({**original, "run": run}) is None
        assert renderer.population(run + "__historical_untimed") == "excluded"
    points = [
        {"run": run, "dataset": dataset, "direction": direction}
        for run in (*renderer.LABELS, *renderer.EXCLUDED_RUNS)
        for dataset in renderer.DATASETS
        for direction in ("de-es", "es-de", "en-de")
    ]
    filtered = renderer.select_analysis_points(points)
    assert len(filtered) == 7 * 7
    assert all(row["run"] not in renderer.EXCLUDED_RUNS for row in filtered)


def language_points(monkeypatch):
    monkeypatch.setattr(renderer, "DATASETS", {"google_patents": "Chemical Patents"})
    monkeypatch.setattr(renderer, "VIEWS", ("luna",))
    monkeypatch.setattr(
        renderer,
        "RANK_FAMILIES",
        {
            "semantic": ("comet",),
            "lexical": ("bleu",),
            "terminology": ("target_term_coverage",),
        },
    )
    runs = list(renderer.LABELS)[:2]
    points = []
    for run_index, run in enumerate(runs):
        for family, metrics in renderer.RANK_FAMILIES.items():
            for category in renderer.CATEGORIES if family == "terminology" else ("not_applicable",):
                for metric in metrics:
                    for setting in renderer.SETTINGS:
                        for direction, value in (("en-de", 10), ("de-en", 0)):
                            points.append(
                                {
                                    "view": "luna" if family == "terminology" else "shared_general",
                                    "dataset": "google_patents",
                                    "category": category,
                                    "metric": metric,
                                    "run": run,
                                    "setting": setting,
                                    "direction": direction,
                                    "value": value + run_index * 1000,
                                    "rows_scored": 99 if direction == "de-en" else 1,
                                }
                            )
    return points, runs


def test_language_mixed_ranks_use_median_or_best_model_after_partner_means(tmp_path, monkeypatch):
    import csv

    import matplotlib.figure

    points, runs = language_points(monkeypatch)
    renderer.RANK_FAMILIES["terminology"] += ("terminology_success_rate",)
    points = [
        {**row, "value": 10 if row["direction"] == "en-de" else 100 if row["run"] == runs[1] else 0}
        for row in points
    ]
    third = list(renderer.LABELS)[2]
    points += [{**row, "run": third} for row in points if row["run"] == runs[0]]
    runs = [*runs, third]
    rows, components, native, support = renderer.build_language_mixed_rank_rows(points, runs)
    assert len(rows) == 24
    for role, median_winner, top_winner in (("from", "en", "de"), ("to", "de", "en")):
        for statistic, winner in (("median", median_winner), ("top", top_winner)):
            selected = [
                row for row in rows if row["role"] == role and row["statistic"] == statistic
            ]
            assert selected and all(
                row["language"] == winner for row in selected if row["mixed_rank"] == 1
            )
            assert {row["language_name"] for row in selected} == {"English", "German"}
    assert components and all(row["n_models"] == 3 for row in native)
    assert all(row["state"] == "completed" for row in support)
    checked = []

    def check(figure, path, **kwargs):
        if path.suffix != ".png":
            return
        position = path.parts.index("rankings")
        statistic, role = path.parts[position + 1 : position + 3]
        expected = (
            "English" if (statistic, role) in (("median", "from"), ("top", "to")) else "German"
        )
        axis = figure.axes[0]
        assert axis.get_yticklabels()[0].get_text() == expected
        assert {label.get_text() for label in axis.get_yticklabels()} == {"English", "German"}
        assert "Language Rankings" in figure._suptitle.get_text()
        column = [label.get_text() for label in axis.get_xticklabels()].index("COMET")
        value = next(text.get_text() for text in axis.texts if text.get_position() == (column, 0))
        assert float(value) == (10 if statistic == "median" else 100)
        checked.append(path)

    monkeypatch.setattr(matplotlib.figure.Figure, "savefig", check)
    saved = renderer.write_language_rank_reports(tmp_path, points, runs)
    assert len(saved) == len(checked) == 12
    with (tmp_path / "tables/language_rankings/language_ranks.csv").open(
        encoding="utf-8", newline=""
    ) as handle:
        exported = list(csv.DictReader(handle))
    assert {row["language_name"] for row in exported} == {"English", "German"}
    assert all("model" not in row and "run" not in row for row in exported)
    monkeypatch.setattr(
        renderer, "DATASETS", {"google_patents": "Patents", "jrc_articles": "Articles"}
    )
    partial = [{**row, "dataset": "jrc_articles"} for row in points if row["direction"] == "en-de"]
    overall, _, _, coverage = renderer.build_language_mixed_rank_rows([*points, *partial], runs)
    assert all(
        row["language"] == "en"
        for row in overall
        if row["scope"] == "overall" and row["role"] == "from"
    )
    assert any(
        row["language"] == "de"
        and row["scope"] == "overall"
        and row["role"] == "from"
        and row["state"] == "incomplete_metric_strata"
        for row in coverage
    )


def test_language_scores_rank_directions_not_models_and_do_not_weight_rows(monkeypatch):
    points, runs = language_points(monkeypatch)
    balanced, components, support = renderer.build_language_direction_rows(points, runs)
    assert len(balanced) == 8 and len(components) == 40
    assert support[0]["n_common_directions"] == 2
    assert all(
        row["balanced_score"]
        == pytest.approx(100 * 2.5 / 3 if row["direction"] == "en-de" else 100 * 0.5 / 3)
        for row in balanced
    )
    pairs, overall = renderer.aggregate_language_pairs(balanced, runs)
    assert len(pairs) == 12 and len(overall) == 12
    source, target = renderer.build_language_rankings(balanced, runs)

    def selected(rows):
        return [
            row
            for row in rows
            if row["dataset"] == "all_datasets" and row["setting"] == "both_prompts"
        ]

    assert selected(source)[0]["language"] == "en"
    assert selected(target)[0]["language"] == "de"
    assert selected(source)[0]["balanced_score"] == pytest.approx(100 * 2.5 / 3)
    with pytest.raises(ValueError, match="Duplicate"):
        renderer.build_language_direction_rows(points + points[:1], runs)


def test_language_scores_balance_families_instead_of_metric_counts(monkeypatch):
    points, runs = language_points(monkeypatch)
    renderer.RANK_FAMILIES["lexical"] = ("bleu", "chrf")
    points += [
        {**row, "metric": "chrf", "value": -row["value"]}
        for row in points
        if row["metric"] == "bleu"
    ]
    balanced, _, _ = renderer.build_language_direction_rows(points, runs)
    for row in balanced:
        assert row["lexical_score"] == pytest.approx(50)
        assert row["balanced_score"] == pytest.approx(
            (row["semantic_score"] + 50 + row["terminology_score"]) / 3
        )


def test_language_prompt_comparisons_share_the_same_rank_pool(monkeypatch):
    points, runs = language_points(monkeypatch)
    points = [{**row, "value": row["value"] + (row["setting"] == "few_shot")} for row in points]
    balanced, _, _ = renderer.build_language_direction_rows(points, runs)
    strong = [row for row in balanced if row["direction"] == "en-de"]
    assert all(
        row["balanced_score"] == pytest.approx(100 if row["setting"] == "few_shot" else 100 * 2 / 3)
        for row in strong
    )


def test_language_scores_intersect_prompt_model_metric_support(monkeypatch):
    points, runs = language_points(monkeypatch)
    points.pop()
    balanced, _, support = renderer.build_language_direction_rows(points, runs)
    assert balanced == []
    assert support[0]["directions"] == "en-de"
    assert support[0]["state"] == "insufficient_common_directions"


def test_language_rankings_do_not_rank_incomplete_overall_languages(monkeypatch):
    points, runs = language_points(monkeypatch)
    balanced, _, _ = renderer.build_language_direction_rows(points, runs)
    monkeypatch.setattr(renderer, "DATASETS", {"google_patents": "Patents", "missing": "Missing"})
    source, target = renderer.build_language_rankings(balanced, runs)
    assert all(
        row["language_rank"] is None and row["balanced_score"] is None
        for row in source + target
        if row["dataset"] == "all_datasets"
    )


def test_language_correlations_average_directions_per_model_and_separate_roles(
    tmp_path, monkeypatch
):
    import json

    import matplotlib.figure

    runs = list(renderer.LABELS)[:3]
    points = [
        {
            "view": "shared_general",
            "dataset": "jrc_articles",
            "category": "not_applicable",
            "metric": "comet",
            "run": run,
            "setting": setting,
            "direction": direction,
            "value": values[index],
            "rows_scored": 1000 if direction == "de-fr" else 1,
        }
        for setting in renderer.SETTINGS
        for direction, values in (
            ("de-en", (1, 2, 3)),
            ("de-fr", (3, 6, 9)),
            ("es-en", (3, 6, 9)),
            ("es-fr", (1, 2, 3)),
            ("en-de", (9, 6, 3)),
            ("fr-de", (9, 6, 3)),
        )
        for index, run in enumerate(runs)
    ]
    rows, scores = renderer.build_language_correlations(points, runs)
    selected = [
        row
        for row in rows
        if row["role_x"] == row["role_y"] == "to"
        and (row["language_x"], row["language_y"]) == ("en", "fr")
    ]
    assert len(selected) == 2
    assert all(
        json.loads(row["values_x"]) == json.loads(row["values_y"]) == [2, 4, 6]
        and row["pearson"] == pytest.approx(1)
        for row in selected
    )
    cross = [
        row
        for row in rows
        if (row["role_x"], row["language_x"], row["role_y"], row["language_y"])
        == ("from", "de", "to", "de")
    ]
    assert len(cross) == 2 and all(row["pearson"] == pytest.approx(-1) for row in cross)
    assert all(
        row["n_directions"] == 2 and row["value"] == 2
        for row in scores
        if row["role"] == "from" and row["language"] == "de" and row["run"] == runs[0]
    )
    checked = []

    def check(figure, path, **kwargs):
        if path.suffix != ".png":
            return
        axes = [axis for axis in figure.axes if axis.images]
        assert len(axes) == 3
        assert all("target" in axis.get_xlabel() for axis in (axes[0], axes[2]))
        assert all("source" in axis.get_ylabel() for axis in (axes[1], axes[2]))
        assert axes[0].images[0].get_array().shape == (3, 3)
        assert axes[1].images[0].get_array().shape == (4, 4)
        assert axes[2].images[0].get_array().shape == (4, 3)
        assert axes[2].images[0].get_array()[0, 0] == pytest.approx(-1)
        assert all(axis.images[0].get_clim() == (-1, 1) for axis in axes)
        figure.canvas.draw()
        canvas = figure.canvas.get_renderer()
        footer = figure.texts[-1].get_window_extent(canvas)
        assert all(not axis.get_tightbbox(canvas).overlaps(footer) for axis in axes)
        checked.append(path)

    monkeypatch.setattr(matplotlib.figure.Figure, "savefig", check)
    saved = renderer.write_language_correlations(tmp_path, points, runs)
    assert len(saved) == len(checked) == 4


def test_combined_language_correlations_balance_strata_and_reject_missing_support(
    tmp_path, monkeypatch
):
    import json

    import matplotlib.figure
    import numpy as np
    from matplotlib.collections import PathCollection

    monkeypatch.setattr(renderer, "DATASETS", {"first": "First", "second": "Second"})
    runs = list(renderer.LABELS)[:3]
    scores = [
        {
            "view": "shared_general",
            "category": "not_applicable",
            "metric": "comet",
            "dataset": dataset,
            "setting": setting,
            "role": role,
            "language": language,
            "run": run,
            "value": value * (3 - index if language == "fr" else index + 1),
            "n_directions": 1000 if dataset == "first" else 1,
            "directions": "de-en;fr-en",
        }
        for dataset, setting, value in (
            ("first", "zero_shot", 1),
            ("first", "few_shot", 3),
            ("second", "zero_shot", 9),
            ("second", "few_shot", 11),
        )
        for role, language in (
            ("from", "de"),
            ("from", "fr"),
            ("to", "de"),
            ("to", "fr"),
            ("from", "pt"),
        )
        for index, run in enumerate(runs)
        if language != "pt" or dataset == "first"
    ]
    rows, combined = renderer.build_combined_language_correlations(scores, runs)
    selected = [
        row
        for row in rows
        if row["role_x"] == row["role_y"] == "from"
        and (row["language_x"], row["language_y"]) == ("de", "fr")
    ]
    assert len(selected) == 1
    assert json.loads(selected[0]["values_x"]) == [6, 12, 18]
    assert json.loads(selected[0]["values_y"]) == [18, 12, 6]
    assert selected[0]["pearson"] == pytest.approx(-1)
    missing = [row for row in combined if row["language"] == "pt"]
    assert len(missing) == 3 and all(
        row["value"] is None
        and row["state"] == "incomplete_strata"
        and row["n_strata"] == 2
        and row["required_strata"] == 4
        for row in missing
    )
    assert not any("pt" in (row["language_x"], row["language_y"]) for row in rows)
    checked = []

    def check(figure, path, **kwargs):
        if path.suffix != ".png":
            return
        axis = figure.axes[0]
        assert "German" in axis.get_xlabel() and "French" in axis.get_ylabel()
        assert "all supported languages" in axis.get_xlabel().lower()
        dots = [item for item in axis.collections if isinstance(item, PathCollection)]
        np.testing.assert_array_equal(
            [dot.get_offsets()[0] for dot in dots], [[6, 18], [12, 12], [18, 6]]
        )
        figure.canvas.draw()
        canvas = figure.canvas.get_renderer()
        assert not axis.get_tightbbox(canvas).overlaps(figure.texts[-1].get_window_extent(canvas))
        assert not axis.get_tightbbox(canvas).overlaps(figure.legends[0].get_window_extent(canvas))
        checked.append(path)

    monkeypatch.setattr(matplotlib.figure.Figure, "savefig", check)
    saved = renderer.write_combined_language_scatter(tmp_path, rows, runs)
    assert len(saved) == len(checked) == 2


def test_language_pair_correlations_compare_models_not_prompts(tmp_path, monkeypatch):
    import matplotlib.figure
    import numpy as np
    from matplotlib.collections import PathCollection

    runs = list(renderer.LABELS)[:3]
    points = [
        {
            "view": "shared_general",
            "dataset": "jrc_articles",
            "category": "not_applicable",
            "metric": "comet",
            "run": run,
            "setting": setting,
            "direction": direction,
            "value": values[index],
            "rows_scored": 1,
        }
        for setting in renderer.SETTINGS
        for direction, values in (
            ("de-en", (1, 2, 3)),
            ("de-fr", (2, 4, 6) if setting == "zero_shot" else (6, 4, 2)),
            ("en-fr", (4, 4, 4)),
        )
        for index, run in enumerate(runs)
    ]
    rows = renderer.build_language_pair_correlations(points, runs)
    selected = [
        row for row in rows if (row["direction_x"], row["direction_y"]) == ("de-en", "de-fr")
    ]
    assert len(selected) == 2
    for row in selected:
        expected = 1 if row["setting"] == "zero_shot" else -1
        assert row["pearson"] == pytest.approx(expected)
        assert row["spearman"] == pytest.approx(expected)
        assert row["n_models"] == 3
        assert row["values_x"] == "[1.0, 2.0, 3.0]"
    constants = [row for row in rows if row["direction_y"] == "en-fr"]
    assert constants and all(
        row["state"] == "constant_scores" and row["pearson"] is None for row in constants
    )
    checked = []

    def check(figure, path, **kwargs):
        if path.suffix != ".png":
            return
        if "english_vs_french" in path.name:
            axis = figure.axes[0]
            assert "English" in axis.get_xlabel() and "French" in axis.get_ylabel()
            dots = [item for item in axis.collections if isinstance(item, PathCollection)]
            expected_y = (2, 4, 6) if "zero_shot" in path.name else (6, 4, 2)
            np.testing.assert_array_equal(
                [dot.get_offsets()[0] for dot in dots],
                list(zip((1, 2, 3), expected_y, strict=True)),
            )
            assert all(handle.get_marker() == "o" for handle in figure.legends[0].legend_handles)
        else:
            for axis in (axis for axis in figure.axes if axis.images):
                matrix = axis.images[0].get_array()
                assert matrix[0, 1] == pytest.approx(1 if "zero_shot" in path.name else -1)
                assert np.ma.getmaskarray(matrix)[2, :].all()
        checked.append(path)

    monkeypatch.setattr(matplotlib.figure.Figure, "savefig", check)
    saved = renderer.write_language_pair_correlations(tmp_path, points, runs)
    assert len(saved) == len(checked) == 4


def test_language_figures_preserve_native_heatmaps_and_pair_model_coordinates(
    tmp_path, monkeypatch
):
    import matplotlib.figure
    import numpy as np

    points, runs = language_points(monkeypatch)
    checked = []

    def check(figure, path, **kwargs):
        if path.suffix != ".png":
            return
        if "native_heatmaps" in path.parts:
            images = [axis.images[0] for axis in figure.axes if axis.images]
            assert images
            assert max(float(image.get_array().max()) for image in images) == 510
        elif "model_pairs" in path.parts:
            axes = [axis for axis in figure.axes if axis.images]
            assert len(axes) == 2
            for axis in axes:
                assert axis.get_xlabel() == axis.get_ylabel() == "Translation direction"
                assert np.ma.getmaskarray(axis.images[0].get_array()).all()
        checked.append(path)

    monkeypatch.setattr(matplotlib.figure.Figure, "savefig", check)
    saved = renderer.write_language_analysis(tmp_path, points, runs)
    assert len(saved) == len(checked) == 32
    assert (tmp_path / "language_rankings_from.md").exists()
    assert (tmp_path / "language_rankings_to.md").exists()
    assert "NOT partner-matched" in (tmp_path / "figures/languages/README.md").read_text()


def test_best_language_scores_use_whole_direction_maximum_and_model_median(monkeypatch):
    points, runs = language_points(monkeypatch)
    selected = [row for row in points if row["metric"] == "comet"]
    summaries, models = renderer.build_best_language_rows(selected, runs)
    assert len(summaries) == 4 and len(models) == 8
    for row in summaries:
        offset = 10 if row["direction"] == "en-de" else 0
        assert row["best_score"] == 1000 + offset
        assert row["median_score"] == 500 + offset
        assert row["best_runs"] == runs[1]
        assert row["hardest_pair_rank"] == (1 if offset == 0 else 2)
    ties = [{**row, "value": 0} for row in selected]
    tied, _ = renderer.build_best_language_rows(ties, runs)
    assert all(
        row["best_score"] == 0 and row["n_tied_best"] == 2 and row["hardest_pair_rank"] == 1
        for row in tied
    )
    with pytest.raises(ValueError, match="every model and both prompts"):
        renderer.build_best_language_rows(selected[:-1], runs)
    with pytest.raises(ValueError, match="Duplicate"):
        renderer.build_best_language_rows(selected + selected[:1], runs)


def test_best_language_figures_share_color_ranges_and_sort_by_best(tmp_path, monkeypatch):
    import matplotlib.figure
    from matplotlib.collections import PathCollection

    points, runs = language_points(monkeypatch)
    points = [row for row in points if row["metric"] == "comet"]
    checked = []

    def check(figure, path, **kwargs):
        if path.suffix != ".png":
            return
        if "best_models" in path.parts:
            axis = next(axis for axis in figure.axes if axis.images)
            assert float(axis.images[0].get_array().max()) == 1010
            assert any("M02" in text.get_text() for text in axis.texts)
        elif "best_vs_median" in path.parts:
            axes = [axis for axis in figure.axes if axis.images]
            assert axes[0].images[0].get_clim() == axes[1].images[0].get_clim()
            assert float(axes[0].images[0].get_array().max()) == 1010
            assert float(axes[1].images[0].get_array().max()) == 510
        elif "hardest_pairs" in path.parts:
            axis = figure.axes[0]
            assert axis.get_yticklabels()[0].get_text() == "German -> English"
            dots = [item for item in axis.collections if isinstance(item, PathCollection)]
            assert len(dots) == 3
            assert dots[-1].get_offsets()[:, 0].tolist() == [1000, 1010]
            assert axis.get_ylim()[0] > axis.get_ylim()[1]
        checked.append(path)

    monkeypatch.setattr(matplotlib.figure.Figure, "savefig", check)
    saved = renderer.write_best_language_figures(tmp_path, points, runs)
    assert len(saved) == len(checked) == 6
    assert (tmp_path / "tables/best_language_pairs.csv").exists()
    assert (tmp_path / "figures/languages/best_performance.md").exists()


def test_direction_terminology_compares_both_metrics_without_changing_originals(
    tmp_path, monkeypatch
):
    import matplotlib.figure

    base, runs = language_points(monkeypatch)
    base = [row for row in base if row["metric"] == "comet"]
    points = [{**row, "view": "luna", "category": "all_terms", "metric": metric,
               "value": float(row["value"]) / divisor}
              for metric, divisor in (("variant_aware_target_term_coverage", 20),
                                       ("term_bertscore_recall", 5000)) for row in base]
    original = tmp_path / "tables/best_language_pairs.csv"
    original.parent.mkdir()
    original.write_bytes(b"Keep original best-language summaries")
    checked = []

    def check(figure, path, **kwargs):
        if path.suffix != ".png":
            return
        axes = [axis for axis in figure.axes if axis.images]
        assert len(axes) == 4
        for index in (0, 2):
            assert axes[index].images[0].get_clim() == axes[index + 1].images[0].get_clim()
        assert renderer.METRIC_LABELS["term_bertscore_recall"] in axes[2].get_title()
        assert float(axes[2].images[0].get_array().max()) == pytest.approx(0.202)
        assert float(axes[3].images[0].get_array().max()) == pytest.approx(0.102)
        assert any(text.get_text() == "0.202" for text in axes[2].texts)
        checked.append(path)

    monkeypatch.setattr(matplotlib.figure.Figure, "savefig", check)
    saved = renderer.write_best_language_figures(
        tmp_path, points, runs, terminology_comparison=True
    )
    assert len(saved) == len(checked) == 2
    assert all("languages/direction_terminology/luna/" in relative for relative in saved)
    assert original.read_bytes() == b"Keep original best-language summaries"
    assert (tmp_path / "tables/direction_terminology_pairs.csv").exists()
    assert (tmp_path / "figures/languages/direction_terminology/README.md").exists()


@pytest.mark.parametrize("role,expected", [("from", 1000), ("to", 1010)])
def test_direction_performance_orients_source_and_target_rows(
    tmp_path, monkeypatch, role, expected
):
    import matplotlib.figure

    points, runs = language_points(monkeypatch)
    points = [row for row in points if row["metric"] == "comet"]
    checked = []

    def check(figure, path, **kwargs):
        if path.suffix == ".png":
            axis = next(axis for axis in figure.axes if axis.images)
            assert axis.get_ylabel().startswith(role.title())
            assert float(axis.images[0].get_array()[0, 1]) == expected
            checked.append(path)

    monkeypatch.setattr(matplotlib.figure.Figure, "savefig", check)
    saved = renderer.write_best_language_figures(tmp_path, points, runs, direction_role=role)
    assert len(saved) == len(checked) == 2
    assert all(f"/shared_general/{role}/" in relative for relative in saved)


def test_direction_terminology_cli_requires_native_input(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr("sys.argv", ["renderer", "--direction-terminology-only",
                                     "--output", str(tmp_path)])
    with pytest.raises(SystemExit) as error:
        renderer.main()
    assert error.value.code == 2
    assert "Generate native direction scores" in capsys.readouterr().err


def test_language_violin_roles_preserve_points_and_equal_direction_weights(monkeypatch):
    points, runs = language_points(monkeypatch)
    points = [row for row in points if row["metric"] == "comet"]
    points += [
        {**row, "direction": "en-fr", "value": row["value"] + 20}
        for row in points
        if row["direction"] == "en-de"
    ]
    rows, support = renderer.build_language_violin_rows(points, runs)
    assert len(rows) == len(points) * 3
    selected = [
        row
        for row in support
        if row["role"] == "from" and row["language_group"] == "en" and row["setting"] == "zero_shot"
    ]
    assert len(selected) == 1
    assert selected[0]["n_points"] == 4 and selected[0]["n_directions"] == 2
    assert selected[0]["mean_score"] == 520
    pair = [row for row in support if row["role"] == "pair"]
    assert all(row["n_points"] == len(runs) for row in pair)
    assert {row["value"] for row in rows if row["role"] == "pair"} == {
        float(row["value"]) for row in points
    }


def test_language_violin_plots_use_native_values_and_all_three_roles(tmp_path, monkeypatch):
    import matplotlib.figure
    import numpy as np
    from matplotlib.collections import PathCollection

    points, runs = language_points(monkeypatch)
    points = [row for row in points if row["metric"] == "comet"]
    checked = []

    def check(figure, path, **kwargs):
        if path.suffix != ".png":
            return
        axis = figure.axes[0]
        dots = [item for item in axis.collections if isinstance(item, PathCollection)]
        values = np.concatenate([item.get_offsets()[:, 1] for item in dots])
        np.testing.assert_array_equal(np.sort(values), [0, 10, 1000, 1010])
        assert "native score" in axis.get_ylabel()
        assert axis.get_ylim() == pytest.approx((-50.5, 1060.5))
        assert all(handle.get_marker() == "o" for handle in figure.legends[0].legend_handles)
        checked.append(path)

    monkeypatch.setattr(matplotlib.figure.Figure, "savefig", check)
    saved = renderer.write_language_violin_figures(tmp_path, points, runs)
    assert len(saved) == len(checked) == 6
    assert {name.split("/")[2] for name in saved} == {"pair", "from", "to"}
    assert (tmp_path / "tables/language_violin_support.csv").exists()


def test_language_violin_cli_requires_native_input(tmp_path, monkeypatch, capsys):
    import sys

    monkeypatch.setattr(
        sys, "argv", ["renderer", "--language-violins-only", "--output", str(tmp_path)]
    )
    with pytest.raises(SystemExit) as error:
        renderer.main()
    assert error.value.code == 2
    assert "Generate native direction scores" in capsys.readouterr().err


def test_population_is_kept_separate():
    assert renderer.population("qwen38_27b_local") == "current"
    assert renderer.population("qwen38_27b_local__historical_untimed") == "historical"
    assert renderer.population("example__native_sample") == "native_sample"


def test_prompting_violin_points_reuse_common_directions_and_corpus_scores():
    run = next(iter(renderer.LABELS))
    groups = {"de-en": result(40), "en-de": result(0), "fr-en": result(90)}
    groups["de-en"]["mean_metrics"]["bleu"] = 99
    summaries = {
        ("original_glm", "all_terms", run): {
            "dataset_settings": {"google_patents": {"zero_shot": {"by_direction": groups}}}
        }
    }
    aggregate = {
        "view": "shared_general",
        "category": "not_applicable",
        "run": run,
        "model": renderer.LABELS[run],
        "dataset": "google_patents",
        "setting": "zero_shot",
        "metric": "bleu",
        "directions": "de-en;en-de",
        "n_directions": 2,
        "statistic": "direction_macro_corpus_score",
        "value": 20,
    }
    points = renderer.build_prompting_violin_rows(summaries, [aggregate])
    assert [row["direction"] for row in points] == ["de-en", "en-de"]
    assert [row["value"] for row in points] == [40, 0]
    assert sum(row["value"] for row in points) / len(points) == aggregate["value"]
    assert all(row["n_common_directions"] == 2 for row in points)
    assert renderer.build_prompting_violin_rows(summaries, [{**aggregate, "directions": ""}]) == []
    groups["de-en"]["metric_status"]["bleu"]["state"] = "not_applicable"
    with pytest.raises(ValueError, match="Unavailable violin point"):
        renderer.build_prompting_violin_rows(summaries, [aggregate])


def test_violin_normalization_uses_shared_panel_bounds_and_preserves_native_values():
    base = {"view": "luna", "category": "all_terms", "dataset": "google_patents", "metric": "comet"}
    rows = [
        {**base, "run": run, "setting": setting, "value": value}
        for run, setting, value in [
            ("first", "zero_shot", 70),
            ("first", "few_shot", 80),
            ("second", "zero_shot", 90),
            ("second", "few_shot", 110),
        ]
    ]
    rows += [{**base, "metric": "bleu", "value": 42}]
    normalized = renderer.normalize_prompting_violin_rows(rows)
    assert [row["value"] for row in normalized] == [0, 0.25, 0.5, 1, 0.5]
    assert [row["raw_value"] for row in normalized] == [70, 80, 90, 110, 42]
    assert [row["value"] for row in rows] == [70, 80, 90, 110, 42]
    assert all(
        row["normalization_min"] == 70 and row["normalization_max"] == 110 for row in normalized[:4]
    )
    assert renderer.normalize_prompting_violin_rows([]) == []
    with pytest.raises(ValueError, match="Nonfinite"):
        renderer.normalize_prompting_violin_rows([{**base, "value": float("nan")}])


@pytest.mark.parametrize(
    "violin,normalized,zoomed",
    [(False, False, False), (True, False, False), (True, True, False), (True, False, True)],
)
def test_prompting_bars_pair_native_scores_and_keep_missing_distinct_from_zero(
    tmp_path, monkeypatch, violin, normalized, zoomed
):
    import math

    import matplotlib.figure
    from matplotlib.collections import PathCollection

    monkeypatch.setattr(renderer, "DATASETS", {"google_patents": "Chemical Patents"})
    monkeypatch.setattr(renderer, "VIEWS", ("luna",))
    monkeypatch.setattr(renderer, "GENERAL", ("comet",))
    runs = list(renderer.LABELS)[:2]
    aggregates = []
    for view, category, metrics in [
        ("shared_general", "not_applicable", renderer.GENERAL),
        *[("luna", category, renderer.TERMINOLOGY) for category in renderer.CATEGORIES],
    ]:
        for metric in metrics:
            for setting in renderer.SETTINGS:
                for index, run in enumerate(runs):
                    aggregates.append(
                        {
                            "view": view,
                            "category": category,
                            "dataset": "google_patents",
                            "setting": setting,
                            "run": run,
                            "metric": metric,
                            "value": (
                                None
                                if metric in renderer.TERMINOLOGY[3:]
                                or (index == 1 and setting == "few_shot")
                                else index + (0.25 if setting == "few_shot" else 0)
                            ),
                        }
                    )
    checked = []
    violin_rows = [
        {**row, "value": value}
        for row in aggregates
        if row["value"] is not None
        for value in (
            [0, 0, 0]
            if row["value"] == 0
            else [row["value"] - 0.1, row["value"], row["value"] + 0.1]
        )
    ]
    if normalized:
        violin_rows = renderer.normalize_prompting_violin_rows(violin_rows)
    if zoomed:
        violin_rows = [{**row, "value": row["value"] + 10} for row in violin_rows]

    def check_figure(figure, path, **kwargs):
        if path.suffix != ".png":
            return
        panels = [axis for axis in figure.axes if axis.get_visible()]
        checked.append(len(panels))
        for axis in panels:
            if violin:
                points = [
                    collection.get_offsets().tolist()
                    for collection in axis.collections
                    if isinstance(collection, PathCollection)
                ]
                assert len(points) == 3
                expected = [[0, 0, 0], [0.9, 1, 1.1], [0.15, 0.25, 0.35]]
                for group, values in zip(points, expected, strict=True):
                    assert [point[1] for point in group] == pytest.approx(
                        [value / 1.1 for value in values]
                        if normalized
                        else [value + 10 for value in values]
                        if zoomed
                        else values
                    )
                for group, center in zip(points, (-0.19, 0.81, 0.19), strict=True):
                    assert all(abs(point[0] - center) <= 0.07 for point in group)
            else:
                zero, few = axis.containers
                assert [bar.get_height() for bar in zero] == [0, 1]
                assert few[0].get_height() == 0.25
                assert math.isnan(few[1].get_height())
                for left, right in zip(zero, few, strict=True):
                    assert left.get_x() + left.get_width() < right.get_x()
            assert any(text.get_text() == "NA" for text in axis.texts)
            if zoomed:
                assert axis.get_ylim() == pytest.approx((9.945, 11.155))
                assert axis.get_ylabel() == "Score (native scale)"
            else:
                assert axis.get_ylim()[0] <= 0
            if normalized:
                assert axis.get_ylim() == pytest.approx((-0.04, 1.04))
            assert [text.get_text() for text in axis.get_xticklabels()] == [
                renderer.LABELS[run] for run in runs
            ]

    monkeypatch.setattr(matplotlib.figure.Figure, "savefig", check_figure)
    saved = renderer.write_prompting_bar_figures(
        tmp_path,
        aggregates,
        runs,
        violin_rows=violin_rows if violin else None,
        normalized=normalized,
        zoomed=zoomed,
    )
    assert len(saved) == 2
    folder = (
        "/violins_zoomed/"
        if zoomed
        else ("/violins_normalized/" if normalized else ("/violins/" if violin else "/bars/"))
    )
    assert all(folder in name for name in saved)
    assert checked == [1, 9]


def test_language_prompting_balances_models_partners_and_flags_row_counts(monkeypatch):
    points, runs = language_points(monkeypatch)
    points = [row for row in points if row["metric"] == "comet"]
    points += [{**row, "direction": "en-fr", "rows_scored": 1000}
               for row in points if row["direction"] == "en-de"]
    for row in points:
        row["value"] = 0.2 if row["run"] == runs[0] else 0.8
        if row["setting"] == "few_shot":
            change = 0.1 if row["run"] == runs[0] else 0.3
            row["value"] += change * {"en-de": 1, "de-en": -1, "en-fr": 0}[row["direction"]]
            if row["direction"] == "en-fr" and row["run"] == runs[0]:
                row["rows_scored"] = 999
    rows, models = renderer.build_language_prompting_rows(points, runs)
    english = next(row for row in rows if row["role"] == "from" and row["language"] == "en")
    german = next(row for row in rows if row["role"] == "from" and row["language"] == "de")
    assert english["zero_shot"] == pytest.approx(0.5)
    assert english["few_shot"] == pytest.approx(0.6)
    assert english["delta"] == pytest.approx(0.1)
    assert english["n_directions"] == english["n_models"] == 2
    assert english["n_row_count_mismatches"] == 1
    assert english["row_support_status"] == "different_row_counts"
    assert german["delta"] == pytest.approx(-0.2)
    assert german["row_support_status"] == "equal_counts_unverified_row_identity"
    assert len(models) == 2 * len(rows)
    with pytest.raises(ValueError, match="every model and both prompts"):
        renderer.build_language_prompting_rows(points[:-1], runs)


def test_language_prompting_heatmaps_show_only_relative_percentage(tmp_path, monkeypatch):
    import matplotlib.figure
    import numpy as np

    monkeypatch.setattr(renderer, "CATEGORIES", ("all_terms",))
    points, runs = language_points(monkeypatch)
    points = [row for row in points if row["metric"] == "comet"]
    for row in points:
        row["value"] = 0.5
        if row["setting"] == "few_shot":
            row["value"] += 0.1 if row["direction"] == "en-de" else -0.2
            row["rows_scored"] += 1
    points += [{**row, "view": "luna", "category": "all_terms", "metric": metric,
                "value": row["value"] * scale}
               for metric, scale in (("variant_aware_target_term_coverage", 100),
                                      ("term_bertscore_recall", 1)) for row in list(points)]
    points += [{**row, "direction": "fr-de"} for row in list(points)
               if row["metric"] == "comet" and row["direction"] == "en-de"]
    points += [{**row, "direction": f"{language}-de"}
               for language in ("es", "ja", "ru", "zh") for row in list(points)
               if row["direction"] == "en-de"]
    checked = []

    def check(figure, path, **kwargs):
        if path.suffix != ".png":
            return
        axes = [axis for axis in figure.axes if axis.images]
        assert len(axes) == 1
        axis = axes[0]
        image = axis.images[0]
        assert image.get_clim() == (-1, 1)
        assert image.get_array().shape[0] == 3
        assert float(np.ma.min(image.get_array())) == pytest.approx(-1)
        assert float(np.ma.max(image.get_array())) == pytest.approx(0.5)
        assert image.cmap(image.norm(-1))[0] > image.cmap(image.norm(-1))[1]
        assert image.cmap(image.norm(1))[1] > image.cmap(image.norm(1))[0]
        assert any("-40.00%*" == text.get_text() for text in axis.texts)
        assert any("+20.00%*" == text.get_text() for text in axis.texts)
        assert all("->" not in text.get_text() and " pp" not in text.get_text()
               for text in axis.texts)
        assert all(text.get_text() == "NA" or "%" in text.get_text() for text in axis.texts)
        assert len(axis.texts) == image.get_array().size
        assert any(text.get_text().endswith("*") for text in axis.texts)
        assert figure.get_size_inches()[1] < 5
        if path.stem.startswith("from"):
            assert sum(text.get_text() == "NA" for text in axis.texts) == 2
            mask = np.ma.getmaskarray(image.get_array())
            assert int(mask.sum()) == 2
            for text in axis.texts:
                if text.get_text() == "NA":
                    column, metric_index = text.get_position()
                    assert mask[int(metric_index), int(column)]
            figure.canvas.draw()
            canvas_renderer = figure.canvas.get_renderer()
            labels = [text.get_window_extent(canvas_renderer) for text in axis.texts]
            assert all(not first.overlaps(second) for index, first in enumerate(labels)
                       for second in labels[index + 1:])
            footer = figure.texts[-1].get_window_extent(canvas_renderer)
            color_axis = next(axis for axis in figure.axes if not axis.images)
            assert not footer.overlaps(
                color_axis.xaxis.label.get_window_extent(canvas_renderer)
            )
        checked.append(path)

    monkeypatch.setattr(matplotlib.figure.Figure, "savefig", check)
    saved = renderer.write_language_prompting_figures(tmp_path, points, runs)
    assert len(saved) == len(checked) == 2
    assert (tmp_path / "tables/language_prompting_scores.csv").exists()


@pytest.mark.parametrize("baseline", [0, -0.5])
def test_language_prompting_percentage_masks_nonpositive_baselines(tmp_path, monkeypatch, baseline):
    import matplotlib.figure
    import numpy as np

    points, runs = language_points(monkeypatch)
    monkeypatch.setattr(renderer, "CATEGORIES", ("all_terms",))
    points = [{**row, "value": baseline + (0.1 if row["setting"] == "few_shot" else 0)}
              for row in points if row["metric"] == "comet"]
    checked = []

    def check(figure, path, **kwargs):
        if path.suffix == ".png":
            axis = next(axis for axis in figure.axes if axis.images)
            assert np.ma.getmaskarray(axis.images[0].get_array()).all()
            assert all(text.get_text() == "NA" for text in axis.texts)
            checked.append(path)

    monkeypatch.setattr(matplotlib.figure.Figure, "savefig", check)
    renderer.write_language_prompting_figures(tmp_path, points, runs)
    assert len(checked) == 2


def test_language_prompting_bars_preserve_percentages_and_symlog(tmp_path, monkeypatch):
    import matplotlib.figure
    import numpy as np

    monkeypatch.setattr(renderer, "CATEGORIES", ("all_terms",))
    points, runs = language_points(monkeypatch)
    points = [row for row in points if row["metric"] == "comet"]
    for row in points:
        row["value"] = 0.5
        if row["setting"] == "few_shot":
            row["value"] += 0.1 if row["direction"] == "en-de" else -0.2
            row["rows_scored"] += 1
    points += [{**row, "view": "luna", "category": "all_terms", "metric": metric}
               for metric in renderer.DIRECTION_TERMINOLOGY_METRICS for row in list(points)]
    points += [{**row, "direction": "fr-de"} for row in list(points)
               if row["metric"] == "comet" and row["direction"] == "en-de"]
    checked = []

    def check(figure, path, **kwargs):
        if path.suffix != ".png":
            return
        axis = figure.axes[0]
        assert not axis.images
        assert axis.get_yscale() == "symlog"
        assert len(axis.containers) == 3
        finite = [bar.get_height() for bars in axis.containers for bar in bars
                  if np.isfinite(bar.get_height())]
        assert min(finite) == pytest.approx(-40)
        assert max(finite) == pytest.approx(20)
        for bars in axis.containers:
            for bar in bars:
                red, green, _, _ = bar.get_facecolor()
                if bar.get_height() > 0:
                    assert green > red
                elif bar.get_height() < 0:
                    assert red > green
        assert len({bars[0].get_hatch() for bars in axis.containers}) == 3
        left, right = axis.get_ylim()
        assert left < -40 and right > 40 and left == -right
        texts = [text.get_text() for text in axis.texts]
        assert "+20%*" in texts and "-40%*" in texts
        if path.stem.startswith("from"):
            assert texts.count("NA") == 2
        else:
            assert "NA" not in texts
        assert len(figure.legends[0].get_texts()) == 6
        assert "Symmetric log axis" in figure.texts[-1].get_text()
        checked.append(path)

    monkeypatch.setattr(matplotlib.figure.Figure, "savefig", check)
    renderer.write_language_prompting_figures(tmp_path, points, runs, grouped_bars=True)
    assert len(checked) == 2


@pytest.mark.parametrize("baseline", [0, -0.5])
def test_language_prompting_bars_mask_nonpositive_baselines(tmp_path, monkeypatch, baseline):
    import matplotlib.figure
    import numpy as np

    points, runs = language_points(monkeypatch)
    monkeypatch.setattr(renderer, "CATEGORIES", ("all_terms",))
    points = [{**row, "value": baseline} for row in points if row["metric"] == "comet"]
    checked = []

    def check(figure, path, **kwargs):
        if path.suffix == ".png":
            assert all(np.isnan(bar.get_height()) for bars in figure.axes[0].containers
                       for bar in bars)
            assert all(text.get_text() == "NA" for text in figure.axes[0].texts)
            checked.append(path)

    monkeypatch.setattr(matplotlib.figure.Figure, "savefig", check)
    renderer.write_language_prompting_figures(tmp_path, points, runs, grouped_bars=True)
    assert len(checked) == 2


@pytest.mark.parametrize("change", [0, 1e-7])
def test_language_prompting_bars_preserve_zero_and_tiny_changes(tmp_path, monkeypatch, change):
    import matplotlib.figure
    import numpy as np

    points, runs = language_points(monkeypatch)
    monkeypatch.setattr(renderer, "CATEGORIES", ("all_terms",))
    points = [{**row, "value": 1 + (change if row["setting"] == "few_shot" else 0)}
              for row in points if row["metric"] == "comet"]
    checked = []

    def check(figure, path, **kwargs):
        if path.suffix != ".png":
            return
        axis = figure.axes[0]
        finite = [bar.get_height() for bars in axis.containers for bar in bars
                  if np.isfinite(bar.get_height())]
        assert finite == pytest.approx([100 * change] * len(finite))
        assert axis.get_yscale() == "symlog"
        if change:
            assert min(finite) > 0
            assert "0%" not in [text.get_text() for text in axis.texts]
        else:
            assert sum(text.get_text() == "0%" for text in axis.texts) == len(finite)
        checked.append(path)

    monkeypatch.setattr(matplotlib.figure.Figure, "savefig", check)
    renderer.write_language_prompting_figures(tmp_path, points, runs, grouped_bars=True)
    assert len(checked) == 2


def test_language_prompting_cli_requires_native_input(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr("sys.argv", ["renderer", "--language-prompting-only",
                                     "--output", str(tmp_path)])
    with pytest.raises(SystemExit) as error:
        renderer.main()
    assert error.value.code == 2
    assert "Generate native direction scores" in capsys.readouterr().err


def test_language_mixed_ranks_can_use_only_luna_llm_enriched(tmp_path, monkeypatch):
    import matplotlib.figure

    points, runs = language_points(monkeypatch)
    for row in points:
        if row["view"] == "luna":
            row["value"] = (100 if row["direction"] == "en-de" else 0)
            if row["category"] != "llm_enriched":
                row["value"] = 100 - row["value"]
    selected = [row for row in points if row["view"] == "shared_general"
                or (row["view"] == "luna" and row["category"] == "llm_enriched")]
    ranked, components, native, support = renderer.build_language_mixed_rank_rows(
        selected, runs, views=("luna",), terminology_categories=("llm_enriched",)
    )
    assert ranked and components and native and support
    assert {row["view"] for row in ranked} == {"luna"}
    assert {row["category"] for row in components if row["family"] == "terminology"} == {
        "llm_enriched"
    }
    for role, expected in (("from", "en"), ("to", "de")):
        winner = next(row for row in ranked if row["role"] == role
                      and row["statistic"] == "median" and row["scope"] == "overall"
                      and row["language"] == expected)
        assert winner["terminology_mean_rank"] == 1
        assert not any(key.startswith(("all_terms.", "externally_verified.")) for key in winner)
    captions = []

    def check_caption(figure, path, **kwargs):
        text = " ".join(label.get_text() for label in figure.texts)
        assert "groups equally (LLM-enriched)" in text
        assert "all / external" not in text
        captions.append(path)

    monkeypatch.setattr(matplotlib.figure.Figure, "savefig", check_caption)
    renderer.write_chosen_rank_figures(
        tmp_path, [row for row in ranked if row["role"] == "from"
                   and row["statistic"] == "median"], statistic="median", language_role="from"
    )
    assert captions


def metric_analysis_points(monkeypatch):
    monkeypatch.setattr(renderer, "DATASETS", {"sample": "Sample"})
    monkeypatch.setattr(renderer, "METRIC_ANALYSIS_METRICS", (
        "chrf2++", "comet", "variant_aware_target_term_coverage"
    ))
    runs = list(renderer.LABELS)[:3]
    points = []
    for direction in ("en-de", "fr-de"):
        for index, run in enumerate(runs, 1):
            for setting, factor in (("zero_shot", 1), ("few_shot", 2)):
                for metric in renderer.METRIC_ANALYSIS_METRICS:
                    term = metric in renderer.TERMINOLOGY
                    points.append({"dataset": "sample", "run": run, "setting": setting,
                                   "metric": metric, "direction": direction,
                                   "view": "luna" if term else "shared_general",
                                   "category": "llm_enriched" if term else "not_applicable",
                                   "value": (8 - index * factor) / 10 if term
                                   else index * factor,
                                   "rows_scored": 5 if term else 10})
    return points, runs


def test_story_metric_analysis_pairs_support_and_detects_opposite_changes(monkeypatch):
    points, runs = metric_analysis_points(monkeypatch)
    points = [row for row in points if not (
        row["run"] == runs[-1] and row["direction"] == "fr-de"
        and row["setting"] == "few_shot" and row["metric"] in renderer.TERMINOLOGY
    )]
    models, relations, cases, languages = renderer.build_story_metric_analysis(points, runs)
    selected = [row for row in relations if row["metric_x"] == "comet"]
    assert {row["directions"] for row in selected} == {"en-de"}
    for row in selected:
        assert row["pearson"] == pytest.approx(-1)
        assert row["spearman"] == pytest.approx(-1)
        assert row["kendall_tau"] == pytest.approx(-1)
        assert row["top_model_overlap"] == 0
        assert row["n_row_count_mismatches"] == 3
        assert row["row_support_status"] == "row_identity_unverified"
    assert next(row for row in selected if row["setting"] == "change")["sign_agreement"] == 0
    assert all(row["opposite_changes"] for row in cases if row["metric_x"] == "comet")
    assert {row["role"] for row in languages} == {"from", "to"}
    assert models and all(row["n_models"] == 3 for row in models)


def test_story_metric_analysis_ignores_other_groups_and_masks_constants(monkeypatch):
    points, runs = metric_analysis_points(monkeypatch)
    points += [{**row, "category": "all_terms", "value": 1000}
               for row in points if row["view"] == "luna"]
    for row in points:
        if row["metric"] == "chrf2++":
            row["value"] = 0
    models, relations, cases, languages = renderer.build_story_metric_analysis(points, runs)
    assert models and cases and languages
    constant = [row for row in relations if row["metric_x"] == "chrf2++"]
    assert all(row["state"] == "constant_scores" and row["pearson"] is None
               and row["top_model_overlap"] is None for row in constant)
    assert all(abs(row["value_y"]) < 1 for row in models
               if row["metric_y"] in renderer.TERMINOLOGY)


def test_story_metric_analysis_unavailable_pairs_are_na(monkeypatch):
    points, runs = metric_analysis_points(monkeypatch)
    points = [row for row in points if row["view"] == "shared_general"]
    models, relations, cases, languages = renderer.build_story_metric_analysis(points, runs)
    unavailable = [row for row in relations if row["metric_y"] in renderer.TERMINOLOGY]
    assert unavailable
    assert all(row["state"] == "insufficient_support" and row["pearson"] is None
               and row["n_models"] == 0 for row in unavailable)
    assert all(row["metric_y"] not in renderer.TERMINOLOGY
               for row in [*models, *cases, *languages])


def test_story_metric_analysis_exports_native_values_and_figures(tmp_path, monkeypatch):
    import csv

    import matplotlib.figure

    points, runs = metric_analysis_points(monkeypatch)
    monkeypatch.setattr(renderer, "METRIC_ANALYSIS_PAIRS", (
        ("chrf2++", "comet"), ("comet", "variant_aware_target_term_coverage")
    ))
    saved = []

    def capture(figure, path, **kwargs):
        assert figure.axes and any(axis.images or axis.collections or axis.patches
                                   for axis in figure.axes)
        if path.stem.startswith("ranking_agreement_"):
            images = [axis.images[0] for axis in figure.axes if axis.images]
            assert images[0].get_clim() == (-1, 1)
            assert images[-1].get_clim() == (0, 1)
            assert figure.get_size_inches()[1] == 12
        text = " ".join(label.get_text() for label in figure.texts)
        assert "Luna LLM-enriched" in text
        assert "Row counts do not prove row identity" in text
        saved.append(path)

    monkeypatch.setattr(matplotlib.figure.Figure, "savefig", capture)
    figures = renderer.write_story_metric_analysis(tmp_path, points, runs)
    assert len(figures) == 10
    assert len(saved) == 20
    assert {Path(figure).name for figure in figures} == {
        name for name, _ in renderer.METRIC_ANALYSIS_FIGURES
    }
    with (tmp_path / "tables/metric_analysis/disagreement_cases.csv").open(
        encoding="utf-8", newline=""
    ) as handle:
        rows = list(csv.DictReader(handle))
    assert rows and all(float(row["delta_x"]) * float(row["delta_y"]) < 0 for row in rows)
    assert all(row["row_support_status"] == "row_identity_unverified" for row in rows)
    assert (tmp_path / "figures/metric_analysis/README.md").exists()


def entity_correlation_points(monkeypatch):
    points, runs = metric_analysis_points(monkeypatch)
    monkeypatch.setattr(renderer, "ENTITY_CORRELATION_METRICS", (
        "comet", "variant_aware_target_term_coverage"
    ))
    points += [{**row, "direction": "de-en"} for row in list(points)
               if row["direction"] == "en-de"]
    for row in points:
        position = ("en-de", "fr-de", "de-en").index(row["direction"])
        model = runs.index(row["run"])
        row["value"] = (position + 1) * (model + 1) if model < 2 else 3 - position
        if row["setting"] == "few_shot":
            row["value"] += 0.1
    return points, runs


def test_story_entity_correlations_keep_model_and_language_observations_distinct(monkeypatch):
    points, runs = entity_correlation_points(monkeypatch)
    correlations, scores = renderer.build_story_entity_correlations(points, runs)
    selected = [row for row in correlations if row["matrix"] == "models"
                and row["metric"] == "comet" and row["role"] == "from"]
    reversed_pair = next(row for row in selected if row["entity_x"] == runs[0]
                         and row["entity_y"] == runs[2])
    assert reversed_pair["pearson"] == pytest.approx(-1)
    assert reversed_pair["spearman"] == pytest.approx(-1)
    assert reversed_pair["n_observations"] == 3
    assert reversed_pair["observation_unit"] == "language"
    assert {row["observation_unit"] for row in correlations if row["matrix"] == "languages"} == {
        "model"
    }
    assert all(row["n_observations"] == 3 for row in correlations if row["matrix"] == "languages")
    assert all(row["pearson"] is None and row["state"] == "insufficient_observations"
               for row in correlations if row["matrix"] == "models" and row["role"] == "to")
    assert next(row for row in scores if row["language"] == "en" and row["run"] == runs[0]
                and row["metric"] == "comet" and row["role"] == "from")["value"] == 1.05
    assert all(row["row_support_status"] == "row_identity_unverified" for row in scores)


def test_story_entity_correlations_drop_incomplete_directions_and_other_term_groups(monkeypatch):
    points, runs = entity_correlation_points(monkeypatch)
    points = [row for row in points if not (
        row["run"] == runs[-1] and row["direction"] == "fr-de" and row["setting"] == "few_shot"
    )]
    points += [{**row, "category": "all_terms", "value": 1000}
               for row in points if row["view"] == "luna"]
    correlations, scores = renderer.build_story_entity_correlations(points, runs)
    assert scores and correlations
    assert all("fr-de" not in row["directions"] for row in scores)
    assert all(row["category"] != "all_terms" for row in scores)
    assert all(row["n_observations"] == 2 and row["pearson"] is None for row in correlations
               if row["matrix"] == "models" and row["role"] == "from")


def test_story_entity_correlations_mask_constant_model_diagonals(monkeypatch):
    points, runs = entity_correlation_points(monkeypatch)
    for row in points:
        if row["run"] == runs[-1]:
            row["value"] = 1
    correlations, _ = renderer.build_story_entity_correlations(points, runs)
    selected = [row for row in correlations if row["matrix"] == "models"
                and row["role"] == "from" and runs[-1] in (row["entity_x"], row["entity_y"])]
    assert selected
    assert all(row["state"] == "constant_scores" and row["pearson"] is None
               and row["spearman"] is None for row in selected)


def test_story_entity_correlations_render_matrices_for_both_roles_and_entity_types(
    tmp_path, monkeypatch,
):
    import matplotlib.figure

    points, runs = entity_correlation_points(monkeypatch)
    checked = []

    def capture(figure, path, **kwargs):
        if path.suffix != ".png":
            return
        panels = [axis for axis in figure.axes if axis.images]
        assert len(panels) == 2
        assert all(axis.images[0].get_clim() == (-1, 1) for axis in panels)
        assert "Pearson" in panels[0].get_title() and "Spearman" in panels[1].get_title()
        if "models" in path.parts and path.stem.startswith("to_"):
            assert all(text.get_text() == "NA" for axis in panels for text in axis.texts)
        assert "row identities unverified" in figure.texts[-1].get_text()
        checked.append(path)

    monkeypatch.setattr(matplotlib.figure.Figure, "savefig", capture)
    saved = renderer.write_story_entity_correlations(tmp_path, points, runs)
    assert len(saved) == len(checked) == 8
    assert (tmp_path / "tables/entity_correlations/correlations.csv").exists()
    assert (tmp_path / "tables/entity_correlations/language_model_scores.csv").exists()


def test_story_sources_filter_luna_llm_enriched_and_keep_both_roles(tmp_path, monkeypatch):
    points, runs = language_points(monkeypatch)
    checked = []

    def capture(output, selected, selected_runs, **kwargs):
        assert output == tmp_path / renderer.STORY_SOURCE_FOLDER
        assert selected_runs == runs
        assert all(row["view"] == "shared_general" or
                   (row["view"] == "luna" and row["category"] == "llm_enriched")
                   for row in selected)
        checked.append(kwargs)
        return []

    for name in ("write_language_rank_reports", "write_best_language_figures",
                 "write_language_prompting_figures", "write_story_metric_analysis",
                 "write_story_entity_correlations"):
        monkeypatch.setattr(renderer, name, capture)
    model_calls = []
    monkeypatch.setattr(renderer, "write_story_model_sources",
                        lambda output: model_calls.append(output) or [])
    renderer.write_story_sources(tmp_path, points, runs)
    assert model_calls == [tmp_path]
    assert len(checked) == 8
    assert {kwargs["direction_role"] for kwargs in checked if "direction_role" in kwargs} == {
        "from", "to"
    }
    assert checked[0]["terminology_categories"] == ("llm_enriched",)
    assert checked[5]["categories"] == ("llm_enriched",)
    assert checked[5]["grouped_bars"] is True


@pytest.mark.parametrize("flag", ["--metric-analysis-only", "--story-correlations-only"])
def test_story_metric_analysis_cli_requires_native_input(tmp_path, monkeypatch, capsys, flag):
    monkeypatch.setattr("sys.argv", ["renderer", flag,
                                     "--output", str(tmp_path)])
    with pytest.raises(SystemExit) as error:
        renderer.main()
    assert error.value.code == 2
    assert "Generate native direction scores before metric analysis" in capsys.readouterr().err


def test_story_model_comparison_cli_requires_cost_data(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr("sys.argv", ["renderer", "--model-comparison-only",
                                     "--output", str(tmp_path)])
    with pytest.raises(SystemExit) as error:
        renderer.main()
    assert error.value.code == 2
    assert "Generate API cost/rank/latency data" in capsys.readouterr().err


def test_story_model_sources_read_native_values_and_preserve_missing_costs(tmp_path, monkeypatch):
    import csv

    tables = tmp_path / "tables"
    tables.mkdir()
    rows = [{"view": view, "mixed_rank": "4", "estimated_api_cost_usd": cost,
             "mean_latency_s": "20", "bubble_area_pt2": "160"}
            for view, cost in (("luna", "12.5"), ("luna", ""), ("original_glm", "9"))]
    renderer.write_csv(tables / "chosen_03_cost_rank_latency.csv", rows)
    calls = []

    def capture(output, selected, *, zoomed):
        assert output == tmp_path / renderer.STORY_SOURCE_FOLDER
        assert zoomed and len(selected) == 2
        assert selected[0]["mixed_rank"] == 4
        assert selected[0]["estimated_api_cost_usd"] == 12.5
        assert selected[1]["estimated_api_cost_usd"] is None
        assert selected[0]["bubble_area_pt2"] == 160
        calls.append(selected)
        return []

    monkeypatch.setattr(renderer, "write_cost_rank_bubble_figures", capture)
    renderer.write_story_model_sources(tmp_path)
    path = tmp_path / renderer.STORY_SOURCE_FOLDER / "tables/model_comparison/cost_rank_latency.csv"
    with path.open(encoding="utf-8", newline="") as handle:
        exported = list(csv.DictReader(handle))
    assert len(calls) == 1 and len(exported) == 2
    assert exported[1]["estimated_api_cost_usd"] == ""


def test_story_chosen_cli_requires_native_input(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr("sys.argv", ["renderer", "--story-chosen-only", "--output", str(tmp_path)])
    with pytest.raises(SystemExit) as error:
        renderer.main()
    assert error.value.code == 2
    assert "Generate native direction scores" in capsys.readouterr().err


def test_story_chosen_copies_are_exact_idempotent_and_preserve_original_chosen(tmp_path):
    import hashlib

    selected = renderer.story_figure_selection()
    assert len(selected) == 86
    assert sum(item["tier"] == "optional" for item in selected) == 2
    metric_correlations = [item for item in selected if item["name"].startswith("metrics_luna_")]
    assert {item["source"] for item in metric_correlations} == {
        f"correlations/luna/metric_correlations_all_datasets_{setting}"
        for setting in renderer.SETTINGS
    }
    assert all(item["section"] == "05_metric_analysis"
               and "Pearson and Spearman" in item["purpose"] for item in metric_correlations)
    new_metrics = [item for item in selected if item["section"] == "05_metric_analysis"
                   and "/metric_analysis/" in item["source"]]
    assert {item["name"] for item in new_metrics} == {
        name for name, _ in renderer.METRIC_ANALYSIS_FIGURES
        if name in renderer.STORY_CORRELATION_FIGURES
    }
    entity_items = [item for item in selected if "/entity_correlations/" in item["source"]]
    assert len(entity_items) == 16
    assert {item["target"].split("/")[2] for item in entity_items} == {"languages", "models"}
    assert not any(item["name"] in ("from_sensitivity", "to_sensitivity", "combined_from_comet",
                                   "combined_to_comet") for item in selected)
    model_figures = [item for item in selected if item["section"] == "04_model_behavior"]
    assert len(model_figures) == 23
    assert sum("zoomed_native_violins" in item["source"] for item in model_figures) == 9
    assert sum("cost_rank_latency_zoomed" in item["source"] for item in model_figures) == 7
    assert sum("01_balanced_mixed_rank" in item["source"] for item in model_figures) == 7
    assert not any("hardest_pairs" in item["source"] for item in model_figures)
    figure_three = [item for item in selected if "prompting/language_changes/" in item["source"]]
    assert len(figure_three) == 2
    assert all("/luna/" in item["source"] and "llm_enriched" in item["source"]
               for item in figure_three)
    ranking_items = [item for item in selected if item["section"] == "01_language_tables"]
    assert len(ranking_items) == 28
    contexts = {"overall"} | {
        f"{dataset}_{setting}" for dataset in renderer.DATASETS for setting in renderer.SETTINGS
    }
    expected = {
        f"{statistic}/{role}/{view}/language_rankings_{context}"
        for statistic in ("median", "top") for role in ("from", "to")
        for view in ("luna",) for context in contexts
    }
    assert {item["source"].removeprefix(
        f"../{renderer.STORY_SOURCE_FOLDER}/figures/languages/rankings/")
            for item in ranking_items} == expected
    assert {item["target"].removeprefix("chosen_story/01_language_tables/")
            for item in ranking_items} == expected
    for item in selected:
        for extension in ("png", "pdf"):
            source = tmp_path / "figures" / f"{item['source']}.{extension}"
            source.parent.mkdir(parents=True, exist_ok=True)
            source.write_bytes(f"{item['source']} {extension}".encode())
    index = tmp_path / "figures/chosen/README.md"
    index.parent.mkdir(parents=True, exist_ok=True)
    index.write_text("Keep original Chosen", encoding="utf-8")
    legacy = tmp_path / "figures/chosen_story/01_language_tables/from_median_overall.png"
    legacy.parent.mkdir(parents=True)
    source = tmp_path / (
        "figures/languages/rankings/median/from/luna/language_rankings_overall.png"
    )
    source.parent.mkdir(parents=True, exist_ok=True)
    source.write_bytes(b"Previous original ranking source")
    legacy.write_bytes(source.read_bytes())
    modified = legacy.with_suffix(".pdf")
    modified.write_bytes(b"Keep user-modified legacy figure")
    obsolete = tmp_path / "figures/chosen_story/03_prompting/unwanted"
    obsolete.parent.mkdir(parents=True)
    obsolete.with_suffix(".png").write_bytes(b"Previous managed image")
    obsolete.with_suffix(".pdf").write_bytes(b"User-modified old PDF")
    old_correlations = tmp_path / "figures/chosen_story/05_optional_correlations/previous.png"
    old_correlations.parent.mkdir(parents=True)
    old_correlations.write_bytes(b"Previous managed correlation")
    moved = tmp_path / "figures/chosen_story/05_metric_analysis/ranking_agreement_zero_shot.png"
    moved.parent.mkdir(parents=True)
    moved.write_bytes(b"Supplementary analysis")
    outside = tmp_path / renderer.STORY_SOURCE_FOLDER / "figures/metric_analysis" / moved.name
    outside.parent.mkdir(parents=True, exist_ok=True)
    outside.write_bytes(moved.read_bytes())
    old_model = tmp_path / "figures/chosen_story/04_model_behavior/old_hardest.png"
    old_model.parent.mkdir(parents=True)
    old_model.write_bytes(b"Previous hardest-direction plot")
    renderer.write_csv(tmp_path / "figures/chosen_story/selection.csv", [{
        "target": "chosen_story/03_prompting/unwanted",
        "png_sha256": hashlib.sha256(b"Previous managed image").hexdigest(),
        "pdf_sha256": hashlib.sha256(b"Previous managed PDF").hexdigest(),
    }, {"target": "chosen_story/05_optional_correlations/previous",
        "png_sha256": hashlib.sha256(b"Previous managed correlation").hexdigest()},
        {"target": "chosen_story/05_metric_analysis/ranking_agreement_zero_shot",
         "png_sha256": hashlib.sha256(b"Supplementary analysis").hexdigest()},
        {"target": "chosen_story/04_model_behavior/old_hardest",
         "png_sha256": hashlib.sha256(b"Previous hardest-direction plot").hexdigest()}])
    snapshots = []
    for _ in range(2):
        saved = renderer.write_story_chosen_figures(tmp_path)
        assert len(saved) == 86
        assert not moved.exists() and outside.read_bytes() == b"Supplementary analysis"
        assert not old_model.exists()
        assert not old_correlations.parent.exists()
        assert not obsolete.with_suffix(".png").exists()
        assert obsolete.with_suffix(".pdf").read_bytes() == b"User-modified old PDF"
        assert not legacy.exists()
        assert modified.read_bytes() == b"Keep user-modified legacy figure"
        for item in selected:
            for extension in ("png", "pdf"):
                source = tmp_path / "figures" / f"{item['source']}.{extension}"
                target = tmp_path / "figures" / f"{item['target']}.{extension}"
                assert target.read_bytes() == source.read_bytes()
        assert index.read_text(encoding="utf-8") == "Keep original Chosen"
        folder = tmp_path / "figures/chosen_story"
        snapshots.append({path.relative_to(folder): hashlib.sha256(path.read_bytes()).hexdigest()
                          for path in folder.rglob("*") if path.is_file()})
    assert snapshots[0] == snapshots[1]


def test_story_chosen_checks_all_sources_before_writing(tmp_path):
    with pytest.raises(FileNotFoundError, match="Generate story source figures first"):
        renderer.write_story_chosen_figures(tmp_path)
    assert not (tmp_path / "figures/chosen_story").exists()


@pytest.mark.parametrize("zoomed", [False, True])
def test_chosen_prompting_copies_preserve_originals_and_append_index_once(tmp_path, zoomed):
    kind = "violins_zoomed" if zoomed else "bars"
    number = "05" if zoomed else "04"
    folder = "05_zoomed_native_violins" if zoomed else "04_zero_vs_few_shot"
    relative = f"prompting/{kind}/shared_general/prompting_{kind}_general_google_patents"
    source = tmp_path / "figures" / relative
    source.parent.mkdir(parents=True)
    for extension in ("png", "pdf"):
        source.with_suffix(f".{extension}").write_bytes(f"original {extension}".encode())
    index = tmp_path / "figures/chosen/README.md"
    index.parent.mkdir()
    previous = "# Chosen Figures\n\n## Chosen 03: Existing Figure\n\nExisting content.\n"
    index.write_text(previous, encoding="utf-8")
    for _ in range(2):
        saved = renderer.write_chosen_prompting_figures(tmp_path, [relative], zoomed=zoomed)
        assert saved == [
            f"chosen/{folder}/shared_general/"
            f"chosen_{number}_prompting_{kind}_general_google_patents"
        ]
        for extension in ("png", "pdf"):
            target = tmp_path / "figures" / f"{saved[0]}.{extension}"
            assert target.read_bytes() == source.with_suffix(f".{extension}").read_bytes()
        assert index.read_text(encoding="utf-8").startswith(previous)
        assert index.read_text(encoding="utf-8").count(f"## Chosen {number}:") == 1
        if "## Chosen 06:" not in index.read_text(encoding="utf-8"):
            index.write_text(
                index.read_text(encoding="utf-8")
                + "\n## Chosen 06: Later Section\n\nRetain this.\n",
                encoding="utf-8",
            )
        else:
            assert index.read_text(encoding="utf-8").endswith("Retain this.\n")
    before = index.read_bytes()
    assert renderer.write_chosen_prompting_figures(tmp_path, []) == []
    assert index.read_bytes() == before


def test_output_token_bubbles_select_defaults_sum_tokens_once_and_keep_original_ranks():
    run = "qwen38_27b_local"
    timing = {
        "run": run,
        "scope": "overall",
        "dataset": "all_datasets",
        "setting": "both_prompts",
        "mixed_rank": 4,
        "mean_latency_s": 20,
    }
    summary = {
        "datasets": {
            dataset: {
                "settings": {
                    setting: {
                        "output_tokens": 100,
                        "reasoning_tokens": 40,
                        "requests_translated": 2,
                    }
                    for setting in renderer.SETTINGS
                }
            }
            for dataset in renderer.DATASETS
        }
    }
    row = renderer.build_output_token_rank_rows([timing], {run: summary})[0]
    assert row["output_tokens"] == 600
    assert row["reported_reasoning_tokens"] == 240
    assert row["mixed_rank"] == 4 and row["bubble_area_pt2"] == 160
    assert row["plot_state"] == "plotted" and row["token_requests_translated"] == 12
    group = summary["datasets"]["google_patents"]["settings"]["zero_shot"]
    del group["output_tokens"]
    assert (
        renderer.build_output_token_rank_rows([timing], {run: summary})[0]["plot_state"]
        == "missing_output_tokens"
    )
    group["output_tokens"] = float("nan")
    assert (
        renderer.build_output_token_rank_rows([timing], {run: summary})[0]["output_tokens"] is None
    )
    group["output_tokens"] = 0
    single = {
        **timing,
        "scope": "dataset_prompt",
        "dataset": "google_patents",
        "setting": "zero_shot",
    }
    assert (
        renderer.build_output_token_rank_rows([single], {run: summary})[0]["plot_state"]
        == "plotted"
    )
    assert (
        renderer.build_output_token_rank_rows([{**single, "mean_latency_s": None}], {run: summary})[
            0
        ]["plot_state"]
        == "missing_latency"
    )
    assert renderer.build_output_token_rank_rows([{**single, "run": "gemma_4_31b_it"}], {})[0][
        "plot_state"
    ] == ("not_selected_by_default_evidence")


@pytest.mark.parametrize("tokens", [False, True])
def test_rank_latency_bubble_figures_keep_numeric_coordinates_and_other_chosen_sections(
    tmp_path, monkeypatch, tokens
):
    import matplotlib.figure

    run = "nemotron_3_5_lightning_30b_a3b" if tokens else "qwen38_27b_local"
    row = {
        "run": run,
        "model": renderer.LABELS[run],
        "view": "luna",
        "scope": "overall",
        "dataset": "all_datasets",
        "setting": "both_prompts",
        "mixed_rank": 6 if tokens else 4,
        "mean_latency_s": 20,
        "bubble_area_pt2": 160,
        "plot_state": "plotted",
        "estimated_api_cost_usd": 12,
        "output_tokens": 10_500_000,
    }
    index = tmp_path / "figures/chosen/README.md"
    index.parent.mkdir(parents=True)
    index.write_text("# Chosen Figures\n\n## Chosen 04: Bars\nKeep bars.\n", encoding="utf-8")
    if tokens:
        with index.open("a", encoding="utf-8") as handle:
            handle.write("\n## Chosen 05: Old Token Plots\nRemove from chosen.\n")
    checked = []

    def check_figure(figure, path, **kwargs):
        if path.suffix != ".png":
            return
        if tokens:
            assert "chosen" not in path.relative_to(tmp_path / "figures").parts
            assert figure._suptitle.get_text() == "Output Tokens vs Mixed Rank"
        axis = figure.axes[0]
        assert axis.collections[0].get_offsets().tolist() == [
            [10.5 if tokens else 12, row["mixed_rank"]]
        ]
        assert axis.collections[0].get_sizes().tolist() == [160]
        assert axis.yaxis_inverted()
        assert "output tokens" in axis.get_xlabel() if tokens else "cost" in axis.get_xlabel()
        if tokens:
            figure.canvas.draw()
            canvas = figure.canvas.get_renderer()
            legend = axis.get_legend().get_window_extent(canvas)
            assert all(
                not text.get_window_extent(canvas).overlaps(legend)
                for text in axis.texts
                if text.get_text() == row["model"]
            )
        checked.append(path)

    monkeypatch.setattr(matplotlib.figure.Figure, "savefig", check_figure)
    writer = (
        renderer.write_output_token_rank_figures
        if tokens
        else renderer.write_cost_rank_bubble_figures
    )
    for _ in range(2):
        saved = writer(tmp_path, [row])
        assert len(saved) == 1
        text = index.read_text(encoding="utf-8")
        if tokens:
            assert "## Chosen 05:" not in text
            token_index = tmp_path / "figures/output_tokens/README.md"
            assert (
                token_index.read_text(encoding="utf-8").count(
                    "# Output Tokens vs Mixed Rank (Latency Bubbles)"
                )
                == 1
            )
        else:
            assert text.count("## Chosen 03:") == 1
        assert "## Chosen 04: Bars\nKeep bars." in text
    assert len(checked) == 2


def test_zoomed_cost_rank_bubbles_keep_values_sizes_and_use_per_panel_limits(tmp_path, monkeypatch):
    import matplotlib.figure

    runs = list(renderer.LABELS)[:2]
    rows = [{"run": run, "model": renderer.LABELS[run], "view": "luna",
             "scope": "dataset_prompt", "dataset": dataset, "setting": "zero_shot",
             "mixed_rank": index + 2, "mean_latency_s": 20,
             "bubble_area_pt2": 160, "plot_state": "plotted",
             "estimated_api_cost_usd": value * factor}
            for dataset, factor in (("google_patents", 1), ("jrc_articles", 100))
            for index, (run, value) in enumerate(zip(runs, (10, 12), strict=True))]
    index = tmp_path / "figures/chosen/README.md"
    index.parent.mkdir(parents=True)
    index.write_text("Keep original Chosen", encoding="utf-8")
    checked = []

    def check(figure, path, **kwargs):
        if path.suffix != ".png":
            return
        axis = figure.axes[0]
        assert "cost_rank_latency_zoomed" in path.parts
        expected = [10, 12] if "google_patents" in path.stem else [1000, 1200]
        assert axis.collections[0].get_offsets().tolist() == [
            [cost, rank] for cost, rank in zip(expected, (2, 3), strict=True)
        ]
        assert axis.collections[0].get_sizes().tolist() == [160, 160]
        left, right = axis.get_xlim()
        bottom, top = axis.get_ylim()
        assert left < min(expected) < max(expected) < right
        assert top < 2 < 3 < bottom
        assert top > 1 and bottom < 4
        assert right - left < max(expected)
        text = " ".join(label.get_text() for label in figure.texts)
        assert "axis ranges zoom to each panel without clipping" in text
        checked.append(path)

    monkeypatch.setattr(matplotlib.figure.Figure, "savefig", check)
    saved = renderer.write_cost_rank_bubble_figures(tmp_path, rows, zoomed=True)
    assert len(saved) == len(checked) == 2
    assert index.read_text(encoding="utf-8") == "Keep original Chosen"


def test_cost_rank_bubbles_join_reference_prices_and_preserve_full_population_ranks():
    timing = {
        "view": "luna",
        "scope": "overall",
        "dataset": "all_datasets",
        "setting": "both_prompts",
        "run": "sample",
        "mixed_rank": 6,
        "mean_latency_s": 20,
    }
    price = {
        "scope": "overall",
        "dataset": "all_datasets",
        "setting": "both_prompts",
        "run": "sample",
        "scenario": "reference",
        "total_cost_usd": 12,
    }
    rows = renderer.build_cost_rank_bubble_rows(
        [timing], [price, {**price, "scenario": "alternative", "total_cost_usd": 99}]
    )
    assert rows[0]["estimated_api_cost_usd"] == 12 and rows[0]["mixed_rank"] == 6
    assert rows[0]["bubble_area_pt2"] == 160 and rows[0]["plot_state"] == "plotted"
    assert renderer.latency_bubble_area(40) == 2 * renderer.latency_bubble_area(20)
    assert renderer.build_cost_rank_bubble_rows([timing], [])[0]["plot_state"] == "unpriced"
    assert (
        renderer.build_cost_rank_bubble_rows([timing], [{**price, "total_cost_usd": 0}])[0][
            "plot_state"
        ]
        == "plotted"
    )
    assert (
        renderer.build_cost_rank_bubble_rows([{**timing, "mean_latency_s": None}], [price])[0][
            "plot_state"
        ]
        == "missing_latency"
    )
    with pytest.raises(ValueError, match="Duplicate"):
        renderer.build_cost_rank_bubble_rows([timing], [price, price])
    with pytest.raises(ValueError):
        renderer.latency_bubble_area(float("nan"))


def test_token_cost_combines_input_output_without_double_counting_cache():
    cost = renderer.estimate_token_cost(2_000_000, 1_000_000, 2, 5)
    assert cost["input_cost_usd"] == 4 and cost["output_cost_usd"] == 5
    assert cost["total_cost_usd"] == 9
    discounted = renderer.estimate_token_cost(
        2_000_000, 1_000_000, 2, 5, cached_tokens=1_000_000, cached_rate=0.2
    )
    assert discounted["input_cost_usd"] == pytest.approx(2.2)
    assert discounted["total_cost_usd"] == pytest.approx(7.2)
    with pytest.raises(ValueError):
        renderer.estimate_token_cost(1, 1, 2, 5, cached_tokens=2, cached_rate=0.2)
    with pytest.raises(ValueError):
        renderer.estimate_token_cost(1, 1, 2, 5, cached_tokens=1)
    with pytest.raises(ValueError):
        renderer.estimate_token_cost(float("nan"), 1, 2, 5)


def test_api_cost_rows_keep_unpriced_models_na_and_do_not_transfer_local_cache(monkeypatch):
    monkeypatch.setattr(renderer, "DATASETS", {"google_patents": "Chemical Patents"})
    monkeypatch.setattr(renderer, "SETTINGS", ("zero_shot",))
    runs = list(renderer.LABELS)[:2]
    summaries = {
        run: {
            "model": "sample",
            "datasets": {
                "google_patents": {
                    "settings": {
                        "zero_shot": {
                            "input_tokens": 2_000_000,
                            "output_tokens": 1_000_000,
                            "cached_tokens": 1_000_000,
                            "reasoning_tokens": 0,
                            "requests": 100,
                        },
                    }
                }
            },
        }
        for run in runs
    }
    pricing = {
        "currency": "USD",
        "rate_unit": "per_1000000_tokens",
        "verified_on": "2026-11-03",
        "scenario": "recorded_token_repricing_without_cache_discount",
        "models": {
            runs[0]: {
                "recorded_model": "sample",
                "provider": "example",
                "pricing_model_id": "sample",
                "input_rate": 2,
                "output_rate": 5,
                "cached_input_rate": 0.2,
                "source_url": "https://example.com",
                "alternatives": [{"name": "alternative", "input_rate": 3, "output_rate": 6}],
            },
        },
    }
    rows = renderer.build_api_cost_rows(summaries, pricing)
    assert len(rows) == 6
    priced = [row for row in rows if row["run"] == runs[0] and row["scenario"] == "reference"]
    assert all(row["total_cost_usd"] == 9 for row in priced)
    assert all(row["billed_cached_tokens_assumed"] == 0 for row in priced)
    assert all(row["cached_tokens"] == 1_000_000 for row in priced)
    assert all(
        row["total_cost_usd"] is None and row["input_usd_per_million"] is None
        for row in rows
        if row["run"] == runs[1]
    )
    assert all(
        row["pricing_model_id"] == "alternative" and row["total_cost_usd"] == 12
        for row in rows
        if row["scenario"] == "alternative"
    )
    summaries[runs[0]]["model"] = "different-model"
    with pytest.raises(ValueError, match="does not match"):
        renderer.build_api_cost_rows(summaries, pricing)


def test_efficiency_means_weight_strata_not_request_counts(monkeypatch):
    monkeypatch.setattr(renderer, "DATASETS", {"google_patents": "Chemical Patents"})
    run = next(iter(renderer.LABELS))
    ranked = {
        "view": "luna",
        "scope": "overall",
        "dataset": "all_datasets",
        "setting": "both_prompts",
        "run": run,
        "model": renderer.LABELS[run],
        "mixed_rank": 1,
        "mixed_mean_rank": 1.2,
    }
    summaries = {
        run: {
            "datasets": {
                "google_patents": {
                    "settings": {
                        "zero_shot": {"timing": {"latency_s": {"mean": 2, "count": 100}}},
                        "few_shot": {"timing": {"latency_s": {"mean": 8, "count": 1}}},
                    }
                }
            }
        }
    }
    row = renderer.build_efficiency_rows([ranked], summaries)[0]
    assert row["mean_latency_s"] == 5
    assert row["timed_latency_requests"] == 101
    assert row["mixed_rank"] == 1 and row["n_timing_strata"] == 2
    summaries[run]["datasets"]["google_patents"]["settings"]["few_shot"]["timing"]["latency_s"][
        "mean"
    ] = 0
    row = renderer.build_efficiency_rows([ranked], summaries)[0]
    assert row["mean_latency_s"] is None and row["timing_state"] == "missing_timing"
    assert row["n_timing_strata"] == 1
    row = renderer.build_efficiency_rows([ranked], {})[0]
    assert row["mean_latency_s"] is None and row["timed_latency_requests"] == 0


def test_language_ranking_statistics_cli_requires_native_input(tmp_path, monkeypatch, capsys):
    import sys

    monkeypatch.setattr(
        sys, "argv", ["renderer", "--language-ranking-statistics-only", "--output", str(tmp_path)]
    )
    with pytest.raises(SystemExit) as error:
        renderer.main()
    assert error.value.code == 2
    assert "Generate native direction scores before ranking languages" in capsys.readouterr().err


def test_ranking_statistics_cli_requires_native_input(tmp_path, monkeypatch, capsys):
    import sys

    monkeypatch.setattr(
        sys, "argv", ["renderer", "--ranking-statistics-only", "--output", str(tmp_path)]
    )
    with pytest.raises(SystemExit) as error:
        renderer.main()
    assert error.value.code == 2
    assert "Generate native metric and direction scores" in capsys.readouterr().err


@pytest.mark.parametrize("statistic,winner", [("median", 0), ("top", 1)])
def test_statistic_rankings_use_direction_median_or_maximum(
    tmp_path, monkeypatch, statistic, winner
):
    from statistics import mean

    import matplotlib.figure

    runs = list(renderer.LABELS)[:2]
    monkeypatch.setattr(renderer, "VIEWS", ("luna",))
    monkeypatch.setattr(renderer, "DATASETS", {"google_patents": "Chemical Patents"})
    monkeypatch.setattr(renderer, "SETTINGS", ("zero_shot",))
    aggregates, points = [], []
    for family, metrics in renderer.RANK_FAMILIES.items():
        for category in renderer.CATEGORIES if family == "terminology" else ("not_applicable",):
            for metric in metrics:
                for index, run in enumerate(runs):
                    values = (1, 3, 100) if index == 0 else (0, 2, 200)
                    available = metric not in renderer.TERMINOLOGY[3:]
                    row = {
                        "view": "luna" if family == "terminology" else "shared_general",
                        "category": category,
                        "dataset": "google_patents",
                        "setting": "zero_shot",
                        "run": run,
                        "model": renderer.LABELS[run],
                        "metric": metric,
                        "value": mean(values) if available else None,
                        "directions": "de-en;en-de;fr-en" if available else "",
                        "n_directions": 3 if available else 0,
                    }
                    aggregates.append(row)
                    if available:
                        points.extend(
                            {
                                **row,
                                "direction": direction,
                                "value": value,
                                "rows_scored": 10000 if direction == "fr-en" else 1,
                            }
                            for direction, value in zip(
                                ("de-en", "en-de", "fr-en"), values, strict=True
                            )
                        )
    selected = renderer.build_statistic_aggregates(aggregates, points, statistic)
    rows, _ = renderer.build_mixed_rank_rows(selected, runs)
    assert all(row["run"] == runs[winner] for row in rows if row["mixed_rank"] == 1)
    assert selected[0]["value"] == (3 if statistic == "median" else 100)
    assert all(
        row["value"] is None for row in selected if row["metric"] in renderer.TERMINOLOGY[3:]
    )
    assert aggregates[0]["value"] == mean((1, 3, 100))
    if statistic == "top":
        assert selected[0]["top_directions"] == "fr-en"
    with pytest.raises(ValueError, match="identical common direction support"):
        renderer.build_statistic_aggregates(aggregates, points[1:], statistic)
    chosen = tmp_path / "figures/chosen/README.md"
    chosen.parent.mkdir(parents=True)
    chosen.write_text("Original mean scorecards", encoding="utf-8")
    checked = []

    def check(figure, path, **kwargs):
        if path.suffix != ".png":
            return
        mode = "median" if "median" in path.parts else "top"
        expected_run = runs[0 if mode == "median" else 1]
        axis = figure.axes[0]
        assert axis.get_yticklabels()[0].get_text() == renderer.LABELS[expected_run]
        column = [label.get_text() for label in axis.get_xticklabels()].index("COMET")
        value = next(text.get_text() for text in axis.texts if text.get_position() == (column, 0))
        assert float(value) == (3 if mode == "median" else 200)
        checked.append(path)

    monkeypatch.setattr(matplotlib.figure.Figure, "savefig", check)
    saved = renderer.write_rank_statistic_reports(tmp_path, aggregates, points, runs)
    assert len(saved) == len(checked) == 4
    assert chosen.read_text(encoding="utf-8") == "Original mean scorecards"
    for mode in ("median", "top"):
        folder = tmp_path / "tables/rankings" / mode
        assert (folder / "rankings.md").is_file() and (folder / "model_ranks.csv").is_file()
        assert "stratum" in (folder / "rankings.md").read_text(encoding="utf-8")


def test_mixed_rank_balances_families_groups_and_preserves_ties(monkeypatch):
    runs = list(renderer.LABELS)[:2]
    monkeypatch.setattr(renderer, "VIEWS", ("luna",))
    monkeypatch.setattr(renderer, "DATASETS", {"google_patents": "Chemical Patents"})
    monkeypatch.setattr(renderer, "SETTINGS", ("zero_shot",))
    aggregates = []
    for family, metrics in renderer.RANK_FAMILIES.items():
        for category in renderer.CATEGORIES if family == "terminology" else ("not_applicable",):
            for metric in metrics:
                for index, run in enumerate(runs):
                    value = 2 - index if family == "semantic" else 1 + index
                    if family == "terminology":
                        value = 5
                    aggregates.append(
                        {
                            "view": "luna" if family == "terminology" else "shared_general",
                            "category": category,
                            "dataset": "google_patents",
                            "setting": "zero_shot",
                            "run": run,
                            "model": renderer.LABELS[run],
                            "metric": metric,
                            "value": None if metric in renderer.TERMINOLOGY[3:] else value,
                        }
                    )
    rows, components = renderer.build_mixed_rank_rows(aggregates, runs)
    assert len(rows) == 4
    assert all(row["mixed_rank"] == 1 and row["mixed_mean_rank"] == 1.5 for row in rows)
    assert all(row["terminology_mean_rank"] == 1.5 for row in rows)
    assert len(components) == 2 * (len(renderer.GENERAL) + 3 * 3)
    assert not any("success_rate" in key for row in rows for key in row)
    assert next(row for row in rows if row["run"] == runs[0])["semantic_mean_rank"] == 1
    language_codes = ("de", "fr")
    language_aggregates = [
        {**row, "run": language_codes[runs.index(row["run"])]} for row in aggregates
    ]
    languages, _ = renderer.build_mixed_rank_rows(
        language_aggregates,
        language_codes,
        labels=renderer.LANGUAGE_LABELS,
        datasets=("google_patents",),
        views=("luna",),
    )
    assert {row["model"] for row in languages} == {"German", "French"}
    assert all(row["mixed_rank"] == 1 for row in languages)
    for row in aggregates:
        if row["metric"] not in renderer.TERMINOLOGY[:3]:
            continue
        index = runs.index(row["run"])
        if row["category"] != "all_terms" and row["metric"] != "target_term_coverage":
            row["value"] = None
        else:
            row["value"] = 1 + index if row["category"] == "llm_enriched" else 2 - index
    weighted, _ = renderer.build_mixed_rank_rows(aggregates, runs)
    first = next(row for row in weighted if row["run"] == runs[0])
    assert first["terminology_mean_rank"] == pytest.approx(4 / 3)
    assert first["mixed_mean_rank"] == pytest.approx(13 / 9)
    assert first["mixed_rank"] == 1
    aggregates[0]["value"] = None
    with pytest.raises(ValueError, match="Incomplete model support"):
        renderer.build_mixed_rank_rows(aggregates, runs)


def test_correlation_colors_expand_high_coefficients_without_changing_their_scale():
    import numpy as np

    norm = renderer.correlation_color_norm()
    coefficients = np.array([-1, -0.999, -0.99, -0.98, -0.8, 0, 0.8, 0.98, 0.99, 0.999, 1])
    colors = norm(coefficients)
    assert colors[0] == 0 and colors[-1] == 1 and norm(0) == 0.5
    assert np.all(np.diff(colors) > 0)
    np.testing.assert_allclose(norm(-coefficients), 1 - colors, atol=1e-12)
    np.testing.assert_allclose(norm.inverse(colors), coefficients, atol=1e-12)
    assert norm(0.99) - norm(0.98) > 5 * (0.99 - 0.98) / 2
    assert np.ma.getmaskarray(norm(np.ma.masked_invalid([np.nan, 0.99]))).tolist() == [True, False]


def test_correlations_match_model_rankings_and_cross_term_groups():
    runs = list(renderer.LABELS)
    summaries = {
        (view, category, run): {
            "dataset_settings": {
                dataset: {
                    setting: {
                        "by_direction": {
                            "de-en": result(index + 1),
                            "en-de": result(100 - index),
                        }
                    }
                    for setting in renderer.SETTINGS
                }
                for dataset in renderer.DATASETS
            }
        }
        for view in renderer.VIEWS
        for category in renderer.CATEGORIES
        for index, run in enumerate(runs)
    }
    del summaries[("luna", "externally_verified", runs[0])]["dataset_settings"]["google_patents"][
        "few_shot"
    ]["by_direction"]["en-de"]
    rows = renderer.build_metric_correlations(summaries, runs)
    selected = [
        row
        for row in rows
        if row["view"] == "luna"
        and row["dataset"] == "google_patents"
        and row["metric_x"] == row["metric_y"] == "target_term_coverage"
        and row["category_x"] == "all_terms"
        and row["category_y"] == "llm_enriched"
    ]
    assert len(selected) == 4
    assert all(row["directions"] == "de-en" for row in selected)
    assert all(row["correlation"] == pytest.approx(1) for row in selected)
    assert any(row["state"] == "constant_scores" and row["correlation"] is None for row in rows)


def test_all_dataset_correlations_average_datasets_before_correlating(monkeypatch):
    from scipy.stats import pearsonr

    monkeypatch.setattr(renderer, "GENERAL", ("comet", "bleurt"))
    monkeypatch.setattr(renderer, "TERMINOLOGY", ())
    monkeypatch.setattr(renderer, "VIEWS", ("luna",))
    runs = list(renderer.LABELS)[:4]
    scores = ([0, 1, 2, 3], [3, 0, 1, 2], [1, 3, 2, 0])
    summaries = {}
    for category in renderer.CATEGORIES:
        for index, run in enumerate(runs):
            datasets = {}
            for dataset_index, dataset in enumerate(renderer.DATASETS):
                directions = {}
                for direction in range(dataset_index + 1):
                    directions[str(direction)] = {
                        "mean_metrics": {"comet": scores[dataset_index][index], "bleurt": index**2},
                        "metric_status": {
                            metric: {"state": "completed", "rows_scored": 1}
                            for metric in renderer.GENERAL
                        },
                    }
                datasets[dataset] = {
                    setting: {"by_direction": directions.copy()} for setting in renderer.SETTINGS
                }
            summaries[("luna", category, run)] = {"dataset_settings": datasets}
    rows = renderer.build_metric_correlations(summaries, runs)
    overall = next(
        row
        for row in rows
        if row["dataset"] == "all_datasets"
        and row["metric_x"] == "comet"
        and row["metric_y"] == "bleurt"
        and row["method"] == "pearson"
    )
    expected = pearsonr([sum(values) / 3 for values in zip(*scores, strict=True)], [0, 1, 4, 9])
    assert overall["correlation"] == pytest.approx(expected.statistic)
    assert overall["n_models"] == 4 and overall["n_datasets"] == 3
    assert overall["n_directions"] == 6 and overall["directions"] == ""
    missing = summaries[("luna", "all_terms", runs[0])]["dataset_settings"]["jrc_articles"]
    missing["few_shot"]["by_direction"] = {}
    rows = renderer.build_metric_correlations(summaries, runs)
    assert all(row["correlation"] is None for row in rows if row["dataset"] == "all_datasets")


def test_distinct_columns_minimize_absolute_correlation_with_complete_support():
    metrics = ("bleu", "chrf", "comet", "cometkiwi_qe", "xcomet_xl")
    rows = []
    for index, metric_x in enumerate(metrics):
        for metric_y in metrics[index:]:
            for method in ("pearson", "spearman"):
                rows.append(
                    {
                        "view": "luna",
                        "dataset": "all_datasets",
                        "setting": "zero_shot",
                        "method": method,
                        "category_x": "not_applicable",
                        "metric_x": metric_x,
                        "category_y": "not_applicable",
                        "metric_y": metric_y,
                        "correlation": 1
                        if metric_x == metric_y or "chrf" in (metric_x, metric_y)
                        else -0.1,
                    }
                )
    selected = renderer.select_distinct_metric_columns(rows)
    assert {row["metric"] for row in selected} == set(metrics) - {"chrf"}
    assert all(row["mean_absolute_correlation"] == pytest.approx(0.1) for row in selected)
    assert all(row["n_contexts"] == 2 for row in selected)
    assert all(row["n_candidate_sets"] == 5 for row in selected)
    with pytest.raises(ValueError, match="Duplicate"):
        renderer.select_distinct_metric_columns([*rows, rows[0]])
    with pytest.raises(ValueError, match="No fully supported"):
        renderer.select_distinct_metric_columns(rows, count=6)


def test_bubble_area_is_proportional_to_bleu():
    assert renderer.bubble_area(40) == 2 * renderer.bubble_area(20)
    assert renderer.bubble_area(0) == 0
    with pytest.raises(ValueError):
        renderer.bubble_area(float("nan"))


@pytest.mark.parametrize(
    ("name", "folder"),
    [
        ("translation_quality_google_patents", "translation_quality"),
        ("learned_metric_comparison", "translation_quality"),
        ("terminology_coverage_luna", "terminology/overview"),
        ("quality_terminology_bubbles_google_patents_zero_shot", "bubbles/all_terms/luna"),
        ("prompting_comet_difference", "prompting"),
        ("translation_coverage", "coverage"),
        ("performance_distributions_zero_shot", "distributions"),
    ],
)
def test_figures_are_grouped_by_type(name, folder):
    assert renderer.figure_folder(name).as_posix() == folder


@pytest.mark.parametrize("view", renderer.VIEWS)
@pytest.mark.parametrize("category", renderer.CATEGORIES)
def test_bubble_axes_and_area_use_identical_direction_support(view, category):
    runs = list(renderer.LABELS)
    summaries = {
        (view, category, run): {
            "dataset_settings": {
                "google_patents": {
                    setting: {"by_direction": {"de-en": result(20), "en-de": result(80)}}
                    for setting in renderer.SETTINGS
                }
            }
        }
        for run in runs
    }
    groups = summaries[(view, category, runs[0])]["dataset_settings"]["google_patents"]
    groups["few_shot"]["by_direction"]["de-en"]["metric_status"]["comet"] = {"state": "not_run"}
    rows = renderer.build_bubble_rows(summaries, runs, view=view, category=category)
    assert len(rows) == len(runs) * len(renderer.SETTINGS)
    assert all(row["view"] == view and row["category"] == category for row in rows)
    assert all(row["directions"] == "en-de" for row in rows)
    assert all(row["comet"] == row["target_term_coverage"] == row["bleu"] == 80 for row in rows)


def test_distribution_points_average_models_and_share_term_subset_support():
    runs = list(renderer.LABELS)
    summaries = {
        (view, category, run): {
            "dataset_settings": {
                dataset: {
                    setting: {"by_direction": {"de-en": result(20), "en-de": result(80)}}
                    for setting in renderer.SETTINGS
                }
                for dataset in renderer.DATASETS
            }
        }
        for view in renderer.VIEWS
        for category in renderer.CATEGORIES
        for run in runs
    }
    group = summaries[("luna", "externally_verified", runs[0])]["dataset_settings"][
        "google_patents"
    ]["few_shot"]["by_direction"]
    del group["de-en"]
    rows = renderer.build_distribution_rows(summaries, runs)
    selected = [row for row in rows if row["view"] == "luna" and row["dataset"] == "google_patents"]
    assert len(selected) == 6
    assert all(row["direction"] == "en-de" and row["n_models"] == len(runs) for row in selected)
    assert all(row["target_term_coverage"] == 80 for row in selected)


def test_density_region_skips_small_or_degenerate_samples():
    import numpy as np

    grid = np.linspace(-5, 5, 100)
    assert renderer.density_region([[0, 0]] * 5, grid, grid) is None
    assert renderer.density_region([[value, value] for value in range(10)], grid, grid) is None


@pytest.mark.parametrize("metric", renderer.TERMINOLOGY[3:])
def test_figures_hide_only_unavailable_success_rates(metric):
    assert not renderer.show_metric_in_figure(metric, [None, None])
    assert not renderer.show_metric_in_figure(metric, [float("nan"), float("inf")])
    assert renderer.show_metric_in_figure(metric, [None, 0])
    assert renderer.show_metric_in_figure(metric, [0.5, None])
    assert renderer.show_metric_in_figure("target_term_coverage", [None, None])


def test_density_region_contains_requested_kde_mass():
    import numpy as np

    points = np.random.default_rng(42).normal(size=(100, 2))
    grid = np.linspace(-5, 5, 200)
    density, threshold = renderer.density_region(points, grid, grid, mass=0.5)
    mass = density[density >= threshold].sum() * (grid[1] - grid[0]) ** 2
    assert 0.5 <= mass < 0.51
