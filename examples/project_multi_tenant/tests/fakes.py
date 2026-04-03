from __future__ import annotations

import dagster as dg


class MockLLMResource(dg.ConfigurableResource):
    model_name: str = "mock-model"

    def generate(self, prompt: str) -> str:
        snippet = " ".join(prompt.split())[:120]
        return f"[mock:{self.model_name}] {snippet}"

    def runtime_metadata(self) -> dict[str, object]:
        return {
            "llm_model": self.model_name,
            "runtime_dependency": "test-double",
        }
