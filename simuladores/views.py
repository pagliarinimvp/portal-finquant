from decimal import ROUND_HALF_UP, ROUND_UP, Decimal, localcontext

from django.views.generic import TemplateView
from django.views.generic.edit import FormView

from .forms import DividaCartaoForm, JurosCompostosForm, MetaFinanceiraForm

TETO_MESES = 600

# Valores em reais vão para o centavo com ROUND_HALF_UP, o arredondamento
# comercial (0,125 -> 0,13). O padrão do Decimal é ROUND_HALF_EVEN, que
# arredonda o meio para o par (0,125 -> 0,12) e diverge de bancos e calculadoras.
CENTAVO = Decimal('0.01')


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
        pontos_grafico = [{'mes': 0, 'saldo': float(saldo.quantize(CENTAVO, rounding=ROUND_HALF_UP))}]
        for mes in range(1, meses + 1):
            saldo += aporte
            juros_do_mes = saldo * taxa
            saldo += juros_do_mes
            total_aportado += aporte
            saldo_arredondado = saldo.quantize(CENTAVO, rounding=ROUND_HALF_UP)
            linhas.append({
                'mes': mes,
                'juros_do_mes': juros_do_mes.quantize(CENTAVO, rounding=ROUND_HALF_UP),
                'saldo': saldo_arredondado,
            })
            pontos_grafico.append({'mes': mes, 'saldo': float(saldo_arredondado)})

        total_juros = saldo - total_aportado
        return {
            'linhas': linhas,
            'pontos_grafico': pontos_grafico,
            'saldo_final': saldo.quantize(CENTAVO, rounding=ROUND_HALF_UP),
            'total_aportado': total_aportado.quantize(CENTAVO, rounding=ROUND_HALF_UP),
            'total_juros': total_juros.quantize(CENTAVO, rounding=ROUND_HALF_UP),
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
        em seguida, replicando como uma fatura de cartão funciona.

        Aplica o teto da Lei 14.690/2023 (em vigor desde 03/01/2024): os juros
        e encargos do rotativo somados não podem passar de 100% do valor
        original da dívida. Quando o total de juros chega a esse teto, os
        juros param e cada pagamento passa a abater só o saldo — por isso,
        mesmo um pagamento que não cobre os juros do mês acaba quitando a
        dívida (o que antes da lei não aconteceria nunca). A simulação ainda
        para em TETO_MESES para pagamentos muito pequenos.
        """
        saldo = dados['saldo_devedor']
        taxa = dados['taxa_mensal'] / Decimal('100')
        pagamento = dados['pagamento_mensal']
        teto_juros = dados['saldo_devedor']

        linhas = []
        pontos_grafico = [{'mes': 0, 'saldo': float(saldo.quantize(CENTAVO, rounding=ROUND_HALF_UP))}]
        total_pago = Decimal('0')
        total_juros = Decimal('0')
        pagamento_nao_cobre_juros = False
        mes_teto = None

        # Precisão elevada por segurança: com o teto o saldo no máximo dobra,
        # mas sem ele o saldo composto por TETO_MESES meses estouraria as ~28
        # casas do contexto padrão de Decimal no `quantize` final.
        with localcontext() as ctx:
            ctx.prec = 60
            mes = 0
            while saldo > Decimal('0.01') and mes < TETO_MESES:
                mes += 1
                juros_calculado = (saldo * taxa).quantize(CENTAVO, rounding=ROUND_HALF_UP)
                if mes == 1 and pagamento <= juros_calculado:
                    pagamento_nao_cobre_juros = True
                juros_do_mes = min(juros_calculado, teto_juros - total_juros)
                if mes_teto is None and juros_calculado > 0 and total_juros + juros_do_mes >= teto_juros:
                    mes_teto = mes
                saldo += juros_do_mes
                pagamento_efetivo = min(pagamento, saldo)
                saldo -= pagamento_efetivo

                total_juros += juros_do_mes
                total_pago += pagamento_efetivo

                saldo_arredondado = saldo.quantize(CENTAVO, rounding=ROUND_HALF_UP)
                linhas.append({
                    'mes': mes,
                    'juros_do_mes': juros_do_mes,
                    'pagamento': pagamento_efetivo,
                    'saldo': saldo_arredondado,
                })
                pontos_grafico.append({'mes': mes, 'saldo': float(saldo_arredondado)})

            quitada = saldo <= Decimal('0.01')

            return {
                'linhas': linhas,
                'pontos_grafico': pontos_grafico,
                'meses_para_quitar': mes if quitada else None,
                'total_pago': total_pago.quantize(CENTAVO, rounding=ROUND_HALF_UP),
                'total_juros': total_juros.quantize(CENTAVO, rounding=ROUND_HALF_UP),
                'saldo_final': saldo.quantize(CENTAVO, rounding=ROUND_HALF_UP),
                'quitada': quitada,
                'pagamento_nao_cobre_juros': pagamento_nao_cobre_juros,
                'teto_juros': teto_juros.quantize(CENTAVO, rounding=ROUND_HALF_UP),
                'mes_teto': mes_teto,
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
        # Arredonda para cima: arredondar para o centavo mais próximo deixava o
        # saldo final alguns centavos abaixo da meta em boa parte dos casos.
        aporte_projecao = max(aporte_necessario, Decimal('0')).quantize(CENTAVO, rounding=ROUND_UP)

        saldo = valor_inicial
        linhas = []
        pontos_grafico = [{'mes': 0, 'saldo': float(saldo.quantize(CENTAVO, rounding=ROUND_HALF_UP))}]
        for mes in range(1, meses + 1):
            saldo += aporte_projecao
            juros_do_mes = saldo * taxa
            saldo += juros_do_mes
            saldo_arredondado = saldo.quantize(CENTAVO, rounding=ROUND_HALF_UP)
            linhas.append({
                'mes': mes,
                'juros_do_mes': juros_do_mes.quantize(CENTAVO, rounding=ROUND_HALF_UP),
                'saldo': saldo_arredondado,
            })
            pontos_grafico.append({'mes': mes, 'saldo': float(saldo_arredondado)})

        total_aportado = (aporte_projecao * meses).quantize(CENTAVO, rounding=ROUND_HALF_UP)
        total_juros_projetado = (saldo - valor_inicial - total_aportado).quantize(CENTAVO, rounding=ROUND_HALF_UP)

        return {
            'linhas': linhas,
            'pontos_grafico': pontos_grafico,
            'aporte_necessario': aporte_projecao,
            'meta_ja_atingida': meta_ja_atingida,
            'saldo_final_projetado': saldo.quantize(CENTAVO, rounding=ROUND_HALF_UP),
            'valor_meta': valor_meta,
            'total_aportado': total_aportado,
            'total_juros_projetado': total_juros_projetado,
        }


class SimuladoresIndexView(TemplateView):
    template_name = 'simuladores/index.html'
