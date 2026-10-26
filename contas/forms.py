from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User


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
