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


# Definição da aplicação

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # Apps do Portal FinQuant
    'core',
    'contas',
    'conteudo',
    'simuladores',
    'avaliacoes',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
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
        'BACKEND': 'whitenoise.storage.CompressedManifestStaticFilesStorage',
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
