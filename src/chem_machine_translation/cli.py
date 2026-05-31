from __future__ import annotations

import sys
from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console
from rich.table import Table

from chem_machine_translation.comparison import (
    timestamped_report_path,
    write_csv,
    write_jsonl,
)
from chem_machine_translation.config import DEFAULT_MAX_INPUT_TOKENS, DEFAULT_MODEL, load_settings
from chem_machine_translation.datasets import DATASET_REPOS, DatasetName, iter_documents
from chem_machine_translation.huggingface_upload import (
    is_huggingface_upload_configured,
    upload_report_to_huggingface,
)
from chem_machine_translation.text import approximate_token_count
from chem_machine_translation.translators import build_translator

DEFAULT_TARGET_LANGUAGES = ["French", "German", "Portuguese", "Chinese", "Spanish"]

app = typer.Typer(
    name="chem-translate",
    help="Chemistry-aware document translation experiments.",
    no_args_is_help=True,
)
datasets_app = typer.Typer(help="Inspect and sample configured datasets.", hidden=True)
app.add_typer(datasets_app, name="datasets")

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

console = Console()


def _parse_dataset_name(dataset: str) -> DatasetName:
    if dataset not in DATASET_REPOS:
        allowed = ", ".join(DATASET_REPOS)
        raise typer.BadParameter(f"Unknown dataset '{dataset}'. Use one of: {allowed}")
    return dataset  # type: ignore[return-value]


def _select_target_languages(target_languages: list[str] | None) -> list[str]:
    return target_languages or DEFAULT_TARGET_LANGUAGES


def _select_datasets(datasets: list[str] | None) -> list[DatasetName]:
    return [_parse_dataset_name(dataset) for dataset in (datasets or ["dolma", "chemrxiv"])]


def _add_document_sample_rows(
    table: Table,
    dataset_name: DatasetName,
    limit: int,
    skip: int,
    split: str,
    min_input_tokens: int,
    max_input_tokens: int,
    max_rows_scanned: int,
) -> None:
    for document in iter_documents(
        dataset_name=dataset_name,
        split=split,
        limit=limit,
        skip=skip,
        min_input_tokens=min_input_tokens,
        max_input_tokens=max_input_tokens,
        max_rows_scanned=max_rows_scanned,
    ):
        table.add_row(
            document.dataset,
            document.source_id,
            str(approximate_token_count(document.text)),
            document.text[:500],
        )


@datasets_app.command("list")
def list_datasets() -> None:
    """List supported dataset aliases."""

    table = Table(title="Supported Datasets")
    table.add_column("Alias")
    table.add_column("Hugging Face repo")
    for alias, repo in DATASET_REPOS.items():
        table.add_row(alias, repo)
    console.print(table)


@app.command("sample")
def sample(
    datasets: Annotated[
        list[str] | None,
        typer.Option("--dataset", "-d", help="Dataset alias. Repeatable; defaults to both."),
    ] = None,
    limit: Annotated[int, typer.Option("--limit", "-n", help="Documents per dataset.")] = 10,
    min_input_tokens: Annotated[
        int,
        typer.Option(help="Minimum approximate tokens per document.", rich_help_panel="Advanced"),
    ] = 192,
    max_input_tokens: Annotated[
        int,
        typer.Option(help="Maximum approximate tokens per document.", rich_help_panel="Advanced"),
    ] = DEFAULT_MAX_INPUT_TOKENS,
    max_rows_scanned: Annotated[
        int,
        typer.Option(help="Maximum rows to scan per dataset.", rich_help_panel="Advanced"),
    ] = 100_000,
) -> None:
    """Preview English source documents that match the token window."""

    table = Table(title="Sampled Source Documents")
    table.add_column("Dataset")
    table.add_column("Source ID", overflow="fold")
    table.add_column("Tokens", justify="right")
    table.add_column("Text", overflow="fold")

    for dataset_name in _select_datasets(datasets):
        _add_document_sample_rows(
            table=table,
            dataset_name=dataset_name,
            limit=limit,
            skip=0,
            split="train",
            min_input_tokens=min_input_tokens,
            max_input_tokens=max_input_tokens,
            max_rows_scanned=max_rows_scanned,
        )

    console.print(table)


@datasets_app.command("sample")
def sample_dataset(
    dataset: Annotated[str, typer.Argument(help="Dataset alias: dolma or chemrxiv")],
    limit: Annotated[int, typer.Option(help="Number of documents to sample")] = 10,
    skip: Annotated[int, typer.Option(help="Rows to skip before sampling")] = 0,
    split: Annotated[str, typer.Option(help="Dataset split")] = "train",
    min_input_tokens: Annotated[
        int, typer.Option(help="Minimum approximate tokens per sampled document")
    ] = 192,
    max_input_tokens: Annotated[
        int, typer.Option(help="Maximum approximate tokens per sampled document")
    ] = DEFAULT_MAX_INPUT_TOKENS,
    max_rows_scanned: Annotated[
        int, typer.Option(help="Maximum rows to scan while looking for matches")
    ] = 100_000,
) -> None:
    """Preview normalized documents that would be translated."""

    dataset_name = _parse_dataset_name(dataset)
    table = Table(title=f"Sample: {dataset_name}")
    table.add_column("Dataset")
    table.add_column("Source ID", overflow="fold")
    table.add_column("Tokens", justify="right")
    table.add_column("Text", overflow="fold")

    _add_document_sample_rows(
        table=table,
        dataset_name=dataset_name,
        split=split,
        limit=limit,
        skip=skip,
        min_input_tokens=min_input_tokens,
        max_input_tokens=max_input_tokens,
        max_rows_scanned=max_rows_scanned,
    )

    console.print(table)


@app.command("translate")
def translate(
    target_languages: Annotated[
        list[str] | None,
        typer.Option(
            "--language",
            "-l",
            help="Target language. Repeatable; defaults to the configured 5 languages.",
        ),
    ] = None,
    datasets: Annotated[
        list[str] | None,
        typer.Option("--dataset", "-d", help="Dataset alias. Repeatable; defaults to both."),
    ] = None,
    strategy: Annotated[
        str,
        typer.Option(
            help="Translation strategy: dry-run, openai, or openai-agentic",
            rich_help_panel="Translation",
        ),
    ] = "openai-agentic",
    dry_run: Annotated[
        bool,
        typer.Option(
            "--dry-run",
            help="Validate loading/reporting without calling an LLM.",
            rich_help_panel="Translation",
        ),
    ] = False,
    limit_per_dataset: Annotated[
        int, typer.Option("--limit", "-n", help="English source documents per dataset.")
    ] = 10,
    model: Annotated[str, typer.Option(help="OpenAI model name")] = DEFAULT_MODEL,
    output: Annotated[
        Path | None,
        typer.Option("--output", "-o", help="Report output path"),
    ] = None,
    output_format: Annotated[
        str,
        typer.Option(help="Report format: jsonl or csv.", rich_help_panel="Output"),
    ] = "jsonl",
    upload: Annotated[
        bool,
        typer.Option(
            "--upload/--no-upload",
            help="Upload report to Hugging Face when configured in .env.",
            rich_help_panel="Output",
        ),
    ] = True,
    source_language: Annotated[
        str, typer.Option(help="Source language.", rich_help_panel="Advanced")
    ] = "English",
    skip: Annotated[
        int, typer.Option(help="Rows to skip before sampling.", rich_help_panel="Advanced")
    ] = 0,
    split: Annotated[
        str,
        typer.Option(help="Dataset split.", rich_help_panel="Advanced"),
    ] = "train",
    temperature: Annotated[
        float, typer.Option(help="Generation temperature.", rich_help_panel="Advanced")
    ] = 0.0,
    max_review_rounds: Annotated[
        int,
        typer.Option(
            help="Maximum review/revision rounds for agentic strategies.",
            rich_help_panel="Advanced",
        ),
    ] = 3,
    min_input_tokens: Annotated[
        int,
        typer.Option(
            help="Minimum approximate tokens per source document.",
            rich_help_panel="Advanced",
        ),
    ] = 192,
    max_input_tokens: Annotated[
        int,
        typer.Option(
            help="Maximum approximate tokens per source document.",
            rich_help_panel="Advanced",
        ),
    ] = DEFAULT_MAX_INPUT_TOKENS,
    max_rows_scanned: Annotated[
        int,
        typer.Option(
            help="Maximum rows to scan per dataset while looking for matches.",
            rich_help_panel="Advanced",
        ),
    ] = 100_000,
) -> None:
    """Translate filtered English chemistry documents."""

    settings = load_settings()
    selected_strategy = "dry-run" if dry_run else strategy
    translator = build_translator(
        strategy=selected_strategy,
        settings=settings,
        model=model,
        temperature=temperature,
        max_rounds=max_review_rounds,
    )
    results = []

    selected_datasets = _select_datasets(datasets)
    selected_languages = _select_target_languages(target_languages)
    for dataset_name in selected_datasets:
        documents = iter_documents(
            dataset_name=dataset_name,
            split=split,
            limit=limit_per_dataset,
            skip=skip,
            min_input_tokens=min_input_tokens,
            max_input_tokens=max_input_tokens,
            max_rows_scanned=max_rows_scanned,
        )
        for document in documents:
            for target_language in selected_languages:
                results.append(
                    translator.translate(
                        document=document,
                        target_language=target_language,
                        source_language=source_language,
                    )
                )

    reports_dir = settings.reports_dir
    if output_format == "jsonl":
        output_path = output or timestamped_report_path(reports_dir, "jsonl")
        write_jsonl(results, output_path)
    elif output_format == "csv":
        output_path = output or timestamped_report_path(reports_dir, "csv")
        write_csv(results, output_path)
    else:
        raise typer.BadParameter("output-format must be jsonl or csv")

    console.print(f"Wrote {len(results)} translations to [bold]{output_path}[/bold]")
    if upload and is_huggingface_upload_configured(settings):
        upload_url = upload_report_to_huggingface(settings, output_path)
        console.print(f"Uploaded report to Hugging Face: [bold]{upload_url}[/bold]")


@app.command("translate-sample", hidden=True)
def translate_sample(
    target_languages: Annotated[
        list[str] | None,
        typer.Option("--target-language", help="Target language. Repeatable."),
    ] = None,
    datasets: Annotated[list[str] | None, typer.Option("--dataset")] = None,
    strategy: Annotated[str, typer.Option()] = "dry-run",
    limit_per_dataset: Annotated[int, typer.Option()] = 10,
) -> None:
    """Legacy alias for translate."""

    translate(
        target_languages=target_languages,
        datasets=datasets,
        strategy=strategy,
        dry_run=False,
        limit_per_dataset=limit_per_dataset,
    )


if __name__ == "__main__":
    app()
