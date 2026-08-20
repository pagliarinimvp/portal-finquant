from django import forms

from .models import Avaliacao


class AvaliacaoForm(forms.ModelForm):
    # Todos os campos de escolha abaixo são declarados explicitamente (em vez
    # de deixar o ModelForm gerar o campo sozinho) para evitar a opção em
    # branco que o Django adiciona por padrão quando o campo do model não tem
    # um "default" definido.
    nota = forms.TypedChoiceField(
        label='Navegação no site',
        choices=Avaliacao.Nota.choices,
        coerce=int,
        widget=forms.RadioSelect(attrs={'class': 'form-check-input'}),
        required=True,
        error_messages={'required': 'Selecione uma nota.'},
    )
    faixa_etaria = forms.ChoiceField(
        label='Faixa etária',
        choices=Avaliacao.FaixaEtaria.choices,
        widget=forms.Select(attrs={'class': 'form-select'}),
        required=True,
        error_messages={'required': 'Selecione sua faixa etária.'},
    )
    sexo = forms.ChoiceField(
        label='Sexo',
        choices=Avaliacao.Sexo.choices,
        widget=forms.Select(attrs={'class': 'form-select'}),
        required=True,
        error_messages={'required': 'Selecione uma opção.'},
    )
    experiencia_investimentos = forms.TypedChoiceField(
        label='Experiência prévia com investimentos',
        choices=Avaliacao.ExperienciaInvestimentos.choices,
        coerce=int,
        widget=forms.RadioSelect(attrs={'class': 'form-check-input'}),
        required=True,
        error_messages={'required': 'Selecione sua experiência com investimentos.'},
    )
    conteudo_ajudou = forms.TypedChoiceField(
        label='O conteúdo do site ajudou a melhorar seu conhecimento sobre o assunto?',
        choices=Avaliacao.ConteudoAjudou.choices,
        coerce=int,
        widget=forms.RadioSelect(attrs={'class': 'form-check-input'}),
        required=True,
        error_messages={'required': 'Selecione uma opção.'},
    )
    faixa_renda_familiar = forms.ChoiceField(
        label='Faixa de renda familiar',
        choices=Avaliacao.FaixaRendaFamiliar.choices,
        widget=forms.Select(attrs={'class': 'form-select'}),
        required=True,
        error_messages={'required': 'Selecione sua faixa de renda familiar.'},
    )

    class Meta:
        model = Avaliacao
        fields = [
            'faixa_etaria', 'sexo', 'experiencia_investimentos',
            'conteudo_ajudou', 'faixa_renda_familiar', 'nota', 'comentario',
        ]
        widgets = {
            'comentario': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
        }
