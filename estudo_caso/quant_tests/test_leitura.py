"""O veredito responde certo em casos conhecidos e nunca recomenda investir."""
import copy
import re

import pytest

from quant import leitura
from quant.dados import CsvFonte
from quant import servico


def base():
    """Um resultado mínimo em que tudo passa."""
    return {
        "foi_sorte": {
            "ic_estrategia": {"baixo_anual": 0.02, "alto_anual": 0.18, "inclui_zero": False},
            "alfa_beta": {"alfa_anual": 0.08, "beta": 0.5, "p_alfa": 0.01, "alfa_significativo": True},
            "sharpe_desconto": {"sharpe": 1.5, "sharpe_ajustado": 1.1, "p_ajustado": 0.02, "n_tentativas": 16, "significativo": True},
        },
        "escolhas": {"capital": 100_000.0},
        "periodo": {"inicio": "2016-11-07", "fim": "2026-11-06"},
        "desempenho": {
            "inteiro": {"estrategia": {"retorno_total": 0.8, "valor_final": 180_000.0}},
            "treino": {"estrategia": {"sharpe": 1.2}},
            "teste": {"estrategia": {"sharpe": 1.0, "retorno_total": 0.5}, "selic": {"retorno_total": 0.3},
                      "buy_hold": {"retorno_total": 0.2, "max_drawdown": -0.40}},
        },
        "variacoes": {
            "ano_a_ano": {"n_acima": 7, "n_avaliados": 10},
            "n_bateram_selic": 12, "n_combinacoes": 16,
            "custos": [{"custo": "tarifas_b3", "retorno_teste": 0.5, "retorno_selic_teste": 0.3, "bateu_selic": True, "n_trades": 80},
                       {"custo": "sem_custo", "retorno_teste": 0.6, "retorno_selic_teste": 0.35, "bateu_selic": True, "n_trades": 80}],
        },
        "sequencia": {
            "monte_carlo": {"n_simulacoes": 10_000, "queda_mediana": -0.15, "queda_pessimista": -0.25},
            "sem_melhores": {"resultado_total": 5000.0, "resultado_sem": 1000.0, "ainda_positivo": True},
        },
    }


def status(r, id_):
    return leitura.montar(r)["testes"][id_]["status"]


def test_tudo_passa():
    v = leitura.montar(base())
    assert v["n_passou"] == v["n_aplicaveis"] == 9
    assert "Há evidência estatística" in v["frase"]


def test_tres_perguntas_separam_ganhar_dinheiro_de_passar():
    r = base()
    r["desempenho"]["teste"]["estrategia"]["retorno_total"] = 0.05           # ganhou, mas menos que as duas alternativas
    v = leitura.montar(r)
    dinheiro, alternativas, confianca = v["perguntas"]
    assert dinheiro["resposta"] == "Sim" and "R$ 180.000" in dinheiro["texto"].replace(" ", " ")
    assert alternativas["resposta"] == "Não" and "30,0% da Selic e 20,0% de comprar e segurar" in alternativas["texto"]
    assert confianca["resposta"] == f'{v["n_passou"]} de {v["n_aplicaveis"]}'
    assert v["linha"] == f'nas janelas de teste, a regra rendeu 5,0%, contra 30,0% da Selic; passou em {v["n_passou"]} de {v["n_aplicaveis"]} testes aplicáveis.'
    assert "mesmo quando a regra ganhou dinheiro" in v["por_que_nao_passou"]


def test_ganhar_de_uma_alternativa_so_e_em_parte():
    r = base()
    r["desempenho"]["teste"]["estrategia"]["retorno_total"] = 0.25           # acima de comprar e segurar, abaixo da Selic
    assert leitura.montar(r)["perguntas"][1]["resposta"] == "Em parte"
    r["desempenho"]["inteiro"]["estrategia"]["retorno_total"] = -0.1
    assert leitura.montar(r)["perguntas"][0]["resposta"] == "Não"


def test_cada_teste_reprova_no_caso_contrario():
    casos = {
        "intervalo": lambda r: r["foi_sorte"]["ic_estrategia"].update(baixo_anual=-0.02, inclui_zero=True),
        "alfa": lambda r: r["foi_sorte"]["alfa_beta"].update(p_alfa=0.3, alfa_significativo=False),
        "desconto": lambda r: r["foi_sorte"]["sharpe_desconto"].update(p_ajustado=0.4, significativo=False),
        "treino_teste": lambda r: r["desempenho"]["teste"]["estrategia"].update(sharpe=0.3),
        "ano_a_ano": lambda r: r["variacoes"]["ano_a_ano"].update(n_acima=5),
        "sensibilidade": lambda r: r["variacoes"].update(n_bateram_selic=8),
        "custo": lambda r: r["variacoes"]["custos"][0].update(bateu_selic=False),
        "monte_carlo": lambda r: r["sequencia"]["monte_carlo"].update(queda_pessimista=-0.5),
        "sem_melhores": lambda r: r["sequencia"]["sem_melhores"].update(resultado_sem=-10.0, ainda_positivo=False),
    }
    for id_, altera in casos.items():
        r = copy.deepcopy(base())
        altera(r)
        assert status(r, id_) == leitura.NAO_PASSOU, id_


def test_nao_se_aplica_em_vez_de_reprovar_por_falta_de_dados():
    r = base()
    r["foi_sorte"]["ic_estrategia"] = None
    r["foi_sorte"]["alfa_beta"] = None
    r["sequencia"]["monte_carlo"] = None
    r["sequencia"]["sem_melhores"] = None
    for id_ in ("intervalo", "alfa", "monte_carlo", "sem_melhores"):
        assert status(r, id_) == leitura.NAO_SE_APLICA, id_


def test_linguagem_cautelosa_quando_falta_evidencia():
    r = base()
    r["foi_sorte"]["ic_estrategia"].update(baixo_anual=-0.02, inclui_zero=True)
    texto = leitura.montar(r)["testes"]["intervalo"]["significado"]
    assert "Não há evidência suficiente" in texto and "não prova" in texto


def test_frase_nao_afirma_evidencia_sem_os_testes():
    r = base()
    r["foi_sorte"]["ic_estrategia"].update(baixo_anual=-0.02, inclui_zero=True)
    assert "não há evidência suficiente" in leitura.montar(r)["frase"]
    r["desempenho"]["teste"]["estrategia"]["retorno_total"] = 0.1
    assert "não superou a Selic" in leitura.montar(r)["frase"]


PROIBIDAS = r"recomend(amos|o )|compre |invista|deve investir|garant|lucro certo|vale a pena investir"


@pytest.mark.parametrize("cfg", [{"tickers": ["PETR4"]},
                                 {"tickers": ["PETR4", "VALE3", "ITUB4"], "divisao": "max_sharpe", "medias": "treino", "protecao": "sem"}])
def test_texto_nunca_recomenda_investir(pasta_sintetica, cfg):
    v = servico.executar(cfg, CsvFonte(pasta_sintetica))["leitura"]
    textos = [v["frase"]] + [t["significado"] for t in v["testes"].values()]
    assert v["n_passou"] <= v["n_aplicaveis"] and "não é a probabilidade" in v["nota_contagem"]
    for texto in textos:
        assert not re.search(PROIBIDAS, texto, re.I), texto


def test_cada_criterio_tecnico_esta_declarado():
    assert set(leitura.CRITERIOS_TECNICOS) >= {"treino_teste", "ano_a_ano", "sensibilidade", "monte_carlo"}
