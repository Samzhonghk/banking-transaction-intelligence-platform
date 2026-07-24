from banking_intelligence.ingestion.fingerprints import build_record_fingerprint


def test_build_record_fingerprint() -> None:
    original = {
        "transaction_id": "TX001",
        "amount": "100.50",
    }
    reordered = {
        "amount": "100.50",
        "transaction_id": "TX001",
    }
    changed = {
        "transaction_id": "TX001",
        "amount": "100.51",
    }

    original_fingerprint = build_record_fingerprint(original)
    assert original_fingerprint == build_record_fingerprint(reordered)
    assert original_fingerprint != build_record_fingerprint(changed)
    assert len(original_fingerprint) == 64
