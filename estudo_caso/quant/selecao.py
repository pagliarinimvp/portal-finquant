"""Seleção automática: as ações em que a regra foi melhor no treino, entre todas as do Ibovespa.

Tudo aqui recebe só o trecho de treino, então o período de teste não influencia a escolha. O resultado
é "a melhor no treino", não uma promessa: o teste continua sendo o juiz.
"""
import numpy as np
import pandas as pd

from . import estrategias, metricas as m
from .backtest import executar_backtest
from .config import MAX_ACOES, MEDIAS, MEDIAS_PELO_TREINO
from .dados import problemas_de_dados

MIN_OPERACOES_TREINO = 5               # escolha técnica: Sharpe com menos operações que isso é instável
FOLGA_INICIO = pd.Timedelta(days=15)   # escolha técnica: começar até aqui depois das demais não encurta a análise
FOLGA_FIM = pd.Timedelta(days=5)       # escolha técnica: dados que param antes disso encurtariam a análise de todas


def filtrar_candidatas(dados: dict[str, pd.DataFrame], ret_ibov: pd.Series | None = None) -> tuple[dict[str, pd.DataFrame], list[dict]]:
    """Separa as ações com histórico completo e confiável. As de fora trazem o motivo.

    Sem isso, uma ação listada há pouco tempo encurtaria o histórico de todas, porque a análise usa as datas comuns."""
    inicio = min(df.index[0] for df in dados.values())
    fim = max(df.index[-1] for df in dados.values())
    candidatas, fora = {}, []
    for t, df in dados.items():
        if df.index[0] > inicio + FOLGA_INICIO:
            fora.append({"ticker": t, "motivo": f"o histórico só começa em {df.index[0].strftime('%d/%m/%Y')}"})
        elif df.index[-1] < fim - FOLGA_FIM:
            fora.append({"ticker": t, "motivo": f"os dados param em {df.index[-1].strftime('%d/%m/%Y')}"})
        else:
            problemas = problemas_de_dados(df, ret_ibov)
            if problemas:
                fora.append({"ticker": t, "motivo": problemas[0]})
            else:
                candidatas[t] = df
    return candidatas, fora


def _retornos_com_caixa(equity: pd.Series, posicao: pd.Series, rf) -> pd.Series:
    """Retornos com o caixa rendendo a taxa livre de risco nos dias totalmente fora do mercado.

    Vale só para dar a nota: sem isso, o Sharpe desconta a Selic de um caixa que não rende e castiga
    os ritmos que ficam menos tempo comprados. A simulação exibida na página não usa esta conta."""
    r = equity.pct_change().dropna()
    if not isinstance(rf, pd.Series):
        return r
    fora = (posicao == 0) & (posicao.shift(1).fillna(0) == 0)
    return r + rf.reindex(r.index).fillna(0.0).where(fora.reindex(r.index), 0.0)


def _nota(df: pd.DataFrame, curta: int, longa: int, capital: float, stop, alvo, custo_pct: float, rf) -> dict:
    res = executar_backtest(df, estrategias.gerar_sinais(df, curta, longa), capital, stop, alvo, custo_pct)
    s = m.sharpe(_retornos_com_caixa(res.equity, res.posicao, rf), rf)
    return {"sharpe_treino": None if s != s else s, "n_trades": int(len(res.trades))}


def _aprovadas(notas: dict[str, dict], max_acoes: int) -> list[str]:
    """As melhores notas positivas, com operações suficientes. Empate: ordem alfabética, para repetir o resultado."""
    validas = [t for t, n in notas.items() if n["n_trades"] >= MIN_OPERACOES_TREINO and (n["sharpe_treino"] or 0) > 0]
    return sorted(validas, key=lambda t: (-notas[t]["sharpe_treino"], t))[:max_acoes]


def selecionar(dfs: dict[str, pd.DataFrame], corte: int, medias: str, stop, alvo, custo_pct: float, capital: float, rf,
               max_acoes: int = MAX_ACOES) -> dict:
    """Escolhe as ações, e o ritmo se for o caso, olhando só os `corte` primeiros pregões."""
    treino = {t: df.iloc[:corte] for t, df in dfs.items()}
    capital_por_acao = capital / max_acoes
    ritmos = MEDIAS if medias == MEDIAS_PELO_TREINO else {medias: MEDIAS[medias]}
    notas_por_ritmo, pontuacao = {}, []
    for chave, md in ritmos.items():
        notas = {t: _nota(df, md["curta"], md["longa"], capital_por_acao, stop, alvo, custo_pct, rf) for t, df in treino.items()}
        notas_por_ritmo[chave] = notas
        melhores = _aprovadas(notas, max_acoes)
        media = float(np.mean([notas[t]["sharpe_treino"] for t in melhores])) if melhores else None
        pontuacao.append({"medias": chave, "curta": md["curta"], "longa": md["longa"], "sharpe_treino": media, "n_aprovadas": len(melhores)})
    com_nota = [p for p in pontuacao if p["sharpe_treino"] is not None]
    if not com_nota:
        raise ValueError("Nenhuma ação teve retorno pelo risco positivo no treino, com ao menos "
                         f"{MIN_OPERACOES_TREINO} operações. Mude o ritmo, a saída automática, o custo ou o capital.")
    vencedor = max(com_nota, key=lambda p: p["sharpe_treino"])["medias"]
    notas = notas_por_ritmo[vencedor]
    escolhidas = _aprovadas(notas, max_acoes)
    ranking = [{"ticker": t, **n, "selecionada": t in escolhidas}
               for t, n in sorted(notas.items(), key=lambda x: (-(x[1]["sharpe_treino"] if x[1]["sharpe_treino"] is not None else -np.inf), x[0]))]
    return {"tickers": escolhidas, "ritmo": vencedor, "pontuacao_ritmos": pontuacao, "ranking": ranking}
