"""
Funções de Autenticação
Gerencia o cadastro, login, logout e persistência de dados do usuário via Supabase.
Inclui suporte a OAuth (Google e GitHub) via Supabase.
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


def obter_url_oauth(provedor: str, redirect_url: str) -> dict:
    """
    Gera a URL de autenticação OAuth para o provedor especificado (google/github).
    O usuário será redirecionado para essa URL e, após autenticar,
    retornará ao app com os tokens na URL.
    """
    cliente = obter_cliente()
    try:
        resposta = cliente.auth.sign_in_with_oauth({
            "provider": provedor,
            "options": {
                "redirect_to": redirect_url,
                "skip_browser_redirect": True,
            }
        })
        return {"sucesso": True, "url": resposta.url}
    except Exception as e:
        return {"sucesso": False, "erro": str(e)}


def processar_oauth_callback(access_token: str, refresh_token: str) -> dict:
    """
    Processa o retorno do OAuth após o usuário ser redirecionado de volta ao app.
    Troca os tokens por uma sessão válida e retorna os dados do usuário.
    """
    cliente = obter_cliente()
    try:
        resposta = cliente.auth.set_session(access_token, refresh_token)
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
        st.session_state[chave] = False if chave != "usuario_id" and chave != "usuario_nome" and chave != "usuario_email" else None

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
