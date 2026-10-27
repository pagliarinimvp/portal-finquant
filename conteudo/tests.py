from datetime import timedelta

from django.contrib import admin
from django.contrib.auth.models import User
from django.test import TestCase
from django.test.client import RequestFactory
from django.urls import reverse

from .models import Artigo
from .templatetags.conteudo_extras import corpo_seguro


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
