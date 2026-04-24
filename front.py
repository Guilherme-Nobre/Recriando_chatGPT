import streamlit as st
import requests
import uuid

# ==========================================
# 1. Configurações Iniciais
# ==========================================
st.set_page_config(
    page_title="Qwen 2.5 Chat",
    page_icon="🤖",
    layout="centered"
)

st.markdown("""
<style>
    .stChatFloatingInputContainer {
        padding-bottom: 20px;
    }
</style>
""", unsafe_allow_html=True)

# Endpoints da API FastAPI
API_BASE_URL = "http://localhost:5000"
API_LOGIN_URL = f"{API_BASE_URL}/login"
API_CADASTRO_URL = f"{API_BASE_URL}/cadastro"
API_GENERATE_URL = f"{API_BASE_URL}/generate"
API_CHATS_URL = f"{API_BASE_URL}/chats"
API_MESSAGES_URL = f"{API_BASE_URL}/chat" # Sufixo /{chat_id}/messages será adicionado

# ==========================================
# 2. Gerenciamento de Estado (Sessão)
# ==========================================
if "chat_id" not in st.session_state:
    st.session_state.chat_id = str(uuid.uuid4())
if "logado" not in st.session_state:
    st.session_state.logado = False
if "token" not in st.session_state:
    st.session_state.token = None
if "pagina" not in st.session_state:
    st.session_state.pagina = "login"
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": "Olá! Sou o Qwen. Como posso ajudar você hoje?"}]

def mudar_pagina(nova_pagina):
    st.session_state.pagina = nova_pagina
    st.rerun()

def fazer_logout():
    st.session_state.logado = False
    st.session_state.token = None
    iniciar_nova_conversa()
    mudar_pagina("login")

def iniciar_nova_conversa():
    st.session_state.chat_id = str(uuid.uuid4())
    st.session_state.messages = [{"role": "assistant", "content": "Olá! Nova conversa iniciada. O que vamos criar hoje?"}]

def carregar_conversa_antiga(chat_id):
    st.session_state.chat_id = chat_id
    headers = {"Authorization": f"Bearer {st.session_state.token}"}
    try:
        resposta = requests.get(f"{API_MESSAGES_URL}/{chat_id}/messages", headers=headers)
        if resposta.status_code == 200:
            msgs = resposta.json()
            if msgs:
                st.session_state.messages = msgs
            else:
                st.session_state.messages = [{"role": "assistant", "content": "Conversa vazia recuperada."}]
        elif resposta.status_code == 401:
            fazer_logout()
    except requests.exceptions.ConnectionError:
        st.error("Erro ao conectar com a API.")

# ==========================================
# 3. Telas da Aplicação
# ==========================================

def tela_login():
    st.title("🔐 Login")
    st.caption("Acesse sua conta para utilizar o Qwen 2.5 com Memória")
    
    with st.form("form_login"):
        email = st.text_input("E-mail")
        senha = st.text_input("Senha", type="password")
        submit = st.form_submit_button("Entrar")
        
        if submit:
            if not email or not senha:
                st.warning("Preencha todos os campos.")
            else:
                with st.spinner("Autenticando..."):
                    try:
                        resposta = requests.post(API_LOGIN_URL, json={"email": email, "password": senha})
                        if resposta.status_code == 200:
                            dados = resposta.json()
                            st.session_state.token = dados.get("access_token")
                            st.session_state.logado = True
                            st.success("Login realizado com sucesso!")
                            mudar_pagina("chat")
                        else:
                            st.error("E-mail ou senha incorretos.")
                    except requests.exceptions.ConnectionError:
                        st.error("Erro de conexão. A API está rodando?")

    st.divider()
    st.write("Não tem uma conta?")
    if st.button("Criar nova conta"):
        mudar_pagina("cadastro")

def tela_cadastro():
    st.title("📝 Cadastro")
    
    with st.form("form_cadastro"):
        email = st.text_input("E-mail")
        senha = st.text_input("Senha", type="password")
        confirmar_senha = st.text_input("Confirmar Senha", type="password")
        submit = st.form_submit_button("Cadastrar")
        
        if submit:
            if not email or not senha:
                st.warning("Preencha todos os campos.")
            elif senha != confirmar_senha:
                st.error("As senhas não coincidem.")
            else:
                with st.spinner("Criando usuário..."):
                    try:
                        resposta = requests.post(API_CADASTRO_URL, json={"email": email, "password": senha})
                        if resposta.status_code == 201:
                            st.success("Conta criada com sucesso! Faça login para continuar.")
                            mudar_pagina("login")
                        else:
                            st.error(f"Erro ao cadastrar: {resposta.json().get('detail', 'Erro desconhecido')}")
                    except requests.exceptions.ConnectionError:
                        st.error("Erro de conexão com a API.")

    st.divider()
    if st.button("Voltar para o Login"):
        mudar_pagina("login")

def tela_chat():
    # Headers para chamadas autenticadas
    headers = {"Authorization": f"Bearer {st.session_state.token}"}

    # Menu lateral com Histórico
    with st.sidebar:
        st.write("### 🧠 Qwen 2.5")
        
        if st.button("➕ Nova Conversa", use_container_width=True, type="primary"):
            iniciar_nova_conversa()
            st.rerun()
            
        st.divider()
        st.write("📂 **Histórico de Conversas**")
        
        # Buscar histórico de chats da API
        try:
            resposta_chats = requests.get(API_CHATS_URL, headers=headers)
            if resposta_chats.status_code == 200:
                chats_db = resposta_chats.json()
                if not chats_db:
                    st.caption("Nenhuma conversa salva ainda.")
                else:
                    # Lista os chats salvos
                    for idx, c in enumerate(chats_db):
                        data_formatada = c['created_at'][:10] # Pega apenas a data YYYY-MM-DD
                        label_botao = f"💬 Chat {data_formatada} ({str(c['id'])[:4]}...)"
                        
                        # Destaca o chat atual
                        is_current = (c['id'] == st.session_state.chat_id)
                        
                        if st.button(label_botao, key=f"chat_{c['id']}", disabled=is_current, use_container_width=True):
                            carregar_conversa_antiga(c['id'])
                            st.rerun()
            elif resposta_chats.status_code == 401:
                fazer_logout()
        except requests.exceptions.ConnectionError:
            st.caption("Offline - Não foi possível carregar o histórico.")

        st.divider()
        if st.button("🚪 Sair (Logout)", use_container_width=True):
            fazer_logout()

    # Corpo principal do Chat
    st.title("🤖 Qwen 2.5 (Com Memória RAG)")
    st.caption(f"ID da Conversa Atual: `{st.session_state.chat_id}`")
    st.divider()

    # Renderiza mensagens
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Input do usuário
    if prompt := st.chat_input("Digite sua mensagem..."):
        
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            
            with st.spinner("Consultando memórias e pensando..."):
                try:
                    payload = {
                        "chat_id": st.session_state.chat_id,
                        "prompt": prompt,
                        "max_new_tokens": 512
                    }
                    
                    resposta_api = requests.post(API_GENERATE_URL, json=payload, headers=headers)
                    
                    if resposta_api.status_code == 200:
                        dados = resposta_api.json()
                        resposta_texto = dados.get("response", "")
                        tempo = dados.get("tempo_segundos", 0.0)
                        
                        message_placeholder.markdown(resposta_texto)
                        st.caption(f"⏱️ Gerado em {tempo:.2f}s")
                        
                        st.session_state.messages.append({"role": "assistant", "content": resposta_texto})
                        
                    elif resposta_api.status_code == 401:
                        message_placeholder.error("Sessão expirada ou não autorizada.")
                        fazer_logout()
                    else:
                        erro_msg = f"Erro na API: {resposta_api.text}"
                        message_placeholder.error(erro_msg)
                        
                except requests.exceptions.ConnectionError:
                    message_placeholder.error("Falha na conexão. A API está rodando?")

# ==========================================
# 4. Roteamento
# ==========================================
if not st.session_state.logado:
    if st.session_state.pagina == "login":
        tela_login()
    elif st.session_state.pagina == "cadastro":
        tela_cadastro()
else:
    tela_chat()