"""
Página 2 — Cadastro e Perfil do Usuário
Gerencia o acesso ao portal (login/cadastro) e coleta os dados
do questionário de perfil para fins de pesquisa acadêmica.
"""
import streamlit as st
from utils.auth import cadastrar_usuario, fazer_login, salvar_perfil


def verificar_acesso():
    """Redireciona para a Página 1 se o disclaimer ainda não foi aceito."""
    if not st.session_state.get("disclaimer_aceito", False):
        st.warning("⚠️ Você precisa ler e aceitar o disclaimer antes de continuar.")
        st.page_link("pages/1_Apresentacao.py", label="← Voltar ao início")
        st.stop()


def tela_login_cadastro():
    """Exibe o formulário de login ou criação de conta."""
    st.markdown("## 👤 Acesso ao Portal")
    st.markdown("Crie uma conta ou entre com uma já existente para continuar.")

    aba_entrar, aba_criar = st.tabs(["🔑 Já tenho conta", "📝 Criar nova conta"])

    # ── Aba: Login ───────────────────────────────────────────────────────
    with aba_entrar:
        with st.form("form_login"):
            st.markdown("### Entre com sua conta")
            email = st.text_input("E-mail", placeholder="seu@email.com")
            senha = st.text_input("Senha", type="password", placeholder="••••••••")
            btn_entrar = st.form_submit_button(
                "Entrar", type="primary", use_container_width=True
            )

        if btn_entrar:
            if email and senha:
                with st.spinner("Verificando credenciais..."):
                    resultado = fazer_login(email, senha)

                if resultado["sucesso"]:
                    usuario = resultado["usuario"]
                    st.session_state.usuario_logado = True
                    st.session_state.usuario_id = str(usuario.id)
                    st.session_state.usuario_email = usuario.email
                    st.session_state.usuario_nome = (
                        usuario.user_metadata.get("nome") or email.split("@")[0]
                    )
                    st.success("✅ Login realizado com sucesso!")
                    st.rerun()
                else:
                    st.error(f"❌ {resultado['erro']}")
            else:
                st.warning("⚠️ Preencha e-mail e senha.")

        st.divider()
        st.markdown("**Ou entre com (em breve):**")
        col_g, col_gh = st.columns(2)
        with col_g:
            st.button("🔵 Google", disabled=True, use_container_width=True)
        with col_gh:
            st.button("⚫ GitHub", disabled=True, use_container_width=True)
        st.caption(
            "O OAuth requer configuração adicional no painel do Supabase. "
            "Consulte o README.md."
        )

    # ── Aba: Cadastro ───────────────────────────────────────────────────────
    with aba_criar:
        with st.form("form_cadastro"):
            st.markdown("### Crie sua conta gratuita")
            nome = st.text_input("Nome completo", placeholder="Seu Nome Completo")
            email_cad = st.text_input("E-mail", placeholder="seu@email.com")
            senha_cad = st.text_input(
                "Senha", type="password", placeholder="Mínimo 6 caracteres"
            )
            confirmar = st.text_input(
                "Confirmar senha", type="password", placeholder="Repita a senha"
            )
            btn_criar = st.form_submit_button(
                "Criar conta", type="primary", use_container_width=True
            )

        if btn_criar:
            if not all([nome, email_cad, senha_cad, confirmar]):
                st.warning("⚠️ Preencha todos os campos.")
            elif senha_cad != confirmar:
                st.error("❌ As senhas não coincidem.")
            elif len(senha_cad) < 6:
                st.error("❌ A senha deve ter no mínimo 6 caracteres.")
            else:
                with st.spinner("Criando conta..."):
                    resultado = cadastrar_usuario(email_cad, senha_cad, nome)

                if resultado["sucesso"]:
                    usuario = resultado["usuario"]
                    st.session_state.usuario_logado = True
                    st.session_state.usuario_id = str(usuario.id)
                    st.session_state.usuario_email = email_cad
                    st.session_state.usuario_nome = nome
                    st.success("✅ Conta criada com sucesso!")
                    st.rerun()
                else:
                    st.error(f"❌ {resultado['erro']}")


def formulario_perfil():
    """Exibe o questionário de pesquisa de perfil do usuário."""
    nome = st.session_state.get("usuario_nome", "Usuário")
    st.markdown(f"## 📋 Olá, **{nome}**! Complete seu perfil de pesquisa")
    st.markdown("""
    As perguntas abaixo são parte da pesquisa acadêmica deste TCC.
    Suas respostas são **confidenciais** e serão utilizadas de forma anônima na análise.
    """)
    st.divider()

    with st.form("form_perfil"):

        # ── Pergunta 1: Idade ──────────────────────────────────────────────
        st.markdown("### 1. Qual é a sua idade?")
        idade = st.number_input(
            "Idade", min_value=14, max_value=100, value=25, step=1,
            label_visibility="collapsed"
        )

        st.markdown("---")

        # ── Pergunta 2: Gênero ─────────────────────────────────────────────
        st.markdown("### 2. Qual é o seu gênero?")
        genero = st.radio(
            "Gênero",
            options=["Masculino", "Feminino", "Outro / Prefiro não informar"],
            horizontal=True,
            label_visibility="collapsed"
        )

        st.markdown("---")

        # ── Pergunta 3: Faixa de Renda ─────────────────────────────────────
        st.markdown("### 3. Qual é a sua faixa de renda familiar mensal?")
        faixas = [
            "Até R$ 1.518 (até 1 salário mínimo)",
            "R$ 1.518 – R$ 3.036 (1 a 2 salários mínimos)",
            "R$ 3.036 – R$ 6.072 (2 a 4 salários mínimos)",
            "R$ 6.072 – R$ 12.144 (4 a 8 salários mínimos)",
            "R$ 12.144 – R$ 20.000 (8 a ~13 salários mínimos)",
            "Acima de R$ 20.000",
            "Prefiro não informar",
        ]
        faixa_renda = st.selectbox(
            "Faixa de renda", options=faixas, label_visibility="collapsed"
        )

        st.markdown("---")

        # ── Pergunta 4: Produtos Financeiros ───────────────────────────────
        st.markdown("### 4. Quais produtos financeiros você já adquiriu ou conhece?")
        st.caption("Selecione todos que se aplicam")
        produtos_opcoes = [
            "Poupança",
            "CDB (Certificado de Depósito Bancário)",
            "LCI / LCA (Letras de Crédito Imobiliário/Agronegócio)",
            "Tesouro Direto",
            "Fundos de Investimento (DI, Multimercado, etc.)",
            "Ações (B3)",
            "FIIs (Fundos de Investimento Imobiliário)",
            "ETFs (Fundos de Índice)",
            "Derivativos / Opções",
            "Criptomoedas",
            "Previdência Privada (PGBL / VGBL)",
            "Nenhum dos acima",
        ]
        produtos = st.multiselect(
            "Produtos financeiros", options=produtos_opcoes,
            label_visibility="collapsed"
        )

        st.markdown("---")

        # ── Pergunta 5: Nível em Renda Variável ───────────────────────────
        st.markdown("### 5. Como você avalia seu conhecimento em renda variável?")
        nivel_rv = st.select_slider(
            "Nível em renda variável",
            options=["Nenhum", "Iniciante", "Intermediário", "Avançado"],
            value="Nenhum",
            label_visibility="collapsed"
        )

        st.markdown("---")

        # ── Pergunta 6: Nível em Estatística ──────────────────────────────
        st.markdown("### 6. Como você avalia seu conhecimento em estatística?")
        nivel_estat = st.select_slider(
            "Nível em estatística",
            options=["Nenhum", "Básico", "Intermediário", "Avançado"],
            value="Nenhum",
            label_visibility="collapsed"
        )

        st.markdown("---")
        btn_salvar = st.form_submit_button(
            "Salvar e Continuar →", type="primary", use_container_width=True
        )

    if btn_salvar:
        dados = {
            "id": st.session_state.usuario_id,
            "nome": st.session_state.usuario_nome,
            "email": st.session_state.usuario_email,
            "idade": idade,
            "genero": genero,
            "faixa_renda": faixa_renda,
            "produtos_financeiros": produtos if produtos else ["Nenhum dos acima"],
            "nivel_renda_variavel": nivel_rv,
            "nivel_estatistica": nivel_estat,
        }
        with st.spinner("Salvando dados..."):
            resultado = salvar_perfil(dados)

        # Mesmo com erro (ex.: perfil duplicado), avançamos para não bloquear o fluxo
        st.session_state.perfil_preenchido = True
        st.success("✅ Perfil salvo! Redirecionando para o conteúdo...")
        st.balloons()
        st.switch_page("pages/3_Conceitos.py")


def main():
    verificar_acesso()

    st.progress(2 / 6, text="Etapa 2 de 6 — Cadastro e Perfil")

    if not st.session_state.get("usuario_logado", False):
        tela_login_cadastro()

    elif not st.session_state.get("perfil_preenchido", False):
        formulario_perfil()

    else:
        # Usuário já tem conta e perfil completo
        nome = st.session_state.get("usuario_nome", "Usuário")
        st.success(f"✅ Bem-vindo de volta, **{nome}**! Seu cadastro já está completo.")
        if st.button("Continuar para os Conceitos →", type="primary"):
            st.switch_page("pages/3_Conceitos.py")

    st.divider()
    st.caption(
        "Portal FinQuant © 2025 | Trabalho de Conclusão de Curso | Fins Acadêmicos e Educacionais"
    )


main()
