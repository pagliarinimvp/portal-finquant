"""
Configuração de URLs do projeto config (Portal FinQuant).

A lista `urlpatterns` roteia URLs para views. Para mais informações, veja:
    https://docs.djangoproject.com/en/6.1/topics/http/urls/
"""
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('core.urls')),
    path('contas/', include('contas.urls')),
    path('artigos/', include('conteudo.urls')),
    path('simuladores/', include('simuladores.urls')),
    path('avaliacao/', include('avaliacoes.urls')),
]
