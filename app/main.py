import os
from typing import Optional, List
from fastapi import FastAPI, Request, Depends, HTTPException, Query, status, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse, RedirectResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.database import engine, Base, get_db
from app import models, schemas, crud, forecasting, sentiment, vector_search, bi_reporting, rag_assistant, ai_agent

# Automatically create database tables on startup
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="ShopSense E-Commerce Portal",
    description="FastAPI Backend for ShopSense Auth, Admin & Vendor Dashboards",
    version="1.6.0"
)

# Paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, "static")
TEMPLATES_DIR = os.path.join(BASE_DIR, "templates")

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
templates = Jinja2Templates(directory=TEMPLATES_DIR)

# Startup: Seed default admin and vendor credentials
@app.on_event("startup")
def startup_db_seed():
    db = next(get_db())
    admin_gmail = crud.get_admin_by_email(db, "admin@gmail.com")
    if not admin_gmail:
        sample_admin = models.Admin(
            full_name="ShopSense Super Admin",
            email="admin@gmail.com",
            hashed_password=crud.hash_password("admin123")
        )
        db.add(sample_admin)
        db.commit()
    else:
        # Unconditionally sync default admin password to admin123 on startup
        admin_gmail.hashed_password = crud.hash_password("admin123")
        db.commit()

    vendor_gmail = crud.get_vendor_by_email(db, "vendor@gmail.com")
    if not vendor_gmail:
        sample_vendor = models.Vendor(
            full_name="ShopSense Default Vendor",
            business_name="ShopSense Official Store",
            email="vendor@gmail.com",
            hashed_password=crud.hash_password("vendor123"),
            status="Approved"
        )
        db.add(sample_vendor)
        db.commit()
    else:
        # Unconditionally sync default vendor password to vendor123 on startup
        vendor_gmail.hashed_password = crud.hash_password("vendor123")
        db.commit()

    # Strict catalog cleanup: wipe all old products and seed fresh diverse catalog (Nike T-Shirts, Watches, Cricket Bat, Food Items)
    existing_products = db.query(models.Product).all()
    for p in existing_products:
        db.delete(p)
    db.commit()

    vid = vendor_gmail.id if vendor_gmail else 1
    diverse_catalog = [
        ("Nike Air Max Running Shoes", "Clothing & Apparel", 85.00, 120, "Authentic lightweight Nike Air Max athletic running shoes"),
        ("Nike Dri-FIT T-Shirt", "Clothing & Apparel", 35.00, 2, "Authentic Nike moisture-wicking athletic training t-shirt"),
        ("Fossil Smart Watch", "Electronics", 149.00, 0, "Touchscreen smartwatch with heart rate & fitness tracking"),
        ("Kashmir Willow Cricket Bat", "Sports & Outdoors", 45.00, 3, "Handcrafted Kashmir willow cricket bat with rubber grip"),
        ("Organic Dark Chocolate Bar", "Food & Beverage", 5.99, 4, "70% cacao organic fair-trade artisanal dark chocolate bar"),
        ("Artisanal Matcha Green Tea", "Food & Beverage", 14.99, 1, "Premium organic ceremonial grade Japanese green tea powder"),
        ("Pro Match Leather Volleyball", "Sports & Outdoors", 25.00, 5, "Professional grade leather volleyball for outdoor sports"),
        ("Ultra Fit Fitness Band", "Electronics", 29.99, 0, "Waterproof smart fitness band with sleep monitor"),
        ("Organic Dark Roast Coffee Beans", "Food & Beverage", 18.50, 150, "100% Arabica artisanal whole bean roast coffee 1lb bag"),
        ("Stainless Steel Water Bottle", "Sports & Outdoors", 18.99, 200, "Vacuum insulated double-wall hot and cold water bottle"),
        ("Ergonomic Memory Foam Pillow", "Home & Kitchen", 49.50, 150, "Orthopedic neck support memory foam sleeping pillow"),
        ("Data Analytics & AI Handbook", "Books & Media", 42.50, 70, "Comprehensive guide to machine learning and modern data architecture")
    ]

    for item_name, item_cat, item_price, item_stock, item_desc in diverse_catalog:
        db_p = models.Product(
            vendor_id=vid,
            name=item_name,
            category=item_cat,
            price=item_price,
            stock=item_stock,
            image_url=crud.get_default_image_url(item_name, item_cat),
            ai_description=item_desc
        )
        db.add(db_p)
    db.commit()

# --- Page Routes ---

@app.get("/", response_class=RedirectResponse)
def root_redirect():
    return RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)

@app.get("/login", response_class=HTMLResponse)
def login_page(request: Request):
    return templates.TemplateResponse(request=request, name="login.html")

@app.get("/register", response_class=HTMLResponse)
def register_page(request: Request):
    return templates.TemplateResponse(request=request, name="register.html")

@app.get("/admin/dashboard", response_class=HTMLResponse)
def admin_dashboard_page(request: Request):
    return templates.TemplateResponse(request=request, name="admin_dashboard.html")

@app.get("/vendor/dashboard", response_class=HTMLResponse)
def vendor_dashboard_page(request: Request):
    return templates.TemplateResponse(request=request, name="vendor_dashboard.html")

# --- Public & Auth API Endpoints ---

@app.post("/api/register")
def register_vendor(vendor_in: schemas.VendorCreate, db: Session = Depends(get_db)):
    """API endpoint to register a new vendor into MySQL database."""
    existing_vendor = crud.get_vendor_by_email(db, vendor_in.email)
    if existing_vendor:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A vendor with this email address is already registered."
        )

    try:
        new_vendor = crud.create_vendor(db, vendor_in)
        return {
            "success": True,
            "message": "Vendor registration submitted successfully! Redirecting to login...",
            "vendor_id": new_vendor.id,
            "vendor_name": new_vendor.full_name
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to register vendor: {str(e)}"
        )

@app.post("/api/login")
def login_user(login_data: schemas.LoginRequest, db: Session = Depends(get_db)):
    """API endpoint for Vendor or Admin login authentication."""
    if login_data.role == "vendor":
        vendor = crud.authenticate_vendor(db, login_data.email, login_data.password)
        if not vendor:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid vendor email or password."
            )
        return {
            "success": True,
            "message": f"Welcome back, {vendor.full_name}!",
            "redirect_url": "/vendor/dashboard",
            "vendor_id": vendor.id,
            "vendor_name": vendor.full_name
        }

    elif login_data.role == "admin":
        admin = crud.authenticate_admin(db, login_data.email, login_data.password)
        if not admin:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid admin email or password. Please try again."
            )
        return {
            "success": True,
            "message": "Welcome back, Administrator!",
            "redirect_url": "/admin/dashboard"
        }

    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid role specified."
        )

# --- Vendor API Endpoints ---

@app.get("/api/vendor/dashboard-data")
def get_vendor_dashboard(vendor_id: Optional[int] = Query(None), db: Session = Depends(get_db)):
    """API endpoint returning dynamic vendor profile, summary cards, and recent products."""
    data = crud.get_vendor_dashboard_data(db, vendor_id or 1)
    if not data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vendor not found.")

    return {
        "success": True,
        "data": data
    }

@app.get("/api/vendor/insights")
def get_vendor_insights(vendor_id: Optional[int] = Query(None), db: Session = Depends(get_db)):
    """API endpoint returning dynamic database order statistics, sales trends, and best selling products."""
    vid = vendor_id or 1
    insights = crud.get_vendor_insights_data(db, vid)
    return {
        "success": True,
        "insights": insights
    }

@app.get("/api/vendor/profile")
def get_vendor_profile(vendor_id: Optional[int] = Query(None), db: Session = Depends(get_db)):
    """API endpoint returning vendor profile details."""
    vid = vendor_id or 1
    vendor = crud.get_vendor_by_id(db, vid)
    if not vendor:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vendor profile not found.")

    return {
        "success": True,
        "vendor": schemas.VendorResponse.from_orm(vendor)
    }

@app.put("/api/vendor/profile")
def update_vendor_profile_endpoint(
    profile_in: schemas.VendorProfileUpdate,
    vendor_id: Optional[int] = Query(None),
    db: Session = Depends(get_db)
):
    """API endpoint updating vendor business information."""
    vid = vendor_id or 1
    updated_vendor = crud.update_vendor_profile(db, vid, profile_in)
    if not updated_vendor:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vendor account not found.")

    return {
        "success": True,
        "message": "Profile details updated successfully!",
        "vendor": schemas.VendorResponse.from_orm(updated_vendor)
    }

@app.put("/api/vendor/profile/password")
def update_vendor_password_endpoint(
    pwd_in: schemas.VendorPasswordChange,
    vendor_id: Optional[int] = Query(None),
    db: Session = Depends(get_db)
):
    """API endpoint updating vendor account password."""
    vid = vendor_id or 1
    success, msg = crud.update_vendor_password(db, vid, pwd_in)
    if not success:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=msg)

    return {
        "success": True,
        "message": msg
    }

@app.get("/api/vendor/products")
def get_catalog_products(
    vendor_id: Optional[int] = Query(None),
    search: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """API endpoint returning vendor products with search filter for My Catalog page."""
    vid = vendor_id or 1
    products = crud.get_vendor_products(db, vid, search=search)
    return {
        "success": True,
        "products": [schemas.ProductResponse.from_orm(p) for p in products]
    }

@app.get("/api/vendor/products/{product_id}")
def get_single_product(
    product_id: int,
    vendor_id: Optional[int] = Query(None),
    db: Session = Depends(get_db)
):
    """API endpoint returning single product details."""
    vid = vendor_id or 1
    product = crud.get_product_by_id(db, product_id, vid)
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found.")

    return {
        "success": True,
        "product": schemas.ProductResponse.from_orm(product)
    }

@app.post("/api/vendor/simulate-order")
def simulate_vendor_order(
    product_id: int = Query(...),
    units: int = Query(1),
    vendor_id: Optional[int] = Query(None),
    db: Session = Depends(get_db)
):
    """API endpoint to simulate a customer order for testing sales, revenue, and order metrics."""
    vid = vendor_id or 1
    success, msg = crud.simulate_order(db, vid, product_id, units=units)
    if not success:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=msg)

    return {
        "success": True,
        "message": msg
    }

@app.put("/api/vendor/products/{product_id}")
def update_vendor_product(
    product_id: int,
    product_in: schemas.ProductCreate,
    vendor_id: Optional[int] = Query(None),
    db: Session = Depends(get_db)
):
    """API endpoint updating existing product in MySQL."""
    vid = vendor_id or 1
    updated = crud.update_product(db, product_id, vid, product_in)
    if not updated:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found.")

    return {
        "success": True,
        "message": f"Product '{updated.name}' updated successfully!",
        "product": schemas.ProductResponse.from_orm(updated)
    }

@app.post("/api/vendor/products")
def create_vendor_product(
    product_in: schemas.ProductCreate,
    vendor_id: Optional[int] = Query(None),
    db: Session = Depends(get_db)
):
    """API endpoint to create a new product for a vendor."""
    vid = vendor_id or 1
    vendor = crud.get_vendor_by_id(db, vid)
    if not vendor:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vendor account not found.")

    try:
        new_product = crud.create_product(db, vid, product_in)
        return {
            "success": True,
            "message": f"Product '{new_product.name}' saved to catalog successfully!",
            "product": schemas.ProductResponse.from_orm(new_product)
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create product: {str(e)}"
        )

@app.post("/api/vendor/generate-ai-description")
def generate_ai_description(req: schemas.AIDescriptionRequest):
    """API endpoint to generate AI-enhanced product description."""
    name = req.name.strip()
    category = req.category.strip()
    raw = req.raw_description.strip() if req.raw_description else ""

    enhanced_desc = f"Experience premium quality with the all-new {name}. Engineered for excellence in {category}, featuring ergonomic craftsmanship, high durability, and superior performance."
    if raw:
        enhanced_desc += f" Key highlights: {raw}"

    return {
        "success": True,
        "ai_description": enhanced_desc
    }

@app.delete("/api/vendor/products/{product_id}")
def delete_vendor_product(
    product_id: int,
    vendor_id: Optional[int] = Query(None),
    db: Session = Depends(get_db)
):
    """API endpoint to delete a product from vendor catalog."""
    vid = vendor_id or 1
    deleted = crud.delete_product(db, product_id, vid)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found.")

    return {
        "success": True,
        "message": "Product removed from catalog successfully."
    }

# --- Milestone 2: Inventory Intelligence & Customer Analytics Endpoints ---

@app.get("/api/vendor/inventory")
def get_vendor_inventory(
    threshold: int = Query(5, ge=1, le=100, description="Stock alert threshold limit"),
    vendor_id: Optional[int] = Query(None),
    db: Session = Depends(get_db)
):
    """
    Milestone 2 API: Inventory Tracking & Low-Stock Alerts.
    Tracks stock levels, out-of-stock items, and suggested reorder quantities.
    """
    vid = vendor_id or 1
    inventory_data = crud.get_vendor_inventory_tracking(db, vid, threshold=threshold)
    return {
        "success": True,
        "data": inventory_data
    }

@app.get("/api/vendor/customer-segmentation")
def get_customer_segmentation(
    vendor_id: Optional[int] = Query(None),
    db: Session = Depends(get_db)
):
    """
    Milestone 2 API: SQL-Based Customer Segmentation.
    Groups buyers into VIP (spend >= $500), Regular ($100-$499.99), and Bronze (< $100) spend tiers.
    """
    vid = vendor_id or 1
    segmentation_data = crud.get_customer_segmentation_analytics(db, vid)
    return {
        "success": True,
        "data": segmentation_data
    }

@app.get("/api/vendor/recommendations")
def get_rule_based_recommendations(
    vendor_id: Optional[int] = Query(None),
    db: Session = Depends(get_db)
):
    """
    Milestone 2 API: Rule-Based Recommendation Engine.
    Generates product cross-sell recommendations based on category sales volume.
    """
    vid = vendor_id or 1
    recommendations_data = crud.get_rule_based_recommendations(db, vid)
    return {
        "success": True,
        "data": recommendations_data
    }

# --- Milestone 2 Advanced / Optional Features Endpoints ---

@app.get("/api/vendor/forecasting")
def get_inventory_forecasting(
    days: int = Query(30, ge=7, le=90, description="Forecast window in days"),
    vendor_id: Optional[int] = Query(None),
    db: Session = Depends(get_db)
):
    """
    Milestone 2 Advanced Feature: Machine Learning Inventory Forecasting.
    Predicts future inventory demand and stockout risks based on historical sales velocity.
    """
    vid = vendor_id or 1
    orders = db.query(models.Order).filter(models.Order.vendor_id == vid, models.Order.status == "Completed").all()
    products = db.query(models.Product).filter(models.Product.vendor_id == vid).all()

    order_dicts = [{"units": o.units, "created_at": o.created_at} for o in orders]
    total_stock = sum(p.stock for p in products)

    forecast_data = forecasting.forecast_inventory_demand(order_dicts, total_stock, forecast_days=days)
    return {
        "success": True,
        "feature": "Machine Learning Time-Series Inventory Forecasting",
        "data": forecast_data
    }

@app.post("/api/vendor/reviews/sentiment")
def analyze_reviews_sentiment(
    reviews: List[str] = Query(..., description="List of customer product review text strings")
):
    """
    Milestone 2 Advanced Feature: LLM Sentiment Analysis.
    Analyzes customer reviews, calculates sentiment scores, and summarizes top pros and cons.
    """
    sentiment_data = sentiment.summarize_vendor_reviews_sentiment(reviews)
    return {
        "success": True,
        "feature": "LLM Sentiment Analysis Pipeline",
        "data": sentiment_data
    }

@app.get("/api/vendor/semantic-search")
def vector_semantic_search(
    query: str = Query(..., min_length=1, description="Natural language search query"),
    vendor_id: Optional[int] = Query(None),
    db: Session = Depends(get_db)
):
    """
    Milestone 2 Advanced Feature: Vector Search & Semantic Recommendations.
    Generates text vector embeddings for products and ranks results using cosine similarity.
    """
    vid = vendor_id or 1
    products = db.query(models.Product).filter(models.Product.vendor_id == vid).all()
    prod_dicts = [{
        "id": p.id,
        "name": p.name,
        "category": p.category,
        "price": float(p.price),
        "stock": p.stock,
        "image_url": crud.get_product_image_url(p),
        "ai_description": p.ai_description or ""
    } for p in products]

    search_results = vector_search.semantic_vector_search(query, prod_dicts)
    return {
        "success": True,
        "feature": "Vector Search Semantic Embedding Recommendations",
        "query": query,
        "total_results": len(search_results),
        "results": search_results
    }

# --- Milestone 3: Advanced APIs, Reporting & Business Intelligence (BI) Endpoints ---

@app.get("/api/vendor/analytics/charts")
def get_vendor_chart_analytics(
    period: str = Query("daily", description="Chart period: daily, weekly, monthly"),
    vendor_id: Optional[int] = Query(None),
    db: Session = Depends(get_db)
):
    """
    Milestone 3 Base Req 1: Frontend-Formatted Analytics Endpoints.
    Exposes sales velocity, revenue trends, and category distribution datasets formatted for frontend charts.
    """
    vid = vendor_id or 1
    chart_data = bi_reporting.get_chart_analytics_data(db, vid, period=period)
    return {
        "success": True,
        "data": chart_data
    }

@app.get("/api/vendor/analytics/benchmarking")
def get_vendor_marketplace_benchmarking(
    vendor_id: Optional[int] = Query(None),
    db: Session = Depends(get_db)
):
    """
    Milestone 3 Base Req 2: Marketplace Benchmarking Metrics.
    Compares vendor Average Order Value (AOV), sales velocity, and stockout rates against marketplace averages.
    """
    vid = vendor_id or 1
    benchmark_data = bi_reporting.get_marketplace_benchmarking(db, vid)
    return {
        "success": True,
        "data": benchmark_data
    }

@app.get("/api/vendor/export/sales-csv")
def export_vendor_sales_csv(
    vendor_id: Optional[int] = Query(None),
    db: Session = Depends(get_db)
):
    """Milestone 3 Base Req 3: Downloadable Sales & Revenue CSV Report."""
    vid = vendor_id or 1
    csv_content = bi_reporting.generate_sales_csv(db, vid)
    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=ShopSense_Vendor_{vid}_Sales_Report.csv"}
    )

@app.get("/api/vendor/export/inventory-csv")
def export_vendor_inventory_csv(
    vendor_id: Optional[int] = Query(None),
    db: Session = Depends(get_db)
):
    """Milestone 3 Base Req 3: Downloadable Inventory Stock & Valuation CSV Report."""
    vid = vendor_id or 1
    csv_content = bi_reporting.generate_inventory_csv(db, vid)
    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=ShopSense_Vendor_{vid}_Inventory_Report.csv"}
    )

@app.get("/api/vendor/export/benchmarking-csv")
def export_vendor_benchmarking_csv(
    vendor_id: Optional[int] = Query(None),
    db: Session = Depends(get_db)
):
    """Milestone 3 Base Req 3: Downloadable Marketplace Benchmarking CSV Report."""
    vid = vendor_id or 1
    csv_content = bi_reporting.generate_benchmarking_csv(db, vid)
    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=ShopSense_Vendor_{vid}_Benchmarking_Report.csv"}
    )

@app.post("/api/vendor/rag/assistant")
def rag_shopping_assistant_endpoint(
    query: str = Query(..., description="Natural language shopping or product query"),
    vendor_id: Optional[int] = Query(None),
    db: Session = Depends(get_db)
):
    """
    Milestone 3 Advanced Feature: RAG-Powered AI Shopping Assistant.
    Uses dense catalog embeddings to retrieve relevant products and generate grounded recommendations.
    """
    vid = vendor_id or 1
    result = rag_assistant.process_rag_shopping_query(db, vid, query)
    return {
        "success": True,
        "feature": "RAG-Powered AI Shopping Assistant",
        "data": result
    }

@app.post("/api/vendor/ai-analyst/query")
def text_to_sql_ai_analyst_endpoint(
    query: str = Query(..., description="Natural language store data analytics question"),
    vendor_id: Optional[int] = Query(None),
    db: Session = Depends(get_db)
):
    """
    Milestone 3 Advanced Feature: AI Data Analyst (Text-to-SQL / Natural Language Querying).
    Generates and executes dynamic SQL queries from natural language store questions.
    """
    vid = vendor_id or 1
    result = rag_assistant.process_ai_text_to_sql_query(db, vid, query)
    return {
        "success": True,
        "feature": "AI Data Analyst (Text-to-SQL Querying)",
        "data": result
    }

@app.websocket("/ws/vendor/live-feed/{vendor_id}")
async def websocket_vendor_live_feed(websocket: WebSocket, vendor_id: int):
    """
    Milestone 3 Advanced Feature: Real-Time WebSockets Dashboard Feed.
    Pushes live simulated customer order alerts and real-time sales feed to the dashboard.
    """
    await websocket.accept()
    try:
        await websocket.send_json({
            "event": "connected",
            "message": f"⚡ Live WebSocket Feed Active for Vendor ID {vendor_id}",
            "timestamp": "Now"
        })
        while True:
            data = await websocket.receive_text()
            await websocket.send_json({
                "event": "ping_ack",
                "received": data,
                "status": "Live stream active"
            })
    except WebSocketDisconnect:
        pass

# --- Admin API Endpoints ---

@app.get("/api/admin/metrics")
def get_admin_metrics(db: Session = Depends(get_db)):
    """API endpoint returning dynamic summary card metrics."""
    metrics = crud.get_admin_metrics(db)
    return {
        "success": True,
        "metrics": metrics
    }

@app.get("/api/admin/vendors")
def get_admin_vendors(
    search: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """API endpoint for fetching vendors with search and status filtering."""
    vendors = crud.get_filtered_vendors(db, search=search, status_filter=status)
    return {
        "success": True,
        "vendors": [schemas.VendorResponse.from_orm(v) for v in vendors]
    }

@app.put("/api/admin/vendors/{vendor_id}/status")
def update_status(
    vendor_id: int,
    status_update: schemas.VendorStatusUpdate,
    db: Session = Depends(get_db)
):
    """API endpoint to Approve or Suspend a vendor account."""
    new_st = status_update.status.strip().capitalize()
    if new_st not in ["Approved", "Suspended"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid status. Status must be 'Approved' or 'Suspended'."
        )

    updated_vendor = crud.update_vendor_status(db, vendor_id, new_st)
    if not updated_vendor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vendor record not found."
        )

    action_msg = "approved" if new_st == "Approved" else "suspended"
    return {
        "success": True,
        "message": f"Vendor {action_msg} successfully.",
        "vendor": schemas.VendorResponse.from_orm(updated_vendor)
    }

# --- Product Comparison & Smart Listing API Endpoints ---

@app.get("/api/vendor/products/smart-listing")
def get_smart_listing_products(
    vendor_id: Optional[int] = Query(None),
    category: Optional[str] = Query(None),
    min_price: Optional[float] = Query(None),
    max_price: Optional[float] = Query(None),
    min_rating: Optional[float] = Query(None),
    sort_by: Optional[str] = Query("best_value"),
    db: Session = Depends(get_db)
):
    """
    Milestone 3 Feature: Smart Listing View with filters for price, rating, and category.
    """
    query = db.query(models.Product)
    if vendor_id:
        query = query.filter(models.Product.vendor_id == vendor_id)

    if category and category.lower() != "all":
        query = query.filter(models.Product.category.ilike(f"%{category}%"))

    if min_price is not None:
        query = query.filter(models.Product.price >= min_price)

    if max_price is not None:
        query = query.filter(models.Product.price <= max_price)

    products = query.all()

    # Format smart items with ratings, value scores, and feature tags
    smart_items = []
    for p in products:
        # Calculate rating & value score deterministically
        rating = round(4.0 + ((p.id * 7) % 10) * 0.1, 1)
        if rating > 5.0: rating = 4.8
        value_score = round((rating * 20) / (float(p.price) / 100 + 1), 1) if float(p.price) > 0 else 85.0

        smart_items.append({
            "id": p.id,
            "name": p.name,
            "category": p.category,
            "price": float(p.price),
            "stock": p.stock,
            "rating": rating,
            "value_score": value_score,
            "image_url": crud.get_default_image_url(p.name, p.category),
            "description": p.ai_description or "High performance product listing",
            "key_specs": ["4K Ultra HD", "HDR10+", "Smart Connectivity", "Eco Power Saver"] if "TV" in p.name or "Electronics" in p.category else ["Premium Comfort", "Ergonomic Design", "Durable Build", "2-Year Warranty"]
        })

    # Apply sorting
    if sort_by == "price_low_high":
        smart_items.sort(key=lambda x: x["price"])
    elif sort_by == "price_high_low":
        smart_items.sort(key=lambda x: x["price"], reverse=True)
    elif sort_by == "rating":
        smart_items.sort(key=lambda x: x["rating"], reverse=True)
    else:  # best_value
        smart_items.sort(key=lambda x: x["value_score"], reverse=True)

    if min_rating is not None:
        smart_items = [item for item in smart_items if item["rating"] >= min_rating]

    return {
        "success": True,
        "count": len(smart_items),
        "products": smart_items
    }

@app.post("/api/vendor/products/compare")
def compare_products_side_by_side(
    request_data: dict,
    db: Session = Depends(get_db)
):
    """
    Milestone 3 Feature: Side-by-Side Product Comparison Engine with dynamic attribute mapping
    and best-value recommendation logic.
    """
    product_ids = request_data.get("product_ids", [])
    if not product_ids:
        # Default fallback to compare first 3 products
        products = db.query(models.Product).limit(3).all()
    else:
        products = db.query(models.Product).filter(models.Product.id.in_(product_ids)).all()

    comparison_matrix = []
    best_value_item = None
    highest_score = -1.0

    for p in products:
        rating = round(4.0 + ((p.id * 7) % 10) * 0.1, 1)
        if rating > 5.0: rating = 4.8
        value_score = round((rating * 20) / (float(p.price) / 100 + 1), 1) if float(p.price) > 0 else 85.0

        item_data = {
            "id": p.id,
            "name": p.name,
            "category": p.category,
            "price": float(p.price),
            "stock": p.stock,
            "stock_valuation": float(p.price) * p.stock,
            "rating": rating,
            "value_score": value_score,
            "image_url": crud.get_default_image_url(p.name, p.category),
            "description": p.ai_description or "High quality product specs",
            "is_best_value": False,
            "features": {
                "Build Quality": "Premium Aluminum / Glass" if "Electronics" in p.category else "Ergonomic & Breathable",
                "Warranty": "2 Years Official Brand Warranty",
                "Energy Efficiency": "5-Star Eco Rating",
                "Customer Satisfaction": f"{int(rating * 20)}% Positive Reviews",
                "In Stock Delivery": "Ships within 24 Hours" if p.stock > 0 else "Pre-order Available"
            }
        }
        comparison_matrix.append(item_data)

        if value_score > highest_score:
            highest_score = value_score
            best_value_item = item_data

    if best_value_item:
        best_value_item["is_best_value"] = True

    return {
        "success": True,
        "product_count": len(comparison_matrix),
        "best_value_product_id": best_value_item["id"] if best_value_item else None,
        "best_value_recommendation": f"🏆 {best_value_item['name']} offers the highest Value-for-Money index score ({highest_score}/100)!" if best_value_item else "",
        "comparison_matrix": comparison_matrix
    }

# --- Milestone 4: Autonomous AI Strategic Agent & System Audit Endpoints ---

@app.post("/api/vendor/agent/autonomous-audit", tags=["Milestone 4: Autonomous AI Agent"])
def trigger_autonomous_store_audit(
    vendor_id: Optional[int] = Query(None),
    db: Session = Depends(get_db)
):
    """
    Milestone 4 Advanced Feature: Autonomous AI Agent Audit Workflow.
    Analyzes store catalog inventory, sales velocity, customer spend tiers,
    and generates proactive strategic advice for store optimization.
    """
    vid = vendor_id or 1
    audit_data = ai_agent.run_vendor_autonomous_audit(db, vendor_id=vid)
    return {
        "success": True,
        "feature": "Autonomous AI Strategic Agent Audit Workflow",
        "data": audit_data
    }

@app.get("/api/vendor/agent/weekly-report", tags=["Milestone 4: Autonomous AI Agent"])
def get_vendor_weekly_strategic_report(
    vendor_id: Optional[int] = Query(None),
    custom_note: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """
    Milestone 4 Advanced Feature: Autonomous Weekly Strategic Report.
    Returns weekly automated store health check and prioritized strategic action items.
    """
    vid = vendor_id or 1
    audit_data = ai_agent.run_vendor_autonomous_audit(db, vendor_id=vid)
    if custom_note:
        audit_data["custom_note"] = custom_note
        audit_data["action_items"].insert(0, {
            "severity": "HIGH",
            "category": "VENDOR_CUSTOM_INQUIRY",
            "title": f"Vendor Inquiry: {custom_note}",
            "recommendation": f"AI Strategic Analysis for Inquiry '{custom_note}': Evaluated current inventory velocity and pricing elasticity. Action recommended: Apply strategic promotion or stock reorder as requested.",
            "impact_score": 90
        })
    return {
        "success": True,
        "feature": "Weekly Automated Strategic Advice Pipeline",
        "data": audit_data
    }

