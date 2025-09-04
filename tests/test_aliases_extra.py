"""
Extra tests for core.aliases to improve coverage.
"""

import csv
import os
import tempfile

from core.aliases import _load_aliases, add_alias


def test_load_aliases_missing_file_returns_empty_dict():
    """_load_aliases gracefully handles missing files."""
    missing = os.path.join(tempfile.gettempdir(), "__no_such_aliases__.csv")
    if os.path.exists(missing):
        os.unlink(missing)
    assert _load_aliases(missing) == {}


def test_add_alias_creates_file_and_writes_header():
    """add_alias should create the file with header on first write."""
    fd, path = tempfile.mkstemp(suffix=".csv")
    os.close(fd)
    # Remove to simulate non-existent file so add_alias writes header
    os.unlink(path)

    try:
        add_alias("Espinacas", "spinach_raw", path)
        add_alias("Pollo", "chicken_breast", path)

        # Verify contents
        with open(path, newline="", encoding="utf-8") as f:
            rows = list(csv.reader(f))
        assert rows[0] == ["alias", "canonical"]
        # Rows are lowercased alias and stripped values
        assert ["espinacas", "spinach_raw"] in rows
        assert ["pollo", "chicken_breast"] in rows
    finally:
        if os.path.exists(path):
            os.unlink(path)

