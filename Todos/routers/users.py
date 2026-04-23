from typing import Annotated
from sqlalchemy.orm import Session
from fastapi import Depends,Path,HTTPException,APIRouter
from Todos.models import Users
from Todos.database import engine,SessionLocal
from starlette import status
from pydantic import BaseModel,Field
from Todos.routers.auth import get_current_user
from passlib.context import CryptContext

router = APIRouter(prefix='/user',tags=['user'])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

class TodoRequest(BaseModel):
    title: str = Field(min_length=3)
    description: str = Field(min_length=3)
    priority: int = Field(gt=0,lt=6)
    complete: bool

class UserVerification(BaseModel):
    password: str
    new_password: str = Field(min_length=6)

db_dependency = Annotated[Session,Depends(get_db)]
user_dependency = Annotated[dict,Depends(get_current_user)]
bcrypt_context = CryptContext(schemes=['bcrypt'],deprecated='auto')

@router.get('/users',status_code=status.HTTP_200_OK)
async def get_user(user: user_dependency,db: db_dependency):
    if user is None:
        raise HTTPException(status_code=401,detail="Authentication Failed")
    return db.query(Users).filter(Users.id == user.get('id')).first()

@router.put("/password")
async def change_password(user: user_dependency,db: db_dependency,user_verification: UserVerification):
    if user is None:
        raise HTTPException(status_code=401,detail="Authentication Failed")
    user_model = db.query(Users).filter(Users.id == user.get('id')).first()
    if not bcrypt_context.verify(user_verification.password,user_model.hashed_password):
        raise HTTPException(status_code=401,detail="Error on Password Change")
    user_model.hashed_password = bcrypt_context.hash(user_verification.new_password)
    db.add(user_model)
    db.commit()

@router.put("/phone_number/{phone_number}")
async def change_phone_number(user: user_dependency,db: db_dependency,phone_number: str):
    if user is None:
        raise HTTPException(status_code=401,detail="Authentication Failed")
    user_model = db.query(Users).filter(Users.id == user.get('id')).first()
    user_model.phone_number = phone_number
    db.add(user_model)
    db.commit()