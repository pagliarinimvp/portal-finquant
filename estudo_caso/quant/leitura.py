"""Transforma os números em linguagem comum: o veredito e o "o que isso significa" de cada teste.

Fica no núcleo para o Portal FinQuant reaproveitar. Regras de redação, em linha com a declaração da ASA sobre p-valores
(Wasserstein e Lazar, 2016):
* "não há evidência suficiente" em vez de "não funciona";
* magnitude junto com probabilidade;
* nada de recomendar investir. A contagem de testes não é probabilidade de ganho.

Os critérios de "passou" são escolhas técnicas desta ferramenta e estão declarados em `CRITERIOS_TECNICOS`.
Todo número vem com o referencial para lê-lo: um ponto matemático (0 ou 1), uma comparação no mesmo período ou o critério desta ferramenta.
"""
from .config import LIMITE_PESO, LOTE, MAX_ACOES, MEDIAS

PASSOU, NAO_PASSOU, NAO_SE_APLICA = "passou", "nao_passou", "nao_se_aplica"

BLOCOS = {
    "sorte": "Foi sorte?",
    "variacoes": "Aguenta variações?",
    "sequencia": "E se a sequência fosse outra?",
}

CRITERIOS_TECNICOS = {
    "sorte": "Intervalo, alfa e Sharpe com desconto usam o nível de significância de 0,05 e precisam indicar diferença a favor da regra.",
    "custo": "Ganhar da Selic no teste pagando as tarifas da B3 e o imposto de renda, com a Selic também depois do imposto.",
    "treino_teste": "Sharpe do teste (as janelas em sequência) positivo e de pelo menos metade do Sharpe do treino inicial.",
    "ano_a_ano": "Ganhar da Selic em mais da metade dos anos avaliados, os que têm ao menos meio ano de pregões (126).",
    "sensibilidade": "Mais da metade das combinações ganha da Selic no teste.",
    "monte_carlo": "O cenário pessimista não passa da queda real de comprar e segurar no teste.",
    "sem_melhores": "Resultado ainda positivo sem as 3 maiores operações.",
}



def _pct(x, casas=1) -> str:
    return "n/d" if x is None else f"{100 * x:.{casas}f}%".replace(".", ",")


def _sinal(x, casas=1) -> str:
    """Número em pontos percentuais com sinal, sem a unidade."""
    return "n/d" if x is None else f"{100 * x:+.{casas}f}".replace(".", ",")


def _pp(x, casas=1) -> str:
    """Pontos percentuais com sinal."""
    return "n/d" if x is None else f"{_sinal(x, casas)} pontos percentuais"


def _queda(x) -> str:
    """Tamanho da queda, sem o sinal: 'caiu 22,2%'."""
    return "n/d" if x is None else _pct(abs(x))


def _num(x, casas=2) -> str:
    return "n/d" if x is None else f"{x:.{casas}f}".replace(".", ",")


def _p(x) -> str:
    if x is None:
        return "n/d"
    return "menor que 0,001" if x < 0.001 else _num(x, 3)


def _brl(x) -> str:
    if x is None:
        return "n/d"
    sinal = "-" if x < 0 else ""
    return f"{sinal}R$ {abs(x):,.0f}".replace(",", ".")      # espaço que não quebra a linha


def _inteiro(x) -> str:
    return f"{x:,}".replace(",", ".")


def _data(x) -> str:
    """AAAA-MM-DD para DD/MM/AAAA."""
    return f"{x[8:10]}/{x[5:7]}/{x[:4]}"


def _teste(id_, bloco, nome, pergunta, status, significado) -> dict:
    return {"id": id_, "bloco": bloco, "nome": nome, "pergunta": pergunta, "status": status, "significado": significado}


# ------------------------------------------------------------------------------- 1. foi sorte?
def _ic(sorte) -> dict:
    pergunta = "Qual é a faixa plausível do ganho acima da Selic? Ela inclui o zero?"
    nome = "Intervalo de confiança de 95%"
    ic = sorte.get("ic_estrategia")
    if not ic or ic.get("baixo_anual") is None:
        return _teste("intervalo", "sorte", nome, pergunta, NAO_SE_APLICA, "Sem Selic ou sem dados para calcular a faixa.")
    faixa = f"de {_sinal(ic['baixo_anual'])} a {_sinal(ic['alto_anual'])} pontos percentuais ao ano"
    if ic["baixo_anual"] > 0:
        return _teste("intervalo", "sorte", nome, pergunta, PASSOU,
                      f"A faixa plausível do ganho acima da Selic vai {faixa}. Ela fica toda acima de zero: "
                      "mesmo a ponta pior da faixa ainda ganha da Selic.")
    return _teste("intervalo", "sorte", nome, pergunta, NAO_PASSOU,
                  f"A faixa plausível do ganho acima da Selic vai {faixa}. Como ela "
                  + ("inclui o zero, ganhar nada a mais que a Selic é um resultado plausível. Não há evidência suficiente de que a "
                     "regra supere a Selic. Isso não prova que ela não funciona: o período de teste pode ser curto para detectar "
                     "uma vantagem pequena."
                     if ic["inclui_zero"] else "fica toda abaixo de zero, há evidência de que a regra rendeu menos que a Selic."))


def _alfa(sorte) -> dict:
    pergunta = "O ganho vem da regra ou só de acompanhar o mercado?"
    nome = "Alfa e beta"
    ab = sorte.get("alfa_beta")
    if not ab or ab.get("alfa_anual") is None:
        return _teste("alfa", "sorte", nome, pergunta, NAO_SE_APLICA, "Sem Ibovespa, ou a regra não operou no teste.")
    beta = _num(ab["beta"])
    texto = (f"O beta foi {beta}: quando o Ibovespa sobe 1%, a regra tende a variar {beta}%. Beta 1 acompanharia o índice na mesma proporção, e beta 0 não o acompanharia. "
             f"O alfa, o que sobra além de acompanhar o mercado, foi de {_pp(ab['alfa_anual'])} ao ano, em que zero significa nada além do mercado "
             f"(p-valor {_p(ab['p_alfa'])}, com limite de 0,05). ")
    if ab["alfa_significativo"]:
        return _teste("alfa", "sorte", nome, pergunta, PASSOU, texto + "Há evidência de ganho além do mercado.")
    if ab["p_alfa"] is not None and ab["p_alfa"] < 0.05:
        return _teste("alfa", "sorte", nome, pergunta, NAO_PASSOU,
                      texto + "Há evidência de que a regra rendeu menos do que o risco de mercado dela explicaria.")
    return _teste("alfa", "sorte", nome, pergunta, NAO_PASSOU,
                  texto + "Não há evidência suficiente de ganho além do que o mercado explica.")


def _desconto(sorte, r_selecao=None) -> dict:
    pergunta = "O que sobra do resultado depois de descontar as tentativas?"
    nome = "Sharpe com desconto por tentativas"
    d = sorte.get("sharpe_desconto") or {}
    if d.get("p_ajustado") is None:
        return _teste("desconto", "sorte", nome, pergunta, NAO_SE_APLICA, "Não há dados suficientes para este teste.")
    n = d["n_tentativas"]
    if (d.get("sharpe") or 0) <= 0:
        return _teste("desconto", "sorte", nome, pergunta, NAO_PASSOU,
                      f"O Sharpe do teste foi {_num(d['sharpe'])}. Abaixo de zero, a regra rendeu menos que a Selic. "
                      "Sem ganho acima da Selic, não há o que descontar.")
    s = r_selecao.get("n_candidatas") if r_selecao else None
    origem = (f"A seleção escolheu entre {s} ações, e esta página oferece 16 combinações: {n} tentativas ao todo. "
              "Como as ações se movem juntas, essa conta é conservadora. " if s else f"Esta página oferece {n} combinações. ")
    texto = (f"{origem}Levando isso em conta, o Sharpe do teste cai de {_num(d['sharpe'])} "
             f"para {_num(d['sharpe_ajustado'])}, e a chance de ao menos uma tentativa chegar a esse resultado só por acaso sobe para "
             f"{_pct(d['p_ajustado'])}. Para haver evidência, esta ferramenta pede uma chance abaixo de 5%. ")
    if d["significativo"]:
        return _teste("desconto", "sorte", nome, pergunta, PASSOU, texto + "Mesmo com o desconto, o resultado se sustenta.")
    return _teste("desconto", "sorte", nome, pergunta, NAO_PASSOU,
                  texto + "Com o desconto, não há evidência suficiente de que o resultado vá além do acaso.")


# ------------------------------------------------------------------------------- 2. aguenta variações?
def _treino_teste(r) -> dict:
    pergunta = "Foi bem na prova ou só no estudo?"
    nome = "Treino × teste"
    tr, te = r["desempenho"]["treino"]["estrategia"]["sharpe"], r["desempenho"]["teste"]["estrategia"]["sharpe"]
    if tr is None or te is None:
        return _teste("treino_teste", "variacoes", nome, pergunta, NAO_SE_APLICA, "A regra não operou o bastante para comparar.")
    passou = te > 0 and te >= 0.5 * tr
    fim = ("O desempenho se manteve nos dados que as escolhas não viram."
           if passou else "O desempenho piorou nos dados que as escolhas não viram: o resultado do treino não se repetiu.")
    pedido = "positivo no teste" + (f" e de pelo menos {_num(0.5 * tr)}, a metade do treino inicial" if tr > 0 else "")
    return _teste("treino_teste", "variacoes", nome, pergunta, PASSOU if passou else NAO_PASSOU,
                  f"O Sharpe foi {_num(tr)} no treino inicial e {_num(te)} nas janelas de teste, em sequência. "
                  f"Esta ferramenta pede um Sharpe {pedido}. {fim}")


def _ano_a_ano(r) -> dict:
    pergunta = "Ganhou de forma constante ou só em uma fase do mercado?"
    nome = "Ano a ano"
    a = r["variacoes"]["ano_a_ano"]
    if not a["n_avaliados"]:
        return _teste("ano_a_ano", "variacoes", nome, pergunta, NAO_SE_APLICA, "Sem Selic ou sem anos com dados suficientes para comparar.")
    passou = a["n_acima"] > a["n_avaliados"] / 2
    return _teste("ano_a_ano", "variacoes", nome, pergunta, PASSOU if passou else NAO_PASSOU,
                  f"A regra ganhou da Selic em {a['n_acima']} de {a['n_avaliados']} anos. Só contam os anos com ao menos meio ano de pregões. Esta ferramenta pede mais da metade. "
                  + ("O ganho apareceu na maior parte do tempo." if passou else "O ganho, quando houve, ficou concentrado em poucos anos."))


def _sensibilidade(r) -> dict:
    pergunta = "O resultado depende de um ajuste exato?"
    nome = "Sensibilidade às escolhas"
    v = r["variacoes"]
    if v["n_bateram_selic"] is None:
        return _teste("sensibilidade", "variacoes", nome, pergunta, NAO_SE_APLICA, "Sem Selic para comparar.")
    n, total = v["n_bateram_selic"], v["n_combinacoes"]
    passou = n > total / 2
    return _teste("sensibilidade", "variacoes", nome, pergunta, PASSOU if passou else NAO_PASSOU,
                  f"{n} de {total} combinações de ritmo e saída automática ganharam da Selic no teste. Esta ferramenta pede mais da metade. "
                  + ("O resultado não depende de um único ajuste." if passou else
                     "Nenhuma delas funcionou no teste." if n == 0 else
                     "A maioria não ganhou. Um bom resultado isolado aqui pode ser fruto do ajuste escolhido."))


def _custo(r) -> dict:
    pergunta = "O ganho sobrevive ao custo?"
    nome = "Sensibilidade ao custo"
    linhas = {ln["custo"]: ln for ln in r["variacoes"]["custos"]}
    caro, barato = linhas["tarifas_b3"], linhas["sem_custo"]
    if caro["bateu_selic"] is None:
        return _teste("custo", "variacoes", nome, pergunta, NAO_SE_APLICA, "Sem Selic para comparar.")
    texto = (f"No teste, pagando as tarifas da B3 e o imposto de renda, a regra rendeu {_pct(caro['retorno_teste'])}, contra "
             f"{_pct(caro['retorno_selic_teste'])} da Selic depois do imposto. Sem tarifas e sem imposto, rendeu {_pct(barato['retorno_teste'])}, "
             f"contra {_pct(barato['retorno_selic_teste'])} da Selic. Foram {caro['n_trades']} operações no período inteiro. ")
    if caro["bateu_selic"]:
        return _teste("custo", "variacoes", nome, pergunta, PASSOU, texto + "Mesmo pagando as tarifas e o imposto, ganhou da Selic.")
    if barato["bateu_selic"]:
        return _teste("custo", "variacoes", nome, pergunta, NAO_PASSOU, texto + "Só ganha da Selic quando não há tarifas nem imposto.")
    return _teste("custo", "variacoes", nome, pergunta, NAO_PASSOU, texto + "Não ganhou da Selic em nenhum dos dois casos.")


# ------------------------------------------------------------------------------- 3. e se a sequência fosse outra?
def _monte_carlo(r) -> dict:
    pergunta = "Quanto o tombo poderia ter sido pior, com as mesmas operações em outra ordem?"
    nome = "Embaralhar a ordem das operações"
    mc = r["sequencia"]["monte_carlo"]
    if not mc:
        return _teste("monte_carlo", "sequencia", nome, pergunta, NAO_SE_APLICA,
                      "Com menos de 5 operações no teste, não há o que embaralhar.")
    ref = r["desempenho"]["teste"]["buy_hold"]["max_drawdown"]
    passou = mc["queda_pessimista"] >= ref
    return _teste("monte_carlo", "sequencia", nome, pergunta, PASSOU if passou else NAO_PASSOU,
                  f"Em {_inteiro(mc['n_simulacoes'])} ordens simuladas, o resultado final é sempre o mesmo. A queda típica ficou em "
                  f"{_queda(mc['queda_mediana'])} e, no cenário pessimista (só 5% das ordens foram piores), em "
                  f"{_queda(mc['queda_pessimista'])}." + (f" Na ordem real, a queda foi de {_queda(mc['queda_observada'])}." if mc.get("queda_observada") is not None else "")
                  + f" Comprar e segurar caiu {_queda(ref)} de fato no teste, "
                  "e esta ferramenta pede que o cenário pessimista não passe disso.")


def _sem_melhores(r) -> dict:
    pergunta = "O resultado depende de poucas operações excepcionais?"
    nome = "Sem as 3 melhores operações"
    s = r["sequencia"]["sem_melhores"]
    if not s:
        return _teste("sem_melhores", "sequencia", nome, pergunta, NAO_SE_APLICA, "Há poucas operações no teste para fazer essa conta.")
    if s["ainda_positivo"]:
        fim = "O ganho não depende só delas."
    elif s["resultado_total"] > 0:
        fim = "Sem elas, a regra perderia dinheiro: o ganho depende de poucas operações."
    else:
        fim = "A regra já perdeu dinheiro nessas operações, mesmo contando as melhores."
    return _teste("sem_melhores", "sequencia", nome, pergunta, PASSOU if s["ainda_positivo"] else NAO_PASSOU,
                  f"O resultado das operações do teste foi de {_brl(s['resultado_total'])}. Sem as 3 melhores, seria de "
                  f"{_brl(s['resultado_sem'])}. {fim}")


# ------------------------------------------------------------------------------- veredito
def _frase(r, testes: dict) -> str:
    te = r["desempenho"]["teste"]
    est, selic, bh = te["estrategia"], te.get("selic"), te["buy_hold"]
    partes = []
    if selic:
        comparacao = (f"a regra rendeu {_pct(est['retorno_total'])}, contra {_pct(selic['retorno_total'])} da Selic e "
                      f"{_pct(bh['retorno_total'])} de comprar e segurar")
        if testes["intervalo"]["status"] == PASSOU:
            conclusao = "Há evidência estatística de que ela superou a Selic nesse período."
        elif est["retorno_total"] > selic["retorno_total"]:
            conclusao = "Ela rendeu mais que a Selic, mas não há evidência suficiente de que isso vá além do acaso."
        else:
            conclusao = "Nesses dados, ela não superou a Selic."
        partes = [f"Nas janelas de teste, a segunda metade do histórico, em que cada escolha foi conferida com dados que não a influenciaram, {comparacao}.", conclusao]
    else:
        partes = [f"Nas janelas de teste, a regra rendeu {_pct(est['retorno_total'])} e comprar e segurar, "
                  f"{_pct(bh['retorno_total'])}. Sem a Selic, os principais testes ficam de fora."]
    return " ".join(partes)


def _perguntas(r: dict, n_passou: int, n_aplicaveis: int) -> tuple[list[dict], str, str]:
    """Três perguntas diferentes, para não confundir ganhar dinheiro com passar nos testes."""
    cap, per = r["escolhas"]["capital"], r["periodo"]
    est_i = r["desempenho"]["inteiro"]["estrategia"]
    te = r["desempenho"]["teste"]
    est, selic, bh = te["estrategia"], te.get("selic"), te["buy_hold"]
    dinheiro = {"pergunta": "A regra ganhou dinheiro?", "resposta": "Sim" if est_i["retorno_total"] > 0 else "Não",
                "texto": f"No histórico inteiro, de {_data(per['inicio'])} a {_data(per['fim'])}, {_brl(cap)} viraram "
                         f"{_brl(est_i['valor_final'])}, depois de pagar as tarifas e o imposto. Nas janelas de teste, a regra rendeu {_pct(est['retorno_total'])}."}
    refs = ([("da Selic", selic["retorno_total"])] if selic else []) + [("de comprar e segurar", bh["retorno_total"])]
    venceu = [nome for nome, v in refs if est["retorno_total"] > v]
    contra = " e ".join(f"{_pct(v)} {nome}" for nome, v in refs)
    alternativas = {"pergunta": "Ganhou mais que as alternativas nas janelas de teste?",
                    "resposta": "Sim" if len(venceu) == len(refs) else ("Em parte" if venceu else "Não"),
                    "texto": f"Nas janelas de teste, a regra rendeu {_pct(est['retorno_total'])}, contra {contra}."}
    confianca = {"pergunta": "O resultado resiste aos testes?", "resposta": f"{n_passou} de {n_aplicaveis}",
                 "texto": "Os testes do passo 4 pedem evidência de que o resultado não foi sorte, desempenho parecido no treino e no teste "
                          "e resistência a outras escolhas, a outro custo e a outra ordem das operações."}
    por_que = ("Os testes respondem só à terceira pergunta, por isso podem dar “não passou” mesmo quando a regra ganhou dinheiro. "
               "Ganhar dinheiro não basta: a Selic também ganha, sem o risco da bolsa, e comprar e segurar pede menos trabalho. "
               "E o histórico inteiro inclui o treino, em que as escolhas foram feitas olhando os próprios dados. "
               "Só as janelas de teste mostram o resultado com dados que as escolhas não viram.")
    linha = (f"nas janelas de teste, a regra rendeu {_pct(est['retorno_total'])}"
             + (f", contra {_pct(selic['retorno_total'])} da Selic" if selic else "")
             + f"; passou em {n_passou} de {n_aplicaveis} testes aplicáveis.")
    return [dinheiro, alternativas, confianca], por_que, linha


def decisoes_treino(r: dict) -> dict:
    """O que foi decidido com os dados de treino nesta análise e o que foi definido pela pessoa."""
    esc, sel, tickers = r["escolhas"], r.get("selecao"), r["config"]["tickers"]
    if sel:
        acoes = ("Treino", f"{len(tickers)} de {sel['n_candidatas']} candidatas na 1ª janela: {', '.join(tickers)}")
    else:
        acoes = ("Você", ", ".join(tickers))
    if esc["medias_pelo_treino"]:
        nota = next((ln["sharpe_treino"] for ln in esc["comparacao_ritmos"] if ln["curta"] == esc["curta"]), None)
        ritmo = ("Treino", esc["medias"] + (f", com Sharpe de {nota:.2f} no treino".replace(".", ",") if nota is not None else ""))
    else:
        ritmo = ("Você", esc["medias"])
    if len(tickers) < 2:
        divisao = ("Não se aplica", "Só há uma ação.")
    elif r["config"]["divisao"] == "igual":
        divisao = ("Você", "Partes iguais, sem cálculo")
    else:
        pesos = ", ".join(f"{t} {_pct(p)}" for t, p in r["pesos"].items())
        divisao = ("Treino", f"{esc['divisao']}, na 1ª janela: {pesos}")
    itens = [{"escolha": nome, "quem": quem, "resultado": resultado}
             for nome, (quem, resultado) in (("Quais ações", acoes), ("Qual ritmo", ritmo), ("Como dividir o dinheiro", divisao))]
    decidiu = any(x["quem"] == "Treino" for x in itens)
    frase = ("Nesta análise, o treino fez as escolhas marcadas abaixo. Elas foram feitas com o treino inicial e refeitas antes de cada janela "
             "de teste, sempre só com os dados anteriores a ela. A tabela das janelas mostra o que foi escolhido em cada uma." if decidiu else
             "Nesta análise, o treino não escolheu nada: as decisões foram suas e valem em todas as janelas. Ele serve de comparação com o teste.")
    return {"itens": itens, "treino_decidiu": decidiu, "frase": frase}


def regra_passos(r: dict) -> list[dict]:
    """A regra de compra e venda, com os parâmetros desta análise."""
    e = r["escolhas"]
    curta, longa, stop, alvo, custo = e["curta"], e["longa"], e["stop"], e["alvo"], e["custo_pct"]
    venda = "A venda acontece na abertura do pregão seguinte ao dia em que a média curta passa para baixo da longa."
    if stop is not None:
        venda = (f"A venda acontece no primeiro destes casos: o preço cai {stop:.0f}% abaixo do preço de compra (limite de perda), sobe {alvo:.0f}% acima dele (limite de ganho) "
                 "ou a média curta passa para baixo da longa, com a venda na abertura seguinte. Os limites valem desde o dia da compra. "
                 "Se o preço abrir além de um limite, a venda sai no preço de abertura. Se os dois limites puderem ter sido atingidos no mesmo pregão, vale o de perda.")
    passos = [
        ("Calcular as médias", f"Ao fim de cada pregão, a ferramenta calcula a média dos últimos {curta} fechamentos (média curta) e a dos últimos {longa} (média longa). "
                               f"Antes de haver {longa} fechamentos, a regra não opera."),
        ("Comprar", "Se a média curta fica acima da longa, depois de estar igual ou abaixo dela no pregão anterior, a compra acontece na abertura do pregão seguinte. "
                    f"A regra usa todo o dinheiro disponível para a ação, em lotes de {LOTE} ações. O que não completa um lote fica parado."),
        ("Vender", venda),
        ("Pagar o custo", f"Cada compra e cada venda pagam {_num(custo, 2)}% do valor negociado, as tarifas que a B3 cobra nas operações com ações. "
                          "Comprar e segurar, a comparação, também paga, na compra e na venda."
                          if custo else "Nesta análise, as operações não pagam custo."),
        ("Pagar o imposto", "No fim de cada mês, o lucro das vendas paga imposto de renda: 15% nas operações comuns, com isenção quando as vendas "
                            "do mês somam até R$ 20 mil, e 20% no day trade, quando a compra e a venda acontecem no mesmo pregão. Perdas abatem "
                            "lucros dos meses seguintes. O imposto sai do patrimônio no último pregão do mês seguinte."
                            if e.get("imposto") else "Nesta análise, o lucro não paga imposto de renda."),
        ("Esperar", "Depois da venda, o dinheiro fica parado, rendendo zero nesta simulação. A regra só volta a comprar na próxima vez que a média curta passar para cima da longa."),
        ("Encerrar", "Uma compra ainda aberta no último pregão do histórico é vendida no fechamento desse pregão. O mesmo acontece no último pregão "
                     "de uma janela quando as escolhas da janela seguinte mudam: as posições são vendidas, pagando o custo, e o dinheiro é dividido pelas novas escolhas."),
    ]
    if len(r["tickers"]) > 1:
        passos.append(("Com várias ações", "Cada ação opera sozinha, com a sua parte do dinheiro, sem rebalancear dentro da janela. O patrimônio é a soma de todas elas."))
    return [{"titulo": t, "texto": x} for t, x in passos]


def _passo_pesos(r: dict) -> tuple[str, str] | None:
    """Como o dinheiro é dividido, se houver mais de uma ação."""
    tickers, divisao = r["config"]["tickers"], r["config"]["divisao"]
    if len(tickers) < 2:
        return None
    if divisao == "igual":
        return "Dividir o dinheiro", f"Você escolheu partes iguais: cada uma das {len(tickers)} ações recebe a mesma parte, sem cálculo."
    objetivo = ("a oscilação e a correlação de cada ação, e um otimizador procura os pesos que dão à carteira a menor oscilação" if divisao == "min_variancia" else
                "o retorno médio, a oscilação e a correlação de cada ação, e um otimizador procura os pesos que dão à carteira o maior índice de Sharpe, usando a Selic média do treino")
    pesos = ", ".join(f"{t} {_pct(p)}" for t, p in r["pesos"].items())
    limite = _pct(LIMITE_PESO, 0)
    return ("Calcular os pesos", f"Com os retornos diários do treino, a ferramenta calcula {objetivo}. Cada peso fica entre 0% e {limite}, e a soma dá 100%. "
            f"O limite de {limite} evita apostar quase tudo na ação que mais subiu no passado; com menos de 3 ações ele seria impossível e não vale. "
            f"Essa conta considera comprar e manter as ações, sem a regra de médias. Uma ação com peso abaixo de 0,5% fica sem dinheiro. Resultado na 1ª janela: {pesos}.")


def _par(a: float, b: float) -> tuple[str, str]:
    """Dois preços com 2 casas, ou 3 quando 2 casas os deixariam iguais na tela."""
    casas = 2 if round(a, 2) != round(b, 2) else 3
    return _num(a, casas), _num(b, casas)


def _nota_ajuste(x: dict) -> str:
    """Explica por que o preço do exemplo é menor que o da época: os preços são ajustados pelo que veio depois."""
    bolsa = x.get("preco_entrada_bolsa")
    if bolsa and abs(bolsa / x["preco_entrada"] - 1) >= 0.01:
        return (f" Esses são preços ajustados: na bolsa, a {x['ticker']} abriu a R$ {_num(bolsa)} nesse dia. O ajuste desconta os dividendos "
                "e os desdobramentos que vieram depois, então os preços antigos ficam menores, e as quantidades, maiores que as da época. "
                "O ganho ou a perda em % é o mesmo.")
    if bolsa:
        return ""                       # sem dividendos nem desdobramentos depois: o ajustado é o próprio preço da época
    return (" Esses são preços ajustados: eles descontam os dividendos e os desdobramentos que vieram depois, então podem ficar menores "
            "que os da época. O ganho ou a perda em % é o mesmo.")


def _exemplo_operacao(r: dict) -> str | None:
    x, e = r.get("primeira_operacao_treino"), r["escolhas"]
    if not x:
        return None
    valor = x["quantidade"] * x["preco_entrada"]
    limites = ""
    if e["stop"] is not None:
        limites = (f" Os limites ficaram em R$ {_num(x['preco_entrada'] * (1 - e['stop'] / 100))} para a perda "
                   f"e em R$ {_num(x['preco_entrada'] * (1 + e['alvo'] / 100))} para o ganho.")
    saida = {"sinal": "A venda veio pelo cruzamento contrário", "stop": "A venda veio no limite de perda", "alvo": "A venda veio no limite de ganho",
             "fim_janela": "A operação foi encerrada no fim da janela, porque as escolhas mudaram", "fim_dados": "A operação foi encerrada no fim do histórico"}[x["motivo"]]
    sinal, antes = _par(x["curta_sinal"], x["longa_sinal"]), _par(x["curta_anterior"], x["longa_anterior"])
    return (f"A primeira operação do treino foi em {x['ticker']}. No fechamento de {_data(x['data_sinal'])}, a média de {e['curta']} dias estava em R$ {sinal[0]} "
            f"e a de {e['longa']} dias, em R$ {sinal[1]}. No pregão anterior, estavam em R$ {antes[0]} e R$ {antes[1]}. "
            f"Na abertura de {_data(x['data_entrada'])}, a regra comprou {_inteiro(x['quantidade'])} ações a R$ {_num(x['preco_entrada'])}, no total de {_brl(valor)}."
            + _nota_ajuste(x) + limites + f" {saida}, em {_data(x['data_saida'])}, a R$ {_num(x['preco_saida'])}, com {x['pregoes']} pregões contando o da compra e o da venda. "
            f"O resultado foi de {_brl(x['resultado'])}, ou {_sinal(x['retorno_pct'] / 100)}% sobre o valor comprado, já com as tarifas e antes do imposto.")


def roteiro_treino(r: dict) -> dict:
    """Como o treino é feito nesta análise, passo a passo, e a regra simulada nele."""
    per, e, sel = r["periodo"], r["escolhas"], r.get("selecao")
    n_jan = per["n_janelas"]
    passos = [("Separar o treino inicial", f"Os {_inteiro(per['n_treino'])} primeiros dos {_inteiro(per['n_pregoes'])} pregões, de {_data(per['inicio'])} a {_data(per['fim_treino'])}, "
               f"formam o treino inicial. Os {_inteiro(per['n_teste'])} pregões seguintes viram {n_jan} janelas de teste, de cerca de {_num(per['anos_teste'] / n_jan, 1)} ano cada. "
               f"As escolhas da 1ª janela usam só o treino inicial: nada depois de {_data(per['fim_treino'])} entra nelas.")]
    pesos = _passo_pesos(r)
    n_ritmos = len(MEDIAS)
    if sel:
        passos += [
            ("Filtrar as ações", f"Das {sel['n_universo']} ações do Ibovespa, ficam {sel['n_candidatas']}: as que têm dados completos e sem sinais de erro desde o início do histórico."),
            ("Simular cada ação", f"A regra roda em cada candidata, só nos pregões do treino, com {_brl(e['capital'] / MAX_ACOES)} (o capital dividido por {MAX_ACOES}), com a saída escolhida e pagando as tarifas e o imposto. "
                                  "Uma compra aberta no último pregão do treino é vendida no fechamento dele."),
            ("Dar uma nota", "A nota é o índice de Sharpe no treino: quanto a ação rendeu acima da Selic para cada ponto de oscilação. Só nesta nota, o dinheiro parado rende a Selic, "
                             "para não punir os ritmos que ficam menos tempo comprados."),
            ("Aplicar os critérios", f"Entram as até {MAX_ACOES} maiores notas acima de zero, com ao menos 5 operações no treino. Em caso de empate, vale a ordem alfabética. "
                                     f"Esses limites são critérios desta ferramenta. Resultado na 1ª janela: {len(r['config']['tickers'])} ações."),
        ]
        if e["medias_pelo_treino"]:
            passos.append(("Escolher o ritmo", f"Esses passos se repetem nos {n_ritmos} ritmos. Vence o de maior nota média entre as ações aprovadas. Na 1ª janela: {e['medias']}."))
        if pesos:
            passos.append(pesos)
    else:
        if pesos:
            passos.append(pesos)
        if e["medias_pelo_treino"]:
            nota = next((ln["sharpe_treino"] for ln in e["comparacao_ritmos"] if ln["curta"] == e["curta"]), None)
            passos.append(("Comparar os ritmos", f"Os {n_ritmos} ritmos são simulados com a saída escolhida e com as tarifas e o imposto, e cada um recebe o índice de Sharpe do trecho de treino: "
                           f"quanto rendeu acima da Selic para cada ponto de oscilação. Vence o maior. Na 1ª janela: {e['medias']}, com {_num(nota)}."))
        if not pesos and not e["medias_pelo_treino"]:
            passos.append(("Nada a escolher", "Com estas escolhas, não há o que decidir: a ação, o ritmo, a saída e o custo foram definidos por você e valem em todas as janelas. "
                                              "O treino serve de comparação."))
    if any(x[0] in ("Calcular os pesos", "Comparar os ritmos", "Filtrar as ações") for x in passos):
        passos.append(("Andar uma janela", "Ao fim de cada janela, os pregões dela passam a fazer parte do treino, e os passos acima se repetem para a janela seguinte. "
                                           "A escolha da 3ª janela, por exemplo, usa tudo até o fim da 2ª, e nada depois."))
    passos.append(("Simular e medir", "A regra roda janela a janela, com as escolhas de cada uma. Enquanto as escolhas não mudam, a carteira segue sem parar. "
                                      "Quando mudam, as posições abertas são vendidas no fechamento do último pregão da janela, pagando o custo, e o dinheiro é dividido "
                                      f"pelas novas escolhas. O resultado do treino é o do treino inicial, até {_data(per['fim_treino'])}. O do teste é a sequência das {n_jan} janelas."))
    return {
        "passos": [{"titulo": t, "texto": x} for t, x in passos],
        "regra": regra_passos(r),
        "nao_decide": ("O treino não muda a regra. A forma de calcular as médias, a regra de compra e venda, a saída automática e o custo continuam iguais em todo o histórico. "
                       "A saída e o custo são sempre definidos por você."),
        "exemplo": _exemplo_operacao(r),
    }


def frase_sharpe(r: dict) -> str:
    """O Sharpe da regra no teste, comparado às alternativas do mesmo período."""
    te = r["desempenho"]["teste"]
    s = te["estrategia"]["sharpe"]
    if s is None:
        return "A regra não variou o bastante no teste para calcular o Sharpe."
    sinal = "rendeu em média mais que a Selic" if s > 0 else "rendeu em média menos que a Selic" if s < 0 else "rendeu em média o mesmo que a Selic"
    partes = [f"No teste, o Sharpe da regra foi {_num(s)}: ela {sinal}."]
    outros = [(n, te[k]["sharpe"]) for k, n in (("buy_hold", "comprar e segurar"), ("ibovespa", "o Ibovespa")) if k in te and te[k]["sharpe"] is not None]
    if outros:
        lista = ", e ".join(f"{n} teve {_num(v)}" for n, v in outros)
        acima = sum(s > v for _, v in outros)
        juizo = (("a regra ficou acima dos dois" if len(outros) > 1 else "a regra ficou acima") if acima == len(outros) else
                 "a regra ficou abaixo" + (" dos dois" if len(outros) > 1 else "") if acima == 0 else "a regra ficou acima de um e abaixo do outro")
        partes.append(f"No mesmo período, {lista}. Por essa medida, {juizo}.")
    return " ".join(partes)


def montar(r: dict) -> dict:
    """Recebe o resultado já em JSON puro e devolve veredito e testes para a página."""
    sorte = r["foi_sorte"]
    lista = [
        _ic(sorte), _alfa(sorte), _desconto(sorte, r.get("selecao")),
        _treino_teste(r), _ano_a_ano(r), _sensibilidade(r), _custo(r),
        _monte_carlo(r), _sem_melhores(r),
    ]
    por_id = {t["id"]: t for t in lista}
    blocos = []
    for chave, titulo in BLOCOS.items():
        itens = [t for t in lista if t["bloco"] == chave]
        aplicaveis = [t for t in itens if t["status"] != NAO_SE_APLICA]
        blocos.append({"id": chave, "titulo": titulo, "testes": itens, "n_passou": sum(t["status"] == PASSOU for t in itens),
                       "n_aplicaveis": len(aplicaveis)})
    aplicaveis = [t for t in lista if t["status"] != NAO_SE_APLICA]
    n_passou = sum(t["status"] == PASSOU for t in lista)
    perguntas, por_que, linha = _perguntas(r, n_passou, len(aplicaveis))
    return {
        "frase": _frase(r, por_id),
        "perguntas": perguntas,
        "por_que_nao_passou": por_que,
        "linha": linha,
        "blocos": blocos,
        "testes": por_id,
        "n_passou": n_passou,
        "n_aplicaveis": len(aplicaveis),
        "nota_contagem": ("Essa contagem resume os testes. Ela não é a probabilidade de ganhar dinheiro nem uma "
                          "recomendação de investimento."),
        "criterios_tecnicos": CRITERIOS_TECNICOS,
    }
