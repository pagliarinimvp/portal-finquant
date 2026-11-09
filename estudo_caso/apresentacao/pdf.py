"""Resumo executivo da análise em PDF, para levar ou mostrar a quem não viu a página. Só uso local (reportlab).

Duas páginas A4: as escolhas, a resposta às três perguntas, quanto o dinheiro teria virado (gráfico e tabela),
os testes, as operações do teste, como ler os termos, os limites e o aviso legal. Os textos vêm do mesmo lugar
que a página (`quant/leitura.py` e `apresentacao/textos.py`), para os dois dizerem a mesma coisa.
"""
from datetime import date
from io import BytesIO
from pathlib import Path
from xml.sax.saxutils import escape

from reportlab.graphics.shapes import Drawing, Line, PolyLine, Rect, String
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import KeepTogether, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from ..quant.universo import DATA_CARTEIRA

from . import textos as tx
from .formatacao import brl, data_br, num, pct

TINTA, SUAVE, LINHA, NEVOA = colors.HexColor("#16323F"), colors.HexColor("#4F636E"), colors.HexColor("#D9E3E8"), colors.HexColor("#F1F6F8")
AZUL_CLARO = colors.HexColor("#E8EFFD")
COR_STATUS = {"passou": colors.HexColor("#0B6B50"), "nao_passou": colors.HexColor("#A8320F"), "nao_se_aplica": SUAVE}
ROTULO_STATUS = {"passou": "Passou", "nao_passou": "Não passou", "nao_se_aplica": "Não se aplica"}
COR_SERIE = {"estrategia": "#2563EB", "selic": "#D97706", "buy_hold": "#9D174D", "ibovespa": "#14A085"}
NOME_SERIE = {"estrategia": "Regra", "buy_hold": "Comprar e segurar", "selic": "Selic", "ibovespa": "Ibovespa"}

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


def _estilo(nome, tamanho=9.5, cor=TINTA, negrito=False, antes=0, depois=3, entrelinha=1.3):
    return ParagraphStyle(nome, fontName=NEGRITO if negrito else FONTE, fontSize=tamanho, leading=tamanho * entrelinha,
                          textColor=cor, spaceBefore=antes, spaceAfter=depois, alignment=TA_LEFT)


E = {
    "topo": _estilo("topo", 8.5, SUAVE, depois=2),
    "titulo": _estilo("titulo", 19, negrito=True, depois=4, entrelinha=1.15),
    "secao": _estilo("secao", 12.5, negrito=True, antes=10, depois=5),
    "texto": _estilo("texto"),
    "suave": _estilo("suave", 8.5, SUAVE, depois=2),
    "celula": _estilo("celula", 8.8, depois=0, entrelinha=1.25),
    "celula_b": _estilo("celula_b", 8.8, negrito=True, depois=0, entrelinha=1.25),
    "pergunta": _estilo("pergunta", 10, negrito=True, depois=0),
    "item": _estilo("item", 9, depois=2),
}


def _p(texto: str, estilo: str = "texto") -> Paragraph:
    """Parágrafo com texto já em marcação simples (<b>). Textos vindos dos dados passam por `escape` antes."""
    return Paragraph(texto, E[estilo])


def _t(texto: str, estilo: str = "texto") -> Paragraph:
    return _p(escape(str(texto)), estilo)


def _status(status: str) -> Paragraph:
    cor = COR_STATUS[status].hexval()[2:]
    return _p(f'<font color="#{cor}"><b>{ROTULO_STATUS[status]}</b></font>', "celula")


def _tabela(linhas: list[list], larguras: list[float], cabecalho: bool = True, destaque: int | None = None) -> Table:
    t = Table(linhas, colWidths=larguras, repeatRows=1 if cabecalho else 0)
    estilo = [("VALIGN", (0, 0), (-1, -1), "TOP"), ("LINEBELOW", (0, 0), (-1, -1), 0.5, LINHA),
              ("TOPPADDING", (0, 0), (-1, -1), 3.5), ("BOTTOMPADDING", (0, 0), (-1, -1), 3.5),
              ("LEFTPADDING", (0, 0), (-1, -1), 4), ("RIGHTPADDING", (0, 0), (-1, -1), 4)]
    if cabecalho:
        estilo += [("LINEBELOW", (0, 0), (-1, 0), 1, TINTA)]
    if destaque is not None:
        estilo += [("BACKGROUND", (0, destaque), (-1, destaque), NEVOA)]
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
    import math
    bruto = (maximo - minimo) / alvo or 1
    base = 10 ** math.floor(math.log10(bruto))
    passo = next(m * base for m in (1, 2, 5, 10) if m * base >= bruto)
    inicio = math.floor(minimo / passo) * passo
    return [inicio + i * passo for i in range(int(math.ceil((maximo - inicio) / passo)) + 1)]


def _grafico(res: dict, largura: float, altura: float = 62 * mm) -> Drawing:
    """As curvas do dinheiro em R$, com a faixa das janelas de teste. Desenhado à mão para não depender de imagem."""
    curvas, per = res["curvas"], res["periodo"]
    ordem = [k for k in ("selic", "ibovespa", "buy_hold", "estrategia") if curvas.get(k)]
    xs = [_ordinal(p["x"]) for k in ordem for p in curvas[k]]
    ys = [p["y"] for k in ordem for p in curvas[k]]
    x0, x1, y0, y1 = min(xs), max(xs), min(ys), max(ys)
    marcas = _escala(0.0, y1)
    y0, y1 = marcas[0], marcas[-1]
    esq, dir_, baixo, cima = 52, 8, 26, 16          # margens internas, em pontos
    larg, alt = largura - esq - dir_, altura - baixo - cima

    def px(d):
        return esq + (d - x0) / (x1 - x0 or 1) * larg

    def py(v):
        return baixo + (v - y0) / (y1 - y0 or 1) * alt

    g = Drawing(largura, altura)
    xt = px(_ordinal(per["inicio_teste"]))
    g.add(Rect(xt, baixo, esq + larg - xt, alt, fillColor=colors.HexColor("#E3ECF6"), strokeColor=None))
    g.add(String(xt + 3, baixo + alt - 9, "Janelas de teste", fontName=FONTE, fontSize=7, fillColor=SUAVE))
    for v in marcas:                                # linhas de grade em valores redondos de R$
        g.add(Line(esq, py(v), esq + larg, py(v), strokeColor=LINHA, strokeWidth=0.5))
        g.add(String(esq - 4, py(v) - 2.5, _mil(v), fontName=FONTE, fontSize=6.8, fillColor=SUAVE, textAnchor="end"))
    for ano in range(date.fromordinal(x0).year + 1, date.fromordinal(x1).year + 1):
        x = px(date(ano, 1, 1).toordinal())
        g.add(Line(x, baixo, x, baixo - 3, strokeColor=SUAVE, strokeWidth=0.5))
        g.add(String(x, baixo - 11, str(ano), fontName=FONTE, fontSize=6.8, fillColor=SUAVE, textAnchor="middle"))
    for k in ordem:
        pts = [c for p in curvas[k] for c in (px(_ordinal(p["x"])), py(p["y"]))]
        g.add(PolyLine(pts, strokeColor=colors.HexColor(COR_SERIE[k]), strokeWidth=1.8 if k == "estrategia" else 1.1))
    x = esq                                          # legenda em cima, na ordem de importância
    for k in [s for s in ("estrategia", "buy_hold", "selic", "ibovespa") if s in ordem]:
        g.add(Line(x, altura - 6, x + 12, altura - 6, strokeColor=colors.HexColor(COR_SERIE[k]), strokeWidth=2))
        g.add(String(x + 15, altura - 8.5, NOME_SERIE[k], fontName=FONTE, fontSize=7.5, fillColor=TINTA))
        x += 22 + pdfmetrics.stringWidth(NOME_SERIE[k], FONTE, 7.5)
    return g


# ------------------------------------------------------------------------------- seções
def _escolhas(res: dict) -> str:
    esc = res["escolhas"]
    acoes = (f"Seleção automática ({len(res['tickers'])} ações na 1ª janela: {', '.join(res['tickers'])})" if res["selecao"]
             else ", ".join(res["tickers"]))
    partes = [f"<b>Ações:</b> {escape(acoes)}", f"<b>Ritmo:</b> {escape(esc['medias'])}", f"<b>Saída automática:</b> {escape(esc['protecao'])}",
              f"<b>Custos:</b> {escape(esc['custo'])}", f"<b>Dinheiro inicial:</b> {brl(esc['capital'])}"]
    if esc.get("divisao"):
        partes.insert(1, f"<b>Divisão:</b> {escape(esc['divisao'])}")
    return " · ".join(partes)


def _resposta(res: dict, largura: float) -> Table:
    v = res["leitura"]
    linhas = []
    for q in v["perguntas"]:
        linhas.append([_t(q["pergunta"], "pergunta"), _t(q["resposta"], "pergunta")])
        linhas.append([_t(q["texto"].replace("Os testes do passo 4", "Os testes"), "celula"), ""])
    t = Table(linhas, colWidths=[largura - 30 * mm, 30 * mm])
    estilo = [("BACKGROUND", (0, 0), (-1, -1), AZUL_CLARO), ("VALIGN", (0, 0), (-1, -1), "TOP"),
              ("LEFTPADDING", (0, 0), (-1, -1), 8), ("RIGHTPADDING", (0, 0), (-1, -1), 8),
              ("TOPPADDING", (0, 0), (-1, -1), 1.5), ("BOTTOMPADDING", (0, 0), (-1, -1), 1.5), ("ALIGN", (1, 0), (1, -1), "RIGHT")]
    for i in range(0, len(linhas), 2):
        estilo += [("SPAN", (0, i + 1), (1, i + 1)), ("TOPPADDING", (0, i), (-1, i), 7)]
        if i:
            estilo += [("LINEABOVE", (0, i), (-1, i), 0.5, colors.white)]
    estilo += [("BOTTOMPADDING", (0, len(linhas) - 1), (-1, len(linhas) - 1), 8)]
    t.setStyle(TableStyle(estilo))
    return t


def _dinheiro(res: dict, largura: float) -> Table:
    inteiro, teste = res["desempenho"]["inteiro"], res["desempenho"]["teste"]
    cab = [_t(x, "celula_b") for x in ("Alternativa", "Valor final no histórico inteiro", "Retorno nas janelas de teste", "Sharpe no teste", "Queda máxima no teste")]
    linhas = [cab]
    for k in [s for s in ("estrategia", "buy_hold", "selic", "ibovespa") if s in teste]:
        sharpe = "—" if k == "selic" else num(teste[k]["sharpe"])      # a Selic é a própria régua do Sharpe
        linhas.append([_t(NOME_SERIE[k], "celula_b" if k == "estrategia" else "celula"), _t(brl(inteiro[k].get("valor_final")), "celula"),
                       _t(pct(teste[k]["retorno_total"]), "celula"), _t(sharpe, "celula"), _t(pct(teste[k]["max_drawdown"]), "celula")])
    return _tabela(linhas, [largura * f for f in (0.26, 0.2, 0.2, 0.14, 0.2)], destaque=1)


def _testes(res: dict, largura: float) -> list:
    v = res["leitura"]
    linhas = [[_t("Teste", "celula_b"), _t("A pergunta", "celula_b"), _t("Resultado", "celula_b")]]
    grupos = []
    for b in v["blocos"]:
        grupos.append(len(linhas))
        linhas.append([_t(f"{b['titulo']} · passou em {b['n_passou']} de {b['n_aplicaveis']}", "celula_b"), "", ""])
        for t in b["testes"]:
            linhas.append([_t(t["nome"], "celula"), _t(t["pergunta"], "celula"), _status(t["status"])])
    tab = _tabela(linhas, [largura * 0.3, largura * 0.52, largura * 0.18])
    tab.setStyle(TableStyle([s for i in grupos for s in (("SPAN", (0, i), (-1, i)), ("BACKGROUND", (0, i), (-1, i), NEVOA))]))
    return [tab, Spacer(1, 4),
            _p(f"<b>A regra passou em {v['n_passou']} de {v['n_aplicaveis']} testes aplicáveis.</b> {escape(v['nota_contagem'])}", "texto")]


def _operacoes(res: dict, largura: float) -> Table:
    t, anos = res["operacoes"]["teste"], res["periodo"]["anos_teste"]
    itens = [(num(t["n_trades"], 0), f"operações, cerca de {num(t['n_trades'] / anos, 0)} por ano" if anos else "operações"),
             (pct(t["win_rate"]), "terminaram com ganho"),
             (num(t["fator_lucro"]), "fator de lucro: ganhos ÷ perdas (abaixo de 1, perdeu dinheiro)"),
             (brl(t["resultado_liquido"]), "resultado das operações, com tarifas e antes do imposto")]
    ir = res["imposto"]
    if ir["aplicado"]:
        itens.append((brl(ir["estrategia"]["total"]), "de imposto de renda pago pela regra no histórico inteiro"))
    linhas = [[_t(valor, "pergunta"), _t(rotulo, "celula")] for valor, rotulo in itens]
    tab = Table(linhas, colWidths=[30 * mm, largura - 30 * mm])
    tab.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "MIDDLE"), ("LINEBELOW", (0, 0), (-1, -1), 0.5, LINHA),
                             ("TOPPADDING", (0, 0), (-1, -1), 3), ("BOTTOMPADDING", (0, 0), (-1, -1), 3), ("LEFTPADDING", (0, 0), (-1, -1), 4)]))
    return tab


def _lista(itens: list[str]) -> list:
    return [_p(f"• {x}", "item") for x in itens]


def _rodape(c, doc):
    c.saveState()
    c.setFont(FONTE, 7.5)
    c.setFillColor(SUAVE)
    c.drawString(doc.leftMargin, 10 * mm, "Análise Quantitativa · conteúdo educacional, não é recomendação de investimento")
    c.drawRightString(A4[0] - doc.rightMargin, 10 * mm, f"Página {c.getPageNumber()}")
    c.restoreState()


# ------------------------------------------------------------------------------- documento
def gerar_pdf(res: dict, hoje: date | None = None) -> bytes:
    """Resumo executivo da análise já rodada. `hoje`: data impressa no topo (fixável nos testes)."""
    saida = BytesIO()
    margem = 16 * mm
    doc = SimpleDocTemplate(saida, pagesize=A4, leftMargin=margem, rightMargin=margem, topMargin=14 * mm, bottomMargin=16 * mm,
                            title="Resumo executivo da análise", author="Análise Quantitativa")
    largura = A4[0] - 2 * margem
    per, v = res["periodo"], res["leitura"]
    gerado = (hoje or date.today()).strftime("%d/%m/%Y")

    corpo = [
        _p(f"RESUMO EXECUTIVO · gerado em {gerado}", "topo"),
        _p(escape(tx.TITULO), "titulo"),
        _p(escape(tx.PERGUNTA), "texto"),
        _p(_escolhas(res), "suave"),
        _p(f"Histórico de {data_br(per['inicio'])} a {data_br(per['fim'])}, com {num(per['n_pregoes'], 0)} pregões. As escolhas foram conferidas em "
           f"{per['n_janelas']} janelas de teste, de {data_br(per['inicio_teste'])} a {data_br(per['fim'])}.", "suave"),
        _p("A resposta", "secao"),
        _resposta(res, largura),
        Spacer(1, 5),
        _t(v["frase"], "texto"),
        KeepTogether([_p("Quanto o dinheiro teria virado", "secao"), _grafico(res, largura), Spacer(1, 4), _dinheiro(res, largura),
                      Spacer(1, 3), _p("Valor final depois das tarifas e do imposto. O histórico inteiro inclui o treino, em que "
                                       "as escolhas foram feitas olhando os próprios dados; por isso, o veredito olha as janelas de teste.", "suave")]),
        KeepTogether([_p("Os testes", "secao"), *_testes(res, largura)]),
        KeepTogether([_p("As operações nas janelas de teste", "secao"), _operacoes(res, largura)]),
        KeepTogether([_p("Como ler os termos", "secao"), *_lista(COMO_LER)]),
        KeepTogether([_p(escape(tx.LIMITES_TITULO), "secao"), *_lista([x.format(data=DATA_CARTEIRA).replace(" Quando isso acontece, a página avisa.", "") for x in tx.LIMITES[:3]])]),
    ]
    if res["avisos"]:
        corpo += [_p("Avisos sobre os dados", "secao"), *_lista([escape(a) for a in res["avisos"]])]
    corpo += [Spacer(1, 6), _t(res["aviso_legal"], "suave")]
    doc.build(corpo, onFirstPage=_rodape, onLaterPages=_rodape)
    return saida.getvalue()
