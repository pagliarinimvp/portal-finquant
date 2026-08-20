from django.contrib.auth import views as auth_views
from django.urls import path

from . import views

app_name = 'contas'

urlpatterns = [
    path('entrar/', auth_views.LoginView.as_view(template_name='contas/login.html'), name='login'),
    path('sair/', auth_views.LogoutView.as_view(), name='logout'),
    path('cadastro/', views.CadastroView.as_view(), name='cadastro'),
    path('minha-conta/', views.MinhaContaView.as_view(), name='minha_conta'),
]
