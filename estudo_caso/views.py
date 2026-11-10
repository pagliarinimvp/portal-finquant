"""Páginas da análise de ações (o app Streamlit da pasta Script Analise Quantitativa, levado para o portal).

Diferente dos simuladores (FormView + POST), aqui tudo vai por GET: as escolhas e a tela atual (`?tela=N`) ficam no
link, que pode ser guardado ou compartilhado, e cada tela é uma página normal. A análise roda em segundo plano
(`execucao.py`); enquanto ela não termina, a página mostra "Calculando…".
"""
from datetime import date
from urllib.parse import urlencode

from django.http import Http404, HttpResponse, JsonResponse
from django.shortcuts import redirect, render
from django.urls import reverse
from django.views import View

from . import execucao, telas
from .apresentacao import textos as tx
from .forms import AnaliseForm, descricoes, parametros
from .quant import config as c
from .quant import servico


def _versao_plotly() -> str:
    from plotly.offline import get_plotlyjs_version     # a mesma versão do plotly.js que a biblioteca Python gera
    return get_plotlyjs_version()


def _urls(cfg: dict | None) -> dict:
    """Os links que as telas e os templates usam, todos levando as escolhas junto."""
    if cfg is None:
        return {"mudar": reverse("estudo_caso:index"), "pdf": "", "analise": ""}
    qs = urlencode(parametros(cfg))
    return {"mudar": f"{reverse('estudo_caso:index')}?{qs}", "pdf": f"{reverse('estudo_caso:pdf')}?{qs}",
            "analise": f"{reverse('estudo_caso:analise')}?{qs}", "qs": qs}


def _perguntar(request, form, erro: str | None = None, cfg: dict | None = None):
    todas = descricoes()
    atual = {campo: todas[campo].get(form.valor(campo) or "", "") for campo in ("medias", "protecao", "divisao")}
    # "Voltar ao resultado" só aparece se a análise destas escolhas já foi feita, como no app Streamlit.
    voltar = _urls(cfg)["analise"] if cfg and execucao.resultado(execucao.chave(cfg)) is not None else None
    contexto = {"form": form, "abertura": telas.abertura(_urls(None)), "descricoes": todas, "descricao_atual": atual,
                "descricao_automatica": c.SELECOES["automatica"]["descricao"], "erro": erro, "tx": tx, "voltar": voltar}
    return render(request, "estudo_caso/perguntar.html", contexto)


class PerguntarView(View):
    """Passo 1. Sem parâmetros, o formulário com os padrões; com parâmetros ("Mudar escolhas"), preenchido."""

    def get(self, request):
        if not request.GET:
            return _perguntar(request, AnaliseForm())
        form = AnaliseForm(request.GET)
        return _perguntar(request, form, cfg=form.para_config() if form.is_valid() else None)


# Combinações de escolhas cujo aviso a pessoa já confirmou ("Entendi"), guardadas na sessão do navegador.
SESSAO_CIENTE = "estudo_caso_ciente"
MAX_CIENTE = 50


def _ja_ciente(request, k: str) -> bool:
    return k in request.session.get(SESSAO_CIENTE, [])


def _marcar_ciente(request, k: str) -> None:
    lista = [x for x in request.session.get(SESSAO_CIENTE, []) if x != k]
    request.session[SESSAO_CIENTE] = (lista + [k])[-MAX_CIENTE:]


class AvisoView(View):
    """Depois do passo 1: o aviso de que a ferramenta é educativa. A análise já começa a calcular por trás."""

    def get(self, request):
        form = AnaliseForm(request.GET)
        if not form.is_valid():
            return _perguntar(request, form)
        cfg = form.para_config()
        k = execucao.chave(cfg)
        calculando = execucao.resultado(k) is None
        if calculando:
            est = execucao.estado(k)
            if est["situacao"] == "erro":
                return _perguntar(request, form, erro=est["erro"])
            execucao.iniciar(cfg, k)
        urls = _urls(cfg)
        return render(request, "estudo_caso/aviso.html", {
            "tx": tx, "urls": urls, "calculando": calculando, "entendi": f"{urls['analise']}&ciente=1",
        })


class AnaliseView(View):
    """Passos 2 a 6: mostra a tela pedida se o resultado já existe; senão, põe a análise na fila e mostra a espera."""

    def get(self, request):
        form = AnaliseForm(request.GET)
        if not form.is_valid():
            return _perguntar(request, form)
        cfg = form.para_config()
        k = execucao.chave(cfg)
        # O aviso vem antes de tudo, inclusive de um link compartilhado. "ciente=1" vem do botão "Entendi" e sai do
        # link logo em seguida, para não ir junto quando a pessoa compartilhar.
        if request.GET.get("ciente") == "1":
            _marcar_ciente(request, k)
            return redirect(_urls(cfg)["analise"])
        if not _ja_ciente(request, k):
            return redirect(f"{reverse('estudo_caso:aviso')}?{_urls(cfg)['qs']}")
        res = execucao.resultado(k)
        if res is None:
            est = execucao.estado(k)
            if est["situacao"] == "erro":
                return _perguntar(request, form, erro=est["erro"])
            execucao.iniciar(cfg, k)
            return render(request, "estudo_caso/calculando.html", {
                "chave": k, "tempo": execucao.tempo_previsto(cfg), "estado": execucao.estado(k), "tx": tx,
                "etapas": list(servico.ETAPAS.items()),
                "automatica": cfg["selecao"] == "automatica", "urls": _urls(cfg),
            })
        try:
            tela = int(request.GET.get("tela", 0))
        except ValueError:
            tela = 0
        urls = _urls(cfg)
        p = telas.pagina(res, tela, urls)
        base = urls["analise"]
        return render(request, "estudo_caso/analise.html", {
            "p": p, "urls": urls, "tx": tx, "parametros": parametros(cfg), "versao_plotly": _versao_plotly(),
            "anterior": f"{base}&tela={p['atual'] - 1}" if p["atual"] > 0 else None,
            "proxima": f"{base}&tela={p['atual'] + 1}" if p["atual"] < p["n_telas"] - 1 else None,
        })


class StatusView(View):
    """Andamento da análise, para a página "Calculando…" (consultada a cada 3 s)."""

    def get(self, request, chave: str):
        if execucao.resultado(chave) is not None:
            return JsonResponse({"situacao": "pronto"})
        return JsonResponse(execucao.estado(chave))


class PdfView(View):
    """O resumo executivo em PDF, a partir do resultado guardado (o mesmo `gerar_pdf` do app Streamlit)."""

    def get(self, request):
        form = AnaliseForm(request.GET)
        if not form.is_valid():
            raise Http404("Escolhas inválidas.")
        res = execucao.resultado(execucao.chave(form.para_config()))
        if res is None:
            raise Http404("Rode a análise antes de baixar o resumo.")
        from .apresentacao.pdf import gerar_pdf     # reportlab só carrega quando alguém pede o PDF
        nome = f"resumo_{'-'.join(res['tickers'][:3])}_{date.today():%d-%m-%Y}.pdf"
        resposta = HttpResponse(gerar_pdf(res), content_type="application/pdf")
        resposta["Content-Disposition"] = f'attachment; filename="{nome}"'
        return resposta
