import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime, timedelta
import random

# Configuração da Página
st.set_page_config(page_title="Cantina Digital Pro", layout="wide")

# Conexão com Google Sheets
conn = st.connection("gsheets", type=GSheetsConnection)

# --- FUNÇÕES DE DADOS ---
def carregar_dados(aba):
    return conn.read(worksheet=aba)

def salvar_dados(df, aba):
    conn.update(worksheet=aba, data=df)
    st.cache_data.clear()

# --- LÓGICA DE LIMPEZA (6 MESES) ---
def limpar_historico():
    df_h = carregar_dados("historico")
    if not df_h.empty:
        df_h['data'] = pd.to_datetime(df_h['data'])
        limite = datetime.now() - timedelta(days=180)
        df_novo = df_h[df_h['data'] > limite]
        if len(df_novo) != len(df_h):
            salvar_dados(df_novo, "historico")

# --- INTERFACE ---
st.title("🏪 Cantina Digital - Gestão Total")
aba_nav = st.sidebar.radio("Navegação", ["Área dos Pais", "Lançar Fiado", "Almoxarifado", "Admin"])

# --- 1. ÁREA DOS PAIS ---
if aba_nav == "Área dos Pais":
    st.header("👨‍👩‍👧 Espaço do Responsável")
    cod = st.text_input("Código de 8 dígitos do Aluno")
    if cod:
        df_a = carregar_dados("alunos")
        aluno = df_a[df_a['codigo'].astype(str) == cod]
        if not aluno.empty:
            st.success(f"Bem-vindo, responsável por {aluno.iloc[0]['nome']}")
            st.metric("Saldo Devedor", f"R$ {aluno.iloc[0]['divida']:.2f}")
            
            st.subheader("Histórico de Consumo")
            df_h = carregar_dados("historico")
            vendas = df_h[df_h['codigo_aluno'].astype(str) == cod]
            st.table(vendas[['data', 'item', 'valor']])
        else:
            st.error("Código não encontrado.")

# --- 2. LANÇAR FIADO ---
elif aba_nav == "Lançar Fiado":
    st.header("📝 Novo Gasto na Conta")
    df_a = carregar_dados("alunos")
    if df_a.empty:
        st.warning("Nenhum aluno cadastrado.")
    else:
        aluno_nome = st.selectbox("Selecione o Aluno", df_a['nome'])
        item = st.text_input("Produto")
        valor = st.number_input("Preço (R$)", min_value=0.0)
        
        if st.button("Confirmar Venda"):
            # Atualiza Dívida
            idx = df_a.index[df_a['nome'] == aluno_nome][0]
            df_a.at[idx, 'divida'] += valor
            salvar_dados(df_a, "alunos")
            
            # Registra Histórico
            df_h = carregar_dados("historico")
            novo_h = pd.DataFrame([{
                "codigo_aluno": df_a.at[idx, 'codigo'],
                "item": item,
                "valor": valor,
                "data": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }])
            df_h = pd.concat([df_h, novo_h], ignore_index=True)
            salvar_dados(df_h, "historico")
            st.success("Lançado com sucesso!")

# --- 3. ALMOXARIFADO ---
elif aba_nav == "Almoxarifado":
    st.header("📦 Estoque e Lucro Independente")
    df_e = carregar_dados("almoxarifado")
    
    with st.expander("Cadastrar Compra/Insumo"):
        nome_i = st.text_input("Nome do Item")
        custo = st.number_input("Preço de Custo", min_value=0.0)
        venda = st.number_input("Preço de Venda Sugerido", min_value=0.0)
        qtd = st.number_input("Quantidade", min_value=0)
        if st.button("Salvar no Estoque"):
            novo_i = pd.DataFrame([{"item": nome_i, "custo": custo, "venda": venda, "qtd": qtd}])
            df_e = pd.concat([df_e, novo_i], ignore_index=True)
            salvar_dados(df_e, "almoxarifado")
    
    st.dataframe(df_e)
    lucro_un = (df_e['venda'] - df_e['custo']) * df_e['qtd']
    st.metric("Projeção de Lucro Total em Estoque", f"R$ {lucro_un.sum():.2f}")

# --- 4. ADMIN (CADASTRAR ALUNOS) ---
elif aba_nav == "Admin":
    st.header("⚙️ Painel de Controle")
    nome_aluno = st.text_input("Nome do Novo Aluno")
    if st.button("Cadastrar e Gerar Código"):
        cod_novo = str(random.randint(10000000, 99999999))
        df_a = carregar_dados("alunos")
        novo_a = pd.DataFrame([{"nome": nome_aluno, "codigo": cod_novo, "divida": 0.0}])
        df_a = pd.concat([df_a, novo_a], ignore_index=True)
        salvar_dados(df_a, "alunos")
        st.success(f"Cadastrado! Código para os pais: {cod_novo}")
