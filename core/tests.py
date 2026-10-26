from datetime import timedelta

from django.test import TestCase
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
