import os
import uuid

import httpx
from dagster import AssetExecutionContext, MetadataValue, asset


def new_id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex}"


@asset
def governed_ai_summary(context: AssetExecutionContext) -> str:
    run_id = new_id("dagster")
    request_id = new_id("req")
    response = httpx.post(
        "https://api.tuningengines.com/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {os.environ['TE_INFERENCE_KEY']}",
            "Content-Type": "application/json",
            "X-TE-Run-ID": run_id,
            "X-TE-Request-ID": request_id,
        },
        timeout=60,
        json={
            "model": os.getenv("TE_MODEL", "auto"),
            "messages": [
                {
                    "role": "user",
                    "content": "Summarize why governed AI assets need durable orchestration.",
                }
            ],
            "metadata": {
                "run_id": run_id,
                "request_id": request_id,
                "runtime": "dagster",
                "event_type": "model.call",
            },
        },
    )
    response.raise_for_status()
    summary = response.json()["choices"][0]["message"]["content"]

    context.add_output_metadata(
        {
            "tuning_engines_run_id": MetadataValue.text(run_id),
            "tuning_engines_request_id": MetadataValue.text(request_id),
        }
    )
    return summary
