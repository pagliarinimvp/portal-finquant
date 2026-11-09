"""Testes da camada Django da análise de ações: formulário, páginas, espera e PDF.

Os testes do núcleo (cálculos) ficam em `quant_tests/` e rodam com `pytest estudo_caso/quant_tests`. Aqui, os dados são
os mesmos sintéticos de lá (`gravar_cache` do `quant_tests/conftest.py`, que precisa do `pytest` do requirements-dev.txt).
"""
import importlib.util
import re
import shutil
import tempfile
import time
from pathlib import Path
from unittest import mock

from django.test import SimpleTestCase, override_settings

from . import execucao, telas
from .forms import PADROES, AnaliseForm

_spec = importlib.util.spec_from_file_location("conftest_quant", Path(__file__).parent / "quant_tests" / "conftest.py")
conftest = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(conftest)

CACHE_TESTE = {"default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"},
               "analises": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache", "LOCATION": "analises-teste"}}
UMA = "selecao=manual&tickers=PETR4&divisao=igual&medias=intermediario&protecao=2_1"
DUAS = "selecao=manual&tickers=PETR4&tickers=VALE3&divisao=min_variancia&medias=treino&protecao=sem"
AUTO = "selecao=automatica&divisao=igual&medias=intermediario&protecao=2_1"


class FormularioTests(SimpleTestCase):
    def dados(self, **extra):
        base = {"selecao": "manual", "tickers": ["PETR4"], "divisao": "max_sharpe", "medias": "intermediario",
                "protecao": "2_1"}
        return {**base, **extra}

    def test_custo_e_capital_sao_fixos(self):
        # Mesmo num link antigo, com outro custo e outro capital, a análise usa sempre os valores fixos.
        form = AnaliseForm(self.dados(custo="sem_custo", capital="50.000"))
        self.assertTrue(form.is_valid(), form.errors)
        cfg = form.para_config()
        self.assertEqual((cfg["custo"], cfg["capital"]), ("tarifas_b3", 100_000.0))
        self.assertNotIn("custo", form.fields)
        self.assertNotIn("capital", form.fields)

    def test_divisao_so_vale_com_duas_ou_mais_acoes(self):
        form = AnaliseForm(self.dados())
        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.para_config()["divisao"], "igual")
        form = AnaliseForm(self.dados(tickers=["PETR4", "VALE3"]))
        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.para_config()["divisao"], "max_sharpe")

    def test_limites_de_acoes(self):
        self.assertIn("tickers", AnaliseForm(self.dados(tickers=[])).errors)
        onze = ["PETR4", "VALE3", "ITUB4", "BBDC4", "ABEV3", "WEGE3", "RENT3", "SUZB3", "GGBR4", "LREN3", "B3SA3"]
        self.assertIn("tickers", AnaliseForm(self.dados(tickers=onze)).errors)

    def test_selecao_automatica_ignora_as_acoes(self):
        form = AnaliseForm(self.dados(selecao="automatica", tickers=[]))
        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.para_config()["tickers"], [])


class MarkdownTests(SimpleTestCase):
    def test_link_com_parenteses_negrito_e_italico(self):
        html = telas._md("**Nome.** Texto.  \n*Fonte: [Tashman](https://doi.org/10.1016/S0169-2070(00)00065-0).*")
        self.assertIn('<a href="https://doi.org/10.1016/S0169-2070(00)00065-0"', html)
        self.assertIn("<b>Nome.</b>", html)
        self.assertIn("<br><i>Fonte:", html)

    def test_escapa_html(self):
        self.assertIn("p &lt; 0,05", telas._md("p < 0,05"))


@override_settings(CACHES=CACHE_TESTE)
class PaginasTests(SimpleTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.pasta = Path(tempfile.mkdtemp())
        conftest.gravar_cache(cls.pasta)
        cls.dados = override_settings(DADOS_ESTUDO=cls.pasta)
        cls.dados.enable()

    @classmethod
    def tearDownClass(cls):
        cls.dados.disable()
        shutil.rmtree(cls.pasta, ignore_errors=True)
        super().tearDownClass()

    def config(self, qs: str) -> dict:
        from django.http import QueryDict
        form = AnaliseForm(QueryDict(qs))
        self.assertTrue(form.is_valid(), form.errors)
        return form.para_config()

    def calcular(self, qs: str):
        execucao.rodar_agora(self.config(qs))

    def todas_as_telas(self, qs: str) -> list[str]:
        r = self.client.get(f"/estudo-caso/analise/?{qs}")
        self.assertEqual(r.status_code, 200)
        n = len(re.findall(r'<option value="\d+"', r.content.decode()))
        self.assertGreaterEqual(n, 13)
        titulos, self.paginas = [], []
        for i in range(n):
            html = self.client.get(f"/estudo-caso/analise/?{qs}&tela={i}").content.decode()
            titulos.append(re.search(r'<h2 class="tela">(.*?)</h2>', html).group(1))
            self.paginas.append(html)
        return titulos

    def test_passo_1(self):
        r = self.client.get("/estudo-caso/")
        self.assertContains(r, "Esta regra de compra e venda teria dado certo?")
        # Custo e capital são explicados dentro da análise, não no formulário.
        self.assertNotContains(r, "Dinheiro inicial: R$ 100.000")
        self.assertNotContains(r, "tarifa da B3")
        self.assertNotContains(r, 'name="capital"')
        self.assertNotContains(r, 'name="custo"')
        self.assertNotContains(r, "Voltar ao resultado")

    def test_todas_as_telas_com_uma_acao(self):
        self.calcular(UMA)
        titulos = self.todas_as_telas(UMA)
        self.assertEqual(titulos[0], "De onde vêm os dados?")
        self.assertEqual(titulos[-1], "O que fazer com isso?")
        self.assertNotIn("A divisão do dinheiro", titulos)
        tudo = "".join(self.paginas)
        self.assertIn("Dinheiro inicial: R$ 100.000", tudo)     # saíram do passo 1 e vivem nas abas da análise
        self.assertIn("tarifa da B3", tudo)
        self.assertGreaterEqual(tudo.count('class="um-por-vez"'), 10)     # o conteúdo das telas fica em abas

    def test_todas_as_telas_com_duas_acoes(self):
        self.calcular(DUAS)
        self.assertIn("A divisão do dinheiro", self.todas_as_telas(DUAS))

    def test_todas_as_telas_com_selecao_automatica(self):
        self.calcular(AUTO)
        self.assertIn("Como a carteira foi escolhida", self.todas_as_telas(AUTO))

    def test_pdf(self):
        self.calcular(UMA)
        r = self.client.get(f"/estudo-caso/pdf/?{UMA}")
        self.assertEqual(r["Content-Type"], "application/pdf")
        self.assertTrue(r.content.startswith(b"%PDF"))
        self.assertRegex(r["Content-Disposition"], r'filename="resumo_PETR4_\d{2}-\d{2}-\d{4}\.pdf"')

    def test_pdf_sem_resultado_da_404(self):
        r = self.client.get(f"/estudo-caso/pdf/?{UMA.replace('protecao=2_1', 'protecao=3_1')}")
        self.assertEqual(r.status_code, 404)

    def test_mudar_escolhas_volta_ao_resultado(self):
        self.calcular(UMA)
        self.assertContains(self.client.get(f"/estudo-caso/?{UMA}"), "Voltar ao resultado")

    def test_escolhas_invalidas_voltam_ao_formulario(self):
        r = self.client.get("/estudo-caso/analise/?selecao=manual&medias=intermediario&protecao=2_1")
        self.assertContains(r, "Escolha ao menos uma ação para rodar a análise.")

    def test_espera_e_status(self):
        qs = UMA.replace("protecao=2_1", "protecao=1_1")
        r = self.client.get(f"/estudo-caso/analise/?{qs}")
        self.assertContains(r, "Calculando a análise")
        k = execucao.chave(self.config(qs))
        for _ in range(120):
            if self.client.get(f"/estudo-caso/status/{k}/").json()["situacao"] == "pronto":
                break
            time.sleep(0.5)
        self.assertEqual(self.client.get(f"/estudo-caso/status/{k}/").json()["situacao"], "pronto")
        self.assertContains(self.client.get(f"/estudo-caso/analise/?{qs}"), "De onde vêm os dados?")


@override_settings(CACHES=CACHE_TESTE)
class PrecalculoTests(SimpleTestCase):
    """O pré-cálculo de madrugada: a lista, a janela de horário e o ceder a vez a quem pede uma análise."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.pasta = Path(tempfile.mkdtemp())
        conftest.gravar_cache(cls.pasta)
        cls.dados = override_settings(DADOS_ESTUDO=cls.pasta)
        cls.dados.enable()

    @classmethod
    def tearDownClass(cls):
        cls.dados.disable()
        shutil.rmtree(cls.pasta, ignore_errors=True)
        super().tearDownClass()

    def cfg(self):
        return {**PADROES, "tickers": [conftest.TICKERS[0]]}

    def test_lista_sem_repeticoes(self):
        from .quant import config as c
        from .quant.universo import IBOVESPA
        lista = execucao.configs_ociosas()
        automaticas = [x for x in lista if x["selecao"] == "automatica"]
        self.assertEqual(len(automaticas), (len(c.MEDIAS) + 1) * len(c.PROTECOES) * len(c.DIVISOES))
        self.assertEqual(len(lista) - len(automaticas), len(IBOVESPA))
        self.assertEqual(lista[0], PADROES)                         # a mais provável vem primeiro
        self.assertTrue(all(x["custo"] == "tarifas_b3" and x["capital"] == 100_000.0 for x in lista))

    @override_settings(ESTUDO_JANELA="2-5")
    def test_janela_de_madrugada(self):
        from datetime import datetime
        b = execucao.BRASILIA
        self.assertFalse(execucao.na_janela(datetime(2026, 11, 14, 1, 59, tzinfo=b)))
        self.assertTrue(execucao.na_janela(datetime(2026, 11, 14, 2, 0, tzinfo=b)))
        self.assertTrue(execucao.na_janela(datetime(2026, 11, 14, 4, 59, tzinfo=b)))
        self.assertFalse(execucao.na_janela(datetime(2026, 11, 14, 5, 0, tzinfo=b)))

    def test_calcula_e_guarda_quando_livre(self):
        cfg = self.cfg()
        k = execucao.chave(cfg)
        self.assertTrue(execucao.rodar_ocioso(cfg, k))
        self.assertIsNotNone(execucao.resultado(k))

    def test_cede_a_vez_no_meio_e_libera_o_servidor(self):
        cfg = {**self.cfg(), "protecao": "3_1"}
        k = execucao.chave(cfg)
        # livre ao começar; alguém entra na fila logo depois, e o cálculo para na troca de etapa
        with mock.patch.object(execucao, "_alguem_esperando", side_effect=[False] + [True] * 20):
            self.assertFalse(execucao.rodar_ocioso(cfg, k))
        self.assertIsNone(execucao.resultado(k))
        self.assertTrue(execucao._TRAVA.acquire(blocking=False))    # a trava foi devolvida
        execucao._TRAVA.release()

    def test_nao_comeca_com_alguem_na_fila(self):
        cfg = {**self.cfg(), "protecao": "1_1"}
        with mock.patch.object(execucao, "_alguem_esperando", return_value=True):
            self.assertFalse(execucao.rodar_ocioso(cfg, execucao.chave(cfg)))

    def test_janela_configuravel_para_teste(self):
        from datetime import datetime
        b = execucao.BRASILIA
        with self.settings(ESTUDO_JANELA="17-19"):
            self.assertTrue(execucao.na_janela(datetime(2026, 11, 9, 17, 30, tzinfo=b)))
            self.assertFalse(execucao.na_janela(datetime(2026, 11, 9, 3, 0, tzinfo=b)))
        for desligado in ("", "abc"):
            with self.settings(ESTUDO_JANELA=desligado):
                self.assertIsNone(execucao.janela())
                self.assertFalse(execucao.na_janela())

    def test_vigia_aponta_requisicao_presa(self):
        from . import vigia
        vigia._EM_CURSO[-1] = (100.0, "/presa/")
        try:
            self.assertEqual(vigia.presas(agora=100.0 + vigia.LIMITE + 1), [(vigia.LIMITE + 1, "/presa/")])
            self.assertEqual(vigia.presas(agora=100.0 + vigia.LIMITE - 1), [])
        finally:
            vigia._EM_CURSO.pop(-1, None)
