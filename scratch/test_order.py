import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_simulate_order_suite():
    print("\n--- 1. Testing Create Product for Vendor ---")
    p_res = client.post("/api/vendor/products?vendor_id=1", json={
        "name": "Wireless Ergonomic Mouse",
        "category": "Electronics",
        "price": 49.99,
        "stock": 100,
        "image_url": "https://images.unsplash.com/photo-1527864550417-7fd91fc51a46?w=500",
        "ai_description": "High precision wireless mouse"
    })
    assert p_res.status_code == 200
    prod = p_res.json()["product"]
    p_id = prod["id"]
    print(f"✓ Product created with ID #{p_id}")

    print("\n--- 2. Testing Simulate Order API ---")
    sim_res = client.post(f"/api/vendor/simulate-order?vendor_id=1&product_id={p_id}&units=2")
    assert sim_res.status_code == 200
    sim_json = sim_res.json()
    assert sim_json["success"] == True
    print(f"✓ Order simulated successfully: '{sim_json['message']}'")

    print("\n--- 3. Testing Vendor Dashboard Metrics Update ---")
    dash_res = client.get("/api/vendor/dashboard-data?vendor_id=1")
    assert dash_res.status_code == 200
    dash_data = dash_res.json()["data"]
    assert dash_data["total_sales"] == 2
    assert dash_data["total_revenue"] == 99.98
    assert dash_data["total_transactions"] == 1
    print(f"✓ Dashboard metrics updated live: Total Sales = {dash_data['total_sales']}, Total Revenue = ${dash_data['total_revenue']}, Transactions = {dash_data['total_transactions']}")

if __name__ == "__main__":
    test_simulate_order_suite()
    print("\n🎉 SIMULATE ORDER TEST SUITE PASSED 100% SUCCESSFULLY!")
