# 🤖 Qwen 2.5 Chat com Memória (Recriando o GPT)

Este projeto é uma aplicação de chat completa (Full-Stack) alimentada pelo modelo de inteligência artificial **Qwen 2.5 (1.5B)**, mas você pode usar outro de sua escolha. Ele apresenta um sistema de **Memória de Longo Prazo (RAG)** em segundo plano, que aprende sobre o usuário durante a conversa e utiliza essas informações como contexto em interações futuras.

O sistema possui arquitetura **Multi-tenant**, garantindo total privacidade e isolamento de dados (conversas e memórias) entre diferentes usuários logados.

## 🚀 Funcionalidades

* **Chatbot com IA Local**: Respostas geradas usando o modelo `Qwen/Qwen2.5-1.5B-Instruct` executado localmente.
* **Memória Inteligente (RAG)**: Extração automática de fatos sobre o usuário em segundo plano (usando `Sentence-Transformers` e `pgvector`).
* **Isolamento de Dados (Multi-tenant)**: Cada usuário possui seu próprio `tenant_id`, isolando conversas e memórias vetoriais de forma segura.
* **Autenticação Segura**: Cadastro, Login e controle de sessão baseados em **JWT**.
* **Histórico de Conversas**: Múltiplas sessões de chat, salvas no banco de dados e facilmente recuperáveis pelo frontend.
* **Interface Amigável**: Frontend intuitivo, reativo e fluido construído com **Streamlit**.

## 🛠️ Tecnologias Utilizadas

### Backend
* **FastAPI**: Framework de alta performance para a construção da API.
* **SQLAlchemy**: ORM para comunicação com o banco de dados.
* **PostgreSQL + pgvector**: Banco de dados relacional com suporte avançado à busca vetorial (fundamental para a funcionalidade RAG).
* **PyJWT & Passlib (Bcrypt)**: Para autenticação e criptografia de senhas.

### IA & Machine Learning
* **Hugging Face Transformers**: Para carregamento e inferência do modelo CausalLM (Qwen 2.5).
* **Sentence Transformers**: Geração de embeddings textuais com o modelo leve `all-MiniLM-L6-v2`.
* **PyTorch**: Framework base para a execução dos modelos de deep learning.

### Frontend
* **Streamlit**: Interface web reativa para o sistema de chat.

## 📋 Pré-requisitos

Antes de começar, você precisará ter instalado em sua máquina:
* Python 3.10 ou superior
* PostgreSQL (com a extensão `pgvector` instalada e ativada)
* Git

## ⚙️ Instalação e Configuração

**1. Clone o repositório**
```bash
git clone https://github.com/Guilherme-Nobre/Recriando_chatGPT
cd Recriando_chatGPT
```

**2. Crie e ative um ambiente virtual (Recomendado)**
```bash
python -m venv venv
# Windows:
venv\\Scripts\\activate
# Linux/Mac:
source venv/bin/activate
```

**3. Instale as dependências**
```bash
pip install -r requirements.txt
```

**4. Configure o Banco de Dados e as Variáveis de Ambiente**
Crie um arquivo `.env` na raiz do projeto com as seguintes variáveis:
```env
DATABASE_URL="postgresql://usuario:senha@localhost:5432/gpt_local"
SECRET_KEY="sua_chave_secreta_super_segura_aqui"
ALGORITHM="HS256"
ACCESS_TOKEN_EXPIRE_MINUTES=60
```
*Atenção: A `SECRET_KEY` deve conter no mínimo 32 caracteres em um ambiente de produção.*

**5. Ative o `pgvector` no PostgreSQL**
Conecte-se ao seu banco de dados (ex: `gpt_local`) via `psql` ou pgAdmin e execute o seguinte comando:
```sql
CREATE EXTENSION IF NOT EXISTS vector;
```

## ▶️ Como Rodar a Aplicação

O projeto é dividido em duas partes que devem rodar simultaneamente: a API (Backend) e a Interface (Frontend).

**1. Iniciando o Backend (FastAPI)**
Abra um terminal na pasta do projeto e inicie a API. O primeiro carregamento demorará um pouco, pois o sistema fará o download dos modelos (`Qwen 2.5` e `MiniLM`) localmente.
```bash
python back.py
```
*A API estará disponível em `http://localhost:5000`.*

**2. Iniciando o Frontend (Streamlit)**
Abra um novo terminal (lembre-se de ativar o ambiente virtual) e execute:
```bash
streamlit run front.py
```
*O painel web será aberto automaticamente no seu navegador, geralmente em `http://localhost:8501`.*

## 📂 Estrutura do Projeto

```text
├── .env                     # Variáveis de ambiente (não versionado)
├── .gitignore               # Arquivos ignorados pelo Git
├── requirements.txt         # Dependências do projeto do Python
├── back.py                  # Ponto de entrada da API e rotas (FastAPI)
├── front.py                 # Interface do chat construída em Streamlit
├── core/                    # Configurações nucleares e Segurança
│   ├── Config.py            # Inicialização e conexão com banco via SQLAlchemy
│   └── Security.py          # Lógica de Autenticação JWT, Hash de senhas
└── model/                   # Modelos de Dados (ORM e Pydantic)
    ├── Models.py            # Tabelas SQLAlchemy (User, Chat, Message, Memory)
    ├── ModelPromptRequest.py# Schemas de Request da API
    └── ModelUserCreate.py   # Schemas de Criação e Login de Usuário
```

## 📝 Próximos Passos & Melhorias Futuras
* Implementar paginação no histórico de conversas longas.
* Adicionar suporte para streaming de respostas (StreamingResponse no FastAPI).
* Refinar as instruções do modelo para respostas ainda mais alinhadas ao contexto do usuário.

## 📄 Licença
Sinta-se à vontade para modificar, expandir e utilizar este projeto como base para seus próprios aplicativos de Inteligência Artificial local!
"""