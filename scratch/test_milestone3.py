import sys
import os
import json
from fastapi.testclient import TestClient

# Ensure app package is importable
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.main import app

def run_milestone3_test_suite():
    print("=" * 80)
    print("           SHOPSENSE MILESTONE 3 AUTOMATED VERIFICATION SUITE")
    print("=" * 80)

    client = TestClient(app)
    passed_tests = 0
    total_tests = 7

    # Test 1: Frontend Chart Analytics API
    print("\n[1/7] Testing Frontend Chart Analytics API (GET /api/vendor/analytics/charts)...")
    res1 = client.get("/api/vendor/analytics/charts?vendor_id=1&period=daily")
    if res1.status_code == 200 and res1.json().get("success"):
        data = res1.json().get("data", {})
        if "sales_trend_chart" in data and "category_distribution_chart" in data:
            print("  --> SUCCESS: Returns formatted chart series and category breakdown! (200 OK)")
            passed_tests += 1
        else:
            print(f"  --> FAILED: Payload missing chart keys: {data}")
    else:
        print(f"  --> FAILED: HTTP {res1.status_code} - {res1.text}")

    # Test 2: Marketplace Benchmarking Metrics API
    print("\n[2/7] Testing Marketplace Benchmarking API (GET /api/vendor/analytics/benchmarking)...")
    res2 = client.get("/api/vendor/analytics/benchmarking?vendor_id=1")
    if res2.status_code == 200 and res2.json().get("success"):
        data = res2.json().get("data", {})
        metrics = data.get("metrics", {})
        if "average_order_value" in metrics and "percentile_badge" in data:
            print(f"  --> SUCCESS: Vendor AOV (${metrics['average_order_value']['vendor']}) vs. Mkt Avg (${metrics['average_order_value']['marketplace_avg']}) [{data['percentile_badge']}]! (200 OK)")
            passed_tests += 1
        else:
            print(f"  --> FAILED: Payload missing benchmarking keys: {data}")
    else:
        print(f"  --> FAILED: HTTP {res2.status_code} - {res2.text}")

    # Test 3: Export Sales CSV
    print("\n[3/7] Testing Sales CSV Report Export (GET /api/vendor/export/sales-csv)...")
    res3 = client.get("/api/vendor/export/sales-csv?vendor_id=1")
    if res3.status_code == 200 and "text/csv" in res3.headers.get("content-type", ""):
        if "Order ID,Customer Name" in res3.text:
            print("  --> SUCCESS: Generated downloadable Sales CSV Stream! (200 OK)")
            passed_tests += 1
        else:
            print(f"  --> FAILED: Invalid CSV content: {res3.text[:100]}")
    else:
        print(f"  --> FAILED: HTTP {res3.status_code} - {res3.headers}")

    # Test 4: Export Inventory CSV
    print("\n[4/7] Testing Inventory CSV Report Export (GET /api/vendor/export/inventory-csv)...")
    res4 = client.get("/api/vendor/export/inventory-csv?vendor_id=1")
    if res4.status_code == 200 and "text/csv" in res4.headers.get("content-type", ""):
        if "Product ID,Product Name" in res4.text:
            print("  --> SUCCESS: Generated downloadable Inventory CSV Stream! (200 OK)")
            passed_tests += 1
        else:
            print(f"  --> FAILED: Invalid CSV content: {res4.text[:100]}")
    else:
        print(f"  --> FAILED: HTTP {res4.status_code} - {res4.headers}")

    # Test 5: Export Benchmarking CSV
    print("\n[5/7] Testing Benchmarking CSV Export (GET /api/vendor/export/benchmarking-csv)...")
    res5 = client.get("/api/vendor/export/benchmarking-csv?vendor_id=1")
    if res5.status_code == 200 and "text/csv" in res5.headers.get("content-type", ""):
        if "Metric Category,Vendor Value" in res5.text:
            print("  --> SUCCESS: Generated downloadable Benchmarking CSV Stream! (200 OK)")
            passed_tests += 1
        else:
            print(f"  --> FAILED: Invalid CSV content: {res5.text[:100]}")
    else:
        print(f"  --> FAILED: HTTP {res5.status_code} - {res5.headers}")

    # Test 6: RAG AI Shopping Assistant API
    print("\n[6/7] Testing RAG AI Shopping Assistant (POST /api/vendor/rag/assistant)...")
    res6 = client.post("/api/vendor/rag/assistant?query=running+shoes&vendor_id=1")
    if res6.status_code == 200 and res6.json().get("success"):
        data = res6.json().get("data", {})
        if "rag_response" in data and "retrieved_products" in data:
            print(f"  --> SUCCESS: RAG Retrieval retrieved {data['total_retrieved']} product matches! (200 OK)")
            passed_tests += 1
        else:
            print(f"  --> FAILED: Payload missing RAG keys: {data}")
    else:
        print(f"  --> FAILED: HTTP {res6.status_code} - {res6.text}")

    # Test 7: AI Data Analyst Text-to-SQL API
    print("\n[7/7] Testing AI Data Analyst Text-to-SQL (POST /api/vendor/ai-analyst/query)...")
    res7 = client.post("/api/vendor/ai-analyst/query?query=who+is+my+top+customer&vendor_id=1")
    if res7.status_code == 200 and res7.json().get("success"):
        data = res7.json().get("data", {})
        if "generated_sql" in data and "ai_explanation" in data:
            print(f"  --> SUCCESS: Text-to-SQL generated: [{data['generated_sql']}]! (200 OK)")
            passed_tests += 1
        else:
            print(f"  --> FAILED: Payload missing Text-to-SQL keys: {data}")
    else:
        print(f"  --> FAILED: HTTP {res7.status_code} - {res7.text}")

    print("\n" + "=" * 80)
    print(f"               RESULT: {passed_tests}/{total_tests} MILESTONE 3 TESTS PASSED")
    print("=" * 80)
    return passed_tests == total_tests

if __name__ == "__main__":
    success = run_milestone3_test_suite()
    sys.exit(0 if success else 1)
