# Arquivo: back.py
from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks
from transformers import AutoModelForCausalLM, AutoTokenizer
from sentence_transformers import SentenceTransformer
from sqlalchemy.orm import Session
from datetime import datetime
from model.ModelPromptRequest import PromptRequest
from model.ModelUserCreate import UserCreate, Token
from model.Models import User, Chat, Message, Memory
from core.Config import get_db
from core.Security import get_password_hash, verify_password, create_access_token, get_current_user
import uvicorn
import uuid

app = FastAPI(title="Qwen API", description="API para geração de texto com Qwen 2.5 1.5B")


# Carregamento global do modelo para evitar recarregamento a cada requisição
model_name = "Qwen/Qwen2.5-1.5B-Instruct"

print("Carregando o modelo e o tokenizador... Isso pode demorar um pouco.")
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForCausalLM.from_pretrained(
    model_name,
    torch_dtype="auto",
    device_map="auto"
)
print("Modelo carregado com sucesso!")

embedding_model = SentenceTransformer('all-MiniLM-L6-v2') 
print("Modelo de Embeddings carregado!")

def extract_and_save_memory(prompt: str, tenant_id: uuid.UUID, db: Session):
    """
    Roda em background para ver se o usuário falou algo importante sobre si mesmo 
    e salva no banco de dados isolado pelo tenant_id.
    """
    extraction_prompt = f"""Extraia apenas afirmações factuais sobre o usuário do texto abaixo. 
Se não houver informações pessoais (nome, gostos, rotina, profissão, etc), responda com a palavra "VAZIO".
Texto: "{prompt}"
Fatos:"""
    
    messages = [{"role": "user", "content": extraction_prompt}]
    text = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
    inputs = tokenizer([text], return_tensors="pt").to(model.device)
    
    generated_ids = model.generate(**inputs, max_new_tokens=50)
    output = tokenizer.batch_decode(generated_ids[:, inputs.input_ids.shape[1]:], skip_special_tokens=True)[0].strip()
    
    if output and "VAZIO" not in output.upper():
        # Gera o vetor e salva no banco pgvector
        vector = embedding_model.encode(output).tolist()
        nova_memoria = Memory(tenant_id=tenant_id, content=output, embedding=vector)
        db.add(nova_memoria)
        db.commit()

# ==========================================
# ROTA PRINCIPAL DE GERAÇÃO
# ==========================================
@app.post("/generate")
def generate_text(request: PromptRequest, background_tasks: BackgroundTasks, db: Session = Depends(get_db), current_user_email: str = Depends(get_current_user)):
    try:
        inicio = datetime.now()
        
        # 1. Obter o Usuário e seu Tenant ID
        db_user = db.query(User).filter(User.email == current_user_email).first()
        if not db_user:
             raise HTTPException(status_code=404, detail="Usuário não encontrado")
        
        # 2. Gerenciar Conversa (Garante que a conversa existe no histórico isolado pelo tenant)
        chat = db.query(Chat).filter(Chat.id == request.chat_id, Chat.tenant_id == db_user.tenant_id).first()
        if not chat:
            chat = Chat(id=request.chat_id, tenant_id=db_user.tenant_id)
            db.add(chat)
            db.commit()

        # 3. Salvar a Mensagem do Usuário no banco
        user_msg = Message(chat_id=chat.id, role="user", content=request.prompt)
        db.add(user_msg)
        db.commit()

        # 4. Recuperação de Memórias via Vetor (RAG Multi-tenant)
        # Transforma o prompt do usuário em um vetor para buscar coisas similares
        query_vector = embedding_model.encode(request.prompt).tolist()
        
        # Busca as 3 memórias mais relevantes DO TENANT DO USUÁRIO usando distância L2 (<->)
        memorias_relevantes = db.query(Memory)\
            .filter(Memory.tenant_id == db_user.tenant_id)\
            .order_by(Memory.embedding.l2_distance(query_vector))\
            .limit(3).all()
        
        contexto_memoria = ""
        if memorias_relevantes:
            contextos = "\n".join([m.content for m in memorias_relevantes])
            contexto_memoria = f"Informações que você lembra sobre este usuário:\n{contextos}\n\n"

        # 5. Montar Histórico da Conversa
        # Pega as últimas 10 mensagens para não estourar o limite de tokens da LLM
        historico_db = db.query(Message).filter(Message.chat_id == chat.id).order_by(Message.created_at.asc()).limit(10).all()
        
        messages = []
        # Adiciona o system prompt com as memórias recuperadas
        system_prompt = "Você é um assistente útil e amigável. " + contexto_memoria
        messages.append({"role": "system", "content": system_prompt})
        
        # Carrega o histórico para o array de mensagens
        for msg in historico_db:
            messages.append({"role": msg.role, "content": msg.content})

        # 6. Geração da Resposta com a LLM
        text = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
        model_inputs = tokenizer([text], return_tensors="pt").to(model.device)

        generated_ids = model.generate(**model_inputs, max_new_tokens=request.max_new_tokens)
        generated_ids = [output_ids[len(input_ids):] for input_ids, output_ids in zip(model_inputs.input_ids, generated_ids)]
        response_text = tokenizer.batch_decode(generated_ids, skip_special_tokens=True)[0]
        
        # 7. Salvar Resposta do Assistente
        assistant_msg = Message(chat_id=chat.id, role="assistant", content=response_text)
        db.add(assistant_msg)
        db.commit()
        
        # 8. Extrair e salvar novas memórias em SEGUNDO PLANO (Background Task)
        # Isso evita que o usuário tenha que esperar a extração para receber a resposta
        background_tasks.add_task(extract_and_save_memory, request.prompt, db_user.tenant_id, db)

        fim = datetime.now()
        tempo_execucao = (fim - inicio).total_seconds()

        return {
            "response": response_text,
            "tempo_segundos": tempo_execucao
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
# Adicione no seu back.py (antes do if __name__ == "__main__":)

@app.get("/chats")
def listar_chats(db: Session = Depends(get_db), current_user_email: str = Depends(get_current_user)):
    """Retorna a lista de conversas do tenant do usuário logado."""
    db_user = db.query(User).filter(User.email == current_user_email).first()
    
    # Consulta pelo tenant_id
    chats = db.query(Chat).filter(Chat.tenant_id == db_user.tenant_id).order_by(Chat.created_at.desc()).all()
    return [{"id": c.id, "created_at": c.created_at.isoformat()} for c in chats]

@app.get("/chat/{chat_id}/messages")
def listar_mensagens(chat_id: str, db: Session = Depends(get_db), current_user_email: str = Depends(get_current_user)):
    """Retorna todas as mensagens de um chat específico, garantindo o isolamento do tenant."""
    db_user = db.query(User).filter(User.email == current_user_email).first()
    
    # Verifica a propriedade pelo tenant_id
    chat = db.query(Chat).filter(Chat.id == chat_id, Chat.tenant_id == db_user.tenant_id).first()
    
    if not chat:
        raise HTTPException(status_code=404, detail="Chat não encontrado ou não pertence a este tenant.")
        
    mensagens = db.query(Message).filter(Message.chat_id == chat_id).order_by(Message.created_at.asc()).all()
    return [{"role": m.role, "content": m.content} for m in mensagens]
    
# ==========================================
# ROTAS DE AUTENTICAÇÃO
# ==========================================
@app.post("/cadastro", status_code=201)
def registrar_usuario(user: UserCreate, db: Session = Depends(get_db)):
    """
    Rota para cadastrar um novo usuário.
    Verifica se o e-mail já existe, faz o hash da senha e salva no BD.
    """
    # Verifica se o e-mail já está em uso
    user_exists = db.query(User).filter(User.email == user.email).first()
    if user_exists:
        raise HTTPException(status_code=400, detail="Este e-mail já está cadastrado.")
    
    novo_id = uuid.uuid4()
    
    # Criptografa a senha e salva no banco
    hashed_pwd = get_password_hash(user.password)
    novo_usuario = User(email=user.email, hashed_password=hashed_pwd, tenant_id=novo_id)
    
    db.add(novo_usuario)
    db.commit()
    db.refresh(novo_usuario)
    
    return {"mensagem": "Usuário criado com sucesso", "id": novo_usuario.id}


@app.post("/login", response_model=Token)
def login_usuario(user: UserCreate, db: Session = Depends(get_db)):
    """
    Rota de login.
    Valida credenciais e retorna um Token JWT em caso de sucesso.
    """
    # Busca o usuário pelo e-mail
    db_user = db.query(User).filter(User.email == user.email).first()
    
    # Valida usuário e senha
    if not db_user or not verify_password(user.password, db_user.hashed_password):
        raise HTTPException(status_code=401, detail="E-mail ou senha inválidos.")
    
    # Gera o Token
    token_jwt = create_access_token(data={"sub": db_user.email})
    
    return {"access_token": token_jwt, "token_type": "bearer"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=5000)
    print("🚀 API rodando na porta 5000!")
