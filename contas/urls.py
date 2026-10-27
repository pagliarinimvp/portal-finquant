from django.contrib.auth import views as auth_views
from django.urls import path, reverse_lazy

from . import views

app_name = 'contas'

urlpatterns = [
    path('entrar/', auth_views.LoginView.as_view(template_name='contas/login.html'), name='login'),
    path('sair/', auth_views.LogoutView.as_view(), name='logout'),
    path('cadastro/', views.CadastroView.as_view(), name='cadastro'),
    path('minha-conta/', views.MinhaContaView.as_view(), name='minha_conta'),
    # Recuperação de senha com as views nativas do Django. Os success_url são
    # explícitos porque o padrão delas procura rotas sem o namespace `contas:`.
    path('esqueci-a-senha/', auth_views.PasswordResetView.as_view(
        template_name='contas/senha_esqueci.html',
        email_template_name='contas/email_senha.txt',
        subject_template_name='contas/email_senha_assunto.txt',
        success_url=reverse_lazy('contas:senha_enviada'),
    ), name='senha_esqueci'),
    path('esqueci-a-senha/enviado/', auth_views.PasswordResetDoneView.as_view(
        template_name='contas/senha_enviada.html',
    ), name='senha_enviada'),
    path('nova-senha/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(
        template_name='contas/senha_nova.html',
        success_url=reverse_lazy('contas:senha_redefinida'),
    ), name='senha_nova'),
    path('nova-senha/pronto/', auth_views.PasswordResetCompleteView.as_view(
        template_name='contas/senha_redefinida.html',
    ), name='senha_redefinida'),
]
