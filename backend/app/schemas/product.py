from pydantic import BaseModel, ConfigDict, Field
from decimal import Decimal
from typing import Optional


class CategoryBase(BaseModel):
    name: str


class CategoryCreate(CategoryBase):
    pass


class CategoryResponse(CategoryBase):
    id: int
    model_config = ConfigDict(from_attributes=True)


class ProductBase(BaseModel):
    barcode: str
    name: str
    cost_price: Decimal = Field(..., alias="purchase_price")
    selling_price: Decimal = Field(..., alias="price")
    discount_percent: Decimal = Field(default=Decimal("0.0"))  # <-- DITAMBAHKAN
    stock: int = 0
    category_id: Optional[int] = None

    model_config = ConfigDict(populate_by_name=True)


class ProductCreate(ProductBase):
    pass


class ProductUpdate(BaseModel):
    barcode: Optional[str] = None
    name: Optional[str] = None
    cost_price: Optional[Decimal] = Field(None, alias="purchase_price")
    selling_price: Optional[Decimal] = Field(None, alias="price")
    discount_percent: Optional[Decimal] = None  # <-- DITAMBAHKAN
    stock: Optional[int] = None
    category_id: Optional[int] = None
    is_active: Optional[bool] = None

    model_config = ConfigDict(populate_by_name=True)


class ProductResponse(ProductBase):
    id: int
    is_active: bool
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)