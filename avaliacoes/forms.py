from django import forms

from .models import Avaliacao


class AvaliacaoForm(forms.ModelForm):
    # Declarado explicitamente (em vez de deixar o ModelForm gerar o campo
    # sozinho) para evitar a opção em branco que o Django adiciona por padrão
    # quando o campo do model não tem um "default" definido.
    nota = forms.TypedChoiceField(
        label='Nota',
        choices=Avaliacao.Nota.choices,
        coerce=int,
        widget=forms.RadioSelect,
        required=True,
        error_messages={'required': 'Selecione uma nota.'},
    )

    class Meta:
        model = Avaliacao
        fields = ['nota', 'comentario']
        widgets = {
            'comentario': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
        }
