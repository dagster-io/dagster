from __future__ import annotations

import pandas as pd
import dagster as dg

from shared.metadata import add_dataframe_preview_metadata
from shared.resources import SupportsGenerate


def _score_row(row: pd.Series) -> int:
    base_score = 10
    if bool(row["merchant_flag"]):
        base_score += 25
    if bool(row["large_amount_flag"]):
        base_score += 35
    if row["risk_tier"] == "high":
        base_score += 20
    if row["risk_tier"] == "medium":
        base_score += 10
    return min(base_score, 99)


def _level_for_score(score: int) -> str:
    if score >= 70:
        return "high"
    if score >= 40:
        return "medium"
    return "low"


@dg.asset(group_name="gold")
def risk_prompt_inputs(
    context,
    selected_risk_context: pd.DataFrame,
) -> pd.DataFrame:
    prompts = selected_risk_context.copy()
    prompts["prompt"] = prompts.apply(
        lambda row: (
            "Review this transaction and return concise reasoning. "
            f"Context: {row['selected_context']}"
        ),
        axis=1,
    )
    return add_dataframe_preview_metadata(
        context,
        prompts[
            [
                "transaction_id",
                "account_id",
                "amount",
                "merchant",
                "risk_tier",
                "merchant_flag",
                "large_amount_flag",
                "prompt",
                "context_summary",
                "triggered_rules",
                "selected_context",
            ]
        ],
    )


@dg.asset(group_name="gold")
def transaction_risk_scores(
    context,
    risk_prompt_inputs: pd.DataFrame,
    llm: dg.ResourceParam[SupportsGenerate],
) -> pd.DataFrame:
    context.add_output_metadata(llm.runtime_metadata())
    rows: list[dict[str, object]] = []
    for row in risk_prompt_inputs.to_dict(orient="records"):
        score = _score_row(pd.Series(row))
        rows.append(
            {
                "transaction_id": row["transaction_id"],
                "account_id": row["account_id"],
                "merchant": row["merchant"],
                "amount": row["amount"],
                "risk_level": _level_for_score(score),
                "score": score,
                "rationale": llm.generate(str(row["prompt"])),
            }
        )
    return add_dataframe_preview_metadata(context, pd.DataFrame(rows))


@dg.asset(group_name="gold")
def risk_llm_audit_log(
    context,
    risk_prompt_inputs: pd.DataFrame,
    transaction_risk_scores: pd.DataFrame,
) -> pd.DataFrame:
    return add_dataframe_preview_metadata(
        context,
        risk_prompt_inputs.merge(
            transaction_risk_scores,
            on=["transaction_id", "account_id", "merchant", "amount"],
        ),
    )


@dg.asset(group_name="gold")
def account_summary(
    context,
    transaction_risk_scores: pd.DataFrame,
) -> pd.DataFrame:
    return add_dataframe_preview_metadata(
        context,
        transaction_risk_scores.groupby("account_id", as_index=False)
        .agg(
            avg_score=("score", "mean"),
            high_risk_transactions=(
                "risk_level",
                lambda values: int(sum(value == "high" for value in values)),
            ),
        )
        .sort_values("account_id"),
    )
