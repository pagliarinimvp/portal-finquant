"""As telas da análise, portadas de `app_streamlit.py` (pasta Script Analise Quantitativa, versão Streamlit de referência).

Cada função `tela_*` e cada auxiliar (`tabela`, `numeros`, `entenda`, `grafico`...) é a mesma do app Streamlit, na mesma
ordem e com os mesmos textos. A diferença está no objeto `st`: aqui ele é um `_Pagina`, que imita as poucas chamadas do
Streamlit usadas pelas telas (`markdown`, `expander`, `container`, `plotly_chart`) e escreve HTML em vez de desenhar.
`um_por_vez` vira abas, e os botões viram links. A navegação entre telas e o formulário ficam nos templates.

Para mudar um texto, edite `apresentacao/textos.py` ou `quant/leitura.py`, como antes.
"""
import re
import threading
from collections.abc import Callable, Sequence
from contextlib import contextmanager
from html import escape

import numpy as np

from .apresentacao import graficos_plotly as g
from .apresentacao import textos as tx
from .apresentacao.formatacao import brl, data_br, nota_salto, num, p_valor, pct, pontos
from .quant import carteira as cart
from .quant import config as c
from .quant import dados as d
from .quant.glossario import GLOSSARIO
from .quant.referencias import REFERENCIAS
from .quant.universo import DATA_CARTEIRA


# ----------------------------------------------------------------------------- o "st" do portal
_LINK = re.compile(r"\[([^\]]+)\]\((https?://\S+?)\)(?=[;,.*\s]|$)")


def _md(texto: str) -> str:
    """O markdown que as telas usam: `código`, **negrito**, *itálico*, [link](url) e quebra de linha com dois espaços."""
    links: list[str] = []

    def guardar(m):        # os links saem antes, porque as URLs têm parênteses, sublinhados e asteriscos
        links.append(f'<a href="{escape(m.group(2))}" target="_blank" rel="noopener">{escape(m.group(1), quote=False)}</a>')
        return f"\x00{len(links) - 1}\x00"

    t = _LINK.sub(guardar, texto)
    t = escape(t, quote=False)
    t = re.sub(r"`([^`]+)`", r"<code>\1</code>", t)
    t = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", t, flags=re.S)
    t = re.sub(r"(?<![\w*])\*(?=\S)(.+?)(?<=\S)\*(?![\w*])", r"<i>\1</i>", t, flags=re.S)
    t = re.sub(r"\x00(\d+)\x00", lambda m: links[int(m.group(1))], t)
    paragrafos = [p.replace("  \n", "<br>") for p in t.split("\n\n") if p.strip()]
    return "".join(f"<p>{p}</p>" for p in paragrafos)


class _Pagina:
    """Junta o HTML de uma tela. Cada requisição monta a sua, numa área própria da thread."""

    def __init__(self):
        self._local = threading.local()

    def comecar(self, urls: dict):
        self._local.partes, self._local.ids, self._local.urls = [], {}, urls

    def terminar(self) -> str:
        return "".join(self._local.partes)

    def _escrever(self, texto: str):
        self._local.partes.append(texto)

    def url(self, nome: str) -> str:
        return escape(self._local.urls[nome])

    def novo_id(self, base: str) -> str:
        n = self._local.ids.get(base, 0)
        self._local.ids[base] = n + 1
        return f"{base}-{n}".replace("_", "-")

    def markdown(self, texto: str, unsafe_allow_html: bool = False):
        self._escrever(texto if unsafe_allow_html else _md(texto))

    @contextmanager
    def expander(self, rotulo: str):
        self._escrever(f'<details class="entenda"><summary>{escape(rotulo)}</summary><div class="entenda-corpo">')
        yield
        self._escrever("</div></details>")

    @contextmanager
    def container(self, key: str):
        self._escrever(f'<div class="caixa caixa-{key.replace("_", "-")}">')
        yield
        self._escrever("</div>")

    def plotly_chart(self, figura, key: str, **_):
        """O gráfico vai como JSON; o estudo_caso.js desenha com o plotly.js quando ele fica visível."""
        alvo = self.novo_id(key)
        dados = figura.to_json().replace("</", "<\\/")
        self._escrever(f'<div class="grafico-plotly" id="{alvo}"></div>'
                       f'<script type="application/json" class="figura-plotly" data-alvo="{alvo}">{dados}</script>')


st = _Pagina()


# ----------------------------------------------------------------------------- daqui em diante, como no app Streamlit
SELO = {"passou": "✓ Passou", "nao_passou": "✕ Não passou", "nao_se_aplica": "– Não se aplica"}
MARCA = {"passou": "✓", "nao_passou": "✕", "nao_se_aplica": "–"}


# ----------------------------------------------------------------------------- blocos de texto
def html(texto: str):
    st.markdown(texto, unsafe_allow_html=True)


def selo(status: str) -> str:
    return f'<span class="selo {status}">{SELO[status]}</span>'


def sub(texto: str):
    html(f'<h3 class="sub">{escape(texto)}</h3>')


def significado(texto: str):
    html(f'<div class="significado"><b>O que isso significa</b>{escape(texto)}</div>')


def nota(texto: str):
    html(f'<div class="nota">{texto}</div>')


def alerta(texto: str):
    html(f'<div class="alerta">{texto}</div>')


def como_ler(chave: str) -> str:
    """O referencial de uma medida. Fica no glossário, para ser o mesmo em toda a página."""
    return GLOSSARIO[chave]["como_ler"]


def leitura_de(texto: str):
    """Uma linha "Como ler" logo depois de um número ou de uma tabela."""
    html(f'<p class="leitura-grafico"><b>Como ler:</b> {escape(texto)}</p>')


def numeros(itens: list[tuple]):
    """Cada item: (valor, o que é) ou (valor, o que é, referencial para ler o valor)."""
    def item(v, r, ref=None):
        return f'<div><div class="v">{escape(v)}</div><div class="r">{escape(r)}</div>' + (f'<div class="ref">{escape(ref)}</div>' if ref else "") + "</div>"
    html('<div class="numeros">' + "".join(item(*x) for x in itens) + "</div>")


def _celula(x, cor: str | None = None) -> str:
    """Uma célula. A tupla (nome, ajuda) mostra o referencial logo abaixo do nome da medida. `cor`: "melhor" ou "pior" na comparação."""
    marca = f' class="{cor}" title="{"A melhor" if cor == "melhor" else "A pior"} desta comparação"' if cor else ""
    if isinstance(x, tuple):
        return f'<td class="com-ajuda">{escape(x[0])}<span class="ajuda">{escape(x[1])}</span></td>'
    if isinstance(x, list):                         # uma linha por item, na mesma célula
        return f"<td{marca}>" + "<br>".join(escape(str(v)) for v in x) + "</td>"
    return f"<td{marca}>{escape(str(x))}</td>"


def melhor_e_pior(valores: list, maior_melhor: bool = True, casas: int = 3) -> list[str | None]:
    """Marca a melhor e a pior entre alternativas comparáveis. Sem valor, ou com todos iguais, nada é marcado.
    A comparação usa o número como aparece na tela (`casas`: 3 para percentuais com uma casa, 2 para o Sharpe):
    duas alternativas que mostram o mesmo valor recebem a mesma marca."""
    valores = [None if v is None or not np.isfinite(v) else round(float(v), casas) for v in valores]
    validos = [v for v in valores if v is not None]
    if len(validos) < 2 or max(validos) == min(validos):
        return [None] * len(valores)
    melhor, pior = (max(validos), min(validos)) if maior_melhor else (min(validos), max(validos))
    return [None if v is None else "melhor" if v == melhor else "pior" if v == pior else None for v in valores]


def por_coluna(colunas: list[list[str | None]]) -> list[list[str | None]]:
    """Transpõe marcas calculadas coluna a coluna (alternativas nas linhas) para o formato linha a linha da tabela."""
    return [list(x) for x in zip(*colunas)]


N_PASSOS_REGRA = 3      # médias, comprar e vender ficam à vista; custo, imposto, espera e encerramento ficam nos detalhes
LEGENDA_CORES = "Verde com ✓: a melhor alternativa daquela comparação. Vermelho: a pior. Sem cor: no meio, ou sem valor para comparar."


def passos(itens: list[dict]):
    html('<ol class="passos">' + "".join(f"<li><b>{escape(x['titulo'])}.</b> {escape(x['texto'])}</li>" for x in itens) + "</ol>")


def tabela(cabecalho: list[str], linhas: list[list[str]], destaque: int | None = None, texto: bool = False, classe: str = "",
           cores: list[list[str | None]] | None = None):
    """`texto=True`: colunas com frases, alinhadas à esquerda e com quebra de linha. `classe`: estilo extra da tabela.
    `cores`: para cada linha, a marca de cada célula de valor ("melhor", "pior" ou None), a partir da 2ª coluna."""
    th = "".join(f"<th>{escape(x)}</th>" for x in cabecalho)
    if cores:
        destaque = None     # com verde e vermelho, um terceiro destaque na linha confundiria a leitura

    def cor(i, j):
        return cores[i][j - 1] if cores and j >= 1 and j - 1 < len(cores[i]) else None
    trs = "".join(f'<tr{" class=destaque" if i == destaque else ""}>' + "".join(_celula(x, cor(i, j)) for j, x in enumerate(ln)) + "</tr>"
                  for i, ln in enumerate(linhas))
    html(f'<div class="tabela{" texto" if texto else ""}{" " + classe if classe else ""}"><table><thead><tr>{th}</tr></thead><tbody>{trs}</tbody></table></div>')


def tabela_grupos(cabecalho: list[str], grupos: list[tuple[str, list[list[str]]]]):
    """Tabela com linhas agrupadas sob um subtítulo."""
    th = "".join(f"<th>{escape(x)}</th>" for x in cabecalho)
    corpo = ""
    for grupo, linhas in grupos:
        corpo += f'<tr class="grupo"><td colspan="{len(cabecalho)}">{escape(grupo)}</td></tr>'
        corpo += "".join("<tr>" + "".join(_celula(x) for x in ln) + "</tr>" for ln in linhas)
    html(f'<div class="tabela"><table><thead><tr>{th}</tr></thead><tbody>{corpo}</tbody></table></div>')


def lista(itens: list[str]):
    html('<ul class="lista">' + "".join(f"<li>{i}</li>" for i in itens) + "</ul>")


def fontes(ids: list[str]):
    """Lista de referências com link. Um id desconhecido quebra de propósito: toda fonte precisa estar conferida."""
    if ids:
        itens = "".join(f'<li>{escape(REFERENCIAS[i]["citacao"])} <a href="{REFERENCIAS[i]["url"]}" target="_blank" rel="noopener">Abrir</a></li>' for i in ids)
        html(f'<div class="fontes"><b>Fontes</b><ul>{itens}</ul></div>')


def entenda(*paragrafos: str, ids: list[str] | None = None, listas: list[str] | None = None):
    with st.expander("Entenda melhor"):
        for p in paragrafos:
            html(f"<p>{p}</p>")
        if listas:
            lista(listas)
        fontes(ids or [])


def grafico(descricao_id: str, titulo: str | None, figura, depois=None):
    """Cartão de gráfico: título com a conclusão, o que mostra, por que está aqui, o gráfico e o que vier depois."""
    mostra, porque = tx.GRAFICOS[descricao_id]
    with st.container(key=f"bloco_{descricao_id}"):
        if titulo:
            html(f'<div class="titulo-grafico">{escape(titulo)}</div>')
        html(f'<p class="leitura-grafico"><b>O que mostra:</b> {escape(mostra)}<br><b>Por que está aqui:</b> {escape(porque)}</p>')
        st.plotly_chart(figura, config=g.CONFIG, width="stretch", theme=None, key=f"grafico_{descricao_id}")
        if depois:
            depois()


def abrir_teste(res: dict, id_: str):
    t = res["leitura"]["testes"][id_]
    html(f'<h3 class="sub">{escape(t["pergunta"])}</h3><p>{selo(t["status"])} &nbsp;<b>{escape(t["nome"])}.</b></p>')


def fechar_teste(res: dict, id_: str, extra: str | None = None, figura=None):
    significado(res["leitura"]["testes"][id_]["significado"])
    formula, ids = tx.CONTA[id_]
    entenda(tx.IDEIA[id_])
    with st.expander("Para quem quer ver a conta"):
        st.markdown(formula)
        if extra:
            st.markdown(extra)
        if figura is not None:
            figura()
        fontes(ids)


def um_por_vez(chave: str, itens: Sequence[tuple[str, Callable[[], object]]]):
    """Mostra um item de cada vez, escolhido em um seletor. O primeiro vem aberto."""
    # No portal, todos os itens vão na página e as abas trocam qual aparece, sem recarregar (estudo_caso.js).
    grupo = st.novo_id(chave)
    abas = "".join(f'<button type="button" class="aba" role="tab" id="{grupo}-aba{k}" aria-controls="{grupo}-{k}" '
                   f'aria-selected="{"true" if k == 0 else "false"}">{escape(rotulo)}</button>' for k, (rotulo, _) in enumerate(itens))
    html(f'<div class="um-por-vez"><div class="abas" role="tablist">{abas}</div>')
    for k, (_, mostrar) in enumerate(itens):
        html(f'<div class="painel" role="tabpanel" id="{grupo}-{k}" aria-labelledby="{grupo}-aba{k}"{"" if k == 0 else " hidden"}>')
        mostrar()
        html("</div>")
    html("</div>")


def rotulo_teste(res: dict, id_: str) -> str:
    t = res["leitura"]["testes"][id_]
    return f'{MARCA[t["status"]]} {t["nome"]}'


# ----------------------------------------------------------------------------- 2. preparar
def tela_preparar(res: dict):
    per = res["periodo"]
    numeros([(num(per["n_pregoes"], 0), "pregões analisados"), (data_br(per["inicio"]), "primeiro dia"), (data_br(per["fim"]), "último dia")])
    s = res["selecao"]
    if s:
        html(f'<p><b>Ações consideradas:</b> as {s["n_universo"]} da carteira do Ibovespa de {DATA_CARTEIRA}. {s["n_candidatas"]} têm histórico completo e confiável para a seleção.</p>')
    else:
        html(f'<p><b>Ações analisadas:</b> {escape(", ".join(res["tickers"]))}, da carteira do Ibovespa de {DATA_CARTEIRA}.</p>')

    def origem():
        html(f"<p>{tx.DADOS}</p>")
        fontes(["yahoo", "bcb_selic", "b3_ibov"])

    um_por_vez("item_dados", [("De onde vêm os dados", origem), ("Por que 10 anos", lambda: html(f"<p>{tx.POR_QUE_10_ANOS}</p>"))])


# ----------------------------------------------------------------------------- 3. processar
def tela_processar(res: dict):
    tratamentos = [t.format(min_pregoes=c.MIN_PREGOES, buraco=d.MAX_BURACO_DIAS, sem_volume=round(100 * d.MAX_FRACAO_SEM_VOLUME),
                            salto=round(100 * d.SALTO_SUSPEITO)) for t in tx.TRATAMENTOS]
    if res["selecao"]:
        tratamentos.append(tx.TRATAMENTO_AUTO)
    lista(tratamentos)


def tela_treino_teste(res: dict):
    """Só a explicação da divisão. Os resultados de cada janela ficam no passo 4, depois da tela do Sharpe."""
    per, dec, rot = res["periodo"], res["decisoes_treino"], res["roteiro_treino"]
    html(f'<div class="nota">{tx.TT_NAO_E_MAQUINA}</div>')
    janelas = "".join(f'<div class="te" title="Janela {j["n"]}: {data_br(j["inicio"])} a {data_br(j["fim"])}">{j["n"]}ª</div>' for j in res["janelas"])
    html(f'<div class="faixa" role="img" aria-label="Treino inicial na primeira metade e {per["n_janelas"]} janelas de teste na segunda">'
         f'<div class="tr">Treino inicial</div>{janelas}</div>'
         f'<div class="datas-faixa"><div>{data_br(per["inicio"])} a {data_br(per["fim_treino"])}<br>{num(per["n_treino"], 0)} pregões, cerca de {num(per["anos"] - per["anos_teste"], 1)} anos</div>'
         f'<div>{per["n_janelas"]} janelas de teste, de {data_br(per["inicio_teste"])} a {data_br(per["fim"])}<br>{num(per["n_teste"], 0)} pregões, cerca de {num(per["anos_teste"], 1)} anos</div></div>')

    def partes():
        tabela(["", "Treino", "Teste, em janelas"], tx.TT_TABELA, texto=True)
        html(f"<p>{tx.TT_POR_QUE_JANELAS}</p>")
        html(f"<p>{tx.TT_SEPARACAO}</p>")
        entenda(tx.DIVISAO_HISTORICO, tx.TT_NAO_INTERCALAR, ids=["bailey2014", "tashman2000"])

    def decidiu():
        html(f"<p>{escape(dec['frase'])}</p>")
        tabela(["Escolha", "Quem definiu", "Resultado"], [[x["escolha"], x["quem"], x["resultado"]] for x in dec["itens"]], texto=True)
        with st.expander("O passo a passo do treino nesta análise"):
            passos(rot["passos"])
            nota(escape(rot["nao_decide"]))

    def usos():
        sub("O que usa cada período")
        lista(tx.TT_USOS)
        sub("Os limites dessa separação")
        lista(tx.TT_LIMITES)

    um_por_vez("item_treino", [("As duas partes", partes), ("O que o treino decidiu", decidiu), ("Usos e limites", usos)])
    html('<p class="leitura-grafico">A regra de compra e venda, com um exemplo real, está no passo 4, em “A regra em ação”. '
         'O resultado de cada janela vem depois, em “As janelas de teste”.</p>')


def tela_janelas(res: dict):
    """O que foi escolhido antes de cada janela e o que cada uma entregou. Vem depois da tela do Sharpe, que explica a medida."""
    js = res["janelas"]
    com_selic = [j for j in js if j["bateu_selic"] is not None]
    titulo = f"A regra rendeu mais que a Selic em {sum(j['bateu_selic'] for j in com_selic)} de {len(com_selic)} janelas de teste" if com_selic else None

    def acoes(j):
        if j["caixa"]:
            return "Dinheiro parado: nenhuma ação passou na seleção"
        return ", ".join(f"{t} {pct(w, 0)}" for t, w in j["pesos"].items()) if len(j["pesos"]) > 1 else ", ".join(j["pesos"])

    def escolhido():
        tabela(["Janela", "Período", "Ações e pesos", "Ritmo"],
               [[f"{j['n']}ª" + (" (mudou)" if j["mudou"] else ""), f"{data_br(j['inicio'])} a {data_br(j['fim'])}", acoes(j), j["rotulo_ritmo"] or "—"] for j in js], texto=True)
        leitura_de("O treino de cada janela vai do início do histórico até o pregão anterior a ela.")

    def entregou():
        tabela(["Janela", "Sharpe no treino", "Sharpe na janela", "Regra", "Selic", "Comprar e segurar"],
               [[f"{j['n']}ª", num(j["sharpe_treino"]), num(j["sharpe_teste"]), pct(j["retorno"]), pct(j["selic"]), pct(j["buy_hold"])] for j in js],
               cores=[[None, None, *melhor_e_pior([j["retorno"], j["selic"], j["buy_hold"]])] for j in js])
        html('<p class="leitura-grafico"><b>Como ler:</b></p>')
        lista(tx.TT_JANELAS_LER)
        fontes(["tashman2000"])

    um_por_vez("item_janelas", [("Janela a janela", lambda: grafico("janelas", titulo, g.fig_janelas(js))),
                                ("O que foi escolhido", escolhido), ("Prometido e entregue", entregou)])


# ----------------------------------------------------------------------------- 4. analisar
def tela_selecao(res: dict):
    s, te = res["selecao"], res["desempenho"]["teste"]
    alerta(tx.ALERTA_SELECAO)
    numeros([(str(s["n_universo"]), "ações no Ibovespa"), (str(s["n_candidatas"]), "com dados completos e confiáveis"), (str(len(res["tickers"])), "selecionadas")])

    def notas():
        grafico("selecao", "A melhor no treino: as ações selecionadas e suas notas", g.fig_selecao(s["ranking"]))
        nota(tx.SELECAO_NOTA)

    def ajudou():
        _selecao_ajudou(s, te)

    def cada_acao():
        j1 = res["janelas"][0]
        if j1["selic"] is not None:
            leitura_de(f"Compare o retorno de cada ação na 1ª janela com a Selic, que rendeu {pct(j1['selic'])} no mesmo período.")
        tabela(["Ação", "Sharpe no treino inicial", "Operações no treino inicial", "Retorno da regra na 1ª janela"],
               [[x["ticker"], num(x["sharpe_treino"]), str(x["n_trades"]), pct(x["retorno_teste"])] for x in s["ranking"] if x["selecionada"]])
        sub("As ações escolhidas antes de cada janela")
        tabela(["Janela", "Treino até", "Ações"],
               [[f"{j['n']}ª", data_br(j["fim_treino"]), ", ".join(j["acoes"]) or "Nenhuma: dinheiro parado"] for j in res["janelas"]], texto=True)
        leitura_de("A seleção é refeita antes de cada janela, só com os dados anteriores a ela. Por isso as ações podem mudar de uma janela para outra.")

    def como():
        html(f"<p>{tx.SELECAO_COMPARA}</p>")
        if s["fora"]:
            html("<p><b>Ações que ficaram de fora:</b></p>")
            lista([f'{escape(x["ticker"])}: {escape(x["motivo"])}.' for x in s["fora"]])
        fontes(["bailey2014", "harvey2015", "brown1992", "b3_ibov"])

    um_por_vez("item_selecao", [("As notas no treino", notas), ("A seleção ajudou?", ajudou), ("Ação por ação", cada_acao), ("Como comparar", como)])


def _selecao_ajudou(s: dict, te: dict):
    alternativas = [("Regra na carteira selecionada", te["estrategia"]), ("Comprar e segurar a carteira selecionada", te["buy_hold"]),
                    ("Comprar e segurar partes iguais de todas as candidatas", s["candidatas_iguais"])]
    if "selic" in te:
        alternativas.append(("Selic", {**te["selic"], "sharpe": None}))   # o Sharpe da Selic não tem sentido: ela é a própria referência
    if "ibovespa" in te:
        alternativas.append(("Ibovespa", te["ibovespa"]))
    linhas = [[nome, pct(x["retorno_total"]), "—" if x["sharpe"] is None else num(x["sharpe"]), pct(x["max_drawdown"])] for nome, x in alternativas]
    cores = por_coluna([melhor_e_pior([x[m] for _, x in alternativas], casas=2 if m == "sharpe" else 3) for m in ("retorno_total", "sharpe", "max_drawdown")])
    tabela(["Nas janelas de teste", "Retorno total", "Sharpe", "Queda máxima"], linhas, 0, cores=cores)
    leitura_de(f"Sharpe: {como_ler('sharpe')} Queda máxima: {como_ler('drawdown')} " + LEGENDA_CORES + " Cada coluna é uma comparação.")


def tela_regra(res: dict):
    esc, rot = res["escolhas"], res["roteiro_treino"]
    html(f"<p>{tx.TT_REGRA}</p>")

    def regra():
        passos(rot["regra"][:N_PASSOS_REGRA])
        with st.expander(tx.DETALHES_SIMULACAO):
            passos(rot["regra"][N_PASSOS_REGRA:])

    def exemplo():
        x = res["primeira_operacao_treino"]
        if x and x.get("grafico") and rot["exemplo"]:
            ganho = "ganho" if x["retorno_pct"] > 0 else "perda"
            grafico("primeira_operacao", f"Um exemplo real: a primeira operação, em {x['ticker']}, comprada em {data_br(x['data_entrada'])} e vendida em "
                    f"{data_br(x['data_saida'])}, com {ganho} de {num(abs(x['retorno_pct']), 1)}%", g.fig_primeira_operacao(x, esc),
                    lambda: html(f"<p>{escape(rot['exemplo'])}</p>"))
        else:
            nota("A regra não chegou a operar nesta combinação, então não há exemplo para mostrar.")

    def trapaca():
        html(f"<p>{tx.REGRA}</p>")
        sub(tx.SEM_TRAPACA_TITULO)
        lista(tx.SEM_TRAPACA)
        fontes(["brock1992"])

    itens = [("A regra, passo a passo", regra), ("Um exemplo real", exemplo)]
    if esc["medias_pelo_treino"]:
        itens.append(("O ritmo escolhido", lambda: _ritmo_pelo_treino(res, esc)))
    um_por_vez("item_regra", itens + [("Sem olhar o futuro", trapaca)])


def _ritmo_pelo_treino(res: dict, esc: dict):
    if res["selecao"]:
        html("<p>Você deixou o treino escolher. Antes de cada janela de teste, vence o ritmo com a maior média de Sharpe entre as 10 melhores ações, "
             "só com os dados anteriores à janela. Nenhuma janela participou da própria escolha.</p>")
    else:
        html("<p>Você deixou o treino escolher. Antes de cada janela de teste, testamos os 4 ritmos só com os dados anteriores a ela e ficamos com o "
             "maior índice de Sharpe. Nenhuma janela participou da própria escolha.</p>")
    ritmos = esc["comparacao_ritmos"]
    tabela(["Ritmo", "Sharpe no treino inicial"], [[f"{ln['curta']} e {ln['longa']} dias", num(ln["sharpe_treino"])] for ln in ritmos],
           cores=[[x] for x in melhor_e_pior([ln["sharpe_treino"] for ln in ritmos], casas=2)])
    leitura_de("Esta é a comparação feita para a 1ª janela. Zero significa render igual à Selic. Entre os ritmos, vence o maior: "
               "o verde com ✓ é o ritmo escolhido, e o vermelho, o pior.")
    if esc["ritmo_muda"]:
        nota("O ritmo mudou entre as janelas: " + "; ".join(f"{j['n']}ª janela, {escape(j['rotulo_ritmo'])}" for j in res["janelas"] if j["rotulo_ritmo"]) + ".")


def tela_carteira(res: dict):
    k = res["carteira"]
    escolhida = next(x for x in k["carteiras"] if x["escolhida"])
    tr = escolhida["treino"]

    def pesos():
        grafico("pesos", f"Com a divisão “{escolhida['nome']}”, o dinheiro ficou assim na 1ª janela", g.fig_pesos(res["pesos"]))
        js = res["janelas"]
        if len({tuple(sorted(j["pesos"].items())) for j in js}) > 1:
            sub("Os pesos em cada janela de teste")
            todas = sorted({t for j in js for t in j["pesos"]} | set(res["pesos"]))
            tabela(["Ação", *[f"{j['n']}ª" for j in js]], [[t, *[pct(j["pesos"].get(t, 0.0), 0) for j in js]] for t in todas])
            leitura_de("Cada coluna é a divisão calculada antes daquela janela, só com os dados anteriores a ela. Quando os pesos mudam, a carteira é refeita no fim da janela anterior, pagando o custo.")
        entenda(tx.CARTEIRA, tx.LIMITE_ACOES, ids=["markowitz1952", "demiguel2009", "statman1987"])

    def correlacao():
        corr = k["correlacao"]
        nomes = list(corr)
        pares = [(corr[a][b], a, b) for i, a in enumerate(nomes) for b in nomes[i + 1:]]
        maior, menor = max(pares), min(pares)
        grafico("correlacao", f"O par mais ligado é {maior[1]} e {maior[2]} ({num(maior[0])}); o menos ligado é {menor[1]} e {menor[2]} ({num(menor[0])})", g.fig_correlacao(corr),
                lambda: leitura_de(como_ler("correlacao")))
        entenda(tx.CORRELACAO, ids=["markowitz1952"])

    def fronteira():
        nota(tx.FRONTEIRA_NOTA)
        titulo = None
        if k["fronteira"]:
            riscos, rets = [q["risco"] for q in k["fronteira"]], [q["retorno"] for q in k["fronteira"]]
            distancia = float(np.interp(tr["risco"], riscos, rets)) - tr["retorno"]
            titulo = (f"No treino inicial, a carteira escolhida ficou {num(100 * distancia, 1)} pontos percentuais ao ano abaixo da fronteira: havia divisão com mais retorno pelo mesmo risco"
                      if distancia > 0.005 else "No treino inicial, a carteira escolhida ficou sobre a fronteira eficiente")
        ib = k.get("ibovespa")

        def depois():
            for x in k["carteiras"]:
                acao, peso = max(x["pesos"].items(), key=lambda p: p[1])
                if peso > cart.LIMITE_CONCENTRACAO:
                    html(f"<p>{tx.FRONTEIRA_CONCENTRADA.format(nome=escape(x['nome']), peso=pct(peso, 0), acao=acao, risco=pct(x['treino']['risco']), retorno=pct(x['treino']['retorno']))}</p>")
            if ib:
                html(f"<p>O Ibovespa aparece como comparação: no treino inicial, oscilou {pct(ib['treino']['risco'])} ao ano e rendeu em média {pct(ib['treino']['retorno'])} ao ano. "
                     "Ele não é uma divisão entre estas ações, por isso pode ficar fora da nuvem.</p>")
        grafico("fronteira", titulo, g.fig_fronteira(k), depois)
        entenda(tx.FRONTEIRA, ids=["markowitz1952", "demiguel2009"])

    def promessa():
        grafico("promessa", f"A carteira escolhida prometia {pct(tr['retorno'])} ao ano no treino inicial e entregou {pct(escolhida['teste']['retorno'])} ao ano nas janelas de teste", g.fig_promessa(k))
        i = next(j for j, x in enumerate(k["carteiras"]) if x["escolhida"])
        cs = k["carteiras"]
        cores = por_coluna([melhor_e_pior([x["teste"][m] for x in cs], m != "risco", 2 if m == "sharpe" else 3) for m in ("retorno", "risco", "sharpe", "max_drawdown")])
        tabela(["Nas janelas de teste", "Retorno médio ao ano", "Oscilação ao ano", "Sharpe", "Queda máxima"],
               [[x["nome"], pct(x["teste"]["retorno"]), pct(x["teste"]["risco"]), num(x["teste"]["sharpe"]), pct(x["teste"]["max_drawdown"])] for x in cs], i, cores=cores)
        selic = res["desempenho"]["teste"].get("selic")
        leitura_de((f"A Selic rendeu {pct(selic['retorno_anualizado'])} ao ano no teste. " if selic else "") + f"Sharpe: {como_ler('sharpe')} "
                   + LEGENDA_CORES + " Cada coluna é uma comparação. Na oscilação, vence a menor.")
        nota("Cada divisão foi refeita antes de cada janela, só com os dados anteriores a ela, como na carteira da análise.")
        entenda(tx.PROMESSA, ids=["markowitz1952"])
        with st.expander("Para quem quer ver a conta"):
            st.markdown("Risco da carteira = √(wᵀΣw), em que w são os pesos e Σ é a covariância dos retornos, ao ano. "
                        f"A nuvem tem {num(k['nuvem']['n'], 0)} carteiras sorteadas pela distribuição de Dirichlet, das quais 1.500 aparecem no gráfico: "
                        "um terço espalhadas pelas ações e dois terços concentradas em poucas, para cobrir todas as divisões possíveis. "
                        "A fronteira procura, para cada retorno-alvo, a divisão de menor risco, sem venda a descoberto e com o mesmo limite por ação da divisão escolhida.")
            fontes(["markowitz1952"])

    conc = (res.get("concentracao") or {}).get("estrategia")
    if conc and conc["alerta"]:
        alerta(f"<b>Atenção à concentração.</b> {conc['ticker']} respondeu por {pct(conc['participacao'], 0)} do ganho da regra. Um resultado que vem quase todo de uma ação depende muito dela.")
    um_por_vez("item_carteira", [("Pesos", pesos), ("Correlação", correlacao), ("Fronteira eficiente", fronteira), ("Promessa e realidade", promessa)])


def tela_dinheiro(res: dict):
    e = res["desempenho"]
    cap = res["escolhas"]["capital"]
    final = e["inteiro"]
    pior = res["pior_momento"]["estrategia"]
    ordem = [k for k in ("estrategia", "buy_hold", "selic", "ibovespa") if k in e["teste"]]

    def evolucao():
        grafico("curvas", f"{brl(cap)} viraram {brl(final['estrategia']['valor_final'])} com a regra e {brl(final['buy_hold']['valor_final'])} ao comprar e segurar"
                + (f"; na Selic, seriam {brl(final['selic']['valor_final'])}" if "selic" in final else ""), g.fig_curvas(res))
        nota(tx.DINHEIRO_NAO_E_PASSAR)

    def pior_momento():
        if pior["data_recuperacao"]:
            volta = f"O patrimônio voltou ao valor do pico em {data_br(pior['data_recuperacao'])}, {num(pior['pregoes_recuperacao'], 0)} pregões depois do fundo."
        else:
            volta = "Até o fim do histórico, o patrimônio não voltou ao valor do pico."
        numeros([(brl(pior["valor_pico"]), f"no pico, em {data_br(pior['data_pico'])}"), (brl(pior["valor_fundo"]), f"no fundo, em {data_br(pior['data_fundo'])}"),
                 (pct(abs(pior["queda"])), "de queda máxima (drawdown)", f"Comprar e segurar, no mesmo histórico: {pct(abs(final['buy_hold']['max_drawdown']))}.")])
        html(f"<p>Para voltar ao pico, seria preciso subir {pct(1 / (1 + pior['queda']) - 1)}. {volta}</p>")

    def medidas(periodo: str):
        def mostrar():
            menor_melhor = {"volatilidade_anual"}       # nas demais medidas, quanto maior, melhor (a queda máxima é negativa)

            def quadro(linhas):
                cores = [melhor_e_pior([e[periodo][k][c] for k in ordem], c not in menor_melhor, 3 if f is pct else 2) for _, c, f in linhas]
                tabela(["Medida", *[g.NOME[k] for k in ordem]], [[r, *[f(e[periodo][k][c]) for k in ordem]] for r, c, f in linhas], cores=cores)
            # "Quanto rendeu e quanto caiu" e, abaixo, as razões entre retorno e risco (sem um terceiro nível de abas).
            sub("Rendimento e queda")
            quadro([("Retorno total", "retorno_total", pct), (("Retorno ao ano", como_ler("retorno_anualizado")), "retorno_anualizado", pct),
                    (("Oscilação ao ano", como_ler("volatilidade")), "volatilidade_anual", pct), (("Queda máxima", como_ler("drawdown")), "max_drawdown", pct)])
            leitura_de(LEGENDA_CORES + " Na oscilação, vence a menor. Nas demais, a maior; na queda máxima, a mais perto de zero.")
            sub("Retorno pelo risco")
            quadro([(("Sharpe", como_ler("sharpe")), "sharpe", num), (("Sortino", como_ler("sortino")), "sortino", num),
                    (("Retorno por queda", como_ler("retorno_por_queda")), "retorno_por_queda", num)])
            leitura_de(LEGENDA_CORES + " Nas três medidas, vence a maior.")
            with st.expander("Entenda melhor: Sharpe, Sortino e retorno por queda"):
                lista(tx.METRICAS_DESEMPENHO)
                fontes(["sharpe1994", "sortino1994"])
        return mostrar

    def todas_as_medidas():
        um_por_vez("item_periodo", [("Teste (janelas)", medidas("teste")), ("Treino inicial", medidas("treino")), ("Histórico inteiro", medidas("inteiro"))])

    def alternativas():
        sub("O que é cada alternativa")
        lista(tx.DINHEIRO_ALTERNATIVAS)
        html(f"<p>No histórico inteiro, a regra ficou comprada em {pct(res['operacoes']['tempo_comprado'], 0)} dos pregões. "
             "No resto do tempo, o dinheiro ficou parado, rendendo zero.</p>")
        sub("Os três períodos das tabelas")
        lista(tx.DINHEIRO_PERIODOS)
        sub(tx.CAPITAL_FIXO[0])
        html(f"<p>{tx.CAPITAL_FIXO[1]}</p>")
        fontes(["bcb_selic", "b3_ibov"])

    def dificil():
        html(f"<p>{tx.DIFICIL_INTRO}</p>")
        lista(tx.DIFICIL)
        fontes(["bcb_selic", "b3_tarifas", "lei_11033", "brock1992", "jensen1968"])

    um_por_vez("item_dinheiro", [("A evolução", evolucao), ("O pior momento", pior_momento), ("As medidas", todas_as_medidas),
                                 ("As alternativas", alternativas), ("Por que é difícil vencer", dificil)])


def tela_sharpe(res: dict):
    contas, e = res["conta_sharpe"], res["desempenho"]
    html(f"<p>{tx.SHARPE_IDEIA}</p>")
    tr, te = contas["treino"]["estrategia"], contas["teste"]["estrategia"]

    def linha(rotulo, chave, formato):
        return [rotulo, formato(tr[chave]), formato(te[chave])]

    em_pontos = lambda v: "—" if v is None else pontos(v) + " pontos"   # noqa: E731

    def conta():
        tabela(["Passo da conta", "Treino inicial", "Teste (janelas)"], [
            linha("1. Retorno médio da regra, ao ano", "retorno_medio_anual", pct),
            linha("2. Selic média, ao ano", "selic_media_anual", pct),
            linha("3. Retorno acima da Selic (1 − 2)", "excesso_anual", em_pontos),
            linha("4. Oscilação da regra, ao ano", "oscilacao_anual", pct),
            linha("5. Índice de Sharpe (3 ÷ 4)", "sharpe", num),
        ], 4)
        leitura_de(tx.SHARPE_CONTA_NOTA)

    def comparar():
        html(f"<p>{escape(res['frase_sharpe'])}</p>")
        series = [k for k in ("estrategia", "buy_hold", "ibovespa") if k in e["teste"]]
        periodos = ("treino", "teste", "inteiro")
        tabela(["Sharpe", "Treino inicial", "Teste (janelas)", "Histórico inteiro"], [[g.NOME[k], *[num(e[p][k]["sharpe"]) for p in periodos]] for k in series], 0,
               cores=por_coluna([melhor_e_pior([e[p][k]["sharpe"] for k in series], casas=2) for p in periodos]))
        leitura_de(LEGENDA_CORES + " Cada coluna é uma comparação: vence o maior Sharpe do período.")

    def limites():
        lista(tx.SHARPE_LIMITES)
        fontes(["sharpe1994", "sharpe1994_texto"])

    um_por_vez("item_sharpe", [("Um exemplo", lambda: nota(tx.SHARPE_EXEMPLO)), ("A conta desta análise", conta),
                               ("Como ler o valor", lambda: lista(tx.SHARPE_LEITURA)), ("Com o que comparar", comparar), ("Os limites", limites)])


SAIU_POR = {"sinal": ["Sinal", "da regra"], "stop": ["Limite", "de perda"], "alvo": ["Limite", "de ganho"],     # em duas linhas
            "fim_janela": ["Fim", "da janela"], "fim_dados": ["Fim", "dos dados"]}


def _na_bolsa(x: dict, lado: str) -> list[str]:
    """O preço que estava na bolsa no dia, quando difere do ajustado em ao menos 1%."""
    bolsa, ajustado = x.get(f"preco_{lado}_bolsa"), x[f"preco_{lado}"]
    return [f"na bolsa: {brl(bolsa, 2)}"] if bolsa and abs(bolsa / ajustado - 1) >= 0.01 else []


def quadro_operacoes(res: dict):
    """Todas as operações, com entrada, saída, variação, tarifas, a parte do imposto e o resultado final, e a soma no fim."""
    ops, janelas = res["operacoes"]["lista"], res["janelas"]
    def parte(data):
        for j in reversed(janelas):
            if str(data) >= str(j["inicio"]):
                return f"{j['n']}ª janela"
        return "Treino"

    cab = ["Nº", "Parte", "Ação", "Compra", "Venda", "Saiu por", "Variação", "Tarifas", "Imposto", "Resultado final", "Saldo em conta"]
    linhas = [[str(i), parte(x["data_entrada"]), x["ticker"],
               [data_br(x["data_entrada"]), f"{num(x['quantidade'], 0)} × {brl(x['preco_entrada'], 2)}", f"= {brl(x['valor_compra'])}", *_na_bolsa(x, "entrada")],
               [data_br(x["data_saida"]), f"{num(x['quantidade'], 0)} × {brl(x['preco_saida'], 2)}", f"= {brl(x['valor_venda'])}", *_na_bolsa(x, "saida")],
               SAIU_POR.get(x["motivo"], [x["motivo"]]),
               [f"{num(x['variacao_pct'], 1)}%", brl(x["variacao_rs"])], brl(x["custo"]), brl(x["imposto"]), brl(x["resultado_final"]),
               [f"após a compra: {brl(x['saldo_apos_compra'])}", f"após a venda: {brl(x['saldo_apos_venda'])}"]]
              for i, x in enumerate(ops, 1)]
    soma = lambda k: sum(x[k] for x in ops)      # noqa: E731
    capital = res["escolhas"]["capital"]
    total_pct = 100 * soma("variacao_rs") / capital     # sobre o dinheiro do início; o R$ já está no resultado final
    linhas.append(["Total", "", "", "", "", "", f"{num(total_pct, 1)}%", brl(soma("custo")),
                   brl(soma("imposto")), brl(soma("resultado_final")),
                   [f"início: {brl(capital)}", f"fim: {brl(capital + soma('resultado_final'))}"]])
    tabela(cab, linhas, destaque=len(linhas) - 1, classe="compacta rolagem")
    with st.expander("Como ler o quadro e o saldo em conta"):
        html(f"<p>{tx.QUADRO_OPERACOES if res['imposto']['aplicado'] else tx.QUADRO_OPERACOES_SEM_IMPOSTO}{tx.AJUSTE_QUADRO}</p><p>{tx.QUADRO_SALDO}</p>")


def tela_operacoes(res: dict):
    o = res["operacoes"]
    t, i = o["teste"], o["inteiro"]
    if not i["n_trades"]:
        nota("A regra não fez nenhuma operação nesta combinação.")
        return
    sub("Nas janelas de teste")
    anos_teste = res["periodo"]["anos_teste"]
    numeros([(num(t["n_trades"], 0), "operações", f"Cerca de {num(t['n_trades'] / anos_teste, 0)} por ano."),
             (num(t["fator_lucro"]), "fator de lucro: ganhos ÷ perdas", como_ler("fator_lucro")),
             (brl(t["maior_ganho"]), "maior ganho", f"O ganho médio foi de {brl(t['ganho_medio'])}."),
             (brl(t["maior_perda"]), "maior perda", f"A perda média foi de {brl(t['perda_media'])}."),
             (pct(t["queda_maxima"]), "queda máxima do patrimônio", f"Comprar e segurar, no mesmo período: {pct(res['desempenho']['teste']['buy_hold']['max_drawdown'])}.")])
    periodos = [o["treino"], t, i]

    def por_periodo(rotulo, chave, formato):
        return [rotulo, *[formato(p[chave]) for p in periodos]]

    def saidas(rotulo, chave):
        return [rotulo, *[num(p["saidas"][chave], 0) for p in periodos]]

    inteiro = lambda v: num(v, 0)   # noqa: E731
    percentual = lambda v: "—" if v is None else num(v, 1) + "%"    # noqa: E731

    def uma_a_uma():
        quadro_operacoes(res)
        salto = nota_salto(o["lista"], res["escolhas"]["stop"])
        if salto:
            nota(salto)

    def distribuicao():
        grafico("hist_operacoes", f"O resultado de cada operação, em todo o histórico: maior perda de {percentual(i['maior_perda_pct'])} e maior ganho de {percentual(i['maior_ganho_pct'])}",
                g.fig_histograma(o["histograma_retornos"], "Resultado da operação", marcas=[(0, "Empate")], rotulo_quantidade="Número de operações"))

    def metricas():
        leitura_de("Todas as métricas, por período: treino inicial, teste e histórico inteiro.")
        tabela_grupos(["Métrica", "Treino inicial", "Teste (janelas)", "Histórico inteiro"], [
            ("Quantidade", [por_periodo("Operações", "n_trades", inteiro), por_periodo("Com ganho", "n_ganhos", inteiro),
                            por_periodo("Com perda", "n_perdas", inteiro), por_periodo(("Taxa de acerto", como_ler("taxa_acerto")), "win_rate", pct),
                            por_periodo(("Taxa para empatar", "O acerto mínimo para não perder, dado o tamanho dos ganhos e das perdas."), "break_even", pct)]),
            ("Tamanho", [por_periodo("Ganho médio", "ganho_medio", brl), por_periodo("Perda média", "perda_media", brl), por_periodo(("Ganho médio ÷ perda média", como_ler("payoff")), "payoff", num),
                         por_periodo("Maior ganho em R$", "maior_ganho", brl), por_periodo("Maior ganho em %", "maior_ganho_pct", percentual),
                         por_periodo("Maior perda em R$", "maior_perda", brl), por_periodo("Maior perda em %", "maior_perda_pct", percentual)]),
            ("Resultado", [por_periodo(("Resultado líquido", "Soma das operações, já com as tarifas e antes do imposto de renda."), "resultado_liquido", brl), por_periodo(("Fator de lucro", como_ler("fator_lucro")), "fator_lucro", num),
                           por_periodo(("Resultado médio por operação", como_ler("expectativa")), "expectancia", brl),
                           por_periodo(("Tarifas pagas", "Já descontadas do resultado líquido."), "custos_pagos", brl),
                           por_periodo(("Imposto de renda pago", "Pago no mês seguinte ao das vendas. Sai do patrimônio, não do resultado de cada operação."),
                                       "imposto_pago", brl)]),
            ("Tempo", [por_periodo("Duração média, em pregões", "duracao_media", inteiro), por_periodo("Tempo comprado", "tempo_comprado", lambda v: pct(v, 0)),
                       por_periodo("Maior sequência de perdas", "maior_sequencia_perdas", inteiro)]),
            ("Risco", [por_periodo(("Queda máxima do patrimônio", como_ler("drawdown")), "queda_maxima", pct)]),
            ("Como as operações terminaram", [saidas("Pelo sinal da regra", "sinal"), saidas("No limite de perda", "stop"), saidas("No limite de ganho", "alvo"),
                                              saidas("No fim da janela, porque as escolhas mudaram", "fim_janela"), saidas("No fim dos dados", "fim_dados")]),
        ])
        nota(tx.AVISO_REAIS)
        with st.expander("Entenda melhor: as métricas"):
            html(f"<p>{tx.OPERACOES}</p>")
            lista(tx.METRICAS_OPERACOES)

    def custos():
        html(f"<p>{tx.CUSTOS_FIXOS[1]}</p>")
        ir = res["imposto"]
        if ir["aplicado"]:
            sub("O imposto de renda nesta análise")
            est_ir, bh_ir = ir["estrategia"], ir["buy_hold"]
            isentos = (f" Em {est_ir['meses_isentos']} meses, as vendas somaram até R$ 20 mil, e esses meses ficaram isentos."
                       if est_ir["meses_isentos"] else "")
            numeros([(brl(est_ir["total"]), "de imposto pago pela regra", f"Pago em {est_ir['meses_pagos']} meses.{isentos}"),
                     (brl(ir["antes_estrategia"]), "seria o valor final sem o imposto", f"Com o imposto, é {brl(res['desempenho']['inteiro']['estrategia']['valor_final'])}. A diferença não é igual ao imposto pago, "
                      "porque o dinheiro usado para pagá-lo deixa de ganhar ou de perder com a regra."),
                     (brl(bh_ir["total"]), "de imposto pago por comprar e segurar", "Ele só vende quando as escolhas mudam entre janelas e no fim do histórico, então paga menos vezes e mais tarde.")])
            with st.expander("Como o imposto é calculado"):
                lista(tx.IMPOSTO)
                html(f"<p>{tx.IMPOSTO_FORA}</p>")
                fontes(["in_rfb_1585", "lei_11033"])
        with st.expander("De onde vem a tarifa de 0,03%"):
            html(f"<p>{tx.CUSTO_B3}</p>")
            fontes(["b3_tarifas"])

    itens = [(f"Uma a uma ({num(len(o['lista']), 0)})", uma_a_uma)]
    if o["histograma_retornos"]:
        itens.append(("Ganhos e perdas", distribuicao))
    um_por_vez("item_operacoes", itens + [("Todas as métricas", metricas), ("Custos e imposto", custos)])


def tela_sorte(res: dict):
    s = res["foi_sorte"]
    alerta(tx.AVISO_PODER.format(anos=num(res["periodo"]["anos_teste"], 1)))
    entenda(tx.SORTE, tx.P_VALOR, ids=["asa2016"])

    def intervalo():
        abrir_teste(res, "intervalo")
        ic = s.get("ic_estrategia")
        extra = None
        if ic and ic.get("baixo_anual") is not None:
            grafico("intervalo", f"O ganho da regra acima da Selic fica entre {pontos(ic['baixo_anual'])} e {pontos(ic['alto_anual'])} pontos ao ano, com 95% de confiança", g.fig_intervalo(s))
            extra = f"Neste caso: média de {pontos(ic['media_anual'])} pontos ao ano, com {num(ic['n'], 0)} dias."
        fechar_teste(res, "intervalo", extra)

    def alfa():
        abrir_teste(res, "alfa")
        ab = s.get("alfa_beta")
        extra = None
        if ab and ab.get("alfa_anual") is not None:
            numeros([(num(ab["beta"]), "beta: o quanto acompanha o Ibovespa", "1 acompanha na mesma proporção; 0 não acompanha."),
                     (pontos(ab["alfa_anual"]), "alfa: pontos ao ano além do mercado", "Zero significa nada além do mercado."),
                     (p_valor(ab["p_alfa"]), "p-valor do alfa", "Abaixo de 0,05, há evidência de que o alfa não é zero.")])
            extra = f"Neste caso: R² de {num(ab['r2'])}, ou seja, o Ibovespa explica {pct(ab['r2'], 0)} das variações diárias da regra."
        fechar_teste(res, "alfa", extra)

    def desconto():
        abrir_teste(res, "desconto")
        q = s.get("sharpe_desconto") or {}
        extra = None
        if q.get("sharpe_ajustado") is not None:
            numeros([(num(q["sharpe"]), "Sharpe no teste", "Antes do desconto."), (num(q["sharpe_ajustado"]), "Sharpe depois do desconto", "O que sobra considerando as tentativas."),
                     (pct(q["p_ajustado"]), f"chance de ao menos 1 de {q['n_tentativas']} tentativas chegar a isso por acaso", "Há evidência abaixo de 5%, critério desta ferramenta.")])
        if q.get("p_ajustado") is not None:
            extra = f"Neste caso: t = {num(q['t'])}, p único = {p_valor(q['p_unico'])}, N = {q['n_tentativas']}, com {num(q['n_obs'], 0)} dias."
        fechar_teste(res, "desconto", extra)

    um_por_vez("item_sorte", [(rotulo_teste(res, "intervalo"), intervalo),
                              (rotulo_teste(res, "alfa"), alfa), (rotulo_teste(res, "desconto"), desconto)])


def tela_variacoes(res: dict):
    v, e = res["variacoes"], res["desempenho"]
    esc = res["escolhas"]
    entenda(tx.VARIACOES, ids=["bailey2014"])

    def treino_teste():
        abrir_teste(res, "treino_teste")
        tr, te = e["treino"]["estrategia"], e["teste"]["estrategia"]
        linhas = [("Retorno ao ano", "retorno_anualizado", pct), ("Oscilação ao ano", "volatilidade_anual", pct), ("Sharpe", "sharpe", num), ("Queda máxima", "max_drawdown", pct)]
        tabela(["Regra", "Treino inicial (estudo)", "Janelas de teste (prova)"], [[r, f(tr[k]), f(te[k])] for r, k, f in linhas]
               + ([["Selic ao ano, para comparar", pct(e["treino"]["selic"]["retorno_anualizado"]), pct(e["teste"]["selic"]["retorno_anualizado"])]] if "selic" in e["teste"] else []))
        fechar_teste(res, "treino_teste")

    def ano_a_ano():
        abrir_teste(res, "ano_a_ano")
        a = v["ano_a_ano"]
        grafico("ano_a_ano", f"A regra ganhou da Selic em {a['n_acima']} de {a['n_avaliados']} anos avaliados", g.fig_ano_a_ano(a["anos"]))
        fechar_teste(res, "ano_a_ano")

    def sensibilidade():
        abrir_teste(res, "sensibilidade")
        sel = e["teste"].get("selic")
        titulo = f"{v['n_bateram_selic']} de {v['n_combinacoes']} combinações superaram a Selic no teste; a sua está em azul" if v["n_bateram_selic"] is not None else None
        grafico("sensibilidade", titulo, g.fig_sensibilidade(v["combinacoes"], c.MEDIAS, c.PROTECOES, sel["retorno_total"] if sel else None, esc["curta"], esc["longa"], res["config"]["protecao"]))
        if esc["ritmo_muda"]:
            nota("Nesta análise, o ritmo mudou entre as janelas, então nenhuma das 16 combinações é exatamente a sua: o destaque marca o ritmo da 1ª janela.")
        fechar_teste(res, "sensibilidade")

    def custo():
        abrir_teste(res, "custo")
        sel = e["teste"].get("selic")
        tabela(["Simulação", "Regra no teste", "Selic no teste", "Superou a Selic?", "Imposto pago no histórico"],
               [[ln["rotulo"], pct(ln["retorno_teste"]), pct(ln["retorno_selic_teste"]) if ln["retorno_selic_teste"] is not None else "—",
                 {True: "Sim", False: "Não", None: "—"}[ln["bateu_selic"]], brl(ln["imposto_pago"])] for ln in v["custos"]])
        fechar_teste(res, "custo")

    um_por_vez("item_variacoes", [(rotulo_teste(res, "treino_teste"), treino_teste), (rotulo_teste(res, "ano_a_ano"), ano_a_ano),
                                  (rotulo_teste(res, "sensibilidade"), sensibilidade), (rotulo_teste(res, "custo"), custo)])


def tela_sequencia(res: dict):
    s = res["sequencia"]
    entenda(tx.SEQUENCIA)

    def monte_carlo():
        abrir_teste(res, "monte_carlo")
        mc = s["monte_carlo"]
        extra = None
        if mc:
            grafico("hist_monte_carlo", f"Em 5% das ordens simuladas, a queda seria maior que {pct(abs(mc['queda_pessimista']))}; na ordem real, foi de {pct(abs(mc['queda_observada']))}",
                    g.fig_histograma(mc["histograma"], "Queda máxima na simulação", marcas=[(100 * mc["queda_pessimista"], "Pessimista"), (100 * mc["queda_observada"], "Real")], rotulo_quantidade="Número de ordens"),
                    lambda: leitura_de(como_ler("monte_carlo")))
            extra = f"Neste caso: {num(mc['n_trades'], 0)} operações, {num(mc['n_simulacoes'], 0)} ordens; {pct(mc['pct_pior_que_observada'], 0)} delas tiveram queda maior que a real."
        fechar_teste(res, "monte_carlo", extra)

    def sem_melhores():
        abrir_teste(res, "sem_melhores")
        m3 = s["sem_melhores"]
        if m3:
            numeros([(brl(m3["resultado_total"]), "com todas as operações do teste", "Acima de zero, as operações deram lucro."),
                     (brl(m3["resultado_sem"]), "sem as 3 melhores", "Esta ferramenta pede que continue acima de zero.")])
        fechar_teste(res, "sem_melhores")

    um_por_vez("item_sequencia", [(rotulo_teste(res, "monte_carlo"), monte_carlo), (rotulo_teste(res, "sem_melhores"), sem_melhores)])


# ----------------------------------------------------------------------------- 5. compartilhar
def tela_compartilhar(res: dict):
    v = res["leitura"]
    perguntas = "".join(f'<div class="bloco">{escape(q["pergunta"])}<span class="resposta">{escape(q["resposta"])}</span></div><p class="det">{escape(q["texto"])}</p>'
                        for q in v["perguntas"])
    html(f'<div class="boletim perguntas">{perguntas}<p class="porque">{escape(v["por_que_nao_passou"])}</p></div>')
    if res["avisos"]:
        alerta("<b>Avisos sobre os dados.</b> " + " ".join(escape(a) for a in res["avisos"]))
    html(f'<p><a class="btn btn-outline-primary" href="{st.url("pdf")}" title="Duas páginas com as escolhas, a resposta, o resultado em R$, '
         f'os testes e os limites.">Baixar o resumo executivo em PDF</a></p>')

    def por_bloco():
        blocos = "".join(f'<div class="bloco">{escape(b["titulo"])}<span>passou em {b["n_passou"]} de {b["n_aplicaveis"]} testes aplicáveis</span></div>' for b in v["blocos"])
        html(f'<div class="boletim"><p class="frase">{escape(v["frase"])}</p>{blocos}'
             f'<p class="contagem">A regra passou em {v["n_passou"]} de {v["n_aplicaveis"]} testes aplicáveis. {escape(v["nota_contagem"])}</p></div>')

    def todos():
        for b in v["blocos"]:
            sub(b["titulo"])
            html("".join(f'<div class="teste-linha"><span>{escape(t["nome"])}</span>{selo(t["status"])}</div>' for t in b["testes"]))

    def criterios():
        st.markdown(tx.CRITERIOS_INTRO)
        lista([escape(x) for x in v["criterios_tecnicos"].values()])
        st.markdown(tx.PARAMETROS)

    um_por_vez("item_resultado", [("Os testes, por bloco", por_bloco), ("Todos os testes", todos), ("Os critérios de “passou”", criterios)])


# ----------------------------------------------------------------------------- 6. agir
def tela_agir(res: dict):
    alerta(escape(res["aviso_legal"]))

    def limites():
        sub(tx.LIMITES_TITULO)
        lista([x.format(data=DATA_CARTEIRA) for x in tx.LIMITES])
        html(f"<p>{tx.PROXIMOS_PASSOS}</p>")
        html(f'<p><a class="btn btn-outline-primary" href="{st.url("mudar")}">{tx.MUDAR}</a></p>')

    def glossario():
        for t in res["glossario"].values():
            cit = "; ".join(f"[{REFERENCIAS[i]['citacao'].split('.')[0]}]({REFERENCIAS[i]['url']})" for i in t["fontes"])
            ler = f"  \nComo ler: {t['como_ler']}" if t.get("como_ler") else ""
            st.markdown(f"**{t['nome']}.** {t['o_que_e']}  \nConta: {t['formula']}  \nExemplo: {t['exemplo']}{ler}" + (f"  \n*Fonte: {cit}.*" if cit else ""))

    um_por_vez("item_agir", [("Os limites", limites), ("Glossário", glossario), ("Todas as referências", lambda: fontes(list(REFERENCIAS)))])


# ----------------------------------------------------------------------------- navegação
def etapas(res: dict) -> list[dict]:
    """As telas depois da análise, em ordem. Cada uma tem o passo, o título e o id da frase de resumo."""
    telas = [{"passo": 2, "titulo": "Os dados", "id": "preparar", "mostrar": tela_preparar},
             {"passo": 3, "titulo": "O tratamento dos dados", "id": "processar", "mostrar": tela_processar},
             {"passo": 3, "titulo": "Treino e teste", "id": "treino_teste", "mostrar": tela_treino_teste}]
    # A regra e a régua (Sharpe) vêm antes das telas que usam o Sharpe para comparar.
    telas += [{"passo": 4, "titulo": "A regra em ação", "id": "regra", "mostrar": tela_regra},
              {"passo": 4, "titulo": "O índice de Sharpe", "id": "sharpe", "mostrar": tela_sharpe}]
    if res["selecao"]:
        telas.append({"passo": 4, "titulo": "Como a carteira foi escolhida", "id": "selecao", "mostrar": tela_selecao})
    if res["carteira"]:
        telas.append({"passo": 4, "titulo": "A divisão do dinheiro", "id": "carteira", "mostrar": tela_carteira})
    telas += [{"passo": 4, "titulo": "Quanto o dinheiro teria virado", "id": "dinheiro", "mostrar": tela_dinheiro},
              {"passo": 4, "titulo": "As janelas de teste", "id": "janelas", "mostrar": tela_janelas},
              {"passo": 4, "titulo": "As operações", "id": "operacoes", "mostrar": tela_operacoes},
              {"passo": 4, "titulo": "Foi sorte?", "id": "sorte", "mostrar": tela_sorte},
              {"passo": 4, "titulo": "Aguenta variações?", "id": "variacoes", "mostrar": tela_variacoes},
              {"passo": 4, "titulo": "E se a sequência fosse outra?", "id": "sequencia", "mostrar": tela_sequencia},
              {"passo": 5, "titulo": "O resultado", "id": "compartilhar", "mostrar": tela_compartilhar},
              {"passo": 6, "titulo": "O que fazer com isso", "id": "agir", "mostrar": tela_agir}]
    return telas


def _itens_etapas(atual: int) -> str:
    itens = ""
    for n, (nome, _) in tx.ETAPAS.items():
        classe = "atual" if n == atual else "feita" if n < atual else ""
        marcador = ' aria-current="step"' if n == atual else ""
        itens += f'<li class="{classe}"{marcador}>{n}. <span class="nome-etapa">{nome}</span></li>'
    return itens



def resumo_escolhas(res: dict) -> str:
    esc = res["escolhas"]
    acoes = f"Seleção automática: {len(res['tickers'])} ações" if res["selecao"] else ", ".join(res["tickers"])
    return " · ".join([acoes, esc["medias"], esc["protecao"], esc["custo"], brl(esc["capital"])])


# ----------------------------------------------------------------------------- montagem das páginas (só no portal)
def _montar(desenhar, urls: dict) -> str:
    st.comecar(urls)
    desenhar()
    return st.terminar()


def abertura(urls: dict) -> dict:
    """O alto do passo 1 (Perguntar), antes do formulário: o mesmo de `tela_perguntar` no app Streamlit."""
    def desenhar():
        html(f'<p class="onde">Passo 1 de 6 · {tx.ETAPAS[1][0]}</p>')
        html(f'<h1 class="titulo">{escape(tx.TITULO)}</h1><p class="abertura">{escape(tx.ABERTURA)}</p><div class="pergunta">{escape(tx.PERGUNTA)}</div>')
        entenda(tx.SOBRE_ETAPAS, tx.REGRA, ids=["google_etapas", "brock1992"])
    return {"etapas": _itens_etapas(1), "corpo": _montar(desenhar, urls)}


def pagina(res: dict, atual: int, urls: dict) -> dict:
    """Uma tela do resultado, com o que o cabeçalho e a navegação precisam (o `mostrar_resultado` do app Streamlit)."""
    telas = etapas(res)
    atual = max(0, min(atual, len(telas) - 1))
    t = telas[atual]
    nome_passo, pergunta = tx.ETAPAS[t["passo"]]
    return {
        "atual": atual,
        "n_telas": len(telas),
        "resumo": resumo_escolhas(res),
        "etapas": _itens_etapas(t["passo"]),
        "opcoes": [(i, f"Ir para: {x['passo']}. {tx.ETAPAS[x['passo']][0]} · {x['titulo']}") for i, x in enumerate(telas)],
        "onde": f"Passo {t['passo']} de 6 · {nome_passo} · {t['titulo']}",
        "titulo": pergunta if t["id"] in ("preparar", "processar", "compartilhar", "agir") else t["titulo"],
        "frase": tx.RESUMO[t["id"]],
        "corpo": _montar(lambda: t["mostrar"](res), urls),
    }
