from __future__ import annotations

import pandas as pd
import dagster as dg

from shared.metadata import add_dataframe_preview_metadata


@dg.asset(group_name="bronze")
def raw_sales(context) -> pd.DataFrame:
    return add_dataframe_preview_metadata(
        context,
        pd.DataFrame(
            [
                {
                    "store_id": "nyc-01",
                    "product_id": 101,
                    "quantity": 3,
                    "revenue": 59.97,
                    "timestamp": "2026-03-01T10:00:00",
                },
                {
                    "store_id": "nyc-01",
                    "product_id": 102,
                    "quantity": 2,
                    "revenue": 39.98,
                    "timestamp": "2026-03-01T10:15:00",
                },
                {
                    "store_id": "nyc-01",
                    "product_id": 105,
                    "quantity": 4,
                    "revenue": 111.96,
                    "timestamp": "2026-03-01T10:40:00",
                },
                {
                    "store_id": "nyc-01",
                    "product_id": 106,
                    "quantity": 1,
                    "revenue": 64.00,
                    "timestamp": "2026-03-01T11:05:00",
                },
                {
                    "store_id": "nyc-01",
                    "product_id": 108,
                    "quantity": 2,
                    "revenue": 50.00,
                    "timestamp": "2026-03-01T11:25:00",
                },
                {
                    "store_id": "bos-02",
                    "product_id": 103,
                    "quantity": 1,
                    "revenue": 18.50,
                    "timestamp": "2026-03-01T11:00:00",
                },
                {
                    "store_id": "bos-02",
                    "product_id": 104,
                    "quantity": 4,
                    "revenue": 120.00,
                    "timestamp": "2026-03-01T11:45:00",
                },
                {
                    "store_id": "bos-02",
                    "product_id": 107,
                    "quantity": 2,
                    "revenue": 48.00,
                    "timestamp": "2026-03-01T12:05:00",
                },
                {
                    "store_id": "bos-02",
                    "product_id": 105,
                    "quantity": 3,
                    "revenue": 83.97,
                    "timestamp": "2026-03-01T12:20:00",
                },
                {
                    "store_id": "bos-02",
                    "product_id": 108,
                    "quantity": 1,
                    "revenue": 25.00,
                    "timestamp": "2026-03-01T12:55:00",
                },
                {
                    "store_id": "phl-03",
                    "product_id": 101,
                    "quantity": 2,
                    "revenue": 39.98,
                    "timestamp": "2026-03-01T12:10:00",
                },
                {
                    "store_id": "phl-03",
                    "product_id": 104,
                    "quantity": 1,
                    "revenue": 30.00,
                    "timestamp": "2026-03-01T12:35:00",
                },
                {
                    "store_id": "phl-03",
                    "product_id": 106,
                    "quantity": 2,
                    "revenue": 128.00,
                    "timestamp": "2026-03-01T13:05:00",
                },
                {
                    "store_id": "phl-03",
                    "product_id": 107,
                    "quantity": 3,
                    "revenue": 72.00,
                    "timestamp": "2026-03-01T13:30:00",
                },
                {
                    "store_id": "phl-03",
                    "product_id": 102,
                    "quantity": 1,
                    "revenue": 19.99,
                    "timestamp": "2026-03-01T13:45:00",
                },
                {
                    "store_id": "dc-04",
                    "product_id": 108,
                    "quantity": 3,
                    "revenue": 75.00,
                    "timestamp": "2026-03-01T14:05:00",
                },
                {
                    "store_id": "dc-04",
                    "product_id": 105,
                    "quantity": 2,
                    "revenue": 55.98,
                    "timestamp": "2026-03-01T14:20:00",
                },
                {
                    "store_id": "dc-04",
                    "product_id": 103,
                    "quantity": 2,
                    "revenue": 37.00,
                    "timestamp": "2026-03-01T14:40:00",
                },
                {
                    "store_id": "dc-04",
                    "product_id": 106,
                    "quantity": 1,
                    "revenue": 64.00,
                    "timestamp": "2026-03-01T15:05:00",
                },
                {
                    "store_id": "dc-04",
                    "product_id": 101,
                    "quantity": 4,
                    "revenue": 79.96,
                    "timestamp": "2026-03-01T15:20:00",
                },
            ]
        ),
    )


@dg.asset(group_name="bronze")
def raw_products(context) -> pd.DataFrame:
    return add_dataframe_preview_metadata(
        context,
        pd.DataFrame(
            [
                {
                    "product_id": 101,
                    "name": "Trail Socks",
                    "category": "Outdoor Gear",
                    "description": "Merino blend trail socks for weekend hikes.",
                },
                {
                    "product_id": 102,
                    "name": "Market Tote",
                    "category": "Everyday Carry",
                    "description": "Canvas tote with reinforced handles.",
                },
                {
                    "product_id": 103,
                    "name": "Desk Lamp",
                    "category": "Home Office",
                    "description": "Compact lamp with adjustable neck.",
                },
                {
                    "product_id": 104,
                    "name": "Travel Mug",
                    "category": "Outdoor Gear",
                    "description": "Insulated mug that keeps drinks warm.",
                },
                {
                    "product_id": 105,
                    "name": "Weekender Duffel",
                    "category": "Everyday Carry",
                    "description": "Soft-sided duffel with easy-access exterior pockets.",
                },
                {
                    "product_id": 106,
                    "name": "Camp Lantern",
                    "category": "Outdoor Gear",
                    "description": "Rechargeable lantern for campsites and patios.",
                },
                {
                    "product_id": 107,
                    "name": "Cable Organizer",
                    "category": "Home Office",
                    "description": "Felt zip pouch sized for chargers and adapters.",
                },
                {
                    "product_id": 108,
                    "name": "Field Notebook Set",
                    "category": "Desk Essentials",
                    "description": "Three-pack of ruled notebooks with durable covers.",
                },
            ]
        ),
    )


@dg.asset(group_name="bronze")
def raw_brand_guidelines(context) -> pd.DataFrame:
    return add_dataframe_preview_metadata(
        context,
        pd.DataFrame(
            [
                {"rule_type": "tone", "content": "Keep descriptions practical, warm, and concise."},
                {
                    "rule_type": "audience",
                    "content": "Write for busy shoppers comparing everyday utility and durability.",
                },
                {
                    "rule_type": "benefit",
                    "content": "Lead with the primary use case before listing supporting details.",
                },
                {
                    "rule_type": "avoid",
                    "content": "Do not use the words premium, luxury, or revolutionary.",
                },
            ]
        ),
    )


@dg.asset(group_name="bronze")
def raw_taxonomy_examples(context) -> pd.DataFrame:
    return add_dataframe_preview_metadata(
        context,
        pd.DataFrame(
            [
                {"example_product": "Hiking socks", "approved_category": "outdoor gear"},
                {"example_product": "Weekender tote", "approved_category": "everyday carry"},
                {"example_product": "Reading lamp", "approved_category": "home office"},
                {"example_product": "Lantern", "approved_category": "outdoor gear"},
                {"example_product": "Tech pouch", "approved_category": "home office"},
                {"example_product": "Notebook set", "approved_category": "desk essentials"},
            ]
        ),
    )
