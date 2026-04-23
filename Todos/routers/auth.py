from fastapi import APIRouter,Depends,HTTPException,Request
from Todos.models import Users
from pydantic import BaseModel
from passlib.context import CryptContext 
from Todos.database import SessionLocal
from typing import Annotated
from sqlalchemy.orm import Session
from starlette import status
from fastapi.security import OAuth2PasswordRequestForm as OPRF,OAuth2PasswordBearer
from jose import jwt,JWSError
from datetime import timedelta,datetime,timezone
from fastapi.templating import Jinja2Templates

router = APIRouter(prefix='/auth',tags=['auth'])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

db_dependency = Annotated[Session,Depends(get_db)]

templates = Jinja2Templates(directory="Todos/templates")

SECRET_KEY = "45D4C7D049535F8B96C9298908B4327A"
ALGORITHM = "HS256"

bcrypt_context = CryptContext(schemes=['bcrypt'],deprecated='auto')
oauth2_bearer = OAuth2PasswordBearer(tokenUrl='auth/token')

class CreateUserRequest(BaseModel):
    email: str
    username: str
    first_name: str
    last_name: str
    password: str
    role: str
    phone_number: str

class Token(BaseModel):
    access_token: str
    token_type: str

def authenticate_user(username: str, password: str, db):
    user = db.query(Users).filter(Users.username == username).first()
    if not user:
        return False
    if not bcrypt_context.verify(password,user.hashed_password):
        return False
    return user

def create_access_token(username: str,user_id: int,role: str,expires_delta: timedelta):
    encode = {'sub':username,'id':user_id,'role': role}
    expires = datetime.now(timezone.utc) + expires_delta
    encode.update({'exp':expires})
    return jwt.encode(encode,SECRET_KEY,algorithm=ALGORITHM)

async def get_current_user(token: Annotated[str, Depends(oauth2_bearer)]):
    try:
        payload = jwt.decode(token,SECRET_KEY,algorithms=[ALGORITHM])
        username: str = payload.get('sub')
        user_id: int = payload.get('id')
        user_role: str = payload.get('role')
        if username is None or user_id is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,detail="User is Not Authroized")
        return {'username':username,'id':user_id,'user_role':user_role}
    except JWSError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,detail="User is Not Authroized")
    
@router.get("/login-page")
def login_page_renderer(request: Request):
    return templates.TemplateResponse(request=request,name="login.html")

@router.get("/register-page")
def register_page_renderer(request: Request):
    return templates.TemplateResponse(request=request,name="register.html")

@router.get("/all")
def get_all_users(db: db_dependency):
    return db.query(Users).all()

@router.post("",status_code=status.HTTP_201_CREATED)
def create_user(db: db_dependency, create_user_request: CreateUserRequest):
    create_user_model = Users(
        email = create_user_request.email,
        username = create_user_request.username,
        first_name = create_user_request.first_name,
        last_name = create_user_request.last_name,
        hashed_password = bcrypt_context.hash(create_user_request.password),
        role = create_user_request.role,
        is_active = True,
        phone_number = create_user_request.phone_number
        )
    db.add(create_user_model)
    db.commit()

@router.post("/token",response_model=Token)
def login_for_token_access(form_data: Annotated[OPRF,Depends()],db: db_dependency):
    user = authenticate_user(form_data.username,form_data.password,db)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,detail="User is Not Authroized")
    token = create_access_token(user.username,user.id,user.role,timedelta(minutes=20))
    return {'access_token':token,'token_type':'bearer'}