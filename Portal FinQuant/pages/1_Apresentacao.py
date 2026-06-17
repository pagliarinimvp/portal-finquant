"""
Página 1 — Apresentação e Disclaimer
Apresenta o projeto ao usuário e solicita a aceitação do disclaimer
para liberar o acesso ao restante do portal.
"""
import streamlit as st


def main():
    # ── Cabeçalho ──────────────────────────────────────────────────────────
    col_esq, col_centro, col_dir = st.columns([1, 4, 1])
    with col_centro:
        st.markdown(
            "<h1 style='text-align:center; font-size:2.8rem;'>📊 Portal FinQuant</h1>",
            unsafe_allow_html=True
        )
        st.markdown(
            "<p style='text-align:center; font-size:1.1rem; color:#94A3B8;'>"
            "Portal Educacional de Finanças Quantitativas</p>",
            unsafe_allow_html=True
        )

    st.divider()

    # ── Apresentação do Projeto ─────────────────────────────────────────────
    st.markdown("## 🎓 Bem-vindo ao Portal FinQuant")

    col_texto, col_jornada = st.columns([3, 2])

    with col_texto:
        st.markdown("""
        O **Portal FinQuant** é um projeto acadêmico desenvolvido como
        **Trabalho de Conclusão de Curso (TCC)**, com o objetivo de
        **democratizar o acesso ao conhecimento em Finanças Quantitativas**,
        tornando conceitos complexos acessíveis ao público que nunca teve
        contato com essa área.

        Finanças Quantitativas combinam **matemática, estatística e
        programação** para analisar mercados financeiros com rigor científico —
        e este portal foi criado para mostrar que qualquer pessoa pode
        compreender seus fundamentos.

        ### O que você vai encontrar aqui:
        - 📖 Conceitos fundamentais explicados de forma didática
        - 📊 Visualizações interativas com **dados reais do mercado brasileiro**
        - 🧪 Um estudo de caso prático aplicado à B3
        - ✅ Avaliação do seu aprendizado ao final da jornada
        """)

    with col_jornada:
        st.info("""
        **🗺️ Sua Jornada no Portal**

        1. 🏠 **Apresentação** ← *você está aqui*
        2. 👤 Cadastro + Perfil de pesquisa
        3. 📚 Conceitos de Fin. Quantitativas
        4. 📈 Estudo de Caso Real (B3)
        5. ⭐ Avaliação do portal
        6. 🙏 Agradecimento

        ---
        ⏱️ *Tempo estimado: 20–30 minutos*
        """)

    st.divider()

    # ── Disclaimer ─────────────────────────────────────────────────────────
    st.markdown("## ⚠️ Aviso Importante — Leia com atenção antes de continuar")

    st.warning("""
    **DISCLAIMER — FINALIDADE EXCLUSIVAMENTE ACADÊMICA E EDUCACIONAL**

    Este portal foi desenvolvido **exclusivamente para fins acadêmicos e educacionais**
    como parte de um Trabalho de Conclusão de Curso (TCC).

    **Nenhuma das informações, análises ou exemplos apresentados neste portal constituem:**
    - Recomendação ou oferta de investimento
    - Consultoria ou assessoria financeira
    - Assessoria em valores mobiliários nos termos da Resolução CVM nº 19/2021

    **Os riscos do mercado financeiro são reais e significativos:**
    - Investimentos em renda variável podem resultar em perdas **totais ou parciais** do capital
    - Resultados passados **não garantem** resultados futuros
    - Modelos matemáticos e estatísticos possuem limitações e **não eliminam** o risco de mercado
    - O uso de alavancagem pode ampliar perdas além do capital investido

    **Antes de tomar qualquer decisão de investimento, consulte obrigatoriamente um
    profissional devidamente habilitado e certificado pela CVM (Comissão de Valores
    Mobiliários) e/ou credenciado pela ANBIMA.**

    O autor deste trabalho e a instituição de ensino **não se responsabilizam** por
    quaisquer decisões financeiras tomadas com base nas informações aqui apresentadas.
    """)

    st.divider()

    # ── Confirmação e Botão de Avanço ───────────────────────────────────────
    st.markdown("### Para continuar, confirme que leu e compreendeu o aviso acima:")

    aceito = st.checkbox(
        "✅ **Li e compreendi o disclaimer acima.** Estou ciente de que este portal tem "
        "finalidade exclusivamente acadêmica e educacional, e que as informações aqui "
        "apresentadas **não constituem recomendação de investimento**.",
        value=st.session_state.get("disclaimer_aceito", False),
        key="checkbox_disclaimer"
    )

    if aceito:
        st.session_state.disclaimer_aceito = True
        st.success("✅ Perfeito! Você pode prosseguir para o cadastro.")
        st.markdown("")  # espaçamento

        if st.button("Ir para o Cadastro →", type="primary", use_container_width=True):
            st.switch_page("pages/2_Cadastro.py")
    else:
        st.session_state.disclaimer_aceito = False
        st.info("☝️ Marque a caixa acima para habilitar o acesso ao conteúdo do portal.")

    # ── Rodapé ─────────────────────────────────────────────────────────────
    st.divider()
    st.caption(
        "Portal FinQuant © 2025 | Trabalho de Conclusão de Curso | Fins Acadêmicos e Educacionais"
    )


main()
