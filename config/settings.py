"""
Configurações do Django para o projeto config (Portal FinQuant).

Para mais informações sobre este arquivo, veja
https://docs.djangoproject.com/en/6.1/topics/settings/

Para a lista completa de configurações e seus valores, veja
https://docs.djangoproject.com/en/6.1/ref/settings/
"""

from pathlib import Path

import environ

# Monta caminhos dentro do projeto assim: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

env = environ.Env(
    DEBUG=(bool, False),
)
# Lê variáveis do arquivo .env na raiz do projeto (não versionado).
environ.Env.read_env(BASE_DIR / '.env')


# AVISO DE SEGURANÇA: mantenha em segredo a chave usada em produção!
# Em desenvolvimento local, se SECRET_KEY não estiver definida no .env,
# usa uma chave insegura de placeholder apenas para não travar o runserver.
SECRET_KEY = env('SECRET_KEY', default='django-insecure-dev-key-troque-em-producao')

# AVISO DE SEGURANÇA: não rode com debug ativado em produção!
DEBUG = env.bool('DEBUG', default=False)

ALLOWED_HOSTS = env.list('ALLOWED_HOSTS', default=['localhost', '127.0.0.1'])

# Necessário quando o Render (ou outro PaaS) fica atrás de proxy HTTPS.
CSRF_TRUSTED_ORIGINS = env.list('CSRF_TRUSTED_ORIGINS', default=[])

# Necessario atras do proxy TLS do Render (ou outro PaaS): sem isso,
# request.is_secure() retorna False em producao e o allauth constroi as
# URLs de callback do OAuth como http://, que Google/GitHub rejeitam.
if not DEBUG:
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')


# Definição da aplicação

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sites',
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'allauth.socialaccount.providers.google',
    'allauth.socialaccount.providers.github',
    # Apps do Portal FinQuant
    'core',
    'contas',
    'conteudo',
    'simuladores',
    'avaliacoes',
]

SITE_ID = 1

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'allauth.account.middleware.AccountMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'avaliacoes.context_processors.modal_avaliacao',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'


# Banco de dados
# https://docs.djangoproject.com/en/6.1/ref/settings/#databases
# Usa SQLite localmente por padrão; em produção, define DATABASE_URL
# (ex: postgres://usuario:senha@host:porta/nome_do_banco) no .env do Render.

DATABASE_URL = env('DATABASE_URL', default='')
if DATABASE_URL:
    DATABASES = {'default': env.db_url_config(DATABASE_URL)}
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }


# Validação de senha
# https://docs.djangoproject.com/en/6.1/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
    'allauth.account.auth_backends.AuthenticationBackend',
]

# Login social (Google e GitHub)
# Cada provedor só entra no dicionário se as duas variáveis de ambiente dele
# estiverem preenchidas — é isso que faz o botão correspondente não aparecer
# no template quando o provedor não está configurado (ver contas/login.html).
SOCIALACCOUNT_PROVIDERS = {}

GOOGLE_CLIENT_ID = env('GOOGLE_CLIENT_ID', default='').strip()
GOOGLE_CLIENT_SECRET = env('GOOGLE_CLIENT_SECRET', default='').strip()
if GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET:
    SOCIALACCOUNT_PROVIDERS['google'] = {
        'APPS': [{
            'client_id': GOOGLE_CLIENT_ID,
            'secret': GOOGLE_CLIENT_SECRET,
            'key': '',
        }],
        'SCOPE': ['profile', 'email'],
    }

GITHUB_CLIENT_ID = env('GITHUB_CLIENT_ID', default='').strip()
GITHUB_CLIENT_SECRET = env('GITHUB_CLIENT_SECRET', default='').strip()
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

# Sem isso, o allauth nao pede o escopo `user:email` nem consulta
# /user/emails do GitHub -- o login com GitHub nunca recebe um e-mail
# verificado, quebrando a vinculacao automatica por e-mail para esse
# provedor especificamente (o Google nao precisa disso, ja retorna o
# e-mail verificado no token OpenID Connect).
SOCIALACCOUNT_QUERY_EMAIL = True


# Internacionalização
# https://docs.djangoproject.com/en/6.1/topics/i18n/

LANGUAGE_CODE = 'pt-br'

TIME_ZONE = 'America/Sao_Paulo'

USE_I18N = True

USE_TZ = True


# Arquivos estáticos (CSS, JavaScript, imagens)
# https://docs.djangoproject.com/en/6.1/howto/static-files/

STATIC_URL = 'static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'

STORAGES = {
    'default': {
        'BACKEND': 'django.core.files.storage.FileSystemStorage',
    },
    'staticfiles': {
        'BACKEND': (
            'django.contrib.staticfiles.storage.StaticFilesStorage'
            if DEBUG else
            'whitenoise.storage.CompressedManifestStaticFilesStorage'
        ),
    },
}

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


# Autenticação — para onde redirecionar após login/logout.
LOGIN_URL = 'contas:login'
LOGIN_REDIRECT_URL = 'core:home'
LOGOUT_REDIRECT_URL = 'core:home'


# E-mail
# https://docs.djangoproject.com/en/6.1/topics/email/#topic-email-configuration

MAILERS = {
    'default': {
        'BACKEND': 'django.core.mail.backends.console.EmailBackend',
    },
}
