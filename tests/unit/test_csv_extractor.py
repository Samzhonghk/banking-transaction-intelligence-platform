from pathlib import Path

from banking_intelligence.ingestion.extractors.csv import extract_csv


def test_extract_csv_preserves_raw_values(tmp_path: Path) -> None:
    """Raw CSV values should not be changed during extraction."""

    csv_path = tmp_path / "transactions.csv"
    csv_path.write_text(
        "transaction_id,account_id,amount,description\n0001,00123,100.50,\n",
        encoding="utf-8",
    )

    dataframe = extract_csv(csv_path)

    assert dataframe.to_dict(orient="records") == [
        {
            "transaction_id": "0001",
            "account_id": "00123",
            "amount": "100.50",
            "description": "",
        }
    ]
