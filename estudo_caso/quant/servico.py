"""Fachada do núcleo: `executar(config) -> dict` 100% JSON-serializável.

É o único ponto de entrada que o Portal FinQuant precisa chamar:

    resultado = servico.executar(form.cleaned_data_como_dict)
    contexto["resultado"] = resultado

Sequência única: dados -> treino inicial e janelas de teste -> antes de cada janela, escolhas só com o passado ->
simulação janela a janela -> recortes -> testes estatísticos -> leitura em linguagem comum.
"Treino" é o treino inicial (a primeira metade do histórico); "teste" é a sequência das janelas, a segunda metade.
Nada aqui importa Django, plotly ou streamlit.
"""
import hashlib
import json
from datetime import date

import numpy as np
import pandas as pd

from . import benchmarks as bm
from . import carteira as cart
from . import estatistica as est
from . import imposto as imp
from . import janelas as jan
from . import leitura, metricas as m, robustez as rob, selecao as sel, universo
from . import config as c
from .config import ConfigAnalise
from .dados import CsvFonte, DadosIndisponiveis, alinhar_fechamentos, carregar_ativos, criar_fonte, problemas_de_dados
from .estrategias import medias as calcular_medias
from .glossario import AVISO, GLOSSARIO
from .referencias import REFERENCIAS
from .util import fmt_data, json_seguro, para_pontos

VERSAO = "4.7"
JANELA_EXEMPLO = 90                 # pregões mostrados antes e depois do cruzamento de exemplo


def chave_cache(config: dict) -> str:
    """Hash estável da configuração (para cache de resultados no portal)."""
    cfg = ConfigAnalise.from_dict(config).to_dict()
    return hashlib.sha256(json.dumps(cfg, sort_keys=True, default=str).encode()).hexdigest()[:24]


def _pior_momento(curva: pd.Series) -> dict:
    """O pico e o fundo da maior queda: 'no pior momento, R$ X viraram R$ Y'."""
    dd = m.drawdown(curva)
    fundo = dd.idxmin()
    pico = curva.loc[:fundo].idxmax()
    depois = curva.loc[fundo:]
    voltou = depois[depois >= curva.loc[pico]]
    return {"data_pico": pico, "valor_pico": float(curva.loc[pico]), "data_fundo": fundo,
            "valor_fundo": float(curva.loc[fundo]), "queda": float(dd.min()),
            "data_recuperacao": voltou.index[0] if len(voltou) else None,
            "pregoes_recuperacao": int(depois.index.get_loc(voltou.index[0])) if len(voltou) else None}


def _resumo_operacoes(trades: pd.DataFrame, custo_pct: float, exposicao: pd.Series, curva: pd.Series, apuracao: pd.DataFrame) -> dict:
    """As métricas de um período, com os custos e o imposto pagos, o tempo comprado e a maior queda do patrimônio no período."""
    custos = (trades["quantidade"] * (trades["preco_entrada"] + trades["preco_saida"])).sum() * custo_pct / 100.0 if len(trades) else 0.0
    return {**m.metricas_trading(trades), "custos_pagos": float(custos),
            "imposto_pago": imp.pago_entre(apuracao, exposicao.index[0], exposicao.index[-1]),
            "tempo_comprado": float(exposicao.mean()), "queda_maxima": m.max_drawdown(curva)}


def _detalhar_operacoes(trades: pd.DataFrame, custo_pct: float, imposto: np.ndarray) -> pd.DataFrame:
    """Acrescenta a cada operação a variação do preço (em % e em R$), as tarifas, a parte do imposto e o resultado final."""
    t = trades.copy()
    if not len(t):
        return t.assign(variacao_pct=[], variacao_rs=[], custo=[], imposto=[], resultado_final=[])
    t["variacao_pct"] = 100.0 * (t["preco_saida"] / t["preco_entrada"] - 1.0)
    t["variacao_rs"] = t["quantidade"] * (t["preco_saida"] - t["preco_entrada"])
    t["custo"] = t["quantidade"] * (t["preco_entrada"] + t["preco_saida"]) * custo_pct / 100.0
    t["imposto"] = imposto
    t["resultado_final"] = t["pnl"] - t["imposto"]
    return t


def _valores(t: pd.DataFrame) -> pd.DataFrame:
    """O valor de cada compra e de cada venda (quantidade × preço). O saldo em conta vem da simulação."""
    return t.assign(valor_compra=t["quantidade"] * t["preco_entrada"], valor_venda=t["quantidade"] * t["preco_saida"])


def _precos_da_bolsa(t: pd.DataFrame, fonte: CsvFonte) -> pd.DataFrame:
    """O preço de compra e de venda como estava na bolsa no dia, para mostrar ao lado do ajustado.

    A simulação usa preços ajustados por dividendos e desdobramentos: os antigos ficam menores que os da época. Sem o fator
    no cache, as colunas ficam vazias e a página explica sem o valor."""
    t = t.assign(preco_entrada_bolsa=np.nan, preco_saida_bolsa=np.nan)
    if not len(t) or not hasattr(fonte, "fator_bolsa"):
        return t
    for ticker in t["ticker"].unique():
        fator = fonte.fator_bolsa(ticker)
        if fator is None:
            continue
        linhas = t["ticker"] == ticker
        for lado in ("entrada", "saida"):
            datas = pd.to_datetime(t.loc[linhas, f"data_{lado}"])
            t.loc[linhas, f"preco_{lado}_bolsa"] = t.loc[linhas, f"preco_{lado}"].to_numpy() * fator.reindex(datas).to_numpy()
    return t


def _liquida(curva: pd.Series, vendas, com_imposto: bool) -> tuple[pd.Series, pd.DataFrame]:
    """A curva depois do imposto de renda, ou a própria curva quando a análise não cobra imposto."""
    vendas = vendas if isinstance(vendas, pd.DataFrame) else pd.DataFrame(vendas)
    return imp.aplicar(curva, vendas if com_imposto else vendas.iloc[:0])


def _apuracao_json(apuracao: pd.DataFrame) -> dict:
    """A apuração mês a mês e os totais, só com os meses que tiveram venda."""
    meses = apuracao.astype(object).where(apuracao.notna(), None).to_dict("records")     # mês sem imposto não tem pagamento
    return {"meses": meses,"total": float(apuracao["imposto"].sum()) if len(apuracao) else 0.0,
            "meses_isentos": int(apuracao["isento"].sum()) if len(apuracao) else 0,
            "meses_pagos": int((apuracao["imposto"] > 0).sum()) if len(apuracao) else 0}


def _exemplo_cruzamento(dfs: dict, pesos: dict, trades: pd.DataFrame, curta: int, longa: int) -> dict | None:
    """Um cruzamento real, da ação de maior peso, para ilustrar a regra na página. `trades` são as do primeiro trecho."""
    ticker = max(pesos, key=lambda t: pesos[t])
    proprios = trades[(trades["ticker"] == ticker)] if len(trades) else trades
    if not len(proprios):
        return None
    t = proprios.iloc[len(proprios) // 2]
    df = dfs[ticker]
    i_ent = df.index.get_loc(t["data_entrada"])
    ini, fim = max(0, i_ent - JANELA_EXEMPLO), min(len(df), i_ent + JANELA_EXEMPLO + 1)
    mc, ml = calcular_medias(df, curta, longa)
    janela = df.index[ini:fim]
    lista = lambda s: [None if v != v else round(float(v), 4) for v in s.iloc[ini:fim]]  # noqa: E731
    return {
        "ticker": ticker, "curta": curta, "longa": longa, "datas": [fmt_data(d) for d in janela],
        "preco": lista(df["Close"]), "media_curta": lista(mc), "media_longa": lista(ml),
        "data_sinal": df.index[max(i_ent - 1, 0)], "data_entrada": t["data_entrada"],
        "preco_entrada": float(t["preco_entrada"]), "data_saida": t["data_saida"],
        "preco_saida": float(t["preco_saida"]), "motivo_saida": t["motivo"],
        "retorno_pct": float(t["retorno_pct"]), "saida_na_janela": bool(t["data_saida"] <= janela[-1]),
    }


def _primeira_operacao(dfs: dict, trades: pd.DataFrame, curta: int, longa: int) -> dict | None:
    """A primeira operação do treino, com as médias do dia do sinal e do dia anterior, para ilustrar a regra com números reais."""
    if not len(trades):
        return None
    t = trades.iloc[0]
    df = dfs[t["ticker"]]
    i = df.index.get_loc(t["data_entrada"])
    mc, ml = calcular_medias(df, curta, longa)
    # Trecho do gráfico: um pouco antes do sinal, para ver as médias se cruzarem, até um pouco depois da venda.
    i_saida = df.index.get_loc(t["data_saida"])
    ini, fim = max(0, i - JANELA_EXEMPLO // 2), min(len(df), i_saida + JANELA_EXEMPLO // 3 + 1)
    lista = lambda s: [None if v != v else round(float(v), 4) for v in s.iloc[ini:fim]]  # noqa: E731
    grafico = {"datas": [fmt_data(d) for d in df.index[ini:fim]], "preco": lista(df["Close"]), "media_curta": lista(mc), "media_longa": lista(ml)}
    return {"ticker": t["ticker"], "grafico": grafico, "data_sinal": df.index[i - 1], "curta_sinal": float(mc.iloc[i - 1]), "longa_sinal": float(ml.iloc[i - 1]),
            "curta_anterior": float(mc.iloc[i - 2]), "longa_anterior": float(ml.iloc[i - 2]), "data_entrada": t["data_entrada"],
            "preco_entrada": float(t["preco_entrada"]), "quantidade": int(t["quantidade"]), "data_saida": t["data_saida"],
            "preco_saida": float(t["preco_saida"]), "motivo": t["motivo"], "resultado": float(t["pnl"]), "retorno_pct": float(t["retorno_pct"]),
            "pregoes": int(t["barras"]), "preco_entrada_bolsa": t.get("preco_entrada_bolsa"), "preco_saida_bolsa": t.get("preco_saida_bolsa")}


def _contas_sharpe(curvas: dict, corte: int, rf) -> dict:
    """As parcelas do Sharpe de cada curva, por período. A Selic fica de fora: ela é a referência da conta."""
    saida = {"inteiro": {}, "treino": {}, "teste": {}}
    for nome, curva in curvas.items():
        if nome != "selic":
            for periodo, trecho in (("inteiro", curva), ("treino", rob.recorte_treino(curva, corte)), ("teste", rob.recorte_teste(curva, corte))):
                saida[periodo][nome] = m.conta_sharpe(trecho.pct_change(), rf)
    return saida


def _blocos_periodo(curvas: dict, corte: int, rf) -> dict:
    """Retorno, risco, Sharpe e queda máxima de cada curva, no inteiro, no treino e no teste."""
    saida = {"inteiro": {}, "treino": {}, "teste": {}}
    for nome, curva in curvas.items():
        partes = {"inteiro": curva, "treino": rob.recorte_treino(curva, corte), "teste": rob.recorte_teste(curva, corte)}
        for periodo, trecho in partes.items():
            d = m.desempenho(trecho, rf)
            if nome == "selic":              # Sharpe e Sortino não se aplicam à própria taxa livre de risco
                d["sharpe"] = d["sortino"] = None
            d["valor_final"] = float(trecho.iloc[-1])
            saida[periodo][nome] = d
    return saida


def _retorno_ibov_bruto(fonte: CsvFonte, inicio: str, fim: str) -> pd.Series | None:
    """Variação diária do Ibovespa, usada para separar erro nos dados de um movimento geral do mercado."""
    try:
        return fonte.precos(universo.SIMBOLO_IBOV, inicio, fim)["Close"].pct_change()
    except DadosIndisponiveis:
        return None


def _variacao(curva: pd.Series, a: int, b: int) -> float:
    """Variação da curva na janela [a, b), a partir do último fechamento antes dela."""
    return float(curva.iloc[b - 1] / curva.iloc[a - 1] - 1.0)


def _janelas(lim, escolhas, indice, equity, bh, trades, selic, ibov, rf) -> list[dict]:
    """Uma linha por janela de teste: as escolhas feitas antes dela, o que o treino prometia e o que a janela entregou."""
    saida = []
    for k, (a, b) in enumerate(zip(lim[:-1], lim[1:])):
        e = escolhas[k]
        s_te = m.sharpe(equity.iloc[a - 1:b].pct_change().dropna(), rf)
        r_selic = float((1.0 + selic.iloc[a:b]).prod() - 1.0) if selic is not None else None
        r_est = _variacao(equity, a, b)
        entrou = (trades["data_entrada"] >= indice[a]) & (trades["data_entrada"] <= indice[b - 1]) if len(trades) else []
        notas = {x["ticker"]: x["sharpe_treino"] for x in e["selecao"]["ranking"] if x["selecionada"]} if e["selecao"] else None
        saida.append({
            "n": k + 1, "inicio": indice[a], "fim": indice[b - 1], "fim_treino": indice[a - 1], "n_treino": int(a), "n_pregoes": int(b - a),
            "acoes": e["acoes"], "pesos": e["pesos"], "fora": e["fora"], "caixa": e["caixa"], "notas_selecao": notas,
            "ritmo": e["ritmo"], "rotulo_ritmo": c.MEDIAS[e["ritmo"]]["rotulo"] if e["ritmo"] else None,
            "comparacao_ritmos": e["comparacao_ritmos"],
            "sharpe_treino": e["sharpe_treino"], "sharpe_teste": None if s_te != s_te else s_te,
            "retorno": r_est, "buy_hold": _variacao(bh, a, b), "selic": r_selic,
            "ibovespa": float((1.0 + ibov.iloc[a:b]).prod() - 1.0) if ibov is not None else None,
            "bateu_selic": None if r_selic is None else bool(r_est > r_selic),
            "n_operacoes": int(np.sum(entrou)),
            "mudou": bool(k > 0 and not jan._igual(escolhas[k - 1], e, com_ritmo=True)),
        })
    return saida


ETAPAS = {"dados": "Lendo os dados", "escolhas": "Fazendo as escolhas do treino", "simulacao": "Simulando a regra",
          "testes": "Rodando os testes estatísticos", "leitura": "Escrevendo a leitura do resultado"}


def executar(config: dict, fonte: CsvFonte | None = None, ao_progresso=None) -> dict:
    """Roda a análise completa descrita por `config` (ver `ConfigAnalise`).

    `ao_progresso`, opcional, recebe a chave de `ETAPAS` quando cada etapa começa. Só avisa o andamento: não muda nenhuma conta."""
    avisar = ao_progresso or (lambda etapa: None)
    avisar("dados")
    cfg = ConfigAnalise.from_dict(config).validar()
    fonte = fonte or criar_fonte(cfg.fonte, cfg.pasta_cache)
    inicio, fim = c.inicio_historico(), date.today().isoformat()
    protecao, custo_pct = c.PROTECOES[cfg.protecao], c.CUSTOS[cfg.custo]["pct"]
    com_imposto = c.CUSTOS[cfg.custo]["imposto"]
    stop, alvo = protecao["stop"], protecao["alvo"]
    automatica = cfg.selecao == "automatica"

    # ---------------------------------------------------------------- dados
    pedidos = list(universo.IBOVESPA) if automatica else cfg.tickers
    dados, avisos = carregar_ativos(fonte, pedidos, inicio, fim, c.MIN_PREGOES)
    if not dados:
        raise ValueError(f"Nenhuma ação com ao menos {c.MIN_PREGOES} pregões disponíveis. " + " ".join(avisos))
    ret_ibov = _retorno_ibov_bruto(fonte, inicio, fim)
    fora_da_selecao = []
    if automatica:
        fora_da_selecao = [{"ticker": t, "motivo": "sem histórico suficiente na fonte de dados"} for t in pedidos if t not in dados]
        avisos = []
        dados, fora = sel.filtrar_candidatas(dados, ret_ibov)
        fora_da_selecao += fora
        if not dados:
            raise ValueError("Nenhuma ação do Ibovespa tem histórico completo e confiável para a seleção automática.")
    else:
        for t, df in dados.items():
            avisos += [f"{t} {p}. Isso pode ser um erro na fonte de dados: confira antes de confiar no resultado."
                       for p in problemas_de_dados(df, ret_ibov)]
    fech = alinhar_fechamentos(dados)
    if len(fech) < c.MIN_PREGOES:
        raise ValueError(f"As ações escolhidas têm só {len(fech)} pregões em comum; o mínimo é {c.MIN_PREGOES}.")
    indice = fech.index
    lim = jan.limites(len(indice))
    corte = lim[0]                                      # primeiro pregão do teste

    bench, notas = bm.carregar(fonte, ["selic", "ibov"], indice)
    avisos += notas
    avisos += [a for a in getattr(fonte, "avisos", []) if a not in avisos]
    selic_bruta = bench.get("selic")
    selic_liq = imp.selic_liquida(selic_bruta) if selic_bruta is not None else None
    selic = selic_liq if com_imposto else selic_bruta         # com imposto, a Selic também paga o da renda fixa
    ibov = bench.get("ibov")
    if selic is None:
        avisos.append("Selic indisponível: os testes contra a taxa livre de risco ficam de fora e o Sharpe usa taxa 0%.")
    rf = selic if selic is not None else 0.0

    # ---------------------------------------------------------------- escolhas: antes de cada janela, só com o passado
    avisar("escolhas")
    dfs = {t: dados[t].loc[indice] for t in fech.columns}
    cache: dict = {}
    escolhas = [jan.escolher(dfs, fech, s, cfg, rf, selic, stop, alvo, custo_pct, cache, obrigatoria=k == 0) for k, s in enumerate(lim[:-1])]
    e1 = escolhas[0]
    if automatica:
        cfg.tickers = e1["acoes"]                       # as ações da 1ª janela, escolhidas com o treino inicial
    pesos, tickers = e1["pesos"], list(e1["pesos"])
    divisao = cfg.divisao if len(e1["acoes"]) > 1 else "igual"
    sem_dinheiro = sorted({t for e in escolhas for t in e["fora"]})
    if sem_dinheiro:
        avisos.append(f"Ficaram sem dinheiro em ao menos uma janela, porque a divisão escolhida lhes deu menos de 0,5%: {', '.join(sem_dinheiro)}.")
    caixa = [k + 1 for k, e in enumerate(escolhas) if e["caixa"]]
    if caixa:
        avisos.append(f"Na janela {', '.join(map(str, caixa))}, nenhuma ação passou nos critérios da seleção com os dados anteriores a ela, "
                      "e o dinheiro ficou parado.")
    blocos = jan.blocos(lim, escolhas)
    md = c.MEDIAS[e1["ritmo"]]

    # ---------------------------------------------------------------- a simulação
    avisar("simulacao")
    sim = jan.simular(dfs, indice, blocos, cfg.capital, stop, alvo, custo_pct, cache, com_imposto=com_imposto)
    trades, equity, apuracao = sim["trades"], sim["equity"], sim["apuracao"]      # a curva já vem depois do imposto
    antes_estrategia = float((jan.simular(dfs, indice, blocos, cfg.capital, stop, alvo, custo_pct, cache) if com_imposto else sim)["equity"].iloc[-1])    # a mesma regra, sem pagar imposto
    trades = _valores(_detalhar_operacoes(trades, custo_pct, imp.rateio(imp.vendas_das_operacoes(trades), apuracao)))
    trades = _precos_da_bolsa(trades, fonte)
    vendas_bh: list = []
    bh, ganhos_bh = jan.simular_buy_hold(fech, blocos, cfg.capital, custo_pct, vendas_bh)
    bh, apuracao_bh = _liquida(bh, vendas_bh, com_imposto)
    curvas = {"estrategia": equity, "buy_hold": bh}
    if selic is not None:
        curvas["selic"] = cfg.capital * (1.0 + selic).cumprod()
    if ibov is not None:
        curvas["ibovespa"] = cfg.capital * (1.0 + ibov).cumprod()

    data_corte = indice[corte]
    ret_est, ret_bh = equity.pct_change().dropna(), bh.pct_change().dropna()
    r_est_te, r_bh_te = ret_est.iloc[corte - 1:], ret_bh.iloc[corte - 1:]
    sel_te = selic.iloc[corte:] if selic is not None else None
    ib_te = ibov.iloc[corte:] if ibov is not None else None
    trades_teste = trades[trades["data_entrada"] >= data_corte]
    trades_treino = trades[trades["data_entrada"] < data_corte]      # treino + teste = todas as operações
    capital_teste = float(equity.iloc[corte - 1])
    periodos = _blocos_periodo(curvas, corte, rf)
    sel_ret_te = float((1.0 + selic.iloc[corte:]).prod() - 1.0) if selic is not None else None

    # ---------------------------------------------------------------- 1. foi sorte?
    avisar("testes")
    sharpe_teste = periodos["teste"]["estrategia"]["sharpe"]
    n_candidatas = fech.shape[1] if automatica else 1
    n_tentativas = c.N_COMBINACOES * n_candidatas      # escolher entre muitas ações também é tentar muitas vezes
    foi_sorte = {
        "ic_estrategia": est.intervalo_confianca(r_est_te - sel_te) if sel_te is not None else None,
        "ic_buy_hold": est.intervalo_confianca(r_bh_te - sel_te) if sel_te is not None else None,
        "alfa_beta": est.alfa_beta(r_est_te, ib_te, sel_te if sel_te is not None else 0.0) if ib_te is not None else None,
        "sharpe_desconto": est.sharpe_com_desconto(sharpe_teste, len(r_est_te), n_tentativas),
    }

    # ---------------------------------------------------------------- 2. aguenta variações?
    retornos_ano = {"estrategia": ret_est, "buy_hold": ret_bh}
    if selic is not None:
        retornos_ano["selic"] = selic.iloc[1:]
    combinacoes = []
    for chave_m, md_m in c.MEDIAS.items():           # as mesmas ações e pesos de cada janela, com o ritmo e a saída fixos
        for chave_p, pr in c.PROTECOES.items():
            r = jan.simular(dfs, indice, blocos, cfg.capital, pr["stop"], pr["alvo"], custo_pct, cache, ritmo=chave_m, com_imposto=com_imposto)
            eq_r = r["equity"]
            combinacoes.append({"medias": chave_m, "protecao": chave_p, "curta": md_m["curta"], "longa": md_m["longa"],
                                **jan.resumo_combinacao(eq_r, len(r["trades"]), corte, rf, sel_ret_te)})
    custos = []
    for chave_c, cc in c.CUSTOS.items():               # cada variação compara com a Selic nas mesmas condições
        r = jan.simular(dfs, indice, blocos, cfg.capital, stop, alvo, cc["pct"], cache, com_imposto=cc["imposto"])
        eq_r, ap_r = r["equity"], r["apuracao"]
        s_var = selic_liq if cc["imposto"] else selic_bruta
        ret_s = float((1.0 + s_var.iloc[corte:]).prod() - 1.0) if s_var is not None else None
        custos.append({"custo": chave_c, "pct": cc["pct"], "imposto": cc["imposto"], "rotulo": cc["rotulo"],
                       "imposto_pago": float(ap_r["imposto"].sum()) if len(ap_r) else 0.0, "retorno_selic_teste": ret_s,
                       **jan.resumo_combinacao(eq_r, len(r["trades"]), corte, rf, ret_s)})
    n_bateram = sum(1 for ln in combinacoes if ln["bateu_selic"])
    variacoes = {
        "ano_a_ano": rob.ano_a_ano(retornos_ano),
        "combinacoes": combinacoes,
        "n_combinacoes": len(combinacoes),
        "n_bateram_selic": n_bateram if selic is not None else None,
        "custos": custos,
    }

    # ---------------------------------------------------------------- 3. e se a sequência fosse outra?
    exposicao = sim["exposicao"]
    trading_inteiro = _resumo_operacoes(trades, custo_pct, exposicao, equity, apuracao)
    trading_treino = _resumo_operacoes(trades_treino, custo_pct, exposicao.iloc[:corte], rob.recorte_treino(equity, corte), apuracao)
    trading_teste = _resumo_operacoes(trades_teste, custo_pct, exposicao.iloc[corte:], rob.recorte_teste(equity, corte), apuracao)
    sequencia = {
        "monte_carlo": rob.monte_carlo_ordem(trades_teste, capital_teste),
        "sem_melhores": rob.sem_melhores_trades(trades_teste, capital_teste),
    }

    # ---------------------------------------------------------------- carteira
    carteira = None
    concentracao = None
    if len(e1["acoes"]) >= 2:
        todas = [t for t in fech.columns if any(t in e["acoes"] for e in escolhas)]
        rets = fech[todas].pct_change().iloc[1:]       # rets.iloc[j] é o retorno do pregão j + 1
        rf_anuais = [float(selic.iloc[1:s].mean() * m.DIAS_ANO) if selic is not None else 0.0 for s in lim[:-1]]
        carteira = cart.analisar_carteira(rets, lim, [e["acoes"] for e in escolhas], divisao, rf, rf_anuais, ibov, c.N_CARTEIRAS, c.SEMENTE)
        carteira["pesos"] = pesos
        carteira["correlacao"] = est.matriz_correlacao(rets[e1["acoes"]].iloc[:corte - 1]).round(4).to_dict()
    usadas = [t for t in fech.columns if any(t in e["pesos"] for e in escolhas)]
    if len(usadas) >= 2:
        peso_medio = {t: sum((b - a) * e["pesos"].get(t, 0.0) for a, b, e in blocos[1:]) / (lim[-1] - lim[0]) for t in usadas}
        ganhos_est = {t: float(trades.loc[trades["ticker"] == t, "pnl"].sum()) if len(trades) else 0.0 for t in usadas}
        concentracao = {}
        for chave, ganhos in (("estrategia", ganhos_est), ("buy_hold", {t: ganhos_bh.get(t, 0.0) for t in usadas})):
            info = cart.analisar_concentracao(ganhos, peso_medio, cfg.capital)
            total = sum(ganhos.values())
            info["contribuicao"] = [{"ticker": t, "peso_medio": peso_medio[t], "ganho": ganhos[t],
                                     "participacao": ganhos[t] / total if total > 0 else None} for t in usadas]
            concentracao[chave] = info

    # ---------------------------------------------------------------- a seleção ajudou?
    selecao = None
    if automatica:
        n = fech.shape[1]
        iguais, g_iguais = cart.curva_buy_hold(fech, {t: 1.0 / n for t in fech.columns}, cfg.capital, custo_pct)
        iguais = _liquida(iguais, [{"data": indice[-1], "valor_venda": cfg.capital / n + v, "resultado": v, "day_trade": False}
                                   for v in g_iguais.values()], com_imposto)[0]
        na_janela_1 = jan.retorno_das_acoes(sim, lim[0], lim[1])
        selecao = {
            "n_universo": len(universo.IBOVESPA), "data_carteira": universo.DATA_CARTEIRA, "n_candidatas": n,
            "fora": fora_da_selecao, "n_tentativas": n_tentativas,
            "ranking": [{**ln, "retorno_teste": na_janela_1.get(ln["ticker"])} for ln in e1["selecao"]["ranking"]],
            "pontuacao_ritmos": e1["selecao"]["pontuacao_ritmos"],
            "candidatas_iguais": m.desempenho(rob.recorte_teste(iguais, corte), rf),
        }

    janelas = _janelas(lim, escolhas, indice, equity, bh, trades, selic, ibov, rf)
    primeiro_trecho = trades[trades["data_entrada"] <= indice[sim["trechos"][0][1] - 1]] if len(trades) else trades
    resultado = {
        "versao": VERSAO,
        "aviso_legal": AVISO,
        "config": cfg.to_dict(),
        "chave_cache": chave_cache(config),
        "avisos": avisos,
        "tickers": tickers,
        "pesos": pesos,
        "escolhas": {
            "divisao": c.DIVISOES[divisao]["rotulo"] if len(e1["acoes"]) > 1 else None,
            "medias": md["rotulo"], "curta": md["curta"], "longa": md["longa"],
            "medias_pelo_treino": cfg.medias == c.MEDIAS_PELO_TREINO, "comparacao_ritmos": e1["comparacao_ritmos"],
            "ritmo_muda": len({e["ritmo"] for e in escolhas if e["ritmo"]}) > 1,
            "protecao": protecao["rotulo"], "stop": stop, "alvo": alvo,
            "custo": c.CUSTOS[cfg.custo]["rotulo"], "custo_pct": custo_pct, "imposto": com_imposto, "capital": cfg.capital,
        },
        "periodo": {
            "inicio": indice[0], "fim": indice[-1], "n_pregoes": int(len(indice)),
            "inicio_teste": data_corte, "fim_treino": indice[corte - 1],
            "n_treino": int(corte), "n_teste": int(len(indice) - corte), "n_janelas": len(lim) - 1,
            "anos": (indice[-1] - indice[0]).days / 365.25, "anos_teste": (indice[-1] - data_corte).days / 365.25,
            "inicios_janelas": [indice[a] for a in lim[:-1]],
        },
        "janelas": janelas,
        "curvas": {k: para_pontos(v) for k, v in curvas.items()},
        "desempenho": periodos,
        "conta_sharpe": _contas_sharpe(curvas, corte, rf),
        "primeira_operacao_treino": _primeira_operacao(dfs, trades_treino, md["curta"], md["longa"]),
        "pior_momento": {"estrategia": _pior_momento(equity), "buy_hold": _pior_momento(bh)},
        "exemplo_cruzamento": _exemplo_cruzamento(dfs, pesos, primeiro_trecho, md["curta"], md["longa"]),
        "operacoes": {
            "inteiro": trading_inteiro, "treino": trading_treino, "teste": trading_teste, "lista": trades,
            "histograma_retornos": est.histograma(trades["retorno_pct"].to_numpy(float), 30) if len(trades) else None,
            "tempo_comprado": float(exposicao.mean()),
        },
        "imposto": {"aplicado": com_imposto, "estrategia": _apuracao_json(apuracao), "buy_hold": _apuracao_json(apuracao_bh),
                    "antes_estrategia": antes_estrategia},
        "foi_sorte": foi_sorte,
        "variacoes": variacoes,
        "sequencia": sequencia,
        "carteira": carteira,
        "concentracao": concentracao,
        "selecao": selecao,
        "glossario": GLOSSARIO,
        "referencias": REFERENCIAS,
    }
    avisar("leitura")
    resultado = json_seguro(resultado)
    resultado["leitura"] = leitura.montar(resultado)
    resultado["decisoes_treino"] = leitura.decisoes_treino(resultado)
    resultado["roteiro_treino"] = leitura.roteiro_treino(resultado)
    resultado["frase_sharpe"] = leitura.frase_sharpe(resultado)
    return resultado
