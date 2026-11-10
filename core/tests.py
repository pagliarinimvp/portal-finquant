from datetime import timedelta

from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from conteudo.models import Artigo


class HomeTests(TestCase):
    def test_home_mostra_os_tres_publicados_mais_recentes(self):
        agora = timezone.now()
        for numero in range(4):
            artigo = Artigo.objects.create(
                titulo=f'Artigo {numero}', slug=f'artigo-{numero}', resumo='Resumo.',
                corpo='Corpo.', status=Artigo.Status.PUBLICADO,
            )
            # Datas explícitas: criados no mesmo instante, a ordem ficaria ao acaso.
            Artigo.objects.filter(pk=artigo.pk).update(publicado_em=agora + timedelta(days=numero))
        Artigo.objects.create(
            titulo='Rascunho', slug='rascunho', resumo='Resumo.', corpo='Corpo.',
            status=Artigo.Status.RASCUNHO,
        )

        response = self.client.get(reverse('core:home'))

        recentes = list(response.context['artigos_recentes'])
        self.assertEqual(len(recentes), 3)
        self.assertNotIn('rascunho', [artigo.slug for artigo in recentes])
        self.assertNotIn('artigo-0', [artigo.slug for artigo in recentes])

    def test_rodape_tem_aviso_de_conteudo_educacional(self):
        response = self.client.get(reverse('core:home'))

        self.assertContains(response, 'Não é recomendação de investimento')


class SaudeTests(TestCase):
    def test_responde_ok_sem_consultar_o_banco(self):
        with self.assertNumQueries(0):
            response = self.client.get(reverse('core:saude'))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, b'ok')


class SeoTests(TestCase):
    """Descrição, prévia de link, robots.txt, sitemap e favicon (09/11/2026)."""

    def test_pagina_tem_descricao_e_previa_da_propria_rota(self):
        html = self.client.get(reverse('simuladores:juros_compostos')).content.decode()
        self.assertIn('<meta name="description" content="Simule quanto um valor inicial', html)
        self.assertIn('og:title" content="Simulador de juros compostos', html)
        self.assertIn('og:image" content="http://testserver/static/img/previa.png"', html)

    def test_artigo_usa_titulo_e_resumo_proprios(self):
        Artigo.objects.create(
            titulo='Título do artigo', slug='titulo-do-artigo', resumo='Resumo do artigo.',
            corpo='Corpo.', status=Artigo.Status.PUBLICADO,
        )
        html = self.client.get('/artigos/titulo-do-artigo/').content.decode()
        self.assertIn('og:title" content="Título do artigo"', html)
        self.assertIn('<meta name="description" content="Resumo do artigo.">', html)

    def test_canonical_ignora_a_query_string(self):
        html = self.client.get('/artigos/?categoria=RENDA_FIXA').content.decode()
        self.assertIn('<link rel="canonical" href="http://testserver/artigos/">', html)

    def test_robots_bloqueia_a_analise_e_aponta_o_sitemap(self):
        texto = self.client.get('/robots.txt').content.decode()
        self.assertIn('Disallow: /estudo-caso/analise/', texto)
        self.assertIn('Disallow: /estudo-caso/aviso/', texto)
        self.assertIn('Sitemap: http://testserver/sitemap.xml', texto)

    def test_sitemap_lista_publicados_e_esconde_rascunho(self):
        for slug, status in (('publicado', Artigo.Status.PUBLICADO), ('rascunho', Artigo.Status.RASCUNHO)):
            Artigo.objects.create(titulo=slug, slug=slug, resumo='R.', corpo='C.', status=status)
        xml = self.client.get('/sitemap.xml').content.decode()
        self.assertIn('/artigos/publicado/', xml)
        self.assertNotIn('/artigos/rascunho/', xml)
        self.assertIn('/simuladores/juros-compostos/', xml)

    def test_favicon_redireciona_para_o_arquivo_estatico(self):
        r = self.client.get('/favicon.ico')
        self.assertEqual(r.status_code, 302)
        self.assertTrue(r['Location'].endswith('favicon.ico'))


class VersaoEstaticoTests(TestCase):
    """Sufixo ?v= nos CSS/JS só em desenvolvimento (09/11/2026)."""

    @override_settings(DEBUG=False)
    def test_sem_sufixo_em_producao(self):
        html = self.client.get(reverse('core:home')).content.decode()
        self.assertNotIn('site.css?v=', html)

    @override_settings(DEBUG=True)
    def test_com_sufixo_em_desenvolvimento(self):
        html = self.client.get(reverse('core:home')).content.decode()
        self.assertIn('site.css?v=', html)
