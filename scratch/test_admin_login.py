import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from fastapi.testclient import TestClient
from app.main import app, startup_db_seed

client = TestClient(app)

def test_admin_login_suite():
    # Force seed to ensure admin account is ready
    startup_db_seed()

    print("\n--- Testing Admin Login API ---")
    res = client.post("/api/login", json={
        "email": "admin@gmail.com",
        "password": "admin123",
        "role": "admin"
    })
    assert res.status_code == 200
    body = res.json()
    assert body["success"] == True
    assert body["redirect_url"] == "/admin/dashboard"
    print(f"✓ Admin Login Successful: {body['message']} -> Redirects to {body['redirect_url']}")

    print("\n--- Testing Vendor Login API ---")
    v_res = client.post("/api/login", json={
        "email": "vendor@gmail.com",
        "password": "vendor123",
        "role": "vendor"
    })
    assert v_res.status_code == 200
    v_body = v_res.json()
    assert v_body["success"] == True
    assert v_body["redirect_url"] == "/vendor/dashboard"
    print(f"✓ Vendor Login Successful: {v_body['message']} -> Redirects to {v_body['redirect_url']}")

if __name__ == "__main__":
    test_admin_login_suite()
    print("\n🎉 ALL AUTHENTICATION TESTS PASSED 100% SUCCESSFULLY!")
