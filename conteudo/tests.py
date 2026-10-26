from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from .models import Artigo
from .templatetags.conteudo_extras import corpo_seguro


def criar_artigo(slug, status=Artigo.Status.PUBLICADO, **campos):
    return Artigo.objects.create(
        titulo=campos.get('titulo', slug), slug=slug, resumo='Resumo.',
        corpo=campos.get('corpo', '<p>Corpo.</p>'), status=status,
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
