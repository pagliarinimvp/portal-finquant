from decimal import Decimal

from django.test import TestCase

from .views import DividaCartaoView, JurosCompostosView, MetaFinanceiraView


class DividaCartaoCalculoTests(TestCase):
    def test_quita_em_quatro_meses(self):
        resultado = DividaCartaoView._calcular({
            'saldo_devedor': Decimal('1000'),
            'taxa_mensal': Decimal('5'),
            'pagamento_mensal': Decimal('350'),
        })

        self.assertTrue(resultado['quitada'])
        self.assertFalse(resultado['nunca_quita'])
        self.assertEqual(resultado['meses_para_quitar'], 4)
        self.assertEqual(len(resultado['linhas']), 4)
        self.assertEqual(resultado['total_pago'], Decimal('1106.96'))
        self.assertEqual(resultado['total_juros'], Decimal('106.96'))
        self.assertEqual(resultado['saldo_final'], Decimal('0.00'))

    def test_pagamento_nao_cobre_juros_nunca_quita(self):
        resultado = DividaCartaoView._calcular({
            'saldo_devedor': Decimal('1000'),
            'taxa_mensal': Decimal('10'),
            'pagamento_mensal': Decimal('90'),
        })

        self.assertTrue(resultado['nunca_quita'])
        self.assertFalse(resultado['quitada'])
        self.assertIsNone(resultado['meses_para_quitar'])
        self.assertEqual(len(resultado['linhas']), 600)
        self.assertGreater(resultado['saldo_final'], Decimal('1000'))

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
