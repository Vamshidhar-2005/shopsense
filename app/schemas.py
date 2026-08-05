from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, EmailStr, Field, field_validator

class VendorCreate(BaseModel):
    full_name: str = Field(..., min_length=1, description="Full Name of Vendor owner")
    business_name: str = Field(..., min_length=1, description="Registered Business Name")
    email: EmailStr = Field(..., description="Valid Business Email Address")
    password: str = Field(..., min_length=6, description="Password (min 6 characters)")
    phone_number: Optional[str] = Field(None, description="Optional contact phone number")
    business_address: Optional[str] = Field(None, description="Optional physical or mailing address")

    @field_validator("full_name", "business_name")
    def not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Field cannot be empty or blank")
        return v.strip()

    @field_validator("password")
    def password_length(cls, v: str) -> str:
        if len(v) < 6:
            raise ValueError("Password must be at least 6 characters long")
        return v

class VendorResponse(BaseModel):
    id: int
    full_name: str
    business_name: str
    email: str
    phone_number: Optional[str] = None
    business_address: Optional[str] = None
    status: str
    is_active: bool
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class VendorProfileUpdate(BaseModel):
    full_name: str = Field(..., min_length=1)
    business_name: str = Field(..., min_length=1)
    phone_number: Optional[str] = None
    business_address: Optional[str] = None

class VendorPasswordChange(BaseModel):
    current_password: str = Field(..., min_length=6)
    new_password: str = Field(..., min_length=6)

class VendorStatusUpdate(BaseModel):
    status: str = Field(..., description="'Approved' or 'Suspended'")

class ProductCreate(BaseModel):
    name: str = Field(..., min_length=1, description="Product Name")
    category: str = Field(..., min_length=1, description="Product Category")
    price: float = Field(..., gt=0, description="Product Price")
    stock: int = Field(..., ge=0, description="Stock Quantity")
    image_url: Optional[str] = Field(None, description="Image URL")
    ai_description: Optional[str] = Field(None, description="Product Description")

class AIDescriptionRequest(BaseModel):
    name: str
    category: str
    raw_description: Optional[str] = None

class ProductResponse(BaseModel):
    id: int
    vendor_id: int
    name: str
    category: str
    price: float
    stock: int
    image_url: Optional[str] = None
    ai_description: Optional[str] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class VendorDashboardResponse(BaseModel):
    vendor_id: int
    vendor_name: str
    business_name: str
    total_sales: int
    total_revenue: float
    total_transactions: int
    products_listed: int
    recent_products: List[ProductResponse]

class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=6)
    role: str = Field(..., description="'vendor' or 'admin'")
