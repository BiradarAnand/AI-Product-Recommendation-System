from pydantic import BaseModel
from typing import List

class UserLogin(BaseModel):
    email: str
    password: str

class UserRegister(BaseModel):
    name: str
    email: str
    password: str

class Product(BaseModel):
    id: int
    title: str
    price: float
    category: str
    imageUrl: str

class Order(BaseModel):
    orderId: int
    userId: int
    productIds: List[int]
    totalAmount: float
    status: str
