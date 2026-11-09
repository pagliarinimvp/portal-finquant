"""Imposto de renda de pessoa física sobre o lucro com ações e sobre a Selic, pelas regras vigentes em 07/11/2026.

Ações à vista (IN RFB nº 1.585/2015 e Lei nº 11.033/2004):
* A apuração é mensal. Operações comuns pagam 15% sobre o ganho líquido do mês (IN 1.585, art. 57; Lei 11.033, art. 2º, II).
* Ficam isentos os ganhos das operações comuns no mês em que o total das vendas de ações não passa de R$ 20.000
  (Lei 11.033, art. 3º, I; IN 1.585, art. 59, I). A isenção não vale para day trade (art. 59, § 2º, I).
* Day trade, a compra e a venda no mesmo dia, paga 20% (IN 1.585, art. 65, § 11; Lei 11.033, art. 2º, I).
* Perdas abatem ganhos do próprio mês e dos meses seguintes, sem prazo, e as de day trade só abatem ganhos de day trade
  (IN 1.585, arts. 64 e 65, § 10).
* O imposto é pago até o último dia útil do mês seguinte ao da apuração (IN 1.585, art. 56, § 5º). Aqui, no fechamento do
  último pregão desse mês.
* As tarifas da B3 já entram no resultado de cada operação, como despesa dedutível.

Escolhas desta ferramenta, para não prometer precisão que a simulação não tem:
* Para o limite de R$ 20.000, entram todas as vendas do mês, inclusive as de day trade: é a leitura mais conservadora.
* Na regra, o imposto sai do dinheiro da conta (`janelas._Fisco`): a venda com lucro separa 15% (20% no day trade), e no
  vencimento o imposto devido é pago e o resto volta. Em comprar e segurar (`aplicar`), o imposto pago sai do patrimônio, e
  a carteira fica menor na mesma proporção dali em diante (as posições não são refeitas em lotes inteiros).
* Ficam de fora: o imposto retido na fonte (0,005% e 1%), que é só uma antecipação descontada do imposto do mês; o mínimo de
  R$ 10 por DARF; e a declaração anual.

Selic (Lei 11.033, art. 1º): renda fixa paga imposto na fonte, no resgate, pela tabela regressiva: 22,5% até 180 dias, 20% até
360, 17,5% até 720 e 15% depois disso. A curva líquida é o valor que a pessoa receberia se resgatasse naquele dia, aplicando
tudo no primeiro pregão.
"""
import numpy as np
import pandas as pd

ALIQUOTA_COMUM = 0.15
ALIQUOTA_DAY_TRADE = 0.20
LIMITE_ISENCAO = 20_000.0
TABELA_RENDA_FIXA = ((180, 0.225), (360, 0.20), (720, 0.175), (np.inf, 0.15))
COLUNAS_APURACAO = ["mes", "vendas", "resultado_comum", "resultado_day_trade", "isento", "imposto_comum", "imposto_day_trade",
                    "imposto", "prejuizo_comum", "prejuizo_day_trade", "data_pagamento"]


def aliquota_renda_fixa(dias) -> np.ndarray:
    """A alíquota da tabela regressiva para quem resgata depois de `dias` corridos."""
    dias = np.asarray(dias, dtype=float)
    return np.select([dias <= lim for lim, _ in TABELA_RENDA_FIXA], [a for _, a in TABELA_RENDA_FIXA])


def selic_liquida(selic: pd.Series) -> pd.Series:
    """Retornos diários da Selic depois do imposto, a partir do valor líquido de resgate de cada dia."""
    bruto = (1.0 + selic).cumprod()
    dias = (selic.index - selic.index[0]).days
    liquido = 1.0 + (bruto - 1.0) * (1.0 - aliquota_renda_fixa(dias))
    return (liquido / liquido.shift(1, fill_value=1.0) - 1.0).rename(selic.name)


def vendas_das_operacoes(trades: pd.DataFrame) -> pd.DataFrame:
    """Cada operação da regra vira uma venda: data, valor vendido, resultado já com as tarifas e se foi day trade."""
    if not len(trades):
        return pd.DataFrame(columns=["data", "valor_venda", "resultado", "day_trade"])
    return pd.DataFrame({"data": pd.to_datetime(trades["data_saida"]).to_numpy(),
                         "valor_venda": (trades["quantidade"] * trades["preco_saida"]).astype(float).to_numpy(),
                         "resultado": trades["pnl"].astype(float).to_numpy(),
                         "day_trade": (pd.to_datetime(trades["data_entrada"]) == pd.to_datetime(trades["data_saida"])).to_numpy()})


def _vencimento(mes: pd.Period, indice: pd.DatetimeIndex) -> pd.Timestamp:
    """O último pregão do mês seguinte ao da apuração. Se os dados acabam antes, o último pregão disponível."""
    seguinte = indice[indice.to_period("M") == mes + 1]
    return seguinte[-1] if len(seguinte) else indice[-1]


def _saldo(resultado: float, prejuizo: float, aliquota: float, isento: bool) -> tuple[float, float]:
    """Imposto do mês e prejuízo que sobra para os meses seguintes."""
    if isento:                                  # ganho isento não consome prejuízo; perda vai para os meses seguintes
        return 0.0, prejuizo + max(-resultado, 0.0)
    base = resultado - prejuizo
    return (aliquota * base, 0.0) if base > 0 else (0.0, -base)


def apurar_mes(vendas: float, comum: float, day: float, prej_c: float, prej_d: float) -> tuple[bool, float, float, float, float]:
    """A apuração de um mês: se ficou isento, o imposto das operações comuns e do day trade e os prejuízos que sobram."""
    isento = vendas <= LIMITE_ISENCAO
    imp_c, prej_c = _saldo(comum, prej_c, ALIQUOTA_COMUM, isento)
    imp_d, prej_d = _saldo(day, prej_d, ALIQUOTA_DAY_TRADE, False)
    return isento, imp_c, imp_d, prej_c, prej_d


def aplicar(curva: pd.Series, vendas: pd.DataFrame) -> tuple[pd.Series, pd.DataFrame]:
    """A curva depois do imposto e a apuração mês a mês.

    Cada pagamento tira dinheiro do patrimônio, e o que vem depois encolhe na mesma proporção: as vendas seguintes são
    escaladas pelo fator do dia anterior a elas, e o fator cai `pagamento / patrimônio bruto` no dia do pagamento."""
    indice = curva.index
    if not len(vendas):
        return curva.copy(), pd.DataFrame(columns=COLUNAS_APURACAO)
    vendas = vendas.sort_values("data", kind="stable")
    meses = vendas["data"].dt.to_period("M")
    pagamentos: list[tuple[pd.Timestamp, float]] = []    # (data, fração do patrimônio bruto que saiu)
    linhas, prej_c, prej_d = [], 0.0, 0.0

    def fator_antes(d):
        return 1.0 - sum(fr for t, fr in pagamentos if t < d)

    for mes, grupo in vendas.groupby(meses, sort=True):
        f = np.array([fator_antes(d) for d in grupo["data"]])
        valor, res, dt = grupo["valor_venda"].to_numpy() * f, grupo["resultado"].to_numpy() * f, grupo["day_trade"].to_numpy(bool)
        total = float(valor.sum())
        comum, day = float(res[~dt].sum()), float(res[dt].sum())
        isento, imp_c, imp_d, prej_c, prej_d = apurar_mes(total, comum, day, prej_c, prej_d)
        imposto = imp_c + imp_d
        quando = _vencimento(mes, indice) if imposto > 0 else None
        if imposto > 0:
            pagamentos.append((quando, imposto / float(curva.loc[quando])))
        linhas.append((str(mes), total, comum, day, isento, imp_c, imp_d, imposto, prej_c, prej_d, quando))
    fator = pd.Series(1.0, index=indice)
    for quando, fr in pagamentos:
        fator.loc[quando:] -= fr
    return (curva * fator).rename(curva.name), pd.DataFrame(linhas, columns=COLUNAS_APURACAO)


def rateio(vendas: pd.DataFrame, apuracao: pd.DataFrame) -> np.ndarray:
    """O imposto de cada venda, na ordem de `vendas`: o imposto do mês dividido entre as vendas com ganho daquele mês,
    na proporção do ganho, separando operações comuns e day trade. Venda com perda fica com zero, porque reduz o imposto."""
    parte = np.zeros(len(vendas))
    if not len(vendas) or not len(apuracao):
        return parte
    meses = pd.to_datetime(vendas["data"]).dt.to_period("M").astype(str).to_numpy()
    res, dt = vendas["resultado"].to_numpy(float), vendas["day_trade"].to_numpy(bool)
    for linha in apuracao.itertuples():
        for imposto, tipo in ((linha.imposto_comum, False), (linha.imposto_day_trade, True)):
            if not imposto or imposto <= 0:
                continue
            alvo = (meses == linha.mes) & (dt == tipo) & (res > 0)
            if alvo.any():
                parte[alvo] = imposto * res[alvo] / res[alvo].sum()
    return parte


def pago_entre(apuracao: pd.DataFrame, inicio, fim) -> float:
    """Imposto pago, em R$, com data de pagamento entre `inicio` e `fim`, inclusive."""
    if not len(apuracao):
        return 0.0
    pagos = apuracao.dropna(subset=["data_pagamento"])
    datas = pd.to_datetime(pagos["data_pagamento"])
    return float(pagos.loc[(datas >= inicio) & (datas <= fim), "imposto"].sum())
