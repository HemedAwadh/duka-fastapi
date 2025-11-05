from fastapi import FastAPI
from pydantic import BaseModel
from app.models import  Product, session,User,datetime,Sale,Payment
from jwt.exceptions import InvalidTokenError
from pwdlib import PasswordHash
from datetime import datetime
from app.jwt_service import create_access_token, get_current_active_user
from fastapi import Depends, FastAPI, HTTPException, status
from pwdlib import PasswordHash
from fastapi.middleware.cors import CORSMiddleware

from typing import Annotated
from fastapi import FastAPI, Depends, HTTPException

# Sentry / Slack / SQLAlchemy / Unit Test / Gitflow workflow / Jira / CICD /Docker

app = FastAPI()
db = session()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)



password_hash = PasswordHash.recommended()

class Token(BaseModel):
    access_token: str | None = None
    


class TokenData(BaseModel):
    username: str | None = None
   

class ProductData(BaseModel):
    name : str
    buying_price : float
    selling_price : float


class ProductDataResponse(ProductData):
    id : int


@app.get("/")
def home():
    return {"Duka FastAPI": "1.0"}


@app.get("/products", response_model=list[ProductDataResponse])
async def get_products(user: Annotated[str, Depends(get_current_active_user)]):
    print("User from main >>>>>>>>>>",user)    
    return db.query(Product).all()

@app.post("/products", response_model=ProductDataResponse)
def add_product(prod : ProductData, user: Annotated[str, Depends(get_current_active_user)]):
    db_prod = Product(**prod.dict())
    db.add(db_prod)
    db.commit()
    return db_prod

class UserReq(BaseModel):
    full_name : str
    email : str
    password : str
    

class UserResponse(UserReq):
    id: int    


@app.get("/users",response_model=list[UserResponse])
def get_users(user: Annotated[str, Depends(get_current_active_user)]):
    return db.query(User).all()

@app.post("/register/user", response_model=Token)
def add_user(user : UserReq):
   try:
        existing_user = db.query(User).filter(User.email == user.email).first()
        if existing_user:
            raise HTTPException(status_code=400, detail="Email already registered")    
        user.password = password_hash.hash(user.password)
        print("Hashed password ***********",user.password)    
        db_user=User(**user.model_dump())
        db.add(db_user)
        db.commit()    
        token= create_access_token(user.email)
        return {"access_token":token}
   except:
        raise HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail="Something went wrong"
    )

   
class UserLoginReq(BaseModel):
    email : str
    password : str

class UserLoginResponse(UserLoginReq):
    full_name : str

@app.post("/login", response_model=Token | dict[str,str])
def login_user(userLogin : UserLoginReq):
    try:
        db_user = db.query(User).filter(User.email == userLogin.email).first()
        response = password_hash.verify(userLogin.password, str(db_user.password))      # type: ignore
        if response == True:
            token= create_access_token(userLogin.email)            
            return {"access_token":token}
        else:
            pass
    except:
        raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid Email or Password"
    )     

class SalesReq(BaseModel):
    pid : int
    quantity : int
    created_at : datetime

class SalesResponse(SalesReq):
    id : int

@app.get("/sales",response_model=list[SalesResponse])
def get_sales(user: Annotated[str, Depends(get_current_active_user)]):
    return db.query(Sale).all()

@app.post("/sales",response_model=SalesResponse)
def add_sale(sale : SalesReq, user: Annotated[str, Depends(get_current_active_user)]) :
    db_sale = Sale(**sale.model_dump())
    db.add(db_sale)
    db.commit()
    return db_sale 

class PaymentReq(BaseModel):
    sale_id : int
    mrid : str
    crid : str
    amount : float  |None = None
    trans_code : str |None = None
    created_at : datetime

class PaymentResp(PaymentReq):
    id : int

@app.get("/payments",response_model=list[PaymentResp])
def get_payments(user: Annotated[str, Depends(get_current_active_user)]):
    return db.query(Payment).all()

@app.post("/payments",response_model=PaymentResp)
def add_payment(payment : PaymentReq):
    db_payment = Payment(**payment.model_dump())
    db.add(db_payment)
    db.commit()
    return db_payment







# Why use fastapi?
# 1. Type hints - We can validate the data type expected by a route.
# 2. Pydantic model - Classes/Objects which convert JSON to an object and Pydantic to validate.
# 3. Async/Await - Performs a heavy task like upload a file asynchronously.
# 4. Swagger library - To document and test your API routes.
