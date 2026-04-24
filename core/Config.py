from sqlalchemy.orm import declarative_base, sessionmaker, Session
from sqlalchemy import create_engine
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Dependência para abrir e fechar a conexão com o BD a cada requisição
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()