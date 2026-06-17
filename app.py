"""
Portal FinQuant — Ponto de Entrada Principal
Este arquivo configura a aplicação globalmente e controla o sistema de navegação.
"""
import streamlit as st
from utils.navigation import inicializar_sessao, configurar_paginas, aplicar_estilos
from utils.auth import fazer_logout

# Configuração global da página (deve ser a primeira chamada Streamlit)
st.set_page_config(
    page_title="Portal FinQuant",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        "About": "Portal Educacional de Finanças Quantitativas — Trabalho de Conclusão de Curso"
    }
)

# Aplicar estilos CSS personalizados
aplicar_estilos()

# Inicializar variáveis de sessão com valores padrão
inicializar_sessao()

# ──────────────────────────────────────────────
# Barra Lateral (Sidebar)
# ──────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 📊 Portal FinQuant")
    st.caption("*Finanças Quantitativas para todos*")
    st.divider()

    # Exibe informações do usuário logado
    if st.session_state.get("usuario_logado"):
        nome = st.session_state.get("usuario_nome", "Usuário")
        email = st.session_state.get("usuario_email", "")
        st.markdown(f"👤 **{nome}**")
        st.caption(email)
        st.divider()

        if st.button("🚪 Sair", key="btn_logout", use_container_width=True):
            fazer_logout()

    # Progresso da jornada
    st.divider()
    st.markdown("**Sua jornada:**")

    etapas = [
        (st.session_state.get("disclaimer_aceito", False), "Apresentação"),
        (st.session_state.get("usuario_logado", False), "Cadastro"),
        (st.session_state.get("perfil_preenchido", False), "Conceitos"),
        (st.session_state.get("perfil_preenchido", False), "Estudo de Caso"),
        (st.session_state.get("avaliacao_enviada", False), "Avaliação"),
        (st.session_state.get("avaliacao_enviada", False), "Agradecimento"),
    ]
    for concluido, nome_etapa in etapas:
        icone = "✅" if concluido else "⭕"
        st.caption(f"{icone} {nome_etapa}")

    st.divider()
    st.caption("TCC — Finanças Quantitativas")
    st.caption("© 2025")

# ──────────────────────────────────────────────
# Configurar e executar a navegação condicional
# ──────────────────────────────────────────────
pg = configurar_paginas()
pg.run()
