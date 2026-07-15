from pathlib import Path

import pandas as pd


def extract_csv(file_path: Path) -> pd.DataFrame:
    """Read raw CSV records without applying business transformations."""

    return pd.read_csv(
        file_path,
        dtype=str,
        keep_default_na=False,
        encoding="utf-8",
        on_bad_lines="error",
    )
