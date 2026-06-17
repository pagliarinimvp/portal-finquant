"""
Utilitário de Navegação
Controla quais páginas ficam visíveis na barra lateral,
baseado no progresso do usuário na jornada do portal.
"""
import streamlit as st


def inicializar_sessao():
    """
    Garante que todas as variáveis de sessão existam com valores padrão.
    Chamada no início de cada execução do app.py.
    """
    valores_padrao = {
        "disclaimer_aceito": False,
        "usuario_logado": False,
        "usuario_id": None,
        "usuario_nome": None,
        "usuario_email": None,
        "perfil_preenchido": False,
        "avaliacao_enviada": False,
    }
    for chave, valor in valores_padrao.items():
        if chave not in st.session_state:
            st.session_state[chave] = valor


def configurar_paginas():
    """
    Retorna a lista de páginas disponíveis conforme o avanço do usuário.
    Apenas páginas desbloqueadas aparecem na barra lateral.
    """
    # Página 1 sempre disponível
    paginas = [
        st.Page("pages/1_Apresentacao.py", title="🏠 Apresentação", default=True)
    ]

    # Página 2 liberada após aceitar o disclaimer
    if st.session_state.disclaimer_aceito:
        paginas.append(
            st.Page("pages/2_Cadastro.py", title="👤 Cadastro")
        )

    # Páginas 3, 4 e 5 liberadas após login e perfil preenchido
    if st.session_state.usuario_logado and st.session_state.perfil_preenchido:
        paginas.extend([
            st.Page("pages/3_Conceitos.py", title="📚 Conceitos"),
            st.Page("pages/4_Estudo_de_Caso.py", title="📈 Estudo de Caso"),
            st.Page("pages/5_Avaliacao.py", title="⭐ Avaliação"),
        ])

    # Página 6 liberada após envio da avaliação
    if st.session_state.avaliacao_enviada:
        paginas.append(
            st.Page("pages/6_Agradecimento.py", title="🙏 Agradecimento")
        )

    return st.navigation(paginas)


def aplicar_estilos():
    """Aplica CSS personalizado para melhorar a aparência do portal."""
    st.markdown("""
    <style>
        /* Cards de métricas com fundo */
        div[data-testid="stMetric"] {
            background-color: rgba(30, 41, 59, 0.8);
            border-radius: 10px;
            padding: 14px 20px;
            border: 1px solid rgba(59, 130, 246, 0.2);
        }
        /* Botões primários com bordas arredondadas */
        div.stButton > button {
            border-radius: 8px;
            font-weight: 500;
            transition: all 0.2s ease;
        }
        /* Links da sidebar com melhor espaçamento */
        section[data-testid="stSidebar"] .stMarkdown {
            padding: 2px 0;
        }
        /* Expandable sections */
        div[data-testid="stExpander"] {
            border: 1px solid rgba(59, 130, 246, 0.15);
            border-radius: 8px;
        }
    </style>
    """, unsafe_allow_html=True)
