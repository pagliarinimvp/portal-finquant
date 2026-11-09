from apresentacao.formatacao import nota_salto


def _op(data, retorno, motivo="stop"):
    return {"data_saida": data, "ticker": "PETR4", "retorno_pct": retorno, "motivo": motivo}


def test_nota_salto_explica_perda_maior_que_o_limite():
    ops = [_op("2017-05-18", -21.106), _op("2021-02-22", -20.11), _op("2018-08-21", -10.057), _op("2019-01-02", -25.0, "sinal")]
    txt = nota_salto(ops, 10.0)
    assert "2 operações" in txt and "18/05/2017, PETR4 perdeu 21,1%" in txt and "22/02/2021" in txt
    assert "2018" not in txt and "2019" not in txt       # perda no limite (com tarifa) e saída pelo sinal ficam de fora


def test_nota_salto_some_sem_salto_ou_sem_limite():
    assert nota_salto([_op("2018-08-21", -10.057)], 10.0) is None
    assert nota_salto([_op("2017-05-18", -21.1)], None) is None
