"""Seleção automática e filtro de qualidade dos dados. Sem rede."""
import numpy as np
import pandas as pd
import pytest

from quant import config as c
from quant import selecao as sel
from quant import servico
from quant.dados import CsvFonte, problemas_de_dados
from conftest import grava_preco, gravar_cache, inicio_sintetico, serie_ohlc


# ------------------------------------------------------------------ filtro de qualidade
def test_precos_normais_nao_tem_problema():
    assert problemas_de_dados(serie_ohlc(600, 1)) == []


def test_intervalo_sem_dados_e_apontado():
    df = serie_ohlc(600, 1)
    assert "intervalo de" in problemas_de_dados(df.drop(df.index[100:130]))[0]


def test_muitos_dias_sem_negocios_sao_apontados():
    df = serie_ohlc(600, 1)
    df.iloc[:60, df.columns.get_loc("Volume")] = 0
    assert "sem negócios" in problemas_de_dados(df)[0]


def _com_salto(volume_multiplo: float):
    df = serie_ohlc(600, 1, sigma=0.005)
    df.iloc[300:, df.columns.get_loc("Close")] *= 2.0
    df.iloc[300, df.columns.get_loc("Volume")] = df["Volume"].iloc[280:300].median() * volume_multiplo
    return df


def test_salto_sem_explicacao_e_apontado():
    assert "sem movimento do mercado" in problemas_de_dados(_com_salto(1.0))[0]


def test_salto_com_volume_alto_e_aceito():
    assert problemas_de_dados(_com_salto(10.0)) == []


def test_salto_com_o_mercado_em_forte_movimento_e_aceito():
    df = _com_salto(1.0)
    ibov = pd.Series(0.0, index=df.index)
    ibov.iloc[300] = -0.14
    assert problemas_de_dados(df, ibov) == []


# ------------------------------------------------------------------ candidatas
def test_candidatas_excluem_historico_curto_e_dados_antigos_e_dizem_o_motivo():
    inteira = serie_ohlc(800, 1)
    dados = {"BOA": inteira, "NOVA": serie_ohlc(800, 2).iloc[300:], "PAROU": serie_ohlc(800, 3).iloc[:700]}
    candidatas, fora = sel.filtrar_candidatas(dados)
    assert list(candidatas) == ["BOA"]
    motivos = {x["ticker"]: x["motivo"] for x in fora}
    assert "só começa" in motivos["NOVA"] and "param em" in motivos["PAROU"]


# ------------------------------------------------------------------ a seleção
def _dfs(n=900, k=14):
    return {f"A{i:02d}": serie_ohlc(n, semente=i, mu=0.0002 + 0.0002 * (i % 5)) for i in range(k)}


def _selecionar(dfs, corte=630, medias="intermediario", **kw):
    args = dict(stop=10.0, alvo=20.0, custo_pct=0.5, capital=1_000_000.0, rf=0.0)
    args.update(kw)
    return sel.selecionar(dfs, corte, medias, **args)


def test_seleciona_ate_o_limite_e_em_ordem_de_nota():
    r = _selecionar(_dfs())
    assert 1 <= len(r["tickers"]) <= c.MAX_ACOES
    notas = {x["ticker"]: x["sharpe_treino"] for x in r["ranking"]}
    valores = [notas[t] for t in r["tickers"]]
    assert valores == sorted(valores, reverse=True) and all(v > 0 for v in valores)


def test_exige_operacoes_minimas():
    r = _selecionar(_dfs())
    n = {x["ticker"]: x["n_trades"] for x in r["ranking"]}
    assert all(n[t] >= sel.MIN_OPERACOES_TREINO for t in r["tickers"])


def test_teste_nao_influencia_a_selecao():
    """Mudar os preços depois do corte não pode mudar a carteira nem as notas."""
    dfs = _dfs()
    original = _selecionar(dfs)
    alterado = {}
    for t, df in dfs.items():
        x = df.copy()
        ruido = np.random.default_rng(1).uniform(0.5, 1.5, len(x) - 630)
        for col in ("Open", "High", "Low", "Close"):
            x.iloc[630:, x.columns.get_loc(col)] = x[col].iloc[630:].to_numpy() * ruido
        alterado[t] = x
    novo = _selecionar(alterado)
    assert novo["tickers"] == original["tickers"] and novo["ranking"] == original["ranking"]


def test_nenhuma_aprovada_avisa_em_vez_de_montar_carteira_ruim():
    dfs = {f"Q{i}": serie_ohlc(900, semente=i, mu=-0.003) for i in range(4)}
    with pytest.raises(ValueError, match="Nenhuma ação"):
        _selecionar(dfs)


def test_capital_sem_dinheiro_para_um_lote_nao_passa():
    with pytest.raises(ValueError, match="Nenhuma ação"):
        _selecionar(_dfs(), capital=1_000.0)      # R$ 100 por ação não compram um lote de 100


def test_com_o_treino_escolhendo_vence_a_maior_media():
    r = _selecionar(_dfs(), medias=c.MEDIAS_PELO_TREINO)
    com_nota = [p for p in r["pontuacao_ritmos"] if p["sharpe_treino"] is not None]
    assert len(r["pontuacao_ritmos"]) == 4
    assert r["ritmo"] == max(com_nota, key=lambda p: p["sharpe_treino"])["medias"]


# ------------------------------------------------------------------ pelo serviço
def test_servico_automatico(fonte):
    r = servico.executar({"selecao": "automatica"}, fonte)
    s = r["selecao"]
    assert s["n_candidatas"] == 12 and 1 <= len(r["tickers"]) <= c.MAX_ACOES
    assert s["n_tentativas"] == c.N_COMBINACOES * s["n_candidatas"]
    assert r["foi_sorte"]["sharpe_desconto"]["n_tentativas"] == s["n_tentativas"]
    assert {x["ticker"] for x in s["fora"]} >= {"AXIA3"}
    assert all(x["retorno_teste"] is not None for x in s["ranking"] if x["ticker"] in r["tickers"])
    assert r["config"]["tickers"] == list(r["config"]["tickers"]) and r["leitura"]["testes"]["desconto"]["status"]


def test_servico_manual_nao_traz_selecao_e_mantem_as_tentativas(fonte):
    r = servico.executar({"tickers": ["PETR4"]}, fonte)
    assert r["selecao"] is None and r["foi_sorte"]["sharpe_desconto"]["n_tentativas"] == c.N_COMBINACOES


def test_acao_curta_nao_encurta_a_analise_da_selecao(tmp_path):
    gravar_cache(tmp_path)
    inicio = inicio_sintetico()
    grava_preco(tmp_path, "HAPV3.SA", serie_ohlc(1500, 50, inicio=inicio).iloc[700:])
    r = servico.executar({"selecao": "automatica"}, CsvFonte(tmp_path))
    assert r["periodo"]["n_pregoes"] == 1500
    assert any(x["ticker"] == "HAPV3" and "só começa" in x["motivo"] for x in r["selecao"]["fora"])


def test_treino_e_teste_nao_mudam_com_a_carteira_escolhida(fonte):
    r = servico.executar({"selecao": "automatica"}, fonte)
    assert r["periodo"]["n_treino"] == int(1500 * c.FRACAO_TREINO)


def test_manual_avisa_sobre_erro_nos_dados(tmp_path):
    gravar_cache(tmp_path)
    df = serie_ohlc(1500, 0, inicio=inicio_sintetico(), sigma=0.005)
    df.iloc[900:, df.columns.get_loc("Close")] *= 2.0
    grava_preco(tmp_path, "PETR4.SA", df)
    r = servico.executar({"tickers": ["PETR4"]}, CsvFonte(tmp_path))
    assert any("PETR4" in a and "erro na fonte" in a for a in r["avisos"])


def test_operacoes_de_treino_e_teste_somam_o_historico(fonte):
    for cfg in ({"tickers": ["PETR4"], "protecao": "sem"}, {"tickers": ["PETR4", "VALE3", "ITUB4"]}):
        o = servico.executar(cfg, fonte)["operacoes"]
        tr, te, tudo = o["treino"], o["teste"], o["inteiro"]
        for k in ("n_trades", "n_ganhos", "n_perdas"):
            assert tr[k] + te[k] == tudo[k], k
        assert tr["resultado_liquido"] + te["resultado_liquido"] == pytest.approx(tudo["resultado_liquido"])
        assert tr["custos_pagos"] + te["custos_pagos"] == pytest.approx(tudo["custos_pagos"])
        assert all(tr["saidas"][k] + te["saidas"][k] == tudo["saidas"][k] for k in tudo["saidas"])
        assert 0 <= tr["tempo_comprado"] <= 1 and 0 <= te["tempo_comprado"] <= 1
        assert tr["queda_maxima"] <= 0 and te["queda_maxima"] <= 0 and tudo["queda_maxima"] <= min(tr["queda_maxima"], te["queda_maxima"]) + 1e-12


def test_custos_pagos_conferem_com_a_conta_a_mao(fonte):
    o = servico.executar({"tickers": ["PETR4"]}, fonte)["operacoes"]
    conta = sum(0.0003 * t["quantidade"] * (t["preco_entrada"] + t["preco_saida"]) for t in o["lista"])
    assert o["inteiro"]["custos_pagos"] == pytest.approx(conta)
    sem = servico.executar({"tickers": ["PETR4"], "custo": "sem_custo"}, fonte)["operacoes"]["inteiro"]
    assert sem["custos_pagos"] == 0


def test_recuperacao_do_pior_momento():
    idx = pd.bdate_range("2024-01-01", periods=6)
    voltou = servico._pior_momento(pd.Series([100.0, 120.0, 90.0, 100.0, 125.0, 110.0], index=idx))
    assert voltou["data_recuperacao"] == idx[4] and voltou["pregoes_recuperacao"] == 2
    nao_voltou = servico._pior_momento(pd.Series([100.0, 120.0, 90.0, 100.0, 110.0, 115.0], index=idx))
    assert nao_voltou["data_recuperacao"] is None and nao_voltou["pregoes_recuperacao"] is None


def _quem(r) -> dict:
    return {x["escolha"]: x["quem"] for x in r["decisoes_treino"]["itens"]}


def test_o_que_o_treino_decidiu_nas_cinco_situacoes(fonte):
    r = servico.executar({"tickers": ["PETR4"]}, fonte)
    assert not r["decisoes_treino"]["treino_decidiu"] and _quem(r)["Como dividir o dinheiro"] == "Não se aplica"

    r = servico.executar({"tickers": ["PETR4", "VALE3"], "divisao": "igual"}, fonte)
    assert not r["decisoes_treino"]["treino_decidiu"] and _quem(r)["Como dividir o dinheiro"] == "Você"

    r = servico.executar({"tickers": ["PETR4", "VALE3"], "divisao": "min_variancia"}, fonte)
    assert r["decisoes_treino"]["treino_decidiu"] and _quem(r)["Como dividir o dinheiro"] == "Treino"
    assert next(iter(r["pesos"])) in r["decisoes_treino"]["itens"][2]["resultado"]

    r = servico.executar({"tickers": ["PETR4"], "medias": "treino"}, fonte)
    assert _quem(r)["Qual ritmo"] == "Treino" and r["escolhas"]["medias"] in r["decisoes_treino"]["itens"][1]["resultado"]

    r = servico.executar({"selecao": "automatica"}, fonte)
    assert _quem(r)["Quais ações"] == "Treino" and "candidatas" in r["decisoes_treino"]["itens"][0]["resultado"]


def _titulos(r):
    return [x["titulo"] for x in r["roteiro_treino"]["passos"]]


def test_roteiro_do_treino_em_cada_situacao(pasta_sintetica):
    from quant import servico
    from quant.dados import CsvFonte
    fonte = CsvFonte(pasta_sintetica)
    assert _titulos(servico.executar({"tickers": ["PETR4"]}, fonte)) == ["Separar o treino inicial", "Nada a escolher", "Simular e medir"]
    assert _titulos(servico.executar({"tickers": ["PETR4"], "medias": "treino"}, fonte)) == ["Separar o treino inicial", "Comparar os ritmos", "Andar uma janela", "Simular e medir"]
    igual = servico.executar({"tickers": ["PETR4", "VALE3"]}, fonte)
    assert _titulos(igual) == ["Separar o treino inicial", "Dividir o dinheiro", "Simular e medir"]
    otimo = servico.executar({"tickers": ["PETR4", "VALE3"], "divisao": "max_sharpe", "medias": "treino"}, fonte)
    assert _titulos(otimo) == ["Separar o treino inicial", "Calcular os pesos", "Comparar os ritmos", "Andar uma janela", "Simular e medir"]
    assert "maior índice de Sharpe" in otimo["roteiro_treino"]["passos"][1]["texto"]
    variancia = servico.executar({"tickers": ["PETR4", "VALE3"], "divisao": "min_variancia"}, fonte)
    assert "menor oscilação" in variancia["roteiro_treino"]["passos"][1]["texto"]
    auto = servico.executar({"selecao": "automatica", "medias": "treino"}, fonte)
    assert _titulos(auto)[:6] == ["Separar o treino inicial", "Filtrar as ações", "Simular cada ação", "Dar uma nota", "Aplicar os critérios", "Escolher o ritmo"]


def test_regra_descrita_com_os_parametros_da_analise(pasta_sintetica):
    from quant import servico
    from quant.dados import CsvFonte
    fonte = CsvFonte(pasta_sintetica)
    com_limite = {x["titulo"]: x["texto"] for x in servico.executar({"tickers": ["PETR4"], "medias": "rapido", "protecao": "3_1"}, fonte)["roteiro_treino"]["regra"]}
    assert "últimos 10 fechamentos" in com_limite["Calcular as médias"] and "últimos 20" in com_limite["Calcular as médias"]
    assert "10% abaixo" in com_limite["Vender"] and "30% acima" in com_limite["Vender"] and "vale o de perda" in com_limite["Vender"]
    assert "0,03%" in com_limite["Pagar o custo"] and "Com várias ações" not in com_limite
    sem = {x["titulo"]: x["texto"] for x in servico.executar({"tickers": ["PETR4", "VALE3"], "protecao": "sem", "custo": "sem_custo"}, fonte)["roteiro_treino"]["regra"]}
    assert "limite" not in sem["Vender"] and "não pagam custo" in sem["Pagar o custo"] and "Com várias ações" in sem


def test_primeira_operacao_mostra_um_cruzamento_verdadeiro(pasta_sintetica):
    """As médias do exemplo são as do dia do sinal, a compra é no pregão seguinte e o resultado confere com a lista de operações."""
    import pandas as pd

    from quant import servico
    from quant.dados import CsvFonte
    r = servico.executar({"tickers": ["PETR4"]}, CsvFonte(pasta_sintetica))
    x = r["primeira_operacao_treino"]
    assert x["curta_sinal"] > x["longa_sinal"] and x["curta_anterior"] <= x["longa_anterior"]
    assert pd.Timestamp(x["data_sinal"]) < pd.Timestamp(x["data_entrada"]) <= pd.Timestamp(r["periodo"]["fim_treino"])
    primeira = r["operacoes"]["lista"][0]
    assert x["data_entrada"] == primeira["data_entrada"] and x["resultado"] == primeira["pnl"] and x["quantidade"] == primeira["quantidade"]
    assert "A primeira operação do treino" in r["roteiro_treino"]["exemplo"] and "R$" in r["roteiro_treino"]["exemplo"]
    # O gráfico do exemplo cobre do sinal à venda, e as séries têm o mesmo tamanho.
    gr = x["grafico"]
    datas = pd.to_datetime(gr["datas"])
    assert datas[0] <= pd.Timestamp(x["data_sinal"]) and pd.Timestamp(x["data_saida"]) <= datas[-1]
    assert len(gr["preco"]) == len(gr["media_curta"]) == len(gr["media_longa"]) == len(datas)
    from apresentacao import graficos_plotly as g
    assert any(a.text == "Sinal" for a in g.fig_primeira_operacao(x, r["escolhas"]).layout.annotations)


def test_medidas_tem_como_ler_sem_faixa_de_bom_ou_ruim():
    """O referencial vem de um ponto matemático, de uma comparação ou de um critério declarado. Faixas sem fonte, como "acima de 1 é bom", não entram."""
    from apresentacao import textos as tx
    from quant.glossario import GLOSSARIO
    medidas = ("retorno_anualizado", "volatilidade", "sharpe", "drawdown", "sortino", "retorno_por_queda", "payoff", "expectativa", "taxa_acerto", "fator_lucro",
               "p_valor", "intervalo_confianca", "alfa_beta", "sharpe_desconto", "monte_carlo", "correlacao")
    assert all(GLOSSARIO[k].get("como_ler") for k in medidas)
    assert "Acima de 1 é considerado bom" not in str(GLOSSARIO)
    assert all("é bom" not in x for x in tx.SHARPE_LEITURA)


def test_todas_as_fontes_do_glossario_existem():
    from quant.glossario import GLOSSARIO
    from quant.referencias import REFERENCIAS
    from apresentacao.textos import CONTA
    usadas = {i for t in GLOSSARIO.values() for i in t["fontes"]} | {i for _, ids in CONTA.values() for i in ids}
    assert usadas <= set(REFERENCIAS)
    assert all(r["url"].startswith("https://") and r["citacao"] for r in REFERENCIAS.values())


def test_nada_cita_o_curso():
    """Os arquivos versionados não citam o curso, nem módulos ou aulas dele."""
    import re
    import subprocess
    from pathlib import Path
    raiz = Path(__file__).resolve().parents[1]
    arquivos = subprocess.run(["git", "ls-files", "--cached", "--others", "--exclude-standard"], cwd=raiz, capture_output=True, text=True, check=True).stdout.splitlines()
    trechos = [r"Trading\s+com\s+Dados", r"M[oó]dulos?\s+\d", r"Jornada\s+Quant", r"Sala\s+de\s+Estudos", r"Aula\s+ao\s+vivo", r"\bPMF\s+2", r"\bdo[\s_]+curso\b", r"\bnas\s+aulas\b", r"\baulas?\s+\d"]
    padrao = re.compile("|".join(trechos), re.I)
    achados = []
    for nome in arquivos:
        p = raiz / nome
        if nome == "tests/test_selecao.py" or p.suffix not in {".py", ".md", ".txt", ".bat", ".toml", ".vbs"} or not p.exists():
            continue
        for i, linha in enumerate(p.read_text(encoding="utf-8", errors="ignore").splitlines(), 1):
            if padrao.search(linha):
                achados.append(f"{nome}:{i}")
    assert not achados, achados
