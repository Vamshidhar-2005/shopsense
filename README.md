# 🛒 ShopSense Multi-Vendor Analytics & E-Commerce Platform

A modern FastAPI web application for **ShopSense** featuring role-based authentication (Vendor / Admin), MySQL/SQLite auto-fallback, and an analytics suite designed around the core milestone objective:

> 🎯 **Objective**: Introduce analytics, forecasting, and customer behavior insights.

---

## 🌟 Objective Core Modules & Features

### 📊 1. Analytics Subsystem
* **Real-time Order & Sales Tracking**: Aggregates gross revenue, completed orders, pending orders, and total transactions (`GET /api/vendor/insights`, `GET /api/vendor/dashboard-data`).
* **Sales Trends Engine**: Interactive daily, weekly, and monthly sales volume and revenue trend visualizations.
* **Inventory Tracking & Low-Stock Alerts**: Real-time stock level monitoring, total stock valuation, out-of-stock warnings, and low-stock threshold alerts (`GET /api/vendor/inventory`).

### 🔮 2. Inventory Demand Forecasting
* **File**: `app/forecasting.py`
* **REST API**: `GET /api/vendor/forecasting`
* **Algorithm**:
  * **Time-Series Sales Velocity**: Calculates daily sales rate per product.
  * **Demand Prediction**: Forecasts required units for 7, 14, or 30 days ahead.
  * **Stockout Risk & Safety Buffer**: Predicts estimated days until stockout and calculates safety stock reorder quantities.

### 👥 3. Customer Behavior Insights & AI
* **SQL Customer Spend Segmentation** (`GET /api/vendor/customer-segmentation`): Groups buyers into **VIP** (Spend ≥ $500), **Regular** ($100–$499.99), and **Bronze** (< $100) spend tiers.
* **LLM Review Sentiment Analysis** (`POST /api/vendor/reviews/sentiment`): Analyzes customer reviews, calculates sentiment scores (-1.0 to +1.0), and summarizes top pros/cons (`app/sentiment.py`).
* **Vector Search Semantic Recommendations** (`GET /api/vendor/semantic-search`): Generates text embeddings and ranks product recommendations using Cosine Similarity (`app/vector_search.py`).

---

## 📁 Project Directory Structure

```
shopsense/
├── app/
│   ├── __init__.py
│   ├── main.py                  # FastAPI application entry point & API endpoints
│   ├── database.py              # MySQL connection with SQLite auto-fallback & schema self-healing
│   ├── models.py                # SQLAlchemy DB models (Vendor, Admin, Product, Order)
│   ├── schemas.py               # Pydantic schemas for request/response validation
│   ├── auth.py                  # Password hashing (bcrypt) & auth helpers
│   ├── crud.py                  # Database CRUD logic & analytics aggregations
│   ├── forecasting.py           # ML Time-Series Inventory Demand Forecasting module
│   ├── sentiment.py             # LLM Customer Review Sentiment Analysis module
│   ├── vector_search.py         # Vector Search Cosine Similarity Recommendation engine
│   ├── static/
│   │   ├── css/
│   │   │   ├── style.css        # Core design system (glassmorphic styling, responsive layout)
│   │   │   └── admin.css        # Admin Portal dark theme design system
│   │   └── js/
│   │       ├── login.js         # Authentication page handlers
│   │       ├── vendor.js        # Vendor dashboard dynamic data & analytics loader
│   │       └── admin.js         # Admin dashboard approval handlers
│   └── templates/
│       ├── login.html           # Authentication portal
│       ├── vendor_dashboard.html# Vendor portal with Analytics, Forecasting & Insights UI
│       └── admin_dashboard.html # Admin management portal
├── scratch/
│   └── test_milestone2.py       # Automated test suite validating Analytics, Forecasting & Insights
├── requirements.txt             # Project Python dependencies
└── README.md                    # Project documentation
```

---

## 🚀 Setup & Running Instructions

1. **Install Dependencies**:
   ```powershell
   pip install -r requirements.txt
   ```

2. **Run Development Server**:
   ```powershell
   python -m uvicorn app.main:app --reload --port 8000
   ```

3. **Run Objective & Milestone Validation Test Suite**:
   ```powershell
   python scratch/test_milestone2.py
   ```

4. **Access Applications & API Documentation**:
   * **Vendor Analytics Portal**: `http://localhost:8000/vendor/dashboard`
   * **Admin Management Portal**: `http://localhost:8000/admin/dashboard`
   * **Interactive Swagger API Docs**: `http://localhost:8000/docs`
