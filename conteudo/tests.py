import importlib
import importlib.util
import json
import tempfile
from datetime import timedelta
from io import StringIO
from pathlib import Path

from PIL import Image

from django.apps import apps as django_apps
from django.conf import settings
from django.contrib import admin
from django.contrib.auth.models import User
from django.core.management import CommandError, call_command
from django.db.migrations.loader import MigrationLoader
from django.test import TestCase, override_settings
from django.test.client import RequestFactory
from django.urls import reverse

from .models import Artigo
from .templatetags.conteudo_extras import capa_url, corpo_seguro, tempo_leitura


def criar_artigo(slug, status=Artigo.Status.PUBLICADO, **campos):
    return Artigo.objects.create(
        titulo=campos.get('titulo', slug), slug=slug, resumo='Resumo.',
        corpo=campos.get('corpo', '<p>Corpo.</p>'), status=status,
        categoria=campos.get('categoria', Artigo.Categoria.FUNDAMENTOS),
    )


class ArtigoVisibilidadeTests(TestCase):
    def setUp(self):
        self.publicado = criar_artigo('publicado')
        self.rascunho = criar_artigo('rascunho', status=Artigo.Status.RASCUNHO)

    def test_lista_mostra_so_publicados(self):
        response = self.client.get(reverse('conteudo:lista'))

        # A migração 0002 cria artigos de exemplo, então não dá para comparar a lista inteira.
        artigos = list(response.context['artigos'])
        self.assertIn(self.publicado, artigos)
        self.assertNotIn(self.rascunho, artigos)

    def test_rascunho_e_404_para_visitante(self):
        response = self.client.get(self.rascunho.get_absolute_url())
        self.assertEqual(response.status_code, 404)

    def test_rascunho_e_404_para_usuario_comum(self):
        self.client.force_login(User.objects.create_user(username='ana', password='x'))

        response = self.client.get(self.rascunho.get_absolute_url())

        self.assertEqual(response.status_code, 404)

    def test_equipe_ve_rascunho_com_aviso(self):
        self.client.force_login(User.objects.create_user(username='equipe', password='x', is_staff=True))

        response = self.client.get(self.rascunho.get_absolute_url())

        self.assertContains(response, 'Rascunho — não publicado')


class CorpoSeguroTests(TestCase):
    def test_remove_script(self):
        limpo = corpo_seguro('<p>Oi</p><script>alert(1)</script>')

        self.assertNotIn('<script', limpo)
        self.assertIn('<p>Oi</p>', limpo)

    def test_remove_atributos_de_evento(self):
        limpo = corpo_seguro('<img src="https://exemplo.com/a.png" onerror="alert(1)">')

        self.assertNotIn('onerror', limpo)
        self.assertIn('src="https://exemplo.com/a.png"', limpo)

    def test_bloqueia_link_javascript(self):
        limpo = corpo_seguro('<a href="javascript:alert(1)">clique</a>')

        self.assertNotIn('javascript:', limpo)

    def test_links_abrem_em_nova_aba_sem_repassar_a_origem(self):
        limpo = corpo_seguro('<a href="https://exemplo.com">fonte</a>')

        self.assertIn('target="_blank"', limpo)
        self.assertIn('noopener', limpo)

    def test_link_para_o_proprio_portal_abre_na_mesma_aba_sem_nofollow(self):
        limpo = corpo_seguro(
            '<a href="/simuladores/juros-compostos/" target="_blank" rel="nofollow">Simulador</a>')

        self.assertIn('href="/simuladores/juros-compostos/"', limpo)
        self.assertNotIn('target', limpo)
        self.assertNotIn('nofollow', limpo)

    def test_link_com_duas_barras_continua_externo(self):
        limpo = corpo_seguro('<a href="//exemplo.com/x">fonte</a>')

        self.assertIn('target="_blank"', limpo)
        self.assertIn('nofollow', limpo)


class ArtigoFiltroCategoriaTests(TestCase):
    def setUp(self):
        self.renda_fixa = criar_artigo('cdb', categoria=Artigo.Categoria.RENDA_FIXA)
        self.fundamentos = criar_artigo('orcamento', categoria=Artigo.Categoria.FUNDAMENTOS)

    def test_filtra_pela_categoria(self):
        response = self.client.get(reverse('conteudo:lista'), {'categoria': 'RENDA_FIXA'})

        artigos = list(response.context['artigos'])
        self.assertIn(self.renda_fixa, artigos)
        self.assertNotIn(self.fundamentos, artigos)
        self.assertEqual(response.context['categoria_atual'], 'RENDA_FIXA')

    def test_categoria_desconhecida_mostra_tudo(self):
        response = self.client.get(reverse('conteudo:lista'), {'categoria': 'INEXISTENTE'})

        artigos = list(response.context['artigos'])
        self.assertIn(self.renda_fixa, artigos)
        self.assertIn(self.fundamentos, artigos)
        self.assertEqual(response.context['categoria_atual'], '')


class PaginasDeErroTests(TestCase):
    def test_404_usa_a_identidade_do_site(self):
        response = self.client.get('/artigos/nao-existe/')

        self.assertEqual(response.status_code, 404)
        self.assertTemplateUsed(response, '404.html')
        self.assertContains(response, 'Página não encontrada', status_code=404)


class DataDePublicacaoTests(TestCase):
    def test_rascunho_nao_tem_data_de_publicacao(self):
        artigo = criar_artigo('rascunho', status=Artigo.Status.RASCUNHO)

        self.assertIsNone(artigo.publicado_em)

    def test_data_e_gravada_quando_o_rascunho_vira_publicado(self):
        artigo = criar_artigo('rascunho', status=Artigo.Status.RASCUNHO)

        artigo.status = Artigo.Status.PUBLICADO
        artigo.save()

        self.assertIsNotNone(artigo.publicado_em)
        self.assertGreater(artigo.publicado_em, artigo.atualizado_em - timedelta(seconds=5))

    def test_data_nao_muda_ao_editar_artigo_publicado(self):
        artigo = criar_artigo('publicado')
        data_original = artigo.publicado_em

        artigo.resumo = 'Resumo novo.'
        artigo.save()

        self.assertEqual(artigo.publicado_em, data_original)

    def test_acao_do_admin_grava_a_data(self):
        artigo = criar_artigo('rascunho', status=Artigo.Status.RASCUNHO)
        modelo_admin = admin.site._registry[Artigo]
        request = RequestFactory().post('/')
        request.user = User.objects.create_superuser(username='adm', password='x')
        modelo_admin.message_user = lambda *args, **kwargs: None

        modelo_admin.marcar_como_publicado(request, Artigo.objects.filter(pk=artigo.pk))

        artigo.refresh_from_db()
        self.assertEqual(artigo.status, Artigo.Status.PUBLICADO)
        self.assertIsNotNone(artigo.publicado_em)


SLUG_GALIPOLO = 'galipolo-defende-juros-restritivos-para-reequilibrar-oferta-e-demanda-no-brasil'
SLUGS_DA_0002 = [
    'o-que-sao-financas-quantitativas',
    'renda-fixa-como-funciona-na-pratica',
    'renda-variavel-o-que-sao-acoes',
]


class CamposNovosTests(TestCase):
    def test_artigo_sem_capa_e_sem_ia_por_padrao(self):
        artigo = criar_artigo('sem-capa')

        self.assertEqual(artigo.capa, '')
        self.assertEqual(artigo.capa_alt, '')
        self.assertEqual(artigo.capa_credito, '')
        self.assertFalse(artigo.com_apoio_ia)

    @staticmethod
    def _rodar_0006():
        # Desde 10/11/2026 as migrações 0008-0011 põem a versão nova (feita com IA) nos
        # artigos de exemplo, então o estado final do banco já não mostra o que a 0006
        # fez. O teste roda a função da 0006 num estado controlado.
        # A 0012 apagou o artigo do Galípolo; ele é recriado para a 0006 ter o que marcar.
        modulo = importlib.import_module('conteudo.migrations.0006_artigo_capa_e_apoio_ia')
        if not Artigo.objects.filter(slug=SLUG_GALIPOLO).exists():
            criar_artigo(SLUG_GALIPOLO)
        Artigo.objects.update(com_apoio_ia=False)
        modulo.marcar_galipolo(django_apps, None)

    def test_artigo_exportado_com_ia_nao_quebra_o_teste_da_0006(self):
        # Um artigo exportado pela skill (com_apoio_ia=True) continua marcado.
        criar_artigo('exportado-pela-skill')
        self._rodar_0006()
        Artigo.objects.filter(slug='exportado-pela-skill').update(com_apoio_ia=True)
        self.assertTrue(Artigo.objects.get(slug='exportado-pela-skill').com_apoio_ia)
        self.assertFalse(Artigo.objects.filter(slug__in=SLUGS_DA_0002, com_apoio_ia=True).exists())

    def test_migracao_marca_o_artigo_do_galipolo_como_feito_com_ia(self):
        self._rodar_0006()

        self.assertTrue(Artigo.objects.get(slug=SLUG_GALIPOLO).com_apoio_ia)
        # Só o do Galípolo; os de exemplo da 0002 não foram feitos com IA.
        exemplos = Artigo.objects.filter(slug__in=SLUGS_DA_0002)
        self.assertTrue(exemplos.exists())
        self.assertFalse(exemplos.filter(com_apoio_ia=True).exists())

    def test_migracoes_0008_a_0010_poem_a_versao_nova_nos_mesmos_enderecos(self):
        for slug in SLUGS_DA_0002:
            artigo = Artigo.objects.get(slug=slug)
            self.assertEqual(artigo.revisado_em.isoformat(), '2026-11-10')
            self.assertTrue(artigo.capa.startswith('img/artigos/'))
            self.assertTrue(artigo.com_apoio_ia)

    def test_migracao_0012_apaga_o_artigo_do_galipolo(self):
        self.assertFalse(Artigo.objects.filter(slug=SLUG_GALIPOLO).exists())

    def test_migracao_0012_apaga_tambem_as_avaliacoes_do_artigo(self):
        from avaliacoes.models import AvaliacaoArtigo
        modulo = importlib.import_module('conteudo.migrations.0012_remove_artigo_galipolo')
        artigo = criar_artigo(SLUG_GALIPOLO)
        AvaliacaoArtigo.objects.create(artigo=artigo, ajudou=True)

        modulo.remover(django_apps, None)

        self.assertFalse(Artigo.objects.filter(slug=SLUG_GALIPOLO).exists())
        self.assertFalse(AvaliacaoArtigo.objects.exists())


class QuadrosNoCorpoTests(TestCase):
    def test_aceita_quadro_com_classe_da_lista(self):
        limpo = corpo_seguro('<aside class="fq-em-30s"><p>x</p></aside>')

        self.assertIn('<aside class="fq-em-30s">', limpo)

    def test_na_pratica_e_glossario_viram_quadro_que_abre_e_fecha(self):
        limpo = corpo_seguro(
            '<aside class="fq-na-pratica"><h4>Na prática</h4><p>conta</p></aside>'
            '<aside class="fq-glossario"><h4>Glossário</h4><dl><dt>A</dt><dd>B</dd></dl></aside>'
        )

        self.assertIn('<details class="fq-quadro fq-na-pratica"><summary>Na prática</summary><p>conta</p></details>', limpo)
        self.assertIn('<details class="fq-quadro fq-glossario"><summary>Glossário</summary><dl>', limpo)
        self.assertNotIn('<aside', limpo)

    def test_quadro_sem_titulo_ganha_o_titulo_padrao(self):
        limpo = corpo_seguro('<aside class="fq-glossario"><dl><dt>A</dt><dd>B</dd></dl></aside>')

        self.assertIn('<summary>Glossário</summary><dl>', limpo)

    def test_texto_do_titulo_continua_escapado(self):
        limpo = corpo_seguro('<aside class="fq-na-pratica"><h4>A &lt;b&gt; <script>x</script></h4><p>y</p></aside>')

        self.assertNotIn('<script', limpo)
        self.assertIn('<summary>A &lt;b&gt; &lt;script&gt;x&lt;/script&gt;</summary>', limpo)

    def test_remove_classe_fora_da_lista(self):
        limpo = corpo_seguro('<aside class="btn btn-danger"><p>x</p></aside>')

        self.assertNotIn('btn', limpo)
        self.assertIn('<aside>', limpo)

    def test_classe_nao_vale_em_outras_tags(self):
        self.assertNotIn('class', corpo_seguro('<p class="fq-na-pratica">x</p>'))

    def test_aceita_glossario_em_lista_de_definicoes(self):
        limpo = corpo_seguro('<dl><dt>Copom</dt><dd>Comitê.</dd></dl>')

        self.assertIn('<dl><dt>Copom</dt><dd>Comitê.</dd></dl>', limpo)

    def test_aceita_id_simples_em_h2(self):
        self.assertIn('id="o-que-e"', corpo_seguro('<h2 id="o-que-e">O que é?</h2>'))

    def test_remove_id_com_caracteres_estranhos(self):
        self.assertNotIn('id=', corpo_seguro('<h2 id="Seção 1!">T</h2>'))

    def test_id_nao_vale_em_outras_tags(self):
        self.assertNotIn('id=', corpo_seguro('<p id="o-que-e">x</p>'))

    def test_link_do_sumario_descarta_target_e_rel_escritos_no_texto(self):
        limpo = corpo_seguro('<a href="#x" target="_blank" rel="opener">X</a>')

        self.assertNotIn('target', limpo)
        self.assertNotIn('opener', limpo)

    def test_link_do_sumario_nao_abre_em_nova_aba(self):
        limpo = corpo_seguro('<a href="#o-que-e">O que é?</a>')

        self.assertIn('href="#o-que-e"', limpo)
        self.assertNotIn('target', limpo)
        self.assertNotIn('nofollow', limpo)


class FiltrosDoArtigoTests(TestCase):
    def test_tempo_de_leitura_arredonda_para_cima(self):
        self.assertEqual(tempo_leitura('<p>' + 'palavra ' * 401 + '</p>'), 3)

    def test_tempo_de_leitura_minimo_e_um_minuto(self):
        self.assertEqual(tempo_leitura(''), 1)

    def test_tempo_de_leitura_ignora_html(self):
        self.assertEqual(tempo_leitura('<p class="x" id="y">' + 'a ' * 200 + '</p>'), 1)

    def test_capa_url_vazia(self):
        self.assertEqual(capa_url(''), '')

    def test_capa_url_existente(self):
        self.assertEqual(capa_url('img/previa.png'), '/static/img/previa.png')

    def test_capa_ausente_do_manifesto_nao_derruba_a_pagina(self):
        armazenamento = {**settings.STORAGES, 'staticfiles': {
            'BACKEND': 'django.contrib.staticfiles.storage.ManifestStaticFilesStorage',
        }}
        with override_settings(STORAGES=armazenamento):
            self.assertEqual(capa_url('img/artigos/nao-existe/capa.jpg'), '')


class PaginaDoArtigoTests(TestCase):
    def pagina(self, slug):
        return self.client.get(reverse('conteudo:detalhe', args=[slug]))

    def test_artigo_feito_com_ia_mostra_autoria_e_nota(self):
        criar_artigo('com-ia')
        Artigo.objects.filter(slug='com-ia').update(com_apoio_ia=True)

        resposta = self.pagina('com-ia')

        self.assertContains(resposta, 'Por Marcos Vinicius Pagliarini')
        self.assertContains(resposta, 'Pesquisa e redação com apoio de IA, revisado pelo autor.')

    def test_artigo_sem_ia_mostra_so_a_autoria(self):
        criar_artigo('sem-ia')

        resposta = self.pagina('sem-ia')

        self.assertContains(resposta, 'Por Marcos Vinicius Pagliarini')
        self.assertNotContains(resposta, 'apoio de IA')

    def test_mostra_atualizado_em_quando_o_conteudo_foi_revisado(self):
        criar_artigo('revisado')
        Artigo.objects.filter(slug='revisado').update(revisado_em='2026-11-10')

        self.assertContains(self.pagina('revisado'), 'Atualizado em 10/11/2026')

    def test_sem_revisao_nao_mostra_atualizado_em(self):
        criar_artigo('nunca-revisado')

        self.assertNotContains(self.pagina('nunca-revisado'), 'Atualizado em')

    def test_mostra_linha_fina(self):
        criar_artigo('fina')

        self.assertContains(self.pagina('fina'), '<p class="fq-linha-fina">Resumo.</p>', html=True)

    def test_mostra_tempo_de_leitura(self):
        criar_artigo('tempo', corpo='<p>' + 'palavra ' * 401 + '</p>')

        self.assertContains(self.pagina('tempo'), '3 min de leitura')

    def test_capa_aparece_com_credito_e_vira_previa_do_link(self):
        criar_artigo('capa')
        Artigo.objects.filter(slug='capa').update(
            capa='img/previa.png', capa_alt='Moedas', capa_credito='Foto: Fulano / Unsplash')

        resposta = self.pagina('capa')

        self.assertContains(resposta, 'alt="Moedas"')
        self.assertContains(resposta, 'Foto: Fulano / Unsplash')
        self.assertEqual(resposta.context['seo_imagem'], 'http://testserver/static/img/previa.png')
        self.assertEqual(resposta.context['seo_imagem_alt'], 'Moedas')
        self.assertContains(resposta, '<meta property="og:image:alt" content="Moedas">', html=True)

    def test_previa_do_link_identifica_o_artigo(self):
        # Título e resumo do próprio artigo, tipo "article", seção e datas (WhatsApp, LinkedIn, X).
        criar_artigo('previa', titulo='Título do artigo')

        resposta = self.pagina('previa')

        self.assertContains(resposta, '<meta property="og:title" content="Título do artigo">', html=True)
        self.assertContains(resposta, '<meta property="og:description" content="Resumo.">', html=True)
        self.assertContains(resposta, '<meta property="og:type" content="article">', html=True)
        self.assertContains(resposta, '<meta property="article:section" content="Fundamentos">', html=True)
        self.assertContains(resposta, 'property="article:published_time"')
        self.assertNotContains(resposta, 'article:modified_time')

    def test_pagina_que_nao_e_artigo_continua_website(self):
        resposta = self.client.get(reverse('conteudo:lista'))

        self.assertContains(resposta, '<meta property="og:type" content="website">', html=True)
        self.assertNotContains(resposta, 'article:section')

    def test_artigo_sem_capa_mantem_previa_padrao(self):
        criar_artigo('sem-capa')

        resposta = self.pagina('sem-capa')

        self.assertNotContains(resposta, 'fq-capa')
        self.assertTrue(resposta.context['seo_imagem'].endswith('img/previa.png'))
        self.assertIn('Portal FinQuant', resposta.context['seo_imagem_alt'])

    def test_lista_mostra_miniatura_so_com_capa(self):
        Artigo.objects.all().delete()  # os artigos das migrações de dados já têm capa
        criar_artigo('a')
        criar_artigo('b')
        Artigo.objects.filter(slug='a').update(capa='img/previa.png', capa_alt='Capa A')

        resposta = self.client.get(reverse('conteudo:lista'))

        self.assertContains(resposta, 'alt="Capa A"', count=1)
        self.assertContains(resposta, 'card-img-top', count=1)

    def test_pagina_inicial_mostra_miniatura_da_capa(self):
        criar_artigo('a')
        Artigo.objects.filter(slug='a').update(capa='img/previa.png', capa_alt='Capa A')

        self.assertContains(self.client.get('/'), 'alt="Capa A"', count=1)


class ImportarArtigoTests(TestCase):
    def setUp(self):
        pasta = tempfile.TemporaryDirectory()
        self.addCleanup(pasta.cleanup)
        self.pasta = Path(pasta.name)
        self.static = self.pasta / 'static'
        configuracao = override_settings(STATICFILES_DIRS=[str(self.static)])
        configuracao.enable()
        self.addCleanup(configuracao.disable)

    def imagem(self, caminho, tamanho=(1200, 630)):
        destino = self.static / caminho
        destino.parent.mkdir(parents=True, exist_ok=True)
        Image.new('RGB', tamanho).save(destino)

    def json(self, **campos):
        dados = {'titulo': 'Título', 'resumo': 'Resumo.', 'corpo': '<p>Corpo.</p>',
                 'categoria': 'RENDA_FIXA', **campos}
        arquivo = self.pasta / 'artigo.json'
        arquivo.write_text(json.dumps(dados), encoding='utf-8')
        return str(arquivo)

    def importar(self, **campos):
        call_command('importar_artigo', self.json(**campos), stdout=StringIO())

    def test_importa_com_capa_valida_e_nota_de_ia(self):
        self.imagem('img/artigos/t/capa.jpg')

        self.importar(capa='img/artigos/t/capa.jpg', capa_alt='Moedas',
                      capa_credito='Foto: X / Pexels', com_apoio_ia=True)

        artigo = Artigo.objects.get(titulo='Título')
        self.assertEqual(artigo.capa, 'img/artigos/t/capa.jpg')
        self.assertEqual(artigo.capa_alt, 'Moedas')
        self.assertEqual(artigo.capa_credito, 'Foto: X / Pexels')
        self.assertTrue(artigo.com_apoio_ia)
        self.assertEqual(artigo.status, Artigo.Status.RASCUNHO)

    def test_sem_capa_continua_funcionando(self):
        self.importar()

        artigo = Artigo.objects.get(titulo='Título')
        self.assertEqual(artigo.capa, '')
        self.assertFalse(artigo.com_apoio_ia)

    def test_recusa_capa_inexistente(self):
        with self.assertRaisesMessage(CommandError, '"capa"'):
            self.importar(capa='img/artigos/t/nao.jpg', capa_alt='a', capa_credito='c')
        self.assertFalse(Artigo.objects.filter(titulo='Título').exists())

    def test_recusa_capa_com_tamanho_errado(self):
        self.imagem('img/artigos/t/capa.jpg', (1600, 900))

        with self.assertRaisesMessage(CommandError, '1200x630'):
            self.importar(capa='img/artigos/t/capa.jpg', capa_alt='a', capa_credito='c')

    def test_recusa_arquivo_que_nao_e_imagem(self):
        destino = self.static / 'img/artigos/t/capa.jpg'
        destino.parent.mkdir(parents=True)
        destino.write_text('não sou imagem', encoding='utf-8')

        with self.assertRaisesMessage(CommandError, '"capa"'):
            self.importar(capa='img/artigos/t/capa.jpg', capa_alt='a', capa_credito='c')

    def test_recusa_caminho_que_sai_da_pasta_static(self):
        with self.assertRaisesMessage(CommandError, '"capa"'):
            self.importar(capa='../config/settings.py', capa_alt='a', capa_credito='c')

    def test_capa_exige_texto_alternativo(self):
        self.imagem('img/artigos/t/capa.jpg')

        with self.assertRaisesMessage(CommandError, '"capa_alt"'):
            self.importar(capa='img/artigos/t/capa.jpg', capa_credito='c')

    def test_capa_exige_credito(self):
        self.imagem('img/artigos/t/capa.jpg')

        with self.assertRaisesMessage(CommandError, '"capa_credito"'):
            self.importar(capa='img/artigos/t/capa.jpg', capa_alt='a')


CORPO_DIFICIL = '<p>Aspas "duplas", \'simples\', acentuação — barra \ e\nquebra de linha.</p>'


class ExportarArtigoMigracaoTests(TestCase):
    def setUp(self):
        pasta = tempfile.TemporaryDirectory()
        self.addCleanup(pasta.cleanup)
        self.pasta = Path(pasta.name)

    def exportar(self, slug):
        call_command('exportar_artigo_migracao', slug, pasta=str(self.pasta), stdout=StringIO())
        (arquivo,) = self.pasta.iterdir()
        return arquivo

    def carregar(self, arquivo):
        especificacao = importlib.util.spec_from_file_location('migracao_gerada', arquivo)
        modulo = importlib.util.module_from_spec(especificacao)
        especificacao.loader.exec_module(modulo)
        return modulo

    def folha_atual(self):
        grafo = MigrationLoader(None, ignore_no_migrations=True).graph
        return next(nome for app, nome in grafo.leaf_nodes() if app == 'conteudo')

    def test_nome_do_arquivo_usa_o_proximo_numero_e_o_slug(self):
        criar_artigo('selic-o-que-e')
        proximo = int(self.folha_atual()[:4]) + 1

        arquivo = self.exportar('selic-o-que-e')

        self.assertEqual(arquivo.name, f'{proximo:04d}_importa_artigo_selic_o_que_e.py')

    def test_depende_da_folha_atual(self):
        criar_artigo('selic-o-que-e')

        modulo = self.carregar(self.exportar('selic-o-que-e'))

        self.assertEqual(modulo.Migration.dependencies, [('conteudo', self.folha_atual())])

    def test_slug_longo_e_cortado_no_nome_do_arquivo(self):
        slug = 'a' * 60
        criar_artigo(slug)

        nome = self.exportar(slug).name

        self.assertEqual(nome[5:], 'importa_artigo_' + 'a' * 40 + '.py')

    def test_ida_e_volta_preserva_os_campos(self):
        criar_artigo('dificil', corpo=CORPO_DIFICIL)
        Artigo.objects.filter(slug='dificil').update(
            capa='img/x.jpg', capa_alt='Alt "x"', capa_credito='Foto: B', com_apoio_ia=True)

        artigo = self.carregar(self.exportar('dificil')).ARTIGO

        self.assertEqual(artigo['corpo'], CORPO_DIFICIL)
        self.assertEqual(artigo['capa_alt'], 'Alt "x"')
        self.assertEqual(artigo['capa'], 'img/x.jpg')
        self.assertTrue(artigo['com_apoio_ia'])

    def test_vai_sempre_como_rascunho(self):
        criar_artigo('publicado-local')

        artigo = self.carregar(self.exportar('publicado-local')).ARTIGO

        self.assertEqual(artigo['status'], 'RASCUNHO')

    def test_importar_cria_o_artigo_quando_nao_existe(self):
        criar_artigo('novo', corpo=CORPO_DIFICIL)
        modulo = self.carregar(self.exportar('novo'))
        Artigo.objects.filter(slug='novo').delete()

        modulo.importar_artigo(django_apps, None)

        artigo = Artigo.objects.get(slug='novo')
        self.assertEqual(artigo.corpo, CORPO_DIFICIL)
        self.assertEqual(artigo.status, Artigo.Status.RASCUNHO)

    def test_importar_nao_duplica_slug_existente(self):
        criar_artigo('ja-existe')
        modulo = self.carregar(self.exportar('ja-existe'))

        modulo.importar_artigo(django_apps, None)

        self.assertEqual(Artigo.objects.filter(slug='ja-existe').count(), 1)

    def test_remover_apaga_so_esse_slug(self):
        criar_artigo('fica')
        criar_artigo('sai')
        modulo = self.carregar(self.exportar('sai'))

        modulo.remover_artigo(django_apps, None)

        self.assertFalse(Artigo.objects.filter(slug='sai').exists())
        self.assertTrue(Artigo.objects.filter(slug='fica').exists())

    def test_slug_inexistente_da_erro(self):
        with self.assertRaisesMessage(CommandError, 'nao-existe'):
            call_command('exportar_artigo_migracao', 'nao-existe', pasta=str(self.pasta))


class SubstituirArtigoTests(TestCase):
    """`exportar_artigo_migracao <novo> --substituir <antigo>`: a versão nova entra
    no lugar da antiga, que mantém endereço, status e data de publicação."""

    def setUp(self):
        pasta = tempfile.TemporaryDirectory()
        self.addCleanup(pasta.cleanup)
        self.pasta = Path(pasta.name)
        self.antigo = criar_artigo('antigo', titulo='Título antigo', corpo='<p>Velho.</p>')
        self.publicado_em = Artigo.objects.get(slug='antigo').publicado_em
        criar_artigo('novo', status=Artigo.Status.RASCUNHO, titulo='Título novo',
                     corpo=CORPO_DIFICIL, categoria=Artigo.Categoria.ANALISE_QUANTITATIVA)
        Artigo.objects.filter(slug='novo').update(
            capa='img/artigos/novo/capa.jpg', capa_alt='Alt', capa_credito='Foto: B', com_apoio_ia=True)

    def exportar(self, novo='novo', antigo='antigo'):
        call_command('exportar_artigo_migracao', novo, substituir=antigo,
                     pasta=str(self.pasta), stdout=StringIO())
        (arquivo,) = self.pasta.iterdir()
        spec = importlib.util.spec_from_file_location('migracao_substituicao', arquivo)
        modulo = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(modulo)
        return arquivo, modulo

    def test_nome_do_arquivo_indica_a_substituicao(self):
        grafo = MigrationLoader(None, ignore_no_migrations=True).graph
        folha = next(nome for app, nome in grafo.leaf_nodes() if app == 'conteudo')

        arquivo, _ = self.exportar()

        self.assertEqual(arquivo.name, f'{int(folha[:4]) + 1:04d}_substitui_artigo_antigo.py')

    def test_troca_o_conteudo_e_mantem_endereco_status_e_data(self):
        _, modulo = self.exportar()

        modulo.substituir_artigo(django_apps, None)

        artigo = Artigo.objects.get(pk=self.antigo.pk)
        self.assertEqual(artigo.slug, 'antigo')
        self.assertEqual(artigo.titulo, 'Título novo')
        self.assertEqual(artigo.corpo, CORPO_DIFICIL)
        self.assertEqual(artigo.categoria, Artigo.Categoria.ANALISE_QUANTITATIVA)
        self.assertEqual(artigo.capa, 'img/artigos/novo/capa.jpg')
        self.assertTrue(artigo.com_apoio_ia)
        self.assertEqual(artigo.status, Artigo.Status.PUBLICADO)
        self.assertEqual(artigo.publicado_em, self.publicado_em)
        self.assertIsNotNone(artigo.revisado_em)

    def test_desfazer_devolve_o_conteudo_anterior(self):
        _, modulo = self.exportar()
        modulo.substituir_artigo(django_apps, None)

        modulo.desfazer_substituicao(django_apps, None)

        artigo = Artigo.objects.get(pk=self.antigo.pk)
        self.assertEqual(artigo.titulo, 'Título antigo')
        self.assertEqual(artigo.corpo, '<p>Velho.</p>')
        self.assertIsNone(artigo.revisado_em)

    def test_sem_o_antigo_no_banco_cria_a_versao_nova_como_rascunho(self):
        _, modulo = self.exportar()
        Artigo.objects.filter(slug__in=['antigo', 'novo']).delete()

        modulo.substituir_artigo(django_apps, None)

        self.assertFalse(Artigo.objects.filter(slug='antigo').exists())
        self.assertEqual(Artigo.objects.get(slug='novo').status, Artigo.Status.RASCUNHO)

    def test_antigo_inexistente_no_banco_local_da_erro(self):
        with self.assertRaisesMessage(CommandError, 'nao-existe'):
            call_command('exportar_artigo_migracao', 'novo', substituir='nao-existe',
                         pasta=str(self.pasta))

    def test_nao_substitui_um_artigo_por_ele_mesmo(self):
        with self.assertRaisesMessage(CommandError, 'ele mesmo'):
            call_command('exportar_artigo_migracao', 'novo', substituir='novo',
                         pasta=str(self.pasta))


class EstruturaDoArtigoTests(TestCase):
    """Trilha, compartilhar e "Leia também" (ideias tiradas da estrutura de um portal de notícias)."""

    def setUp(self):
        # O banco de testes já vem com os artigos criados pelas migrações de dados.
        Artigo.objects.all().delete()

    def test_trilha_aponta_para_a_categoria(self):
        criar_artigo('a', categoria=Artigo.Categoria.RENDA_FIXA)
        resposta = self.client.get(reverse('conteudo:detalhe', args=['a']))
        self.assertContains(resposta, 'aria-label="Trilha de navegação"')
        self.assertContains(resposta, '?categoria=RENDA_FIXA">Renda fixa</a>')

    def test_link_ir_para_o_conteudo(self):
        resposta = self.client.get(reverse('core:home'))
        self.assertContains(resposta, 'href="#conteudo">Ir para o conteúdo</a>')
        self.assertContains(resposta, 'id="conteudo"')

    def test_compartilhar_leva_o_endereco_completo_codificado(self):
        criar_artigo('a', titulo='Juros & você')
        resposta = self.client.get(reverse('conteudo:detalhe', args=['a']))
        self.assertContains(resposta, 'https://wa.me/?text=Juros%20%26%20voc%C3%AA%20http%3A%2F%2Ftestserver%2Fartigos%2Fa%2F')
        self.assertContains(resposta, 'rel="noopener noreferrer nofollow"')

    def test_rascunho_nao_tem_compartilhar(self):
        criar_artigo('r', status=Artigo.Status.RASCUNHO)
        self.client.force_login(User.objects.create_user(username='equipe', password='x', is_staff=True))
        resposta = self.client.get(reverse('conteudo:detalhe', args=['r']))
        self.assertNotContains(resposta, 'wa.me')

    def test_leia_tambem_prefere_a_mesma_categoria_e_completa_com_outras(self):
        atual = criar_artigo('atual', categoria=Artigo.Categoria.RENDA_FIXA)
        mesma = criar_artigo('mesma', categoria=Artigo.Categoria.RENDA_FIXA)
        outra1 = criar_artigo('outra1')
        outra2 = criar_artigo('outra2')
        criar_artigo('rascunho', status=Artigo.Status.RASCUNHO, categoria=Artigo.Categoria.RENDA_FIXA)
        resposta = self.client.get(reverse('conteudo:detalhe', args=['atual']))
        lista = resposta.context['leia_tambem']
        self.assertEqual(len(lista), 3)
        self.assertEqual(lista[0], mesma)
        self.assertEqual(set(lista[1:]), {outra1, outra2})
        self.assertNotIn(atual, lista)

    def test_sem_outros_artigos_nao_mostra_leia_tambem(self):
        criar_artigo('so')
        resposta = self.client.get(reverse('conteudo:detalhe', args=['so']))
        self.assertNotContains(resposta, 'Leia também')
