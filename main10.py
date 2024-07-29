from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy import create_engine, Column, Integer, String, ForeignKey, DateTime, Enum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from pydantic import BaseModel
from datetime import datetime
import enum

DATABASE_URL = "sqlite:///my_database.db"  # Используем SQLite для простоты

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Определяем модели SQLAlchemy
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    first_name = Column(String, index=True)
    last_name = Column(String, index=True)
    email = Column(String, unique=True, index=True)
    password = Column(String)

class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    description = Column(String)
    price = Column(Integer)

class OrderStatus(str, enum.Enum):
    pending = "pending"
    completed = "completed"
    canceled = "canceled"

class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    product_id = Column(Integer, ForeignKey("products.id"))
    order_date = Column(DateTime, default=datetime.utcnow)
    status = Column(Enum(OrderStatus), default=OrderStatus.pending)

    user = relationship("User", back_populates="orders")
    product = relationship("Product", back_populates="orders")

User.orders = relationship("Order", back_populates="user")
Product.orders = relationship("Order", back_populates="product")

# Создаем базу данных
Base.metadata.create_all(bind=engine)

# Определяем Pydantic модели
class UserCreate(BaseModel):
    first_name: str
    last_name: str
    email: str
    password: str

class UserResponse(BaseModel):
    id: int
    first_name: str
    last_name: str
    email: str

    class Config:
        orm_mode = True

class ProductCreate(BaseModel):
    name: str
    description: str
    price: int

class ProductResponse(BaseModel):
    id: int
    name: str
    description: str
    price: int

    class Config:
        orm_mode = True

class OrderCreate(BaseModel):
    user_id: int
    product_id: int

class OrderResponse(BaseModel):
    id: int
    user_id: int
    product_id: int
    order_date: datetime
    status: OrderStatus

    class Config:
        orm_mode = True

app = FastAPI()

# Зависимость для получения сессии базы данных
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# CRUD операции для пользователей
@app.post("/users/", response_model=UserResponse)
async def create_user(user: UserCreate, db: SessionLocal = Depends(get_db)):
    db_user = User(**user.dict())
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

@app.get("/users/{user_id}", response_model=UserResponse)
async def read_user(user_id: int, db: SessionLocal = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return user

# CRUD операции для товаров
@app.post("/products/", response_model=ProductResponse)
async def create_product(product: ProductCreate, db: SessionLocal = Depends(get_db)):
    db_product = Product(**product.dict())
    db.add(db_product)
    db.commit()
    db.refresh(db_product)
    return db_product

@app.get("/products/{product_id}", response_model=ProductResponse)
async def read_product(product_id: int, db: SessionLocal = Depends(get_db)):
    product = db.query(Product).filter(Product.id == product_id).first()
    if product is None:
        raise HTTPException(status_code=404, detail="Product not found")
    return product

# CRUD операции для заказов
@app.post("/orders/", response_model=OrderResponse)
async def create_order(order: OrderCreate, db: SessionLocal = Depends(get_db)):
    db_order = Order(**order.dict())
    db.add(db_order)
    db.commit()
    db.refresh(db_order)
    return db_order

@app.get("/orders/{order_id}", response_model=OrderResponse)
def read_order(order_id: int, db: SessionLocal = Depends(get_db)):
    order = db.query(Order).filter(Order.id == order_id).first()
    if order is None:
        raise HTTPException(status_code=404, detail="Order not found")
    return order
