"""
Database Schemas for Interior Design Quotation System

Each Pydantic model corresponds to a MongoDB collection. The collection name is the lowercase of the class name.

Collections:
- User (admin/employee profiles)
- HouseCategory
- Subcategory
- Package
- Quotation
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Literal

class User(BaseModel):
    name: str = Field(..., description="Full name")
    email: str = Field(..., description="Email address")
    role: Literal["admin", "employee"] = Field(..., description="User role")
    phone: Optional[str] = Field(None, description="Phone number")
    avatar_url: Optional[str] = Field(None, description="Avatar image URL")
    is_active: bool = Field(True, description="Whether user is active")

class HouseCategory(BaseModel):
    name: str = Field(..., description="Category name (e.g., Apartment, Villa)")
    description: Optional[str] = Field(None, description="Description of the house category")
    is_active: bool = Field(True, description="Whether this category is active")

class Subcategory(BaseModel):
    name: str = Field(..., description="Sub-housing category name (e.g., 1BHK, 2BHK)")
    description: Optional[str] = Field(None, description="Description")
    category_id: str = Field(..., description="Reference to HouseCategory _id as string")
    is_active: bool = Field(True, description="Whether this subcategory is active")

class Package(BaseModel):
    name: str = Field(..., description="Package name")
    description: Optional[str] = Field(None, description="Package description")
    category_id: Optional[str] = Field(None, description="HouseCategory _id")
    subcategory_id: Optional[str] = Field(None, description="Subcategory _id")
    features: List[str] = Field(default_factory=list, description="List of features included")
    price: float = Field(..., ge=0, description="Base price of the package")
    is_active: bool = Field(True, description="Whether this package is active")

class QuotationItem(BaseModel):
    package_id: str = Field(..., description="Package _id")
    name: Optional[str] = Field(None, description="Resolved package name (optional)")
    quantity: int = Field(1, ge=1, description="Quantity")
    unit_price: float = Field(..., ge=0, description="Unit price at the time of quotation")
    total: float = Field(..., ge=0, description="Calculated total for the item")

class Quotation(BaseModel):
    employee_id: str = Field(..., description="User _id of the employee creating the quotation")
    client_name: str = Field(..., description="Client full name")
    client_contact: Optional[str] = Field(None, description="Phone or email")
    house_category_id: Optional[str] = Field(None, description="HouseCategory _id")
    subcategory_id: Optional[str] = Field(None, description="Subcategory _id")
    items: List[QuotationItem] = Field(default_factory=list, description="Items included in the quotation")
    subtotal: float = Field(..., ge=0, description="Subtotal before discounts and taxes")
    discount: float = Field(0, ge=0, description="Discount amount")
    tax: float = Field(0, ge=0, description="Tax amount")
    total: float = Field(..., ge=0, description="Grand total")
    status: Literal["draft", "sent", "approved", "rejected"] = Field("draft", description="Status of the quotation")
    notes: Optional[str] = Field(None, description="Additional notes")
