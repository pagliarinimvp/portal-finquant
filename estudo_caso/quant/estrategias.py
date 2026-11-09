"""A regra de compra e venda: cruzamento de médias móveis simples.

Sinais causais: o valor em t só usa preços até t. A execução na barra seguinte fica no motor de backtest.
"""
import pandas as pd


def medias(df: pd.DataFrame, curta: int, longa: int) -> tuple[pd.Series, pd.Series]:
    """Média curta e média longa do fechamento."""
    c = df["Close"]
    return c.rolling(int(curta)).mean(), c.rolling(int(longa)).mean()


def gerar_sinais(df: pd.DataFrame, curta: int, longa: int) -> pd.DataFrame:
    """Entrada quando a média curta cruza acima da longa; saída no cruzamento oposto."""
    if curta >= longa:
        raise ValueError("A média curta deve ter período menor que a longa.")
    mc, ml = medias(df, curta, longa)
    entrada = (mc > ml) & (mc.shift(1) <= ml.shift(1))
    saida = (mc < ml) & (mc.shift(1) >= ml.shift(1))
    return pd.DataFrame({"entrada": entrada, "saida": saida}).fillna(False).astype(bool)
