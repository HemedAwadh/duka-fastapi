from typing import List
from fastapi import FastAPI, Depends, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.orm import Session
from datetime import datetime
import json

from app.models import Product, Sale, User, Payment, session
from app.auth.auth_service import get_current_user
from app.auth.auth_routes import router as auth_router
from app.mpesa import send_stk_push

from pydantic import BaseModel

# -----------------------------
# FastAPI app
# -----------------------------
app = FastAPI(title="Duka FastAPI", version="1.0")

# -----------------------------
# CORS
# -----------------------------
origins = [
    "*"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -----------------------------
# DB dependency
# -----------------------------
def get_db():
    db = session()
    try:
        yield db
    finally:
        db.close()

# -----------------------------
# Include auth routes
# -----------------------------
app.include_router(auth_router, prefix="/auth", tags=["auth"])

# -----------------------------
# Pydantic Models
# -----------------------------
class ProductData(BaseModel):
    name: str
    buying_price: float
    selling_price: float

class ProductDataResponse(ProductData):
    id: int

class SaleData(BaseModel):
    pid: int
    quantity: int
    created_at: datetime = datetime.utcnow()

class SaleDataResponse(SaleData):
    id: int
    product_name: str
    product_sp: float
    amount: float

class UserDataResponse(BaseModel):
    id: int
    full_name: str
    email: str

class PaymentDataResponse(BaseModel):
    id: int
    sale_id: int
    mrid: str
    crid: str
    amount: float | None
    trans_code: str | None
    created_at: datetime

class STKPushRequest(BaseModel):
    amount: float
    phone_number: str
    sale_id: int

# -----------------------------
# Routes
# -----------------------------
@app.get("/")
def home():
    return {"Duka FastAPI": "1.0"}

# -------- Products ----------
@app.get("/products", response_model=List[ProductDataResponse])
def get_products(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return db.query(Product).all()

@app.post("/products", response_model=ProductDataResponse)
def add_product(
    prod: ProductData,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    db_prod = Product(**prod.dict())
    db.add(db_prod)
    db.commit()
    db.refresh(db_prod)
    return db_prod

@app.put("/products/{product_id}", response_model=ProductDataResponse)
def update_product(
    product_id: int,
    prod: ProductData,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    db_prod = db.query(Product).filter(Product.id == product_id).first()
    if not db_prod:
        raise HTTPException(status_code=404, detail="Product not found")

    db_prod.name = prod.name
    db_prod.buying_price = prod.buying_price
    db_prod.selling_price = prod.selling_price
    db.commit()
    db.refresh(db_prod)
    return db_prod

    # -------- Delete Product ----------
@app.delete("/products/{product_id}", status_code=204)
def delete_product(
    product_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    product = db.query(Product).filter(Product.id == product_id).first()

    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    db.delete(product)
    db.commit()

    return


# -------- Sales ----------
@app.get("/sales", response_model=List[SaleDataResponse])
def get_sales(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    sales = db.query(Sale).all()
    response = []

    for sale in sales:
        product = db.query(Product).filter(Product.id == sale.pid).first()
        if not product:
            continue

        response.append(SaleDataResponse(
            id=sale.id,
            pid=sale.pid,
            quantity=sale.quantity,
            created_at=sale.created_at,
            product_name=product.name,
            product_sp=product.selling_price,
            amount=sale.quantity * product.selling_price
        ))
    return response

@app.post("/sales", response_model=SaleDataResponse)
def add_sale(
    sale: SaleData,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    db_sale = Sale(
        pid=sale.pid,
        quantity=sale.quantity,
        created_at=sale.created_at
    )
    db.add(db_sale)
    db.commit()
    db.refresh(db_sale)

    product = db.query(Product).filter(Product.id == db_sale.pid).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    return SaleDataResponse(
        id=db_sale.id,
        pid=db_sale.pid,
        quantity=db_sale.quantity,
        created_at=db_sale.created_at,
        product_name=product.name,
        product_sp=product.selling_price,
        amount=db_sale.quantity * product.selling_price
    )

# -------- Dashboard ----------
@app.get("/dashboard")
def dashboard(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    profit_product = db.execute(text("""
        SELECT p.name,
               SUM((p.selling_price - p.buying_price) * s.quantity) AS profit
        FROM sales s
        JOIN products p ON s.pid = p.id
        GROUP BY p.id
    """)).fetchall()

    sales_day = db.execute(text("""
        SELECT DATE(s.created_at) AS date,
               SUM(p.selling_price * s.quantity) AS sales
        FROM sales s
        JOIN products p ON s.pid = p.id
        GROUP BY date
        ORDER BY date
    """)).fetchall()

    return {
        "profit_per_product": {
            "products_name": [row[0] for row in profit_product],
            "products_sales": [float(row[1]) for row in profit_product],
        },
        "sales_per_day": {
            "dates": [row[0].strftime("%Y-%m-%d") for row in sales_day],
            "sales": [float(row[1]) for row in sales_day],
        }
    }

# -------- Payments ----------
@app.get("/payments", response_model=List[PaymentDataResponse])
def get_payments(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return db.query(Payment).all()

# -------- MPesa ----------
@app.post("/mpesa/stkpush")
def mpesa_stk_push(
    data: STKPushRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    res = send_stk_push(data.amount, data.phone_number, data.sale_id)

    mrid = res.get("MerchantRequestID")
    crid = res.get("CheckoutRequestID")

    if not mrid or not crid:
        raise HTTPException(status_code=400, detail="Failed to initiate STK Push")

    payment = Payment(
        sale_id=data.sale_id,
        mrid=mrid,
        crid=crid,
        amount=0,
        trans_code="PENDING",
        created_at=datetime.utcnow()
    )

    db.add(payment)
    db.commit()
    db.refresh(payment)

    return {"mpesa_response": res, "payment_id": payment.id}

@app.post("/mpesa/callback")
def mpesa_callback(data: dict, db: Session = Depends(get_db)):
    stk = data.get("Body", {}).get("stkCallback")
    if not stk:
        return {"error": "Invalid callback"}

    payment = db.query(Payment).filter_by(
        mrid=stk.get("MerchantRequestID"),
        crid=stk.get("CheckoutRequestID")
    ).first()

    if not payment:
        return {"error": "Payment not found"}

    if stk.get("ResultCode") == 0:
        items = stk.get("CallbackMetadata", {}).get("Item", [])
        payment.amount = next((i["Value"] for i in items if i["Name"] == "Amount"), 0)
        payment.trans_code = next((i["Value"] for i in items if "Receipt" in i["Name"]), "N/A")
    else:
        payment.trans_code = "FAILED"
        payment.amount = 0

    db.commit()
    return {"success": True}

@app.get("/mpesa/checker/{sale_id}")
def mpesa_checker(sale_id: int, db: Session = Depends(get_db)):
    payment = db.query(Payment).filter_by(sale_id=sale_id).first()
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")

    return {
        "trans_code": payment.trans_code,
        "amount": payment.amount
    }
