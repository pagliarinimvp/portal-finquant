"""
Página 6 — Agradecimento
Mensagem final de agradecimento ao usuário pela participação na pesquisa
e conclusão da jornada no Portal FinQuant.
"""
import streamlit as st
from utils.auth import fazer_logout


def verificar_acesso():
    """Redireciona se a avaliação ainda não foi enviada."""
    if not st.session_state.get("avaliacao_enviada", False):
        st.warning("⚠️ Você precisa concluir a avaliação para acessar esta página.")
        st.page_link("pages/5_Avaliacao.py", label="← Ir para Avaliação")
        st.stop()


def main():
    verificar_acesso()

    st.progress(6 / 6, text="🎉 Jornada concluída!")

    nome = st.session_state.get("usuario_nome", "Participante")

    # ── Cabeçalho ───────────────────────────────────────────────────
    st.markdown(
        f"<h1 style='text-align:center; font-size:2.5rem;'>🎉 Muito Obrigado, {nome}!</h1>",
        unsafe_allow_html=True
    )
    st.success("""
    ## ✅ Você concluiu o Portal FinQuant!

    Sua participação é fundamental para o sucesso desta pesquisa acadêmica.
    """)
    st.divider()

    # ── Mensagem do autor e Recursos ───────────────────────────────────
    col_msg, col_recursos = st.columns([3, 2])

    with col_msg:
        st.markdown(f"""
        ### 🙏 Uma mensagem do autor

        Caro(a) **{nome}**,

        Agradeço imensamente por dedicar seu tempo para conhecer o **Portal FinQuant**
        e contribuir com esta pesquisa. Cada participação é uma contribuição valiosa para
        demonstrar que é possível tornar o conhecimento de **Finanças Quantitativas**
        acessível ao grande público.

        Espero que esta jornada tenha despertado em você a curiosidade sobre esta
        fascinante área que combina **matemática, estatística e mercado financeiro**
        de forma única e poderosa.

        Se quiser continuar aprendendo, os recursos ao lado são excelentes pontos de partida.
        O mais importante é que você já deu o primeiro passo — e isso faz toda a diferença!

        Com gratidão,

        **[Nome do Autor]**
        *[Curso — Turma — Ano]*
        *[Nome da Instituição de Ensino]*
        """)

    with col_recursos:
        st.info("""
        ### 📚 Continue Aprendendo

        **Educação Financeira — Base:**
        - [ANBIMA Educa](https://www.anbima.com.br/pt_br/educar/)
        - [Banco Central — Cidadania Financeira](https://www.bcb.gov.br/cidadaniafinanceira)
        - [B3 Educação](https://edu.b3.com.br)

        **Finanças Quantitativas:**
        - [Comunidade de Estatística](https://comunidadedeestatistica.com.br)
        - [Python para Finanças — YouTube](https://youtube.com)
        - [Quantitative Finance — Coursera](https://coursera.org)

        **Certificações:**
        - CPA-10 / CPA-20 (ANBIMA)
        - CEA — Especialista em Investimentos
        - CFP® (Planejador Financeiro Pessoal)
        """)

        st.warning("""
        ⚠️ **Lembre-se sempre:**

        Conhecimento é essencial, mas sempre consulte
        um **profissional certificado** antes de tomar
        decisões de investimento!
        """)

    st.divider()

    # ── Informações do Projeto ──────────────────────────────────────
    st.markdown("### 📋 Sobre este Projeto")
    col_i1, col_i2, col_i3, col_i4 = st.columns(4)
    with col_i1:
        st.metric("Projeto", "Portal FinQuant")
    with col_i2:
        st.metric("Tipo", "TCC")
    with col_i3:
        st.metric("Área", "Finanças Quantitativas")
    with col_i4:
        st.metric("Ano", "2025")

    st.divider()

    # ── Botões de Ação ─────────────────────────────────────────────
    col_btn1, col_btn2 = st.columns(2)

    with col_btn1:
        if st.button("🔄 Recomeçar do início", use_container_width=True):
            # Limpa toda a sessão e volta ao início
            for chave in list(st.session_state.keys()):
                del st.session_state[chave]
            st.switch_page("pages/1_Apresentacao.py")

    with col_btn2:
        if st.button("🚪 Sair da conta", use_container_width=True):
            fazer_logout()

    st.divider()
    st.caption(
        "Portal FinQuant © 2025 | Trabalho de Conclusão de Curso | Fins Acadêmicos e Educacionais"
    )


main()
