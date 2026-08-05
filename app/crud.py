from sqlalchemy.orm import Session
from sqlalchemy import or_, func
from app.models import Vendor, Admin, Product, Order
from app.schemas import VendorCreate, ProductCreate, VendorProfileUpdate, VendorPasswordChange
from app.auth import hash_password, verify_password

def get_vendor_by_email(db: Session, email: str):
    """Retrieve vendor by email address."""
    return db.query(Vendor).filter(Vendor.email == email.strip().lower()).first()

def get_vendor_by_id(db: Session, vendor_id: int):
    """Retrieve vendor by ID."""
    return db.query(Vendor).filter(Vendor.id == vendor_id).first()

def get_admin_by_email(db: Session, email: str):
    """Retrieve admin by email address."""
    return db.query(Admin).filter(Admin.email == email.strip().lower()).first()

def create_vendor(db: Session, vendor_in: VendorCreate) -> Vendor:
    """Create a new vendor in the database with default 'Pending' status."""
    hashed_pwd = hash_password(vendor_in.password)
    db_vendor = Vendor(
        full_name=vendor_in.full_name.strip(),
        business_name=vendor_in.business_name.strip(),
        email=vendor_in.email.strip().lower(),
        hashed_password=hashed_pwd,
        phone_number=vendor_in.phone_number.strip() if vendor_in.phone_number else None,
        business_address=vendor_in.business_address.strip() if vendor_in.business_address else None,
        status="Pending"
    )
    db.add(db_vendor)
    db.commit()
    db.refresh(db_vendor)
    return db_vendor

def update_vendor_profile(db: Session, vendor_id: int, profile_in: VendorProfileUpdate):
    """Update vendor business profile details."""
    vendor = get_vendor_by_id(db, vendor_id)
    if not vendor:
        return None

    vendor.full_name = profile_in.full_name.strip()
    vendor.business_name = profile_in.business_name.strip()
    vendor.phone_number = profile_in.phone_number.strip() if profile_in.phone_number else None
    vendor.business_address = profile_in.business_address.strip() if profile_in.business_address else None

    db.commit()
    db.refresh(vendor)
    return vendor

def update_vendor_password(db: Session, vendor_id: int, pwd_in: VendorPasswordChange):
    """Update vendor account password after verifying current password."""
    vendor = get_vendor_by_id(db, vendor_id)
    if not vendor:
        return False, "Vendor account not found."

    if not verify_password(pwd_in.current_password, vendor.hashed_password):
        return False, "Current password is incorrect."

    vendor.hashed_password = hash_password(pwd_in.new_password)
    db.commit()
    return True, "Password updated successfully."

def authenticate_vendor(db: Session, email: str, password: str):
    """Authenticate vendor by email & password."""
    vendor = get_vendor_by_email(db, email)
    if not vendor:
        return None
    if not verify_password(password, vendor.hashed_password):
        return None
    return vendor

def authenticate_admin(db: Session, email: str, password: str):
    """Authenticate admin by email & password."""
    admin = get_admin_by_email(db, email)
    if not admin:
        return None
    if not verify_password(password, admin.hashed_password):
        return None
    return admin

def get_admin_metrics(db: Session):
    """Get count metrics for Admin Dashboard summary cards."""
    total = db.query(Vendor).count()
    pending = db.query(Vendor).filter(Vendor.status == "Pending").count()
    approved = db.query(Vendor).filter(Vendor.status == "Approved").count()
    suspended = db.query(Vendor).filter(Vendor.status == "Suspended").count()

    return {
        "total": total,
        "pending": pending,
        "approved": approved,
        "suspended": suspended
    }

def get_filtered_vendors(db: Session, search: str = None, status_filter: str = None, limit: int = 100):
    """Retrieve vendors filtered by search term and status filter."""
    query = db.query(Vendor)

    if status_filter and status_filter.strip() and status_filter.strip().lower() != "all":
        st = status_filter.strip().capitalize()
        query = query.filter(Vendor.status == st)

    if search and search.strip():
        term = f"%{search.strip().lower()}%"
        query = query.filter(
            or_(
                Vendor.full_name.ilike(term),
                Vendor.business_name.ilike(term),
                Vendor.email.ilike(term)
            )
        )

    return query.order_by(Vendor.created_at.desc()).limit(limit).all()

def update_vendor_status(db: Session, vendor_id: int, new_status: str):
    """Update vendor status to 'Approved' or 'Suspended'."""
    vendor = db.query(Vendor).filter(Vendor.id == vendor_id).first()
    if not vendor:
        return None

    vendor.status = new_status.strip().capitalize()
    db.commit()
    db.refresh(vendor)
    return vendor

def get_vendor_dashboard_data(db: Session, vendor_id: int):
    """Get Vendor profile, real sales metrics from Order table, and recent products list."""
    vendor = get_vendor_by_id(db, vendor_id)
    if not vendor:
        vendor = db.query(Vendor).order_by(Vendor.id.asc()).first()
        if not vendor:
            return None

    recent_products = db.query(Product).filter(Product.vendor_id == vendor.id).order_by(Product.created_at.desc()).limit(10).all()
    products_count = db.query(Product).filter(Product.vendor_id == vendor.id).count()

    # Calculate real order metrics from Order table
    total_sales_units = db.query(func.coalesce(func.sum(Order.units), 0)).filter(Order.vendor_id == vendor.id, Order.status == "Completed").scalar()
    total_revenue_sum = db.query(func.coalesce(func.sum(Order.total_price), 0.0)).filter(Order.vendor_id == vendor.id, Order.status == "Completed").scalar()
    total_transactions_cnt = db.query(Order).filter(Order.vendor_id == vendor.id).count()

    return {
        "vendor_id": vendor.id,
        "vendor_name": vendor.full_name,
        "business_name": vendor.business_name,
        "total_sales": int(total_sales_units or 0),
        "total_revenue": float(total_revenue_sum or 0.0),
        "total_transactions": int(total_transactions_cnt or 0),
        "products_listed": products_count,
        "recent_products": recent_products
    }

def simulate_order(db: Session, vendor_id: int, product_id: int, units: int = 1):
    """Simulate a customer purchase for a product, recording real sales and updating stock."""
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        return False, "Product not found in store catalog."

    vid = product.vendor_id
    total_price = float(product.price) * units

    # Create new completed order
    order = Order(
        vendor_id=vid,
        product_id=product.id,
        units=units,
        total_price=total_price,
        status="Completed"
    )
    db.add(order)

    # Deduct stock if available
    if product.stock >= units:
        product.stock -= units

    db.commit()
    db.refresh(order)
    return True, f"Simulated sale of {units} unit(s) for '{product.name}' recorded successfully! Revenue: +${total_price:.2f}"

def get_vendor_insights_data(db: Session, vendor_id: int):
    """Retrieve dynamic vendor order stats, sales trends, and best selling products from database."""
    vendor = get_vendor_by_id(db, vendor_id)
    if not vendor:
        vendor = db.query(Vendor).order_by(Vendor.id.asc()).first()

    vid = vendor.id if vendor else vendor_id

    total_orders = db.query(Order).filter(Order.vendor_id == vid).count()
    completed_orders = db.query(Order).filter(Order.vendor_id == vid, Order.status == "Completed").count()
    pending_orders = db.query(Order).filter(Order.vendor_id == vid, Order.status == "Pending").count()
    cancelled_orders = db.query(Order).filter(Order.vendor_id == vid, Order.status == "Cancelled").count()

    # Query best selling products grouped by product
    best_sellers_query = db.query(
        Product.id,
        Product.name,
        Product.category,
        Product.price,
        Product.image_url,
        Product.ai_description,
        func.sum(Order.units).label("units_sold"),
        func.sum(Order.total_price).label("total_revenue")
    ).join(Order, Product.id == Order.product_id)\
     .filter(Order.vendor_id == vid, Order.status == "Completed")\
     .group_by(Product.id)\
     .order_by(func.sum(Order.units).desc())\
     .limit(5).all()

    best_selling_products = [
        {
            "id": r.id,
            "name": r.name,
            "category": r.category,
            "price": float(r.price),
            "image_url": r.image_url,
            "ai_description": r.ai_description,
            "units_sold": int(r.units_sold or 0),
            "total_revenue": float(r.total_revenue or 0.0)
        } for r in best_sellers_query
    ]

    return {
        "order_stats": {
            "total_orders": total_orders,
            "completed_orders": completed_orders,
            "pending_orders": pending_orders,
            "cancelled_orders": cancelled_orders
        },
        "sales_trends": [],
        "best_selling_products": best_selling_products
    }

def get_vendor_products(db: Session, vendor_id: int, search: str = None):
    """Get all products for a vendor filtered by search (name or category)."""
    query = db.query(Product).filter(Product.vendor_id == vendor_id)

    if search and search.strip():
        term = f"%{search.strip().lower()}%"
        query = query.filter(
            or_(
                Product.name.ilike(term),
                Product.category.ilike(term)
            )
        )

    return query.order_by(Product.created_at.desc()).all()

def get_product_by_id(db: Session, product_id: int, vendor_id: int):
    """Retrieve single product by ID for vendor."""
    return db.query(Product).filter(Product.id == product_id, Product.vendor_id == vendor_id).first()

def get_default_image_url(name: str, category: str) -> str:
    """Smart image resolution based on product name keywords and category."""
    n = (name or "").lower()
    c = (category or "").lower()

    if any(k in n for k in ["volley", "ball", "football", "soccer", "basketball", "tennis"]):
        return "https://images.unsplash.com/photo-1612872087720-bb876e2e67d1?w=200&auto=format&fit=crop"
    if any(k in n for k in ["watch", "smartwatch", "clock"]):
        return "https://images.unsplash.com/photo-1523275335684-37898b6baf30?w=200&auto=format&fit=crop"
    if any(k in n for k in ["shoe", "sneaker", "boot", "footwear", "slipper"]):
        return "https://images.unsplash.com/photo-1542291026-7eec264c27ff?w=200&auto=format&fit=crop"
    if any(k in n for k in ["phone", "mobile", "iphone", "android", "smartphone"]):
        return "https://images.unsplash.com/photo-1511707171634-5f897ff02aa9?w=200&auto=format&fit=crop"
    if any(k in n for k in ["laptop", "computer", "macbook", "pc", "notebook"]):
        return "https://images.unsplash.com/photo-1496181133206-80ce9b88a853?w=200&auto=format&fit=crop"
    if any(k in n for k in ["headphone", "earbud", "audio", "speaker", "headset"]):
        return "https://images.unsplash.com/photo-1505740420928-5e560c06d30e?w=200&auto=format&fit=crop"
    if any(k in n for k in ["shirt", "cloth", "jacket", "dress", "pant", "jean", "t-shirt", "apparel"]):
        return "https://images.unsplash.com/photo-1521572267360-ee0c2909d518?w=200&auto=format&fit=crop"
    if any(k in n for k in ["bag", "backpack", "wallet", "purse"]):
        return "https://images.unsplash.com/photo-1553062407-98eeb64c6a62?w=200&auto=format&fit=crop"
    if any(k in n for k in ["perfume", "cream", "lotion", "makeup", "beauty", "lipstick"]):
        return "https://images.unsplash.com/photo-1522337360788-8b13dee7a37e?w=200&auto=format&fit=crop"
    if any(k in n for k in ["coffee", "cup", "mug", "blender", "kitchen", "food"]):
        return "https://images.unsplash.com/photo-1556911220-e15b29be8c8f?w=200&auto=format&fit=crop"
    if any(k in n for k in ["book", "novel", "read"]):
        return "https://images.unsplash.com/photo-1544716278-ca5e3f4abd8c?w=200&auto=format&fit=crop"
    if any(k in n for k in ["toy", "game", "lego", "puzzle"]):
        return "https://images.unsplash.com/photo-1566576912321-d58ddd7a6088?w=200&auto=format&fit=crop"

    if "sports" in c or "outdoors" in c:
        return "https://images.unsplash.com/photo-1517649763962-0c623266010b?w=200&auto=format&fit=crop"
    if "clothing" in c or "apparel" in c:
        return "https://images.unsplash.com/photo-1521572267360-ee0c2909d518?w=200&auto=format&fit=crop"
    if "home" in c or "kitchen" in c:
        return "https://images.unsplash.com/photo-1556911220-e15b29be8c8f?w=200&auto=format&fit=crop"
    if "beauty" in c or "personal" in c:
        return "https://images.unsplash.com/photo-1522337360788-8b13dee7a37e?w=200&auto=format&fit=crop"
    if "food" in c or "beverage" in c:
        return "https://images.unsplash.com/photo-1504674900247-0877df9cc836?w=200&auto=format&fit=crop"
    if "book" in c or "media" in c:
        return "https://images.unsplash.com/photo-1544716278-ca5e3f4abd8c?w=200&auto=format&fit=crop"
    if "toy" in c or "game" in c:
        return "https://images.unsplash.com/photo-1566576912321-d58ddd7a6088?w=200&auto=format&fit=crop"
    if "electronics" in c:
        return "https://images.unsplash.com/photo-1498049794561-7780e7231661?w=200&auto=format&fit=crop"

    return "https://images.unsplash.com/photo-1505740420928-5e560c06d30e?w=200&auto=format&fit=crop"

def create_product(db: Session, vendor_id: int, product_in: ProductCreate) -> Product:
    """Create and save a new product into MySQL products table."""
    img_url = product_in.image_url.strip() if product_in.image_url and product_in.image_url.strip() else get_default_image_url(product_in.name, product_in.category)
    db_product = Product(
        vendor_id=vendor_id,
        name=product_in.name.strip(),
        category=product_in.category.strip(),
        price=product_in.price,
        stock=product_in.stock,
        image_url=img_url,
        ai_description=product_in.ai_description.strip() if product_in.ai_description else None
    )
    db.add(db_product)
    db.commit()
    db.refresh(db_product)
    return db_product

def update_product(db: Session, product_id: int, vendor_id: int, product_in: ProductCreate) -> Product:
    """Update existing product details in MySQL database."""
    product = get_product_by_id(db, product_id, vendor_id)
    if not product:
        return None

    img_url = product_in.image_url.strip() if product_in.image_url and product_in.image_url.strip() else get_default_image_url(product_in.name, product_in.category)

    product.name = product_in.name.strip()
    product.category = product_in.category.strip()
    product.price = product_in.price
    product.stock = product_in.stock
    product.image_url = img_url
    product.ai_description = product_in.ai_description.strip() if product_in.ai_description else None

    db.commit()
    db.refresh(product)
    return product

def delete_product(db: Session, product_id: int, vendor_id: int):
    """Delete a product belonging to a vendor."""
    product = get_product_by_id(db, product_id, vendor_id)
    if not product:
        return False

    db.delete(product)
    db.commit()
    return True
