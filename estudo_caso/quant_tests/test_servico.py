"""Fachada `servico.executar`: contrato JSON, ausência de vazamento e coerência dos números."""
import json
import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from quant import config as c
from quant import janelas as jan
from quant import metricas as m, servico
from quant.dados import CsvFonte
from conftest import TICKERS, gravar_cache

RAIZ = Path(__file__).resolve().parents[1]
QUATRO = ["PETR4", "VALE3", "ITUB4", "WEGE3"]


@pytest.fixture(scope="module")
def um(pasta_sintetica):
    return servico.executar({"tickers": ["PETR4"]}, CsvFonte(pasta_sintetica))


@pytest.fixture(scope="module")
def carteira(pasta_sintetica):
    return servico.executar({"tickers": QUATRO, "divisao": "max_sharpe", "medias": "treino"}, CsvFonte(pasta_sintetica))


def test_resultado_e_json_puro(um, carteira):
    for r in (um, carteira):
        json.dumps(r, allow_nan=False)


def test_padroes_vindos_do_curso():
    cfg = c.ConfigAnalise()
    assert (cfg.tickers, cfg.divisao, cfg.medias, cfg.protecao, cfg.custo) == (["PETR4"], "igual", "intermediario", "2_1", "tarifas_b3")
    assert (c.MEDIAS["intermediario"]["curta"], c.MEDIAS["intermediario"]["longa"]) == (12, 50)
    assert (c.PROTECOES["2_1"]["stop"], c.PROTECOES["2_1"]["alvo"]) == (10.0, 20.0)
    assert c.CUSTOS["tarifas_b3"]["pct"] == 0.03 and c.N_COMBINACOES == 16


def test_todas_as_opcoes_citam_a_aula():
    for catalogo in (c.DIVISOES, c.MEDIAS, c.PROTECOES, c.CUSTOS):
        assert all(v["rotulo"] and v["descricao"] for v in catalogo.values())


@pytest.mark.parametrize("campo,valor", [("divisao", "hrp"), ("medias", "9_21"), ("protecao", "x"), ("custo", "y"),
                                         ("capital", 10), ("tickers", ["NAOEXISTE"]), ("tickers", TICKERS[:12])])
def test_config_invalida_e_recusada(campo, valor):
    with pytest.raises(ValueError):
        c.ConfigAnalise.from_dict({campo: valor}).validar()


def test_chave_cache_estavel():
    assert servico.chave_cache({"tickers": ["PETR4"]}) == servico.chave_cache({"tickers": ["PETR4"]})
    assert servico.chave_cache({"tickers": ["PETR4"]}) != servico.chave_cache({"tickers": ["VALE3"]})


def test_uma_acao_nao_tem_bloco_de_carteira(um):
    assert um["carteira"] is None and um["concentracao"] is None and um["pesos"] == {"PETR4": 1.0}


def test_treino_inicial_de_metade_e_janelas_em_sequencia(um):
    p, js = um["periodo"], um["janelas"]
    assert p["n_treino"] == int(p["n_pregoes"] * c.FRACAO_TREINO) and p["n_treino"] + p["n_teste"] == p["n_pregoes"]
    assert p["fim_treino"] < p["inicio_teste"] and p["n_janelas"] == len(js) == c.N_JANELAS
    assert js[0]["inicio"] == p["inicio_teste"] == p["inicios_janelas"][0] and js[-1]["fim"] == p["fim"]
    assert sum(j["n_pregoes"] for j in js) == p["n_teste"]
    for antes, depois in zip(js, js[1:]):
        assert antes["fim"] < depois["inicio"] and depois["fim_treino"] == antes["fim"] and depois["n_treino"] == antes["n_treino"] + antes["n_pregoes"]


def test_janelas_encadeiam_o_retorno_do_teste(um):
    total = np.prod([1 + j["retorno"] for j in um["janelas"]]) - 1
    assert total == pytest.approx(um["desempenho"]["teste"]["estrategia"]["retorno_total"])
    selic = np.prod([1 + j["selic"] for j in um["janelas"]]) - 1
    assert selic == pytest.approx(um["desempenho"]["teste"]["selic"]["retorno_total"], rel=1e-6)


def test_escolhas_manuais_valem_em_todas_as_janelas(um):
    assert all(j["pesos"] == {"PETR4": 1.0} and j["ritmo"] == um["janelas"][0]["ritmo"] and not j["mudou"] for j in um["janelas"])
    assert "fim_janela" not in {x["motivo"] for x in um["operacoes"]["lista"]}


def test_periodo_fica_dentro_de_10_anos(um):
    assert um["periodo"]["inicio"] >= c.inicio_historico()


def test_datas_em_iso_no_contrato(um):
    assert um["periodo"]["inicio"][4] == "-" and um["curvas"]["estrategia"][0]["x"][4] == "-"


def test_numeros_batem_entre_o_inteiro_e_os_recortes(um):
    d = um["desempenho"]
    inteiro, tr, te = d["inteiro"]["estrategia"], d["treino"]["estrategia"], d["teste"]["estrategia"]
    assert (1 + tr["retorno_total"]) * (1 + te["retorno_total"]) == pytest.approx(1 + inteiro["retorno_total"])
    assert inteiro["valor_final"] == pytest.approx(te["valor_final"])


def test_resultado_das_operacoes_explica_o_patrimonio(um, carteira):
    for r in (um, carteira):                          # o imposto sai do saldo: capital + resultado − imposto, exato
        ops = r["operacoes"]["lista"]
        final = r["desempenho"]["inteiro"]["estrategia"]["valor_final"]
        assert final == pytest.approx(100_000 + r["operacoes"]["inteiro"]["resultado_liquido"] - r["imposto"]["estrategia"]["total"])
        assert final == pytest.approx(100_000 + sum(x["resultado_final"] for x in ops))
    assert um["desempenho"]["inteiro"]["estrategia"]["valor_final"] == pytest.approx(um["imposto"]["antes_estrategia"])
    # sem pagar imposto, as compras seguintes seriam maiores: a diferença não é igual ao imposto pago
    final = carteira["desempenho"]["inteiro"]["estrategia"]["valor_final"]
    esperado = carteira["imposto"]["antes_estrategia"] - carteira["imposto"]["estrategia"]["total"]
    assert final != pytest.approx(esperado) and final == pytest.approx(esperado, abs=0.02 * 100_000)


def test_imposto_de_renda_na_analise(carteira):
    ir, o = carteira["imposto"], carteira["operacoes"]
    assert ir["aplicado"] and ir["estrategia"]["total"] > 0 and ir["buy_hold"]["total"] > 0
    assert o["treino"]["imposto_pago"] + o["teste"]["imposto_pago"] == pytest.approx(o["inteiro"]["imposto_pago"])
    assert o["inteiro"]["imposto_pago"] == pytest.approx(ir["estrategia"]["total"])
    assert ir["antes_estrategia"] > carteira["desempenho"]["inteiro"]["estrategia"]["valor_final"]
    custos = {ln["custo"]: ln for ln in carteira["variacoes"]["custos"]}
    assert custos["tarifas_b3"]["imposto_pago"] == pytest.approx(ir["estrategia"]["total"]) and custos["sem_custo"]["imposto_pago"] == 0
    # cada variação compara com a Selic nas mesmas condições: com imposto, a Selic rende menos
    assert custos["tarifas_b3"]["retorno_selic_teste"] == pytest.approx(carteira["desempenho"]["teste"]["selic"]["retorno_total"])
    assert custos["sem_custo"]["retorno_selic_teste"] > custos["tarifas_b3"]["retorno_selic_teste"]


def test_sem_custo_nao_cobra_imposto(pasta_sintetica):
    r = servico.executar({"tickers": QUATRO, "divisao": "max_sharpe", "medias": "treino", "custo": "sem_custo"}, CsvFonte(pasta_sintetica))
    assert not r["imposto"]["aplicado"] and r["imposto"]["estrategia"]["total"] == 0
    assert r["desempenho"]["inteiro"]["estrategia"]["valor_final"] == pytest.approx(r["imposto"]["antes_estrategia"])


def test_selic_sem_sharpe(um):
    assert um["desempenho"]["teste"]["selic"]["sharpe"] is None


def test_testes_rodam(um):
    s = um["foi_sorte"]
    assert "t_selic" not in s and "t_buy_hold" not in s
    assert s["ic_estrategia"]["baixo_anual"] < s["ic_estrategia"]["alto_anual"]
    assert s["sharpe_desconto"]["n_tentativas"] == 16
    assert len(um["variacoes"]["combinacoes"]) == 16 and len(um["variacoes"]["custos"]) == 2


def test_pior_momento(um):
    p = um["pior_momento"]["estrategia"]
    assert p["valor_fundo"] / p["valor_pico"] - 1 == pytest.approx(p["queda"])
    assert p["queda"] == pytest.approx(um["desempenho"]["inteiro"]["estrategia"]["max_drawdown"])
    assert p["data_pico"] <= p["data_fundo"]


def test_exemplo_de_cruzamento_e_real(um):
    e = um["exemplo_cruzamento"]
    assert e["ticker"] == "PETR4" and e["data_entrada"] in e["datas"] and e["data_sinal"] < e["data_entrada"]
    assert len(e["datas"]) == len(e["preco"]) == len(e["media_curta"]) == len(e["media_longa"])
    i = e["datas"].index(e["data_sinal"])
    assert e["media_curta"][i] > e["media_longa"][i] and e["media_curta"][i - 1] <= e["media_longa"][i - 1]


def test_carteira_traz_fronteira_e_a_escolhida(carteira):
    b = carteira["carteira"]
    assert b["fronteira"] and 0 < b["nuvem"]["n"] <= c.N_CARTEIRAS          # as sorteadas acima do limite por ação saem
    assert sum(k["escolhida"] for k in b["carteiras"]) == 1 and len(b["carteiras"]) == 3
    assert b["ibovespa"]["nome"] == "Ibovespa" and b["correlacao"]
    assert sum(carteira["pesos"].values()) == pytest.approx(1.0)


def test_escolha_pelo_treino_e_o_maior_sharpe_de_treino(carteira):
    e = carteira["escolhas"]
    assert e["medias_pelo_treino"] is True
    ritmos = e["comparacao_ritmos"]
    melhor = max(ritmos, key=lambda ln: ln["sharpe_treino"] if ln["sharpe_treino"] is not None else -9)
    assert (e["curta"], e["longa"]) == (melhor["curta"], melhor["longa"]) and len(ritmos) == 4


# ------------------------------------------------------------------ vazamento
def _gemeos(tmp_path_factory, nome, desde):
    """Dois caches iguais até um pregão e diferentes depois dele."""
    a = tmp_path_factory.mktemp(nome + "a")
    gravar_cache(a)
    b = tmp_path_factory.mktemp(nome + "b")
    gravar_cache(b)
    rng = np.random.default_rng(11)
    n = len(pd.read_csv(b / "preco_PETR4_SA.csv"))
    corte = desde(n)
    for t in QUATRO:
        arq = b / f"preco_{t}_SA.csv"
        df = pd.read_csv(arq, index_col=0, float_precision="round_trip")      # o treino fica idêntico, bit a bit
        fator = np.cumprod(1 + rng.normal(0, 0.03, n - corte))     # o futuro muda bastante
        for col in ("Open", "High", "Low", "Close"):
            df.iloc[corte:, df.columns.get_loc(col)] = df[col].to_numpy()[corte:] * fator
        df.to_csv(arq)
    return a, b


@pytest.fixture(scope="module")
def caches_gemeos(tmp_path_factory):
    """Mesmo treino inicial, testes diferentes."""
    return _gemeos(tmp_path_factory, "teste", lambda n: int(n * c.FRACAO_TREINO))


@pytest.fixture(scope="module")
def caches_ultima_janela(tmp_path_factory):
    """Iguais até o começo da última janela."""
    return _gemeos(tmp_path_factory, "ultima", lambda n: jan.limites(n)[-2])


def test_mudar_a_ultima_janela_nao_muda_nenhuma_escolha(caches_ultima_janela):
    a, b = caches_ultima_janela
    cfg = {"tickers": QUATRO, "divisao": "max_sharpe", "medias": "treino"}
    ra, rb = servico.executar(cfg, CsvFonte(a)), servico.executar(cfg, CsvFonte(b))
    campos = ("acoes", "pesos", "ritmo", "comparacao_ritmos", "sharpe_treino")
    for ja, jb in zip(ra["janelas"], rb["janelas"]):
        assert {k: ja[k] for k in campos} == {k: jb[k] for k in campos}       # toda escolha usa só o passado
    assert [j["retorno"] for j in ra["janelas"][:-1]] == pytest.approx([j["retorno"] for j in rb["janelas"][:-1]])
    assert ra["janelas"][-1]["retorno"] != rb["janelas"][-1]["retorno"]       # só a última janela mudou
    assert [k["pesos_janelas"] for k in ra["carteira"]["carteiras"]] == [k["pesos_janelas"] for k in rb["carteira"]["carteiras"]]


def test_divisao_otimizada_respeita_o_limite_em_toda_janela(carteira):
    for j in carteira["janelas"]:
        assert sum(j["pesos"].values()) == pytest.approx(1.0) and max(j["pesos"].values()) <= c.LIMITE_PESO + 1e-9


@pytest.mark.parametrize("divisao", ["min_variancia", "max_sharpe"])
def test_mudar_o_teste_nao_muda_pesos_nem_fronteira_nem_escolhas(caches_gemeos, divisao):
    a, b = caches_gemeos
    cfg = {"tickers": QUATRO, "divisao": divisao, "medias": "treino"}
    ra, rb = servico.executar(cfg, CsvFonte(a)), servico.executar(cfg, CsvFonte(b))
    assert ra["desempenho"]["teste"]["estrategia"] != rb["desempenho"]["teste"]["estrategia"]     # o teste mudou
    assert ra["pesos"] == rb["pesos"]
    assert ra["carteira"]["fronteira"] == rb["carteira"]["fronteira"]
    assert ra["carteira"]["nuvem"] == rb["carteira"]["nuvem"]
    assert (ra["escolhas"]["curta"], ra["escolhas"]["longa"]) == (rb["escolhas"]["curta"], rb["escolhas"]["longa"])
    assert [x["sharpe_treino"] for x in ra["variacoes"]["combinacoes"]] == [x["sharpe_treino"] for x in rb["variacoes"]["combinacoes"]]
    assert [k["treino"] for k in ra["carteira"]["carteiras"]] == [k["treino"] for k in rb["carteira"]["carteiras"]]


# ------------------------------------------------------------------ erros e dados faltando
def test_sem_dados_da_mensagem_clara(tmp_path):
    with pytest.raises(ValueError, match="Nenhuma ação"):
        servico.executar({"tickers": ["PETR4"]}, CsvFonte(tmp_path))


def test_historico_curto_e_recusado(tmp_path):
    gravar_cache(tmp_path, n=300)
    with pytest.raises(ValueError, match="Nenhuma ação"):
        servico.executar({"tickers": ["PETR4"]}, CsvFonte(tmp_path))


def test_sem_selic_ainda_roda_e_avisa(tmp_path):
    gravar_cache(tmp_path)
    (tmp_path / "sgs_11.csv").unlink()
    r = servico.executar({"tickers": ["PETR4"]}, CsvFonte(tmp_path))
    assert any("Selic" in a for a in r["avisos"])
    assert r["foi_sorte"]["ic_estrategia"] is None and r["leitura"]["testes"]["intervalo"]["status"] == "nao_se_aplica"


def test_acao_sem_dados_vira_aviso(pasta_sintetica):
    r = servico.executar({"tickers": ["PETR4", "ABEV3", "CSAN3"]}, CsvFonte(pasta_sintetica))
    assert r["tickers"] == ["PETR4", "ABEV3"] and any("CSAN3" in a for a in r["avisos"])


# ------------------------------------------------------------------ conferência independente
def test_conferencia_independente_das_metricas(pasta_sintetica, um):
    """Refaz retorno, Sharpe e queda à parte, com os mesmos dados do cache, pela curva completa."""
    from quant import estrategias
    from quant.backtest import executar_backtest

    df = pd.read_csv(pasta_sintetica / "preco_PETR4_SA.csv", index_col=0, parse_dates=True)
    sel = pd.read_csv(pasta_sintetica / "sgs_11.csv", index_col=0, parse_dates=True)["valor"]
    r = executar_backtest(df, estrategias.gerar_sinais(df, 12, 50), 100_000, 10, 20, c.CUSTOS["tarifas_b3"]["pct"])
    corte = int(len(df) * c.FRACAO_TREINO)
    teste = r.equity.iloc[corte - 1:]
    ret = teste.pct_change().dropna().to_numpy()
    assert sel.iloc[0] == 0.045
    # a Selic paga o imposto da renda fixa: valor líquido de resgate a cada dia, aplicando tudo no primeiro pregão
    dias = (df.index - df.index[0]).days.to_numpy()
    aliq = np.where(dias <= 180, 0.225, np.where(dias <= 360, 0.20, np.where(dias <= 720, 0.175, 0.15)))
    liquido = 1 + (1.00045 ** np.arange(1, len(df) + 1) - 1) * (1 - aliq)
    selic = (liquido[1:] / liquido[:-1] - 1)[corte - 1:]
    assert len(selic) == len(ret)
    # nesta ação a regra não teve lucro tributável, então a curva depois do imposto é a própria curva da simulação
    assert um["imposto"]["estrategia"]["total"] == 0
    d = um["desempenho"]["teste"]["estrategia"]
    assert d["retorno_total"] == pytest.approx(teste.iloc[-1] / teste.iloc[0] - 1)
    assert d["sharpe"] == pytest.approx((ret.mean() - selic.mean()) * 252 / (ret.std(ddof=1) * np.sqrt(252)), rel=1e-3)
    pico = np.maximum.accumulate(teste.to_numpy())
    assert d["max_drawdown"] == pytest.approx((teste.to_numpy() / pico - 1).min())


def test_metrica_usa_252_pregoes():
    assert m.DIAS_ANO == 252


# ------------------------------------------------------------------ isolamento do núcleo
def test_nucleo_nao_carrega_apresentacao(pasta_sintetica):
    codigo = (
        "import sys, json\n"
        f"sys.path.insert(0, {str(RAIZ)!r})\n"
        "from quant import servico\n"
        "from quant.dados import CsvFonte\n"
        f"r = servico.executar({{'tickers': ['PETR4']}}, CsvFonte({str(pasta_sintetica)!r}))\n"
        "json.dumps(r)\n"
        "ruins = [m for m in ('plotly', 'streamlit', 'reportlab', 'django', 'matplotlib') if m in sys.modules]\n"
        "print(ruins)\n"
    )
    saida = subprocess.run([sys.executable, "-c", codigo], capture_output=True, text=True, timeout=180)
    assert saida.returncode == 0, saida.stderr
    assert saida.stdout.strip() == "[]"


def test_cada_operacao_traz_variacao_tarifas_e_a_parte_do_imposto(fonte):
    r = servico.executar({"tickers": TICKERS[:2], "custo": "tarifas_b3"}, fonte)
    ops = r["operacoes"]["lista"]
    assert ops and {"variacao_pct", "variacao_rs", "custo", "imposto", "resultado_final"} <= set(ops[0])
    for x in ops:
        assert x["variacao_rs"] - x["custo"] == pytest.approx(x["pnl"])
        assert x["resultado_final"] == pytest.approx(x["pnl"] - x["imposto"])
        assert x["imposto"] >= 0 and (x["pnl"] > 0 or x["imposto"] == 0)
    assert sum(x["imposto"] for x in ops) == pytest.approx(r["imposto"]["estrategia"]["total"])


def test_o_saldo_em_conta_fecha_com_o_patrimonio(fonte):
    """O extrato não perde nem inventa dinheiro: o saldo nunca fica negativo e o patrimônio final é o capital mais o
    resultado final de cada operação."""
    r = servico.executar({"tickers": TICKERS[:2], "custo": "tarifas_b3", "capital": 50_000}, fonte)
    ops = r["operacoes"]["lista"]
    assert ops and all(x["saldo_apos_compra"] >= 0 and x["saldo_apos_venda"] >= 0 for x in ops)
    for x in ops:
        assert x["valor_compra"] == pytest.approx(x["quantidade"] * x["preco_entrada"])
        assert x["valor_venda"] - x["valor_compra"] == pytest.approx(x["variacao_rs"])
    # sem posição aberta, o saldo é todo o patrimônio: na última venda ele não passa do valor final da curva
    ultima = max(str(x["data_saida"]) for x in ops)
    saldo_final = max(x["saldo_apos_venda"] for x in ops if str(x["data_saida"]) == ultima)
    assert saldo_final <= r["desempenho"]["inteiro"]["estrategia"]["valor_final"] + 1e-6
    assert r["desempenho"]["inteiro"]["estrategia"]["valor_final"] == pytest.approx(r["escolhas"]["capital"] + sum(x["resultado_final"] for x in ops))



def test_progresso_avisa_as_etapas_sem_mudar_o_resultado(pasta_sintetica):
    """O aviso de progresso (usado pela tela de espera do portal) só informa o andamento."""
    vistas = []
    com = servico.executar({"tickers": ["PETR4"]}, CsvFonte(pasta_sintetica), ao_progresso=vistas.append)
    sem = servico.executar({"tickers": ["PETR4"]}, CsvFonte(pasta_sintetica))
    assert vistas == list(servico.ETAPAS)
    assert json.dumps(com, sort_keys=True, default=str) == json.dumps(sem, sort_keys=True, default=str)
