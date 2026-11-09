"""Testes estatísticos que dizem o quanto confiar no resultado.

Todas as funções recebem retornos diários já alinhados. Quando o teste não pode ser feito (poucos
dados ou série sem variação), os campos vêm como `None`, em vez de um número enganoso.
"""
import numpy as np
import pandas as pd
from scipy import stats

from .config import SIGNIFICANCIA
from .metricas import DIAS_ANO

Z_95 = 1.96                    # intervalo de 95%


def histograma(valores, n_faixas: int = 40) -> dict:
    """Contagens por faixa, em formato leve para o gráfico."""
    v = np.asarray(valores, dtype=float)
    v = v[np.isfinite(v)]
    if len(v) == 0:
        return {"bordas": [], "contagens": []}
    contagens, bordas = np.histogram(v, bins=n_faixas)
    return {"bordas": bordas.tolist(), "contagens": contagens.tolist()}


def intervalo_confianca(excesso: pd.Series) -> dict:
    """Média ± 1,96 × erro padrão, anualizada; erro padrão = desvio ÷ √n."""
    v = pd.Series(excesso).dropna()
    if len(v) < 3:
        return {"media_anual": None, "baixo_anual": None, "alto_anual": None, "inclui_zero": None, "n": int(len(v))}
    media, erro = float(v.mean()), float(v.std(ddof=1) / np.sqrt(len(v)))
    baixo, alto = media - Z_95 * erro, media + Z_95 * erro
    return {"media_anual": media * DIAS_ANO, "baixo_anual": baixo * DIAS_ANO, "alto_anual": alto * DIAS_ANO,
            "inclui_zero": bool(baixo <= 0 <= alto), "n": int(len(v))}


def alfa_beta(retorno: pd.Series, mercado: pd.Series, rf=0.0) -> dict:
    """Regressão do excesso sobre a taxa livre de risco: y = alfa + beta × x.

    Beta = o quanto a regra acompanha o mercado. Alfa = o que sobra além disso. H0 do alfa: alfa = 0."""
    dados = pd.concat({"r": retorno, "m": mercado}, axis=1).dropna()
    rf_s = rf.reindex(dados.index).ffill().fillna(0.0) if isinstance(rf, pd.Series) else float(rf) / DIAS_ANO
    y, x = dados["r"] - rf_s, dados["m"] - rf_s
    base = {"alfa_anual": None, "beta": None, "r2": None, "p_alfa": None, "p_beta": None, "alfa_significativo": None,
            "n": int(len(y))}
    if len(y) < 3 or x.std(ddof=1) == 0 or y.std(ddof=1) == 0:
        return base
    reg = stats.linregress(x.to_numpy(), y.to_numpy())
    t_alfa = reg.intercept / reg.intercept_stderr if reg.intercept_stderr > 0 else float("nan")
    p_alfa = float(2 * stats.t.sf(abs(t_alfa), len(y) - 2))
    return {**base, "alfa_anual": float(reg.intercept) * DIAS_ANO, "beta": float(reg.slope),
            "r2": float(reg.rvalue ** 2), "p_alfa": p_alfa, "p_beta": float(reg.pvalue),
            "alfa_significativo": bool(p_alfa < SIGNIFICANCIA and reg.intercept > 0)}


def sharpe_com_desconto(sharpe_anual: float | None, n_obs: int, n_tentativas: int, ppa: int = DIAS_ANO) -> dict:
    """Sharpe ajustado pelo número de tentativas, no caso independente de Harvey & Liu (2015, equações 3 a 5).

    p^S = Pr(|t| > SR·√T) com T − 1 graus de liberdade; p^M = 1 − (1 − p^S)^N; o Sharpe ajustado é o que
    daria p^M em um teste único. `sharpe_anual` é convertido para o período da série por √ppa."""
    base = {"sharpe": sharpe_anual, "n_tentativas": int(n_tentativas), "n_obs": int(n_obs), "t": None, "p_unico": None,
            "p_ajustado": None, "sharpe_ajustado": None, "corte": None, "significativo": None}
    if sharpe_anual is None or sharpe_anual != sharpe_anual or n_obs < 3:
        return base
    gl = n_obs - 1
    t = abs(sharpe_anual) / np.sqrt(ppa) * np.sqrt(n_obs)
    p_unico = float(2 * stats.t.sf(t, gl))
    # log1p/expm1 evitam perda de precisão quando p_unico é muito pequeno
    p_ajustado = float(-np.expm1(n_tentativas * np.log1p(-min(p_unico, 1 - 1e-16))))
    t_ajustado = float(stats.t.isf(p_ajustado / 2, gl))
    positivo = sharpe_anual > 0
    ajustado = t_ajustado / np.sqrt(n_obs) * np.sqrt(ppa) if positivo else None
    return {**base, "t": float(np.sign(sharpe_anual) * t), "p_unico": p_unico, "p_ajustado": p_ajustado,
            "sharpe_ajustado": float(ajustado) if ajustado is not None else None,
            "corte": float(1 - ajustado / sharpe_anual) if positivo else None,
            "significativo": bool(positivo and p_ajustado < SIGNIFICANCIA)}



def matriz_correlacao(retornos: pd.DataFrame) -> pd.DataFrame:
    """Correlação de Pearson entre os retornos diários."""
    return retornos.corr(method="pearson")
