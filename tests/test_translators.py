from chem_machine_translation.openai_agents import OpenAITranslationAgents, parse_translation_review
from chem_machine_translation.schemas import Document
from chem_machine_translation.translators import DryRunTranslator


def test_dry_run_translator_returns_source_text() -> None:
    document = Document(
        dataset="dolma",
        source_id="1",
        text="Preserve CO2 and Zr/ZIF-8 notation.",
        metadata={},
    )

    result = DryRunTranslator().translate(document, target_language="German")

    assert result.translated_text == document.text
    assert result.target_language == "German"
    assert result.strategy == "dry-run"


class _FakeResponse:
    def __init__(self, output_text: str) -> None:
        self.output_text = output_text


class _FakeResponses:
    def __init__(self, outputs: list[str]) -> None:
        self.outputs = outputs
        self.calls = []

    def create(self, **kwargs) -> _FakeResponse:
        self.calls.append(kwargs)
        return _FakeResponse(self.outputs.pop(0))


class _FakeClient:
    def __init__(self, outputs: list[str]) -> None:
        self.responses = _FakeResponses(outputs)


def test_parse_translation_review_from_json() -> None:
    review = parse_translation_review(
        '{"approved": false, "issues": ["CO2 changed"], '
        '"required_changes": ["Restore CO2"], "rationale": "Formula changed."}'
    )

    assert review.approved is False
    assert review.issues == ["CO2 changed"]
    assert review.required_changes == ["Restore CO2"]


def test_agentic_translation_revises_until_approved() -> None:
    document = Document(
        dataset="dolma",
        source_id="1",
        text="CO2 hydrogenation to formate at 80 °C.",
        metadata={},
    )
    client = _FakeClient(
        [
            "Bad German translation with changed CO2.",
            (
                '{"approved": false, "issues": ["CO2 was mistranslated"], '
                '"required_changes": ["Preserve CO2 exactly"], "rationale": "Formula changed."}'
            ),
            "Good German translation preserving CO2.",
            '{"approved": true, "issues": [], "required_changes": [], "rationale": "Accurate."}',
        ]
    )
    agents = OpenAITranslationAgents(client=client, model="gpt-4.1-mini")

    translation, review, rounds, notes = agents.translate_with_review(
        document=document,
        target_language="German",
        source_language="English",
        max_rounds=3,
    )

    assert translation == "Good German translation preserving CO2."
    assert review.approved is True
    assert rounds == 2
    assert "rejected" in notes[0]
    assert "approved" in notes[1]
