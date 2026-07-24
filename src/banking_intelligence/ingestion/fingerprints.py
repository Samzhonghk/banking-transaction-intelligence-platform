import hashlib
import json
from collections.abc import Mapping


def build_record_fingerprint(record: Mapping[str, object]) -> str:
    """Return a deterministic SHA-256 fingerprint for one raw record."""
    canonical_record = json.dumps(
        record, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    )
    return hashlib.sha256(canonical_record.encode("utf-8")).hexdigest()
