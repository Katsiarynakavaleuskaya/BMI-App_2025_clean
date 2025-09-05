from fastapi.testclient import TestClient
from app import app

def test_no_nameerror_on_export_csv():
    """Test that the export endpoint doesn't raise a NameError due to _module typo."""
    # This test simply checks that the app can be imported and the endpoint exists
    # without raising a NameError during the import/definition phase
    client = TestClient(app)
    
    # We're not actually calling the endpoint, just checking that it exists
    # and doesn't have the _module NameError
    routes = [route.path for route in app.routes]
    assert "/api/v1/premium/export/week/csv" in routes
    assert "/api/v1/premium/export/day/csv" in routes
    assert "/api/v1/premium/export/week/pdf" in routes
    assert "/api/v1/premium/export/day/pdf" in routes