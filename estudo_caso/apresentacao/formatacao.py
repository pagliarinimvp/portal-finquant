"""Formatação pt-BR de números e datas para a interface (sem dependência de Streamlit)."""


def _br(txt: str) -> str:
    return txt.replace(",", "X").replace(".", ",").replace("X", ".")


def num(v, casas: int = 2) -> str:
    return "—" if v is None else _br(f"{v:,.{casas}f}")


def pct(v, casas: int = 1) -> str:
    return "—" if v is None else _br(f"{100 * v:,.{casas}f}") + "%"


def pontos(v, casas: int = 1) -> str:
    """Diferença em pontos percentuais, com sinal: 0,05 -> '+5,0'."""
    return "—" if v is None else _br(f"{100 * v:+,.{casas}f}")


def brl(v, casas: int = 0) -> str:
    """R$ sem centavos, por padrão: valores grandes ficam mais fáceis de ler."""
    if v is None:
        return "—"
    return ("-" if v < 0 else "") + "R$ " + num(abs(v), casas)      # espaço que não quebra a linha


def p_valor(v) -> str:
    if v is None:
        return "—"
    return "menor que 0,001" if v < 0.001 else num(v, 3)


def data_br(v) -> str:
    """'2026-10-02' -> '02/10/2026'. Aceita também Timestamp e date."""
    if v is None or v == "":
        return "—"
    txt = str(v).split(" ")[0].split("T")[0]
    try:
        ano, mes, dia = txt.split("-")
    except ValueError:
        return str(v)
    return f"{dia}/{mes}/{ano}"


def nota_salto(operacoes: list, stop: float | None) -> str | None:
    """Explica as perdas maiores que o limite: a ação abriu abaixo dele, e a venda saiu na abertura."""
    if not stop:
        return None
    folga = 1.0                     # as tarifas somam centésimos de ponto; acima de 1 ponto, foi salto de preço
    casos = sorted((x for x in operacoes if x["motivo"] == "stop" and x["retorno_pct"] < -(stop + folga)), key=lambda x: x["retorno_pct"])
    if not casos:
        return None
    exemplos = [f"em {data_br(x['data_saida'])}, {x['ticker']} perdeu {num(abs(x['retorno_pct']), 1)}%" for x in casos[:3]]
    lista_txt = exemplos[0] if len(exemplos) == 1 else ", ".join(exemplos[:-1]) + " e " + exemplos[-1]
    resto = f" (e mais {len(casos) - 3})" if len(casos) > 3 else ""
    quantas = "uma operação" if len(casos) == 1 else f"{len(casos)} operações"
    return (f"<b>Por que há perdas maiores que {num(stop, 0)}%.</b> O limite manda vender ao perder {num(stop, 0)}%, mas em {quantas} "
            f"a ação já abriu abaixo desse ponto, em geral por uma notícia saída com a bolsa fechada: {lista_txt}{resto}. Sem negócios no "
            "meio do caminho, a venda sai no primeiro preço disponível, o da abertura. Na bolsa de verdade, a ordem de saída também "
            "seria executada nesse preço ou pior.")
