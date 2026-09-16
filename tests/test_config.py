from chem_machine_translation.config import (
    DEFAULT_LLM_MAX_OUTPUT_TOKENS,
    DEFAULT_MODEL,
    load_settings,
)


def clear_explicit_llm_runtime_overrides(monkeypatch) -> None:
    for name in (
        "CHEM_MT_LLM_API_MODE",
        "CHEM_MT_LLM_THINKING",
        "CHEM_MT_LLM_REASONING_EFFORT",
        "OPENCODE_API_MODE",
        "OPENCODE_THINKING",
        "OPENCODE_REASONING_EFFORT",
    ):
        monkeypatch.delenv(name, raising=False)


def test_load_settings_uses_opencode_provider_aliases(monkeypatch) -> None:
    clear_explicit_llm_runtime_overrides(monkeypatch)
    monkeypatch.setenv("OPENAI_API_KEY", "")
    monkeypatch.delenv("OPENAI_BASE_URL", raising=False)
    monkeypatch.delenv("CHEM_MT_MODEL", raising=False)
    monkeypatch.setenv("OPENCODE_API_KEY", "test-opencode-key")
    monkeypatch.setenv("OPENCODE_BASE_URL", "https://example.test/v1")
    monkeypatch.setenv("OPENCODE_MODEL", "deepseek/deepseek-v4-flash-0731")

    settings = load_settings()

    assert not settings.openai_api_key
    assert settings.openai_base_url is None
    assert settings.opencode_api_key == "test-opencode-key"
    assert settings.opencode_base_url == "https://example.test/v1"
    assert settings.default_model == "deepseek/deepseek-v4-flash-0731"
    assert settings.llm_api_mode == "chat_completions"
    assert settings.llm_thinking == "disabled"
    assert settings.llm_reasoning_effort is None
    assert settings.llm_max_output_tokens == DEFAULT_LLM_MAX_OUTPUT_TOKENS


def test_load_settings_prefers_openai_and_chem_mt_names(monkeypatch) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "test-openai-key")
    monkeypatch.setenv("OPENAI_BASE_URL", "https://openai-compatible.test/v1")
    monkeypatch.setenv("CHEM_MT_MODEL", "gpt-4.1-mini")
    monkeypatch.setenv("OPENCODE_API_KEY", "test-opencode-key")
    monkeypatch.setenv("OPENCODE_BASE_URL", "https://example.test/v1")
    monkeypatch.setenv("OPENCODE_MODEL", "deepseek/deepseek-v4-flash-0731")

    settings = load_settings()

    assert settings.openai_api_key == "test-openai-key"
    assert settings.openai_base_url == "https://openai-compatible.test/v1"
    assert settings.opencode_api_key == "test-opencode-key"
    assert settings.opencode_base_url == "https://example.test/v1"
    assert settings.default_model == "gpt-4.1-mini"
    assert settings.llm_api_mode == "responses"
    assert settings.llm_thinking is None


def test_load_settings_pairs_opencode_key_with_opencode_base_url(monkeypatch) -> None:
    clear_explicit_llm_runtime_overrides(monkeypatch)
    monkeypatch.setenv("OPENAI_API_KEY", "test-openai-key")
    monkeypatch.delenv("OPENAI_BASE_URL", raising=False)
    monkeypatch.setenv("OPENCODE_API_KEY", "test-opencode-key")
    monkeypatch.setenv("OPENCODE_BASE_URL", "https://opencode.test/v1")

    settings = load_settings()

    assert settings.openai_api_key == "test-openai-key"
    assert settings.openai_base_url is None
    assert settings.opencode_api_key == "test-opencode-key"
    assert settings.opencode_base_url == "https://opencode.test/v1"
    assert settings.llm_api_mode == "chat_completions"
    assert settings.llm_thinking == "disabled"


def test_load_settings_uses_explicit_llm_api_mode(monkeypatch) -> None:
    monkeypatch.setenv("OPENCODE_BASE_URL", "https://opencode.test/v1")
    monkeypatch.setenv("CHEM_MT_LLM_API_MODE", "responses")

    settings = load_settings()

    assert settings.llm_api_mode == "responses"


def test_load_settings_uses_explicit_llm_runtime_settings(monkeypatch) -> None:
    monkeypatch.setenv("CHEM_MT_LLM_MAX_OUTPUT_TOKENS", "512")
    monkeypatch.setenv("CHEM_MT_LLM_THINKING", "enabled")
    monkeypatch.setenv("CHEM_MT_LLM_REASONING_EFFORT", "low")

    settings = load_settings()

    assert settings.llm_max_output_tokens == 512
    assert settings.llm_thinking == "enabled"
    assert settings.llm_reasoning_effort == "low"


def test_load_settings_keeps_default_model_without_overrides(monkeypatch) -> None:
    monkeypatch.delenv("CHEM_MT_MODEL", raising=False)
    monkeypatch.delenv("OPENCODE_MODEL", raising=False)

    settings = load_settings()

    assert settings.default_model == DEFAULT_MODEL
