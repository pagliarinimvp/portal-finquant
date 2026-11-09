"""Formulário do passo 1 (Perguntar). As opções vêm dos catálogos de `quant/config.py`, como no app Streamlit.

O formulário é enviado por GET: as escolhas ficam no link, que pode ser guardado ou compartilhado.
"""
from django import forms

from .apresentacao import textos as tx
from .quant import config as c
from .quant.universo import IBOVESPA

PADROES = {"tickers": ["PETR4"], "selecao": "manual", "divisao": "igual", "medias": "intermediario", "protecao": "2_1",
           "custo": "tarifas_b3", "capital": 100_000.0}
CAPITAL_MIN, CAPITAL_MAX = 1_000.0, 1_000_000_000.0
MEDIAS_CAT = {**c.MEDIAS, c.MEDIAS_PELO_TREINO: {"rotulo": c.ROTULO_PELO_TREINO, "descricao": c.DESCRICAO_PELO_TREINO}}


def capital_em_texto(valor: float) -> str:
    """100000.0 -> "100.000": o campo mostra o ponto de milhar, como se escreve no Brasil."""
    return f"{valor:,.0f}".replace(",", ".")


def ler_capital(texto: str) -> float | None:
    """Aceita "100.000", "100000", "R$ 100.000" ou "100.000,50". Fora do intervalo ou ilegível: None."""
    limpo = texto.replace("R$", "").replace(" ", "").replace(" ", "").replace(".", "").replace(",", ".")
    try:
        valor = float(limpo)
    except ValueError:
        return None
    return valor if CAPITAL_MIN <= valor <= CAPITAL_MAX else None


def _opcoes(catalogo: dict) -> list[tuple[str, str]]:
    return [(k, v["rotulo"]) for k, v in catalogo.items()]


class AnaliseForm(forms.Form):
    selecao = forms.ChoiceField(label=tx.ESCOLHA_ACOES[0], help_text=tx.ESCOLHA_ACOES[1], choices=_opcoes(c.SELECOES),
                                widget=forms.RadioSelect)
    tickers = forms.MultipleChoiceField(label="Ações", required=False, choices=[(t, t) for t in sorted(IBOVESPA)])
    medias = forms.ChoiceField(label=tx.ESCOLHA_RITMO[0], help_text=tx.ESCOLHA_RITMO[1], choices=_opcoes(MEDIAS_CAT))
    protecao = forms.ChoiceField(label=tx.ESCOLHA_PROTECAO[0], help_text=tx.ESCOLHA_PROTECAO[1], choices=_opcoes(c.PROTECOES))
    custo = forms.ChoiceField(label=tx.ESCOLHA_CUSTO[0], help_text=tx.ESCOLHA_CUSTO[1], choices=_opcoes(c.CUSTOS))
    capital = forms.CharField(label=tx.ESCOLHA_CAPITAL, max_length=30,
                              widget=forms.TextInput(attrs={"placeholder": "Ex.: 100.000", "inputmode": "decimal"}))
    divisao = forms.ChoiceField(label=tx.ESCOLHA_DIVISAO, choices=_opcoes(c.DIVISOES), required=False)

    def __init__(self, *args, **kwargs):
        kwargs.setdefault("initial", {**PADROES, "capital": capital_em_texto(PADROES["capital"])})
        super().__init__(*args, **kwargs)
        for nome in ("medias", "protecao", "custo", "divisao", "tickers"):
            self.fields[nome].widget.attrs["class"] = "form-select"
        self.fields["capital"].widget.attrs["class"] = "form-control"
        self.fields["tickers"].widget.attrs["data-max"] = str(c.MAX_ACOES)
        for nome in ("medias", "protecao", "custo"):
            self.fields[nome].widget.attrs["aria-describedby"] = f"ajuda-{nome}"

    def valor(self, nome: str):
        """O valor que o campo mostra: o enviado ou, sem envio, o padrão."""
        return self[nome].value() if self.is_bound else self.initial.get(nome)

    def clean_capital(self):
        valor = ler_capital(self.cleaned_data["capital"])
        if valor is None:
            raise forms.ValidationError(f"Digite um valor entre R$ {capital_em_texto(CAPITAL_MIN)} e R$ {capital_em_texto(CAPITAL_MAX)}, como 100.000.")
        return valor

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
                "custo": d["custo"], "capital": d["capital"]}


def parametros(cfg: dict) -> list[tuple[str, str]]:
    """O caminho de volta: a configuração como parâmetros do link (para "Mudar escolhas", o PDF e a navegação)."""
    pares = [("selecao", cfg["selecao"])] + [("tickers", t) for t in cfg["tickers"]]
    pares += [(k, cfg[k]) for k in ("divisao", "medias", "protecao", "custo")]
    return pares + [("capital", capital_em_texto(cfg["capital"]))]


def descricoes() -> dict:
    """As descrições que aparecem abaixo de cada lista, para o estudo_caso.js trocar quando a opção muda."""
    return {"medias": {k: v["descricao"] for k, v in MEDIAS_CAT.items()},
            "protecao": {k: v["descricao"] for k, v in c.PROTECOES.items()},
            "custo": {k: v["descricao"] for k, v in c.CUSTOS.items()},
            "divisao": {k: v["descricao"] for k, v in c.DIVISOES.items()},
            "selecao": {k: v["descricao"] for k, v in c.SELECOES.items()}}
