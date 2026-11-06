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


def test_language_figures_preserve_native_heatmaps_and_pair_model_coordinates(
    tmp_path, monkeypatch
):
    import matplotlib.figure
    import numpy as np
    from matplotlib.collections import PathCollection
    from matplotlib.markers import MarkerStyle

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
            axes = [axis for axis in figure.axes if axis.get_visible()]
            assert len(axes) == 2
            circle = MarkerStyle("o")
            circle_path = circle.get_path().transformed(circle.get_transform())
            assert all(handle.get_marker() == "o" for handle in figure.legends[0].legend_handles)
            for axis in axes:
                dots = [item for item in axis.collections if isinstance(item, PathCollection)]
                assert len(dots) == len(runs)
                for dot in dots:
                    np.testing.assert_array_equal(dot.get_paths()[0].vertices, circle_path.vertices)
                assert len({tuple(dot.get_facecolors()[0]) for dot in dots}) == len(runs)
                assert all(
                    item.get_offsets()[0][0] == pytest.approx(item.get_offsets()[0][1])
                    for item in dots
                )
        checked.append(path)

    monkeypatch.setattr(matplotlib.figure.Figure, "savefig", check)
    saved = renderer.write_language_analysis(tmp_path, points, runs)
    assert len(saved) == len(checked) == 12
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
