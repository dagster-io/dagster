from __future__ import annotations

from shared.resources import (
    CatalogCoach,
    EmbeddedLLMResource,
    OllamaLLMResource,
    build_llm_resource,
)


def test_build_llm_resource_defaults_to_embedded_backend(monkeypatch) -> None:
    monkeypatch.delenv("LLM_BACKEND", raising=False)

    resource = build_llm_resource(
        CatalogCoach,
        model_env_var="HARBOR_OUTFITTERS_MODEL",
        default_model_name="qwen2.5:0.5b",
        runtime_dependency_package="catalog_coach_runtime",
    )

    assert isinstance(resource, EmbeddedLLMResource)
    assert "Trail Socks" in resource.generate(
        (
            "Write cleaner catalog copy for Trail Socks. "
            "Use category outdoor gear. "
            "Context: Product facts: Product: Trail Socks. "
            "Category: outdoor gear. "
            "Description: Merino blend trail socks for weekend hikes."
        )
    )
    assert resource.runtime_metadata()["llm_backend"] == "embedded"


def test_build_llm_resource_can_use_ollama_backend(monkeypatch) -> None:
    monkeypatch.setenv("LLM_BACKEND", "ollama")
    monkeypatch.setenv("OLLAMA_BASE_URL", "http://localhost:11434")

    resource = build_llm_resource(
        CatalogCoach,
        model_env_var="HARBOR_OUTFITTERS_MODEL",
        default_model_name="qwen2.5:0.5b",
        runtime_dependency_package="catalog_coach_runtime",
    )

    assert isinstance(resource, OllamaLLMResource)
    assert resource.base_url == "http://localhost:11434"
    assert resource.runtime_metadata()["llm_backend"] == "ollama"
