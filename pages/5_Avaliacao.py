"""
Página 5 — Avaliação do Portal
Coleta o feedback do usuário sobre a experiência no portal
e avalia o aprendizado obtido ao longo da jornada.
"""
import streamlit as st
from utils.auth import salvar_avaliacao


def verificar_acesso():
    """Redireciona se o usuário não estiver autenticado."""
    if not st.session_state.get("usuario_logado") or not st.session_state.get("perfil_preenchido"):
        st.warning("⚠️ Você precisa estar logado para acessar esta página.")
        st.page_link("pages/2_Cadastro.py", label="← Ir para Cadastro")
        st.stop()


def mostrar_resumo_perfil():
    """Exibe um resumo das informações do usuário logado."""
    nome = st.session_state.get("usuario_nome", "—")
    email = st.session_state.get("usuario_email", "—")

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("👤 Usuário", nome)
    with col2:
        st.metric("📧 E-mail", email)
    with col3:
        st.metric("📊 Status", "✅ Conteúdo concluído")


def legenda_escala(valor: int, descricoes: dict) -> str:
    """Formata a legenda para os sliders de avaliação."""
    return descricoes.get(valor, str(valor))


def main():
    verificar_acesso()

    st.progress(5 / 6, text="Etapa 5 de 6 — Avaliação do Portal")
    st.markdown("# ⭐ Avaliação do Portal")
    st.markdown(
        "*Suas respostas são muito importantes para a pesquisa acadêmica. "
        "O preenchimento leva menos de 2 minutos.*"
    )
    st.divider()

    mostrar_resumo_perfil()
    st.divider()

    st.markdown("""
    ## 📝 Questionário de Avaliação

    Responda às perguntas abaixo com base na sua experiência ao usar o portal.
    As respostas são utilizadas **exclusivamente para fins de pesquisa acadêmica**.
    """)

    with st.form("form_avaliacao"):

        # ── Pergunta 1: Facilidade de uso ─────────────────────────────────
        st.markdown("### 1. Como você avalia a **facilidade de uso** do portal?")
        facilidade = st.select_slider(
            "Facilidade de uso",
            options=[1, 2, 3, 4, 5],
            value=3,
            format_func=lambda x: {
                1: "1 — Muito difícil",
                2: "2 — Difícil",
                3: "3 — Neutro",
                4: "4 — Fácil",
                5: "5 — Muito fácil",
            }[x],
            label_visibility="collapsed",
        )

        st.markdown("---")

        # ── Pergunta 2: Clareza do conteúdo ───────────────────────────────
        st.markdown("### 2. Como você avalia a **clareza e qualidade do conteúdo** apresentado?")
        clareza = st.select_slider(
            "Clareza do conteúdo",
            options=[1, 2, 3, 4, 5],
            value=3,
            format_func=lambda x: {
                1: "1 — Muito confuso",
                2: "2 — Confuso",
                3: "3 — Neutro",
                4: "4 — Claro",
                5: "5 — Muito claro",
            }[x],
            label_visibility="collapsed",
        )

        st.markdown("---")

        # ── Pergunta 3: Aprendizado percebido ─────────────────────────────
        st.markdown("### 3. O quanto você **aprendeu** sobre Finanças Quantitativas com este portal?")
        aprendizado = st.select_slider(
            "Aprendizado percebido",
            options=[1, 2, 3, 4, 5],
            value=3,
            format_func=lambda x: {
                1: "1 — Não aprendi nada novo",
                2: "2 — Aprendi muito pouco",
                3: "3 — Aprendi algo interessante",
                4: "4 — Aprendi bastante",
                5: "5 — Aprendi muito",
            }[x],
            label_visibility="collapsed",
        )

        st.markdown("---")

        # ── Pergunta 4: Confiança após o portal ───────────────────────────
        st.markdown(
            "### 4. Após usar o portal, você se sente mais **preparado para "
            "estudar o tema** de Finanças Quantitativas?"
        )
        confianca = st.select_slider(
            "Confiança após o portal",
            options=[1, 2, 3, 4, 5],
            value=3,
            format_func=lambda x: {
                1: "1 — Não me sinto preparado",
                2: "2 — Me sinto pouco preparado",
                3: "3 — Indiferente",
                4: "4 — Me sinto razoavelmente preparado",
                5: "5 — Me sinto muito mais preparado",
            }[x],
            label_visibility="collapsed",
        )

        st.markdown("---")

        # ── Pergunta 5: Recomendação ─────────────────────────────────────
        st.markdown("### 5. Você **recomendaria** este portal para outras pessoas?")
        recomendaria = st.radio(
            "Recomendaria?",
            options=["Sim, definitivamente", "Talvez", "Não"],
            horizontal=True,
            label_visibility="collapsed",
        )

        st.markdown("---")

        # ── Campo livre ────────────────────────────────────────────────────
        st.markdown("### 6. Deixe um comentário ou sugestão *(opcional)*")
        comentario = st.text_area(
            "Comentário",
            placeholder="Escreva aqui suas impressões, críticas ou sugestões sobre o portal...",
            label_visibility="collapsed",
            height=120,
        )

        st.markdown("")
        btn_enviar = st.form_submit_button(
            "Enviar Avaliação →", type="primary", use_container_width=True
        )

    if btn_enviar:
        dados_avaliacao = {
            "usuario_id": st.session_state.usuario_id,
            "facilidade_uso": facilidade,
            "clareza_conteudo": clareza,
            "aprendizado_percebido": aprendizado,
            "confianca_pos_portal": confianca,
            "recomendaria": recomendaria == "Sim, definitivamente",
            "comentario_livre": comentario if comentario.strip() else None,
        }

        with st.spinner("Enviando avaliação..."):
            resultado = salvar_avaliacao(dados_avaliacao)

        # Avança independentemente do resultado do banco para não bloquear o usuário
        st.session_state.avaliacao_enviada = True
        st.success("✅ Avaliação enviada com sucesso! Obrigado pela sua participação.")
        st.balloons()
        st.switch_page("pages/6_Agradecimento.py")

    st.divider()
    st.caption(
        "Portal FinQuant © 2025 | Trabalho de Conclusão de Curso | Fins Acadêmicos e Educacionais"
    )


main()
