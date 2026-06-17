"""
Página 4 — Estudo de Caso Real
Apresenta um estudo de caso prático com dados do mercado financeiro brasileiro.

NOTA PARA O DESENVOLVEDOR:
Esta página está estruturada como template.
O conteúdo detalhado (ativos, período e metodologia) deve ser inserido
nas seções marcadas com [PREENCHER]. As seções de código Python e gráficos
serão adicionadas após a definição do caso.
"""
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import yfinance as yf
from datetime import datetime, timedelta


def verificar_acesso():
    """Redireciona se o usuário não estiver autenticado."""
    if not st.session_state.get("usuario_logado") or not st.session_state.get("perfil_preenchido"):
        st.warning("⚠️ Você precisa estar logado para acessar esta página.")
        st.page_link("pages/2_Cadastro.py", label="← Ir para Cadastro")
        st.stop()


# ════════════════════════════════════════════════════════════════════════════════
# CONFIGURAÇÕES DO ESTUDO DE CASO
# Edite as variáveis abaixo para personalizar o estudo de caso.
# ════════════════════════════════════════════════════════════════════════════════

TITULO_CASO = "Otimização de Carteira com Ações da B3"
SUBTITULO_CASO = "Aplicando a Teoria Moderna do Portfólio no mercado brasileiro"

# Ativos do estudo de caso (tickers com sufixo .SA para a B3)
TICKERS = ["PETR4.SA", "VALE3.SA", "ITUB4.SA", "WEGE3.SA", "BBAS3.SA"]

# Período de análise
DATA_INICIO = "2022-01-01"
DATA_FIM = "2024-12-31"

# ════════════════════════════════════════════════════════════════════════════════


@st.cache_data(ttl=3600)
def carregar_dados_caso(tickers: list, inicio: str, fim: str):
    """Baixa os dados históricos para o estudo de caso."""
    try:
        dados = yf.download(tickers, start=inicio, end=fim, auto_adjust=True, progress=False)["Close"]
        dados.columns = [col.replace(".SA", "") for col in dados.columns]
        return dados.dropna()
    except Exception:
        return None


def main():
    verificar_acesso()

    st.progress(4 / 6, text="Etapa 4 de 6 — Estudo de Caso Real")

    st.markdown(f"# 📈 Estudo de Caso: {TITULO_CASO}")
    st.markdown(f"*{SUBTITULO_CASO}*")
    st.divider()

    st.info("""
    📌 **Sobre este estudo de caso**

    Este estudo de caso demonstra como os conceitos de Finanças Quantitativas
    apresentados na seção anterior se aplicam na prática ao mercado financeiro brasileiro.
    Todos os dados utilizados são públicos e foram obtidos via B3 / Yahoo Finance.
    """)

    # ── Seção 1: Contextualização ─────────────────────────────────────────
    st.markdown("## 1. Contextualização")
    st.markdown(f"""
    **Problema:** Um investidor deseja alocar seu capital entre ações da B3, mas
    não sabe como escolher a combinação que ofereça o melhor equilíbrio entre
    **retorno e risco**.

    **Solução proposta:** Aplicar os princípios da **Teoria Moderna do Portfólio**
    (Harry Markowitz, 1952) para identificar a composição de carteira que maximiza
    o retorno para um dado nível de risco.

    **Período analisado:** {DATA_INICIO} a {DATA_FIM}
    **Ativos analisados:** {', '.join([t.replace('.SA', '') for t in TICKERS])}
    **Fonte dos dados:** B3 via Yahoo Finance (yfinance)
    """)
    st.divider()

    # ── Seção 2: Dados Utilizados ──────────────────────────────────────────
    st.markdown("## 2. Dados Utilizados")

    with st.spinner("Carregando dados do estudo de caso..."):
        precos = carregar_dados_caso(TICKERS, DATA_INICIO, DATA_FIM)

    if precos is None or precos.empty:
        st.warning("⚠️ Não foi possível carregar os dados. Verifique sua conexão.")
        return

    st.markdown(f"""
    Os dados abaixo mostram a evolução do preço de fechamento diário ajustado
    (dividendos e splits incluídos) das ações selecionadas ao longo do período analisado.
    """)

    # Preços normalizados
    precos_norm = (precos / precos.iloc[0]) * 100
    fig_dados = px.line(
        precos_norm,
        labels={"value": "Índice (base 100)", "variable": "Ativo", "index": "Data"},
        color_discrete_sequence=px.colors.qualitative.Set1,
    )
    fig_dados.update_layout(
        title="Evolução dos Preços — Base 100",
        plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
        font_color="#F1F5F9", hovermode="x unified",
    )
    st.plotly_chart(fig_dados, use_container_width=True)

    # Estatísticas descritivas
    retornos = precos.pct_change().dropna()
    st.markdown("**Estatísticas dos retornos diários:**")
    desc = (retornos * 100).describe().round(4)
    st.dataframe(desc, use_container_width=True)
    st.divider()

    # ── Seção 3: Metodologia ──────────────────────────────────────────────
    st.markdown("## 3. Metodologia Aplicada")
    st.markdown("""
    Utilizamos a abordagem de **Simulação de Monte Carlo** para gerar milhares de
    combinações aleatórias de pesos entre os ativos e encontrar aquela que oferece
    o **maior Índice de Sharpe** (melhor relação risco/retorno).

    **Passos da metodologia:**
    1. Calcular os retornos diários de cada ativo
    2. Estimar a matrix de covariância dos retornos
    3. Simular 5.000 carteiras com pesos aleatórios
    4. Calcular retorno, volatilidade e Sharpe de cada carteira simulada
    5. Identificar a carteira com o maior Índice de Sharpe
    """)

    # Simulação de Monte Carlo
    st.markdown("### Simulação de Monte Carlo — 5.000 carteiras")

    n_ativos = len(retornos.columns)
    n_simulacoes = 5000
    taxa_livre_risco = 0.1075  # Selic aproximada no período

    retorno_anual = retornos.mean() * 252
    cov_anual = retornos.cov() * 252

    # Arrays para armazenar resultados
    resultados = np.zeros((3, n_simulacoes))
    pesos_simulados = np.zeros((n_ativos, n_simulacoes))

    np.random.seed(42)  # Para reprodutibilidade
    for i in range(n_simulacoes):
        pesos = np.random.random(n_ativos)
        pesos /= pesos.sum()  # Normaliza para somar 100%

        ret_port = np.dot(pesos, retorno_anual)
        vol_port = np.sqrt(np.dot(pesos.T, np.dot(cov_anual, pesos)))
        sharpe_port = (ret_port - taxa_livre_risco) / vol_port

        resultados[0, i] = ret_port
        resultados[1, i] = vol_port
        resultados[2, i] = sharpe_port
        pesos_simulados[:, i] = pesos

    df_simulacao = pd.DataFrame({
        "Volatilidade (%)": resultados[1] * 100,
        "Retorno (%)": resultados[0] * 100,
        "Índice de Sharpe": resultados[2],
    })

    fig_mc = px.scatter(
        df_simulacao,
        x="Volatilidade (%)", y="Retorno (%)",
        color="Índice de Sharpe", color_continuous_scale="Viridis",
        opacity=0.6,
        labels={"Índice de Sharpe": "Sharpe"},
    )

    # Destaca a carteira ótima
    idx_melhor = resultados[2].argmax()
    fig_mc.add_trace(go.Scatter(
        x=[resultados[1, idx_melhor] * 100],
        y=[resultados[0, idx_melhor] * 100],
        mode="markers",
        marker=dict(size=18, color="#F59E0B", symbol="star", line=dict(width=2, color="white")),
        name="⭐ Carteira Ótima",
    ))
    fig_mc.update_layout(
        title="Fronteira Eficiente — Simulação de Monte Carlo",
        plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
        font_color="#F1F5F9",
    )
    st.plotly_chart(fig_mc, use_container_width=True)
    st.divider()

    # ── Seção 4: Resultados ───────────────────────────────────────────────
    st.markdown("## 4. Resultados")

    pesos_otimos = pesos_simulados[:, idx_melhor]
    ret_otimo = resultados[0, idx_melhor]
    vol_otimo = resultados[1, idx_melhor]
    sharpe_otimo = resultados[2, idx_melhor]

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Retorno Anual Estimado", f"{ret_otimo * 100:.2f}%")
    with col2:
        st.metric("Volatilidade Anual", f"{vol_otimo * 100:.2f}%")
    with col3:
        st.metric("Índice de Sharpe", f"{sharpe_otimo:.2f}")

    st.markdown("### Composição da Carteira Ótima")
    df_pesos = pd.DataFrame({
        "Ativo": retornos.columns,
        "Peso (%)": (pesos_otimos * 100).round(2),
    }).sort_values("Peso (%)", ascending=False)

    col_tabela, col_pizza = st.columns([1, 2])
    with col_tabela:
        st.dataframe(df_pesos.set_index("Ativo"), use_container_width=True)
    with col_pizza:
        fig_pizza = px.pie(
            df_pesos, values="Peso (%)", names="Ativo",
            color_discrete_sequence=px.colors.qualitative.Set1,
        )
        fig_pizza.update_layout(
            plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
            font_color="#F1F5F9",
        )
        st.plotly_chart(fig_pizza, use_container_width=True)

    # Comparação carteira ótima vs. igual peso
    pesos_iguais = np.array([1 / n_ativos] * n_ativos)
    ret_igual = np.dot(pesos_iguais, retorno_anual)
    vol_igual = np.sqrt(np.dot(pesos_iguais.T, np.dot(cov_anual, pesos_iguais)))
    sharpe_igual = (ret_igual - taxa_livre_risco) / vol_igual

    st.markdown("### Comparativo: Carteira Ótima vs. Pesos Iguais")
    df_comp = pd.DataFrame({
        "Estratégia": ["Pesos Iguais", "Carteira Ótima (Sharpe máximo)"],
        "Retorno Anual (%)": [round(ret_igual * 100, 2), round(ret_otimo * 100, 2)],
        "Volatilidade (%)": [round(vol_igual * 100, 2), round(vol_otimo * 100, 2)],
        "Índice de Sharpe": [round(sharpe_igual, 2), round(sharpe_otimo, 2)],
    })
    st.dataframe(df_comp.set_index("Estratégia"), use_container_width=True)
    st.divider()

    # ── Seção 5: Conclusões ───────────────────────────────────────────────
    st.markdown("## 5. Conclusões")
    st.markdown(f"""
    Este estudo de caso demonstrou que a aplicação da **Teoria Moderna do Portfólio**,
    combinada com técnicas de simulação computacional, permite identificar alocações
    de ativos significativamente mais eficientes do que estratégias ingênuas como
    a de pesos iguais.

    **Principais aprendizados:**
    - A diversificação entre ativos com baixa correlação **reduz o risco total** da carteira
    - O **Índice de Sharpe** é uma métrica poderosa para comparar estratégias de investimento
    - Modelos quantitativos fornecem uma base objetiva para decisões de alocação de capital
    - Resultados históricos **não garantem** retornos futuros — o modelo é uma ferramenta,
      não uma certeza

    **Limitações:**
    - A simulação de Monte Carlo assume que os retornos futuros seguirão o mesmo padrão histórico
    - Custos de transação, liquidez e impostos não foram considerados neste modelo simplificado
    - A Selic utilizada como taxa livre de risco é uma aproximação
    """)

    st.caption(
        "⚠️ *Análise com finalidade exclusivamente educacional. "
        "Não constitui recomendação de investimento.*"
    )
    st.divider()

    # ── Próximo Passo ────────────────────────────────────────────────
    if st.button("Ir para a Avaliação →", type="primary", use_container_width=True):
        st.switch_page("pages/5_Avaliacao.py")

    st.divider()
    st.caption(
        "Portal FinQuant © 2025 | Trabalho de Conclusão de Curso | Fins Acadêmicos e Educacionais"
    )


main()
