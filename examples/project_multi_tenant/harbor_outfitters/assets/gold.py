from __future__ import annotations

import pandas as pd
import dagster as dg

from shared.metadata import add_dataframe_preview_metadata
from shared.resources import SupportsGenerate


@dg.asset(group_name="gold")
def enriched_products(
    context,
    catalog_prompt_inputs: pd.DataFrame,
    llm: dg.ResourceParam[SupportsGenerate],
) -> pd.DataFrame:
    context.add_output_metadata(llm.runtime_metadata())
    rows: list[dict[str, object]] = []
    for row in catalog_prompt_inputs.itertuples(index=False):
        response = llm.generate(str(row.prompt))
        rows.append(
            {
                "product_id": row.product_id,
                "name": row.name,
                "category": row.category,
                "generated_copy": response,
            }
        )
    return add_dataframe_preview_metadata(context, pd.DataFrame(rows))


@dg.asset(group_name="gold")
def catalog_llm_audit_log(
    context,
    catalog_prompt_inputs: pd.DataFrame,
    enriched_products: pd.DataFrame,
) -> pd.DataFrame:
    return add_dataframe_preview_metadata(
        context,
        catalog_prompt_inputs.merge(enriched_products, on=["product_id", "name", "category"]),
    )


@dg.asset(group_name="gold")
def sales_summary(
    context,
    cleaned_sales: pd.DataFrame,
    standardized_products: pd.DataFrame,
) -> pd.DataFrame:
    merged = cleaned_sales.merge(standardized_products[["product_id", "category"]], on="product_id")
    summary = (
        merged.groupby(["store_id", "category"], as_index=False)
        .agg(total_revenue=("revenue", "sum"), total_units=("quantity", "sum"))
        .sort_values(["store_id", "category"])
    )
    return add_dataframe_preview_metadata(context, summary)
