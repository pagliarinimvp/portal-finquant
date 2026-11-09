"""Motor de backtest: stop e alvo, gap, mesmo candle, custos, lote e fim dos dados."""
import pandas as pd
import pytest

from quant.backtest import executar_backtest
from quant.estrategias import gerar_sinais
from conftest import serie_ohlc


def candles(linhas):
    """linhas = [(open, high, low, close), ...]"""
    idx = pd.bdate_range("2024-01-02", periods=len(linhas))
    return pd.DataFrame(linhas, columns=["Open", "High", "Low", "Close"], index=idx)


def sinais(n, entrada=(), saida=()):
    df = pd.DataFrame(False, index=pd.bdate_range("2024-01-02", periods=n), columns=["entrada", "saida"])
    for col, posicoes in (("entrada", entrada), ("saida", saida)):
        for p in posicoes:
            df.iloc[p, df.columns.get_loc(col)] = True
    return df


ENTRADA = (100, 101, 99, 100)   # entra a 100 no candle 1 (sinal no candle 0)


def rodar(dia2, stop=5.0, alvo=10.0, custo=0.0):
    df = candles([(100, 100, 100, 100), ENTRADA, dia2, (100, 100, 100, 100)])
    return executar_backtest(df, sinais(4, entrada=[0]), 100_000, stop, alvo, custo)


def test_stop():
    t = rodar((100, 102, 94, 96)).trades.iloc[0]
    assert t.motivo == "stop" and t.preco_saida == pytest.approx(95)
    assert t.quantidade == 1000 and t.pnl == pytest.approx(-5000)


def test_alvo():
    t = rodar((100, 111, 99, 110)).trades.iloc[0]
    assert t.motivo == "alvo" and t.preco_saida == pytest.approx(110) and t.pnl == pytest.approx(10_000)


def test_stop_e_alvo_no_mesmo_candle_vale_o_stop():
    t = rodar((100, 111, 94, 100)).trades.iloc[0]
    assert t.motivo == "stop" and t.preco_saida == pytest.approx(95)


def test_gap_abaixo_do_stop_executa_na_abertura():
    t = rodar((90, 92, 88, 91)).trades.iloc[0]
    assert t.motivo == "stop" and t.preco_saida == pytest.approx(90) and t.pnl == pytest.approx(-10_000)


def test_gap_acima_do_alvo_executa_na_abertura():
    t = rodar((115, 118, 114, 116)).trades.iloc[0]
    assert t.motivo == "alvo" and t.preco_saida == pytest.approx(115) and t.pnl == pytest.approx(15_000)


def test_sem_stop_nem_alvo_encerra_no_fim_dos_dados():
    t = rodar((100, 101, 99, 100.5), stop=None, alvo=None).trades.iloc[0]
    assert t.motivo == "fim_dados" and t.preco_saida == pytest.approx(100)


def test_saida_por_sinal_na_abertura_seguinte_com_custo_nas_duas_pontas():
    df = candles([(100, 100, 100, 100), ENTRADA, (101, 102, 100, 101), (103, 104, 102, 103), (103, 103, 103, 103)])
    r = executar_backtest(df, sinais(5, entrada=[0], saida=[2]), 100_000, custo_pct=0.5)
    t = r.trades.iloc[0]
    assert t.motivo == "sinal" and t.preco_entrada == pytest.approx(100) and t.preco_saida == pytest.approx(103)
    assert t.quantidade == 900                     # 100.000 ÷ (100 × 1,005) = 995 -> 9 lotes de 100
    custos = 0.005 * 900 * 100 + 0.005 * 900 * 103
    assert t.pnl == pytest.approx(900 * 3 - custos)
    assert r.equity.iloc[-1] == pytest.approx(100_000 + t.pnl)


def test_patrimonio_paga_o_custo_de_entrada_no_dia_da_compra():
    df = candles([(100, 100, 100, 100), (100, 100, 100, 100), (100, 100, 100, 100)])
    r = executar_backtest(df, sinais(3, entrada=[0]), 100_000, custo_pct=0.5)
    assert r.equity.iloc[1] == pytest.approx(100_000 - 0.005 * 900 * 100)


def test_lote_arredonda_para_baixo():
    df = candles([(100, 100, 100, 100), (333, 334, 332, 333), (333, 333, 333, 333)])
    r = executar_backtest(df, sinais(3, entrada=[0]), 100_000)
    assert r.trades.iloc[0].quantidade == 300      # 100000/333 = 300,3 -> 3 lotes de 100


def test_capital_menor_que_um_lote_nao_opera():
    df = candles([(100, 100, 100, 100), (100, 100, 100, 100), (100, 100, 100, 100)])
    r = executar_backtest(df, sinais(3, entrada=[0]), 5_000)
    assert len(r.trades) == 0 and (r.equity == 5_000).all()


def test_sem_look_ahead_sinal_do_ultimo_candle_nao_opera():
    df = candles([(100, 100, 100, 100), (100, 100, 100, 100)])
    assert len(executar_backtest(df, sinais(2, entrada=[1]), 100_000).trades) == 0


def test_nao_compra_no_ultimo_pregao():
    # o sinal do penúltimo pregão viraria compra na abertura do último, vendida no mesmo fechamento só pagando tarifa
    df = candles([(100, 100, 100, 100), (100, 101, 99, 100), (100, 101, 99, 100)])
    r = executar_backtest(df, sinais(3, entrada=[1]), 100_000, custo_pct=0.5)
    assert len(r.trades) == 0 and r.equity.iloc[-1] == 100_000
    assert len(executar_backtest(df, sinais(3, entrada=[0]), 100_000).trades) == 1   # um pregão antes, compra normalmente


def test_truncar_o_futuro_nao_muda_o_passado():
    df = serie_ohlc(600, 3)
    longo = executar_backtest(df, gerar_sinais(df, 10, 20), 100_000, 10, 20, 0.5)
    curto = executar_backtest(df.iloc[:400], gerar_sinais(df.iloc[:400], 10, 20), 100_000, 10, 20, 0.5)
    # o último candle do trecho curto encerra a posição aberta, por isso compara até o anterior
    pd.testing.assert_series_equal(longo.equity.iloc[:399], curto.equity.iloc[:399])


def test_sinais_nao_dependem_do_futuro():
    df = serie_ohlc(400, 3)
    assert gerar_sinais(df, 5, 20).iloc[:300].equals(gerar_sinais(df.iloc[:300], 5, 20))


def test_media_curta_precisa_ser_menor_que_a_longa():
    with pytest.raises(ValueError):
        gerar_sinais(serie_ohlc(100, 3), 50, 20)
