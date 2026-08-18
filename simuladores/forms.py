from decimal import Decimal

from django import forms


class JurosCompostosForm(forms.Form):
    valor_inicial = forms.DecimalField(
        label='Valor inicial (R$)', min_value=0, max_digits=12, decimal_places=2,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
    )
    aporte_mensal = forms.DecimalField(
        label='Aporte mensal (R$)', min_value=0, max_digits=12, decimal_places=2, required=False, initial=0,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
    )
    taxa_mensal = forms.DecimalField(
        label='Taxa de juros mensal (%)', min_value=0, max_digits=6, decimal_places=2,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
    )
    periodo_meses = forms.IntegerField(
        label='Período (meses)', min_value=1, max_value=600,
        widget=forms.NumberInput(attrs={'class': 'form-control'}),
    )


class DividaCartaoForm(forms.Form):
    saldo_devedor = forms.DecimalField(
        label='Saldo devedor atual (R$)', min_value=Decimal('0.01'), max_digits=12, decimal_places=2,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
    )
    taxa_mensal = forms.DecimalField(
        label='Taxa de juros do rotativo (% ao mês)', min_value=0, max_digits=6, decimal_places=2,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
    )
    pagamento_mensal = forms.DecimalField(
        label='Quanto pretende pagar por mês (R$)', min_value=Decimal('0.01'), max_digits=12, decimal_places=2,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
    )


class MetaFinanceiraForm(forms.Form):
    valor_inicial = forms.DecimalField(
        label='Valor já guardado hoje (R$)', min_value=0, max_digits=12, decimal_places=2, required=False, initial=0,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
    )
    valor_meta = forms.DecimalField(
        label='Valor da meta (R$)', min_value=Decimal('0.01'), max_digits=12, decimal_places=2,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
    )
    taxa_mensal = forms.DecimalField(
        label='Taxa de juros mensal esperada (%)', min_value=0, max_digits=6, decimal_places=2,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
    )
    periodo_meses = forms.IntegerField(
        label='Prazo (meses)', min_value=1, max_value=600,
        widget=forms.NumberInput(attrs={'class': 'form-control'}),
    )
