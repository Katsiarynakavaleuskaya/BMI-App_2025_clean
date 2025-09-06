from fastapi.testclient import TestClient

import app.utils.patchable as P
from app import app


def test_csv_endpoint_does_not_call_pdf_after_fix():
    """Test that the CSV endpoint doesn't call PDF generation after the fix."""
    client = TestClient(app)

    # Track calls to CSV and PDF functions
    calls = {"csv": 0, "pdf": 0}

    # Store original functions
    original_resolve = P.resolve_patchable

    # Mock functions
    def mock_make_weekly_menu(*a, **k):
        return {"days": [{"meals": []}]*7}, {}, {}, 0, 0

    def mock_csv_week(plan):
        calls["csv"] += 1
        return b"x,y\n"

    def mock_pdf_week(plan):
        calls["pdf"] += 1
        return b"%PDF"

    # Mock the patchable resolver to return our mock functions
    def mock_resolve(name, fallback):
        if name == "make_weekly_menu":
            return mock_make_weekly_menu
        elif name == "to_csv_week":
            return mock_csv_week
        elif name == "to_pdf_week":
            return mock_pdf_week
        else:
            return original_resolve(name, fallback)

    # Patch the resolver
    P.resolve_patchable = mock_resolve

    try:
        # Make request to CSV endpoint
        response = client.post("/api/v1/premium/export/week/csv",
                              json={"sex": "male", "age": 30, "height_cm": 175, "weight_kg": 70},
                              headers={"X-API-Key": "test_key"})

        # Check that the response is successful (200 or 403 for auth)
        assert response.status_code in (200, 403)

        # Check that CSV was called but PDF was not
        assert calls["csv"] == 1
        assert calls["pdf"] == 0, "PDF function should not be called in CSV endpoint"
    finally:
        # Restore original resolver
        P.resolve_patchable = original_resolve
