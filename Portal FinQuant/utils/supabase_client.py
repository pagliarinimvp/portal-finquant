"""
Cliente Supabase
Cria e retorna a instância do cliente para comunicação com o banco de dados.
"""
import streamlit as st
from supabase import create_client, Client


def obter_cliente() -> Client:
    """
    Cria o cliente Supabase usando as credenciais definidas em .streamlit/secrets.toml.
    Lança um erro amigável caso as credenciais não estejam configuradas.
    """
    try:
        url = st.secrets["supabase"]["url"]
        chave = st.secrets["supabase"]["anon_key"]
        return create_client(url, chave)
    except Exception:
        st.error("❌ Credenciais do Supabase não encontradas.")
        st.info(
            "Configure o arquivo `.streamlit/secrets.toml` com a URL e a chave "
            "anônima do seu projeto Supabase. Consulte o README.md para instruções."
        )
        st.stop()
