"""Motor de backtest candle a candle, só comprado.

Convenções:
* Sinal no fechamento de t -> execução na ABERTURA de t+1, sem olhar o futuro.
* Stop e alvo são checados na máxima e na mínima, a partir do candle de entrada.
* Gap além do stop ou do alvo: execução na abertura, pior ou melhor que o nível, porque o preço do nível
  não foi negociado.
* Stop e alvo no mesmo candle: vale o STOP, a leitura conservadora.
* Posição aberta no fim do histórico é encerrada no último fechamento (motivo `fim_dados`).
* Não abre compra no último pregão: ela seria vendida no mesmo fechamento e só pagaria tarifa.
* Custo percentual em cada compra e em cada venda.
* Quantidade em lotes inteiros (escolha técnica: lote-padrão da B3), arredondada para baixo.
"""
from dataclasses import dataclass

import numpy as np
import pandas as pd

from .config import LOTE

COLUNAS_TRADES = ["data_entrada", "preco_entrada", "data_saida", "preco_saida", "quantidade",
                  "motivo", "pnl", "retorno_pct", "barras"]


@dataclass
class ResultadoBacktest:
    equity: pd.Series                      # patrimônio ao fechamento
    posicao: pd.Series                     # 1 comprado, 0 fora
    trades: pd.DataFrame
    capital_inicial: float


class Conta:
    """A regra em uma ação, pregão a pregão. `passo(i)` roda o pregão i; entre dois passos, quem coordena pode tirar ou pôr
    dinheiro no `caixa` (o imposto guardado e devolvido). `caixa` é o patrimônio realizado, sem a posição aberta."""

    def __init__(self, df: pd.DataFrame, sinais: pd.DataFrame, capital: float, stop_pct: float | None = None,
                 alvo_pct: float | None = None, custo_pct: float = 0.0, lote: int = LOTE):
        if not df.index.equals(sinais.index):
            raise ValueError("`sinais` deve ter o mesmo índice de `df`.")
        self.n, self.datas = len(df), df.index
        self.o, self.h, self.l, self.c = (df[k].to_numpy(float) for k in ("Open", "High", "Low", "Close"))
        self.entra, self.sai = sinais["entrada"].to_numpy(bool), sinais["saida"].to_numpy(bool)
        self.stop_pct, self.alvo_pct, self.custo, self.lote = stop_pct, alvo_pct, custo_pct / 100.0, lote
        self.capital = self.caixa = float(capital)
        self.equity, self.posicao = np.empty(self.n), np.zeros(self.n)
        self.trades: list[tuple] = []
        self.comprado, self.qtd, self.preco_ent, self.stop, self.alvo, self.custo_ent, self.i_ent = False, 0, np.nan, np.nan, np.nan, 0.0, 0
        self.pend_entrada = self.pend_saida = False

    def livre(self, i: int) -> float:
        """O dinheiro parado, sem o valor das ações compradas."""
        return self.caixa - (self.qtd * self.preco_ent if self.comprado else 0.0)    # a tarifa da compra já saiu do caixa

    def _fechar(self, i, preco, motivo):
        bruto = self.qtd * (preco - self.preco_ent)
        custo_sai = self.custo * self.qtd * preco
        pnl = bruto - self.custo_ent - custo_sai
        self.caixa += bruto - custo_sai
        self.trades.append((self.datas[self.i_ent], self.preco_ent, self.datas[i], preco, self.qtd, motivo, pnl,
                            100.0 * pnl / (self.qtd * self.preco_ent), i - self.i_ent + 1))
        self.comprado, self.qtd = False, 0

    def passo(self, i: int):
        o, h, l, c = self.o, self.h, self.l, self.c
        # 1) ordens do fechamento anterior executam na abertura
        if self.pend_saida and self.comprado:
            self._fechar(i, o[i], "sinal")
        self.pend_saida = False
        # no último pregão, a compra seria vendida no mesmo fechamento (fim da janela ou dos dados): só pagaria tarifa
        if self.pend_entrada and not self.comprado and i < self.n - 1:
            q = int(np.floor(self.caixa / (o[i] * (1.0 + self.custo)) / self.lote)) * self.lote
            if q >= self.lote:
                self.comprado, self.qtd, self.preco_ent, self.i_ent = True, q, o[i], i
                self.custo_ent = self.custo * q * o[i]
                self.caixa -= self.custo_ent
                self.stop = o[i] * (1.0 - self.stop_pct / 100.0) if self.stop_pct is not None else np.nan
                self.alvo = o[i] * (1.0 + self.alvo_pct / 100.0) if self.alvo_pct is not None else np.nan
        self.pend_entrada = False

        # 2) stop e alvo dentro do candle (inclui o candle de entrada)
        if self.comprado:
            if o[i] <= self.stop:
                self._fechar(i, o[i], "stop")
            elif o[i] >= self.alvo:
                self._fechar(i, o[i], "alvo")
            elif l[i] <= self.stop:
                self._fechar(i, self.stop, "stop")
            elif h[i] >= self.alvo:
                self._fechar(i, self.alvo, "alvo")

        # 3) fim dos dados: encerra a posição aberta no fechamento
        if i == self.n - 1 and self.comprado:
            self._fechar(i, c[i], "fim_dados")

        # 5) sinais do fechamento de i viram ordens para a abertura de i+1
        if i < self.n - 1:
            if self.comprado:
                self.pend_saida = bool(self.sai[i])
            else:
                self.pend_entrada = bool(self.entra[i])

    def marcar(self, i: int):
        """4) marcação a mercado, depois de qualquer ajuste no caixa do pregão."""
        self.equity[i] = self.caixa + (self.qtd * (self.c[i] - self.preco_ent) if self.comprado else 0.0)
        self.posicao[i] = 1.0 if self.comprado else 0.0

    def resultado(self) -> "ResultadoBacktest":
        return ResultadoBacktest(
            equity=pd.Series(self.equity, index=self.datas, name="equity"),
            posicao=pd.Series(self.posicao, index=self.datas, name="posicao"),
            trades=pd.DataFrame(self.trades, columns=COLUNAS_TRADES),
            capital_inicial=self.capital,
        )


def executar_backtest(df: pd.DataFrame, sinais: pd.DataFrame, capital: float, stop_pct: float | None = None,
                      alvo_pct: float | None = None, custo_pct: float = 0.0, lote: int = LOTE) -> ResultadoBacktest:
    """Roda a regra (`sinais` com colunas booleanas `entrada` e `saida`, alinhadas a `df`)."""
    conta = Conta(df, sinais, capital, stop_pct, alvo_pct, custo_pct, lote)
    for i in range(conta.n):
        conta.passo(i)
        conta.marcar(i)
    return conta.resultado()
