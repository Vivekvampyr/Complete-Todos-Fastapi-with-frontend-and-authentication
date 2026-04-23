from typing import Annotated
from sqlalchemy.orm import Session
from fastapi import Depends,Path,HTTPException,APIRouter,Request
from Todos.models import Todos
from Todos.database import engine,SessionLocal
from starlette import status
from pydantic import BaseModel,Field
from Todos.routers.auth import get_current_user
from fastapi.templating import Jinja2Templates
from starlette.responses import RedirectResponse

router = APIRouter(prefix="/todos",tags=['todos'])


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

db_dependency = Annotated[Session,Depends(get_db)]
user_dependency = Annotated[dict,Depends(get_current_user)]

templates = Jinja2Templates(directory="Todos/templates")

def redirect_to_login():
    redirect_response = RedirectResponse(url="/auth/login-page",status_code=302)
    redirect_response.delete_cookie(key="access_token")
    return redirect_response

### PAGES ###

@router.get("/todo-page")
async def render_todo_page(db: db_dependency,request: Request):
    try:
        user = await get_current_user(request.cookies.get('access_token'))
        if user is None:
            return redirect_to_login()
        todos = db.query(Todos).filter(Todos.owner_id == user.get('id')).all()
        return templates.TemplateResponse(request=request,name="todo.html",context={"todos":todos,"user":user})
    except:
        return redirect_to_login()
    
@router.get("/add-todo-page")
async def render_todo_page(request: Request):
    try:
        user = await get_current_user(request.cookies.get('access_token'))

        if user is None:
            return redirect_to_login()
        return templates.TemplateResponse(request=request,name="add-todo.html",context={"user":user})
    except:
        return redirect_to_login()
    
@router.get("/edit-todo-page/{todo_id}")
async def render_edit_todo_page(request: Request, todo_id: int, db: db_dependency):
    try:
        user = await get_current_user(request.cookies.get('access_token'))

        if user is None:
            return redirect_to_login()
        todo = db.query(Todos).filter(Todos.id == todo_id).first()

        return templates.TemplateResponse(request=request,name="edit-todo.html",context={"todo":todo,"user":user})
    except:
        return redirect_to_login()


### END-POINTS ###
@router.get("/todos/all")
def read_all(user: user_dependency, db: db_dependency):
    return db.query(Todos).filter(Todos.owner_id == user.get('id')).all()

@router.get("/todos/{todo_id}",status_code=status.HTTP_200_OK)
def get_by_id(user: user_dependency, db: db_dependency,todo_id: int = Path(gt=0)):
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,detail="Authentication Failed")
    todo_model = db.query(Todos).filter(Todos.id == todo_id).filter(Todos.owner_id == user.get('id')).first()
    if todo_model is not None:
        return todo_model
    raise HTTPException(status_code=404,detail="ID is Not Found")

@router.post("/todo",status_code=status.HTTP_201_CREATED)
def create_todo(user: user_dependency, db: db_dependency,todo_request: TodoRequest):
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,detail="Authentication Failed")
    todo_model = Todos(**todo_request.model_dump(), owner_id=user.get('id'))
    db.add(todo_model)
    db.commit()

@router.put("/todo/{todo_id}",status_code=status.HTTP_204_NO_CONTENT)
def update_todo(user: user_dependency, db: db_dependency,todo_request: TodoRequest,todo_id: int = Path(gt=0)):
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,detail="Authentication Failed")
    todo_model = db.query(Todos).filter(Todos.id == todo_id).filter(Todos.owner_id == user.get('id')).first()
    if todo_id is None:
        raise HTTPException(status_code=404,detail="File Not Found")
    todo_model.title = todo_request.title
    todo_model.description = todo_request.description
    todo_model.priority = todo_request.priority
    todo_model.complete = todo_request.complete
    db.add(todo_model)
    db.commit()

@router.delete("/todo/{todo_id}",status_code=status.HTTP_204_NO_CONTENT)
def delete_todo(user: user_dependency, db: db_dependency,todo_id: int = Path(gt=0)):
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,detail="Authentication Failed")
    todo_model = db.query(Todos).filter(Todos.id == todo_id).filter(Todos.owner_id == user.get('id')).first()
    if todo_model is None:
        raise HTTPException(status_code=404,detail="File Not Found")
    db.query(Todos).filter(Todos.id == todo_id).filter(Todos.owner_id == user.get('id')).delete()
    db.commit()