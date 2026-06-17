"""
Página 3 — Introdução às Finanças Quantitativas
Apresenta os conceitos fundamentais com exemplos didáticos e visualizações
interativas usando dados reais de ações da B3 (Bolsa brasileira).
"""
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import yfinance as yf
from datetime import datetime, timedelta


def verificar_acesso():
    """Redireciona se o usuário não estiver autenticado com perfil preenchido."""
    if not st.session_state.get("usuario_logado") or not st.session_state.get("perfil_preenchido"):
        st.warning("⚠️ Você precisa estar cadastrado e logado para acessar esta página.")
        st.page_link("pages/2_Cadastro.py", label="← Ir para Cadastro")
        st.stop()


@st.cache_data(ttl=3600)  # Cache de 1 hora para não sobrecarregar a API
def carregar_dados_b3():
    """
    Baixa dados históricos dos últimos 2 anos de 5 ações representativas da B3.
    Retorna um DataFrame com os preços de fechamento ajustados.
    """
    tickers_b3 = ["PETR4.SA", "VALE3.SA", "ITUB4.SA", "WEGE3.SA", "BBDC4.SA"]
    data_inicio = (datetime.now() - timedelta(days=730)).strftime("%Y-%m-%d")
    data_fim = datetime.now().strftime("%Y-%m-%d")

    try:
        dados = yf.download(
            tickers_b3, start=data_inicio, end=data_fim, auto_adjust=True, progress=False
        )["Close"]
        # Remove o sufixo ".SA" para exibição mais limpa
        dados.columns = [col.replace(".SA", "") for col in dados.columns]
        dados = dados.dropna()
        return dados
    except Exception:
        return None


def calcular_metricas(precos: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Calcula retorno anual, volatilidade e Índice de Sharpe para cada ativo."""
    retornos = precos.pct_change().dropna()

    metricas = pd.DataFrame({
        "Retorno Anual (%)": (retornos.mean() * 252 * 100).round(2),
        "Volatilidade Anual (%)": (retornos.std() * np.sqrt(252) * 100).round(2),
    })
    metricas["Índice de Sharpe"] = (
        metricas["Retorno Anual (%)"] / metricas["Volatilidade Anual (%)"]
    ).round(2)
    metricas.index.name = "Ativo"

    return metricas, retornos


# ── Seções de Conteúdo ──────────────────────────────────────────────

def secao_o_que_e():
    st.markdown("## 🎯 O que são Finanças Quantitativas?")
    col_texto, col_destaque = st.columns([3, 2])

    with col_texto:
        st.markdown("""
        **Finanças Quantitativas** — ou simplesmente *"Quant Finance"* — é o campo que aplica
        **matemática, estatística e programação** para analisar mercados financeiros,
        precificar ativos e tomar decisões de investimento com base em dados.

        Ao contrário da análise tradicional, que muitas vezes depende de intuição e do
        "feeling" do investidor, a abordagem quantitativa é **sistemática e objetiva**:
        as decisões são guiadas por modelos matemáticos e evidências estatísticas,
        não por emoções.

        O profissional que trabalha com esse método é chamado de **"Quant"** e
        costuma ter formação em Matemática, Estatística, Engenharia, Física ou
        Ciência da Computação.
        """)

    with col_destaque:
        st.info("""
        **💡 Você sabia?**

        O matemático **Jim Simons** criou o primeiro grande fundo quantitativo do mundo,
        o **Medallion Fund**, em 1988.

        Ao longo de 30 anos, o fundo obteve retornos médios de
        **~66% ao ano** (antes de taxas) — um desempenho sem precedentes
        no mercado financeiro global, superando consistentemente o S&P 500.
        """)

    st.divider()


def secao_quant_vs_tradicional():
    st.markdown("## ⚖️ Abordagem Quantitativa vs. Tradicional")

    col_trad, col_quant = st.columns(2)
    with col_trad:
        st.markdown("""
        ### 🧠 Investidor Tradicional
        - Lê balanços, notícias e relatórios de analistas
        - Baseia decisões em intuição e experiência
        - Sujeito a viês emocionais (medo e ganância)
        - Monitora poucos ativos manualmente
        - Tempo de reação limitado em momentos de crise
        """)
    with col_quant:
        st.markdown("""
        ### 📊 Investidor Quantitativo
        - Analisa grandes volumes de dados históricos
        - Decisões baseadas em modelos matemáticos testados
        - Elimina o viés emocional do processo de decisão
        - Pode monitorar centenas de ativos simultaneamente
        - Algoritmos executam estratégias em milissegundos
        """)

    st.divider()


def secao_conceitos_fundamentais():
    st.markdown("## 🔑 Conceitos Fundamentais")

    with st.expander("📈 Retorno — O que é e como calcular", expanded=True):
        st.markdown("""
        **Retorno** é o ganho (ou perda) de um investimento em relação ao valor inicial.

        **Fórmula:**
        > `Retorno (%) = (Preço Final − Preço Inicial) ÷ Preço Inicial × 100`

        **Exemplo:** Você comprou 1 ação por **R$ 10,00** e ela passou a valer **R$ 13,00**.
        Seu retorno foi: `(13 − 10) ÷ 10 × 100 = 30%` 📈

        Em finanças quantitativas, trabalhamos com **retornos diários** para
        construir modelos estatísticos e comparar ativos de períodos diferentes.
        """)

    with st.expander("📉 Risco — O outro lado do retorno"):
        st.markdown("""
        **Risco** em finanças é medido pela **volatilidade** — o quanto o preço de um ativo
        oscila ao longo do tempo. A medida mais utilizada é o **desvio padrão** dos retornos.

        - **Alta volatilidade** → grandes oscilações → maior risco e maior potencial de ganho
        - **Baixa volatilidade** → preços estáveis → menor risco, menor potencial de ganho

        > 🎯 **Regra de ouro:** Não existe retorno sem risco.
        > O segredo está em encontrar o equilíbrio certo para o seu perfil de investidor.
        """)

    with st.expander("🔗 Correlação — A base da diversificação"):
        st.markdown("""
        **Correlação** mede o quanto dois ativos se movem juntos ao longo do tempo.

        | Correlação | Significado |
        |---|---|
        | **+1,0** | Os ativos sobem e caem sempre juntos |
        | **0,0** | Os ativos se movem de forma independente |
        | **−1,0** | Quando um sobe, o outro cai (proteção perfeita) |

        Combinar ativos com **baixa correlação entre si** reduz o risco total da carteira
        sem necessariamente reduzir o retorno esperado — isso é o princípio da **diversificação**.

        > 💬 *"Diversificação é o único almoço grátis em finanças."*
        > — Harry Markowitz, ganhador do Prêmio Nobel de Economia (1990)
        """)

    with st.expander("🏆 Índice de Sharpe — Retorno ajustado ao risco"):
        st.markdown("""
        O **Índice de Sharpe** mede o retorno obtido por unidade de risco assumido.
        É uma das métricas mais importantes em finanças quantitativas.

        **Fórmula:**
        > `Sharpe = (Retorno da Carteira − Taxa Livre de Risco) ÷ Volatilidade`

        | Sharpe | Interpretação |
        |---|---|
        | < 1 | Retorno inadequado para o risco assumido |
        | 1 a 2 | Bom |
        | > 2 | Excelente |
        | > 3 | Excepcional (muito raro) |

        **Em palavras simples:** Um Sharpe de 2 significa que, para cada unidade de risco
        assumida, você obteve 2 unidades de retorno acima da taxa livre de risco.
        """)

    st.divider()


def secao_demo_b3():
    """Seção com visualizações interativas usando dados reais da B3."""
    st.markdown("## 📊 Demonstração com Dados Reais da B3")
    st.markdown(
        "*Abaixo aplicamos os conceitos acima usando dados históricos reais "
        "de ações brasileiras dos últimos 2 anos.*"
    )

    with st.spinner("🔄 Carregando dados do mercado financeiro..."):
        precos = carregar_dados_b3()

    if precos is None or precos.empty:
        st.warning(
            "⚠️ Não foi possível carregar os dados de mercado. "
            "Verifique sua conexão com a internet."
        )
        return

    metricas, retornos = calcular_metricas(precos)

    # ── Gráfico 1: Evolução de Preços Normalizados ───────────────────────
    st.markdown("### 📈 Evolução dos Preços (base 100)")
    st.caption(
        "Normalizamos os preços para comparar ativos com valores diferentes "
        "numa mesma escala. Se a linha está acima de 100, o ativo valorizou."
    )

    precos_norm = (precos / precos.iloc[0]) * 100
    fig_precos = px.line(
        precos_norm,
        labels={"value": "Índice (base 100)", "variable": "Ativo", "index": "Data"},
        color_discrete_sequence=px.colors.qualitative.Set1,
    )
    fig_precos.update_layout(
        plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
        font_color="#F1F5F9", hovermode="x unified", legend_title_text="Ação",
    )
    st.plotly_chart(fig_precos, use_container_width=True)

    # ── Gráfico 2: Risco vs. Retorno ─────────────────────────────────
    st.markdown("### ⚖️ Risco vs. Retorno")
    st.caption(
        "Cada ponto é um ativo. O ideal é estar no canto superior esquerdo: "
        "alto retorno com baixa volatilidade. A cor indica o Índice de Sharpe."
    )

    fig_rr = px.scatter(
        metricas.reset_index(),
        x="Volatilidade Anual (%)", y="Retorno Anual (%)",
        text="Ativo", color="Índice de Sharpe",
        color_continuous_scale="Blues", size_max=20,
    )
    fig_rr.update_traces(
        textposition="top center",
        marker=dict(size=18, line=dict(width=2, color="#3B82F6"))
    )
    fig_rr.update_layout(
        plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
        font_color="#F1F5F9",
    )
    st.plotly_chart(fig_rr, use_container_width=True)

    st.markdown("**Tabela de métricas calculadas:**")
    st.dataframe(metricas, use_container_width=True)

    # ── Gráfico 3: Matriz de Correlação ─────────────────────────────
    st.markdown("### 🔗 Matriz de Correlação entre os Ativos")
    st.caption(
        "Valores próximos de +1 = ativos se movem juntos | "
        "Valores próximos de −1 = se movem em direções opostas."
    )

    corr = retornos.corr().round(2)
    fig_corr = px.imshow(
        corr, text_auto=True,
        color_continuous_scale="RdBu_r", zmin=-1, zmax=1,
        aspect="auto",
    )
    fig_corr.update_layout(
        plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
        font_color="#F1F5F9",
    )
    st.plotly_chart(fig_corr, use_container_width=True)

    # ── Gráfico 4: Poder da Diversificação ──────────────────────────
    st.markdown("### 💼 O Poder da Diversificação")
    st.caption(
        "Comparamos uma carteira concentrada em um único ativo "
        "com uma carteira diversificada com pesos iguais entre os cinco ativos."
    )

    ret_concentrado = retornos["PETR4"]          # 100% em PETR4
    ret_diversificado = retornos.mean(axis=1)    # Média simples = pesos iguais

    acum_conc = (1 + ret_concentrado).cumprod() * 100
    acum_div = (1 + ret_diversificado).cumprod() * 100

    df_comp = pd.DataFrame({
        "Concentrada (100% PETR4)": acum_conc,
        "Diversificada (pesos iguais)": acum_div,
    })
    fig_comp = px.line(
        df_comp,
        labels={"value": "Capital (base 100)", "variable": "Carteira", "index": "Data"},
        color_discrete_map={
            "Concentrada (100% PETR4)": "#EF4444",
            "Diversificada (pesos iguais)": "#22C55E",
        },
    )
    fig_comp.update_layout(
        plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
        font_color="#F1F5F9", hovermode="x unified",
    )
    st.plotly_chart(fig_comp, use_container_width=True)

    # Métricas comparativas
    vol_conc = ret_concentrado.std() * np.sqrt(252) * 100
    vol_div = ret_diversificado.std() * np.sqrt(252) * 100
    sharpe_conc = (ret_concentrado.mean() * 252) / (ret_concentrado.std() * np.sqrt(252))
    sharpe_div = (ret_diversificado.mean() * 252) / (ret_diversificado.std() * np.sqrt(252))

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Volatilidade — Concentrada", f"{vol_conc:.1f}%")
    with col2:
        st.metric(
            "Volatilidade — Diversificada", f"{vol_div:.1f}%",
            delta=f"{vol_div - vol_conc:.1f}%", delta_color="inverse"
        )
    with col3:
        st.metric(
            "Sharpe — Diversificada vs. Concentrada",
            f"{sharpe_div:.2f}",
            delta=f"{sharpe_div - sharpe_conc:.2f}"
        )

    st.caption(
        "⚠️ *Dados históricos não garantem resultados futuros. "
        "Esta demonstração tem fins exclusivamente educacionais.*"
    )
    st.divider()


def secao_brasil():
    st.markdown("## 🇪🇧 Finanças Quantitativas no Brasil")

    col_br1, col_br2 = st.columns(2)
    with col_br1:
        st.markdown("""
        O mercado de **fundos quantitativos no Brasil** tem crescido de forma expressiva.
        Algumas referências do setor:

        - **Giant Steps Capital** — Maior gestora quantitativa do Brasil
        - **Kadima Asset Management** — Pioneira em estratégias sistemáticas
        - **Trend Capital** — Especialista em *trend following* quantitativo

        A **B3** processa mais de **R$ 30 bilhões** em negociações por dia, grande parte
        delas executadas por algoritmos que utilizam modelos quantitativos.
        """)
    with col_br2:
        st.success("""
        **📈 Crescimento do setor**

        - Investidores pessoa física na B3: de **600 mil** (2018)
          para mais de **5 milhões** (2024)
        - Demanda por profissionais "quant" cresceu mais de
          **300%** na última década
        - FGV, USP e UNICAMP já oferecem cursos
          especializados em métodos quantitativos em finanças
        - O Brasil é o maior mercado de derivativos
          da América Latina
        """)

    st.divider()


def main():
    verificar_acesso()

    st.progress(3 / 6, text="Etapa 3 de 6 — Conceitos de Finanças Quantitativas")
    st.markdown("# 📚 Introdução às Finanças Quantitativas")
    st.markdown(
        "*Aprenda como matemática e dados podem transformar suas decisões financeiras.*"
    )
    st.divider()

    secao_o_que_e()
    secao_quant_vs_tradicional()
    secao_conceitos_fundamentais()
    secao_demo_b3()
    secao_brasil()

    # ── Próximo Passo ─────────────────────────────────────────────
    st.markdown("## ✅ Pronto para o próximo passo?")
    st.markdown(
        "Agora que você conhece os fundamentos, veja como eles se aplicam "
        "em um caso real do mercado financeiro brasileiro!"
    )
    if st.button("Ir para o Estudo de Caso →", type="primary", use_container_width=True):
        st.switch_page("pages/4_Estudo_de_Caso.py")

    st.divider()
    st.caption(
        "Portal FinQuant © 2025 | Trabalho de Conclusão de Curso | Fins Acadêmicos e Educacionais"
    )


main()
