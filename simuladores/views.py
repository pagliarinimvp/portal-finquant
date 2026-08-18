from decimal import Decimal, localcontext

from django.views.generic import TemplateView
from django.views.generic.edit import FormView

from .forms import DividaCartaoForm, JurosCompostosForm, MetaFinanceiraForm

TETO_MESES = 600


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


class DividaCartaoView(FormView):
    template_name = 'simuladores/divida_cartao.html'
    form_class = DividaCartaoForm

    def form_valid(self, form):
        dados = form.cleaned_data
        contexto = self.get_context_data(form=form)
        contexto['resultado'] = self._calcular(dados)
        return self.render_to_response(contexto)

    @staticmethod
    def _calcular(dados):
        """Simula a evolução mês a mês do saldo devedor do rotativo do cartão.

        Juros incidem sobre o saldo do início do mês e o pagamento é abatido
        em seguida, replicando como uma fatura de cartão funciona. Se o
        pagamento não superar os juros do primeiro mês, a dívida nunca é
        quitada — a simulação roda até um teto de meses para deixar isso
        visualmente claro no gráfico, em vez de tentar achar um fim que não
        existe.
        """
        saldo = dados['saldo_devedor']
        taxa = dados['taxa_mensal'] / Decimal('100')
        pagamento = dados['pagamento_mensal']

        linhas = []
        pontos_grafico = [{'mes': 0, 'saldo': float(saldo.quantize(Decimal('0.01')))}]
        total_pago = Decimal('0')
        total_juros = Decimal('0')
        nunca_quita = False

        # Precisão elevada: no caso "nunca quita", o saldo é composto por até
        # TETO_MESES meses sem nunca diminuir e pode ultrapassar as ~28 casas
        # significativas do contexto padrão de Decimal, o que faria o
        # `quantize` final falhar com InvalidOperation.
        with localcontext() as ctx:
            ctx.prec = 60
            mes = 0
            while saldo > Decimal('0.01') and mes < TETO_MESES:
                mes += 1
                juros_do_mes = (saldo * taxa).quantize(Decimal('0.01'))
                saldo += juros_do_mes
                if mes == 1 and pagamento <= juros_do_mes:
                    nunca_quita = True
                pagamento_efetivo = min(pagamento, saldo)
                saldo -= pagamento_efetivo

                total_juros += juros_do_mes
                total_pago += pagamento_efetivo

                saldo_arredondado = saldo.quantize(Decimal('0.01'))
                linhas.append({
                    'mes': mes,
                    'juros_do_mes': juros_do_mes,
                    'pagamento': pagamento_efetivo,
                    'saldo': saldo_arredondado,
                })
                pontos_grafico.append({'mes': mes, 'saldo': float(saldo_arredondado)})

            quitada = saldo <= Decimal('0.01') and not nunca_quita

            return {
                'linhas': linhas,
                'pontos_grafico': pontos_grafico,
                'meses_para_quitar': mes if quitada else None,
                'total_pago': total_pago.quantize(Decimal('0.01')),
                'total_juros': total_juros.quantize(Decimal('0.01')),
                'saldo_final': saldo.quantize(Decimal('0.01')),
                'quitada': quitada,
                'nunca_quita': nunca_quita,
            }


class MetaFinanceiraView(FormView):
    template_name = 'simuladores/meta_financeira.html'
    form_class = MetaFinanceiraForm

    def form_valid(self, form):
        dados = form.cleaned_data
        contexto = self.get_context_data(form=form)
        contexto['resultado'] = self._calcular(dados)
        return self.render_to_response(contexto)

    @staticmethod
    def _calcular(dados):
        """Calcula o aporte mensal necessário para atingir uma meta financeira.

        Resolve a fórmula de valor futuro de uma série de aportes mensais
        para o valor do aporte (PMT), usando a mesma ordem de operações do
        simulador de juros compostos (o aporte entra antes dos juros do mês),
        e depois projeta a evolução mês a mês com esse aporte para montar o
        mesmo tipo de tabela/gráfico.
        """
        valor_inicial = dados.get('valor_inicial') or Decimal('0')
        valor_meta = dados['valor_meta']
        taxa = dados['taxa_mensal'] / Decimal('100')
        meses = dados['periodo_meses']

        fator = (Decimal('1') + taxa) ** meses
        if taxa == 0:
            aporte_necessario = (valor_meta - valor_inicial) / Decimal(meses)
        else:
            fator_anuidade = ((fator - 1) / taxa) * (Decimal('1') + taxa)
            aporte_necessario = (valor_meta - valor_inicial * fator) / fator_anuidade

        meta_ja_atingida = aporte_necessario <= 0
        aporte_projecao = max(aporte_necessario, Decimal('0')).quantize(Decimal('0.01'))

        saldo = valor_inicial
        linhas = []
        pontos_grafico = [{'mes': 0, 'saldo': float(saldo.quantize(Decimal('0.01')))}]
        for mes in range(1, meses + 1):
            saldo += aporte_projecao
            juros_do_mes = saldo * taxa
            saldo += juros_do_mes
            saldo_arredondado = saldo.quantize(Decimal('0.01'))
            linhas.append({
                'mes': mes,
                'juros_do_mes': juros_do_mes.quantize(Decimal('0.01')),
                'saldo': saldo_arredondado,
            })
            pontos_grafico.append({'mes': mes, 'saldo': float(saldo_arredondado)})

        total_aportado = (aporte_projecao * meses).quantize(Decimal('0.01'))
        total_juros_projetado = (saldo - valor_inicial - total_aportado).quantize(Decimal('0.01'))

        return {
            'linhas': linhas,
            'pontos_grafico': pontos_grafico,
            'aporte_necessario': aporte_projecao,
            'meta_ja_atingida': meta_ja_atingida,
            'saldo_final_projetado': saldo.quantize(Decimal('0.01')),
            'valor_meta': valor_meta,
            'total_aportado': total_aportado,
            'total_juros_projetado': total_juros_projetado,
        }


class SimuladoresIndexView(TemplateView):
    template_name = 'simuladores/index.html'
