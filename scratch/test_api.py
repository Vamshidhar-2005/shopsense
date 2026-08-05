import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_zero_hardcode_insights_suite():
    print("\n--- 1. Testing Insights Page HTML Template for Zero Hardcoded Samples ---")
    res = client.get("/vendor/dashboard")
    assert res.status_code == 200
    text = res.text

    # Verify hardcoded sample numbers and items are NOT in HTML
    assert "248" not in text
    assert "184" not in text
    assert "43" not in text
    assert "21" not in text
    assert "Wireless Pro Headphones" not in text
    assert "Smart Fitness Watch" not in text
    assert "Ultra Cushion Running Shoes" not in text

    # Verify required visible section headings
    assert "Customer Order Statistics" in text
    assert "Total Orders" in text
    assert "Completed Orders" in text
    assert "Pending Orders" in text
    assert "Cancelled Orders" in text
    assert "Sales Trends" in text
    assert "No sales trend data available yet." in text
    assert "No products available." in text
    print("✓ Zero hardcoded data confirmed in HTML template!")

    print("\n--- 2. Testing Insights API Endpoint ---")
    insights_res = client.get("/api/vendor/insights?vendor_id=1")
    assert insights_res.status_code == 200
    data = insights_res.json()
    assert data["success"] == True
    stats = data["insights"]["order_stats"]
    assert stats["total_orders"] == 0
    assert stats["completed_orders"] == 0
    assert stats["pending_orders"] == 0
    assert stats["cancelled_orders"] == 0
    assert len(data["insights"]["sales_trends"]) == 0
    assert len(data["insights"]["best_selling_products"]) == 0
    print("✓ API returns zeroes and empty arrays when no orders exist in DB!")

if __name__ == "__main__":
    test_zero_hardcode_insights_suite()
    print("\n🎉 ZERO-HARDCODE INSIGHTS TEST SUITE PASSED SUCCESSFULLY!")
