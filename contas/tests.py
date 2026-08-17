from django.test import TestCase, override_settings

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
