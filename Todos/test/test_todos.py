from sqlalchemy import create_engine,text
from sqlalchemy.pool import StaticPool
from database import Base
from sqlalchemy.orm import sessionmaker
from main import app
from routers.todos import get_db,get_current_user
from fastapi.testclient import TestClient
from fastapi import status
import pytest
from models import Todos

SQLALCHEMY_DATABASE = "sqlite:///./testdb.db"

engine = create_engine(SQLALCHEMY_DATABASE,connect_args={'check_same_thread': False},poolclass=StaticPool)

TestingSessionLocal = sessionmaker(autoflush=False,autocommit = False,bind=engine)

Base.metadata.create_all(bind=engine)

def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

def override_get_current_user():
    return {'username':'vampyr','id':1,'user_role':'admin'}

app.dependency_overrides[get_db] = override_get_db
app.dependency_overrides[get_current_user] = override_get_current_user

client = TestClient(app)

@pytest.fixture
def test_todo():
    todo = Todos(
        title='Learn to Code',
        description='Learn Everyday',
        priority=5,
        complete=False,
        owner_id=1
    )

    db = TestingSessionLocal()
    db.add(todo)
    db.commit()
    db.refresh(todo)
    yield todo
    # with engine.connect() as connection:
    #     connection.execute(text("DELETE FROM Todos;"))
    #     connection.commit()
    db.query(Todos).delete()
    db.commit()
    db.close()


def test_all_authentication(test_todo):
    response = client.get("/")
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == [{'id':1,'priority':5,'owner_id':1,'complete':False,'description':'Learn Everyday','title':'Learn to Code'}]
    
def test_one_authentication(test_todo):
    response = client.get("/todos/1")
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {'id':1,'priority':5,'owner_id':1,'complete':False,'description':'Learn Everyday','title':'Learn to Code'}
    
def test_authentication_but_not_found(test_todo):
    response = client.get("/todos/999")
    assert response.status_code == 404
    assert response.json() == {'detail':'ID is Not Found'}