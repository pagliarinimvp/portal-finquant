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


# --- Avaliação por artigo ("Este artigo te ajudou?"), desde 10/11/2026 -------
from datetime import date

from django.db.models import ProtectedError

from conteudo.models import Artigo

from .models import AvaliacaoArtigo


def _artigo(slug='selic', status=Artigo.Status.PUBLICADO):
    return Artigo.objects.create(
        titulo='Selic', slug=slug, resumo='Resumo.', corpo='<p>Corpo.</p>', status=status)


class AvaliacaoArtigoTests(TestCase):
    def votar(self, artigo, **dados):
        return self.client.post(reverse('avaliacoes:artigo', args=[artigo.slug]), dados)

    def test_artigo_publicado_mostra_a_pergunta(self):
        artigo = _artigo()

        self.assertContains(self.client.get(artigo.get_absolute_url()), 'Este artigo te ajudou?')

    def test_registra_sim_com_comentario_e_volta_ao_artigo(self):
        artigo = _artigo()

        resposta = self.votar(artigo, ajudou='1', comentario='Explicou bem.')

        self.assertRedirects(resposta, artigo.get_absolute_url() + '#avaliacao-artigo',
                             fetch_redirect_response=False)
        voto = AvaliacaoArtigo.objects.get()
        self.assertEqual(voto.artigo, artigo)
        self.assertTrue(voto.ajudou)
        self.assertEqual(voto.comentario, 'Explicou bem.')
        self.assertIsNone(voto.usuario)

    def test_registra_nao(self):
        self.votar(_artigo(), ajudou='0')

        self.assertFalse(AvaliacaoArtigo.objects.get().ajudou)

    def test_guarda_a_versao_do_artigo_no_momento_do_voto(self):
        artigo = _artigo()
        Artigo.objects.filter(pk=artigo.pk).update(revisado_em='2026-11-10')

        self.votar(artigo, ajudou='1')

        self.assertEqual(AvaliacaoArtigo.objects.get().versao_revisada_em, date(2026, 11, 10))

    def test_um_voto_por_artigo_na_mesma_sessao(self):
        artigo = _artigo()

        self.votar(artigo, ajudou='1')
        self.votar(artigo, ajudou='0')

        self.assertEqual(AvaliacaoArtigo.objects.count(), 1)

    def test_depois_de_votar_a_pagina_agradece_em_vez_de_perguntar(self):
        artigo = _artigo()
        self.votar(artigo, ajudou='1')

        resposta = self.client.get(artigo.get_absolute_url())

        self.assertContains(resposta, 'Obrigado! Sua resposta sobre este artigo foi registrada.')
        self.assertNotContains(resposta, 'Este artigo te ajudou?')

    def test_voto_em_outro_artigo_e_aceito(self):
        self.votar(_artigo('a'), ajudou='1')
        self.votar(_artigo('b'), ajudou='1')

        self.assertEqual(AvaliacaoArtigo.objects.count(), 2)

    def test_resposta_invalida_nao_grava(self):
        self.votar(_artigo(), ajudou='talvez')

        self.assertFalse(AvaliacaoArtigo.objects.exists())

    def test_rascunho_nao_recebe_voto(self):
        resposta = self.votar(_artigo(status=Artigo.Status.RASCUNHO), ajudou='1')

        self.assertEqual(resposta.status_code, 404)
        self.assertFalse(AvaliacaoArtigo.objects.exists())

    def test_get_nao_grava(self):
        resposta = self.client.get(reverse('avaliacoes:artigo', args=[_artigo().slug]))

        self.assertEqual(resposta.status_code, 405)

    def test_usuario_logado_fica_registrado_e_nao_vota_duas_vezes(self):
        usuario = User.objects.create_user(username='ana', password='x')
        artigo = _artigo()
        self.client.force_login(usuario)
        self.votar(artigo, ajudou='1')
        self.client.logout()
        self.client.force_login(usuario)

        self.votar(artigo, ajudou='0')

        self.assertEqual(AvaliacaoArtigo.objects.get().usuario, usuario)

    def test_artigo_com_respostas_nao_pode_ser_apagado(self):
        artigo = _artigo()
        self.votar(artigo, ajudou='1')

        with self.assertRaises(ProtectedError):
            artigo.delete()


# --- Convites para avaliar o site, desde 10/11/2026 --------------------------
# Aparecem logo depois de a pessoa receber algo útil (resultado de simulador,
# fim da análise de ações, resposta sobre um artigo) e somem para quem já avaliou.

CONVITE = 'aria-label="Avaliar o site"'
LINK_SIMULADOR = {
    'valor_inicial': '1000', 'aporte_mensal': '100', 'taxa_mensal': '1',
    'periodo_taxa': 'mensal', 'periodo_meses': '3',
}


class ConviteAvaliacaoTests(TestCase):
    def test_resultado_de_simulador_convida(self):
        resposta = self.client.get(reverse('simuladores:juros_compostos'), LINK_SIMULADOR)

        self.assertContains(resposta, CONVITE)

    def test_simulador_sem_resultado_nao_convida(self):
        self.assertNotContains(self.client.get(reverse('simuladores:juros_compostos')), CONVITE)

    def test_quem_ja_avaliou_nao_ve_convite(self):
        self.client.post(reverse('avaliacoes:avaliar'), RESPOSTA_VALIDA)

        resposta = self.client.get(reverse('simuladores:juros_compostos'), LINK_SIMULADOR)

        self.assertNotContains(resposta, CONVITE)

    def test_artigo_respondido_convida_para_o_site(self):
        artigo = _artigo()
        self.assertNotContains(self.client.get(artigo.get_absolute_url()), CONVITE)

        self.client.post(reverse('avaliacoes:artigo', args=[artigo.slug]), {'ajudou': '1'})

        self.assertContains(self.client.get(artigo.get_absolute_url()), CONVITE)

    def test_rodape_tem_link_para_avaliar(self):
        resposta = self.client.get(reverse('core:home'))

        self.assertContains(resposta, 'fq-rodape-avaliar')


class OrdemFormularioTests(TestCase):
    def test_opiniao_vem_antes_do_perfil(self):
        # Desde 10/11/2026: opinião primeiro, perfil no fim (menos desistência).
        html = self.client.get(reverse('avaliacoes:avaliar')).content.decode()

        nota = html.index('name="nota"')
        ajudou = html.index('name="conteudo_ajudou"')
        idade = html.index('name="faixa_etaria"')
        renda = html.index('name="faixa_renda_familiar"')
        self.assertLess(nota, idade)
        self.assertLess(ajudou, idade)
        self.assertLess(ajudou, renda)
