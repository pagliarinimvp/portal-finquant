# Login Social (Google e GitHub) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Adicionar botões "Entrar com Google" e "Entrar com GitHub" ao lado do login/cadastro por usuário e senha já existente no Portal FinQuant.

**Architecture:** `django-allauth` cuida só do handshake OAuth (login/callback com Google e GitHub); as telas `contas/login.html` e `contas/cadastro.html` continuam sendo as views/templates próprias do projeto, só ganhando botões que apontam pras URLs do allauth. Vinculação automática de conta por e-mail verificado é feita por configuração nativa do allauth (`SOCIALACCOUNT_EMAIL_AUTHENTICATION` + `_AUTO_CONNECT`), sem adapter customizado.

**Tech Stack:** Django 6.1, `django-allauth[socialaccount]==65.19.1`, `django-environ` (já usado no projeto), SQLite (dev).

**Spec:** [docs/superpowers/specs/2026-08-17-login-social-design.md](../specs/2026-08-17-login-social-design.md)

## Global Constraints

- Idioma do projeto é pt-BR: comentários, mensagens de commit e textos de UI em português (`CLAUDE.md`).
- Testes rodam com `python manage.py test` (Django `TestCase`), não há pytest configurado.
- Segredos e credenciais só via `.env` / `django-environ`, nunca hardcoded (padrão já usado em `config/settings.py`).
- Versão fixa: `django-allauth[socialaccount]==65.19.1`.
- O fluxo de usuário/senha existente (`contas.views.CadastroView`, `django.contrib.auth` login/logout views) não é removido nem alterado.
- Um botão de provedor só aparece no template se **as duas** variáveis de ambiente daquele provedor (`client_id` e `secret`) estiverem preenchidas.

---

## Task 1: Instalar django-allauth e configurar apps/middleware base

**Files:**
- Modify: `requirements.txt`
- Modify: `config/settings.py`

**Interfaces:**
- Consumes: nada (primeira tarefa).
- Produces: `django.contrib.sites`, `allauth`, `allauth.account`, `allauth.socialaccount`, `allauth.socialaccount.providers.google`, `allauth.socialaccount.providers.github` instalados e migrados. `SITE_ID = 1` disponível para tasks seguintes.

- [ ] **Step 1: Adicionar a dependência**

Edite `requirements.txt` e adicione a linha (mantendo ordem alfabética como o resto do arquivo):

```
django-allauth[socialaccount]==65.19.1
```

- [ ] **Step 2: Instalar no ambiente virtual**

Run: `source venv/Scripts/activate && pip install -r requirements.txt`
Expected: `Successfully installed django-allauth-65.19.1 ...` (junto com dependências transitivas como `requests-oauthlib`).

- [ ] **Step 3: Registrar as apps, middleware e backend de autenticação**

Em `config/settings.py`, no bloco `INSTALLED_APPS` (depois de `'django.contrib.staticfiles',` e antes do comentário `# Apps do Portal FinQuant`), adicione:

```python
    'django.contrib.sites',
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'allauth.socialaccount.providers.google',
    'allauth.socialaccount.providers.github',
```

Logo abaixo do bloco `INSTALLED_APPS`, adicione:

```python
SITE_ID = 1
```

Em `MIDDLEWARE`, adicione como último item da lista:

```python
    'allauth.account.middleware.AccountMiddleware',
```

Depois do bloco `AUTH_PASSWORD_VALIDATORS` (ou em qualquer lugar após `INSTALLED_APPS`), adicione:

```python
AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
    'allauth.account.auth_backends.AuthenticationBackend',
]
```

- [ ] **Step 4: Verificar a configuração**

Run: `python manage.py check`
Expected: `System check identified no issues (0 silenced).`

Se aparecer erro sobre `SITE_ID`/`sites` não instalado, confirme que `django.contrib.sites` está em `INSTALLED_APPS` antes de `allauth`.

- [ ] **Step 5: Migrar o banco**

Run: `python manage.py migrate`
Expected: aplica migrações novas de `sites`, `account`, `socialaccount` (algo como `Applying account.0001_initial... OK`, `Applying socialaccount.0001_initial... OK`, etc.), sem erros.

Run: `python manage.py showmigrations sites account socialaccount`
Expected: todas as migrações listadas com `[X]` (aplicadas).

- [ ] **Step 6: Commit**

```bash
git add requirements.txt config/settings.py
git commit -m "Instala django-allauth e configura apps/middleware base"
```

---

## Task 2: Configurar credenciais dos provedores, URLs do allauth e vinculação automática por e-mail

**Files:**
- Modify: `config/settings.py`
- Modify: `config/urls.py`
- Modify: `.env.example`
- Test: `contas/tests.py`

**Interfaces:**
- Consumes: apps/middleware da Task 1 (`allauth.socialaccount.providers.google`/`github` já instalados e migrados).
- Produces: `SOCIALACCOUNT_PROVIDERS` (dict, populado condicionalmente por provedor), rotas em `/contas/social/<provider>/login/` e `/contas/social/<provider>/login/callback/` respondendo. Task 3 depende dessas rotas existirem para os botões funcionarem.

- [ ] **Step 1: Escrever o teste que falha**

Crie/edite `contas/tests.py`:

```python
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
        response = self.client.get("/contas/social/google/login/")
        self.assertEqual(response.status_code, 302)
        self.assertIn("accounts.google.com", response.url)

    @override_settings(SOCIALACCOUNT_PROVIDERS=GITHUB_CONFIGURADO)
    def test_login_github_redireciona_para_o_github(self):
        response = self.client.get("/contas/social/github/login/")
        self.assertEqual(response.status_code, 302)
        self.assertIn("github.com", response.url)
```

- [ ] **Step 2: Rodar o teste e confirmar que falha**

Run: `python manage.py test contas.tests.LoginSocialUrlsTests -v 2`
Expected: FAIL nos dois testes com `404` (as rotas `/contas/social/.../` ainda não existem — `config/urls.py` ainda não inclui `allauth.urls`).

- [ ] **Step 3: Incluir as URLs do allauth**

Em `config/urls.py`, adicione ao `urlpatterns` (depois da linha `path('contas/', include('contas.urls')),`):

```python
    path('contas/social/', include('allauth.urls')),
```

- [ ] **Step 4: Configurar os provedores e a vinculação automática por e-mail**

Em `config/settings.py`, logo abaixo do bloco `AUTHENTICATION_BACKENDS` da Task 1, adicione:

```python
# Login social (Google e GitHub)
# Cada provedor só entra no dicionário se as duas variáveis de ambiente dele
# estiverem preenchidas — é isso que faz o botão correspondente não aparecer
# no template quando o provedor não está configurado (ver contas/login.html).
SOCIALACCOUNT_PROVIDERS = {}

GOOGLE_CLIENT_ID = env('GOOGLE_CLIENT_ID', default='')
GOOGLE_CLIENT_SECRET = env('GOOGLE_CLIENT_SECRET', default='')
if GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET:
    SOCIALACCOUNT_PROVIDERS['google'] = {
        'APPS': [{
            'client_id': GOOGLE_CLIENT_ID,
            'secret': GOOGLE_CLIENT_SECRET,
            'key': '',
        }],
        'SCOPE': ['profile', 'email'],
    }

GITHUB_CLIENT_ID = env('GITHUB_CLIENT_ID', default='')
GITHUB_CLIENT_SECRET = env('GITHUB_CLIENT_SECRET', default='')
if GITHUB_CLIENT_ID and GITHUB_CLIENT_SECRET:
    SOCIALACCOUNT_PROVIDERS['github'] = {
        'APPS': [{
            'client_id': GITHUB_CLIENT_ID,
            'secret': GITHUB_CLIENT_SECRET,
            'key': '',
        }],
    }

# Pula a tela extra de confirmacao do allauth: clicar no botao -> autorizar
# no provedor -> volta logado, sem passo intermediario.
SOCIALACCOUNT_AUTO_SIGNUP = True

# Se o e-mail vindo do provedor (verificado) ja pertence a um usuario local
# existente, loga nessa conta em vez de dar erro de e-mail duplicado, e
# conecta a conta social a ela automaticamente.
SOCIALACCOUNT_EMAIL_AUTHENTICATION = True
SOCIALACCOUNT_EMAIL_AUTHENTICATION_AUTO_CONNECT = True
```

- [ ] **Step 5: Rodar o teste de novo e confirmar que passa**

Run: `python manage.py test contas.tests.LoginSocialUrlsTests -v 2`
Expected: `OK` (2 testes passando).

- [ ] **Step 6: Verificação manual do settings**

Run: `python manage.py check`
Expected: `System check identified no issues (0 silenced).`

- [ ] **Step 7: Documentar as variáveis novas no `.env.example`**

Adicione ao final de `.env.example`:

```
# Login social (opcional). Deixe em branco para não mostrar o botão
# correspondente. Veja o passo a passo em
# docs/superpowers/specs/2026-08-17-login-social-design.md (Apêndice).
GOOGLE_CLIENT_ID=
GOOGLE_CLIENT_SECRET=
GITHUB_CLIENT_ID=
GITHUB_CLIENT_SECRET=
```

- [ ] **Step 8: Commit**

```bash
git add config/settings.py config/urls.py .env.example contas/tests.py
git commit -m "Configura provedores OAuth, URLs do allauth e vinculacao automatica por e-mail"
```

---

## Task 3: Botões de login social nas telas de entrar e cadastro

**Files:**
- Modify: `templates/contas/login.html`
- Modify: `templates/contas/cadastro.html`
- Test: `contas/tests.py`

**Interfaces:**
- Consumes: rotas `/contas/social/google/login/` e `/contas/social/github/login/` da Task 2; `SOCIALACCOUNT_PROVIDERS` (dict) controlando quais provedores aparecem.
- Produces: nada consumido por outras tasks — última tarefa do plano.

- [ ] **Step 1: Escrever os testes que falham**

Adicione a `contas/tests.py` (mesmo arquivo da Task 2, reaproveitando `GOOGLE_CONFIGURADO`/`GITHUB_CONFIGURADO`). Primeiro, junte `reverse` ao import já existente no topo do arquivo:

```python
from django.test import TestCase, override_settings
from django.urls import reverse
```

Depois, adicione a nova classe de teste no final do arquivo:

```python
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
```

- [ ] **Step 2: Rodar os testes e confirmar que falham**

Run: `python manage.py test contas.tests.LoginSocialBotoesTests -v 2`
Expected: FAIL em `test_login_mostra_botao_google_quando_configurado` e `test_cadastro_mostra_botao_github_quando_configurado` (texto "Entrar com Google"/"Entrar com GitHub" ainda não existe nos templates). O teste `test_login_nao_mostra_botoes_quando_nada_configurado` já passa (nada foi adicionado ainda) — isso é esperado, ele serve de guarda de regressão daqui pra frente.

- [ ] **Step 3: Adicionar os botões em `templates/contas/login.html`**

No topo do arquivo, depois de `{% extends "base.html" %}`, adicione:

```django
{% load socialaccount %}
```

Dentro do `<div class="card p-4">`, depois do `</form>` existente e antes do `<p class="mt-3 mb-0 text-center">`, adicione:

```django
            {% get_providers as socialaccount_providers %}
            {% if socialaccount_providers %}
            <hr class="my-3">
            <div class="d-grid gap-2">
                {% for provider in socialaccount_providers %}
                    {% if provider.id == "google" %}
                    <a href="{% provider_login_url 'google' %}" class="btn btn-outline-dark">
                        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 18 18" class="me-1" aria-hidden="true">
                            <path fill="#4285F4" d="M17.64 9.2c0-.64-.06-1.25-.16-1.84H9v3.48h4.84c-.21 1.13-.84 2.09-1.8 2.73v2.27h2.92c1.7-1.57 2.68-3.88 2.68-6.64z"/>
                            <path fill="#34A853" d="M9 18c2.43 0 4.47-.8 5.96-2.17l-2.92-2.27c-.81.54-1.84.86-3.04.86-2.34 0-4.32-1.58-5.03-3.7H.96v2.33C2.44 15.98 5.48 18 9 18z"/>
                            <path fill="#FBBC05" d="M3.97 10.72A5.4 5.4 0 0 1 3.68 9c0-.6.1-1.18.29-1.72V4.95H.96A9 9 0 0 0 0 9c0 1.45.35 2.83.96 4.05l3.01-2.33z"/>
                            <path fill="#EA4335" d="M9 3.58c1.32 0 2.51.45 3.44 1.35l2.58-2.58C13.46.89 11.43 0 9 0 5.48 0 2.44 2.02.96 4.95l3.01 2.33C4.68 5.16 6.66 3.58 9 3.58z"/>
                        </svg>
                        Entrar com Google
                    </a>
                    {% elif provider.id == "github" %}
                    <a href="{% provider_login_url 'github' %}" class="btn btn-outline-dark">
                        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 16 16" class="me-1" fill="currentColor" aria-hidden="true">
                            <path d="M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38 0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01 1.08.58 1.23.82.72 1.21 1.87.87 2.33.66.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82.64-.18 1.32-.27 2-.27.68 0 1.36.09 2 .27 1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 1.27.82 2.15 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01 1.93-.01 2.2 0 .21.15.46.55.38A8.01 8.01 0 0 0 16 8c0-4.42-3.58-8-8-8z"/>
                        </svg>
                        Entrar com GitHub
                    </a>
                    {% endif %}
                {% endfor %}
            </div>
            {% endif %}
```

- [ ] **Step 4: Repetir em `templates/contas/cadastro.html`**

Faça a mesma alteração: `{% load socialaccount %}` depois do `{% extends %}`, e o mesmo bloco `{% get_providers %}`/botões dentro do `<div class="card p-4">`, depois do `</form>` e antes do `<p class="mt-3 mb-0 text-center">`.

- [ ] **Step 5: Rodar os testes de novo e confirmar que passam**

Run: `python manage.py test contas.tests -v 2`
Expected: `OK` — todos os testes de `contas.tests` passando (`LoginSocialUrlsTests` da Task 2 e `LoginSocialBotoesTests` desta task).

- [ ] **Step 6: Rodar a suíte completa do projeto**

Run: `python manage.py test`
Expected: `OK`, nenhum teste de outro app quebrado.

- [ ] **Step 7: Commit**

```bash
git add templates/contas/login.html templates/contas/cadastro.html contas/tests.py
git commit -m "Adiciona botoes de login social nas telas de entrar e cadastro"
```

---

## Depois do plano: verificação manual (não automatizável)

Depois que as três tasks estiverem commitadas, siga o apêndice do spec para criar os apps OAuth reais no Google Cloud Console e no GitHub, preencher `GOOGLE_CLIENT_ID`/`GOOGLE_CLIENT_SECRET`/`GITHUB_CLIENT_ID`/`GITHUB_CLIENT_SECRET` no `.env` local, e testar manualmente (não dá pra automatizar o consentimento numa tela real do provedor):

1. Clicar em cada botão, autorizar, confirmar que volta logado.
2. Conferir em `/admin/auth/user/` e `/admin/socialaccount/socialaccount/` que a conta foi criada/conectada.
3. Logar com Google usando `pagliarinimvp@gmail.com` (e-mail do superusuário já existente) e confirmar que conecta à conta existente em vez de criar uma nova.
