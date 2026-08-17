from decimal import Decimal

from django.views.generic.edit import FormView

from .forms import JurosCompostosForm


class JurosCompostosView(FormView):
    template_name = 'simuladores/juros_compostos.html'
    form_class = JurosCompostosForm

    def form_valid(self, form):
        dados = form.cleaned_data
        contexto = self.get_context_data(form=form)
        contexto['resultado'] = self._calcular(dados)
        return self.render_to_response(contexto)

    @staticmethod
    def _calcular(dados):
        """Simula a evolução mês a mês com aportes e juros compostos.

        Retorna a lista de linhas (uma por mês) e os totais finais, para que o
        usuário leigo veja como o valor cresce ao longo do tempo, não só o
        resultado final.
        """
        saldo = dados['valor_inicial']
        aporte = dados.get('aporte_mensal') or Decimal('0')
        taxa = dados['taxa_mensal'] / Decimal('100')
        meses = dados['periodo_meses']

        total_aportado = dados['valor_inicial']
        linhas = []
        pontos_grafico = [{'mes': 0, 'saldo': float(saldo.quantize(Decimal('0.01')))}]
        for mes in range(1, meses + 1):
            saldo += aporte
            juros_do_mes = saldo * taxa
            saldo += juros_do_mes
            total_aportado += aporte
            saldo_arredondado = saldo.quantize(Decimal('0.01'))
            linhas.append({
                'mes': mes,
                'juros_do_mes': juros_do_mes.quantize(Decimal('0.01')),
                'saldo': saldo_arredondado,
            })
            pontos_grafico.append({'mes': mes, 'saldo': float(saldo_arredondado)})

        total_juros = saldo - total_aportado
        return {
            'linhas': linhas,
            'pontos_grafico': pontos_grafico,
            'saldo_final': saldo.quantize(Decimal('0.01')),
            'total_aportado': total_aportado.quantize(Decimal('0.01')),
            'total_juros': total_juros.quantize(Decimal('0.01')),
        }
