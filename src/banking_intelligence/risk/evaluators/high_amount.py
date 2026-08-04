from decimal import Decimal


def evaluate_high_amount(
    amount: Decimal,
    threshold: Decimal,
) -> tuple[bool, Decimal, dict[str, object]]:
    """Evaluate whether a transaction exceeds the high-amount threshold."""
    if threshold <= 0:
        raise ValueError("High-amount threshold must be greater than zero")

    matched = amount > threshold
    excess_amount = max(amount - threshold, Decimal("0"))

    if matched:
        risk_score = min(
            Decimal("100"),
            Decimal("50") + (excess_amount / threshold) * Decimal("50"),
        )
    else:
        risk_score = Decimal("0")

    risk_score = risk_score.quantize(Decimal("0.01"))
    money_precision = Decimal("0.01")

    evidence = {
        "rule_type": "high_amount",
        "amount": str(amount.quantize(money_precision)),
        "threshold": str(threshold.quantize(money_precision)),
        "excess_amount": str(excess_amount.quantize(money_precision)),
    }

    return matched, risk_score, evidence
