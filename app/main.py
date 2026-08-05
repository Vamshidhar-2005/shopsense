import os
from typing import Optional
from fastapi import FastAPI, Request, Depends, HTTPException, Query, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.database import engine, Base, get_db
from app import models, schemas, crud

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

    # Clean up and assign exact images to existing products based on product name
    existing_products = db.query(models.Product).all()
    for p in existing_products:
        smart_url = crud.get_default_image_url(p.name, p.category)
        if not p.image_url or "photo-1505740420928-5e560c06d30e" in p.image_url or "photo-1523275335684-37898b6baf30" in p.image_url:
            p.image_url = smart_url
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
