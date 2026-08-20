from django.contrib.auth.models import User
from django.test import TestCase, override_settings
from django.urls import reverse

from avaliacoes.models import Avaliacao

GOOGLE_CONFIGURADO = {
    "google": {
        "APPS": [{"client_id": "dummy-google-id", "secret": "dummy-google-secret", "key": ""}],
        "SCOPE": ["profile", "email"],
    },
}

GITHUB_CONFIGURADO = {
    "github": {
        "APPS": [{"client_id": "dummy-github-id", "secret": "dummy-github-secret", "key": ""}],
    },
}


class LoginSocialUrlsTests(TestCase):
    @override_settings(SOCIALACCOUNT_PROVIDERS=GOOGLE_CONFIGURADO)
    def test_login_google_redireciona_para_o_google(self):
        response = self.client.post("/contas/social/google/login/")
        self.assertEqual(response.status_code, 302)
        self.assertIn("accounts.google.com", response.url)

    @override_settings(SOCIALACCOUNT_PROVIDERS=GITHUB_CONFIGURADO)
    def test_login_github_redireciona_para_o_github(self):
        response = self.client.post("/contas/social/github/login/")
        self.assertEqual(response.status_code, 302)
        self.assertIn("github.com", response.url)

    def test_telas_de_conta_do_allauth_redirecionam_para_as_nossas(self):
        """As rotas de login/cadastro do allauth sao blindadas em
        config/urls.py (antes do include) para nao expor uma segunda tela de
        login nem um cadastro que contorna a CadastroView do projeto."""
        self.assertRedirects(
            self.client.get("/contas/social/login/"), reverse('contas:login')
        )
        self.assertRedirects(
            self.client.get("/contas/social/signup/"), reverse('contas:cadastro')
        )


class LoginSocialBotoesTests(TestCase):
    @override_settings(SOCIALACCOUNT_PROVIDERS=GOOGLE_CONFIGURADO)
    def test_login_mostra_botao_google_quando_configurado(self):
        response = self.client.get(reverse('contas:login'))
        self.assertContains(response, 'Entrar com Google')
        self.assertNotContains(response, 'Entrar com GitHub')
        # O botao precisa ser um form POST, nao um link GET: com
        # SOCIALACCOUNT_LOGIN_ON_GET no padrao (False), um <a href> quebraria.
        self.assertContains(response, 'action="/contas/social/google/login/"')
        self.assertContains(response, 'method="post"')

    @override_settings(SOCIALACCOUNT_PROVIDERS={})
    def test_login_nao_mostra_botoes_quando_nada_configurado(self):
        response = self.client.get(reverse('contas:login'))
        self.assertNotContains(response, 'Entrar com Google')
        self.assertNotContains(response, 'Entrar com GitHub')
        self.assertNotContains(response, 'action="/contas/social/google/login/"')
        self.assertNotContains(response, 'action="/contas/social/github/login/"')

    @override_settings(SOCIALACCOUNT_PROVIDERS=GITHUB_CONFIGURADO)
    def test_cadastro_mostra_botao_github_quando_configurado(self):
        response = self.client.get(reverse('contas:cadastro'))
        self.assertContains(response, 'Entrar com GitHub')
        self.assertNotContains(response, 'Entrar com Google')
        self.assertContains(response, 'action="/contas/social/github/login/"')
        self.assertContains(response, 'method="post"')


class MinhaContaViewTests(TestCase):
    def test_exige_login(self):
        response = self.client.get(reverse('contas:minha_conta'))
        self.assertRedirects(
            response, f"{reverse('contas:login')}?next={reverse('contas:minha_conta')}"
        )

    def test_usuario_logado_ve_seus_dados_e_avaliacoes(self):
        usuario = User.objects.create_user(
            username='joana', email='joana@example.com', password='senha-123',
        )
        Avaliacao.objects.create(
            usuario=usuario,
            nota=Avaliacao.Nota.CINCO,
            faixa_etaria=Avaliacao.FaixaEtaria.DE_19_A_25,
            sexo=Avaliacao.Sexo.FEMININO,
            experiencia_investimentos=Avaliacao.ExperienciaInvestimentos.INICIANTE,
            conteudo_ajudou=Avaliacao.ConteudoAjudou.CONCORDO_TOTALMENTE,
            faixa_renda_familiar=Avaliacao.FaixaRendaFamiliar.NAO_INFORMAR,
            comentario='Muito bom!',
        )
        self.client.force_login(usuario)

        response = self.client.get(reverse('contas:minha_conta'))

        self.assertContains(response, 'joana')
        self.assertContains(response, 'joana@example.com')
        self.assertContains(response, 'Excelente')
        self.assertContains(response, 'Muito bom!')

    def test_usuario_sem_avaliacoes_ve_convite_para_avaliar(self):
        usuario = User.objects.create_user(username='pedro', password='senha-123')
        self.client.force_login(usuario)

        response = self.client.get(reverse('contas:minha_conta'))

        self.assertContains(response, 'ainda não avaliou o site')
        self.assertContains(response, reverse('avaliacoes:avaliar'))
