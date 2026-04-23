from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker,declarative_base
# from sqlalchemy.ext.declarative import declarative_base

# SQLALCHEMY_DATABASE = "postgresql://postgres:password@localhost/TodoApplicationDatabase"
# SQLALCHEMY_DATABASE = "mysql+pymysql://root:password@localhost:3306/TodoApplicationDatabase"
SQLALCHEMY_DATABASE = "sqlite:///./todoapp.db"

engine = create_engine(SQLALCHEMY_DATABASE)

SessionLocal = sessionmaker(autoflush=False,autocommit = False,bind=engine)

Base = declarative_base()

