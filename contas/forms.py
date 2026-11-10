import logging

from django import forms
from django.contrib.auth.forms import AuthenticationForm, PasswordResetForm, UserCreationForm
from django.contrib.auth.models import User

logger = logging.getLogger(__name__)


class EntrarForm(AuthenticationForm):
    """Login com aviso claro quando o usuário está bloqueado por excesso de tentativas.

    Sem isto, o bloqueio (contas/limite_login.py) apareceria como "usuário ou
    senha incorretos", e a pessoa continuaria tentando a senha certa.
    """

    def clean(self):
        from .limite_login import MENSAGEM, bloqueado
        if bloqueado(self.cleaned_data.get('username')):
            raise forms.ValidationError(MENSAGEM, code='bloqueado')
        return super().clean()


class CadastroForm(UserCreationForm):
    """Cadastro com e-mail, base para uma futura recuperação de senha.

    O e-mail não ganha uma EmailAddress verificada do allauth: sem
    confirmação, marcá-lo como verificado deixaria alguém cadastrar o e-mail
    de outra pessoa e receber o login social dela. Por isso o allauth trata
    esse e-mail como não verificado no primeiro login com Google/GitHub.
    """

    email = forms.EmailField(
        label='E-mail',
        help_text='Usado só para recuperar o acesso à conta.',
    )

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ('username', 'email')

    def clean_email(self):
        email = self.cleaned_data['email'].strip().lower()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError('Já existe uma conta com este e-mail.')
        return email


class RecuperarSenhaForm(PasswordResetForm):
    """Registra no log por que um pedido de senha enviou ou não o e-mail.

    A tela responde igual nos dois casos (para não revelar quem tem conta), e
    o Django não envia nada para conta sem senha local (criada pelo Google ou
    GitHub). Sem este registro, um e-mail que "não chegou" não deixa pista.
    O endereço digitado não vai para o log, só as contagens.
    """

    def get_users(self, email):
        usuarios = list(super().get_users(email))
        if usuarios:
            logger.info('Recuperação de senha: enviando e-mail para %d conta(s).', len(usuarios))
        else:
            contas = User.objects.filter(email__iexact=email, is_active=True)
            logger.info(
                'Recuperação de senha: nada enviado (%d conta(s) ativa(s) com este e-mail, '
                'nenhuma com senha local).', contas.count(),
            )
        return usuarios
