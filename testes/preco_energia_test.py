from datetime import datetime
from sqlite3 import apilevel
import unittest
import pandas as pd
from ..src.aosol.analise import analise_precos_energia as ape

class TestPrecoEnergia(unittest.TestCase):

    def test_bihorario_diario(self):
        df = pd.DataFrame({'time' : [
            '2022-03-01 22:00', # vazio
            '2022-03-01 00:00', # vazio
            '2022-03-01 08:00', # fora vazio
            '2022-03-01 13:00', # fora vazio
        ], 'energia' : [1, 1, 1, 1]})
        df['time'] = pd.to_datetime(df['time'])
        df = df.set_index('time')
        custo,_ = ape.calcula_tarifario_bihorario_diario(df, 5, 2, 'energia')
        self.assertEqual(14.0, custo)

    def test_trihorario_diario(self):
        df = pd.DataFrame({'time' : [
            '2022-03-01 22:00', # vazio
            '2022-03-01 00:00', # vazio
            '2022-03-01 08:00', # cheias
            '2022-03-01 09:00', # ponta
            '2022-03-01 13:00', # cheias
            '2022-03-01 18:00', # ponta
            '2022-03-01 21:00', # cheias
        ], 'energia' : [1, 1, 1, 1, 1, 1, 1]})
        df['time'] = pd.to_datetime(df['time'])
        df = df.set_index('time')
        custo,_ = ape.calcula_tarifario_trihorario_diario(df, 2022, 5, 3, 2, 'energia')
        self.assertEqual(23.0, custo)

    def test_trihorario_diario_inverno_verao(self):
        df = pd.DataFrame({'time' : [
            # inverno 24
            '2022-03-01 22:00', # vazio
            '2022-03-01 08:00', # cheias
            '2022-03-01 09:00', # ponta
            '2022-03-01 12:00', # cheias
            '2022-03-01 13:00', # cheias
            '2022-03-01 18:00', # ponta
            '2022-03-01 21:00', # cheias
            # verao 22
            '2022-09-01 22:00', # vazio
            '2022-09-01 08:00', # cheias
            '2022-09-01 09:00', # cheias
            '2022-09-01 12:00', # ponta
            '2022-09-01 13:00', # cheias
            '2022-09-01 18:00', # cheias
            '2022-09-01 21:00', # cheias
            # inverno 5
            '2022-11-01 09:00'  # ponta
        ], 'energia' : [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1]})
        df['time'] = pd.to_datetime(df['time'])
        df = df.set_index('time')
        custo,_ = ape.calcula_tarifario_trihorario_diario(df, 2022, 5, 3, 2, 'energia')
        #print(df)
        self.assertEqual(51.0, custo)

    def test_horario_inverno_verao(self):
        #['2022-03-22', '2022-10-30']
        dom_mar, dom_out = ape.datas_horario_legal(2022)
        self.assertEqual(datetime.strptime('2022-03-27', '%Y-%m-%d'), dom_mar)
        self.assertEqual(datetime.strptime('2022-10-30', '%Y-%m-%d'), dom_out)

    def test_simples(self):
        df = pd.DataFrame({'time' : [
            '2022-03-01 22:00', # vazio
            '2022-03-01 00:00', # vazio
            '2022-03-01 08:00', # fora vazio
            '2022-03-01 13:00', # fora vazio
        ], 'energia' : [1, 1, 1, 1]})
        df['time'] = pd.to_datetime(df['time'])
        df = df.set_index('time')
        custo,_ = ape.calcula_tarifario_simples(df, 5, 'energia')
        self.assertEqual(20.0, custo)
        print(df)
