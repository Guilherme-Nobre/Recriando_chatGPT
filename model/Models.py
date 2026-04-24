from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Text
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy.dialects.postgresql import UUID
from pgvector.sqlalchemy import Vector
import datetime
import uuid
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL)
Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    tenant_id = Column(UUID(as_uuid=True), default=uuid.uuid4, nullable=False, unique=True)

class Chat(Base):
    __tablename__ = "chats"
    id = Column(String, primary_key=True, index=True) # UUID enviado pelo front-end
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("users.tenant_id"), nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class Message(Base):
    __tablename__ = "messages"
    id = Column(Integer, primary_key=True, autoincrement=True)
    chat_id = Column(String, ForeignKey("chats.id"), nullable=False)
    role = Column(String, nullable=False) # 'user' ou 'assistant'
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class Memory(Base):
    __tablename__ = "memories"
    id = Column(Integer, primary_key=True, autoincrement=True)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("users.tenant_id"), nullable=False) # Isolamento Multi-tenant
    content = Column(Text, nullable=False)
    # Usaremos um modelo leve de embeddings que gera vetores de tamanho 384 (ex: all-MiniLM-L6-v2)
    embedding = Column(Vector(384)) 
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

# IMPORTANTE: Antes de criar as tabelas, o PostgreSQL precisa da extensão do pgvector.
# Se ainda não tiver ativado no seu banco, rode "CREATE EXTENSION IF NOT EXISTS vector;" via psql ou pgAdmin.
Base.metadata.create_all(bind=engine)