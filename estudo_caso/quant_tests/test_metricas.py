"""Métricas conferidas contra cálculo manual."""
import numpy as np
import pandas as pd
import pytest

from quant import benchmarks as bm
from quant import metricas as m


def curva(valores):
    return pd.Series(valores, index=pd.bdate_range("2024-01-02", periods=len(valores)), dtype=float)


def test_drawdown_manual():
    assert m.max_drawdown(curva([100, 120, 90, 100, 130])) == pytest.approx(90 / 120 - 1)


def test_sharpe_manual():
    ret = pd.Series([0.01, -0.02, 0.015, 0.005, -0.01, 0.02], index=pd.bdate_range("2024-01-02", periods=6))
    assert m.sharpe(ret) == pytest.approx(ret.mean() * 252 / (ret.std(ddof=1) * np.sqrt(252)))


def test_sharpe_com_rf_serie_diaria():
    idx = pd.bdate_range("2024-01-02", periods=100)
    ret = pd.Series(np.random.default_rng(1).normal(0.001, 0.01, 100), index=idx)
    rf = pd.Series(0.0004, index=idx)
    assert m.sharpe(ret, rf) == pytest.approx((ret.mean() - 0.0004) * 252 / (ret.std(ddof=1) * np.sqrt(252)))


def test_cagr_dois_anos():
    idx = pd.to_datetime(["2022-01-01", "2024-01-01"])
    assert m.cagr(pd.Series([100.0, 121.0], index=idx)) == pytest.approx(0.1, abs=2e-3)


def test_sortino_conta_so_os_dias_ruins():
    ret = pd.Series([0.02, -0.01, 0.03, -0.02])
    risco = np.sqrt((0.01 ** 2 + 0.02 ** 2) / 4) * np.sqrt(252)
    assert m.sortino(ret) == pytest.approx(ret.mean() * 252 / risco)
    assert np.isnan(m.sortino(pd.Series([0.01, 0.02, 0.03])))       # sem dia ruim, não há risco para dividir


def test_retorno_por_queda():
    idx = pd.to_datetime(["2022-01-01", "2023-01-01", "2024-01-01"])
    d = m.desempenho(pd.Series([100.0, 80.0, 121.0], index=idx))
    assert d["max_drawdown"] == pytest.approx(-0.2)
    assert d["retorno_por_queda"] == pytest.approx(d["retorno_anualizado"] / 0.2)
    assert np.isnan(m.desempenho(pd.Series([100.0, 110.0, 121.0], index=idx))["retorno_por_queda"])


def _trades(pnl, pct, motivos):
    return pd.DataFrame({"pnl": pnl, "retorno_pct": pct, "motivo": motivos, "barras": [2] * len(pnl)})


def test_maior_ganho_e_perda_e_saidas():
    mt = m.metricas_trading(_trades([300.0, -100.0, 50.0, -200.0], [3.0, -4.0, 10.0, -2.0], ["alvo", "stop", "sinal", "sinal"]))
    assert (mt["n_ganhos"], mt["n_perdas"]) == (2, 2)
    assert mt["maior_ganho"] == 300 and mt["maior_perda"] == -200
    assert mt["maior_ganho_pct"] == 10 and mt["maior_perda_pct"] == -4      # em % podem ser outras operações
    assert mt["saidas"] == {"sinal": 2, "stop": 1, "alvo": 1, "fim_janela": 0, "fim_dados": 0}


def test_sem_perdas_ou_sem_ganhos_nao_inventa_numero():
    so_ganhos = m.metricas_trading(_trades([10.0, 20.0], [1.0, 2.0], ["alvo", "alvo"]))
    assert np.isnan(so_ganhos["maior_perda"]) and np.isnan(so_ganhos["maior_perda_pct"]) and np.isnan(so_ganhos["fator_lucro"])
    so_perdas = m.metricas_trading(_trades([-10.0, -20.0], [-1.0, -2.0], ["stop", "stop"]))
    assert np.isnan(so_perdas["maior_ganho"]) and np.isnan(so_perdas["maior_ganho_pct"]) and so_perdas["fator_lucro"] == 0


def test_sem_operacoes():
    mt = m.metricas_trading(pd.DataFrame(columns=["pnl", "retorno_pct", "motivo", "barras"]))
    assert mt["n_trades"] == 0 and mt["n_ganhos"] == 0 and np.isnan(mt["maior_ganho"]) and sum(mt["saidas"].values()) == 0


def test_metricas_trading_manual():
    tr = pd.DataFrame({"pnl": [300.0, -100.0, 300.0, -200.0, 100.0], "barras": [5, 3, 4, 2, 6]})
    mt = m.metricas_trading(tr)
    assert mt["n_trades"] == 5 and mt["win_rate"] == pytest.approx(0.6)
    assert mt["ganho_medio"] == pytest.approx(700 / 3) and mt["perda_media"] == pytest.approx(150)
    assert mt["fator_lucro"] == pytest.approx(700 / 300)
    payoff = (700 / 3) / 150
    assert mt["payoff"] == pytest.approx(payoff)
    assert mt["break_even"] == pytest.approx(1 / (1 + payoff))
    assert mt["edge"] == pytest.approx(0.6 - 1 / (1 + payoff))
    assert mt["expectancia"] == pytest.approx(0.6 * 700 / 3 - 0.4 * 150)
    assert mt["maior_sequencia_perdas"] == 1


def test_selic_compoe_taxa_diaria():
    idx = pd.bdate_range("2024-01-02", periods=253)
    taxa = pd.Series(0.04, index=pd.bdate_range("2023-12-01", periods=300))     # 0,04% ao dia
    r = bm._acumular_taxa_diaria(taxa, idx)
    assert (1 + r).prod() - 1 == pytest.approx(1.0004 ** 252 - 1, rel=1e-6)


def test_datas_no_formato_brasileiro():
    from apresentacao.formatacao import data_br
    assert data_br("2026-10-02") == "02/10/2026"
    assert data_br(pd.Timestamp("2026-03-09")) == "09/03/2026" and data_br(None) == "—"


def test_conta_sharpe_fecha_com_o_sharpe():
    import numpy as np
    import pandas as pd

    from quant import metricas as m
    ret = pd.Series(np.random.default_rng(1).normal(0.001, 0.01, 500))
    rf = pd.Series(0.0004, index=ret.index)
    c = m.conta_sharpe(ret, rf)
    assert abs(c["retorno_medio_anual"] - ret.mean() * 252) < 1e-12 and abs(c["selic_media_anual"] - 0.0004 * 252) < 1e-12
    assert abs(c["excesso_anual"] - (c["retorno_medio_anual"] - c["selic_media_anual"])) < 1e-12
    assert abs(c["excesso_anual"] / c["oscilacao_anual"] - c["sharpe"]) < 1e-12
    assert abs(c["sharpe"] - m.sharpe(ret, rf)) < 1e-12
    assert m.conta_sharpe(pd.Series([0.01]), 0.0)["sharpe"] is None
