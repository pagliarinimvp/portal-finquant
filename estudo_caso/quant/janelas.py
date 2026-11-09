"""Janelas sucessivas: o treino anda junto com o tempo.

O histórico começa com um treino inicial (a primeira metade dos pregões), e a segunda metade vira `N_JANELAS` janelas de teste.
Antes de cada janela, as escolhas (ações, pesos e ritmo) são refeitas só com os pregões anteriores a ela, e a janela é
simulada com essas escolhas. Assim, cada escolha é conferida com dados que ela não viu, em vários momentos do mercado, e não
em um único corte. É a avaliação com origem móvel (rolling origin) descrita por Tashman (2000).

Simulação: enquanto as escolhas não mudam, a carteira segue sem interrupção, como se a regra rodasse direto. Quando mudam, as
posições abertas são vendidas no fechamento do último pregão da janela, pagando o custo (motivo `fim_janela`), e o dinheiro é
dividido pelas novas escolhas. Os sinais são calculados no histórico inteiro e são causais: nada depois de um pregão muda o
sinal dele.
"""
import numpy as np
import pandas as pd

from . import carteira as cart
from . import estrategias, imposto as imp, metricas as m, selecao as sel
from .backtest import COLUNAS_TRADES, Conta, executar_backtest
from .config import FRACAO_TREINO, MEDIAS, MEDIAS_PELO_TREINO, N_JANELAS


def limites(n: int, fracao: float = FRACAO_TREINO, n_janelas: int = N_JANELAS) -> list[int]:
    """O primeiro pregão de cada janela de teste e, no fim, `n`. O primeiro valor é o fim do treino inicial."""
    corte = int(n * fracao)
    return [corte + round(k * (n - corte) / n_janelas) for k in range(n_janelas + 1)]


def _sinais(dfs: dict, t: str, curta: int, longa: int, cache: dict) -> pd.DataFrame:
    chave = (t, curta, longa)
    if chave not in cache:
        cache[chave] = estrategias.gerar_sinais(dfs[t], curta, longa)
    return cache[chave]


def rodar_trecho(dfs: dict, pesos: dict, curta: int, longa: int, capital: float, stop, alvo, custo_pct: float,
                 a: int, b: int, cache: dict) -> dict:
    """A regra em cada ação, do pregão a ao b − 1, com `capital × peso`, começando sem posição."""
    return {t: executar_backtest(dfs[t].iloc[a:b], _sinais(dfs, t, curta, longa, cache).iloc[a:b], capital * w, stop, alvo, custo_pct)
            for t, w in pesos.items()}


def sharpe_no_treino(dfs: dict, pesos: dict, ritmo: str, capital: float, stop, alvo, custo_pct: float, s: int, rf, cache: dict) -> float | None:
    """O Sharpe da carteira com estas escolhas nos pregões 0 a s − 1: o que o treino prometia."""
    md = MEDIAS[ritmo]
    por_ativo = rodar_trecho(dfs, pesos, md["curta"], md["longa"], capital, stop, alvo, custo_pct, 0, s, cache)
    v = m.sharpe(sum(r.equity for r in por_ativo.values()).pct_change().dropna(), rf)
    return None if v != v else v


def escolher(dfs: dict, fech: pd.DataFrame, s: int, cfg, rf, selic, stop, alvo, custo_pct: float, cache: dict,
             obrigatoria: bool) -> dict:
    """As escolhas para a janela que começa no pregão `s`, feitas só com os pregões 0 a s − 1.

    `fech` traz os fechamentos de todas as candidatas. Se a seleção automática não aprovar nenhuma ação, a janela fica em
    caixa; no treino inicial (`obrigatoria`), o erro sobe, porque sem escolha não há análise."""
    automatica = cfg.selecao == "automatica"
    auto = None
    if automatica:
        try:
            auto = sel.selecionar({t: dfs[t] for t in fech.columns}, s, cfg.medias, stop, alvo, custo_pct, cfg.capital, rf)
        except ValueError:
            if obrigatoria:
                raise
            return {"acoes": [], "pesos": {}, "fora": [], "ritmo": None, "comparacao_ritmos": None, "selecao": None,
                    "sharpe_treino": None, "caixa": True}
        acoes, ritmo = auto["tickers"], auto["ritmo"]
    else:
        acoes, ritmo = list(fech.columns), (None if cfg.medias == MEDIAS_PELO_TREINO else cfg.medias)
    rf_anual = float(selic.iloc[1:s].mean() * m.DIAS_ANO) if selic is not None else 0.0
    divisao = cfg.divisao if len(acoes) > 1 else "igual"
    pesos, fora = cart.dividir(fech[acoes].pct_change().iloc[1:s], divisao, rf_anual)
    comparacao = None
    if ritmo is None:                                   # ações da pessoa, ritmo pelo treino
        comparacao = [{"medias": k, "curta": md["curta"], "longa": md["longa"],
                       "sharpe_treino": sharpe_no_treino(dfs, pesos, k, cfg.capital, stop, alvo, custo_pct, s, rf, cache)} for k, md in MEDIAS.items()]
        ritmo = max(comparacao, key=lambda x: -np.inf if x["sharpe_treino"] is None else x["sharpe_treino"])["medias"]
    elif automatica and cfg.medias == MEDIAS_PELO_TREINO:
        comparacao = auto["pontuacao_ritmos"]
    return {"acoes": acoes, "pesos": pesos, "fora": fora, "ritmo": ritmo, "comparacao_ritmos": comparacao, "selecao": auto,
            "sharpe_treino": sharpe_no_treino(dfs, pesos, ritmo, cfg.capital, stop, alvo, custo_pct, s, rf, cache), "caixa": False}


# --------------------------------------------------------------------------- simulação em trechos
def _igual(a: dict, b: dict, com_ritmo: bool) -> bool:
    mesmos = a["pesos"].keys() == b["pesos"].keys() and all(abs(a["pesos"][t] - b["pesos"][t]) < 1e-9 for t in a["pesos"])
    return mesmos and (not com_ritmo or a["ritmo"] == b["ritmo"])


def _trechos(blocos: list[tuple[int, int, dict]], com_ritmo: bool) -> list[tuple[int, int, dict]]:
    """Junta blocos seguidos com as mesmas escolhas: a carteira não para entre eles."""
    saida = []
    for a, b, e in blocos:
        if saida and _igual(saida[-1][2], e, com_ritmo):
            saida[-1] = (saida[-1][0], b, saida[-1][2])
        else:
            saida.append((a, b, e))
    return saida


def blocos(lim: list[int], escolhas: list[dict]) -> list[tuple[int, int, dict]]:
    """O treino inicial usa as escolhas da 1ª janela, que foram feitas com ele; cada janela usa as suas."""
    return [(0, lim[0], escolhas[0])] + [(a, b, e) for a, b, e in zip(lim[:-1], lim[1:], escolhas)]


class _Fisco:
    """O imposto de renda pago com o dinheiro da conta, como na vida real.

    Na venda com ganho, a regra separa 15% do ganho (20% no day trade): esse dinheiro sai do saldo e não entra na próxima
    compra. No vencimento (último pregão do mês seguinte), o mês é apurado com todas as vendas dele, o imposto devido é pago e
    o que sobrou da reserva volta para o saldo. O imposto devido nunca passa da reserva, porque isenção e prejuízos só o
    reduzem. Tudo é causal: a apuração usa só vendas já feitas."""

    def __init__(self, indice: pd.DatetimeIndex):
        self.indice, self.pos = indice, {d: i for i, d in enumerate(indice)}
        self.meses: dict = {}            # mês -> vendas, resultado comum, resultado day trade, reserva
        self.agenda: dict = {}           # posição do vencimento -> meses
        self.cofre = self.prej_c = self.prej_d = 0.0
        self.linhas: list = []

    def venda(self, t: tuple) -> float:
        """Registra a venda da operação `t` (linha de COLUNAS_TRADES) e devolve o valor separado para o imposto."""
        entrada, _, saida, preco_saida, qtd, _, pnl, _, _ = t
        mes, day = pd.Timestamp(saida).to_period("M"), pd.Timestamp(entrada) == pd.Timestamp(saida)
        if mes not in self.meses:
            self.meses[mes] = {"vendas": 0.0, "comum": 0.0, "day": 0.0, "reserva": 0.0}
            self.agenda.setdefault(self.pos[imp._vencimento(mes, self.indice)], []).append(mes)
        m_ = self.meses[mes]
        m_["vendas"] += qtd * preco_saida
        m_["day" if day else "comum"] += pnl
        reserva = (imp.ALIQUOTA_DAY_TRADE if day else imp.ALIQUOTA_COMUM) * max(pnl, 0.0)
        m_["reserva"] += reserva
        self.cofre += reserva
        return reserva

    def vencimentos(self, i: int) -> float:
        """Apura os meses que vencem no pregão i, paga o imposto e devolve o que sobrou das reservas."""
        volta = 0.0
        for mes in sorted(self.agenda.pop(i, [])):
            m_ = self.meses.pop(mes)
            isento, imp_c, imp_d, self.prej_c, self.prej_d = imp.apurar_mes(m_["vendas"], m_["comum"], m_["day"], self.prej_c, self.prej_d)
            devido = imp_c + imp_d
            volta += m_["reserva"] - devido
            self.cofre -= m_["reserva"]
            self.linhas.append((str(mes), m_["vendas"], m_["comum"], m_["day"], isento, imp_c, imp_d, devido,
                                self.prej_c, self.prej_d, self.indice[i] if devido > 0 else None))
        return volta

    def apuracao(self) -> pd.DataFrame:
        return pd.DataFrame(self.linhas, columns=imp.COLUNAS_APURACAO)


def simular(dfs: dict, indice: pd.DatetimeIndex, blocos_: list[tuple[int, int, dict]], capital: float, stop, alvo, custo_pct: float,
            cache: dict, ritmo: str | None = None, com_imposto: bool = False) -> dict:
    """A regra em todo o histórico, trecho a trecho, com as ações andando juntas pregão a pregão. `ritmo` força um ritmo em
    todas as janelas (sensibilidade). Com `com_imposto`, o imposto sai do saldo (veja `_Fisco`) e a curva já é a líquida.

    Cada operação traz o saldo parado na conta, somando todas as ações, no fim do pregão da compra e no da venda."""
    trechos = _trechos(blocos_, com_ritmo=ritmo is None)
    fisco = _Fisco(indice) if com_imposto else None
    partes, exposicao, lista, por_acao = [], [], [], []
    cap = float(capital)
    for j, (a, b, e) in enumerate(trechos):
        idx = indice[a:b]
        curva = np.empty(b - a)
        if not e["pesos"]:
            for k in range(b - a):
                if fisco:
                    cap += fisco.vencimentos(a + k)
                curva[k] = cap + (fisco.cofre if fisco else 0.0)
            partes.append(pd.Series(curva, index=idx))
            exposicao.append(pd.Series(0.0, index=idx))
            por_acao.append({})
            continue
        md = MEDIAS[ritmo or e["ritmo"]]
        contas = {t: Conta(dfs[t].iloc[a:b], _sinais(dfs, t, md["curta"], md["longa"], cache).iloc[a:b], cap * w, stop, alvo, custo_pct)
                  for t, w in e["pesos"].items()}
        saldos = {t: [] for t in contas}               # (saldo na compra, saldo na venda) de cada operação, na ordem
        compra = {t: None for t in contas}
        for k in range(b - a):
            antes = {t: len(x.trades) for t, x in contas.items()}
            for x in contas.values():
                x.passo(k)
            if fisco:
                for t, x in contas.items():
                    for tr in x.trades[antes[t]:]:
                        x.caixa -= fisco.venda(tr)
                volta = fisco.vencimentos(a + k)
                if volta:
                    base = sum(x.caixa for x in contas.values())
                    for x in contas.values():
                        x.caixa += volta * x.caixa / base
            for x in contas.values():
                x.marcar(k)
            curva[k] = sum(x.equity[k] for x in contas.values()) + (fisco.cofre if fisco else 0.0)
            livre = sum(x.livre(k) for x in contas.values())
            for t, x in contas.items():
                for _ in x.trades[antes[t]:]:
                    saldos[t].append((livre if compra[t] is None else compra[t], livre))
                    compra[t] = None
                if x.comprado and x.i_ent == k:
                    compra[t] = livre
        partes.append(pd.Series(curva, index=idx))
        res = {t: x.resultado() for t, x in contas.items()}
        exposicao.append(sum(r.posicao for r in res.values()) / len(res))
        for t, r in res.items():
            tr = r.trades.assign(ticker=t, ritmo=ritmo or e["ritmo"],
                                 saldo_apos_compra=[s_[0] for s_ in saldos[t]], saldo_apos_venda=[s_[1] for s_ in saldos[t]])
            if j < len(trechos) - 1:
                tr.loc[tr["motivo"] == "fim_dados", "motivo"] = "fim_janela"
            lista.append(tr)
        por_acao.append({t: (r.equity, r.capital_inicial) for t, r in res.items()})
        cap = float(sum(r.equity.iloc[-1] for r in res.values()))
    cheias = [x for x in lista if len(x)]
    trades = (pd.concat(cheias, ignore_index=True).sort_values("data_entrada", kind="stable", ignore_index=True) if cheias
              else pd.DataFrame(columns=[*COLUNAS_TRADES, "ticker", "ritmo", "saldo_apos_compra", "saldo_apos_venda"]))
    return {"equity": pd.concat(partes).rename("equity"), "trades": trades, "exposicao": pd.concat(exposicao),
            "trechos": [(a, b) for a, b, _ in trechos], "por_acao": por_acao,
            "apuracao": fisco.apuracao() if fisco else pd.DataFrame(columns=imp.COLUNAS_APURACAO)}


def retorno_das_acoes(sim: dict, a: int, b: int) -> dict:
    """O retorno da regra em cada ação da janela [a, b), sobre o dinheiro que ela tinha no início da janela."""
    for (ta, tb), acoes in zip(sim["trechos"], sim["por_acao"]):
        if ta <= a and b <= tb:
            saida = {}
            for t, (eq, inicial) in acoes.items():
                antes = inicial if a == ta else float(eq.iloc[a - ta - 1])
                saida[t] = float(eq.iloc[b - ta - 1]) / antes - 1.0
            return saida
    return {}


def simular_buy_hold(fech: pd.DataFrame, blocos_: list[tuple[int, int, dict]], capital: float, custo_pct: float,
                     vendas: list | None = None) -> tuple[pd.Series, dict]:
    """Comprar e segurar as ações e os pesos de cada janela. Quando eles mudam, vende tudo e compra de novo, pagando o custo.

    Se `vendas` vier, recebe uma linha por ação vendida (data, valor da venda e resultado), para a conta do imposto."""
    partes, ganhos, cap = [], {}, float(capital)
    for a, b, e in _trechos(blocos_, com_ritmo=False):
        if not e["pesos"]:
            partes.append(pd.Series(cap, index=fech.index[a:b]))
        else:
            curva, g = cart.curva_buy_hold(fech[list(e["pesos"])].iloc[a:b], e["pesos"], cap, custo_pct)
            partes.append(curva)
            for t, v in g.items():
                ganhos[t] = ganhos.get(t, 0.0) + v
                if vendas is not None:
                    vendas.append({"data": fech.index[b - 1], "valor_venda": cap * e["pesos"][t] + v, "resultado": v, "day_trade": False})
        cap = float(partes[-1].iloc[-1])
    return pd.concat(partes).rename("buy_hold"), ganhos


def resumo_combinacao(equity: pd.Series, n_trades: int, corte: int, rf, retorno_selic_teste) -> dict:
    tr, te = equity.iloc[:corte], equity.iloc[corte - 1:]
    ret_te = float(te.iloc[-1] / te.iloc[0] - 1.0)
    return {
        "sharpe_treino": m.sharpe(tr.pct_change().dropna(), rf),
        "sharpe_teste": m.sharpe(te.pct_change().dropna(), rf),
        "retorno_teste": ret_te,
        "n_trades": int(n_trades),
        "bateu_selic": None if retorno_selic_teste is None else bool(ret_te > retorno_selic_teste),
    }
