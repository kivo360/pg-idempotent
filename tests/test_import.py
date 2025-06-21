"""Test PG Idempotent."""

import pg_idempotent


def test_import() -> None:
    """Test that the package can be imported."""
    assert isinstance(pg_idempotent.__name__, str)
