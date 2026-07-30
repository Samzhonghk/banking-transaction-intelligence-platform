"""Generate reproducible transaction CSV data for local demonstrations."""

import argparse
import csv
import random
from collections.abc import Iterator
from datetime import UTC, datetime, timedelta
from pathlib import Path

FIELDNAMES = (
    "transaction_id",
    "account_id",
    "amount",
    "currency",
    "description",
    "transaction_timestamp",
)

CURRENCIES = ("NZD", "AUD", "USD")
DESCRIPTIONS = (
    "Coffee shop",
    "Fuel station",
    "Grocery store",
    "Online purchase",
    "Restaurant",
    "Salary payment",
    "Utility payment",
)
INVALID_CASES = (
    "missing_transaction_id",
    "missing_account_id",
    "invalid_amount",
    "unsupported_currency",
    "invalid_timestamp",
)
INVALID_RATE = 0.05
ACCOUNT_COUNT = 1_000
DEMO_PERIOD_DAYS = 180


def build_parser() -> argparse.ArgumentParser:
    """Build command-line arguments for reproducible data generation."""
    parser = argparse.ArgumentParser(
        description="Generate medium-sized transaction demo data.",
    )
    parser.add_argument(
        "--rows",
        type=int,
        default=10_000,
        help="Number of transaction rows to generate.",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed used to make output reproducible.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("data/generated/transactions_medium.csv"),
        help="Destination CSV path.",
    )
    return parser


def apply_invalid_case(
    row: dict[str, str],
    invalid_case: str,
) -> None:
    """Mutate one generated row to represent a controlled validation failure."""
    if invalid_case == "missing_transaction_id":
        row["transaction_id"] = ""
    elif invalid_case == "missing_account_id":
        row["account_id"] = ""
    elif invalid_case == "invalid_amount":
        row["amount"] = "-1.00"
    elif invalid_case == "unsupported_currency":
        row["currency"] = "GBP"
    elif invalid_case == "invalid_timestamp":
        row["transaction_timestamp"] = "not-a-timestamp"
    else:
        raise ValueError(f"Unsupported invalid case: {invalid_case}")


def generate_transaction_rows(
    row_count: int,
    seed: int,
) -> Iterator[dict[str, str]]:
    """Yield deterministic transaction rows with a controlled invalid rate."""
    if row_count < 1:
        raise ValueError("row_count must be at least 1")

    random_generator = random.Random(seed)
    start_timestamp = datetime(2026, 1, 1, tzinfo=UTC)
    demo_minutes = DEMO_PERIOD_DAYS * 24 * 60

    for row_number in range(1, row_count + 1):
        account_number = random_generator.randint(1, ACCOUNT_COUNT)
        timestamp = start_timestamp + timedelta(
            minutes=random_generator.randrange(demo_minutes),
        )
        row = {
            "transaction_id": f"TX-GEN-{row_number:08d}",
            "account_id": f"ACC-GEN-{account_number:06d}",
            "amount": f"{random_generator.uniform(1, 5_000):.2f}",
            "currency": CURRENCIES[(account_number - 1) % len(CURRENCIES)],
            "description": random_generator.choice(DESCRIPTIONS),
            "transaction_timestamp": timestamp.isoformat().replace(
                "+00:00",
                "Z",
            ),
        }

        if random_generator.random() < INVALID_RATE:
            apply_invalid_case(
                row,
                random_generator.choice(INVALID_CASES),
            )

        yield row


def main() -> int:
    """Generate the requested CSV file and return a process exit code."""
    args = build_parser().parse_args()

    if args.rows < 1:
        raise SystemExit("--rows must be at least 1")

    args.output.parent.mkdir(parents=True, exist_ok=True)

    with args.output.open("w", encoding="utf-8", newline="") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(
            generate_transaction_rows(
                row_count=args.rows,
                seed=args.seed,
            )
        )

    print(
        f"Generated {args.rows} transaction rows at {args.output} "
        f"using seed {args.seed}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
