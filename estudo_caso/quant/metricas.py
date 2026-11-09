"""Métricas de retorno, risco e do sistema de trading.

Convenção: 252 pregões por ano (`DIAS_ANO`). `rf` pode ser um número (taxa anual) ou uma série de
taxa livre de risco por dia (a Selic), alinhada aos retornos.
"""
import numpy as np
import pandas as pd

DIAS_ANO = 252
MOTIVOS_SAIDA = ("sinal", "stop", "alvo", "fim_janela", "fim_dados")


# --------------------------------------------------------------------------- retorno
def cagr(curva: pd.Series) -> float:
    """Retorno anualizado composto: (final/inicial)^(1/anos) − 1."""
    curva = curva.dropna()
    if len(curva) < 2 or curva.iloc[0] <= 0:
        return float("nan")
    anos = (curva.index[-1] - curva.index[0]).total_seconds() / (365.25 * 86400)
    if anos <= 0:
        return float("nan")
    razao = curva.iloc[-1] / curva.iloc[0]
    return float(razao ** (1.0 / anos) - 1.0) if razao > 0 else -1.0


def volatilidade_anual(ret: pd.Series) -> float:
    """Desvio padrão (n−1) anualizado por √252."""
    return float(ret.std(ddof=1) * np.sqrt(DIAS_ANO)) if len(ret) > 1 else float("nan")


# --------------------------------------------------------------------------- risco
def _rf_dia(ret: pd.Series, rf) -> pd.Series:
    if isinstance(rf, pd.Series):
        return rf.reindex(ret.index).ffill().fillna(0.0)
    return pd.Series((1.0 + float(rf)) ** (1.0 / DIAS_ANO) - 1.0, index=ret.index)


def sharpe(ret: pd.Series, rf=0.0) -> float:
    """(retorno anualizado médio − taxa livre de risco) ÷ volatilidade anualizada."""
    ret = ret.dropna()
    if len(ret) < 2:
        return float("nan")
    vol = ret.std(ddof=1) * np.sqrt(DIAS_ANO)
    if vol == 0 or np.isnan(vol):
        return float("nan")
    return float((ret.mean() - _rf_dia(ret, rf).mean()) * DIAS_ANO / vol)


def conta_sharpe(ret: pd.Series, rf=0.0) -> dict:
    """As parcelas do Sharpe, para mostrar a conta. O retorno médio é a média simples × 252, e não o retorno composto ao ano."""
    ret = ret.dropna()
    if len(ret) < 2:
        return {"retorno_medio_anual": None, "selic_media_anual": None, "excesso_anual": None, "oscilacao_anual": None, "sharpe": None}
    media, taxa = float(ret.mean() * DIAS_ANO), float(_rf_dia(ret, rf).mean() * DIAS_ANO)
    return {"retorno_medio_anual": media, "selic_media_anual": taxa, "excesso_anual": media - taxa,
            "oscilacao_anual": float(ret.std(ddof=1) * np.sqrt(DIAS_ANO)), "sharpe": sharpe(ret, rf)}


def sortino(ret: pd.Series, rf=0.0) -> float:
    """Como o Sharpe, mas só os dias abaixo da taxa livre de risco contam como risco (Sortino e Price, 1994)."""
    ret = ret.dropna()
    if len(ret) < 2:
        return float("nan")
    excesso = ret - _rf_dia(ret, rf)
    risco = float(np.sqrt((excesso.clip(upper=0.0) ** 2).mean()) * np.sqrt(DIAS_ANO))
    return float(excesso.mean() * DIAS_ANO / risco) if risco > 0 else float("nan")


def drawdown(curva: pd.Series) -> pd.Series:
    """Queda percentual desde o pico acumulado. Valores <= 0."""
    return curva / curva.expanding(min_periods=1).max() - 1.0


def max_drawdown(curva: pd.Series) -> float:
    dd = drawdown(curva)
    return float(dd.min()) if len(dd) else float("nan")


def desempenho(curva: pd.Series, rf=0.0) -> dict:
    """Métricas de retorno e risco a partir de uma curva de patrimônio ou preço."""
    ret = curva.pct_change().dropna()
    retorno_ano, queda = cagr(curva), max_drawdown(curva)
    return {
        "retorno_total": float(curva.iloc[-1] / curva.iloc[0] - 1.0),
        "retorno_anualizado": retorno_ano,
        "volatilidade_anual": volatilidade_anual(ret),
        "sharpe": sharpe(ret, rf),
        "sortino": sortino(ret, rf),
        "max_drawdown": queda,
        "retorno_por_queda": retorno_ano / abs(queda) if queda < 0 else float("nan"),
    }


# --------------------------------------------------------------------------- sistema de trading
def metricas_trading(trades: pd.DataFrame) -> dict:
    """Métricas do sistema."""
    n = len(trades)
    base = {
        "n_trades": n, "win_rate": float("nan"), "ganho_medio": float("nan"), "perda_media": float("nan"),
        "payoff": float("nan"), "fator_lucro": float("nan"), "expectancia": float("nan"),
        "break_even": float("nan"), "edge": float("nan"), "melhor_trade": float("nan"), "pior_trade": float("nan"),
        "duracao_media": float("nan"), "maior_sequencia_perdas": 0, "resultado_liquido": 0.0,
        "n_ganhos": 0, "n_perdas": 0, "maior_ganho": float("nan"), "maior_perda": float("nan"),
        "maior_ganho_pct": float("nan"), "maior_perda_pct": float("nan"),
        "saidas": {motivo: 0 for motivo in MOTIVOS_SAIDA},
    }
    if n == 0:
        return base
    pnl = trades["pnl"].to_numpy(float)
    ganhos, perdas = pnl[pnl > 0], pnl[pnl < 0]
    if "retorno_pct" in trades:                # em %: compara operações feitas com capitais diferentes
        pct = trades["retorno_pct"].to_numpy(float)
        base["maior_ganho_pct"] = float(pct[pct > 0].max()) if (pct > 0).any() else float("nan")
        base["maior_perda_pct"] = float(pct[pct < 0].min()) if (pct < 0).any() else float("nan")
    if "motivo" in trades:
        base["saidas"] = {motivo: int((trades["motivo"] == motivo).sum()) for motivo in MOTIVOS_SAIDA}
    win = len(ganhos) / n
    ganho_medio = float(ganhos.mean()) if len(ganhos) else 0.0
    perda_media = float(abs(perdas.mean())) if len(perdas) else 0.0
    payoff = ganho_medio / perda_media if perda_media > 0 else float("nan")
    # Edge = taxa de acerto − break-even; break-even = 1/(1 + retorno/risco)
    break_even = 1.0 / (1.0 + payoff) if payoff == payoff and payoff > 0 else float("nan")
    seq = maxseq = 0
    for p in pnl:
        seq = seq + 1 if p < 0 else 0
        maxseq = max(maxseq, seq)
    base.update({
        "win_rate": win, "ganho_medio": ganho_medio, "perda_media": perda_media, "payoff": payoff,
        "fator_lucro": float(ganhos.sum() / abs(perdas.sum())) if len(perdas) else float("nan"),
        "expectancia": win * ganho_medio - (1 - win) * perda_media,
        "break_even": break_even,
        "edge": win - break_even if break_even == break_even else float("nan"),
        "melhor_trade": float(pnl.max()), "pior_trade": float(pnl.min()),
        "duracao_media": float(trades["barras"].mean()),
        "maior_sequencia_perdas": int(maxseq), "resultado_liquido": float(pnl.sum()),
        "n_ganhos": int(len(ganhos)), "n_perdas": int(len(perdas)),
        "maior_ganho": float(ganhos.max()) if len(ganhos) else float("nan"),
        "maior_perda": float(perdas.min()) if len(perdas) else float("nan"),
    })
    return base
