from pydantic import BaseModel, ConfigDict
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
    cost_price: Decimal
    selling_price: Decimal
    stock: int = 0
    category_id: Optional[int] = None


class ProductCreate(ProductBase):
    pass


class ProductUpdate(BaseModel):
    name: Optional[str] = None
    cost_price: Optional[Decimal] = None
    selling_price: Optional[Decimal] = None
    stock: Optional[int] = None
    category_id: Optional[int] = None
    is_active: Optional[bool] = None


class ProductResponse(ProductBase):
    id: int
    is_active: bool
    model_config = ConfigDict(from_attributes=True)