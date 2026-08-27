import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from fastapi.testclient import TestClient
from app.main import app, startup_db_seed
from app.database import get_db
from app import crud, schemas, models

client = TestClient(app)

def test_milestone2_suite():
    print("\n=======================================================")
    print("RUNNING MILESTONE 2 COMPREHENSIVE VALIDATION SUITE")
    print("=======================================================")

    # 1. Force seed database
    startup_db_seed()
    db = next(get_db())

    # Ensure a clean test vendor exists
    vendor = crud.get_vendor_by_email(db, "vendor@gmail.com")
    assert vendor is not None, "Test vendor must exist"
    vid = vendor.id

    # Add test items to trigger low stock and healthy stock
    p_low = crud.create_product(db, vid, schemas.ProductCreate(
        name="Pro Match Volleyball",
        category="Sports & Outdoors",
        price=15.00,
        stock=3, # Low stock (<= 5)
        ai_description="Professional grade leather volleyball for outdoor sports"
    ))

    p_out = crud.create_product(db, vid, schemas.ProductCreate(
        name="Ultra Fit Smartwatch",
        category="Electronics",
        price=120.00,
        stock=0, # Out of stock (0)
        ai_description="Advanced health tracker smartwatch with heart rate monitoring"
    ))

    p_healthy = crud.create_product(db, vid, schemas.ProductCreate(
        name="Pro Athletic Running Shoes",
        category="Clothing & Apparel",
        price=85.00,
        stock=45, # Healthy stock (> 5)
        ai_description="Lightweight breathable cushioning athletic running shoes"
    ))

    # --- 1. TEST INVENTORY TRACKING API (GET /api/vendor/inventory) ---
    print("\n[1/6] Testing Inventory Tracking & Low Stock Alerts API...")
    res_inv = client.get(f"/api/vendor/inventory?vendor_id={vid}&threshold=5")
    assert res_inv.status_code == 200, f"Expected 200 OK, got {res_inv.status_code}"
    inv_data = res_inv.json()["data"]

    summary = inv_data["summary"]
    alerts = inv_data["alerts"]

    print(f"  Total Products Tracked: {summary['total_products']}")
    print(f"  Low Stock Count (<= 5): {summary['low_stock_count']}")
    print(f"  Out of Stock Count (0): {summary['out_of_stock_count']}")

    assert summary["low_stock_count"] >= 1, "Should detect at least 1 low stock item"
    assert summary["out_of_stock_count"] >= 1, "Should detect at least 1 out of stock item"
    assert len(alerts["low_stock_items"]) >= 1, "Alerts array must contain low stock items"
    print("  [SUCCESS] Base Requirement 1: Inventory Tracking API Passed!")

    # --- 2. TEST SQL-BASED CUSTOMER SEGMENTATION API (GET /api/vendor/customer-segmentation) ---
    print("\n[2/6] Testing SQL-Based Customer Segmentation API...")
    crud.simulate_order(db, vid, p_healthy.id, units=7) # 7 * 85 = $595 -> VIP
    crud.simulate_order(db, vid, p_low.id, units=1)     # 1 * 15 = $15   -> Bronze

    res_seg = client.get(f"/api/vendor/customer-segmentation?vendor_id={vid}")
    assert res_seg.status_code == 200, f"Expected 200 OK, got {res_seg.status_code}"
    seg_data = res_seg.json()["data"]

    seg_summary = seg_data["summary"]
    print(f"  Total Unique Buyers: {seg_summary['total_customers']}")
    print(f"  VIP Buyers (>= $500): {seg_summary['vip_count']} (Revenue: ${seg_summary['vip_revenue']})")
    print(f"  Regular Buyers ($100-$499): {seg_summary['regular_count']} (Revenue: ${seg_summary['regular_revenue']})")
    print(f"  Bronze Buyers (< $100): {seg_summary['bronze_count']} (Revenue: ${seg_summary['bronze_revenue']})")

    assert seg_summary["total_customers"] >= 1, "Should track customer buyers"
    assert seg_summary["total_revenue"] > 0, "Total segmented revenue must be > 0"
    print("  [SUCCESS] Base Requirement 2: SQL Customer Segmentation API Passed!")

    # --- 3. TEST RULE-BASED RECOMMENDATIONS API (GET /api/vendor/recommendations) ---
    print("\n[3/6] Testing Rule-Based Recommendation System API...")
    res_rec = client.get(f"/api/vendor/recommendations?vendor_id={vid}")
    assert res_rec.status_code == 200, f"Expected 200 OK, got {res_rec.status_code}"
    rec_data = res_rec.json()["data"]

    top_selling = rec_data["top_selling_products"]
    recommendations = rec_data["recommendations"]

    print(f"  Top Selling Category Champions Count: {len(rec_data['category_champions'])}")
    print(f"  Generated Cross-Sell Recommendations Count: {len(recommendations)}")
    assert len(top_selling) >= 1, "Must return top selling items"
    assert len(recommendations) >= 1, "Must return cross-sell recommendations"
    print("  [SUCCESS] Base Requirement 3: Rule-Based Recommendation System API Passed!")

    # --- 4. TEST ADVANCED FEATURE 1: ML INVENTORY FORECASTING ---
    print("\n[4/6] Testing Advanced Feature: Machine Learning Inventory Forecasting...")
    res_fc = client.get(f"/api/vendor/forecasting?vendor_id={vid}&days=30")
    assert res_fc.status_code == 200, f"Expected 200 OK, got {res_fc.status_code}"
    fc_data = res_fc.json()["data"]
    print(f"  30-Day Sales Velocity: {fc_data['daily_sales_velocity']} units/day")
    print(f"  Predicted Demand (30 days): {fc_data['predicted_demand_units']} units")
    print(f"  Recommended Reorder Qty: {fc_data['recommended_reorder_qty']} units")
    assert "predicted_demand_units" in fc_data
    print("  [SUCCESS] Advanced Feature 1: ML Inventory Forecasting Passed!")

    # --- 5. TEST ADVANCED FEATURE 2: LLM SENTIMENT ANALYSIS ---
    print("\n[5/6] Testing Advanced Feature: LLM Review Sentiment Analysis...")
    sample_reviews = [
        "Great quality volleyball! Really durable and fast shipping.",
        "The smartwatch battery drains too fast, very disappointed with slow delivery."
    ]
    res_sent = client.post("/api/vendor/reviews/sentiment", params={"reviews": sample_reviews})
    assert res_sent.status_code == 200, f"Expected 200 OK, got {res_sent.status_code}"
    sent_data = res_sent.json()["data"]
    print(f"  Analyzed Reviews Count: {sent_data['total_reviews']}")
    print(f"  Overall Sentiment: {sent_data['overall_sentiment']}")
    print(f"  Extracted Top Pros: {sent_data['top_pros']}")
    print(f"  Extracted Top Cons: {sent_data['top_cons']}")
    assert sent_data["total_reviews"] == 2
    print("  [SUCCESS] Advanced Feature 2: LLM Review Sentiment Analysis Passed!")

    # --- 6. TEST ADVANCED FEATURE 3: VECTOR SEARCH RECOMMENDATIONS ---
    print("\n[6/6] Testing Advanced Feature: Vector Search & Semantic Recommendations...")
    res_vec = client.get(f"/api/vendor/semantic-search?vendor_id={vid}&query=running+shoes")
    assert res_vec.status_code == 200, f"Expected 200 OK, got {res_vec.status_code}"
    vec_data = res_vec.json()
    print(f"  Vector Search Query: '{vec_data['query']}' -> Total Semantic Matches: {vec_data['total_results']}")
    if vec_data["results"]:
        top_match = vec_data["results"][0]
        print(f"  Top Vector Match: '{top_match['name']}' (Cosine Similarity: {top_match['similarity_score']} / {top_match['match_confidence']})")
    assert vec_data["total_results"] >= 1
    print("  [SUCCESS] Advanced Feature 3: Vector Search Semantic Recommendations Passed!")

    print("\n=======================================================")
    print("ALL MILESTONE 2 BASE + ADVANCED FEATURES PASSED 100%!")
    print("=======================================================\n")

if __name__ == "__main__":
    test_milestone2_suite()
