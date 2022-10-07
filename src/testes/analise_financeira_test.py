from tkinter.tix import Tree
import pandas as pd
import unittest

from ..aosol.analise.indicadores_autoconsumo import indicadores_autoconsumo
from ..aosol.analise import analise_financeira as af
from ..aosol.analise import analise_precos_energia as ape
from IPython.display import HTML, display_html

class TestAnaliseFinanceira(unittest.TestCase):
    def test_poupanca_anual(self):
        df = pd.DataFrame({'stamp':[
            '2022-01-01 00:00','2022-02-01 00:00','2022-03-01 00:00','2022-04-01 00:00',
            '2022-05-01 00:00','2022-06-01 00:00','2022-07-01 00:00','2022-08-01 00:00',
            '2022-09-01 00:00','2022-10-01 00:00','2022-11-01 00:00','2022-12-01 00:00',
        ],
        'consumo' :     [ 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2], 
        'consumo_rede' : [ 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0]})
        df['stamp'] = pd.to_datetime(df['stamp'])
        df = df.set_index('stamp')
        precos_energia = ape.TarifarioEnergia(True, custo_bi_kwh_fora_vazio=2.0, custo_bi_kwh_vazio=1.0)
        mensal = af.analise_poupanca_anual(df, ape.Tarifario.Bihorario, precos_energia, False)

        self.assertEqual(24.0, mensal.loc['Anual','fatura sem upac'])
        self.assertEqual(8.0, mensal.loc['Anual','fatura com upac'])
        self.assertEqual(16.0, mensal.loc['Anual','poupanca'])
        #print(df)
        print(mensal)

    def test_poupanca_anual_venda_rede(self):
        df = pd.DataFrame({'stamp':[
            '2022-01-01 00:00','2022-02-01 00:00','2022-03-01 00:00','2022-04-01 00:00',
            '2022-05-01 00:00','2022-06-01 00:00','2022-07-01 00:00','2022-08-01 00:00',
            '2022-09-01 00:00','2022-10-01 00:00','2022-11-01 00:00','2022-12-01 00:00',
        ],
        'consumo' :     [ 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2], 
        'consumo_rede' : [ 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0],
        'injeccao_rede': [ 0, 0, 0, 0, 1, 1, 1, 1, 0, 0, 0, 0]})
        df['stamp'] = pd.to_datetime(df['stamp'])
        df = df.set_index('stamp')
        precos_energia = ape.TarifarioEnergia(False, custo_bi_kwh_fora_vazio=2.0, custo_bi_kwh_vazio=1.0, preco_venda_kwh=1.0)
        mensal = af.analise_poupanca_anual(df, ape.Tarifario.Bihorario, precos_energia, True)

        self.assertEqual(24.0, mensal.loc['Anual','fatura sem upac'])
        self.assertEqual(8.0, mensal.loc['Anual','fatura com upac'])
        self.assertEqual(4.0, mensal.loc['Anual','venda a rede'])
        self.assertEqual(20.0, mensal.loc['Anual','poupanca'])

        print(mensal)

    def test_analise_financeira_projectos(self):
        df = pd.DataFrame({'stamp':[
            '2022-01-01 00:00','2022-02-01 00:00','2022-03-01 00:00','2022-04-01 00:00',
            '2022-05-01 00:00','2022-06-01 00:00','2022-07-01 00:00','2022-08-01 00:00',
            '2022-09-01 00:00','2022-10-01 00:00','2022-11-01 00:00','2022-12-01 00:00',
        ],
        'autoconsumo' : [ 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2]}) 
        #'consumo_rede' : [ 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0]})
        df['stamp'] = pd.to_datetime(df['stamp'])
        df = df.set_index('stamp')
        preco_energia = ape.TarifarioEnergia(1.0)

        fin, _ = af.analise_financeira_projecto(df, 60, 10, 1, 2021, 5, 0.0, 0.0, ape.Tarifario.Simples, preco_energia, False)
        self.assertAlmostEqual(7.948, fin.val, 3)
        self.assertAlmostEqual(5.3686, fin.tir, 4)
        self.assertAlmostEqual(4.4, fin.tempo_retorno, 1)
        self.assertAlmostEqual(0, fin.lcoe)

    def test_analise_financeira_com_degradacao_sistema(self):
        df = pd.DataFrame({'stamp':[
            '2022-01-01 00:00','2022-02-01 00:00','2022-03-01 00:00','2022-04-01 00:00',
            '2022-05-01 00:00','2022-06-01 00:00','2022-07-01 00:00','2022-08-01 00:00',
            '2022-09-01 00:00','2022-10-01 00:00','2022-11-01 00:00','2022-12-01 00:00',
        ],
        'autoconsumo' : [ 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2]}) 

        df['stamp'] = pd.to_datetime(df['stamp'])
        df = df.set_index('stamp')
        precos_energia = ape.TarifarioEnergia(1.0)

        # taxa degradacao = 0.7%
        fin, _ = af.analise_financeira_projecto(df, 60, 10, 1, 2021, 5, 0.7, 0.0, ape.Tarifario.Simples, precos_energia, False)
        self.assertAlmostEqual(6.658, fin.val, 3)
        self.assertAlmostEqual(4.703, fin.tir, 3)
        self.assertAlmostEqual(4.5, fin.tempo_retorno, 1)
        self.assertAlmostEqual(0, fin.lcoe)

    def test_analise_financeira_venda_rede(self):
        df = pd.DataFrame({'stamp':[
            '2022-01-01 00:00','2022-02-01 00:00','2022-03-01 00:00','2022-04-01 00:00',
            '2022-05-01 00:00','2022-06-01 00:00','2022-07-01 00:00','2022-08-01 00:00',
            '2022-09-01 00:00','2022-10-01 00:00','2022-11-01 00:00','2022-12-01 00:00',
        ],
        'autoconsumo' : [ 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2],
        'injeccao_rede' : [ 0, 0, 0, 0, 1, 1, 1, 1, 0, 0, 0, 0]})
        df['stamp'] = pd.to_datetime(df['stamp'])
        df = df.set_index('stamp')
        precos_energia = ape.TarifarioEnergia(1.0, preco_venda_kwh=1.0)

        fin, _ = af.analise_financeira_projecto(df, 60, 10, 1, 2021, 5, 0.0, 0.0, ape.Tarifario.Simples, precos_energia, True)
        self.assertAlmostEqual(27.362, fin.val, 3)
        self.assertAlmostEqual(15.238, fin.tir, 3)
        self.assertAlmostEqual(3.4, fin.tempo_retorno, 1)
        self.assertAlmostEqual(0, fin.lcoe)

    def test_analise_financeira_venda_rede_com_degradacao_sistema(self):
        df = pd.DataFrame({'stamp':[
            '2022-01-01 00:00','2022-02-01 00:00','2022-03-01 00:00','2022-04-01 00:00',
            '2022-05-01 00:00','2022-06-01 00:00','2022-07-01 00:00','2022-08-01 00:00',
            '2022-09-01 00:00','2022-10-01 00:00','2022-11-01 00:00','2022-12-01 00:00',
        ],
        'autoconsumo' : [ 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2],
        'injeccao_rede' : [ 0, 0, 0, 0, 1, 1, 1, 1, 0, 0, 0, 0]})
        df['stamp'] = pd.to_datetime(df['stamp'])
        df = df.set_index('stamp')
        precos_energia = ape.TarifarioEnergia(1.0, preco_venda_kwh=1.0)

        fin, _ = af.analise_financeira_projecto(df, 60, 10, 1, 2021, 5, 0.7, 0.0, ape.Tarifario.Simples, precos_energia, True)
        self.assertAlmostEqual(25.857, fin.val, 3)
        self.assertAlmostEqual(14.610, fin.tir, 3)
        self.assertAlmostEqual(3.4, fin.tempo_retorno, 1)
        self.assertAlmostEqual(0, fin.lcoe)

    def test_analise_financeira_venda_rede_com_degradacao_sistema_e_inflacao(self):
        df = pd.DataFrame({'stamp':[
            '2022-01-01 00:00','2022-02-01 00:00','2022-03-01 00:00','2022-04-01 00:00',
            '2022-05-01 00:00','2022-06-01 00:00','2022-07-01 00:00','2022-08-01 00:00',
            '2022-09-01 00:00','2022-10-01 00:00','2022-11-01 00:00','2022-12-01 00:00',
        ],
        'autoconsumo' : [ 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2],
        'injeccao_rede' : [ 0, 0, 0, 0, 1, 1, 1, 1, 0, 0, 0, 0]})
        df['stamp'] = pd.to_datetime(df['stamp'])
        df = df.set_index('stamp')

        preco_energia = ape.TarifarioEnergia(1.0, preco_venda_kwh=1.0)

        fin, _ = af.analise_financeira_projecto(df, 60, 10, 5, 2021, 5, 0.7, 2, ape.Tarifario.Simples, preco_energia, True)
        self.assertAlmostEqual(21.2696, fin.val, 4)

    def test_analise_financeira_indicadores_autoconsumo(self):
        energia_total = 2240
        energia_autoproduzida = 1400
        iac = 60.0
        energia_autoconsumida = energia_autoproduzida*iac/100.0
        energia_rede = energia_total-energia_autoconsumida
        custo_kwh = 0.1
        taxa_actualizacao = 5.0
        inflacao = 0.0
        indicadores = indicadores_autoconsumo(iac, None, 100.0-iac, 1.0, energia_autoproduzida, energia_autoconsumida, energia_rede, energia_total)

        #calc_tarifario = lambda en, ano, col : ape.calcula_tarifario_simples(en, 1, col)

        fin, _ = af.analise_financeira_projecto_indicadores_autoconsumo(indicadores, 60.0, 300.0, 5.0, taxa_actualizacao, 2022, 5, 0, inflacao, custo_kwh)

        self.assertAlmostEqual(42.03, fin.val, 2)

    def test_analise_financeira_indicadores_autoconsumo_com_venda_rede(self):
        energia_total = 2240
        energia_autoproduzida = 1400
        iac = 60.0
        energia_autoconsumida = energia_autoproduzida*iac/100.0
        energia_rede = energia_total-energia_autoconsumida
        custo_kwh = 0.1
        preco_kwh_venda_rede = 0.05
        taxa_actualizacao = 5.0
        inflacao = 0.0
        indicadores = indicadores_autoconsumo(iac, None, 100.0-iac, 1.0, energia_autoproduzida, energia_autoconsumida, energia_rede, energia_total)

        #calc_tarifario = lambda en, ano, col : ape.calcula_tarifario_simples(en, 1, col)

        fin, _ = af.analise_financeira_projecto_indicadores_autoconsumo(indicadores, 60.0, 300.0, 5.0, taxa_actualizacao, 2022, 5, 0, inflacao, custo_kwh, preco_kwh_venda_rede)

        self.assertAlmostEqual(163.25, fin.val, 2)

    def test_analise_financeira_indicadores_com_degradacao_sistema(self):
        energia_total = 2240
        energia_autoproduzida = 1400
        iac = 60.0
        energia_autoconsumida = energia_autoproduzida*iac/100.0
        energia_rede = energia_total-energia_autoconsumida
        custo_kwh = 0.1
        preco_kwh_venda_rede = 0.05
        taxa_actualizacao = 5.0
        taxa_degradacao = 0.7
        inflacao = 0.0
        indicadores = indicadores_autoconsumo(iac, None, 100.0-iac, 1.0, energia_autoproduzida, energia_autoconsumida, energia_rede, energia_total)

        #calc_tarifario = lambda en, ano, col : ape.calcula_tarifario_simples(en, 1, col)

        fin, _ = af.analise_financeira_projecto_indicadores_autoconsumo(indicadores, 60.0, 300.0, 5.0, taxa_actualizacao, 2022, 5, taxa_degradacao, inflacao, custo_kwh, preco_kwh_venda_rede)

        self.assertAlmostEqual(158.12, fin.val, 2)

    def test_analise_financeira_indicadores_com_taxa_inflacao(self):
        energia_total = 2240
        energia_autoproduzida = 1400
        iac = 60.0
        energia_autoconsumida = energia_autoproduzida*iac/100.0
        energia_rede = energia_total-energia_autoconsumida
        custo_kwh = 0.1
        preco_kwh_venda_rede = 0.05
        taxa_actualizacao = 5.0
        taxa_degradacao = 0.7
        taxa_inflacao = 2
        indicadores = indicadores_autoconsumo(iac, None, 100.0-iac, 1.0, energia_autoproduzida, energia_autoconsumida, energia_rede, energia_total)

        #calc_tarifario = lambda en, ano, col : ape.calcula_tarifario_simples(en, 1, col)

        fin, _ = af.analise_financeira_projecto_indicadores_autoconsumo(indicadores, 60.0, 300.0, 5.0, taxa_actualizacao, 2022, 5, taxa_degradacao, taxa_inflacao, custo_kwh, preco_kwh_venda_rede)

        self.assertAlmostEqual(176.61, fin.val, 2)

    def test_val(self):
        cf = pd.DataFrame({'cash flow':[-100, 40, 40, 40], 'ano_projecto':[0, 1, 2, 3]})
        taxa_actualizacao = 8.333
        val = af._val(cf, taxa_actualizacao)
        self.assertAlmostEqual(2.468, val, 3)

    def test_tir(self):
        # Utiliza valores de https://seer.pgsskroton.com/exatas/article/download/488/457
        cf = pd.DataFrame({'cash flow':[-100, 40, 40, 40]})

        tir = af._tir(cf, 0, 3)
        self.assertAlmostEqual(9.701, tir, 3)

    def test_indicador_financeiro_frame(self):

        id = af.indicadores_financeiros(10, 5.1, 12, 1000, 10, 20, 0)
        display_html(id.as_frame())

    def test_lcoe(self):
        taxa_actualizacao = 10
        taxa_degradacao = 0.7
        # n horas equivalentes = 1533 kWh/kWp
        ind = indicadores_autoconsumo(0, 0, 0, 0.68, 1042.7, 0, 0, 0)
        opex = 10
        capex = 1500
        n_anos = 15
        lcoe = af._lcoe(n_anos, capex, opex, taxa_actualizacao, 0.68, 1042.7 / 0.68, taxa_degradacao)

        self.assertAlmostEqual(0.207, lcoe, 3)
