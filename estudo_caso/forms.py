"""Formulário do passo 1 (Perguntar). As opções vêm dos catálogos de `quant/config.py`, como no app Streamlit.

O formulário é enviado por GET: as escolhas ficam no link, que pode ser guardado ou compartilhado.
Desde 09/11/2026, o custo e o capital são fixos (tarifas da B3 com imposto e R$ 100.000), por decisão do autor: um
cenário real e um valor que não deixa faltar dinheiro para comprar. O núcleo continua aceitando os dois (o teste de
sensibilidade ao custo usa "sem_custo" por dentro); o formulário só não oferece mais a escolha.
"""
from django import forms

from .apresentacao import textos as tx
from .quant import config as c
from .quant.universo import IBOVESPA

CUSTO_FIXO, CAPITAL_FIXO = "tarifas_b3", 100_000.0
PADROES = {"tickers": ["PETR4"], "selecao": "manual", "divisao": "igual", "medias": "intermediario", "protecao": "2_1",
           "custo": CUSTO_FIXO, "capital": CAPITAL_FIXO}
MEDIAS_CAT = {**c.MEDIAS, c.MEDIAS_PELO_TREINO: {"rotulo": c.ROTULO_PELO_TREINO, "descricao": c.DESCRICAO_PELO_TREINO}}


def _opcoes(catalogo: dict) -> list[tuple[str, str]]:
    return [(k, v["rotulo"]) for k, v in catalogo.items()]


class AnaliseForm(forms.Form):
    selecao = forms.ChoiceField(label=tx.ESCOLHA_ACOES[0], help_text=tx.ESCOLHA_ACOES[1], choices=_opcoes(c.SELECOES),
                                widget=forms.RadioSelect)
    tickers = forms.MultipleChoiceField(label="Ações", required=False, choices=[(t, t) for t in sorted(IBOVESPA)])
    medias = forms.ChoiceField(label=tx.ESCOLHA_RITMO[0], help_text=tx.ESCOLHA_RITMO[1], choices=_opcoes(MEDIAS_CAT))
    protecao = forms.ChoiceField(label=tx.ESCOLHA_PROTECAO[0], help_text=tx.ESCOLHA_PROTECAO[1], choices=_opcoes(c.PROTECOES))
    divisao = forms.ChoiceField(label=tx.ESCOLHA_DIVISAO, choices=_opcoes(c.DIVISOES), required=False)

    def __init__(self, *args, **kwargs):
        kwargs.setdefault("initial", PADROES)
        super().__init__(*args, **kwargs)
        for nome in ("medias", "protecao", "divisao", "tickers"):
            self.fields[nome].widget.attrs["class"] = "form-select"
        self.fields["tickers"].widget.attrs["data-max"] = str(c.MAX_ACOES)
        for nome in ("medias", "protecao"):
            self.fields[nome].widget.attrs["aria-describedby"] = f"ajuda-{nome}"

    def valor(self, nome: str):
        """O valor que o campo mostra: o enviado ou, sem envio, o padrão."""
        return self[nome].value() if self.is_bound else self.initial.get(nome)

    def clean_tickers(self):
        tickers = self.cleaned_data["tickers"]
        if len(tickers) > c.MAX_ACOES:
            raise forms.ValidationError(f"Escolha no máximo {c.MAX_ACOES} ações.")
        return tickers

    def clean(self):
        dados = super().clean()
        if dados.get("selecao") == "manual" and not dados.get("tickers") and not self.has_error("tickers"):
            self.add_error("tickers", "Escolha ao menos uma ação para rodar a análise.")
        return dados

    def para_config(self) -> dict:
        """As escolhas no formato do núcleo, como o `config_atual` do app Streamlit (a divisão só vale com 2 ou mais ações)."""
        d = self.cleaned_data
        automatica = d["selecao"] == "automatica"
        tickers = [] if automatica else list(d["tickers"])
        divisao = (d.get("divisao") or "igual") if automatica or len(tickers) >= 2 else "igual"
        return {"tickers": tickers, "selecao": d["selecao"], "divisao": divisao, "medias": d["medias"], "protecao": d["protecao"],
                "custo": CUSTO_FIXO, "capital": CAPITAL_FIXO}


def parametros(cfg: dict) -> list[tuple[str, str]]:
    """O caminho de volta: a configuração como parâmetros do link (para "Mudar escolhas", o PDF e a navegação)."""
    pares = [("selecao", cfg["selecao"])] + [("tickers", t) for t in cfg["tickers"]]
    return pares + [(k, cfg[k]) for k in ("divisao", "medias", "protecao")]


def descricoes() -> dict:
    """As descrições que aparecem abaixo de cada lista, para o estudo_caso.js trocar quando a opção muda."""
    return {"medias": {k: v["descricao"] for k, v in MEDIAS_CAT.items()},
            "protecao": {k: v["descricao"] for k, v in c.PROTECOES.items()},
            "divisao": {k: v["descricao"] for k, v in c.DIVISOES.items()},
            "selecao": {k: v["descricao"] for k, v in c.SELECOES.items()}}
