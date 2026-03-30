from __future__ import annotations

import errno
import fcntl
import json
from importlib import metadata as importlib_metadata
import os
from pathlib import Path
import re
import time
from typing import Any, Protocol
from urllib import error, request

import dagster as dg


class SupportsGenerate(Protocol):
    def generate(self, prompt: str) -> str:
        """Generate a text response for the provided prompt."""

    def runtime_metadata(self) -> dict[str, object]:
        """Return metadata describing the active model runtime."""


class BaseLLMResource(dg.ConfigurableResource):
    model_name: str
    system_prompt: str
    runtime_dependency_package: str | None = None

    def runtime_metadata(self) -> dict[str, object]:
        metadata: dict[str, object] = {
            "llm_model": self.model_name,
            "llm_backend": self.backend_name,
        }
        if self.runtime_dependency_package:
            metadata["runtime_dependency"] = _distribution_string(self.runtime_dependency_package)
        return metadata

    @property
    def backend_name(self) -> str:
        raise NotImplementedError


class OllamaLLMResource(BaseLLMResource):
    base_url: str = "http://localhost:11434"
    timeout_seconds: float = 300.0
    lock_path: str = "data/.ollama_generate.lock"
    lock_timeout_seconds: float = 900.0

    @property
    def backend_name(self) -> str:
        return "ollama"

    def generate(self, prompt: str) -> str:
        body = self._generate_with_lock(prompt)

        result = body.get("response")
        if not isinstance(result, str) or not result.strip():
            raise dg.Failure(
                description="Ollama returned an empty or invalid response payload.",
                metadata={
                    "model_name": self.model_name,
                    "base_url": self.base_url,
                    "response_body": json.dumps(body)[:500],
                },
            )

        return result.strip()

    def runtime_metadata(self) -> dict[str, object]:
        metadata = super().runtime_metadata()
        metadata["ollama_base_url"] = self.base_url
        return metadata

    def _post_json(self, path: str, payload: dict[str, Any]) -> dict[str, Any]:
        req = request.Request(
            f"{self.base_url.rstrip('/')}{path}",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        try:
            with request.urlopen(req, timeout=self.timeout_seconds) as response:
                raw_body = response.read().decode("utf-8")
        except error.HTTPError as exc:
            error_body = exc.read().decode("utf-8", errors="replace")
            raise dg.Failure(
                description="Ollama returned an HTTP error while generating text.",
                metadata={
                    "model_name": self.model_name,
                    "base_url": self.base_url,
                    "status_code": exc.code,
                    "response_body": error_body[:500],
                },
            ) from exc
        except (OSError, TimeoutError, error.URLError) as exc:
            raise dg.Failure(
                description="Could not reach the configured Ollama server.",
                metadata={
                    "model_name": self.model_name,
                    "base_url": self.base_url,
                    "error": str(exc),
                },
            ) from exc

        try:
            parsed = json.loads(raw_body)
        except ValueError as exc:
            raise dg.Failure(
                description="Ollama returned a non-JSON response.",
                metadata={
                    "model_name": self.model_name,
                    "base_url": self.base_url,
                    "response_body": raw_body[:500],
                },
            ) from exc

        if not isinstance(parsed, dict):
            raise dg.Failure(
                description="Ollama returned an unexpected response shape.",
                metadata={
                    "model_name": self.model_name,
                    "base_url": self.base_url,
                    "response_body": json.dumps(parsed)[:500],
                },
            )

        return parsed

    def _generate_with_lock(self, prompt: str) -> dict[str, Any]:
        lock_file = Path(self.lock_path)
        lock_file.parent.mkdir(parents=True, exist_ok=True)
        deadline = time.monotonic() + self.lock_timeout_seconds

        with lock_file.open("a+", encoding="utf-8") as handle:
            while True:
                try:
                    fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                    break
                except OSError as exc:
                    if exc.errno not in {errno.EACCES, errno.EAGAIN}:
                        raise
                    if time.monotonic() >= deadline:
                        raise dg.Failure(
                            description="Timed out waiting for the local Ollama request lock.",
                            metadata={
                                "model_name": self.model_name,
                                "lock_path": str(lock_file),
                                "lock_timeout_seconds": self.lock_timeout_seconds,
                            },
                        ) from exc
                    time.sleep(0.1)

            try:
                return self._post_json(
                    "/api/generate",
                    {
                        "model": self.model_name,
                        "system": self.system_prompt,
                        "prompt": prompt,
                        "stream": False,
                    },
                )
            finally:
                fcntl.flock(handle.fileno(), fcntl.LOCK_UN)


class EmbeddedLLMResource(BaseLLMResource):
    @property
    def backend_name(self) -> str:
        return "embedded"

    def generate(self, prompt: str) -> str:
        compact_prompt = _compact_text(prompt)
        prompt_lower = compact_prompt.lower()

        if "write cleaner catalog copy for" in prompt_lower:
            return _generate_catalog_copy(compact_prompt)
        if "review this transaction and return concise reasoning" in prompt_lower:
            return _generate_risk_rationale(compact_prompt)
        if "write a concise executive summary" in prompt_lower:
            return _generate_executive_summary(compact_prompt)

        return f"[embedded:{self.model_name}] {compact_prompt[:180]}"


def build_llm_resource(
    resource_cls: type[BaseLLMResource],
    *,
    model_env_var: str,
    default_model_name: str,
    runtime_dependency_package: str,
    legacy_model_env_var: str | None = None,
) -> BaseLLMResource:
    common_kwargs = {
        "model_name": _get_str_env(
            model_env_var,
            default=default_model_name,
            legacy_name=legacy_model_env_var,
        ),
        "system_prompt": _field_default(resource_cls, "system_prompt"),
        "runtime_dependency_package": runtime_dependency_package,
    }

    llm_backend = _get_str_env(
        "LLM_BACKEND",
        default="embedded",
        legacy_name="MULTI_TENANT_LLM_BACKEND",
    ).lower()
    if llm_backend in {"embedded", "builtin", "local"}:
        return EmbeddedLLMResource(**common_kwargs)
    if llm_backend == "ollama":
        return OllamaLLMResource(
            **common_kwargs,
            base_url=_get_str_env(
                "OLLAMA_BASE_URL",
                default="http://localhost:11434",
            ),
            timeout_seconds=_get_float_env(
                "OLLAMA_TIMEOUT_SECONDS",
                default=300.0,
            ),
            lock_path=_get_str_env(
                "OLLAMA_LOCK_PATH",
                default="data/.ollama_generate.lock",
            ),
            lock_timeout_seconds=_get_float_env(
                "OLLAMA_LOCK_TIMEOUT_SECONDS",
                default=900.0,
            ),
        )

    raise ValueError("LLM_BACKEND must be one of: embedded, builtin, local, ollama.")


def _field_default(resource_cls: type[BaseLLMResource], field_name: str) -> str:
    field = resource_cls.model_fields[field_name]
    default = field.default
    if not isinstance(default, str):
        raise TypeError(f"Expected default string value for field {field_name}.")
    return default


def _distribution_string(package_name: str) -> str:
    try:
        version = importlib_metadata.version(package_name)
    except importlib_metadata.PackageNotFoundError:
        return f"{package_name} (bundled in project)"
    return f"{package_name}=={version}"


def _get_str_env(name: str, *, default: str, legacy_name: str | None = None) -> str:
    value = os.getenv(name)
    if value:
        return value

    if legacy_name:
        legacy_value = os.getenv(legacy_name)
        if legacy_value:
            return legacy_value

    return default


def _get_float_env(name: str, *, default: float, legacy_name: str | None = None) -> float:
    raw_value = os.getenv(name)
    source_name = name
    if not raw_value and legacy_name:
        raw_value = os.getenv(legacy_name)
        source_name = legacy_name

    if not raw_value:
        return default

    try:
        return float(raw_value)
    except ValueError as exc:
        raise ValueError(f"Environment variable {source_name} must be a float.") from exc


def _compact_text(text: str) -> str:
    return " ".join(text.split())


def _search(pattern: str, text: str) -> str | None:
    match = re.search(pattern, text)
    if not match:
        return None
    value = match.group(1).strip()
    return value or None


def _sentence_case(text: str) -> str:
    stripped = text.strip().rstrip(".")
    if not stripped:
        return ""
    return stripped[0].lower() + stripped[1:]


def _generate_catalog_copy(prompt: str) -> str:
    name = _search(r"Write cleaner catalog copy for (.+?)\. Use category", prompt) or "This item"
    category = _search(r"Use category (.+?)\. Context:", prompt) or "general merchandise"
    description = _search(r"Description: (.+?)(?:\.\s|$)", prompt)

    description_line = _sentence_case(description or f"built for reliable {category} use")
    return (
        f"{name} brings practical {category} utility with {description_line}. "
        "Made to feel straightforward, durable, and ready for everyday use."
    )


def _generate_risk_rationale(prompt: str) -> str:
    triggered_rules = _search(r"Triggered rules: (.+?)\. Rules reference:", prompt) or "none"
    risk_tier = _search(r"tier=(.+?) has", prompt) or "unknown"
    merchant = _search(r"Current merchant=(.+?), amount=", prompt) or "the merchant"
    amount = _search(r"amount=([0-9.]+)", prompt) or "0.00"

    if triggered_rules == "none":
        return (
            f"Low concern. {merchant} for {amount} does not trigger major rules, "
            f"though the {risk_tier} account tier still merits normal monitoring."
        )

    rules_text = triggered_rules.replace(",", ", ")
    return (
        f"Escalate for review. {merchant} for {amount} triggered {rules_text}, "
        f"and the account is currently tiered {risk_tier}. Confirm whether the "
        "behavior matches recent transaction patterns before clearing it."
    )


def _generate_executive_summary(prompt: str) -> str:
    total_revenue = _search(r"total_revenue=([0-9.]+)", prompt) or "0.00"
    top_category_revenue = _search(r"top_category_revenue=([0-9.]+)", prompt) or "0.00"
    avg_score = _search(r"avg_score=([0-9.]+)", prompt) or "0.00"
    high_risk_transactions = _search(r"high_risk_transactions=([0-9.]+)", prompt) or "0"

    return (
        f"Retail performance remained steady with total revenue at {total_revenue} "
        f"and top-category revenue at {top_category_revenue}. Risk operations "
        f"averaged {avg_score} with {high_risk_transactions} high-risk transactions, "
        "so leadership should keep focus on flagged payment activity while preserving "
        "momentum in the retail pipeline."
    )


class CatalogCoach(BaseLLMResource):
    model_name: str = "embedded-catalog-coach"
    system_prompt: str = (
        "You are a retail catalog editor. Improve copy and keep category labels tidy."
    )


class RiskReviewer(BaseLLMResource):
    model_name: str = "embedded-risk-reviewer"
    system_prompt: str = (
        "You are a cautious fraud analyst. Provide concise reasoning for transaction risk."
    )


class BriefingWriter(BaseLLMResource):
    model_name: str = "embedded-briefing-writer"
    system_prompt: str = (
        "You summarize analytics for executives in a short and direct weekly briefing."
    )
