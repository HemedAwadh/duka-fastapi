from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from pydantic import BaseModel

from .auth_service import authenticate_user, create_access_token, register_user
from app.models import session

router = APIRouter()

def get_db():
    db = session()
    try:
        yield db
    finally:
        db.close()

class UserRegisterRequest(BaseModel):
    full_name: str
    email: str
    password: str

@router.post("/register")
def register(
    user: UserRegisterRequest,
    db: Session = Depends(get_db)
):
    try:
        new_user = register_user(
            user.full_name,
            user.email,
            user.password,
            db
        )
        token = create_access_token(new_user.email)

        return {
            "user": {
                "id": new_user.id,
                "full_name": new_user.full_name,
                "email": new_user.email
            },
            "access_token": token,
            "token_type": "bearer"
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/token")
def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    user = authenticate_user(
        form_data.username,
        form_data.password,
        db
    )

    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    access_token = create_access_token(user.email)
    return {"access_token": access_token, "token_type": "bearer"}
