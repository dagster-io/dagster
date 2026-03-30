from __future__ import annotations

import pandas as pd
import dagster as dg

from shared.metadata import add_dataframe_preview_metadata


@dg.asset(group_name="silver")
def cleaned_transactions(
    context,
    raw_transactions: pd.DataFrame,
) -> pd.DataFrame:
    transactions = raw_transactions.copy()
    transactions["timestamp"] = pd.to_datetime(transactions["timestamp"], utc=False)
    transactions["amount"] = transactions["amount"].abs()
    transactions["merchant_flag"] = transactions["merchant"].eq("Wire Outlet")
    transactions["large_amount_flag"] = transactions["amount"] >= 900
    return add_dataframe_preview_metadata(context, transactions)


@dg.asset(group_name="silver")
def validated_accounts(
    context,
    raw_accounts: pd.DataFrame,
) -> pd.DataFrame:
    accounts = raw_accounts.copy()
    allowed_tiers = {"low", "medium", "high"}
    assert set(accounts["risk_tier"]).issubset(allowed_tiers)
    return add_dataframe_preview_metadata(context, accounts)


@dg.asset(group_name="silver")
def transaction_context_windows(
    context,
    cleaned_transactions: pd.DataFrame,
    validated_accounts: pd.DataFrame,
) -> pd.DataFrame:
    account_rollup = cleaned_transactions.groupby("account_id", as_index=False).agg(
        transaction_count=("transaction_id", "count"),
        recent_total_amount=("amount", "sum"),
        flagged_count=("merchant_flag", "sum"),
    )
    return add_dataframe_preview_metadata(
        context,
        validated_accounts.merge(account_rollup, on="account_id"),
    )


@dg.asset(group_name="silver")
def risk_context_documents(
    context,
    cleaned_transactions: pd.DataFrame,
    validated_accounts: pd.DataFrame,
    transaction_context_windows: pd.DataFrame,
    raw_risk_rules: pd.DataFrame,
) -> pd.DataFrame:
    merged = cleaned_transactions.merge(validated_accounts, on="account_id").merge(
        transaction_context_windows,
        on=["account_id", "customer_name", "account_type", "risk_tier"],
    )
    rules_text = " | ".join(
        f"{row.rule_name}: {row.condition} (weight={row.weight})"
        for row in raw_risk_rules.itertuples(index=False)
    )
    merged["rules_context"] = rules_text
    merged["context_summary"] = merged.apply(
        lambda row: (
            f"Account {row['account_id']} tier={row['risk_tier']} has "
            f"{row['transaction_count']} recent transactions totaling {row['recent_total_amount']:.2f}. "
            f"Current merchant={row['merchant']}, amount={row['amount']:.2f}, "
            f"merchant_flag={row['merchant_flag']}, large_amount_flag={row['large_amount_flag']}."
        ),
        axis=1,
    )
    return add_dataframe_preview_metadata(context, merged)


@dg.asset(group_name="silver")
def selected_risk_context(
    context,
    risk_context_documents: pd.DataFrame,
) -> pd.DataFrame:
    selected = risk_context_documents.copy()
    selected["triggered_rules"] = selected.apply(
        lambda row: (
            ", ".join(
                rule
                for rule, is_triggered in [
                    ("large_wire", bool(row["large_amount_flag"])),
                    ("flagged_merchant", bool(row["merchant_flag"])),
                    ("high_risk_account", row["risk_tier"] == "high"),
                ]
                if is_triggered
            )
            or "none"
        ),
        axis=1,
    )
    selected["selected_context"] = selected.apply(
        lambda row: (
            f"Triggered rules: {row['triggered_rules']}. "
            f"Rules reference: {row['rules_context']}. "
            f"Transaction context: {row['context_summary']}"
        ),
        axis=1,
    )
    return add_dataframe_preview_metadata(context, selected)
