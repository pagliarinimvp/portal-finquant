"""Universo de ações do Ibovespa (lista estática e editável).

Retrato da carteira publicada pela B3 no site de índices, consultado em 07/11/2026, com a carteira
do dia 09/11/2026. A composição muda a cada quadrimestre, então esta lista precisa ser atualizada.
Tickers sem dados no Yahoo Finance são descartados com aviso, sem interromper a análise.
"""

DATA_CARTEIRA = "09/11/2026"

IBOVESPA = [
    "ABEV3", "ALOS3", "ASAI3", "AURE3", "AXIA3", "AZZA3", "B3SA3", "BBAS3",
    "BBDC3", "BBDC4", "BBSE3", "BEEF3", "BPAC11", "BRAP4", "BRAV3", "CEAB3",
    "CMIG4", "CMIN3", "COGN3", "CPFE3", "CPLE3", "CSAN3", "CSMG3", "CSNA3",
    "CURY3", "CXSE3", "CYRE3", "DIRR3", "EGIE3", "EMBJ3", "ENEV3", "ENGI11",
    "EQTL3", "FLRY3", "GGBR4", "GOAU4", "HAPV3", "HYPE3", "IGTI11", "ISAE4",
    "ITSA4", "ITUB4", "KLBN11", "LREN3", "MBRF3", "MGLU3", "MOTV3", "MRVE3",
    "MULT3", "NATU3", "PETR3", "PETR4", "POMO4", "PRIO3", "PSSA3", "RADL3",
    "RAIL3", "RDOR3", "RENT3", "SANB11", "SBSP3", "SMFT3", "SUZB3", "TAEE11",
    "TEND3", "TIMS3", "TOTS3", "UGPA3", "USIM5", "VALE3", "VAMO3", "VBBR3",
    "VIVA3", "VIVT3", "WEGE3", "YDUQ3",
]

# Benchmark de mercado no Yahoo Finance.
SIMBOLO_IBOV = "^BVSP"


def normalizar(ticker: str) -> str:
    """'petr4.sa' -> 'PETR4'."""
    t = str(ticker).strip().upper()
    return t[:-3] if t.endswith(".SA") else t


def simbolo_yahoo(ticker: str) -> str:
    """'PETR4' -> 'PETR4.SA'; índices (^BVSP) passam direto."""
    t = normalizar(ticker)
    if t.startswith("^") or "=" in t:
        return t
    return f"{t}.SA"


def validar_tickers(tickers) -> list[str]:
    """Normaliza, remove duplicados e exige que estejam no universo."""
    vistos, saida = set(), []
    for t in tickers:
        n = normalizar(t)
        if n not in IBOVESPA:
            raise ValueError(f"Ticker fora do universo do Ibovespa: {n}")
        if n not in vistos:
            vistos.add(n)
            saida.append(n)
    if not saida:
        raise ValueError("Informe ao menos um ticker.")
    return saida
