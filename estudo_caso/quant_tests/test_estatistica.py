"""Testes estatísticos conferidos contra contas feitas à parte e casos conhecidos."""
import numpy as np
import pandas as pd
import pytest
from scipy import stats

from quant import estatistica as est

IDX = pd.bdate_range("2020-01-01", periods=5)


# ---------------------------------------------------------------- intervalo de confiança como prova de "não foi sorte"
def test_intervalo_em_series_sem_vantagem_passa_em_cerca_de_2_5_por_cento():
    """Sem vantagem real, a faixa inteira fica acima de zero só por acaso em cerca de 2,5% das vezes (o lado de cima de 95%)."""
    rng = np.random.default_rng(7)
    n, passou = 2000, 0
    for _ in range(n):
        passou += est.intervalo_confianca(pd.Series(rng.normal(0, 0.01, 250)))["baixo_anual"] > 0
    assert passou / n == pytest.approx(0.025, abs=0.01)


def test_intervalo_detecta_vantagem_grande():
    rng = np.random.default_rng(1)
    ic = est.intervalo_confianca(pd.Series(0.002 + rng.normal(0, 0.002, 750)))
    assert ic["baixo_anual"] > 0 and ic["inclui_zero"] is False


# ---------------------------------------------------------------- intervalo de confiança
def test_intervalo_contra_conta_manual():
    r = est.intervalo_confianca(pd.Series([0.01, 0.02, 0.03, 0.04, 0.05]))
    erro = 0.0158114 / np.sqrt(5)
    assert r["media_anual"] == pytest.approx(0.03 * 252)
    assert r["baixo_anual"] == pytest.approx((0.03 - 1.96 * erro) * 252, rel=1e-4)
    assert r["alto_anual"] == pytest.approx((0.03 + 1.96 * erro) * 252, rel=1e-4)
    assert r["inclui_zero"] is False


def test_intervalo_inclui_zero():
    assert est.intervalo_confianca(pd.Series([-0.02, 0.02, -0.01, 0.01, 0.0]))["inclui_zero"] is True


# ---------------------------------------------------------------- alfa e beta
def test_alfa_e_beta_em_dados_construidos():
    rng = np.random.default_rng(2)
    idx = pd.bdate_range("2020-01-01", periods=1000)
    rf = pd.Series(0.0004, index=idx)
    mercado = pd.Series(rng.normal(0.0005, 0.012, 1000), index=idx)
    alfa, beta = 0.0008, 0.6
    r = rf + alfa + beta * (mercado - rf) + rng.normal(0, 0.0005, 1000)
    res = est.alfa_beta(r, mercado, rf)
    assert res["beta"] == pytest.approx(beta, abs=0.01)
    assert res["alfa_anual"] == pytest.approx(alfa * 252, abs=0.02)
    assert res["alfa_significativo"] is True and res["r2"] > 0.9


def test_sem_alfa_nao_e_significativo():
    rng = np.random.default_rng(5)
    idx = pd.bdate_range("2020-01-01", periods=750)
    mercado = pd.Series(rng.normal(0.0005, 0.012, 750), index=idx)
    res = est.alfa_beta(0.9 * mercado + rng.normal(0, 0.008, 750), mercado, 0.0)
    assert res["alfa_significativo"] is False


def test_alfa_sem_variacao_nao_inventa_numero():
    idx = pd.bdate_range("2020-01-01", periods=30)
    assert est.alfa_beta(pd.Series(0.0, index=idx), pd.Series(np.arange(30.0), index=idx), 0.0)["beta"] is None


# ---------------------------------------------------------------- Sharpe com desconto (Harvey & Liu, 2015)
def test_uma_tentativa_nao_tem_desconto():
    r = est.sharpe_com_desconto(0.8, 750, 1)
    assert r["p_ajustado"] == pytest.approx(r["p_unico"])
    assert r["sharpe_ajustado"] == pytest.approx(0.8) and r["corte"] == pytest.approx(0.0, abs=1e-9)


def test_desconto_cresce_com_o_numero_de_tentativas():
    ajustados = [est.sharpe_com_desconto(1.0, 750, n)["sharpe_ajustado"] for n in (1, 4, 16, 64)]
    assert ajustados == sorted(ajustados, reverse=True) and ajustados[-1] < ajustados[0]


def test_formula_p_ajustado_do_artigo():
    # Equação 4, exemplo do artigo: N = 10 e p único de 0,05 dão p ajustado de 0,401
    assert 1 - (1 - 0.05) ** 10 == pytest.approx(0.401, abs=0.001)
    t = stats.t.isf(0.05 / 2, 749)
    r = est.sharpe_com_desconto(t * np.sqrt(252 / 750), 750, 10)
    assert r["p_unico"] == pytest.approx(0.05, abs=1e-6) and r["p_ajustado"] == pytest.approx(0.401, abs=0.001)


def test_exemplo_numerico_do_artigo():
    # 240 meses, Sharpe anual de 0,75 e 200 tentativas: o artigo chega a cerca de 0,32 (corte de cerca de 60%)
    r = est.sharpe_com_desconto(0.75, 240, 200, ppa=12)
    assert r["sharpe_ajustado"] == pytest.approx(0.32, abs=0.03)
    assert r["corte"] == pytest.approx(0.6, abs=0.05)


def test_sharpe_negativo_nao_tem_ajuste():
    r = est.sharpe_com_desconto(-0.5, 750, 16)
    assert r["sharpe_ajustado"] is None and r["significativo"] is False


def test_desconto_sem_sharpe():
    assert est.sharpe_com_desconto(None, 750, 16)["p_ajustado"] is None


