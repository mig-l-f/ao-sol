from datetime import datetime
from sqlite3 import apilevel
import unittest
import pandas as pd
from datetime import datetime
from ..aosol.analise import analise_precos_energia as ape

class TestPrecoEnergia(unittest.TestCase):

    def test_horario_inverno_verao(self):
        #['2022-03-22', '2022-10-30']
        dom_mar, dom_out = ape.datas_horario_legal(2022)
        self.assertEqual(datetime.strptime('2022-03-27', '%Y-%m-%d'), dom_mar)
        self.assertEqual(datetime.strptime('2022-10-30', '%Y-%m-%d'), dom_out)

    def test_taxas_iva_para_diferentes_potencias_contratadas(self):
        # testar os diferentes taxas iva aplicados dada a potencia contratada
        pot_contratada = ape.PotenciaContratada.kVA_3_45
        self.assertEqual(0.06, ape._taxas_iva(ape._TermosFatura.PotContratadaTermoFixo, pot_contratada))
        self.assertEqual(0.23, ape._taxas_iva(ape._TermosFatura.PotContratadaTermoVariavel, pot_contratada))
        self.assertEqual(0.13, ape._taxas_iva(ape._TermosFatura.EnergiaAteLimiar, pot_contratada))
        self.assertEqual(0.23, ape._taxas_iva(ape._TermosFatura.EnegiaAcimaLimiar, pot_contratada))

        pot_contratada = ape.PotenciaContratada.kVA_6_9
        self.assertEqual(0.23, ape._taxas_iva(ape._TermosFatura.PotContratadaTermoFixo, pot_contratada))
        self.assertEqual(0.23, ape._taxas_iva(ape._TermosFatura.PotContratadaTermoVariavel, pot_contratada))
        self.assertEqual(0.13, ape._taxas_iva(ape._TermosFatura.EnergiaAteLimiar, pot_contratada))
        self.assertEqual(0.23, ape._taxas_iva(ape._TermosFatura.EnegiaAcimaLimiar, pot_contratada))

    def test_fatura_mensal_tarifario_simples(self):
        # potencia contratada de 3.45 kVA
        # consumo mensal de 160kWh
        # periodo de faturacao de 30 dias
        pot_contratada = ape.PotenciaContratada.kVA_3_45
        consumo = 160
        n_dias_faturacao = 30
        preco_simples = 0.1486
        custo_pot_contratada = 0.1480 + 0.018
        custo_pot_contratada_termo_fixo = 0.1480
        total_c_iva, total_s_iva = ape.calcula_fatura_tarifario_simples(consumo, n_dias_faturacao, preco_simples, pot_contratada, custo_pot_contratada, custo_pot_contratada_termo_fixo)
        self.assertEqual(31.84, total_s_iva, 2)
        self.assertEqual(36.43, total_c_iva, 2)

    def test_fatura_mensal_tarifario_simples_2(self):
        pot_contratada = ape.PotenciaContratada.kVA_3_45
        consumo = 167
        d_inicial = datetime.strptime('16/08/2022', '%d/%m/%Y')
        d_final = datetime.strptime("15/09/2022", "%d/%m/%Y")
        n_dias_faturacao = abs((d_final - d_inicial).days) + 1 # incluir dia inicial e final
        custo_pot_contratada = 0.0904 + 0.0758
        custo_pot_contratada_termo_fixo = 0.0904
        preco_simples = 0.1542
        total_c_iva, _ = ape.calcula_fatura_tarifario_simples(consumo, n_dias_faturacao, preco_simples, pot_contratada, custo_pot_contratada, custo_pot_contratada_termo_fixo)
        self.assertEqual(39.26, total_c_iva, 2)

    def test_fatura_mensal_tarifario_bihorario(self):
        pot_contratada = ape.PotenciaContratada.kVA_6_9
        consumo_fora_vazio = 170
        consumo_vazio = 80
        n_dias_faturacao = 30
        preco_fora_vazio = 0.1815
        preco_vazio = 0.0958
        custo_pot_contratada = 0.2959 + 0.0188
        custo_pot_contratada_termo_fixo = 0.2959
        total_c_iva, total_s_iva = ape.calcula_fatura_tarifario_bihorario(consumo_fora_vazio, consumo_vazio, n_dias_faturacao, preco_fora_vazio, preco_vazio, pot_contratada, custo_pot_contratada, custo_pot_contratada_termo_fixo)
        # valores ate novembro 2021
        #self.assertEqual(60.93, total_c_iva, 2)
        #self.assertEqual(51.13, total_s_iva, 2)
        # valores a partir dezembro 2021 (limiar consumo energia)
        self.assertEqual(60.86, total_c_iva, 2)
        self.assertEqual(51.13, total_s_iva, 2)

    def test_fatura_mensal_tarifario_trihorario(self):
        pot_contratada = ape.PotenciaContratada.kVA_3_45
        consumo_ponta = 37
        consumo_cheia = 80
        consumo_vazio = 50
        n_dias_faturacao = 31
        preco_ponta = 0.2336
        preco_cheia = 0.1710
        preco_vazio = 0.1073
        custo_pot_contratada = 0.0904 + 0.0758
        custo_pot_contratada_termo_fixo = 0.0904
        total_c_iva, total_s_iva = ape.calcula_fatura_tarifario_trihorario(consumo_ponta, consumo_cheia, consumo_vazio, n_dias_faturacao, preco_ponta, preco_cheia, preco_vazio, pot_contratada, custo_pot_contratada, custo_pot_contratada_termo_fixo)
        self.assertEqual(44.85, total_c_iva)
        self.assertEqual(39.21, total_s_iva)

    def test_energia_mensal_tarifario_simples(self):
        # 2 timestamps em cada mes, 1 vazio outro fora vazio
        df = pd.DataFrame({'stamp':[
            '2022-01-01 00:00','2022-01-01 10:00','2022-02-01 00:00','2022-02-01 10:00',
            '2022-03-01 00:00','2022-03-01 10:00','2022-04-01 00:00','2022-04-01 10:00',
            '2022-05-01 00:00','2022-05-01 10:00','2022-06-01 00:00','2022-06-01 10:00',
            '2022-07-01 00:00','2022-07-01 10:00','2022-08-01 00:00','2022-08-01 10:00',
            '2022-09-01 00:00','2022-09-01 10:00','2022-10-01 00:00','2022-10-01 10:00',
            '2022-11-01 00:00','2022-11-01 10:00','2022-12-01 00:00','2022-12-01 10:00',
        ],
        'consumo' :     [ 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2], 
        'consumo_rede' : [ 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0]})
        df['stamp'] = pd.to_datetime(df['stamp'])
        df = df.set_index('stamp')
        consumo_mensal = ape.calcula_energia_mensal_tarifario_simples(df, 'consumo')
        self.assertEqual(2*24, consumo_mensal['consumo'].sum())
        self.assertEqual(4, consumo_mensal['2022-04']['consumo'].item())

    def test_energia_mensal_tarifario_bihorario(self):
        # 2 timestamps em cada mes, 1 vazio outro fora vazio
        df = pd.DataFrame({'stamp':[
            '2022-01-01 00:00','2022-01-01 10:00','2022-02-01 00:00','2022-02-01 10:00',
            '2022-03-01 00:00','2022-03-01 10:00','2022-04-01 00:00','2022-04-01 10:00',
            '2022-05-01 00:00','2022-05-01 10:00','2022-06-01 00:00','2022-06-01 10:00',
            '2022-07-01 00:00','2022-07-01 10:00','2022-08-01 00:00','2022-08-01 10:00',
            '2022-09-01 00:00','2022-09-01 10:00','2022-10-01 00:00','2022-10-01 10:00',
            '2022-11-01 00:00','2022-11-01 10:00','2022-12-01 00:00','2022-12-01 10:00',
        ],
        'consumo' :     [ 2, 1, 2, 1, 2, 1, 2, 1, 2, 1, 2, 1, 2, 1, 2, 1, 2, 1, 2, 1, 2, 1, 2, 1]})
        df['stamp'] = pd.to_datetime(df['stamp'])
        df = df.set_index('stamp')
        consumo_mensal = ape.calcula_energia_mensal_tarifario_bihorario(df, 'consumo')
        self.assertEqual(12*2, consumo_mensal['vazio'].sum())
        self.assertEqual(12*1, consumo_mensal['fora_vazio'].sum())
        self.assertEqual(1, consumo_mensal['2022-09']['fora_vazio'].item())
        self.assertEqual(2, consumo_mensal['2022-05']['vazio'].item())

    def test_energia_mensal_tarifario_trihorario(self):
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
        'consumo' :     [ 1, 2, 3, 1, 2, 3, 1, 2, 3, 1, 2, 3, 1, 2, 3, 1, 2, 3, 1, 2, 3, 1, 2, 3, 1, 2, 3, 1, 2, 3, 1, 2, 3, 1, 2, 3, ]})
        df['stamp'] = pd.to_datetime(df['stamp'])
        df = df.set_index('stamp')
        consumo_mensal = ape.calcula_energia_mensal_tarifario_trihorario(df, 'consumo', 2022)
        self.assertEqual(12*1, consumo_mensal['cheia'].sum())
        self.assertEqual(12*2, consumo_mensal['ponta'].sum())
        self.assertEqual(12*3, consumo_mensal['vazio'].sum())
