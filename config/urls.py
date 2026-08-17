"""
Configuração de URLs do projeto config (Portal FinQuant).

A lista `urlpatterns` roteia URLs para views. Para mais informações, veja:
    https://docs.djangoproject.com/en/6.1/topics/http/urls/
"""
from django.contrib import admin
from django.urls import include, path
from django.views.generic import RedirectView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('core.urls')),
    path('contas/', include('contas.urls')),
    # O include do allauth abaixo monta o app de contas inteiro dele (login,
    # cadastro, gestao de e-mail, troca de senha...). Usamos so os endpoints de
    # OAuth, entao estas duas rotas vem ANTES do include para interceptar as
    # telas concorrentes do allauth e mandar o usuario para as telas do projeto.
    path('contas/social/login/', RedirectView.as_view(pattern_name='contas:login', permanent=False)),
    path('contas/social/signup/', RedirectView.as_view(pattern_name='contas:cadastro', permanent=False)),
    path('contas/social/', include('allauth.urls')),
    path('artigos/', include('conteudo.urls')),
    path('simuladores/', include('simuladores.urls')),
    path('avaliacao/', include('avaliacoes.urls')),
]
