"""
Comprehensive Pytest Suite for ShopSense Multi-Vendor Platform (Milestones 1, 2, 3, 4).
"""

def test_root_redirect(client):
    """Test root URL redirects to login."""
    response = client.get("/", follow_redirects=False)
    assert response.status_code == 302
    assert response.headers["location"] == "/login"

def test_admin_metrics(client):
    """Test Admin metrics API endpoint."""
    response = client.get("/api/admin/metrics")
    assert response.status_code == 200
    json_data = response.json()
    assert json_data["success"] is True
    assert "metrics" in json_data

def test_vendor_dashboard_data(client):
    """Test Vendor dashboard sales & revenue summary API."""
    response = client.get("/api/vendor/dashboard-data?vendor_id=1")
    assert response.status_code == 200
    json_data = response.json()
    assert json_data["success"] is True
    assert "data" in json_data

def test_milestone2_inventory_tracking(client):
    """Test Milestone 2 Inventory Tracking & Stock Alerts API."""
    response = client.get("/api/vendor/inventory?vendor_id=1&threshold=5")
    assert response.status_code == 200
    json_data = response.json()
    assert json_data["success"] is True

def test_milestone2_customer_segmentation(client):
    """Test Milestone 2 Customer Spend Segmentation API."""
    response = client.get("/api/vendor/customer-segmentation?vendor_id=1")
    assert response.status_code == 200
    json_data = response.json()
    assert json_data["success"] is True

def test_milestone2_ml_forecasting(client):
    """Test Milestone 2 ML Demand Forecasting API."""
    response = client.get("/api/vendor/forecasting?vendor_id=1&days=30")
    assert response.status_code == 200
    json_data = response.json()
    assert json_data["success"] is True

def test_milestone2_llm_sentiment(client):
    """Test Milestone 2 LLM Review Sentiment Analysis API."""
    review_text = "The product quality is top notch, amazing visual clarity!"
    response = client.post(f"/api/vendor/reviews/sentiment?reviews={review_text}")
    assert response.status_code == 200
    json_data = response.json()
    assert json_data["success"] is True

def test_milestone3_rag_shopping_assistant(client):
    """Test Milestone 3 RAG AI Shopping Assistant API."""
    response = client.post("/api/vendor/rag/assistant?query=best running shoes")
    assert response.status_code == 200
    json_data = response.json()
    assert json_data["success"] is True

def test_milestone3_product_comparison(client):
    """Test Milestone 3 Product Comparison & Best Value Engine."""
    payload = {"product_ids": [1, 2]}
    response = client.post("/api/vendor/products/compare", json=payload)
    assert response.status_code == 200
    json_data = response.json()
    assert json_data["success"] is True

def test_milestone3_csv_export(client):
    """Test Milestone 3 Sales CSV Download API."""
    response = client.get("/api/vendor/export/sales-csv?vendor_id=1")
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/csv")

def test_milestone4_autonomous_ai_agent(client):
    """Test Milestone 4 Autonomous AI Strategic Agent Audit API."""
    response = client.post("/api/vendor/agent/autonomous-audit?vendor_id=1")
    assert response.status_code == 200
    json_data = response.json()
    assert json_data["success"] is True
    assert "health_score" in json_data["data"]
