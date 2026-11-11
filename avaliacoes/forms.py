from django import forms

from .models import Avaliacao


def _com_selecione(choices):
    """Põe "Selecione…" vazio no topo de uma lista suspensa.

    Sem isso o navegador já abre a lista na primeira opção, e quem não mexe
    no campo envia "Até R$ 2.000" ou "Masculino" sem ter escolhido, o que
    distorce a pesquisa. Com o vazio, o required=True barra o envio.
    """
    return [('', 'Selecione…')] + list(choices)


FAIXAS_ETARIAS_ACEITAS = [
    (valor, rotulo) for valor, rotulo in Avaliacao.FaixaEtaria.choices
    if valor != Avaliacao.FaixaEtaria.ATE_18
]


class AvaliacaoForm(forms.ModelForm):
    # Todos os campos de escolha abaixo são declarados explicitamente (em vez
    # de deixar o ModelForm gerar o campo sozinho) para evitar a opção em
    # branco que o Django adiciona por padrão quando o campo do model não tem
    # um "default" definido.
    nota = forms.TypedChoiceField(
        label='Como você avalia a navegação no site?',
        choices=Avaliacao.Nota.choices,
        coerce=int,
        widget=forms.RadioSelect(attrs={'class': 'form-check-input'}),
        required=True,
        error_messages={'required': 'Selecione uma nota.'},
    )
    faixa_etaria = forms.ChoiceField(
        label='Faixa etária',
        choices=_com_selecione(FAIXAS_ETARIAS_ACEITAS),
        widget=forms.Select(attrs={'class': 'form-select'}),
        required=True,
        error_messages={'required': 'Selecione sua faixa etária.'},
    )
    sexo = forms.ChoiceField(
        label='Sexo',
        choices=_com_selecione(Avaliacao.Sexo.choices),
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
        label='Faixa de renda familiar mensal',
        choices=_com_selecione(Avaliacao.FaixaRendaFamiliar.choices),
        widget=forms.Select(attrs={'class': 'form-select'}),
        required=True,
        error_messages={'required': 'Selecione sua faixa de renda familiar mensal.'},
    )

    # O BooleanField do model vira um campo opcional no ModelForm; aqui ele é
    # obrigatório, porque sem o consentimento a resposta não pode ser usada.
    consentimento = forms.BooleanField(
        label='Tenho 18 anos ou mais, li o aviso de privacidade acima e concordo em participar da pesquisa.',
        required=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        error_messages={'required': 'Para enviar, confirme que tem 18 anos ou mais e concorda em participar.'},
    )

    class Meta:
        model = Avaliacao
        # Mesma ordem da página (desde 10/11/2026): opinião primeiro, perfil no fim.
        fields = [
            'nota', 'conteudo_ajudou', 'comentario',
            'experiencia_investimentos', 'faixa_etaria', 'sexo', 'faixa_renda_familiar',
            'consentimento',
        ]
        widgets = {
            'comentario': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
        }


class AvaliacaoArtigoForm(forms.Form):
    """"Este artigo te ajudou?": os botões Sim e Não enviam ajudou=1 ou ajudou=0."""

    ajudou = forms.TypedChoiceField(choices=[('1', 'Sim'), ('0', 'Não')], coerce=lambda valor: valor == '1')
    comentario = forms.CharField(required=False, max_length=1000)
