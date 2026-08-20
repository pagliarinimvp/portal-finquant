from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from .models import Avaliacao


class ModalAvaliacaoContextProcessorTests(TestCase):
    def test_anonimo_ve_modal_em_pagina_qualquer(self):
        resposta = self.client.get(reverse('core:home'))
        self.assertTrue(resposta.context['mostrar_modal_avaliacao'])

    def test_usuario_sem_avaliacao_ve_modal(self):
        User.objects.create_user(username='joana', password='senha123')
        self.client.login(username='joana', password='senha123')

        resposta = self.client.get(reverse('core:home'))

        self.assertTrue(resposta.context['mostrar_modal_avaliacao'])

    def test_usuario_com_avaliacao_nao_ve_modal(self):
        usuario = User.objects.create_user(username='joana', password='senha123')
        Avaliacao.objects.create(usuario=usuario, nota=Avaliacao.Nota.CINCO)
        self.client.login(username='joana', password='senha123')

        resposta = self.client.get(reverse('core:home'))

        self.assertFalse(resposta.context['mostrar_modal_avaliacao'])

    def test_paginas_de_avaliacoes_nunca_mostram_modal(self):
        resposta = self.client.get(reverse('avaliacoes:avaliar'))
        self.assertFalse(resposta.context['mostrar_modal_avaliacao'])

        resposta = self.client.get(reverse('avaliacoes:obrigado'))
        self.assertFalse(resposta.context['mostrar_modal_avaliacao'])
