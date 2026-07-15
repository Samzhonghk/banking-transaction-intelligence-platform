import pandas as pd


def transform_transactions(df: pd.DataFrame) -> pd.DataFrame:
    """Standardise raw transaction fields for validation."""
    transformed = df.copy()

    for column in ("transaction_id", "account_id", "description"):
        transformed[column] = transformed[column].str.strip()

    transformed["currency"] = transformed["currency"].str.strip().str.upper()

    transformed["amount"] = pd.to_numeric(
        transformed["amount"].str.strip(),
        errors="coerce",
    )

    transformed["transaction_timestamp"] = pd.to_datetime(
        transformed["transaction_timestamp"].str.strip(),
        errors="coerce",
        utc=True,
    )

    return transformed
