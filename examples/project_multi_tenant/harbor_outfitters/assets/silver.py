from __future__ import annotations

import pandas as pd
import dagster as dg

from shared.metadata import add_dataframe_preview_metadata


@dg.asset(group_name="silver")
def cleaned_sales(
    context,
    raw_sales: pd.DataFrame,
) -> pd.DataFrame:
    sales = raw_sales.copy()
    sales["timestamp"] = pd.to_datetime(sales["timestamp"], utc=False)
    sales["revenue_per_unit"] = sales["revenue"] / sales["quantity"]
    return add_dataframe_preview_metadata(context, sales)


@dg.asset(group_name="silver")
def standardized_products(
    context,
    raw_products: pd.DataFrame,
) -> pd.DataFrame:
    products = raw_products.copy()
    products["category"] = products["category"].str.lower().str.strip()
    products["name"] = products["name"].str.strip()
    return add_dataframe_preview_metadata(
        context,
        products.drop_duplicates(subset=["product_id"]),
    )


@dg.asset(group_name="silver")
def catalog_context_documents(
    context,
    standardized_products: pd.DataFrame,
    raw_brand_guidelines: pd.DataFrame,
    raw_taxonomy_examples: pd.DataFrame,
) -> pd.DataFrame:
    tone_rules = " | ".join(raw_brand_guidelines["content"].tolist())
    examples = " | ".join(
        f"{row.example_product} -> {row.approved_category}"
        for row in raw_taxonomy_examples.itertuples(index=False)
    )
    documents = standardized_products.copy()
    documents["style_guide"] = tone_rules
    documents["taxonomy_examples"] = examples
    documents["context_snippet"] = (
        "Product: "
        + documents["name"]
        + ". Category: "
        + documents["category"]
        + ". Description: "
        + documents["description"]
    )
    return add_dataframe_preview_metadata(context, documents)


@dg.asset(group_name="silver")
def selected_catalog_context(
    context,
    catalog_context_documents: pd.DataFrame,
) -> pd.DataFrame:
    selected = catalog_context_documents.copy()
    selected["selected_context"] = selected.apply(
        lambda row: (
            f"Style guide: {row['style_guide']} "
            f"Approved examples: {row['taxonomy_examples']} "
            f"Product facts: {row['context_snippet']}"
        ),
        axis=1,
    )
    return add_dataframe_preview_metadata(
        context,
        selected[
            [
                "product_id",
                "name",
                "category",
                "description",
                "context_snippet",
                "selected_context",
            ]
        ],
    )


@dg.asset(group_name="silver")
def catalog_prompt_inputs(
    context,
    selected_catalog_context: pd.DataFrame,
) -> pd.DataFrame:
    prompts = selected_catalog_context.copy()
    prompts["prompt"] = prompts.apply(
        lambda row: (
            f"Write cleaner catalog copy for {row['name']}. "
            f"Use category {row['category']}. "
            f"Context: {row['selected_context']}."
        ),
        axis=1,
    )
    return add_dataframe_preview_metadata(
        context,
        prompts[
            [
                "product_id",
                "name",
                "category",
                "context_snippet",
                "selected_context",
                "prompt",
            ]
        ],
    )
