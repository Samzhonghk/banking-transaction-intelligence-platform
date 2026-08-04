from decimal import Decimal

import pytest

from banking_intelligence.risk.evaluators.high_amount import evaluate_high_amount


@pytest.mark.parametrize(
    "amount",
    [
        Decimal("80.00"),
        Decimal("100.00"),
    ],
)
def test_high_amount_does_not_match_at_or_below_threshold(
    amount: Decimal,
) -> None:
    """Amounts must exceed, rather than equal, the configured threshold."""
    matched, score, evidence = evaluate_high_amount(
        amount=amount,
        threshold=Decimal("100.00"),
    )

    assert matched is False
    assert score == Decimal("0.00")
    assert evidence["excess_amount"] == "0.00"


def test_high_amount_returns_score_and_audit_evidence() -> None:
    """A matched amount should produce a proportional score and evidence."""
    matched, score, evidence = evaluate_high_amount(
        amount=Decimal("150.00"),
        threshold=Decimal("100.00"),
    )

    assert matched is True
    assert score == Decimal("75.00")
    assert evidence == {
        "rule_type": "high_amount",
        "amount": "150.00",
        "threshold": "100.00",
        "excess_amount": "50.00",
    }


def test_high_amount_caps_score_at_one_hundred() -> None:
    """Very large amounts should not exceed the database score constraint."""
    _, score, _ = evaluate_high_amount(
        amount=Decimal("1000.00"),
        threshold=Decimal("100.00"),
    )

    assert score == Decimal("100.00")


def test_high_amount_rejects_non_positive_threshold() -> None:
    """Invalid rule configuration should fail before score calculation."""
    with pytest.raises(
        ValueError,
        match="threshold must be greater than zero",
    ):
        evaluate_high_amount(
            amount=Decimal("100.00"),
            threshold=Decimal("0"),
        )
