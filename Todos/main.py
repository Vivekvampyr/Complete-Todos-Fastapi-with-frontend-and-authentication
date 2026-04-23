from fastapi import FastAPI, Request
from Todos import models
from Todos.database import engine
from Todos.routers import auth, todos,admin,users
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles

app = FastAPI()
templates = Jinja2Templates(directory="Todos/templates")
app.mount("/static",StaticFiles(directory="Todos/static"),name="static")

models.Base.metadata.create_all(engine)

@app.get("/")
def test(request: Request):
    return templates.TemplateResponse(request=request,name="home.html")

@app.get("/healthy")
def check_health():
    return {'status':'healthy'}

app.include_router(auth.router)
app.include_router(todos.router)
app.include_router(admin.router)
app.include_router(users.router)
