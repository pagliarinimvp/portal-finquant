"""
Funções de Autenticação
Gerencia o cadastro, login, logout e persistência de dados do usuário via Supabase.
"""
import streamlit as st
from utils.supabase_client import obter_cliente


def cadastrar_usuario(email: str, senha: str, nome: str) -> dict:
    """Cadastra um novo usuário no Supabase Auth."""
    cliente = obter_cliente()
    try:
        resposta = cliente.auth.sign_up({
            "email": email,
            "password": senha,
            "options": {"data": {"nome": nome}}
        })
        return {"sucesso": True, "usuario": resposta.user}
    except Exception as e:
        return {"sucesso": False, "erro": str(e)}


def fazer_login(email: str, senha: str) -> dict:
    """Autentica um usuário existente com e-mail e senha."""
    cliente = obter_cliente()
    try:
        resposta = cliente.auth.sign_in_with_password({
            "email": email,
            "password": senha
        })
        return {"sucesso": True, "usuario": resposta.user}
    except Exception as e:
        return {"sucesso": False, "erro": str(e)}


def fazer_logout():
    """Encerra a sessão do usuário e limpa o estado da aplicação."""
    cliente = obter_cliente()
    try:
        cliente.auth.sign_out()
    except Exception:
        pass

    # Limpa todas as variáveis de sessão
    chaves_para_limpar = [
        "usuario_logado", "usuario_id", "usuario_nome",
        "usuario_email", "perfil_preenchido", "avaliacao_enviada",
    ]
    for chave in chaves_para_limpar:
        st.session_state[chave] = False if chave not in ("usuario_id", "usuario_nome", "usuario_email") else None

    st.rerun()


def salvar_perfil(dados_perfil: dict) -> dict:
    """Salva os dados do questionário de perfil do usuário no banco de dados."""
    cliente = obter_cliente()
    try:
        cliente.table("usuarios_perfil").insert(dados_perfil).execute()
        return {"sucesso": True}
    except Exception as e:
        return {"sucesso": False, "erro": str(e)}


def salvar_avaliacao(dados_avaliacao: dict) -> dict:
    """Salva a avaliação do usuário no banco de dados."""
    cliente = obter_cliente()
    try:
        cliente.table("avaliacoes").insert(dados_avaliacao).execute()
        return {"sucesso": True}
    except Exception as e:
        return {"sucesso": False, "erro": str(e)}
