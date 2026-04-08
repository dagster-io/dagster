from __future__ import annotations

import pandas as pd
import dagster as dg

from shared.metadata import add_dataframe_preview_metadata


@dg.asset(group_name="bronze")
def raw_transactions(context) -> pd.DataFrame:
    return add_dataframe_preview_metadata(
        context,
        pd.DataFrame(
            [
                {
                    "transaction_id": "tx-100",
                    "account_id": "acct-1",
                    "amount": 42.50,
                    "merchant": "Corner Market",
                    "timestamp": "2026-03-02T08:00:00",
                },
                {
                    "transaction_id": "tx-101",
                    "account_id": "acct-1",
                    "amount": 950.00,
                    "merchant": "Wire Outlet",
                    "timestamp": "2026-03-02T08:10:00",
                },
                {
                    "transaction_id": "tx-102",
                    "account_id": "acct-2",
                    "amount": 210.75,
                    "merchant": "Travel Hub",
                    "timestamp": "2026-03-02T09:00:00",
                },
                {
                    "transaction_id": "tx-103",
                    "account_id": "acct-3",
                    "amount": 1200.00,
                    "merchant": "Wire Outlet",
                    "timestamp": "2026-03-02T09:30:00",
                },
                {
                    "transaction_id": "tx-104",
                    "account_id": "acct-2",
                    "amount": 18.99,
                    "merchant": "Coffee Stop",
                    "timestamp": "2026-03-02T09:45:00",
                },
                {
                    "transaction_id": "tx-105",
                    "account_id": "acct-4",
                    "amount": 680.00,
                    "merchant": "Equipment Lease",
                    "timestamp": "2026-03-02T10:05:00",
                },
                {
                    "transaction_id": "tx-106",
                    "account_id": "acct-5",
                    "amount": 89.30,
                    "merchant": "Office Supply Hub",
                    "timestamp": "2026-03-02T10:20:00",
                },
                {
                    "transaction_id": "tx-107",
                    "account_id": "acct-3",
                    "amount": 430.00,
                    "merchant": "Airport Transfer",
                    "timestamp": "2026-03-02T10:45:00",
                },
                {
                    "transaction_id": "tx-108",
                    "account_id": "acct-6",
                    "amount": 990.00,
                    "merchant": "Wire Outlet",
                    "timestamp": "2026-03-02T11:10:00",
                },
                {
                    "transaction_id": "tx-109",
                    "account_id": "acct-4",
                    "amount": 72.40,
                    "merchant": "Catering Corner",
                    "timestamp": "2026-03-02T11:35:00",
                },
                {
                    "transaction_id": "tx-110",
                    "account_id": "acct-2",
                    "amount": 510.00,
                    "merchant": "Travel Hub",
                    "timestamp": "2026-03-02T12:00:00",
                },
                {
                    "transaction_id": "tx-111",
                    "account_id": "acct-5",
                    "amount": 1250.00,
                    "merchant": "Wire Outlet",
                    "timestamp": "2026-03-02T12:30:00",
                },
                {
                    "transaction_id": "tx-112",
                    "account_id": "acct-6",
                    "amount": 34.25,
                    "merchant": "Coffee Stop",
                    "timestamp": "2026-03-02T12:45:00",
                },
                {
                    "transaction_id": "tx-113",
                    "account_id": "acct-1",
                    "amount": 305.00,
                    "merchant": "Data Services",
                    "timestamp": "2026-03-02T13:05:00",
                },
                {
                    "transaction_id": "tx-114",
                    "account_id": "acct-4",
                    "amount": 940.00,
                    "merchant": "Wire Outlet",
                    "timestamp": "2026-03-02T13:25:00",
                },
                {
                    "transaction_id": "tx-115",
                    "account_id": "acct-6",
                    "amount": 155.75,
                    "merchant": "Fleet Fuel",
                    "timestamp": "2026-03-02T13:50:00",
                },
            ]
        ),
    )


@dg.asset(group_name="bronze")
def raw_accounts(context) -> pd.DataFrame:
    return add_dataframe_preview_metadata(
        context,
        pd.DataFrame(
            [
                {
                    "account_id": "acct-1",
                    "customer_name": "Avery Reed",
                    "account_type": "checking",
                    "risk_tier": "medium",
                },
                {
                    "account_id": "acct-2",
                    "customer_name": "Jordan Hale",
                    "account_type": "savings",
                    "risk_tier": "low",
                },
                {
                    "account_id": "acct-3",
                    "customer_name": "Riley Chen",
                    "account_type": "business",
                    "risk_tier": "high",
                },
                {
                    "account_id": "acct-4",
                    "customer_name": "Morgan Ellis",
                    "account_type": "business",
                    "risk_tier": "medium",
                },
                {
                    "account_id": "acct-5",
                    "customer_name": "Taylor Brooks",
                    "account_type": "checking",
                    "risk_tier": "high",
                },
                {
                    "account_id": "acct-6",
                    "customer_name": "Casey Morgan",
                    "account_type": "commercial",
                    "risk_tier": "medium",
                },
            ]
        ),
    )


@dg.asset(group_name="bronze")
def raw_risk_rules(context) -> pd.DataFrame:
    return add_dataframe_preview_metadata(
        context,
        pd.DataFrame(
            [
                {"rule_name": "large_wire", "condition": "amount >= 900", "weight": 35},
                {
                    "rule_name": "flagged_merchant",
                    "condition": "merchant == Wire Outlet",
                    "weight": 25,
                },
                {"rule_name": "high_risk_account", "condition": "risk_tier == high", "weight": 20},
                {
                    "rule_name": "large_business_spend",
                    "condition": "account_type in {business, commercial} and amount >= 600",
                    "weight": 15,
                },
                {
                    "rule_name": "travel_spike",
                    "condition": "merchant == Travel Hub and amount >= 400",
                    "weight": 10,
                },
            ]
        ),
    )
