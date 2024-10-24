import os
os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'

import streamlit as st
import hashlib
import time
import pandas as pd  # Importar pandas para manipular o CSV
import despesas_ug
import diarias
import contratos
import servidores  # Novo dashboard de Servidores
import adiantamentos  # Novo dashboard de Servidores
import combustivel  # Novo dashboard de Servidores
import orcamento  # Novo dashboard de Servidores
from sidebar import load_sidebar, navigate_pages
from data_loader import load_data, load_login_data # Importar o módulo de carregamento de dados

# Configuração da página
st.set_page_config(layout="wide")

# Criar um contêiner fixo no topo da página
header = st.container()

# Adicionar a imagem e o título dentro do contêiner
with header:
    col1, col2 = st.columns([5, 1])
    with col1:
        st.markdown('<style>h1 { margin-left: 0px; font-size: 30px; }</style>', unsafe_allow_html=True)
        st.title('Painel do Gestor')
    with col2:
        st.image('./src/assets/logo.png', width=150)
        st.text("")

# Função para gerar hash da senha
def make_hashes(password):
    return hashlib.sha256(str.encode(password)).hexdigest()

def check_hashes(password, hashed_text):
    return password == hashed_text  # Comparar diretamente se as senhas são em texto puro


def load_users():
    df = load_login_data()   
    return df

# Função de login
def login():
    st.markdown("<h1 style='text-align: center;'>Login</h1>", unsafe_allow_html=True)
    
    # Criar colunas para centralizar o formulário de login
    col1, col2, col3 = st.columns([2, 2, 2])
    
    with col2:
        # Inputs de login e senha
        username = st.text_input("Usuário")
        password = st.text_input("Senha", type='password')
    
        # Botão de login
        if st.button("Login", on_click=login_action, args=(username, password)):
            pass  # Ação de login é tratada pela função `login_action`

# Função de autenticação usando CSV
def login_action(username, password):
    users_df = load_users()

    # Converter o 'username' para string e garantir que não tenha espaços em branco
    users_df['username'] = users_df['username'].astype(str).str.strip()

    # Garantir que a entrada do usuário também seja tratada como string e sem espaços
    username = username.strip()

    try:
        # Converter a senha digitada pelo usuário para inteiro
        password = int(password)

        # Verificar se o usuário existe e se a senha está correta
        user_row = users_df[users_df['username'] == username]
        #st.write(user_row)  # Depuração: Verificar se o usuário foi encontrado

        # Comparar a senha digitada (int) com a senha armazenada no CSV
        if not user_row.empty and password == user_row.iloc[0]['password']:
            st.session_state['authenticated'] = True
            placeholder = st.empty()  # Placeholder para a mensagem de sucesso
            placeholder.success("Login bem-sucedido!")
            time.sleep(3)  # Espera por 3 segundos
            placeholder.empty()  # Limpa a mensagem de sucesso
        else:
            st.error("Usuário ou senha incorretos.")
    except ValueError:
        st.error("A senha deve ser um número inteiro.")

# Verifica se o usuário já está autenticado
if 'authenticated' not in st.session_state:
    st.session_state['authenticated'] = False

if not st.session_state['authenticated']:
    login()
else:
    st.button("Logout", on_click=lambda: st.session_state.update(authenticated=False, data=None))
    selected_page = navigate_pages()
    if selected_page == 'Despesas Detalhado':
        despesas_ug.run_dashboard()
    elif selected_page == 'Diárias':
        diarias.run_dashboard()
    elif selected_page == 'Contratos':
        contratos.run_dashboard()
    elif selected_page == 'Servidores': 
        servidores.run_dashboard()
    elif selected_page == 'Adiantamentos': 
        adiantamentos.run_dashboard()
    elif selected_page == 'Combustível': 
        combustivel.run_dashboard()
    elif selected_page == 'Orçamento': 
        orcamento.run_dashboard()
