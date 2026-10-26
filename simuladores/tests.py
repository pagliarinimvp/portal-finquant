from decimal import Decimal

from django.test import TestCase

from .forms import JurosCompostosForm, taxa_anual_para_mensal
from .views import DividaCartaoView, JurosCompostosView, MetaFinanceiraView


class ConversaoTaxaTests(TestCase):
    def test_exemplo_do_painel_12_68_ao_ano_e_1_ao_mes(self):
        self.assertAlmostEqual(taxa_anual_para_mensal(Decimal('12.68')), Decimal('1'), places=3)

    def test_taxa_zero_continua_zero(self):
        self.assertEqual(taxa_anual_para_mensal(Decimal('0')), Decimal('0'))

    def test_form_converte_taxa_anual_e_mantem_a_mensal(self):
        base = {'valor_inicial': '1000', 'aporte_mensal': '0', 'taxa_mensal': '12.68', 'periodo_meses': '12'}

        anual = JurosCompostosForm({**base, 'periodo_taxa': 'anual'})
        mensal = JurosCompostosForm({**base, 'periodo_taxa': 'mensal'})

        self.assertTrue(anual.is_valid())
        self.assertTrue(mensal.is_valid())
        self.assertAlmostEqual(anual.cleaned_data['taxa_mensal'], Decimal('1'), places=3)
        self.assertEqual(mensal.cleaned_data['taxa_mensal'], Decimal('12.68'))

    def test_um_ano_a_taxa_anual_rende_a_propria_taxa(self):
        form = JurosCompostosForm({
            'valor_inicial': '1000', 'aporte_mensal': '0', 'taxa_mensal': '10',
            'periodo_taxa': 'anual', 'periodo_meses': '12',
        })
        self.assertTrue(form.is_valid())

        resultado = JurosCompostosView._calcular(form.cleaned_data)

        self.assertEqual(resultado['saldo_final'], Decimal('1100.00'))


class JurosCompostosCalculoTests(TestCase):
    def test_exemplo_do_painel_como_calculamos_isso(self):
        resultado = JurosCompostosView._calcular({
            'valor_inicial': Decimal('1000'),
            'aporte_mensal': Decimal('100'),
            'taxa_mensal': Decimal('1'),
            'periodo_meses': 3,
        })

        self.assertEqual(resultado['saldo_final'], Decimal('1336.34'))
        self.assertEqual(resultado['total_aportado'], Decimal('1300.00'))
        self.assertEqual(resultado['total_juros'], Decimal('36.34'))


class DividaCartaoCalculoTests(TestCase):
    def test_quita_em_quatro_meses(self):
        resultado = DividaCartaoView._calcular({
            'saldo_devedor': Decimal('1000'),
            'taxa_mensal': Decimal('5'),
            'pagamento_mensal': Decimal('350'),
        })

        self.assertTrue(resultado['quitada'])
        self.assertFalse(resultado['pagamento_nao_cobre_juros'])
        self.assertEqual(resultado['meses_para_quitar'], 4)
        self.assertEqual(len(resultado['linhas']), 4)
        self.assertEqual(resultado['total_pago'], Decimal('1106.96'))
        self.assertEqual(resultado['total_juros'], Decimal('106.96'))
        self.assertEqual(resultado['saldo_final'], Decimal('0.00'))

    def test_pagamento_nao_cobre_juros_para_no_teto_da_lei(self):
        # Lei 14.690/2023: os juros somados param em 100% do valor original,
        # então a dívida de R$ 1.000 custa no máximo R$ 2.000 e acaba quitada.
        resultado = DividaCartaoView._calcular({
            'saldo_devedor': Decimal('1000'),
            'taxa_mensal': Decimal('10'),
            'pagamento_mensal': Decimal('90'),
        })

        self.assertTrue(resultado['pagamento_nao_cobre_juros'])
        self.assertTrue(resultado['quitada'])
        self.assertEqual(resultado['total_juros'], Decimal('1000.00'))
        self.assertEqual(resultado['total_pago'], Decimal('2000.00'))
        self.assertEqual(resultado['mes_teto'], 10)
        self.assertEqual(resultado['meses_para_quitar'], 23)

    def test_juros_abaixo_do_teto_nao_marcam_mes_teto(self):
        resultado = DividaCartaoView._calcular({
            'saldo_devedor': Decimal('1000'),
            'taxa_mensal': Decimal('5'),
            'pagamento_mensal': Decimal('350'),
        })

        self.assertIsNone(resultado['mes_teto'])
        self.assertFalse(resultado['pagamento_nao_cobre_juros'])

    def test_pagamento_minusculo_nao_quita_em_50_anos(self):
        resultado = DividaCartaoView._calcular({
            'saldo_devedor': Decimal('10000'),
            'taxa_mensal': Decimal('10'),
            'pagamento_mensal': Decimal('1'),
        })

        self.assertFalse(resultado['quitada'])
        self.assertIsNone(resultado['meses_para_quitar'])
        self.assertEqual(len(resultado['linhas']), 600)
        self.assertEqual(resultado['total_juros'], Decimal('10000.00'))

    def test_quita_no_primeiro_mes_sem_saldo_negativo(self):
        resultado = DividaCartaoView._calcular({
            'saldo_devedor': Decimal('1000'),
            'taxa_mensal': Decimal('5'),
            'pagamento_mensal': Decimal('1050'),
        })

        self.assertTrue(resultado['quitada'])
        self.assertEqual(resultado['meses_para_quitar'], 1)
        self.assertEqual(resultado['saldo_final'], Decimal('0.00'))


class MetaFinanceiraCalculoTests(TestCase):
    def test_taxa_zero_e_divisao_simples(self):
        resultado = MetaFinanceiraView._calcular({
            'valor_inicial': Decimal('0'),
            'valor_meta': Decimal('1000'),
            'taxa_mensal': Decimal('0'),
            'periodo_meses': 10,
        })

        self.assertFalse(resultado['meta_ja_atingida'])
        self.assertEqual(resultado['aporte_necessario'], Decimal('100.00'))

    def test_com_juros_aporte_aproximado(self):
        resultado = MetaFinanceiraView._calcular({
            'valor_inicial': Decimal('0'),
            'valor_meta': Decimal('1000'),
            'taxa_mensal': Decimal('1'),
            'periodo_meses': 12,
        })

        self.assertEqual(resultado['aporte_necessario'], Decimal('78.07'))

    def test_meta_ja_atingida_com_valor_inicial(self):
        resultado = MetaFinanceiraView._calcular({
            'valor_inicial': Decimal('2000'),
            'valor_meta': Decimal('1000'),
            'taxa_mensal': Decimal('1'),
            'periodo_meses': 12,
        })

        self.assertTrue(resultado['meta_ja_atingida'])
        self.assertEqual(resultado['aporte_necessario'], Decimal('0.00'))

    def test_round_trip_com_simulador_de_juros_compostos(self):
        meta = MetaFinanceiraView._calcular({
            'valor_inicial': Decimal('0'),
            'valor_meta': Decimal('1000'),
            'taxa_mensal': Decimal('1'),
            'periodo_meses': 12,
        })

        projecao = JurosCompostosView._calcular({
            'valor_inicial': Decimal('0'),
            'aporte_mensal': meta['aporte_necessario'],
            'taxa_mensal': Decimal('1'),
            'periodo_meses': 12,
        })

        diferenca = abs(projecao['saldo_final'] - Decimal('1000'))
        self.assertLessEqual(diferenca, Decimal('0.05'))

    def test_saldo_final_nunca_fica_abaixo_da_meta(self):
        # Com arredondamento para o centavo mais próximo, estes casos
        # terminavam centavos abaixo da meta; o aporte agora sobe para cima.
        casos = [
            (Decimal('0'), Decimal('1000'), Decimal('1'), 12),
            (Decimal('1234'), Decimal('98765'), Decimal('0.87'), 137),
            (Decimal('500'), Decimal('3333'), Decimal('2.5'), 7),
            (Decimal('0'), Decimal('1000'), Decimal('0'), 3),
        ]
        for valor_inicial, valor_meta, taxa, meses in casos:
            with self.subTest(meta=valor_meta, taxa=taxa, meses=meses):
                resultado = MetaFinanceiraView._calcular({
                    'valor_inicial': valor_inicial,
                    'valor_meta': valor_meta,
                    'taxa_mensal': taxa,
                    'periodo_meses': meses,
                })
                self.assertGreaterEqual(resultado['saldo_final_projetado'], valor_meta)


class ArredondamentoComercialTests(TestCase):
    # R$ 12,50 a 1% dá R$ 0,125 de juros: meio centavo exato. O arredondamento
    # comercial (ROUND_HALF_UP) sobe para 0,13; o padrão do Decimal daria 0,12.
    def test_juros_compostos_arredonda_meio_centavo_para_cima(self):
        resultado = JurosCompostosView._calcular({
            'valor_inicial': Decimal('12.50'),
            'aporte_mensal': Decimal('0'),
            'taxa_mensal': Decimal('1'),
            'periodo_meses': 1,
        })

        self.assertEqual(resultado['linhas'][0]['juros_do_mes'], Decimal('0.13'))
        self.assertEqual(resultado['saldo_final'], Decimal('12.63'))

    def test_divida_arredonda_meio_centavo_para_cima(self):
        resultado = DividaCartaoView._calcular({
            'saldo_devedor': Decimal('12.50'),
            'taxa_mensal': Decimal('1'),
            'pagamento_mensal': Decimal('100'),
        })

        self.assertEqual(resultado['total_juros'], Decimal('0.13'))
        self.assertEqual(resultado['total_pago'], Decimal('12.63'))
