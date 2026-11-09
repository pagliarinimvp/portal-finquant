"""Divisão do dinheiro: fronteira, comprar e segurar e concentração."""
import numpy as np
import pandas as pd
import pytest

from quant import carteira as cart

DATAS = pd.to_datetime(["2019-12-30", "2019-12-31", "2020-01-02", "2020-01-03"])
PRECOS = pd.DataFrame({"A": [100.0, 200.0, 200.0, 400.0], "B": [100.0, 100.0, 100.0, 100.0]}, index=DATAS)
PESOS = {"A": 0.5, "B": 0.5}


def rets_exemplo(n=600, k=4, semente=3):
    rng = np.random.default_rng(semente)
    idx = pd.bdate_range("2020-01-01", periods=n)
    comum = rng.normal(0.0003, 0.008, n)
    dados = {f"T{i}": comum + rng.normal(0.0002 * i, 0.01 + 0.002 * i, n) for i in range(k)}
    return pd.DataFrame(dados, index=idx)


# ---------------------------------------------------------------- comprar e segurar
def test_os_pesos_derivam_sem_rebalancear():
    curva, ganhos = cart.curva_buy_hold(PRECOS, PESOS, 100.0)
    assert curva.iloc[-1] == pytest.approx(250.0)              # 50 em A viram 200; 50 em B ficam 50
    assert ganhos["A"] == pytest.approx(150.0) and ganhos["B"] == pytest.approx(0.0)


def test_paga_custo_na_compra_e_na_venda():
    curva, ganhos = cart.curva_buy_hold(PRECOS, PESOS, 100.0, custo_pct=1.0)
    assert curva.iloc[0] == pytest.approx(99.0)                # compra de 1%
    assert curva.iloc[1] == pytest.approx(49.5 * 2 + 49.5)     # no meio do caminho, sem nova cobrança
    assert curva.iloc[-1] == pytest.approx((49.5 * 4 + 49.5) * 0.99)    # venda de 1% no último dia
    assert sum(ganhos.values()) == pytest.approx(curva.iloc[-1] - 100.0)


# ---------------------------------------------------------------- concentração
def test_concentracao_alerta_quando_uma_acao_domina():
    r = cart.analisar_concentracao({"PRIO3": 750.0, "WEGE3": 150.0, "ITUB4": 100.0},
                                   {"PRIO3": 0.3, "WEGE3": 0.4, "ITUB4": 0.3}, 1000.0, limite=0.40)
    assert r["ticker"] == "PRIO3" and r["participacao"] == pytest.approx(0.75) and r["alerta"] is True
    assert r["retorno_sem_dominante"] == pytest.approx(250.0 / 700.0)


def test_concentracao_nao_se_aplica_a_uma_acao_ou_ganho_negativo():
    assert cart.analisar_concentracao({"A": 10.0}, {"A": 1.0}, 100.0) is None
    r = cart.analisar_concentracao({"A": -10.0, "B": -5.0}, {"A": 0.5, "B": 0.5}, 100.0)
    assert r["participacao"] is None and r["alerta"] is False


# ---------------------------------------------------------------- otimização e fronteira
def test_pesos_somam_um_e_sao_positivos():
    r = rets_exemplo()
    for metodo in ("igual", "min_variancia", "max_sharpe"):
        w = cart.otimizar(r, metodo, 0.05)
        assert w.sum() == pytest.approx(1.0) and (w >= 0).all()


def test_min_variancia_tem_menor_risco_e_max_sharpe_maior_sharpe():
    r = rets_exemplo()
    est = {m: cart.estatisticas(r, cart.otimizar(r, m, 0.05), 0.05) for m in ("igual", "min_variancia", "max_sharpe")}
    assert est["min_variancia"]["risco"] <= est["igual"]["risco"]
    assert est["max_sharpe"]["sharpe"] >= est["igual"]["sharpe"]


def test_nenhuma_carteira_aleatoria_acima_da_fronteira():
    r = rets_exemplo()
    fronteira = cart.fronteira_eficiente(r)
    riscos, retornos = np.array([p["risco"] for p in fronteira]), np.array([p["retorno"] for p in fronteira])
    assert len(fronteira) >= 10 and (np.diff(retornos) > 0).all()
    pontos = cart.monte_carlo(r, 20_000, 0.05)["pontos"]
    excesso = [p["retorno"] - np.interp(p["risco"], riscos, retornos) for p in pontos]
    assert max(excesso) < 1e-3


def test_nuvem_chega_perto_das_pontas_da_fronteira():
    """Com 10 ações, sortear e dividir pela soma deixava a nuvem presa perto das partes iguais, longe da ponta de maior retorno."""
    r = rets_exemplo(k=10)
    fronteira = cart.fronteira_eficiente(r)
    pontos = cart.monte_carlo(r, 20_000, 0.05, max_pontos=20_000)["pontos"]
    topo, base = fronteira[-1]["retorno"], fronteira[0]["retorno"]
    maior = max(p["retorno"] for p in pontos)
    assert maior >= base + 0.9 * (topo - base)


def test_carteira_sorteada_tem_pesos_que_somam_um_no_calculo():
    # com 1 ação só, toda carteira sorteada é a própria ação
    r = rets_exemplo(k=1)
    pontos = cart.monte_carlo(r, 50, 0.0)["pontos"]
    esperado = r["T0"].mean() * 252
    assert all(p["retorno"] == pytest.approx(esperado) for p in pontos)


LIMITES = [421, 511, 601]          # 601 pregões: treino inicial até o 420º retorno e 2 janelas


def test_analisar_carteira_marca_a_escolhida_e_refaz_a_divisao_em_cada_janela():
    r = rets_exemplo()
    acoes = [list(r.columns)] * 2
    out = cart.analisar_carteira(r, LIMITES, acoes, "min_variancia", 0.05, [0.05, 0.05], None, 500, 1)
    escolhidas = [c for c in out["carteiras"] if c["escolhida"]]
    assert len(escolhidas) == 1 and escolhidas[0]["nome"] == "Menor oscilação"
    c = escolhidas[0]
    p1, _ = cart.dividir(r.iloc[:420], "min_variancia", 0.05)
    p2, _ = cart.dividir(r.iloc[:510], "min_variancia", 0.05)
    assert c["pesos"] == pytest.approx(p1) and c["pesos_janelas"] == [pytest.approx(p1), pytest.approx(p2)]
    w1 = np.array(list(p1.values()))
    assert c["treino"]["retorno"] == pytest.approx(float(w1 @ r[list(p1)].iloc[:420].mean().to_numpy() * 252))
    oos = pd.concat([r[list(p1)].iloc[420:510] @ w1, r[list(p2)].iloc[510:] @ np.array(list(p2.values()))])
    assert c["teste"]["retorno"] == pytest.approx(float(oos.mean() * 252))
    assert c["teste"]["max_drawdown"] <= 0


def test_a_divisao_de_cada_janela_nao_ve_o_futuro():
    r = rets_exemplo()
    acoes = [list(r.columns)] * 2
    antes = cart.analisar_carteira(r, LIMITES, acoes, "max_sharpe", 0.05, [0.05, 0.05], None, 300, 1)
    mexido = r.copy()
    mexido.iloc[510:] *= -3                                   # muda só a última janela
    depois = cart.analisar_carteira(mexido, LIMITES, acoes, "max_sharpe", 0.05, [0.05, 0.05], None, 300, 1)
    for a, b in zip(antes["carteiras"], depois["carteiras"]):
        assert a["pesos_janelas"] == b["pesos_janelas"] and a["treino"] == b["treino"]
    assert antes["fronteira"] == depois["fronteira"]


@pytest.mark.parametrize("metodo", ["min_variancia", "max_sharpe"])
def test_nenhuma_acao_passa_de_40_por_cento(metodo):
    r = rets_exemplo(k=5)
    r["T4"] += 0.004                                          # uma ação muito melhor puxa a conta para ela
    pesos, _ = cart.dividir(r, metodo, 0.05)
    assert sum(pesos.values()) == pytest.approx(1.0)
    assert max(pesos.values()) <= cart.LIMITE_PESO + 1e-9


def test_com_duas_acoes_o_limite_nao_vale():
    r = rets_exemplo(k=2)
    r["T1"] += 0.004
    pesos, _ = cart.dividir(r, "max_sharpe", 0.05)
    assert max(pesos.values()) > cart.LIMITE_PESO             # 2 × 40% não fecha 100%
