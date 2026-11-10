"""Gráficos Plotly a partir do dict da fachada. Só uso local (o Portal desenha os seus).

Princípios: uma ideia por gráfico, eixos com unidade, datas DD/MM/AAAA, números no formato
brasileiro, mesma cor para a mesma série em todos os gráficos, sem depender só de vermelho e verde.
O título, que diz a conclusão, fica na página, para quebrar bem em telas estreitas.
"""
import numpy as np
import pandas as pd
import plotly.graph_objects as go

from .formatacao import rotulo_ano

# Paleta validada para daltonismo (scripts/validate_palette.js da skill dataviz), nesta ordem.
COR = {"estrategia": "#2563EB", "selic": "#D97706", "buy_hold": "#9D174D", "ibovespa": "#14A085"}
NOME = {"estrategia": "Regra", "selic": "Selic", "buy_hold": "Comprar e segurar", "ibovespa": "Ibovespa"}
FONTE_SERIE = {"selic": "Banco Central", "ibovespa": "B3"}     # dado oficial, como veio da fonte; o resto é calculado pela análise
# Contraste contra o branco: TINTA 13,4:1 e TINTA_SUAVE 5,3:1 (textos); NEVOA 3,4:1 (marcas cinzas, mínimo de 3:1);
# GRADE fica discreta de propósito, porque é só fundo.
TINTA, TINTA_SUAVE, GRADE, NEVOA = "#16323F", "#5B6F7A", "#DCE4E8", "#7A8E99"
EIXO = dict(color=TINTA_SUAVE, size=13)
FONTE = dict(family="'Source Sans', 'Source Sans Pro', system-ui, 'Segoe UI', sans-serif", size=14, color=TINTA)
CONFIG = {"displayModeBar": False, "scrollZoom": False, "responsive": True}
FORMATO_DATA = "%d/%m/%Y"


def _base(fig: go.Figure, altura: int = 380, **kw) -> go.Figure:
    margem = dict(l=62, r=18, t=40, b=48)
    margem.update(kw.pop("margin", {}))
    fig.update_layout(height=altura, font=FONTE, separators=",.", margin=margem, paper_bgcolor="#FFFFFF",
                      plot_bgcolor="#FFFFFF", dragmode=False, hoverlabel=dict(font_size=14, align="left"),
                      legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0, title_text=""),
                      barcornerradius=4, **kw)
    for eixos in (fig.update_xaxes, fig.update_yaxes):
        eixos(gridcolor=GRADE, zeroline=False, fixedrange=True, linecolor=NEVOA, automargin=True, tickfont=EIXO, title_font=EIXO)
    return fig


def _datas(fig: go.Figure, x: list, marcos: list | None = None) -> go.Figure:
    """Eixo de datas DD/MM/AAAA, só até onde há dados. Com `marcos`, as marcas caem exatamente nessas datas."""
    fig.update_xaxes(tickformat=FORMATO_DATA, hoverformat=FORMATO_DATA, nticks=8, showgrid=False, range=[x[0], x[-1]])
    if marcos:
        datas = pd.to_datetime(marcos)
        fig.update_xaxes(tickvals=datas, ticktext=[d.strftime("%d/%m<br>%Y") for d in datas])
    return fig


def _marcos_janelas(res: dict, x: list) -> list:
    """Datas do eixo: o treino inicial em trechos do tamanho de uma janela, o início de cada janela de teste e o fim."""
    per = res["periodo"]
    inicios = list(per.get("inicios_janelas") or [per["inicio_teste"]])
    xs = pd.DatetimeIndex(pd.to_datetime(x))
    i_teste = int(xs.searchsorted(pd.Timestamp(inicios[0])))
    n = max(len(inicios), 1)
    treino = [xs[round(i_teste * k / n)] for k in range(n)] if i_teste > 0 else []
    return [*treino, *inicios, xs[-1]]


def _numerar_janelas(fig: go.Figure, res: dict) -> None:
    """Escreve 1ª, 2ª... no pé de cada janela de teste."""
    for j in res.get("janelas", []):
        meio = pd.Timestamp(j["inicio"]) + (pd.Timestamp(j["fim"]) - pd.Timestamp(j["inicio"])) / 2
        fig.add_annotation(x=meio, y=0, yref="paper", yanchor="bottom", text=f"{j['n']}ª", showarrow=False,
                           font=dict(color=TINTA_SUAVE, size=12), hovertext=f"Janela {j['n']}")


def _xy(pontos):
    return [p["x"] for p in pontos], [p["y"] for p in pontos]


def _br(v, casas=0):
    return f"{v:,.{casas}f}".replace(",", "X").replace(".", ",").replace("X", ".")


def _rotulos_sem_colisao(valores: dict, altura_px: float, minimo_px: float = 18.0) -> dict:
    """Quanto subir ou descer cada rótulo direto, em pixels, para não encostar no vizinho."""
    if not valores:
        return {}
    vmin, vmax = min(valores.values()), max(valores.values())
    escala = altura_px / (vmax - vmin) if vmax > vmin else 0.0
    ordem = sorted(valores, key=valores.get)
    desloc, anterior = {}, None
    for nome in ordem:
        pos = (valores[nome] - vmin) * escala
        final = pos if anterior is None else max(pos, anterior + minimo_px)
        desloc[nome] = final - pos
        anterior = final
    return desloc


# ------------------------------------------------------------------ a regra
def fig_regra(e: dict) -> go.Figure:
    x = e["datas"]
    fig = go.Figure()
    fig.add_scatter(x=x, y=e["preco"], name="Preço de fechamento ajustado", mode="lines", line=dict(color=NEVOA, width=1.5),
                    hovertemplate="Preço: R$ %{y:,.2f}<extra></extra>")
    fig.add_scatter(x=x, y=e["media_curta"], name=f"Média de {e['curta']} dias", mode="lines",
                    line=dict(color=COR["estrategia"], width=2), hovertemplate=f"Média de {e['curta']} dias: R$ %{{y:,.2f}}<extra></extra>")
    fig.add_scatter(x=x, y=e["media_longa"], name=f"Média de {e['longa']} dias", mode="lines",
                    line=dict(color=TINTA, width=2, dash="dash"), hovertemplate=f"Média de {e['longa']} dias: R$ %{{y:,.2f}}<extra></extra>")
    fig.add_scatter(x=[e["data_entrada"]], y=[e["preco_entrada"]], name="Compra", mode="markers",
                    marker=dict(symbol="triangle-up", size=14, color=COR["estrategia"], line=dict(color="#FFF", width=2)),
                    hovertemplate="Compra a R$ %{y:,.2f}<extra></extra>", showlegend=False)
    fig.add_annotation(x=e["data_entrada"], y=e["preco_entrada"], text="Compra", showarrow=True, arrowcolor=TINTA_SUAVE, ax=0, ay=44,
                       bgcolor="rgba(255,255,255,.9)", font=dict(color=TINTA, size=13))
    if e["saida_na_janela"]:
        fig.add_scatter(x=[e["data_saida"]], y=[e["preco_saida"]], name="Venda", mode="markers",
                        marker=dict(symbol="triangle-down", size=14, color=TINTA, line=dict(color="#FFF", width=2)),
                        hovertemplate="Venda a R$ %{y:,.2f}<extra></extra>", showlegend=False)
        fig.add_annotation(x=e["data_saida"], y=e["preco_saida"], text="Venda", showarrow=True, arrowcolor=TINTA_SUAVE, ax=0, ay=-44,
                           bgcolor="rgba(255,255,255,.9)", font=dict(color=TINTA, size=13))
    _base(fig, hovermode="x unified")
    fig.update_yaxes(tickprefix="R$ ", tickformat=",.2f", title_text=None)
    return _datas(fig, x)


def fig_primeira_operacao(x: dict, escolhas: dict) -> go.Figure:
    """A primeira operação do treino: o cruzamento que deu o sinal, a compra, a venda e, com proteção, os limites de perda e de ganho."""
    e = {**x["grafico"], "curta": escolhas["curta"], "longa": escolhas["longa"], "data_entrada": x["data_entrada"], "preco_entrada": x["preco_entrada"],
         "data_saida": x["data_saida"], "preco_saida": x["preco_saida"], "saida_na_janela": True}
    fig = fig_regra(e)
    # O sinal e a compra ficam a um pregão de distância: a etiqueta da compra vai para baixo e para a direita, a do sinal para cima e para a esquerda.
    fig.update_annotations(selector=dict(text="Compra"), ax=36, ay=56)
    fig.add_scatter(x=[x["data_sinal"]], y=[x["curta_sinal"]], name="Sinal", mode="markers", showlegend=False,
                    marker=dict(symbol="circle", size=11, color="#FFFFFF", line=dict(color=COR["estrategia"], width=2.5)),
                    hovertemplate="Sinal: a média curta passou para cima da longa<extra></extra>")
    fig.add_annotation(x=x["data_sinal"], y=x["curta_sinal"], text="Sinal", showarrow=True, arrowcolor=TINTA_SUAVE, ax=-48, ay=-44,
                       bgcolor="rgba(255,255,255,.9)", font=dict(color=TINTA, size=13))
    if escolhas.get("stop") is not None:
        for nome, preco in (("Limite de perda", x["preco_entrada"] * (1 - escolhas["stop"] / 100)),
                            ("Limite de ganho", x["preco_entrada"] * (1 + escolhas["alvo"] / 100))):
            fig.add_shape(type="line", xref="x", yref="y", x0=x["data_entrada"], x1=x["data_saida"], y0=preco, y1=preco,
                          line=dict(color=TINTA_SUAVE, width=1.5, dash="dot"))
            fig.add_annotation(x=x["data_saida"], y=preco, text=f"{nome}: R$ {_br(preco, 2)}", showarrow=False, xanchor="right",
                               yanchor="bottom" if "ganho" in nome else "top", font=dict(color=TINTA_SUAVE, size=12))
    return fig


# ------------------------------------------------------------------ dinheiro
def fig_curvas(res: dict) -> go.Figure:
    curvas, inicio_teste, fim = res["curvas"], res["periodo"]["inicio_teste"], res["periodo"]["fim"]
    fig = go.Figure()
    fig.add_vrect(x0=inicio_teste, x1=fim, fillcolor="#DCE7F3", line_width=0, layer="below")
    fig.add_annotation(x=inicio_teste, xanchor="left", y=1, yref="paper", yanchor="top", text="Janelas de teste",
                       showarrow=False, font=dict(color=TINTA_SUAVE, size=13), xshift=4)
    for d in res["periodo"].get("inicios_janelas", [])[1:]:
        fig.add_shape(type="line", x0=d, x1=d, y0=0, y1=1, yref="paper", layer="below", line=dict(color=TINTA_SUAVE, width=1, dash="dot"))
    ordem = [k for k in ("selic", "ibovespa", "buy_hold", "estrategia") if k in curvas]
    finais = {}
    for k in ordem:
        x, y = _xy(curvas[k])
        legenda = f"{NOME[k]} ({FONTE_SERIE[k]})" if k in FONTE_SERIE else NOME[k]
        fig.add_scatter(x=x, y=y, name=legenda, mode="lines", line=dict(color=COR[k], width=2.5 if k == "estrategia" else 2),
                        hovertemplate=f"{NOME[k]}: R$ %{{y:,.0f}}<extra></extra>")
        finais[k] = y[-1]
    desloc = _rotulos_sem_colisao(finais, 280)
    for k, v in finais.items():
        fig.add_annotation(x=curvas[k][-1]["x"], y=v, text=NOME[k].replace("Comprar e segurar", "Segurar"), showarrow=False,
                           xanchor="left", xshift=6, yshift=desloc[k], font=dict(color=TINTA, size=13), align="left")
    p = res["pior_momento"]["estrategia"]
    fig.add_scatter(x=[p["data_pico"], p["data_fundo"]], y=[p["valor_pico"], p["valor_fundo"]], mode="markers",
                    marker=dict(size=9, color="#FFF", line=dict(color=COR["estrategia"], width=2)),
                    name="Pior queda da regra", hovertemplate="R$ %{y:,.0f}<extra>Pior queda da regra</extra>")
    _numerar_janelas(fig, res)
    _base(fig, altura=420, hovermode="x unified", margin=dict(r=78))
    fig.update_yaxes(tickprefix="R$ ", tickformat=",.0f")
    return _datas(fig, [res["periodo"]["inicio"], fim], _marcos_janelas(res, _xy(curvas["estrategia"])[0]))


def fig_janelas(janelas: list) -> go.Figure:
    """Retorno de cada janela de teste: a regra, a Selic e comprar e segurar lado a lado."""
    rotulos = [f"{j['n']}ª" for j in janelas]
    fig = go.Figure()
    for chave, campo in (("estrategia", "retorno"), ("selic", "selic"), ("buy_hold", "buy_hold")):
        valores = [None if j[campo] is None else 100 * j[campo] for j in janelas]
        if all(v is None for v in valores):
            continue
        fig.add_bar(x=rotulos, y=valores, name=NOME[chave], marker=dict(color=COR[chave]),
                    customdata=[[j["inicio"][8:10] + "/" + j["inicio"][5:7] + "/" + j["inicio"][:4], j["fim"][8:10] + "/" + j["fim"][5:7] + "/" + j["fim"][:4]] for j in janelas],
                    hovertemplate=f"{NOME[chave]}: %{{y:.1f}}%<br>%{{customdata[0]}} a %{{customdata[1]}}<extra>Janela %{{x}}</extra>")
    _base(fig, altura=360, barmode="group", bargap=0.25, bargroupgap=0.05)
    fig.update_xaxes(title_text="Janela de teste", showgrid=False)
    fig.update_yaxes(ticksuffix="%", zeroline=True, zerolinecolor=TINTA_SUAVE, title_text=None)
    return fig


# ------------------------------------------------------------------ seleção automática
def fig_selecao(ranking: list) -> go.Figure:
    itens = sorted((x for x in ranking if x["selecionada"]), key=lambda x: x["sharpe_treino"])
    fig = go.Figure(go.Bar(x=[x["sharpe_treino"] for x in itens], y=[x["ticker"] for x in itens], orientation="h",
                           marker=dict(color=COR["estrategia"]), text=[_br(x["sharpe_treino"], 2) for x in itens],
                           textposition="outside", cliponaxis=False, hovertemplate="%{y}: Sharpe de %{x:.2f} no treino<extra></extra>"))
    _base(fig, altura=max(150, 34 * len(itens) + 50), margin=dict(l=70, r=56, t=10, b=10), showlegend=False, bargap=0.3)
    fig.update_xaxes(visible=False, rangemode="tozero")
    fig.update_yaxes(showgrid=False)
    return fig


# ------------------------------------------------------------------ divisão do dinheiro
def fig_pesos(pesos: dict) -> go.Figure:
    itens = sorted(pesos.items(), key=lambda kv: kv[1])
    fig = go.Figure(go.Bar(x=[100 * v for _, v in itens], y=[k for k, _ in itens], orientation="h",
                           marker=dict(color=COR["estrategia"]), text=[_br(100 * v, 1) + "%" for _, v in itens],
                           textposition="outside", cliponaxis=False, hovertemplate="%{y}: %{x:.1f}%<extra></extra>"))
    _base(fig, altura=max(150, 42 * len(itens) + 50), margin=dict(l=70, r=56, t=10, b=10), showlegend=False, bargap=0.35)
    fig.update_xaxes(visible=False, rangemode="tozero")
    fig.update_yaxes(showgrid=False)
    return fig


def fig_correlacao(corr: dict) -> go.Figure:
    nomes = list(corr)
    z = [[corr[a][b] for b in nomes] for a in nomes]
    texto = [[_br(v, 2) for v in linha] for linha in z]
    fig = go.Figure(go.Heatmap(z=z, x=nomes, y=nomes, zmin=-1, zmax=1, text=texto, texttemplate="%{text}", showscale=False,
                               colorscale=[[0, "#B45309"], [0.5, "#F4F6F7"], [1, "#2563EB"]], xgap=2, ygap=2,
                               hovertemplate="%{y} e %{x}: %{text}<extra></extra>"))
    _base(fig, altura=max(220, 44 * len(nomes) + 70), margin=dict(l=70, t=10, b=40))
    fig.update_yaxes(autorange="reversed", showgrid=False)
    fig.update_xaxes(showgrid=False)
    return fig


SIMBOLO_CARTEIRA = {"Partes iguais": "circle", "Menor oscilação": "square", "Melhor retorno pelo risco": "diamond"}


def fig_fronteira(c: dict) -> go.Figure:
    fig = go.Figure()
    nuvem = c["nuvem"]["pontos"]
    fig.add_scatter(x=[100 * p["risco"] for p in nuvem], y=[100 * p["retorno"] for p in nuvem], mode="markers",
                    marker=dict(size=4, color=NEVOA, opacity=0.5), name="Carteiras sorteadas", hoverinfo="skip")
    if c["fronteira"]:
        fig.add_scatter(x=[100 * p["risco"] for p in c["fronteira"]], y=[100 * p["retorno"] for p in c["fronteira"]],
                        mode="lines", line=dict(color=TINTA, width=2.5), name="Fronteira eficiente",
                        hovertemplate="Risco %{x:.1f}%, retorno %{y:.1f}%<extra>Fronteira eficiente</extra>")
    for k in c["carteiras"]:
        tr = k["treino"]
        esc = k["escolhida"]
        fig.add_scatter(x=[100 * tr["risco"]], y=[100 * tr["retorno"]], mode="markers+text" if esc else "markers", name=k["nome"],
                        text=["Sua carteira"] if esc else None, textposition="top center",
                        marker=dict(size=15 if esc else 11, symbol=SIMBOLO_CARTEIRA.get(k["nome"], "circle"),
                                    color=COR["estrategia"] if esc else "#FFFFFF",
                                    line=dict(color=COR["estrategia"] if esc else TINTA, width=2)),
                        hovertemplate=f"{k['nome']}<br>Risco %{{x:.1f}}%, retorno %{{y:.1f}}%<extra></extra>")
    ib = c.get("ibovespa")
    if ib and ib["treino"]["risco"] == ib["treino"]["risco"]:
        fig.add_scatter(x=[100 * ib["treino"]["risco"]], y=[100 * ib["treino"]["retorno"]], mode="markers+text", name="Ibovespa",
                        text=["Ibovespa"], textposition="bottom center", cliponaxis=False,
                        marker=dict(size=12, symbol="triangle-up", color=COR["ibovespa"], line=dict(color="#FFF", width=2)),
                        hovertemplate="Ibovespa<br>Risco %{x:.1f}%, retorno %{y:.1f}%<extra></extra>")
    _base(fig, altura=470, margin=dict(t=72))
    fig.update_xaxes(title_text="Risco (oscilação ao ano)", ticksuffix="%")
    fig.update_yaxes(title_text="Retorno médio ao ano", ticksuffix="%")
    return fig


def fig_promessa(c: dict) -> go.Figure:
    """Cada carteira tem um símbolo, explicado na legenda: nomes sobre os pontos se sobrepõem em tela estreita."""
    fig = go.Figure()
    for k in c["carteiras"]:
        cor = COR["estrategia"] if k["escolhida"] else TINTA_SUAVE
        simbolo = SIMBOLO_CARTEIRA.get(k["nome"], "circle")
        tr, te = k["treino"], k["teste"]
        fig.add_annotation(x=100 * te["risco"], y=100 * te["retorno"], ax=100 * tr["risco"], ay=100 * tr["retorno"],
                           xref="x", yref="y", axref="x", ayref="y", showarrow=True, arrowhead=3, arrowsize=1.2,
                           arrowwidth=2, arrowcolor=cor, standoff=6, text="")
        fig.add_scatter(x=[100 * tr["risco"]], y=[100 * tr["retorno"]], mode="markers", showlegend=False,
                        marker=dict(size=11, symbol=simbolo, color="#FFF", line=dict(color=cor, width=2)),
                        hovertemplate=f"{k['nome']}: promessa<br>Risco %{{x:.1f}}%, retorno %{{y:.1f}}%<extra></extra>")
        fig.add_scatter(x=[100 * te["risco"]], y=[100 * te["retorno"]], mode="markers", name=k["nome"],
                        marker=dict(size=12, symbol=simbolo, color=cor, line=dict(color="#FFF", width=2)),
                        hovertemplate=f"{k['nome']}: realidade<br>Risco %{{x:.1f}}%, retorno %{{y:.1f}}%<extra></extra>")
    fig.add_scatter(x=[None], y=[None], mode="markers", name="Vazado: promessa (treino)", marker=dict(size=11, color="#FFF", line=dict(color=TINTA_SUAVE, width=2)))
    fig.add_scatter(x=[None], y=[None], mode="markers", name="Cheio: realidade (teste)", marker=dict(size=11, color=TINTA_SUAVE))
    _base(fig, altura=430, margin=dict(t=48))
    fig.update_xaxes(title_text="Risco (oscilação ao ano)", ticksuffix="%")
    fig.update_yaxes(title_text="Retorno médio ao ano", ticksuffix="%")
    return fig


# ------------------------------------------------------------------ distribuições
def fig_histograma(h: dict, eixo: str, cor: str = COR["estrategia"], marcas: list | None = None, altura: int = 300,
                   rotulo_quantidade: str = "Quantidade") -> go.Figure:
    b = np.array(h["bordas"], dtype=float)
    meio, largura = (b[:-1] + b[1:]) / 2, b[1:] - b[:-1]
    fig = go.Figure(go.Bar(x=meio, y=h["contagens"], width=largura * 0.92, marker=dict(color=cor), showlegend=False,
                           customdata=np.stack([b[:-1], b[1:]], axis=1),
                           hovertemplate="De %{customdata[0]:.2f}% a %{customdata[1]:.2f}%: %{y}<extra></extra>"))
    marcas = marcas or []
    for i, (valor, rotulo) in enumerate(marcas):
        fig.add_shape(type="line", x0=valor, x1=valor, y0=0, y1=1, yref="paper", line=dict(color=TINTA, width=2))
        fig.add_annotation(x=valor, y=1, yref="paper", yanchor="bottom", text=rotulo, showarrow=False, yshift=2 + 20 * i,
                           font=dict(color=TINTA, size=13))
    _base(fig, altura=altura, margin=dict(t=20 + 22 * len(marcas)), bargap=0)
    fig.update_xaxes(title_text=eixo, ticksuffix="%", showgrid=False)
    fig.update_yaxes(title_text=rotulo_quantidade)
    return fig


# ------------------------------------------------------------------ foi sorte?
def fig_intervalo(sorte: dict) -> go.Figure:
    fig = go.Figure()
    fig.add_shape(type="line", x0=0, x1=0, y0=0, y1=1, yref="paper", line=dict(color=TINTA, width=2))
    fig.add_annotation(x=0, y=1, yref="paper", yanchor="bottom", text="Igual à Selic", showarrow=False, font=dict(color=TINTA, size=13))
    linhas = [("Regra", "ic_estrategia", "estrategia"), ("Comprar e segurar", "ic_buy_hold", "buy_hold")]
    extremos = [0.0]
    for nome, chave, serie in reversed(linhas):
        ic = sorte.get(chave)
        if not ic or ic.get("baixo_anual") is None:
            continue
        v = [100 * ic["baixo_anual"], 100 * ic["media_anual"], 100 * ic["alto_anual"]]
        extremos += [v[0], v[2]]
        fig.add_scatter(x=v, y=[nome] * 3, mode="lines+markers+text", line=dict(color=COR[serie], width=5), cliponaxis=False,
                        marker=dict(size=[1, 13, 1], color=COR[serie], line=dict(color="#FFF", width=2)),
                        text=[f"{v[0]:+.1f}".replace(".", ","), f"{v[1]:+.1f}".replace(".", ","), f"{v[2]:+.1f}".replace(".", ",")],
                        textposition="top center", showlegend=False, hovertemplate=f"{nome}: %{{x:+.1f}} pontos ao ano<extra></extra>")
    _base(fig, altura=230, margin=dict(l=140, t=34))
    folga = 0.15 * (max(extremos) - min(extremos))          # espaço para os rótulos das pontas em tela estreita
    fig.update_xaxes(title_text="Pontos ao ano acima da Selic", zeroline=False, range=[min(extremos) - folga, max(extremos) + folga])
    fig.update_yaxes(showgrid=False, range=[-0.6, 1.8])
    return fig


# ------------------------------------------------------------------ aguenta variações?
def fig_ano_a_ano(anos: list, inicio=None, fim=None) -> go.Figure:
    fig = go.Figure()
    rotulos = [rotulo_ano(a["ano"], inicio, fim, quebra="<br>") if inicio and fim else str(a["ano"]) for a in anos]
    for k in ("estrategia", "selic", "buy_hold"):
        if k in anos[0]:
            fig.add_bar(x=rotulos, y=[100 * a[k] for a in anos], name=NOME[k], marker=dict(color=COR[k]),
                        hovertemplate=f"{NOME[k]}: %{{y:.1f}}%<extra></extra>")
    fig.add_hline(y=0, line=dict(color=TINTA, width=1))
    _base(fig, altura=360, barmode="group", bargap=0.25, bargroupgap=0.08, hovermode="x unified")
    fig.update_yaxes(ticksuffix="%")
    fig.update_xaxes(showgrid=False, type="category")
    return fig


def fig_sensibilidade(combinacoes: list, medias: dict, protecoes: dict, selic_teste, curta: int, longa: int, protecao: str) -> go.Figure:
    fig = go.Figure()
    simbolos = dict(zip(protecoes, ("circle", "square", "diamond", "triangle-up")))
    nomes_y = {k: f"{m['curta']} e {m['longa']} dias" for k, m in medias.items()}
    for chave, p in protecoes.items():
        linhas = [ln for ln in combinacoes if ln["protecao"] == chave]
        fig.add_scatter(x=[100 * ln["retorno_teste"] for ln in linhas], y=[nomes_y[ln["medias"]] for ln in linhas], mode="markers",
                        name=p["rotulo"],
                        marker=dict(symbol=simbolos[chave], size=11, color="#FFFFFF", line=dict(color=TINTA, width=2)),
                        hovertemplate="%{y}<br>" + p["rotulo"] + ": %{x:.1f}%<extra></extra>")
    # a combinação escolhida vem por cima, em traço próprio: assim a legenda não herda o azul dela
    for ln in combinacoes:
        if ln["curta"] == curta and ln["longa"] == longa and ln["protecao"] == protecao:
            fig.add_scatter(x=[100 * ln["retorno_teste"]], y=[nomes_y[ln["medias"]]], mode="markers", showlegend=False,
                            marker=dict(symbol=simbolos[protecao], size=16, color=COR["estrategia"], line=dict(color=COR["estrategia"], width=2)),
                            hovertemplate="%{y}<br>Sua escolha: %{x:.1f}%<extra></extra>")
    if selic_teste is not None:
        v = 100 * selic_teste
        fig.add_shape(type="line", x0=v, x1=v, y0=0, y1=1, yref="paper", line=dict(color=COR["selic"], width=2, dash="dash"))
        fig.add_annotation(x=v, y=0.99, yref="paper", yanchor="top", xanchor="right", xshift=-5, text="Selic", showarrow=False, font=dict(color=TINTA, size=13))
        fig.add_scatter(x=[v], y=[nomes_y[next(iter(medias))]], mode="markers", marker=dict(opacity=0), showlegend=False, hoverinfo="skip")
    _base(fig, altura=400, margin=dict(l=120, t=60, b=60))
    fig.update_xaxes(title_text="Retorno no período de teste", ticksuffix="%", title_standoff=26)
    fig.update_yaxes(showgrid=False, categoryorder="array", categoryarray=list(reversed(list(nomes_y.values()))))
    return fig
