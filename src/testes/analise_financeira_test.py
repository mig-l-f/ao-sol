from tkinter.tix import Tree
import pandas as pd
import unittest

from ..aosol.analise.indicadores_autoconsumo import indicadores_autoconsumo
from ..aosol.analise import analise_financeira as af
from ..aosol.analise import analise_precos_energia as ape
from IPython.display import HTML, display_html

class TestAnaliseFinanceira(unittest.TestCase):
    def test_poupanca_anual_fatura_tarifario_simples(self):
        df = pd.DataFrame({'stamp':[
            '2022-01-01 00:00','2022-02-01 00:00','2022-03-01 00:00','2022-04-01 00:00',
            '2022-05-01 00:00','2022-06-01 00:00','2022-07-01 00:00','2022-08-01 00:00',
            '2022-09-01 00:00','2022-10-01 00:00','2022-11-01 00:00','2022-12-01 00:00',
        ],
        'consumo' :     [ 160, 160, 160, 160, 160, 160, 160, 160, 160, 160, 160, 160], 
        'consumo_rede' : [ 120, 120, 120, 120, 120, 120, 120, 120, 120, 120, 120, 120]})
        df['stamp'] = pd.to_datetime(df['stamp'])
        df = df.set_index('stamp')
        precos_energia = ape.TarifarioEnergia(custo_kwh_simples=0.1486, pot_contratada=ape.PotenciaContratada.kVA_3_45, pot_contratada_custo_dia=0.1480 + 0.018, pot_contratada_termo_fixo_redes_custo_dia=0.1480)
        mensal = af.analise_poupanca_anual_fatura(df, ape.Tarifario.Simples, precos_energia, False)
        self.assertAlmostEqual(36.43, mensal.loc['Setembro','fatura sem upac'], 2)
        print(mensal)

    def test_poupanca_anual_fatura_tarifario_bihorario(self):
        df = pd.DataFrame({'stamp':[
            '2022-01-01 00:00','2022-01-01 10:00',
            '2022-02-01 00:00','2022-02-01 10:00',
            '2022-03-01 00:00','2022-03-01 10:00',
            '2022-04-01 00:00','2022-04-01 10:00',
            '2022-05-01 00:00','2022-05-01 10:00',
            '2022-06-01 00:00','2022-06-01 10:00',
            '2022-07-01 00:00','2022-07-01 10:00',
            '2022-08-01 00:00','2022-08-01 10:00',
            '2022-09-01 00:00','2022-09-01 10:00',
            '2022-10-01 00:00','2022-10-01 10:00',
            '2022-11-01 00:00','2022-11-01 10:00',
            '2022-12-01 00:00','2022-12-01 10:00',
        ],
        'consumo' :     [ 80, 170, 80, 170, 80, 170, 80, 170, 80, 170, 80, 170, 80, 170, 80, 170, 80, 170, 80, 170, 80, 170, 80, 170], 
        'consumo_rede' : [ 40, 120, 40, 120, 40, 120, 40, 120, 40, 120, 40, 120, 40, 120, 40, 120, 40, 120, 40, 120, 40, 120, 40, 120,]})
        df['stamp'] = pd.to_datetime(df['stamp'])
        df = df.set_index('stamp')
        precos_energia = ape.TarifarioEnergia(custo_bi_kwh_fora_vazio=0.1815, custo_bi_kwh_vazio=0.0958, pot_contratada=ape.PotenciaContratada.kVA_6_9, pot_contratada_custo_dia=0.2959 + 0.0188, pot_contratada_termo_fixo_redes_custo_dia=0.2959)
        mensal = af.analise_poupanca_anual_fatura(df, ape.Tarifario.Bihorario, precos_energia, False)
        self.assertAlmostEqual(60.86, mensal.loc['Setembro','fatura sem upac'], 2)
        print(mensal)

    def test_poupanca_anual_fatura_tarifario_trihorario(self):
        # 3 timestamps em cada mes: vazio (22:00), ponta (20:00) e cheia (08:00)
        df = pd.DataFrame({'stamp':[
            # cheia           ,  ponta           , vazio
            '2022-01-01 08:00','2022-01-01 20:00','2022-01-01 22:00',
            '2022-02-01 08:00','2022-02-01 20:00','2022-02-01 22:00',
            '2022-03-01 08:00','2022-03-01 20:00','2022-03-01 22:00',
            '2022-04-01 08:00','2022-04-01 20:00','2022-04-01 22:00',
            '2022-05-01 08:00','2022-05-01 20:00','2022-05-01 22:00',
            '2022-06-01 08:00','2022-06-01 20:00','2022-06-01 22:00',
            '2022-07-01 08:00','2022-07-01 20:00','2022-07-01 22:00',
            '2022-08-01 08:00','2022-08-01 20:00','2022-08-01 22:00',
            '2022-09-01 08:00','2022-09-01 20:00','2022-09-01 22:00',
            '2022-10-01 08:00','2022-10-01 20:00','2022-10-01 22:00',
            '2022-11-01 08:00','2022-11-01 20:00','2022-11-01 22:00',
            '2022-12-01 08:00','2022-12-01 20:00','2022-12-01 22:00',
        ],
        'consumo' : [ 80, 37, 50, 80, 37, 50, 80, 37, 50, 80, 37, 50, 80, 37, 50, 80, 37, 50, 80, 37, 50, 80, 37, 50, 80, 37, 50, 80, 37, 50, 80, 37, 50, 80, 37, 50 ],
        'consumo_rede' : [60, 25, 50, 60, 25, 50, 60, 25, 50, 60, 25, 50, 60, 25, 50, 60, 25, 50, 60, 25, 50, 60, 25, 50, 60, 25, 50, 60, 25, 50, 60, 25, 50, 60, 25, 50, ]})
        df['stamp'] = pd.to_datetime(df['stamp'])
        df = df.set_index('stamp')
        precos_energia = ape.TarifarioEnergia(custo_tri_kwh_ponta=0.2336, custo_tri_kwh_cheia=0.1710, custo_tri_kwh_vazio=0.1073, pot_contratada=ape.PotenciaContratada.kVA_3_45, pot_contratada_custo_dia=0.0904 + 0.0758, pot_contratada_termo_fixo_redes_custo_dia=0.0904)
        mensal = af.analise_poupanca_anual_fatura(df, ape.Tarifario.Trihorario, precos_energia, False, 2022)
        self.assertAlmostEqual(44.85, mensal.loc['Janeiro','fatura sem upac'], 2)

    def test_poupanca_anual_venda_rede(self):
        df = pd.DataFrame({'stamp':[
            '2022-01-01 00:00','2022-02-01 00:00','2022-03-01 00:00','2022-04-01 00:00',
            '2022-05-01 00:00','2022-06-01 00:00','2022-07-01 00:00','2022-08-01 00:00',
            '2022-09-01 00:00','2022-10-01 00:00','2022-11-01 00:00','2022-12-01 00:00',
        ],
        'consumo' :     [ 160, 160, 160, 160, 160, 160, 160, 160, 160, 160, 160, 160], 
        'consumo_rede' : [ 120, 120, 120, 120, 120, 120, 120, 120, 120, 120, 120, 120],
        'injeccao_rede': [ 0, 0, 0, 0, 1, 1, 1, 1, 0, 0, 0, 0]})
        df['stamp'] = pd.to_datetime(df['stamp'])
        df = df.set_index('stamp')
        precos_energia = ape.TarifarioEnergia(preco_venda_kwh=1.0, custo_kwh_simples=0.1486, pot_contratada=ape.PotenciaContratada.kVA_3_45, pot_contratada_custo_dia=0.1480 + 0.018, pot_contratada_termo_fixo_redes_custo_dia=0.1480)
        mensal = af.analise_poupanca_anual_fatura(df, ape.Tarifario.Simples, precos_energia, True)
        self.assertAlmostEqual(36.43, mensal.loc['Setembro','fatura sem upac'], 2)
        self.assertEqual(4.0, mensal.loc['Anual','venda a rede'])
        print(mensal)

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

    def test_analise_financeira_tarifario_simples_faturas(self):
        df = pd.DataFrame({'stamp':[
            '2022-01-01 00:00','2022-02-01 00:00','2022-03-01 00:00','2022-04-01 00:00',
            '2022-05-01 00:00','2022-06-01 00:00','2022-07-01 00:00','2022-08-01 00:00',
            '2022-09-01 00:00','2022-10-01 00:00','2022-11-01 00:00','2022-12-01 00:00',
        ],
        'consumo': [160, 160, 160, 160, 160, 160, 160, 160, 160, 160, 160, 160],
        'consumo_rede' : [ 130, 130, 130, 130, 130, 130, 130, 130, 130, 130, 130, 130]}) 
        df['stamp'] = pd.to_datetime(df['stamp'])
        df = df.set_index('stamp')
        preco_energia = ape.TarifarioEnergia(0.1486)
        fin, _ = af.analise_financeira_projecto_faturas(df, 200, 10, 5, 2021, 5, 0.0, 0.0, ape.Tarifario.Simples, preco_energia, False)
        self.assertAlmostEqual(43.490, fin.val, 3)

    def test_analise_financeira_tarifario_simples_faturas_com_degradacao(self):
        df = pd.DataFrame({'stamp':[
            '2022-01-01 00:00','2022-02-01 00:00','2022-03-01 00:00','2022-04-01 00:00',
            '2022-05-01 00:00','2022-06-01 00:00','2022-07-01 00:00','2022-08-01 00:00',
            '2022-09-01 00:00','2022-10-01 00:00','2022-11-01 00:00','2022-12-01 00:00',
        ],
        'consumo': [160, 160, 160, 160, 160, 160, 160, 160, 160, 160, 160, 160],
        'consumo_rede' : [ 130, 130, 130, 130, 130, 130, 130, 130, 130, 130, 130, 130]}) 
        df['stamp'] = pd.to_datetime(df['stamp'])
        df = df.set_index('stamp')
        preco_energia = ape.TarifarioEnergia(0.1486)
        fin, _ = af.analise_financeira_projecto_faturas(df, 200, 10, 5, 2021, 5, 0.7, 0.0, ape.Tarifario.Simples, preco_energia, False)
        self.assertAlmostEqual(40.484, fin.val, 3)

    def test_analise_financeira_tarifario_simples_venda_rede(self):
        df = pd.DataFrame({'stamp':[
            '2022-01-01 00:00','2022-02-01 00:00','2022-03-01 00:00','2022-04-01 00:00',
            '2022-05-01 00:00','2022-06-01 00:00','2022-07-01 00:00','2022-08-01 00:00',
            '2022-09-01 00:00','2022-10-01 00:00','2022-11-01 00:00','2022-12-01 00:00',
        ],
        'consumo': [160, 160, 160, 160, 160, 160, 160, 160, 160, 160, 160, 160],
        'consumo_rede' : [ 130, 130, 130, 130, 130, 130, 130, 130, 130, 130, 130, 130],
        'injeccao_rede': [ 20, 20, 20, 20, 20, 20, 20, 20, 20, 20, 20, 20]}) 
        df['stamp'] = pd.to_datetime(df['stamp'])
        df = df.set_index('stamp')
        preco_energia = ape.TarifarioEnergia(0.1486, preco_venda_kwh=0.07)
        fin, _ = af.analise_financeira_projecto_faturas(df, 200, 10, 5, 2021, 5, 0.0, 0.0, ape.Tarifario.Simples, preco_energia, True)
        self.assertAlmostEqual(116.225, fin.val, 3)

    def test_analise_financeira_tarifario_simples_venda_rede_degradacao_sistema(self):
        df = pd.DataFrame({'stamp':[
            '2022-01-01 00:00','2022-02-01 00:00','2022-03-01 00:00','2022-04-01 00:00',
            '2022-05-01 00:00','2022-06-01 00:00','2022-07-01 00:00','2022-08-01 00:00',
            '2022-09-01 00:00','2022-10-01 00:00','2022-11-01 00:00','2022-12-01 00:00',
        ],
        'consumo': [160, 160, 160, 160, 160, 160, 160, 160, 160, 160, 160, 160],
        'consumo_rede' : [ 130, 130, 130, 130, 130, 130, 130, 130, 130, 130, 130, 130],
        'injeccao_rede': [ 2.50, 2.50, 2.50, 2.50, 2.50, 2.50, 2.50, 2.50, 2.50, 2.50, 2.50, 2.50]}) 
        df['stamp'] = pd.to_datetime(df['stamp'])
        df = df.set_index('stamp')
        preco_energia = ape.TarifarioEnergia(0.1486, preco_venda_kwh=1.0)
        fin, _ = af.analise_financeira_projecto_faturas(df, 200, 10, 5, 2021, 5, 0.7, 0.0, ape.Tarifario.Simples, preco_energia, True)
        self.assertAlmostEqual(168.993, fin.val, 3)

    def test_analise_financeira_tarifario_simples_venda_rede_com_degradacao_sistema_e_inflacao(self):
        df = pd.DataFrame({'stamp':[
            '2022-01-01 00:00','2022-02-01 00:00','2022-03-01 00:00','2022-04-01 00:00',
            '2022-05-01 00:00','2022-06-01 00:00','2022-07-01 00:00','2022-08-01 00:00',
            '2022-09-01 00:00','2022-10-01 00:00','2022-11-01 00:00','2022-12-01 00:00',
        ],
        'consumo': [160, 160, 160, 160, 160, 160, 160, 160, 160, 160, 160, 160],
        'consumo_rede' : [ 130, 130, 130, 130, 130, 130, 130, 130, 130, 130, 130, 130],
        'injeccao_rede': [ 2.50, 2.50, 2.50, 2.50, 2.50, 2.50, 2.50, 2.50, 2.50, 2.50, 2.50, 2.50]}) 
        df['stamp'] = pd.to_datetime(df['stamp'])
        df = df.set_index('stamp')
        preco_energia = ape.TarifarioEnergia(0.1486, preco_venda_kwh=0.07)
        fin, _ = af.analise_financeira_projecto_faturas(df, 200, 10, 5, 2021, 5, 0.7, 2.0, ape.Tarifario.Simples, preco_energia, True)
        self.assertAlmostEqual(60.593, fin.val, 3)

    def test_analise_financeira_indicadores_autoconsumo_simples_faturas(self):
        # reproduz test simples sem degradacao, inflacao ou venda rede de AF faturas simples
        energia_total = 160*12
        iac = 60.0
        energia_autoproduzida = (30*12)/(iac/100)
        energia_autoconsumida = energia_autoproduzida*iac/100.0
        energia_rede = energia_total-energia_autoconsumida
        taxa_actualizacao = 5.0
        inflacao = 0.0
        indicadores = indicadores_autoconsumo(iac, None, 100.0-iac, 1.0, energia_autoproduzida, energia_autoconsumida, energia_rede, energia_total)
        
        preco_energia = ape.TarifarioEnergia(0.1486)

        fin, _ = af.analise_financeira_projecto_indicadores_autoconsumo_faturas(indicadores, 60.0, 200.0, 10.0, taxa_actualizacao, 2022, 5, 0, inflacao, preco_energia, False)
        self.assertAlmostEqual(43.49, fin.val, 2)

    def test_analise_financeira_indicadores_autoconsumo_venda_rede_faturas(self):
        # reproduz teste simple com venda rede AF faturas simples
        energia_total = 160*12
        iac = 60.0
        energia_autoproduzida = 50*12 #(60%=30, 40%=20)
        energia_autoconsumida = energia_autoproduzida*iac/100.0
        energia_rede = energia_total-energia_autoconsumida
        taxa_actualizacao = 5.0
        inflacao = 0.0
        indicadores = indicadores_autoconsumo(iac, None, 100.0-iac, 1.0, energia_autoproduzida, energia_autoconsumida, energia_rede, energia_total)
        
        preco_energia = ape.TarifarioEnergia(0.1486, preco_venda_kwh=0.07)

        fin, _ = af.analise_financeira_projecto_indicadores_autoconsumo_faturas(indicadores, 60.0, 200.0, 10.0, taxa_actualizacao, 2022, 5, 0, inflacao, preco_energia, True)
        self.assertAlmostEqual(116.225, fin.val, 3)