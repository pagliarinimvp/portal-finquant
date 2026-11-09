"""Imposto de renda: contas feitas à mão para cada regra."""
import numpy as np
import pandas as pd
import pytest

from quant import imposto as imp

IDX = pd.bdate_range("2024-01-01", "2024-06-30")
CURVA = pd.Series(100_000.0, index=IDX)


def venda(data, valor, resultado, day_trade=False):
    return {"data": pd.Timestamp(data), "valor_venda": float(valor), "resultado": float(resultado), "day_trade": day_trade}


def apurar(*vendas, curva=CURVA):
    return imp.aplicar(curva, pd.DataFrame(list(vendas)))


def impostos(ap):
    return dict(zip(ap["mes"], ap["imposto"]))


# ---------------------------------------------------------------- operações comuns
def test_isento_ate_20_mil_em_vendas_no_mes():
    _, ap = apurar(venda("2024-01-10", 20_000, 1_000), venda("2024-02-10", 20_000.01, 1_000))
    assert impostos(ap) == pytest.approx({"2024-01": 0.0, "2024-02": 150.0})
    assert ap["isento"].tolist() == [True, False]


def test_vendas_do_mes_somam_para_o_limite():
    _, ap = apurar(venda("2024-01-10", 12_000, 500), venda("2024-01-20", 12_000, 500))
    assert impostos(ap)["2024-01"] == pytest.approx(150.0)


def test_perda_abate_o_ganho_dos_meses_seguintes():
    _, ap = apurar(venda("2024-01-10", 30_000, -2_000), venda("2024-02-10", 30_000, 3_000))
    assert impostos(ap) == pytest.approx({"2024-01": 0.0, "2024-02": 150.0})
    assert ap["prejuizo_comum"].tolist() == pytest.approx([2_000, 0])


def test_perda_de_mes_isento_tambem_abate():
    _, ap = apurar(venda("2024-01-10", 10_000, -500), venda("2024-02-10", 30_000, 1_000))
    assert impostos(ap)["2024-02"] == pytest.approx(75.0)


def test_ganho_isento_nao_gasta_o_prejuizo():
    _, ap = apurar(venda("2024-01-10", 30_000, -1_000), venda("2024-02-10", 10_000, 800), venda("2024-03-10", 30_000, 1_500))
    assert impostos(ap) == pytest.approx({"2024-01": 0.0, "2024-02": 0.0, "2024-03": 75.0})


# ---------------------------------------------------------------- day trade
def test_day_trade_paga_20_por_cento_sem_isencao():
    _, ap = apurar(venda("2024-01-10", 5_000, 100, day_trade=True))
    assert impostos(ap)["2024-01"] == pytest.approx(20.0)


def test_perda_de_day_trade_nao_abate_operacao_comum():
    _, ap = apurar(venda("2024-01-10", 30_000, 1_000), venda("2024-01-11", 5_000, -500, day_trade=True),
                   venda("2024-02-10", 5_000, 1_000, day_trade=True))
    assert ap["imposto_comum"].tolist() == pytest.approx([150.0, 0.0])
    assert ap["imposto_day_trade"].tolist() == pytest.approx([0.0, 100.0])        # 20% de (1.000 − 500)


# ---------------------------------------------------------------- pagamento e curva
def test_paga_no_ultimo_pregao_do_mes_seguinte_e_a_carteira_encolhe():
    liq, ap = apurar(venda("2024-01-10", 30_000, 1_000), venda("2024-03-12", 30_000, 1_000))
    pagamento = pd.Timestamp("2024-02-29")
    assert ap["data_pagamento"].iloc[0] == pagamento
    assert liq.loc[:"2024-02-28"].eq(100_000).all() and liq.loc[pagamento] == pytest.approx(99_850)
    fator = 1 - 150 / 100_000                       # a venda de março já é de uma carteira 0,15% menor
    assert ap["imposto"].iloc[1] == pytest.approx(150 * fator)
    assert liq.iloc[-1] == pytest.approx(100_000 - 150 - 150 * fator)


def test_imposto_depois_do_fim_dos_dados_sai_no_ultimo_pregao():
    liq, ap = apurar(venda("2024-06-20", 30_000, 1_000))
    assert ap["data_pagamento"].iloc[0] == IDX[-1] and liq.iloc[-1] == pytest.approx(99_850)


def test_sem_vendas_a_curva_nao_muda():
    liq, ap = imp.aplicar(CURVA, pd.DataFrame(columns=["data", "valor_venda", "resultado", "day_trade"]))
    assert liq.equals(CURVA) and len(ap) == 0
    assert imp.pago_entre(ap, IDX[0], IDX[-1]) == 0


def test_pago_entre_conta_pela_data_do_pagamento():
    _, ap = apurar(venda("2024-01-10", 30_000, 1_000), venda("2024-04-10", 30_000, 1_000))
    assert imp.pago_entre(ap, IDX[0], pd.Timestamp("2024-03-31")) == pytest.approx(150)
    assert imp.pago_entre(ap, pd.Timestamp("2024-04-01"), IDX[-1]) == pytest.approx(ap["imposto"].iloc[1])


def test_operacoes_viram_vendas_com_day_trade_no_mesmo_dia():
    trades = pd.DataFrame({"data_entrada": pd.to_datetime(["2024-01-02", "2024-01-05"]),
                           "data_saida": pd.to_datetime(["2024-01-02", "2024-01-09"]),
                           "quantidade": [100, 200], "preco_saida": [10.0, 20.0], "pnl": [5.0, -3.0]})
    v = imp.vendas_das_operacoes(trades)
    assert v["day_trade"].tolist() == [True, False] and v["valor_venda"].tolist() == [1_000.0, 4_000.0]


# ---------------------------------------------------------------- Selic
def test_tabela_regressiva_da_renda_fixa():
    dias = [0, 180, 181, 360, 361, 720, 721, 3_000]
    assert imp.aliquota_renda_fixa(dias).tolist() == [0.225, 0.225, 0.20, 0.20, 0.175, 0.175, 0.15, 0.15]


def test_selic_liquida_e_o_valor_de_resgate():
    idx = pd.date_range("2020-01-01", periods=1_000, freq="D")
    bruta = pd.Series(0.0004, index=idx)
    liq = imp.selic_liquida(bruta)
    final = (1 + liq).prod()
    assert final == pytest.approx(1 + (1.0004 ** 1_000 - 1) * 0.85)
    em_100_dias = (1 + liq.iloc[:101]).prod()
    assert em_100_dias == pytest.approx(1 + (1.0004 ** 101 - 1) * 0.775)
    assert np.all(liq > 0)


# ---------------------------------------------------------------- imposto de cada operação
def rateio(*vendas):
    v = pd.DataFrame(list(vendas))
    return imp.rateio(v, apurar(*vendas)[1])


def test_rateio_divide_o_imposto_do_mes_pelo_ganho_e_perda_fica_com_zero():
    # janeiro: ganhos de 3.000 e 1.000 e perda de 2.000 → base de 2.000, imposto de 300, dividido 3 para 1
    p = rateio(venda("2024-01-10", 30_000, 3_000), venda("2024-01-15", 10_000, 1_000), venda("2024-01-20", 10_000, -2_000))
    assert p.tolist() == pytest.approx([225.0, 75.0, 0.0])
    assert p.sum() == pytest.approx(300.0)


def test_rateio_soma_o_imposto_de_cada_mes_e_separa_day_trade():
    vendas = [venda("2024-01-10", 30_000, 1_000), venda("2024-01-11", 5_000, 500, day_trade=True),
              venda("2024-02-10", 10_000, 800), venda("2024-03-10", 30_000, -400)]
    v = pd.DataFrame(vendas)
    _, ap = apurar(*vendas)
    p = imp.rateio(v, ap)
    assert p.tolist() == pytest.approx([150.0, 100.0, 0.0, 0.0])      # fevereiro isento; março com perda
    assert p.sum() == pytest.approx(ap["imposto"].sum())
