"""Recortes de treino e teste, ano a ano, embaralhamento da ordem e resultado sem os melhores trades."""
import itertools

import numpy as np
import pandas as pd
import pytest

from quant import robustez as rob


def trades(pnl):
    return pd.DataFrame({"pnl": np.array(pnl, dtype=float)})


# ---------------------------------------------------------------- embaralhamento da ordem
def test_toda_ordem_chega_ao_mesmo_resultado_final():
    pnl = [1000, -500, 2000, -1500, 800, -200, 1200]
    r = rob._retornos_dos_trades(trades(pnl), 100_000)
    esperado = (100_000 + sum(pnl)) / 100_000 - 1
    assert np.prod(1 + r) - 1 == pytest.approx(esperado)
    rng = np.random.default_rng(1)
    for _ in range(50):
        assert np.prod(1 + rng.permutation(r)) - 1 == pytest.approx(esperado)
    assert rob.monte_carlo_ordem(trades(pnl), 100_000, 1000)["resultado_final"] == pytest.approx(esperado)


def test_percentil_confere_com_todas_as_ordens_em_um_caso_pequeno():
    pnl = [1000, -2000, 1500, -500, 700]
    capital = 10_000
    r = rob._retornos_dos_trades(trades(pnl), capital)
    todas = np.array(list(itertools.permutations(r)))
    curvas = capital * np.cumprod(1 + todas, axis=1)
    quedas = rob._queda_maxima(curvas, capital)
    mc = rob.monte_carlo_ordem(trades(pnl), capital, 20_000)
    assert mc["queda_pessimista"] == pytest.approx(np.percentile(quedas, 5), abs=0.01)
    assert mc["queda_mediana"] == pytest.approx(np.percentile(quedas, 50), abs=0.01)
    assert mc["queda_pessimista"] <= mc["queda_mediana"] <= 0


def test_queda_maxima_conta_o_capital_como_primeiro_pico():
    assert rob._queda_maxima(np.array([[90.0, 95.0, 120.0]]), 100.0)[0] == pytest.approx(-0.10)
    assert rob._queda_maxima(np.array([[120.0, 90.0, 95.0]]), 100.0)[0] == pytest.approx(-0.25)


def test_embaralhamento_reproduzivel_e_em_lotes():
    pnl = list(np.random.default_rng(2).normal(100, 800, 60))
    a = rob.monte_carlo_ordem(trades(pnl), 100_000, 1200, tamanho_lote=500)
    b = rob.monte_carlo_ordem(trades(pnl), 100_000, 1200, tamanho_lote=500)
    assert a["queda_pessimista"] == b["queda_pessimista"] and sum(a["histograma"]["contagens"]) == 1200


def test_poucas_operacoes_nao_embaralha():
    assert rob.monte_carlo_ordem(trades([1, 2, 3, 4]), 1000) is None


# ---------------------------------------------------------------- sem os melhores trades
def test_sem_os_3_melhores():
    r = rob.sem_melhores_trades(trades([100, 500, -50, 300, 200, -40]), 10_000)
    assert r["resultado_total"] == pytest.approx(1010)
    assert r["resultado_sem"] == pytest.approx(100 - 50 - 40)
    assert r["ainda_positivo"] is True


def test_depende_de_poucos_trades():
    assert rob.sem_melhores_trades(trades([5000, 4000, 3000, -100, -200]), 10_000)["ainda_positivo"] is False
    assert rob.sem_melhores_trades(trades([1, 2, 3]), 10_000) is None


# ---------------------------------------------------------------- ano a ano
def test_ano_a_ano_composto_e_ignora_ano_incompleto():
    idx = pd.bdate_range("2021-12-01", "2023-12-29")
    est = pd.Series(0.001, index=idx)
    sel = pd.Series(0.0005, index=idx)
    est.loc["2023"] = 0.0
    r = rob.ano_a_ano({"estrategia": est, "selic": sel})
    por_ano = {a["ano"]: a for a in r["anos"]}
    assert por_ano[2022]["estrategia"] == pytest.approx(1.001 ** por_ano[2022]["pregoes"] - 1)
    assert por_ano[2021]["acima_ref"] is None                     # só dezembro: aparece, mas não conta
    assert por_ano[2022]["acima_ref"] is True and por_ano[2023]["acima_ref"] is False
    assert (r["n_acima"], r["n_avaliados"]) == (1, 2)


# ---------------------------------------------------------------- recortes
def test_recortes_de_treino_e_teste_nao_deixam_buraco():
    s = pd.Series(np.arange(10.0))
    tr, te = rob.recorte_treino(s, 7), rob.recorte_teste(s, 7)
    assert tr.iloc[-1] == te.iloc[0] == 6.0 and len(tr) == 7 and te.iloc[-1] == 9.0
