"""A divisão do dinheiro: pesos, fronteira eficiente de Markowitz e promessa × realidade.

Base: Markowitz (1952).
Retornos esperados e covariância são amostrais, anualizados por 252. Pesos e fronteira usam só o treino.
Nas divisões otimizadas, cada ação fica com no máximo `LIMITE_PESO`: pesos estimados com o passado erram, e a otimização
sem limite tende a concentrar o dinheiro na ação que mais subiu (DeMiguel, Garlappi e Uppal, 2009).
"""
import numpy as np
import pandas as pd
from scipy.optimize import minimize

from . import metricas as m
from .config import DIVISOES, LIMITE_PESO, PESO_MINIMO

DIAS_ANO = m.DIAS_ANO
LIMITE_CONCENTRACAO = 0.40          # escolha técnica: uma ação acima disso do ganho total gera aviso
CONCENTRACAO_NUVEM = (1.0, 0.3, 0.1)  # escolha técnica: do sorteio espalhado ao concentrado, em partes iguais da nuvem


# --------------------------------------------------------------------------- básicos
def retorno_carteira(rets: pd.DataFrame, pesos: np.ndarray) -> pd.Series:
    """Soma ponderada dos retornos diários, com pesos constantes."""
    return (rets * pesos).sum(axis=1)


def estatisticas_serie(r: pd.Series, rf=0.0) -> dict:
    """Retorno médio, oscilação, Sharpe, queda máxima e retorno total de uma série de retornos diários."""
    ret_a, vol = float(r.mean() * DIAS_ANO), float(r.std(ddof=1) * np.sqrt(DIAS_ANO))
    rf_a = float(rf.reindex(r.index).ffill().fillna(0.0).mean() * DIAS_ANO) if isinstance(rf, pd.Series) else float(rf)
    curva = (1.0 + r).cumprod()
    curva = pd.concat([pd.Series([1.0], index=[r.index[0] - pd.Timedelta(days=1)]), curva])
    return {"retorno": ret_a, "risco": vol, "sharpe": (ret_a - rf_a) / vol if vol > 0 else float("nan"),
            "max_drawdown": m.max_drawdown(curva), "retorno_total": float(curva.iloc[-1] - 1.0)}


def estatisticas(rets: pd.DataFrame, pesos: np.ndarray, rf=0.0) -> dict:
    """Retorno, volatilidade √(wᵀΣw) e Sharpe anualizados."""
    mu = rets.mean().to_numpy() * DIAS_ANO
    cov = rets.cov().to_numpy() * DIAS_ANO
    ret_a = float(pesos @ mu)
    vol = float(np.sqrt(pesos @ cov @ pesos))
    rf_a = float(rf.reindex(rets.index).ffill().fillna(0.0).mean() * DIAS_ANO) if isinstance(rf, pd.Series) else float(rf)
    return {"retorno": ret_a, "risco": vol, "sharpe": (ret_a - rf_a) / vol if vol > 0 else float("nan")}


# --------------------------------------------------------------------------- otimização
def otimizar(rets: pd.DataFrame, metodo: str, rf_anual: float = 0.0, teto: float = 1.0) -> np.ndarray:
    """Pesos só comprados, de 0 a `teto` em cada ação: partes iguais, mínima variância ou máximo Sharpe (SLSQP)."""
    n = rets.shape[1]
    if metodo == "igual":
        return np.full(n, 1.0 / n)
    mu = rets.mean().to_numpy() * DIAS_ANO
    cov = rets.cov().to_numpy() * DIAS_ANO
    if metodo == "min_variancia":
        objetivo = lambda w: w @ cov @ w  # noqa: E731
    elif metodo == "max_sharpe":
        objetivo = lambda w: -(w @ mu - rf_anual) / np.sqrt(max(w @ cov @ w, 1e-16))  # noqa: E731
    else:
        raise ValueError(f"Método de pesos desconhecido: {metodo}")
    w0 = np.full(n, 1.0 / n)
    res = minimize(objetivo, w0, method="SLSQP", bounds=[(0.0, teto)] * n,
                   constraints=({"type": "eq", "fun": lambda w: w.sum() - 1.0},),
                   options={"maxiter": 500, "ftol": 1e-10})
    w = np.clip(res.x if res.success else w0, 0, None)
    return w / w.sum()


def teto_de(n: int, metodo: str) -> float:
    """O limite por ação. Com 1 ou 2 ações ele seria impossível (2 × 40% não chega a 100%), e partes iguais não precisam dele."""
    return LIMITE_PESO if metodo != "igual" and n * LIMITE_PESO >= 1.0 else 1.0


def _redistribuir(w: np.ndarray, teto: float) -> np.ndarray:
    """Soma 100% sem passar do teto: o que sobra acima dele vai para as demais, na proporção dos pesos delas."""
    w = w / w.sum()
    for _ in range(len(w)):
        acima = w > teto + 1e-12
        if not acima.any():
            break
        sobra = float((w[acima] - teto).sum())
        w[acima] = teto
        livres = w < teto - 1e-12
        w[livres] += sobra * w[livres] / w[livres].sum()
    return w


def dividir(rets: pd.DataFrame, metodo: str, rf_anual: float = 0.0) -> tuple[dict, list[str]]:
    """Os pesos de uma divisão e as ações que ficaram sem dinheiro (peso abaixo de `PESO_MINIMO`)."""
    cols = list(rets.columns)
    teto = teto_de(len(cols), metodo)
    w = otimizar(rets, metodo, rf_anual, teto)
    mantem = w >= PESO_MINIMO
    if teto < 1.0 and mantem.sum() * teto < 1.0:       # sem ações suficientes para respeitar o teto
        teto = 1.0
    w = _redistribuir(w[mantem], teto)
    return {t: float(x) for t, x in zip([c for c, k in zip(cols, mantem) if k], w)}, [c for c, k in zip(cols, mantem) if not k]


def fronteira_eficiente(rets: pd.DataFrame, n_pontos: int = 25, teto: float = 1.0) -> list[dict]:
    """Para cada retorno-alvo, a carteira de menor risco, com no máximo `teto` em cada ação."""
    n = rets.shape[1]
    mu = rets.mean().to_numpy() * DIAS_ANO
    cov = rets.cov().to_numpy() * DIAS_ANO
    w_min = otimizar(rets, "min_variancia", teto=teto)
    pontos, w0 = [], w_min
    topo = float(np.sort(mu)[::-1] @ _maior_mistura(n, teto))    # o maior retorno possível respeitando o teto
    for alvo in np.linspace(float(w_min @ mu), topo, n_pontos):
        cons = ({"type": "eq", "fun": lambda w: w.sum() - 1.0},
                {"type": "eq", "fun": lambda w, a=alvo: w @ mu - a})
        r = minimize(lambda w: w @ cov @ w, w0, method="SLSQP", bounds=[(0.0, teto)] * n, constraints=cons,
                     options={"maxiter": 300, "ftol": 1e-10})
        if r.success:
            w0 = r.x
            pontos.append({"risco": float(np.sqrt(r.x @ cov @ r.x)), "retorno": float(alvo)})
    return pontos


def _maior_mistura(n: int, teto: float) -> np.ndarray:
    """Pesos, em ordem decrescente, da carteira de maior retorno: o teto nas melhores ações e o resto na seguinte."""
    w, falta = np.zeros(n), 1.0
    for i in range(n):
        w[i] = min(teto, falta)
        falta -= w[i]
    return w


def monte_carlo(rets: pd.DataFrame, n: int = 20_000, rf_anual: float = 0.0, semente: int = 42,
                max_pontos: int = 1500, teto: float = 1.0) -> dict:
    """Carteiras de pesos aleatórios, sorteados pela distribuição de Dirichlet.

    Sortear um número por ação e dividir pela soma junta quase todas as carteiras perto das partes iguais: com 10 ações,
    uma carteira com 70% numa ação praticamente não aparece. Por isso um terço da nuvem é sorteado de forma espalhada
    (parâmetro 1, que cobre por igual todas as divisões possíveis) e dois terços de forma cada vez mais concentrada
    (0,3 e 0,1), para a nuvem chegar perto das pontas da fronteira. Com `teto`, ficam só as carteiras que o respeitam,
    as mesmas que a fronteira considera."""
    rng = np.random.default_rng(semente)
    k = rets.shape[1]
    mu = rets.mean().to_numpy() * DIAS_ANO
    cov = rets.cov().to_numpy() * DIAS_ANO
    partes = np.array_split(np.arange(n), len(CONCENTRACAO_NUVEM))
    blocos = []
    for a, p in zip(CONCENTRACAO_NUVEM, partes):
        aceitas, tentativas = [], 0
        while sum(len(x) for x in aceitas) < len(p) and tentativas < 50:
            lote = rng.dirichlet(np.full(k, a), size=len(p))
            aceitas.append(lote[lote.max(axis=1) <= teto + 1e-12])
            tentativas += 1
        blocos.append(np.vstack(aceitas)[:len(p)])
    w = np.vstack(blocos)
    n = len(w)
    ret = w @ mu
    vol = np.sqrt(np.einsum("ij,jk,ik->i", w, cov, w))
    sh = (ret - rf_anual) / vol
    sel = rng.choice(n, size=min(max_pontos, n), replace=False)
    return {"n": int(n),
            "pontos": [{"risco": float(vol[i]), "retorno": float(ret[i]), "sharpe": float(sh[i])} for i in sel]}


# --------------------------------------------------------------------------- promessa × realidade
def _avaliar(nome: str, rets: pd.DataFrame, limites: list[int], acoes: list[list[str]], metodo: str, rf, rf_anuais: list[float],
             escolhida: bool) -> dict:
    """O que a divisão prometia no treino inicial e o que entregou nas janelas de teste, refeita antes de cada uma.

    `rets.iloc[j]` é o retorno do pregão j + 1, então a janela que começa no pregão a usa `rets.iloc[a − 1:b − 1]`."""
    oos, pesos_janelas = [], []
    for k, (a, b) in enumerate(zip(limites[:-1], limites[1:])):
        trecho = rets.iloc[a - 1:b - 1]
        if not acoes[k]:
            oos.append(pd.Series(0.0, index=trecho.index))
            pesos_janelas.append({})
            continue
        p, _ = dividir(rets[acoes[k]].iloc[:a - 1], metodo, rf_anuais[k])
        pesos_janelas.append(p)
        oos.append(retorno_carteira(trecho[list(p)], np.array(list(p.values()))))
    p1 = pesos_janelas[0]
    rets_tr = rets[list(p1)].iloc[:limites[0] - 1]
    return {"nome": nome, "escolhida": escolhida, "pesos": p1, "pesos_janelas": pesos_janelas,
            "treino": estatisticas(rets_tr, np.array(list(p1.values())), rf), "teste": estatisticas_serie(pd.concat(oos), rf)}


def analisar_carteira(rets: pd.DataFrame, limites: list[int], acoes: list[list[str]], divisao: str, rf, rf_anuais: list[float],
                      ret_ibov: pd.Series | None, n_carteiras: int, semente: int) -> dict:
    """Fronteira, nuvem e correlação no treino inicial; cada divisão com o que prometeu e entregou no teste.

    `acoes[k]` são as ações da janela k antes do peso mínimo. A fronteira avalia só a alocação entre ações compradas e
    mantidas, sem a regra de médias."""
    rets_tr = rets[acoes[0]].iloc[:limites[0] - 1]
    rets_te = rets.iloc[limites[0] - 1:]
    carteiras = [_avaliar(info["rotulo"], rets, limites, acoes, chave, rf, rf_anuais, chave == divisao) for chave, info in DIVISOES.items()]
    ibov = None
    if ret_ibov is not None:
        ib_tr, ib_te = ret_ibov.reindex(rets_tr.index).to_frame("Ibovespa"), ret_ibov.reindex(rets_te.index).to_frame("Ibovespa")
        unico = np.array([1.0])
        ibov = {"nome": "Ibovespa", "treino": estatisticas(ib_tr, unico, rf), "teste": estatisticas(ib_te, unico, rf)}
    try:
        fronteira = fronteira_eficiente(rets_tr, teto=teto_de(rets_tr.shape[1], divisao))
    except ValueError:
        fronteira = []
    return {
        "carteiras": carteiras, "ibovespa": ibov, "fronteira": fronteira,
        "nuvem": monte_carlo(rets_tr, n_carteiras, rf_anuais[0], semente, teto=teto_de(rets_tr.shape[1], divisao)),
        "tickers": list(rets_tr.columns),
    }


# --------------------------------------------------------------------------- comprar e segurar
def curva_buy_hold(precos: pd.DataFrame, pesos: dict, capital: float, custo_pct: float = 0.0) -> tuple[pd.Series, dict]:
    """Patrimônio de comprar no primeiro dia e vender no último, sem rebalancear, e o ganho de cada ação.

    Paga uma compra e uma venda, para comparar com a regra em condições iguais."""
    custo = custo_pct / 100.0
    cols = list(precos.columns)
    w = np.array([float(pesos[c]) for c in cols])
    investido = capital * w
    fator = (precos[cols] / precos[cols].iloc[0]).to_numpy(float)
    valores = (investido * (1.0 - custo)) * fator
    valores[-1] = valores[-1] * (1.0 - custo)
    total = valores.sum(axis=1)
    ganhos = {c: float(valores[-1, i] - investido[i]) for i, c in enumerate(cols)}
    return pd.Series(total, index=precos.index, name="buy_hold"), ganhos


def analisar_concentracao(ganhos: dict, pesos: dict, capital: float, limite: float = LIMITE_CONCENTRACAO):
    """Quanto do ganho total vem da ação que mais contribuiu, e o retorno sem ela. None com menos de 2 ações."""
    if len(ganhos) < 2:
        return None
    total = sum(ganhos.values())
    topo = max(ganhos, key=ganhos.get)
    restante = capital * (1.0 - float(pesos[topo]))
    ok = total > 0
    return {
        "ticker": topo,
        "participacao": ganhos[topo] / total if ok else None,
        "retorno_total": total / capital,
        "retorno_sem_dominante": (total - ganhos[topo]) / restante if restante > 0 else None,
        "alerta": bool(ok and ganhos[topo] / total > limite),
    }
