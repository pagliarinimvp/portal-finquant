from decimal import Decimal

from django import forms

PERIODO_TAXA_CHOICES = [('mensal', 'ao mês'), ('anual', 'ao ano')]


def taxa_anual_para_mensal(taxa_anual):
    """Converte uma taxa anual (em %) na taxa mensal equivalente (em %).

    Juros compostos: (1 + taxa mensal)^12 = 1 + taxa anual, então a taxa
    mensal é (1 + taxa anual)^(1/12) − 1. Dividir por 12 superestimaria o
    resultado, porque ignora os juros sobre juros dentro do ano.
    """
    fator_anual = Decimal('1') + taxa_anual / Decimal('100')
    return (fator_anual ** (Decimal('1') / Decimal('12')) - Decimal('1')) * Decimal('100')


def campo_periodo_taxa():
    return forms.ChoiceField(
        label='A taxa informada é', choices=PERIODO_TAXA_CHOICES, initial='mensal',
        widget=forms.Select(attrs={'class': 'form-select'}),
    )


class TaxaComPeriodoMixin:
    """Aceita a taxa ao mês ou ao ano e sempre entrega `taxa_mensal` ao cálculo.

    Leigos costumam conhecer a taxa anual (CDI, Selic, poupança); os cálculos
    dos simuladores são mês a mês, então a taxa anual é convertida aqui e o
    `_calcular` de cada view continua recebendo só a taxa mensal.
    """

    def clean(self):
        dados = super().clean()
        if dados.get('taxa_mensal') is not None and dados.get('periodo_taxa') == 'anual':
            dados['taxa_mensal'] = taxa_anual_para_mensal(dados['taxa_mensal'])
        return dados


class JurosCompostosForm(TaxaComPeriodoMixin, forms.Form):
    valor_inicial = forms.DecimalField(
        label='Valor inicial (R$)', min_value=0, max_digits=12, decimal_places=2,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
    )
    aporte_mensal = forms.DecimalField(
        label='Aporte mensal (R$)', min_value=0, max_digits=12, decimal_places=2, required=False, initial=0,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
    )
    taxa_mensal = forms.DecimalField(
        label='Taxa de juros (%)', min_value=0, max_digits=6, decimal_places=2,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
    )
    periodo_taxa = campo_periodo_taxa()
    periodo_meses = forms.IntegerField(
        label='Período (meses)', min_value=1, max_value=600,
        widget=forms.NumberInput(attrs={'class': 'form-control'}),
    )


class DividaCartaoForm(TaxaComPeriodoMixin, forms.Form):
    saldo_devedor = forms.DecimalField(
        label='Saldo devedor atual (R$)', min_value=Decimal('0.01'), max_digits=12, decimal_places=2,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
    )
    taxa_mensal = forms.DecimalField(
        label='Taxa de juros do rotativo (%)', min_value=0, max_digits=6, decimal_places=2,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
    )
    periodo_taxa = campo_periodo_taxa()
    pagamento_mensal = forms.DecimalField(
        label='Quanto pretende pagar por mês (R$)', min_value=Decimal('0.01'), max_digits=12, decimal_places=2,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
    )


class MetaFinanceiraForm(TaxaComPeriodoMixin, forms.Form):
    valor_inicial = forms.DecimalField(
        label='Valor já guardado hoje (R$)', min_value=0, max_digits=12, decimal_places=2, required=False, initial=0,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
    )
    valor_meta = forms.DecimalField(
        label='Valor da meta (R$)', min_value=Decimal('0.01'), max_digits=12, decimal_places=2,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
    )
    taxa_mensal = forms.DecimalField(
        label='Taxa de juros esperada (%)', min_value=0, max_digits=6, decimal_places=2,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
    )
    periodo_taxa = campo_periodo_taxa()
    periodo_meses = forms.IntegerField(
        label='Prazo (meses)', min_value=1, max_value=600,
        widget=forms.NumberInput(attrs={'class': 'form-control'}),
    )
