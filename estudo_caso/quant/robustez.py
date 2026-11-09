"""O resultado aguenta variações? Recortes de treino e teste, ano a ano e ordem dos trades.

As combinações de ritmo, saída e custo rodam pelas mesmas janelas da análise, em `janelas.py`. Os números de treino
e teste são recortes de uma única curva, para que os valores sempre batam entre si.
"""
import numpy as np
import pandas as pd

from . import estatistica as est
from .config import N_SIMULACOES, SEMENTE

MIN_PREGOES_ANO = 126          # escolha técnica: meio ano; menos que isso não representa o ano


def recorte_treino(serie: pd.Series, corte: int) -> pd.Series:
    return serie.iloc[:corte]


def recorte_teste(serie: pd.Series, corte: int) -> pd.Series:
    """Começa no último fechamento do treino, para o primeiro retorno do teste existir."""
    return serie.iloc[corte - 1:]


def ano_a_ano(retornos: dict[str, pd.Series], nome_principal: str = "estrategia", nome_ref: str = "selic") -> dict:
    """Retorno composto por ano civil para cada série.

    Anos com menos de `MIN_PREGOES_ANO` pregões aparecem na tabela, mas não entram na contagem."""
    tabela = pd.DataFrame({k: (1.0 + v).groupby(v.index.year).prod() - 1.0 for k, v in retornos.items()})
    dias = next(iter(retornos.values())).groupby(next(iter(retornos.values())).index.year).size()
    anos = []
    for ano, linha in tabela.iterrows():
        d = {"ano": int(ano), "pregoes": int(dias.loc[ano]), **{k: float(v) for k, v in linha.items()}}
        completo = nome_ref in tabela and dias.loc[ano] >= MIN_PREGOES_ANO
        d["acima_ref"] = bool(linha[nome_principal] > linha[nome_ref]) if completo else None
        anos.append(d)
    avaliados = [a for a in anos if a["acima_ref"] is not None]
    n_acima = sum(a["acima_ref"] for a in avaliados)
    return {"anos": anos, "n_acima": int(n_acima), "n_avaliados": len(avaliados)}


def _retornos_dos_trades(trades: pd.DataFrame, capital: float) -> np.ndarray:
    """Cada trade como retorno sobre o patrimônio da época, reconstruído em ordem cronológica."""
    patrimonio, r = capital, []
    for p in trades["pnl"].to_numpy(float):
        r.append(p / patrimonio)
        patrimonio += p
    return np.array(r)


def _queda_maxima(curvas: np.ndarray, capital: float) -> np.ndarray:
    """Maior queda de cada linha de `curvas`, contando o capital inicial como primeiro pico."""
    inicio = np.full((curvas.shape[0], 1), capital)
    picos = np.maximum.accumulate(np.concatenate([inicio, curvas], axis=1), axis=1)[:, 1:]
    return (curvas / picos - 1.0).min(axis=1)


def monte_carlo_ordem(trades: pd.DataFrame, capital: float, n_sim: int = N_SIMULACOES, semente: int = SEMENTE,
                      tamanho_lote: int = 500) -> dict | None:
    """Embaralha a ordem dos trades.

    As mesmas operações em outra ordem chegam ao mesmo resultado final; o que muda é o caminho.
    Percentil 5% = cenário razoavelmente pessimista. Roda em lotes para caber na memória do Portal."""
    if len(trades) < 5:
        return None
    r = _retornos_dos_trades(trades, capital)
    fatores = 1.0 + r
    observado = float(_queda_maxima((capital * np.cumprod(fatores)).reshape(1, -1), capital)[0])
    rng = np.random.default_rng(semente)
    quedas = []
    final = float(np.prod(fatores) - 1.0)
    for ini in range(0, n_sim, tamanho_lote):
        k = min(tamanho_lote, n_sim - ini)
        ordem = rng.permuted(np.tile(np.arange(len(r)), (k, 1)), axis=1)
        quedas.append(_queda_maxima(capital * np.cumprod(fatores[ordem], axis=1), capital))
    mdd = np.concatenate(quedas)
    return {
        "n_trades": int(len(r)), "n_simulacoes": int(n_sim), "resultado_final": final,
        "queda_observada": observado, "queda_mediana": float(np.percentile(mdd, 50)),
        "queda_pessimista": float(np.percentile(mdd, 5)),
        "pct_pior_que_observada": float((mdd < observado).mean()),
        "histograma": est.histograma(100.0 * mdd, 40),
    }


def sem_melhores_trades(trades: pd.DataFrame, capital: float, k: int = 3) -> dict | None:
    """Resultado em R$ com e sem os `k` melhores trades."""
    if len(trades) <= k:
        return None
    pnl = np.sort(trades["pnl"].to_numpy(float))
    total, sem = float(pnl.sum()), float(pnl[:-k].sum())
    return {"k": int(k), "resultado_total": total, "resultado_sem": sem, "retorno_total": total / capital,
            "retorno_sem": sem / capital, "ainda_positivo": bool(sem > 0)}
