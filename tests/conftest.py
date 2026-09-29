import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool
from sqlalchemy.orm import sessionmaker

from app.database import Base, get_db
from app import models
from app.main import app

# Use isolated in-memory SQLite database with StaticPool for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    """Create test database tables and seed initial data."""
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    
    admin = models.Admin(full_name="Reddy Admin", email="admin@gmail.com", hashed_password="admin")
    vendor = models.Vendor(id=1, full_name="Vamshi", business_name="Vamshi Store", email="vendor@gmail.com", hashed_password="vendor")
    db.add_all([admin, vendor])
    db.commit()

    prod1 = models.Product(id=1, vendor_id=1, name="Nike Air Max", category="Footwear", price=120.0, stock=2, ai_description="Running shoes")
    prod2 = models.Product(id=2, vendor_id=1, name="Adidas Ultraboost", category="Footwear", price=140.0, stock=15, ai_description="Comfort shoes")
    db.add_all([prod1, prod2])
    db.commit()

    order1 = models.Order(id=1, vendor_id=1, product_id=1, customer_name="Vamshi", customer_email="vamshi@gmail.com", units=1, total_price=120.0, status="Completed")
    order2 = models.Order(id=2, vendor_id=1, product_id=2, customer_name="Adi", customer_email="adi@gmail.com", units=2, total_price=280.0, status="Completed")
    db.add_all([order1, order2])
    db.commit()
    db.close()
    
    yield
    Base.metadata.drop_all(bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

@pytest.fixture(scope="module")
def client():
    """FastAPI TestClient fixture."""
    with TestClient(app) as c:
        yield c
