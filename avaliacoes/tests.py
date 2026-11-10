from django.contrib.auth.models import AnonymousUser, User
from django.test import RequestFactory, TestCase
from django.urls import reverse

from .context_processors import modal_avaliacao
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
        Avaliacao.objects.create(
            usuario=usuario,
            nota=Avaliacao.Nota.CINCO,
            faixa_etaria=Avaliacao.FaixaEtaria.DE_26_A_35,
            sexo=Avaliacao.Sexo.FEMININO,
            experiencia_investimentos=Avaliacao.ExperienciaInvestimentos.INTERMEDIARIA,
            conteudo_ajudou=Avaliacao.ConteudoAjudou.CONCORDO,
            faixa_renda_familiar=Avaliacao.FaixaRendaFamiliar.DE_2000_A_5000,
        )
        self.client.login(username='joana', password='senha123')

        resposta = self.client.get(reverse('core:home'))

        self.assertFalse(resposta.context['mostrar_modal_avaliacao'])

    def test_paginas_de_avaliacoes_nunca_mostram_modal(self):
        resposta = self.client.get(reverse('avaliacoes:avaliar'))
        self.assertFalse(resposta.context['mostrar_modal_avaliacao'])

        resposta = self.client.get(reverse('avaliacoes:obrigado'))
        self.assertFalse(resposta.context['mostrar_modal_avaliacao'])

    def test_url_inexistente_nao_quebra_o_context_processor(self):
        # Sem rota resolvida (página 404), resolve() lançava Resolver404.
        requisicao = RequestFactory().get('/pagina-que-nao-existe/')
        requisicao.user = AnonymousUser()
        requisicao.session = {}

        self.assertEqual(modal_avaliacao(requisicao), {'mostrar_modal_avaliacao': True})


RESPOSTA_VALIDA = {
    'faixa_etaria': Avaliacao.FaixaEtaria.DE_26_A_35,
    'sexo': Avaliacao.Sexo.FEMININO,
    'faixa_renda_familiar': Avaliacao.FaixaRendaFamiliar.DE_2000_A_5000,
    'experiencia_investimentos': Avaliacao.ExperienciaInvestimentos.INICIANTE,
    'conteudo_ajudou': Avaliacao.ConteudoAjudou.CONCORDO,
    'nota': Avaliacao.Nota.QUATRO,
    'comentario': '',
    'consentimento': 'on',
}


class AvaliacaoEnvioTests(TestCase):
    def test_sem_consentimento_nao_salva(self):
        dados = {k: v for k, v in RESPOSTA_VALIDA.items() if k != 'consentimento'}

        resposta = self.client.post(reverse('avaliacoes:avaliar'), dados)

        self.assertContains(resposta, 'confirme que tem 18 anos ou mais e concorda em participar')
        self.assertEqual(Avaliacao.objects.count(), 0)

    def test_com_consentimento_salva_e_registra(self):
        resposta = self.client.post(reverse('avaliacoes:avaliar'), RESPOSTA_VALIDA)

        self.assertRedirects(resposta, reverse('avaliacoes:obrigado'))
        self.assertTrue(Avaliacao.objects.get().consentimento)

    def test_formulario_mostra_aviso_de_privacidade(self):
        resposta = self.client.get(reverse('avaliacoes:avaliar'))
        self.assertContains(resposta, 'Aviso de privacidade')

    def test_anonimo_nao_avalia_duas_vezes_no_mesmo_navegador(self):
        self.client.post(reverse('avaliacoes:avaliar'), RESPOSTA_VALIDA)

        resposta = self.client.post(reverse('avaliacoes:avaliar'), RESPOSTA_VALIDA)

        self.assertRedirects(resposta, reverse('avaliacoes:obrigado'))
        self.assertEqual(Avaliacao.objects.count(), 1)

    def test_usuario_que_ja_avaliou_e_redirecionado(self):
        usuario = User.objects.create_user(username='joana', password='senha123')
        Avaliacao.objects.create(usuario=usuario, **{
            k: v for k, v in RESPOSTA_VALIDA.items() if k not in ('comentario', 'consentimento')
        })
        self.client.force_login(usuario)

        resposta = self.client.get(reverse('avaliacoes:avaliar'), follow=True)

        self.assertRedirects(resposta, reverse('avaliacoes:obrigado'))
        self.assertContains(resposta, 'Você já avaliou o site')

    def test_anonimo_que_avaliou_nao_ve_mais_o_modal(self):
        self.client.post(reverse('avaliacoes:avaliar'), RESPOSTA_VALIDA)

        resposta = self.client.get(reverse('core:home'))

        self.assertFalse(resposta.context['mostrar_modal_avaliacao'])


class AvaliacaoCamposTests(TestCase):
    def test_listas_abrem_sem_opcao_escolhida(self):
        # Antes de 10/11/2026 as listas abriam na primeira opção, e quem não
        # mexia enviava "Até 18 anos", "Masculino" e "Até R$ 2.000".
        resposta = self.client.get(reverse('avaliacoes:avaliar'))

        self.assertContains(resposta, '<option value="" selected>Selecione…</option>', count=3)

    def test_lista_nao_tocada_nao_e_aceita(self):
        for campo in ('faixa_etaria', 'sexo', 'faixa_renda_familiar'):
            with self.subTest(campo=campo):
                dados = dict(RESPOSTA_VALIDA, **{campo: ''})

                resposta = self.client.post(reverse('avaliacoes:avaliar'), dados)

                self.assertEqual(resposta.status_code, 200)
                self.assertTrue(resposta.context['form'].errors[campo])
        self.assertEqual(Avaliacao.objects.count(), 0)

    def test_menor_de_idade_nao_e_aceito(self):
        dados = dict(RESPOSTA_VALIDA, faixa_etaria=Avaliacao.FaixaEtaria.ATE_18)

        resposta = self.client.post(reverse('avaliacoes:avaliar'), dados)

        self.assertNotContains(resposta, 'Até 18 anos')
        self.assertTrue(resposta.context['form'].errors['faixa_etaria'])
        self.assertEqual(Avaliacao.objects.count(), 0)

    def test_consentimento_confirma_maioridade(self):
        resposta = self.client.get(reverse('avaliacoes:avaliar'))

        self.assertContains(resposta, 'Tenho 18 anos ou mais')
        self.assertContains(resposta, 'Comentário')
