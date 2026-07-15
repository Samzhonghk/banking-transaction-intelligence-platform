import pandas as pd

CURRENCIES = frozenset({"AUD", "NZD", "USD"})


def add_rejection_reasons(df: pd.DataFrame) -> pd.DataFrame:
    """Return a copy with validation failures recorded for every row."""
    validated = df.copy()
    validated["rejection_reason"] = ""

    rejection_rules = (
        (validated["transaction_id"].eq(""), "missing_transaction_id"),
        (
            validated["transaction_id"].duplicated(keep=False)
            & validated["transaction_id"].ne(""),
            "duplicate_transaction_id",
        ),
        (validated["account_id"].eq(""), "missing_account_id"),
        (
            validated["amount"].isna() | validated["amount"].le(0),
            "invalid_amount",
        ),
        (~validated["currency"].isin(CURRENCIES), "unsupported_currency"),
        (validated["transaction_timestamp"].isna(), "invalid_timestamp"),
    )

    for invalid_mask, reason in rejection_rules:
        validated.loc[invalid_mask, "rejection_reason"] += f"{reason};"

    validated["rejection_reason"] = validated["rejection_reason"].str.rstrip(";")
    return validated


def build_valid_transaction_mask(df: pd.DataFrame) -> pd.Series:
    """Return a boolean mask identifying valid transaction rows."""
    validated = add_rejection_reasons(df)
    return validated["rejection_reason"].eq("")


def split_transactions(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Split transformed transactions into accepted and rejected rows."""
    validated = add_rejection_reasons(df)
    valid_mask = validated["rejection_reason"].eq("")

    accepted = validated.loc[valid_mask].drop(columns="rejection_reason").copy()
    rejected = validated.loc[~valid_mask].copy()

    return accepted, rejected
