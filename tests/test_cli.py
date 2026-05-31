from chem_machine_translation.cli import (
    DEFAULT_TARGET_LANGUAGES,
    _select_datasets,
    _select_target_languages,
)


def test_default_target_languages_cover_requested_languages() -> None:
    assert DEFAULT_TARGET_LANGUAGES == [
        "French",
        "German",
        "Portuguese",
        "Chinese",
        "Spanish",
    ]


def test_select_target_languages_allows_override() -> None:
    assert _select_target_languages(["German"]) == ["German"]


def test_select_datasets_defaults_to_both_configured_datasets() -> None:
    assert _select_datasets(None) == ["dolma", "chemrxiv"]
