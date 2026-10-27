#to create a session and pass it as a dependency so route handlers can use 
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from config import DATABASE_URL

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

#usually used a fastapi dependency
def get_db():
    db = SessionLocal() #used to give a fresh database conn
    try:
        yield db
    finally:
        db.close()
