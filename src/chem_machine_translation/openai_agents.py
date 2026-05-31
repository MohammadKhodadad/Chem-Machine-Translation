from __future__ import annotations

import json
import re

from openai import OpenAI

from chem_machine_translation.prompts import (
    REVIEWER_SYSTEM_PROMPT,
    TRANSLATOR_SYSTEM_PROMPT,
    build_initial_translation_prompt,
    build_review_prompt,
    build_revision_prompt,
)
from chem_machine_translation.schemas import Document, TranslationReview

_JSON_OBJECT_RE = re.compile(r"\{.*\}", re.DOTALL)


class OpenAITranslationAgents:
    """OpenAI-backed translator and reviewer agents for chemistry text."""

    def __init__(
        self,
        client: OpenAI,
        model: str,
        temperature: float = 0.0,
    ) -> None:
        self.client = client
        self.model = model
        self.temperature = temperature

    def translate_once(
        self,
        document: Document,
        target_language: str,
        source_language: str,
    ) -> str:
        return self._generate_text(
            system_prompt=TRANSLATOR_SYSTEM_PROMPT,
            user_prompt=build_initial_translation_prompt(
                document=document,
                target_language=target_language,
                source_language=source_language,
            ),
            temperature=self.temperature,
        )

    def revise(
        self,
        document: Document,
        current_translation: str,
        review: TranslationReview,
        target_language: str,
        source_language: str,
    ) -> str:
        return self._generate_text(
            system_prompt=TRANSLATOR_SYSTEM_PROMPT,
            user_prompt=build_revision_prompt(
                document=document,
                current_translation=current_translation,
                review=review,
                target_language=target_language,
                source_language=source_language,
            ),
            temperature=self.temperature,
        )

    def review(
        self,
        document: Document,
        candidate_translation: str,
        target_language: str,
        source_language: str,
    ) -> TranslationReview:
        review_text = self._generate_text(
            system_prompt=REVIEWER_SYSTEM_PROMPT,
            user_prompt=build_review_prompt(
                document=document,
                candidate_translation=candidate_translation,
                target_language=target_language,
                source_language=source_language,
            ),
            temperature=0.0,
        )
        return parse_translation_review(review_text)

    def translate_with_review(
        self,
        document: Document,
        target_language: str,
        source_language: str,
        max_rounds: int = 3,
    ) -> tuple[str, TranslationReview, int, list[str]]:
        if max_rounds < 1:
            raise ValueError("max_rounds must be at least 1.")

        translation = self.translate_once(
            document=document,
            target_language=target_language,
            source_language=source_language,
        )
        notes: list[str] = []

        for round_number in range(1, max_rounds + 1):
            review = self.review(
                document=document,
                candidate_translation=translation,
                target_language=target_language,
                source_language=source_language,
            )
            notes.append(format_review_note(round_number, review))
            if review.approved or round_number == max_rounds:
                return translation, review, round_number, notes

            translation = self.revise(
                document=document,
                current_translation=translation,
                review=review,
                target_language=target_language,
                source_language=source_language,
            )

        return translation, review, max_rounds, notes

    def _generate_text(self, system_prompt: str, user_prompt: str, temperature: float) -> str:
        response = self.client.responses.create(
            model=self.model,
            temperature=temperature,
            input=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        )
        return response.output_text.strip()


def parse_translation_review(review_text: str) -> TranslationReview:
    match = _JSON_OBJECT_RE.search(review_text)
    payload = json.loads(match.group(0) if match else review_text)

    return TranslationReview(
        approved=bool(payload.get("approved", False)),
        issues=[str(issue) for issue in payload.get("issues", [])],
        required_changes=[str(change) for change in payload.get("required_changes", [])],
        rationale=str(payload.get("rationale", "")),
    )


def format_review_note(round_number: int, review: TranslationReview) -> str:
    if review.approved:
        return f"Round {round_number}: approved. {review.rationale}".strip()

    issue_summary = "; ".join(review.issues) if review.issues else "No issues provided"
    return f"Round {round_number}: rejected. {issue_summary}".strip()
