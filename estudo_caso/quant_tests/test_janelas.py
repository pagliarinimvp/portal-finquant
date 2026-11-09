"""Janelas sucessivas: limites, simulação em trechos e escolhas só com o passado."""
from types import SimpleNamespace

import pandas as pd
import pytest

from quant import janelas as jan
from quant import metricas as m
from quant.config import MEDIAS, MEDIAS_PELO_TREINO, N_COMBINACOES, PROTECOES
from conftest import serie_ohlc

N = 800


@pytest.fixture(scope="module")
def dfs():
    return {"PETR4": serie_ohlc(N, 1), "VALE3": serie_ohlc(N, 2)}


def escolha(pesos, ritmo="rapido"):
    return {"acoes": list(pesos), "pesos": pesos, "fora": [], "ritmo": ritmo, "comparacao_ritmos": None, "selecao": None,
            "sharpe_treino": None, "caixa": False}


def fech_de(dfs):
    return pd.DataFrame({t: d["Close"] for t, d in dfs.items()})


# ---------------------------------------------------------------- limites
def test_limites_cobrem_a_segunda_metade_sem_buraco():
    lim = jan.limites(1000)
    assert lim == [500, 600, 700, 800, 900, 1000]
    lim = jan.limites(1253)
    assert lim[0] == 626 and lim[-1] == 1253 and len(lim) == 6
    tamanhos = [b - a for a, b in zip(lim[:-1], lim[1:])]
    assert max(tamanhos) - min(tamanhos) <= 1


# ---------------------------------------------------------------- simulação
def test_imposto_e_separado_na_venda_e_o_que_sobra_volta_no_vencimento():
    indice = pd.bdate_range("2024-01-01", "2024-04-30")
    f = jan._Fisco(indice)
    d = lambda x: pd.Timestamp(x)                                    # noqa: E731
    # janeiro: vendas de R$ 30 mil, ganho de R$ 10 mil e perda de R$ 4 mil -> paga 15% de 6 mil
    assert f.venda((d("2024-01-02"), 10.0, d("2024-01-10"), 20.0, 1000, "sinal", 10_000.0, 100.0, 7)) == pytest.approx(1_500)
    assert f.venda((d("2024-01-11"), 20.0, d("2024-01-20"), 16.0, 625, "stop", -4_000.0, -20.0, 7)) == 0
    assert f.cofre == pytest.approx(1_500)
    vence = f.pos[indice[indice.month == 2][-1]]                     # último pregão de fevereiro
    assert f.vencimentos(vence - 1) == 0                              # antes do vencimento, nada acontece
    assert f.vencimentos(vence) == pytest.approx(1_500 - 900) and f.cofre == pytest.approx(0)
    # março: vendas de R$ 12 mil, isento -> a reserva volta inteira
    assert f.venda((d("2024-03-01"), 5.0, d("2024-03-05"), 6.0, 2000, "alvo", 2_000.0, 20.0, 3)) == pytest.approx(300)
    assert f.vencimentos(f.pos[indice[-1]]) == pytest.approx(300)
    ap = f.apuracao()
    assert list(ap["imposto"]) == pytest.approx([900, 0]) and list(ap["isento"]) == [False, True]


def test_com_imposto_a_curva_fecha_com_capital_mais_resultados_menos_imposto():
    dfs = {"PETR4": serie_ohlc(N, 3), "VALE3": serie_ohlc(N, 4)}      # sementes com lucro, para haver imposto
    e = escolha({"PETR4": 0.5, "VALE3": 0.5})
    lim = jan.limites(N)
    sim = jan.simular(dfs, dfs["PETR4"].index, jan.blocos(lim, [e] * (len(lim) - 1)), 1_000_000, None, None, 0.5, {}, com_imposto=True)
    tr, ap = sim["trades"], sim["apuracao"]
    assert len(tr) and ap["imposto"].sum() > 0
    assert sim["equity"].iloc[-1] == pytest.approx(1_000_000 + tr["pnl"].sum() - ap["imposto"].sum())
    assert (tr["saldo_apos_compra"] >= 0).all() and (tr["saldo_apos_venda"] >= 0).all()
    sem = jan.simular(dfs, dfs["PETR4"].index, jan.blocos(lim, [e] * (len(lim) - 1)), 1_000_000, None, None, 0.5, {})
    assert sim["equity"].iloc[-1] < sem["equity"].iloc[-1]


def test_escolhas_iguais_dao_a_mesma_curva_da_simulacao_continua(dfs):
    e = escolha({"PETR4": 0.5, "VALE3": 0.5})
    lim = jan.limites(N)
    sim = jan.simular(dfs, dfs["PETR4"].index, jan.blocos(lim, [e] * (len(lim) - 1)), 100_000, None, None, 0.5, {})
    md = MEDIAS["rapido"]
    direto = jan.rodar_trecho(dfs, e["pesos"], md["curta"], md["longa"], 100_000, None, None, 0.5, 0, N, {})
    assert sim["trechos"] == [(0, N)]
    pd.testing.assert_series_equal(sim["equity"], sum(r.equity for r in direto.values()).rename("equity"))
    assert "fim_janela" not in set(sim["trades"]["motivo"])


def test_quando_as_escolhas_mudam_o_dinheiro_passa_inteiro_para_a_janela_seguinte(dfs):
    lim = jan.limites(N)
    escolhas = [escolha({"PETR4": 0.5, "VALE3": 0.5}), escolha({"PETR4": 1.0}), escolha({"PETR4": 1.0}, "lento"),
                escolha({"VALE3": 1.0}, "lento"), escolha({"PETR4": 0.3, "VALE3": 0.7})]
    sim = jan.simular(dfs, dfs["PETR4"].index, jan.blocos(lim, escolhas), 100_000, None, None, 0.5, {})
    eq, tr = sim["equity"], sim["trades"]
    assert len(eq) == N and eq.index.is_unique and eq.iloc[0] == pytest.approx(100_000)
    assert eq.iloc[-1] == pytest.approx(100_000 + tr["pnl"].sum())
    assert len(sim["trechos"]) == 5                       # o treino inicial se junta à 1ª janela
    ultimo = dfs["PETR4"].index[sim["trechos"][-1][0]]
    assert set(tr.loc[tr["data_entrada"] < ultimo, "motivo"]) <= {"sinal", "fim_janela"}
    assert tr["data_entrada"].is_monotonic_increasing


def test_ritmo_forcado_vale_em_todas_as_janelas(dfs):
    lim = jan.limites(N)
    escolhas = [escolha({"PETR4": 1.0}, "rapido"), escolha({"PETR4": 1.0}, "lento")] + [escolha({"PETR4": 1.0}, "lento")] * 3
    sim = jan.simular(dfs, dfs["PETR4"].index, jan.blocos(lim, escolhas), 100_000, None, None, 0.5, {}, ritmo="intermediario")
    assert sim["trechos"] == [(0, N)] and set(sim["trades"]["ritmo"]) == {"intermediario"}
    assert len(MEDIAS) * len(PROTECOES) == N_COMBINACOES == 16


def test_custo_maior_nunca_rende_mais_com_as_mesmas_escolhas(dfs):
    lim = jan.limites(N)
    blocos = jan.blocos(lim, [escolha({"PETR4": 0.5, "VALE3": 0.5})] * 5)
    finais = [jan.simular(dfs, dfs["PETR4"].index, blocos, 100_000, None, None, c, {})["equity"].iloc[-1] for c in (0.0, 0.1, 0.5)]
    assert finais[0] > finais[1] > finais[2]


def test_comprar_e_segurar_paga_a_troca(dfs):
    lim = jan.limites(N)
    fech = fech_de(dfs)
    igual = [escolha({"PETR4": 1.0})] * 5
    troca = [escolha({"PETR4": 1.0}), escolha({"VALE3": 1.0})] + [escolha({"VALE3": 1.0})] * 3
    bh_igual, _ = jan.simular_buy_hold(fech, jan.blocos(lim, igual), 100_000, 0.0)
    assert bh_igual.iloc[-1] == pytest.approx(100_000 * fech["PETR4"].iloc[-1] / fech["PETR4"].iloc[0])
    bh_troca, ganhos = jan.simular_buy_hold(fech, jan.blocos(lim, troca), 100_000, 0.0)
    a = lim[1]
    esperado = 100_000 * fech["PETR4"].iloc[a - 1] / fech["PETR4"].iloc[0] * fech["VALE3"].iloc[-1] / fech["VALE3"].iloc[a]
    assert bh_troca.iloc[-1] == pytest.approx(esperado)
    assert set(ganhos) == {"PETR4", "VALE3"}


# ---------------------------------------------------------------- escolhas só com o passado
def test_as_escolhas_de_uma_janela_nao_veem_o_que_vem_depois(dfs):
    cfg = SimpleNamespace(selecao="manual", medias=MEDIAS_PELO_TREINO, capital=100_000, divisao="max_sharpe")
    s = jan.limites(N)[2]
    antes = jan.escolher(dfs, fech_de(dfs), s, cfg, 0.0, None, None, None, 0.5, {}, True)
    mexido = {t: d.copy() for t, d in dfs.items()}
    for d in mexido.values():
        d.iloc[s:, :4] = d.iloc[s:, :4] * 3.0              # o futuro sobe 200% de uma vez
    depois = jan.escolher(mexido, fech_de(mexido), s, cfg, 0.0, None, None, None, 0.5, {}, True)
    assert antes["pesos"] == depois["pesos"] and antes["ritmo"] == depois["ritmo"]
    assert antes["comparacao_ritmos"] == depois["comparacao_ritmos"] and antes["sharpe_treino"] == depois["sharpe_treino"]


def test_o_ritmo_vencedor_e_o_de_maior_sharpe_no_treino(dfs):
    cfg = SimpleNamespace(selecao="manual", medias=MEDIAS_PELO_TREINO, capital=100_000, divisao="igual")
    e = jan.escolher(dfs, fech_de(dfs), jan.limites(N)[0], cfg, 0.0, None, None, None, 0.5, {}, True)
    validos = [x for x in e["comparacao_ritmos"] if x["sharpe_treino"] is not None]
    assert e["ritmo"] == max(validos, key=lambda x: x["sharpe_treino"])["medias"]
    assert e["sharpe_treino"] == pytest.approx(max(x["sharpe_treino"] for x in validos))


def test_resumo_da_combinacao_corta_a_mesma_curva():
    idx = pd.bdate_range("2020-01-01", periods=10)
    eq = pd.Series([100, 101, 102, 101, 103, 104, 103, 105, 106, 108], index=idx, dtype=float)
    r = jan.resumo_combinacao(eq, 7, 5, 0.0, 0.01)
    assert r["retorno_teste"] == pytest.approx(108 / 103 - 1)
    assert r["sharpe_treino"] == pytest.approx(m.sharpe(eq.iloc[:5].pct_change().dropna()))
    assert r["bateu_selic"] is True and r["n_trades"] == 7
