from django.test import TestCase, override_settings
from django.urls import reverse

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


class LoginSocialBotoesTests(TestCase):
    @override_settings(SOCIALACCOUNT_PROVIDERS=GOOGLE_CONFIGURADO)
    def test_login_mostra_botao_google_quando_configurado(self):
        response = self.client.get(reverse('contas:login'))
        self.assertContains(response, 'Entrar com Google')
        self.assertNotContains(response, 'Entrar com GitHub')

    @override_settings(SOCIALACCOUNT_PROVIDERS={})
    def test_login_nao_mostra_botoes_quando_nada_configurado(self):
        response = self.client.get(reverse('contas:login'))
        self.assertNotContains(response, 'Entrar com Google')
        self.assertNotContains(response, 'Entrar com GitHub')

    @override_settings(SOCIALACCOUNT_PROVIDERS=GITHUB_CONFIGURADO)
    def test_cadastro_mostra_botao_github_quando_configurado(self):
        response = self.client.get(reverse('contas:cadastro'))
        self.assertContains(response, 'Entrar com GitHub')
        self.assertNotContains(response, 'Entrar com Google')
