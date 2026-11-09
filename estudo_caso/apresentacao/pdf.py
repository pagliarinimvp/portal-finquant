"""Resumo executivo da análise em PDF, para levar ou mostrar a quem não viu a página. Só uso local (reportlab).

Duas páginas A4, com a cara do portal ("painel institucional"): cabeçalho timbrado, ficha das escolhas, números-chave,
a resposta às três perguntas, quanto o dinheiro teria virado (gráfico e tabela), os testes, as operações do teste,
como ler os termos, os limites e o aviso legal. Os textos vêm do mesmo lugar que a página (`quant/leitura.py` e
`apresentacao/textos.py`), para os dois dizerem a mesma coisa.
"""
import math
import re
from datetime import date
from io import BytesIO
from pathlib import Path
from xml.sax.saxutils import escape

from reportlab.graphics.shapes import Drawing, Line, PolyLine, Rect, String
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas as rl_canvas
from reportlab.platypus import HRFlowable, KeepTogether, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from ..quant.universo import DATA_CARTEIRA

from . import textos as tx
from .formatacao import brl, data_br, num, pct

# Paleta do portal (static/css/site.css, tema claro): sóbria, com cor só onde ela informa.
TINTA, SUAVE, LINHA, NEVOA = colors.HexColor("#14161A"), colors.HexColor("#5B6470"), colors.HexColor("#DCDFE3"), colors.HexColor("#F4F5F7")
AZUL, AZUL_CLARO = colors.HexColor("#35506B"), colors.HexColor("#E7EDF3")
VERDE, VERDE_CLARO = colors.HexColor("#3E6B55"), colors.HexColor("#E3EFE8")
TERRA, TERRA_CLARO = colors.HexColor("#A64D39"), colors.HexColor("#F7E7E2")
AMBAR, AMBAR_CLARO = colors.HexColor("#8A5F0F"), colors.HexColor("#F7EFDC")
CINZA_CABECALHO = colors.HexColor("#C9CED6")
COR_STATUS = {"passou": (VERDE, VERDE_CLARO), "nao_passou": (TERRA, TERRA_CLARO), "nao_se_aplica": (SUAVE, NEVOA)}
ROTULO_STATUS = {"passou": "Passou", "nao_passou": "Não passou", "nao_se_aplica": "Não se aplica"}
COR_SERIE = {"estrategia": "#2563EB", "selic": "#D97706", "buy_hold": "#9D174D", "ibovespa": "#14A085"}
NOME_SERIE = {"estrategia": "Regra", "buy_hold": "Comprar e segurar", "selic": "Selic", "ibovespa": "Ibovespa"}
ALTURA_FAIXA = 17 * mm          # o cabeçalho timbrado, no alto de cada página

COMO_LER = [
    "<b>Janelas de teste:</b> a segunda metade do histórico, dividida em períodos de cerca de 1 ano. Antes de cada um, as escolhas "
    "foram refeitas só com o passado. É o trecho que vale para o veredito.",
    "<b>Comprar e segurar:</b> as mesmas ações, compradas no início e mantidas, sem a regra.",
    "<b>Selic:</b> a taxa básica de juros, o que se ganharia em renda fixa sem o risco da bolsa.",
    "<b>Sharpe:</b> quanto rendeu acima da Selic para cada ponto de oscilação. Zero é render igual à Selic; maior é melhor.",
    "<b>Queda máxima:</b> a maior queda do patrimônio, do pico ao fundo. Quanto mais perto de zero, melhor.",
]


# ------------------------------------------------------------------------------- fontes
def _fontes() -> tuple[str, str]:
    """Segoe UI ou Arial, quando o Windows tem (acentos e símbolos completos); senão, a DejaVu Sans que vem com o portal
    (`estudo_caso/fontes/`, para o servidor Linux); por último, Helvetica, que vem com o reportlab."""
    windows = Path("C:/Windows/Fonts")
    empacotada = Path(__file__).resolve().parents[1] / "fontes"
    for pasta, normal, negrito in ((windows, "segoeui.ttf", "segoeuib.ttf"), (windows, "arial.ttf", "arialbd.ttf"),
                                   (empacotada, "DejaVuSans.ttf", "DejaVuSans-Bold.ttf")):
        if (pasta / normal).exists() and (pasta / negrito).exists():
            nome = normal.split(".")[0]
            if nome not in pdfmetrics.getRegisteredFontNames():
                pdfmetrics.registerFont(TTFont(nome, str(pasta / normal)))
                pdfmetrics.registerFont(TTFont(nome + "-b", str(pasta / negrito)))
                pdfmetrics.registerFontFamily(nome, normal=nome, bold=nome + "-b", italic=nome, boldItalic=nome + "-b")
            return nome, nome + "-b"
    return "Helvetica", "Helvetica-Bold"


FONTE, NEGRITO = _fontes()
# A DejaVu (servidor Linux) é cerca de 10% mais larga que a Segoe UI: sem compensar, o resumo passa de duas páginas.
ESCALA = 0.92 if FONTE.startswith("DejaVu") else 1.0


def _estilo(nome, tamanho=9.5, cor=TINTA, negrito=False, antes=0, depois=3, entrelinha=1.3, alinhamento=TA_LEFT, recuo=0):
    tamanho *= ESCALA
    return ParagraphStyle(nome, fontName=NEGRITO if negrito else FONTE, fontSize=tamanho, leading=tamanho * entrelinha,
                          textColor=cor, spaceBefore=antes, spaceAfter=depois, alignment=alinhamento, leftIndent=recuo, bulletIndent=0)


E = {
    "titulo": _estilo("titulo", 17, negrito=True, depois=2, entrelinha=1.15),
    "pergunta_doc": _estilo("pergunta_doc", 9.4, SUAVE, depois=6, entrelinha=1.33),
    "secao": _estilo("secao", 11.5, negrito=True, antes=9, depois=2),
    "texto": _estilo("texto"),
    "suave": _estilo("suave", 7.8, SUAVE, depois=0, entrelinha=1.35),
    "celula": _estilo("celula", 8.4, depois=0, entrelinha=1.28),
    "celula_s": _estilo("celula_s", 7.9, SUAVE, depois=0, entrelinha=1.32),
    "celula_b": _estilo("celula_b", 8.4, negrito=True, depois=0, entrelinha=1.28),
    "celula_d": _estilo("celula_d", 8.4, depois=0, entrelinha=1.28, alinhamento=TA_RIGHT),
    "celula_db": _estilo("celula_db", 8.4, negrito=True, depois=0, entrelinha=1.28, alinhamento=TA_RIGHT),
    "cab": _estilo("cab", 7.6, colors.white, negrito=True, depois=0, entrelinha=1.2),
    "cab_d": _estilo("cab_d", 7.6, colors.white, negrito=True, depois=0, entrelinha=1.2, alinhamento=TA_RIGHT),
    "grupo": _estilo("grupo", 8.4, AZUL, negrito=True, depois=0, entrelinha=1.2),
    "grupo_d": _estilo("grupo_d", 7.9, AZUL, depois=0, entrelinha=1.2, alinhamento=TA_RIGHT),
    "rotulo": _estilo("rotulo", 6.8, SUAVE, negrito=True, depois=1, entrelinha=1.2),
    "valor": _estilo("valor", 8.4, depois=0, entrelinha=1.3),
    "kpi": _estilo("kpi", 14.5, negrito=True, depois=1.5, entrelinha=1.1),
    "kpi_op": _estilo("kpi_op", 12, negrito=True, depois=1.5, entrelinha=1.1),
    "pergunta": _estilo("pergunta", 9.6, negrito=True, depois=1.5),
    "selo": _estilo("selo", 8.4, negrito=True, depois=0, alinhamento=TA_CENTER),
    "item": _estilo("item", 8, depois=3.5, entrelinha=1.35, recuo=8),     # o texto alinha depois do marcador
    "subtitulo": _estilo("subtitulo", 9.2, negrito=True, depois=5),
    "destaque": _estilo("destaque", 9.6, depois=0, entrelinha=1.42),
}


def _p(texto: str, estilo: str = "texto") -> Paragraph:
    """Parágrafo com texto já em marcação simples (<b>). Textos vindos dos dados passam por `escape` antes."""
    return Paragraph(texto, E[estilo])


def _t(texto: str, estilo: str = "texto") -> Paragraph:
    return _p(escape(str(texto)), estilo)


def _hex(cor) -> str:
    return "#" + cor.hexval()[2:]


def _rotulo(texto: str) -> Paragraph:
    """Rótulo pequeno em caixa alta, como o `.fq-eyebrow` do portal."""
    return _t(texto.upper(), "rotulo")


def _secao(numero: int, titulo: str) -> list:
    """Título de seção numerado, com uma régua fina embaixo."""
    return [_p(f'<font color="{_hex(AZUL)}">{numero:02d}</font>&nbsp;&nbsp;&nbsp;{escape(titulo)}', "secao"),
            HRFlowable(width="100%", thickness=0.6, color=LINHA, spaceBefore=0, spaceAfter=6)]


def _selo(texto: str, cor, fundo, largura: float) -> Table:
    """Etiqueta colorida (Sim, Não, Passou...)."""
    s = Table([[_p(f'<font color="{_hex(cor)}">{escape(texto)}</font>', "selo")]], colWidths=[largura])
    s.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), fundo), ("TOPPADDING", (0, 0), (-1, -1), 1.8),
                           ("BOTTOMPADDING", (0, 0), (-1, -1), 2.8), ("LEFTPADDING", (0, 0), (-1, -1), 3), ("RIGHTPADDING", (0, 0), (-1, -1), 3)]))
    return s


def _caixa(conteudo: list, fundo, filete, largura: float) -> Table:
    """Bloco de destaque com um filete colorido à esquerda."""
    c = Table([[conteudo]], colWidths=[largura])
    c.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), fundo), ("LINEBEFORE", (0, 0), (0, -1), 3, filete),
                           ("LEFTPADDING", (0, 0), (-1, -1), 10), ("RIGHTPADDING", (0, 0), (-1, -1), 10),
                           ("TOPPADDING", (0, 0), (-1, -1), 7), ("BOTTOMPADDING", (0, 0), (-1, -1), 8)]))
    return c


def _tabela(linhas: list[list], larguras: list[float], destaque: int | None = None, grupos: tuple[int, ...] = ()) -> Table:
    """Tabela com cabeçalho escuro, linhas alternadas e, se pedido, uma linha em destaque e linhas de grupo."""
    t = Table(linhas, colWidths=larguras, repeatRows=1)
    estilo = [("VALIGN", (0, 0), (-1, -1), "MIDDLE"), ("BACKGROUND", (0, 0), (-1, 0), AZUL),
              ("LINEBELOW", (0, 1), (-1, -1), 0.4, LINHA),
              ("TOPPADDING", (0, 0), (-1, -1), 3), ("BOTTOMPADDING", (0, 0), (-1, -1), 3.6),
              ("LEFTPADDING", (0, 0), (-1, -1), 5), ("RIGHTPADDING", (0, 0), (-1, -1), 5)]
    zebra = 0
    for i in range(1, len(linhas)):
        if i in grupos:
            zebra = 0
            continue
        zebra += 1
        if zebra % 2 == 0:
            estilo.append(("BACKGROUND", (0, i), (-1, i), NEVOA))
    if destaque is not None:
        estilo += [("BACKGROUND", (0, destaque), (-1, destaque), AZUL_CLARO), ("LINEBEFORE", (0, destaque), (0, destaque), 2.5, AZUL)]
    for i in grupos:
        estilo += [("BACKGROUND", (0, i), (-1, i), AZUL_CLARO), ("LINEABOVE", (0, i), (-1, i), 0.8, AZUL), ("SPAN", (1, i), (-1, i))]
    t.setStyle(TableStyle(estilo))
    return t


# ------------------------------------------------------------------------------- gráfico
def _ordinal(d: str) -> int:
    return date.fromisoformat(d[:10]).toordinal()


def _mil(v: float) -> str:
    if v == 0:
        return "R$ 0"
    if v >= 1_000_000:
        return "R$ " + num(v / 1_000_000, 1).replace(",0", "") + " mi"
    return "R$ " + num(v / 1_000, 0) + " mil"


def _escala(minimo: float, maximo: float, alvo: int = 5) -> list[float]:
    """Marcas redondas no eixo (1, 2 ou 5 vezes uma potência de 10), começando em zero."""
    bruto = (maximo - minimo) / alvo or 1
    base = 10 ** math.floor(math.log10(bruto))
    passo = next(m * base for m in (1, 2, 5, 10) if m * base >= bruto)
    inicio = math.floor(minimo / passo) * passo
    return [inicio + i * passo for i in range(int(math.ceil((maximo - inicio) / passo)) + 1)]


def _grafico(res: dict, largura: float, altura: float = 48 * mm) -> Drawing:
    """As curvas do dinheiro em R$, com a faixa das janelas de teste. Desenhado à mão para não depender de imagem."""
    curvas, per = res["curvas"], res["periodo"]
    ordem = [k for k in ("selic", "ibovespa", "buy_hold", "estrategia") if curvas.get(k)]
    xs = [_ordinal(p["x"]) for k in ordem for p in curvas[k]]
    ys = [p["y"] for k in ordem for p in curvas[k]]
    x0, x1, y1 = min(xs), max(xs), max(ys)
    marcas = _escala(0.0, y1)
    y0, y1 = marcas[0], marcas[-1]
    esq, dir_, baixo, cima = 46, 6, 22, 20          # margens internas, em pontos
    larg, alt = largura - esq - dir_, altura - baixo - cima

    def px(d):
        return esq + (d - x0) / (x1 - x0 or 1) * larg

    def py(v):
        return baixo + (v - y0) / (y1 - y0 or 1) * alt

    g = Drawing(largura, altura)
    xt = px(_ordinal(per["inicio_teste"]))
    g.add(Rect(xt, baixo, esq + larg - xt, alt, fillColor=AZUL_CLARO, strokeColor=None))
    g.add(String(xt + 4, baixo + alt - 9, "JANELAS DE TESTE", fontName=NEGRITO, fontSize=6, fillColor=AZUL))
    for v in marcas:                                # linhas de grade em valores redondos de R$
        g.add(Line(esq, py(v), esq + larg, py(v), strokeColor=LINHA, strokeWidth=0.4))
        g.add(String(esq - 5, py(v) - 2.3, _mil(v), fontName=FONTE, fontSize=6.5, fillColor=SUAVE, textAnchor="end"))
    g.add(Line(esq, baixo, esq + larg, baixo, strokeColor=SUAVE, strokeWidth=0.6))
    for ano in range(date.fromordinal(x0).year + 1, date.fromordinal(x1).year + 1):
        x = px(date(ano, 1, 1).toordinal())
        g.add(Line(x, baixo, x, baixo - 2.5, strokeColor=SUAVE, strokeWidth=0.5))
        g.add(String(x, baixo - 10, str(ano), fontName=FONTE, fontSize=6.5, fillColor=SUAVE, textAnchor="middle"))
    for k in ordem:
        pts = [c for p in curvas[k] for c in (px(_ordinal(p["x"])), py(p["y"]))]
        g.add(PolyLine(pts, strokeColor=colors.HexColor(COR_SERIE[k]), strokeWidth=1.8 if k == "estrategia" else 1))
    x = esq                                          # legenda em cima, na ordem de importância
    for k in [s for s in ("estrategia", "buy_hold", "selic", "ibovespa") if s in ordem]:
        g.add(Rect(x, altura - 9, 10, 3, fillColor=colors.HexColor(COR_SERIE[k]), strokeColor=None))
        g.add(String(x + 14, altura - 10, NOME_SERIE[k], fontName=FONTE, fontSize=7.3, fillColor=TINTA))
        x += 26 + pdfmetrics.stringWidth(NOME_SERIE[k], FONTE, 7.3)
    return g


# ------------------------------------------------------------------------------- seções
def _ficha(res: dict, largura: float) -> Table:
    """As escolhas e o período, numa grade de rótulo e valor (4 colunas)."""
    esc, per = res["escolhas"], res["periodo"]
    acoes = (f"Automática: {', '.join(res['tickers'])} na 1ª janela" if res["selecao"]
             else ", ".join(res["tickers"]))
    itens = [("Ações", acoes), ("Ritmo das médias", esc["medias"]), ("Saída automática", esc["protecao"])]
    if esc.get("divisao"):
        itens.append(("Divisão do dinheiro", esc["divisao"]))
    itens += [("Custos e dinheiro inicial", f"{esc['custo']}, {brl(esc['capital'])}"),
              ("Período", f"{data_br(per['inicio'])} a {data_br(per['fim'])}, com {per['n_janelas']} janelas de teste")]
    itens += [("", "")] * (-len(itens) % 3)
    celula = lambda r, v: [_rotulo(r), _t(v, "valor")] if r else ""     # noqa: E731
    linhas = [[celula(*x) for x in itens[i:i + 3]] for i in range(0, len(itens), 3)]
    t = Table(linhas, colWidths=[largura * 0.36, largura * 0.30, largura * 0.34])
    t.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), NEVOA), ("VALIGN", (0, 0), (-1, -1), "TOP"),
                           ("LEFTPADDING", (0, 0), (-1, -1), 9), ("RIGHTPADDING", (0, 0), (-1, -1), 9),
                           ("TOPPADDING", (0, 0), (-1, -1), 5), ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                           ("LINEBELOW", (0, 0), (-1, -2), 0.5, colors.white), ("LINEAFTER", (0, 0), (-2, -1), 0.5, colors.white),
                           ("TOPPADDING", (0, 0), (-1, 0), 7), ("BOTTOMPADDING", (0, -1), (-1, -1), 7)]))
    return t


def _numeros_chave(res: dict, largura: float) -> Table:
    """Quatro números no alto: o valor final, o teste contra a Selic, os testes e a queda máxima."""
    inteiro, teste, v = res["desempenho"]["inteiro"], res["desempenho"]["teste"], res["leitura"]
    est = teste["estrategia"]
    selic = teste.get("selic")
    abaixo_selic = selic is not None and est["retorno_total"] < selic["retorno_total"]
    itens = [
        ("Valor final da regra", brl(inteiro["estrategia"]["valor_final"]), f"início: {brl(res['escolhas']['capital'])}", AZUL),
        ("Retorno nas janelas de teste", pct(est["retorno_total"]), f"Selic no mesmo período: {pct(selic['retorno_total'])}" if selic else "nas janelas de teste",
         TERRA if abaixo_selic else VERDE),
        ("Testes em que passou", f"{v['n_passou']} de {v['n_aplicaveis']}", "testes aplicáveis",
         VERDE if v["n_passou"] == v["n_aplicaveis"] else TERRA if v["n_passou"] * 2 < v["n_aplicaveis"] else AMBAR),
        ("Queda máxima no teste", pct(est["max_drawdown"]), f"comprar e segurar: {pct(teste['buy_hold']['max_drawdown'])}", AZUL),
    ]
    celulas = [[_rotulo(r), _p(f'<font color="{_hex(cor)}">{escape(valor)}</font>', "kpi"), _t(nota, "celula_s")] for r, valor, nota, cor in itens]
    t = Table([celulas], colWidths=[(largura - 3 * 5) / 4 + 5] * 3 + [(largura - 3 * 5) / 4])
    estilo = [("VALIGN", (0, 0), (-1, -1), "TOP"), ("LEFTPADDING", (0, 0), (-1, -1), 8), ("RIGHTPADDING", (0, 0), (-1, -1), 6),
              ("TOPPADDING", (0, 0), (-1, -1), 7), ("BOTTOMPADDING", (0, 0), (-1, -1), 8), ("BOX", (0, 0), (-1, -1), 0.5, LINHA),
              ("LINEAFTER", (0, 0), (-2, -1), 0.5, LINHA)]
    estilo += [("LINEABOVE", (i, 0), (i, 0), 2.2, cor) for i, (*_, cor) in enumerate(itens)]
    t.setStyle(TableStyle(estilo))
    return t


def _cor_resposta(resposta: str) -> tuple:
    if resposta == "Sim":
        return VERDE, VERDE_CLARO
    if resposta == "Não":
        return TERRA, TERRA_CLARO
    m = re.fullmatch(r"(\d+) de (\d+)", resposta)
    if m:
        a, b = int(m.group(1)), int(m.group(2))
        if a == b:
            return VERDE, VERDE_CLARO
        if a * 2 < b:
            return TERRA, TERRA_CLARO
    return AMBAR, AMBAR_CLARO


def _resposta(res: dict, largura: float) -> Table:
    v = res["leitura"]
    larg_selo = 24 * mm
    linhas, estilo = [], [("VALIGN", (0, 0), (-1, -1), "MIDDLE"), ("LEFTPADDING", (0, 0), (-1, -1), 0), ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                          ("TOPPADDING", (0, 0), (-1, -1), 4.5), ("BOTTOMPADDING", (0, 0), (-1, -1), 5), ("LEFTPADDING", (1, 0), (1, -1), 10)]
    for i, q in enumerate(v["perguntas"]):
        cor, fundo = _cor_resposta(q["resposta"])
        texto = q["texto"].replace("Os testes do passo 4", "Os testes")
        linhas.append([_selo(q["resposta"], cor, fundo, larg_selo), [_t(q["pergunta"], "pergunta"), _t(texto, "celula_s")]])
        if i:
            estilo.append(("LINEABOVE", (0, i), (-1, i), 0.5, LINHA))
    t = Table(linhas, colWidths=[larg_selo, largura - larg_selo])
    t.setStyle(TableStyle(estilo))
    return t


def _dinheiro(res: dict, largura: float) -> Table:
    inteiro, teste = res["desempenho"]["inteiro"], res["desempenho"]["teste"]
    cab = [_t("Alternativa", "cab"), *[_t(x, "cab_d") for x in ("Valor final, histórico inteiro", "Retorno no teste", "Sharpe no teste", "Queda máxima no teste")]]
    linhas = [cab]
    for k in [s for s in ("estrategia", "buy_hold", "selic", "ibovespa") if s in teste]:
        sharpe = "—" if k == "selic" else num(teste[k]["sharpe"])      # a Selic é a própria régua do Sharpe
        b = "b" if k == "estrategia" else ""
        linhas.append([_t(NOME_SERIE[k], "celula_b" if b else "celula"), _t(brl(inteiro[k].get("valor_final")), f"celula_d{b}"),
                       _t(pct(teste[k]["retorno_total"]), f"celula_d{b}"), _t(sharpe, f"celula_d{b}"), _t(pct(teste[k]["max_drawdown"]), f"celula_d{b}")])
    return _tabela(linhas, [largura * f for f in (0.26, 0.22, 0.17, 0.15, 0.2)], destaque=1)


def _testes(res: dict, largura: float) -> list:
    v = res["leitura"]
    larg_status = 25 * mm
    linhas = [[_t("Teste", "cab"), _t("A pergunta que ele responde", "cab"), _t("Resultado", "cab")]]
    grupos = []
    for b in v["blocos"]:
        grupos.append(len(linhas))
        linhas.append([_t(b["titulo"], "grupo"), _t(f"passou em {b['n_passou']} de {b['n_aplicaveis']} testes aplicáveis", "grupo_d"), ""])
        for t in b["testes"]:
            cor, fundo = COR_STATUS[t["status"]]
            linhas.append([_t(t["nome"], "celula"), _t(t["pergunta"], "celula_s"), _selo(ROTULO_STATUS[t["status"]], cor, fundo, larg_status - 10)])
    resto = largura - larg_status
    return [_tabela(linhas, [resto * 0.36, resto * 0.64, larg_status], grupos=tuple(grupos)), Spacer(1, 5),
            _p(f"<b>A regra passou em {v['n_passou']} de {v['n_aplicaveis']} testes aplicáveis.</b> {escape(v['nota_contagem'])}", "celula_s")]


def _operacoes(res: dict, largura: float) -> Table:
    """Os números das operações nas janelas de teste, em quadros lado a lado."""
    t, anos = res["operacoes"]["teste"], res["periodo"]["anos_teste"]
    itens = [(num(t["n_trades"], 0), f"operações, cerca de {num(t['n_trades'] / anos, 0)} por ano" if anos else "operações"),
             (pct(t["win_rate"]), "terminaram com ganho"),
             (num(t["fator_lucro"]), "fator de lucro: ganhos ÷ perdas (abaixo de 1, perdeu)"),
             (brl(t["resultado_liquido"]), "resultado, com tarifas e antes do imposto")]
    ir = res["imposto"]
    if ir["aplicado"]:
        itens.append((brl(ir["estrategia"]["total"]), "de imposto de renda no histórico inteiro"))
    tab = Table([[[_t(valor, "kpi_op"), _t(rotulo, "celula_s")] for valor, rotulo in itens]], colWidths=[largura / len(itens)] * len(itens))
    tab.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP"), ("BACKGROUND", (0, 0), (-1, -1), NEVOA),
                             ("LINEAFTER", (0, 0), (-2, -1), 1.5, colors.white),
                             ("LEFTPADDING", (0, 0), (-1, -1), 8), ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                             ("TOPPADDING", (0, 0), (-1, -1), 7), ("BOTTOMPADDING", (0, 0), (-1, -1), 8)]))
    return tab


def _lista(itens: list[str]) -> list:
    return [Paragraph(x, E["item"], bulletText="•") for x in itens]


def _duas_colunas(esquerda: list, direita: list, largura: float) -> Table:
    t = Table([[esquerda, direita]], colWidths=[largura / 2] * 2)
    t.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP"), ("LEFTPADDING", (0, 0), (-1, -1), 0), ("RIGHTPADDING", (0, 0), (0, -1), 9),
                           ("LEFTPADDING", (1, 0), (1, -1), 9), ("RIGHTPADDING", (1, 0), (1, -1), 0), ("LINEAFTER", (0, 0), (0, -1), 0.5, LINHA)]))
    return t


# ------------------------------------------------------------------------------- moldura das páginas
def _canvas_numerado(gerado: str):
    """Canvas que só desenha cabeçalho e rodapé no fim, quando já sabe o total de páginas ("Página 1 de 2")."""
    class Numerado(rl_canvas.Canvas):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self._paginas = []

        def showPage(self):
            self._paginas.append(dict(self.__dict__))
            self._startPage()

        def save(self):
            for estado in self._paginas:
                self.__dict__.update(estado)
                self._moldura(len(self._paginas))
                super().showPage()
            super().save()

        def _moldura(self, total: int):
            largura, altura = A4
            margem = 16 * mm
            self.saveState()
            self.setFillColor(TINTA)
            self.rect(0, altura - ALTURA_FAIXA, largura, ALTURA_FAIXA, stroke=0, fill=1)
            self.setFillColor(AZUL)
            self.rect(0, altura - ALTURA_FAIXA - 1.2 * mm, largura, 1.2 * mm, stroke=0, fill=1)
            base = altura - ALTURA_FAIXA / 2
            self.setFillColor(colors.white)
            self.setFont(NEGRITO, 10.5)
            self.drawString(margem, base + 1.5, "Portal FinQuant")
            self.setFillColor(CINZA_CABECALHO)
            self.setFont(FONTE, 7.8)
            self.drawString(margem, base - 9, "Análise de ações · Resumo executivo")
            self.drawRightString(largura - margem, base + 1.5, f"Gerado em {gerado}")
            self.drawRightString(largura - margem, base - 9, "Conteúdo educacional")
            self.setStrokeColor(LINHA)
            self.setLineWidth(0.5)
            self.line(margem, 12.5 * mm, largura - margem, 12.5 * mm)
            self.setFillColor(SUAVE)
            self.setFont(FONTE, 7.2)
            self.drawString(margem, 8.5 * mm, "Simulação com dados do passado. Não é recomendação de investimento.")
            self.drawRightString(largura - margem, 8.5 * mm, f"Página {self._pageNumber} de {total}")
            self.restoreState()

    return Numerado


# ------------------------------------------------------------------------------- documento
def gerar_pdf(res: dict, hoje: date | None = None) -> bytes:
    """Resumo executivo da análise já rodada. `hoje`: data impressa no cabeçalho (fixável nos testes)."""
    saida = BytesIO()
    margem = 16 * mm
    doc = SimpleDocTemplate(saida, pagesize=A4, leftMargin=margem, rightMargin=margem, topMargin=ALTURA_FAIXA + 7 * mm,
                            bottomMargin=17 * mm, title="Resumo executivo da análise de ações", author="Portal FinQuant")
    largura = A4[0] - 2 * margem
    v = res["leitura"]
    gerado = (hoje or date.today()).strftime("%d/%m/%Y")
    limites = [x.format(data=DATA_CARTEIRA).replace(" Quando isso acontece, a página avisa.", "") for x in tx.LIMITES[:3]]

    corpo = [
        _p(escape(tx.TITULO), "titulo"),
        _p(escape(tx.PERGUNTA), "pergunta_doc"),
        _ficha(res, largura),
        Spacer(1, 6),
        _numeros_chave(res, largura),
        *_secao(1, "A resposta"),
        _resposta(res, largura),
        Spacer(1, 4),
        _caixa([_t(v["frase"], "destaque")], AZUL_CLARO, AZUL, largura),
        KeepTogether([*_secao(2, "Quanto o dinheiro teria virado"), _grafico(res, largura), Spacer(1, 6), _dinheiro(res, largura),
                      Spacer(1, 4), _p("Valor final depois das tarifas e do imposto. O histórico inteiro inclui o treino, em que "
                                       "as escolhas foram feitas olhando os próprios dados; por isso, o veredito olha as janelas de teste.", "suave")]),
        KeepTogether([*_secao(3, "Os testes"), *_testes(res, largura)]),
        KeepTogether([*_secao(4, "As operações nas janelas de teste"), _operacoes(res, largura)]),
        KeepTogether([*_secao(5, "Para ler com cuidado"),
                      _duas_colunas([_p("Como ler os termos", "subtitulo"), *_lista(COMO_LER)],
                                    [_p(escape(tx.LIMITES_TITULO), "subtitulo"), *_lista(limites)], largura)]),
    ]
    if res["avisos"]:
        corpo += [Spacer(1, 8), _caixa([_p("Avisos sobre os dados", "subtitulo"), *[_t(a, "celula") for a in res["avisos"]]], AMBAR_CLARO, AMBAR, largura)]
    corpo += [Spacer(1, 8), _t(res["aviso_legal"], "suave")]
    doc.build(corpo, canvasmaker=_canvas_numerado(gerado))
    return saida.getvalue()
