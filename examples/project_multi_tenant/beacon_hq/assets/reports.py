from __future__ import annotations

import pandas as pd
import dagster as dg

from shared.metadata import add_dataframe_preview_metadata
from shared.resources import SupportsGenerate


@dg.asset(
    group_name="silver",
    deps=[dg.AssetKey(["harbor_outfitters", "sales_summary"])],
)
def consolidated_revenue(context) -> pd.DataFrame:
    return add_dataframe_preview_metadata(
        context,
        pd.DataFrame(
            [
                {"tenant": "harbor_outfitters", "metric": "total_revenue", "value": 308.43},
                {
                    "tenant": "harbor_outfitters",
                    "metric": "top_category_revenue",
                    "value": 149.97,
                },
            ]
        ),
    )


@dg.asset(
    group_name="silver",
    deps=[dg.AssetKey(["summit_financial", "account_summary"])],
)
def risk_overview(context) -> pd.DataFrame:
    return add_dataframe_preview_metadata(
        context,
        pd.DataFrame(
            [
                {"tenant": "summit_financial", "metric": "avg_score", "value": 53.33},
                {
                    "tenant": "summit_financial",
                    "metric": "high_risk_transactions",
                    "value": 2.0,
                },
            ]
        ),
    )


@dg.asset(group_name="gold")
def briefing_highlights(
    context,
    consolidated_revenue: pd.DataFrame,
    risk_overview: pd.DataFrame,
) -> pd.DataFrame:
    revenue_lines = "; ".join(
        f"{row.metric}={row.value:.2f}" for row in consolidated_revenue.itertuples(index=False)
    )
    risk_lines = "; ".join(
        f"{row.metric}={row.value:.2f}" for row in risk_overview.itertuples(index=False)
    )
    return add_dataframe_preview_metadata(
        context,
        pd.DataFrame(
            [
                {
                    "section": "weekly_briefing",
                    "highlight_text": (
                        f"Retail metrics: {revenue_lines}. Risk metrics: {risk_lines}."
                    ),
                }
            ]
        ),
    )


@dg.asset(group_name="gold")
def executive_context_packet(
    context,
    briefing_highlights: pd.DataFrame,
) -> pd.DataFrame:
    return add_dataframe_preview_metadata(
        context,
        pd.DataFrame(
            [
                {
                    "section": "weekly_briefing",
                    "context_packet": (
                        "Write a concise executive summary using this prepared context. "
                        + str(briefing_highlights.iloc[0]["highlight_text"])
                    ),
                }
            ]
        ),
    )


@dg.asset(group_name="gold")
def executive_summary(
    context,
    executive_context_packet: pd.DataFrame,
    llm: dg.ResourceParam[SupportsGenerate],
) -> pd.DataFrame:
    context.add_output_metadata(llm.runtime_metadata())
    context_packet = str(executive_context_packet.iloc[0]["context_packet"])
    response = llm.generate(context_packet)
    return add_dataframe_preview_metadata(context, pd.DataFrame([{"summary": response}]))


@dg.asset(group_name="gold")
def executive_llm_audit_log(
    context,
    executive_context_packet: pd.DataFrame,
    executive_summary: pd.DataFrame,
) -> pd.DataFrame:
    return add_dataframe_preview_metadata(
        context,
        pd.DataFrame(
            [
                {
                    "context_packet": str(executive_context_packet.iloc[0]["context_packet"]),
                    "summary": str(executive_summary.iloc[0]["summary"]),
                }
            ]
        ),
    )
