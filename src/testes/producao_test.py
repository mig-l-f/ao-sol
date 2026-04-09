from datetime import datetime
import unittest
from aosol.series import producao
import pandas as pd
import numpy as np

class TestProducao(unittest.TestCase):

    def test_converter_pvgis(self):
        df = pd.DataFrame({
            'time' : ['2016-01-01 00:10', '2016-12-31 23:10'],
            'P' : [1000.0, 2000.0],
            'poa_global' : [10.0, 10.0]
        })
        df['time'] = pd.to_datetime(df['time'])
        df = df.set_index('time')
        dummy1 = []
        dummy2 = []
        pvgis_tuple = (df, dummy1, dummy2)

        prod = producao.converter_pvgis_data(pvgis_tuple, 2021)
        self.assertEqual(datetime(2021, 1, 1, 0, 0, 0), prod.index[0])
        self.assertEqual(datetime(2021, 12, 31, 23, 0, 0), prod.index[-1])
        # potencia
        self.assertAlmostEqual(1.0, prod['autoproducao'].iloc[0], 2)
        self.assertAlmostEqual(2.0, prod['autoproducao'].iloc[-1], 2)

    def test_converter_pvgis_com_temperatura(self):
        df = pd.DataFrame({
            'time' : ['2016-01-01 00:10', '2016-12-31 23:10'],
            'P' : [1000.0, 2000.0],
            'poa_global' : [10.0, 10.0],
            'temp_air': [15.0, 17.0]
        })
        df['time'] = pd.to_datetime(df['time'])
        df = df.set_index('time')
        dummy1 = []
        dummy2 = []
        pvgis_tuple = (df, dummy1, dummy2)

        prod = producao.converter_pvgis_data(pvgis_tuple, 2021, inclui_temp=True)
        self.assertEqual(datetime(2021, 1, 1, 0, 0, 0), prod.index[0])
        self.assertEqual(datetime(2021, 12, 31, 23, 0, 0), prod.index[-1])
        # potencia
        self.assertAlmostEqual(1.0, prod['autoproducao'].iloc[0], 2)
        self.assertAlmostEqual(2.0, prod['autoproducao'].iloc[-1], 2)
        # temp
        self.assertAlmostEqual(15.0, prod['temperatura'].iloc[0], 2)
        self.assertAlmostEqual(17.0, prod['temperatura'].iloc[-1], 2)

    def test_converter_multiyear_ts(self):
        # Given
        df = pd.DataFrame({
            'time' : ['2018-01-01 00:10', '2018-12-31 23:10', '2019-01-01 00:10', '2019-12-31 23:10'],
            'P': [500.0, 1000.0, 700.0, 1200.0],
            'poa_global': [10.0, 10.0, 10.0, 10.0],
        })
        df['time'] = pd.to_datetime(df['time'])
        df = df.set_index('time')
        dummy1 = []
        dummy2 = []
        pvgis_tuple = (df, dummy1, dummy2)

        # When
        prod = producao.converter_pvgis_multiyear_ts(pvgis_tuple, 2021)

        # Then
        self.assertEqual(2, len(prod))
        self.assertEqual(datetime(2021, 1, 1, 0, 0, 0), prod.index[0])
        self.assertEqual(datetime(2021, 12, 31, 23, 0, 0), prod.index[-1])
        # media (P50)
        self.assertAlmostEqual(0.6, prod['autoproducao'].iloc[0], 2)
        self.assertAlmostEqual(1.1, prod['autoproducao'].iloc[-1], 2)
        # P90
        self.assertAlmostEqual(0.419, prod['autoproducao_p90'].iloc[0], 2)
        self.assertAlmostEqual(0.919, prod['autoproducao_p90'].iloc[-1], 2)

    def test_converter_multiyear_ts_sem_p90(self):
                # Given
        df = pd.DataFrame({
            'time' : ['2018-01-01 00:10', '2018-12-31 23:10', '2019-01-01 00:10', '2019-12-31 23:10'],
            'P': [500.0, 1000.0, 700.0, 1200.0],
            'poa_global': [10.0, 10.0, 10.0, 10.0],
        })
        df['time'] = pd.to_datetime(df['time'])
        df = df.set_index('time')
        dummy1 = []
        dummy2 = []
        pvgis_tuple = (df, dummy1, dummy2)

        # When
        prod = producao.converter_pvgis_multiyear_ts(pvgis_tuple, 2021, inclui_p90=False)

        # Then
        self.assertEqual(2, len(prod))
        self.assertEqual(datetime(2021, 1, 1, 0, 0, 0), prod.index[0])
        self.assertEqual(datetime(2021, 12, 31, 23, 0, 0), prod.index[-1])
        # media (P50)
        self.assertAlmostEqual(0.6, prod['autoproducao'].iloc[0], 2)
        self.assertAlmostEqual(1.1, prod['autoproducao'].iloc[-1], 2)
        # P90
        self.assertNotIn('autoproducao_p90', prod.columns)

    def test_converter_multiyear_ts_com_temperatura(self):
        df = pd.DataFrame({
            'time' : ['2018-01-01 00:10', '2018-12-31 23:10', '2019-01-01 00:10', '2019-12-31 23:10'],
            'P': [500.0, 1000.0, 700.0, 1200.0],
            'poa_global': [10.0, 10.0, 10.0, 10.0],
            'temp_air': [10.0, 15.0, 12.0, 17.0]
        })
        df['time'] = pd.to_datetime(df['time'])
        df = df.set_index('time')
        dummy1 = []
        dummy2 = []
        pvgis_tuple = (df, dummy1, dummy2)

        # When
        prod = producao.converter_pvgis_multiyear_ts(pvgis_tuple, 2021, inclui_temp=True)

        # Then
        self.assertEqual(2, len(prod))
        self.assertEqual(datetime(2021, 1, 1, 0, 0, 0), prod.index[0])
        self.assertEqual(datetime(2021, 12, 31, 23, 0, 0), prod.index[-1])
        # media (P50)
        self.assertAlmostEqual(0.6, prod['autoproducao'].iloc[0], 2)
        self.assertAlmostEqual(1.1, prod['autoproducao'].iloc[-1], 2)
        self.assertAlmostEqual(11.0, prod['temperatura'].iloc[0], 2)
        self.assertAlmostEqual(16.0, prod['temperatura'].iloc[-1], 2)
        # P90
        self.assertAlmostEqual(0.419, prod['autoproducao_p90'].iloc[0], 2)
        self.assertAlmostEqual(0.919, prod['autoproducao_p90'].iloc[-1], 2) 
        self.assertAlmostEqual(9.19, prod['temperatura_p90'].iloc[0], 2)
        self.assertAlmostEqual(14.19, prod['temperatura_p90'].iloc[-1], 2)

    def test_inputbisexto_multiano_alvo_naobisexto_pvgis(self):
        # df contem 29/02 mas ano alvo nao é bisexto
        df = pd.DataFrame({
            'time' : ['2016-01-01 00:10', '2016-02-29 23:10', '2016-12-31 23:10', '2017-01-01 00:10', '2017-12-31 23:10'],
            'P': [500.0, 2000.0, 1000.0, 700.0, 1200.0],
            'poa_global': [10.0, 10.0, 10.0, 10.0, 10.0]
        })
        df['time'] = pd.to_datetime(df['time'])
        df = df.set_index('time')
        dummy1 = []
        dummy2 = []
        pvgis_tuple = (df, dummy1, dummy2)
        ano_alvo = 2021

        # When
        prod = producao.converter_pvgis_multiyear_ts(pvgis_tuple, ano_alvo)

        # Then
        self.assertEqual(2, len(prod))
        self.assertEqual(datetime(ano_alvo, 1, 1, 0, 0, 0), prod.index[0])
        self.assertEqual(datetime(ano_alvo, 12, 31, 23, 0, 0), prod.index[-1])
        # media
        self.assertAlmostEqual(0.6, prod['autoproducao'].iloc[0], 2)
        self.assertAlmostEqual(1.1, prod['autoproducao'].iloc[-1], 2)

    def test_inputbisexto_multiano_alvo_bisexto_pvgis(self):
        # df contem 29/02 mas ano alvo nao é bisexto
        df = pd.DataFrame({
            'time' : ['2016-01-01 00:10', '2016-02-29 23:10', '2016-12-31 23:10', '2017-01-01 00:10', '2017-12-31 23:10'],
            'P': [500.0, 2000.0, 1000.0, 700.0, 1200.0],
            'poa_global': [10.0, 10.0, 10.0, 10.0, 10.0]
        })
        df['time'] = pd.to_datetime(df['time'])
        df = df.set_index('time')
        dummy1 = []
        dummy2 = []
        pvgis_tuple = (df, dummy1, dummy2)
        ano_alvo = 2020

        # When
        prod = producao.converter_pvgis_multiyear_ts(pvgis_tuple, ano_alvo)

        # Then
        self.assertEqual(3, len(prod))
        self.assertEqual(datetime(ano_alvo, 1, 1, 0, 0, 0), prod.index[0])
        self.assertEqual(datetime(ano_alvo, 2, 29, 23, 0, 0), prod.index[1])
        self.assertEqual(datetime(ano_alvo, 12, 31, 23, 0, 0), prod.index[-1])
        # media
        self.assertAlmostEqual(0.6, prod['autoproducao'].iloc[0], 2)
        self.assertAlmostEqual(2.0, prod['autoproducao'].iloc[1], 2)
        self.assertAlmostEqual(1.1, prod['autoproducao'].iloc[-1], 2)

    def test_downscale_solar_1h_15min(self):
        # Given
        # 1. Criar dados de teste (3 horas)
        idx = pd.date_range("2024-01-01 07:00", periods=13, freq="H")
        df = pd.DataFrame({"potencia": [0.0, 0.0, 113.34, 265.88, 236.53, 311.58, 555.8, 414.17, 449.71, 329.81, 11.62, 0.0, 0.0]}, index=idx)

        # When
        df_15min = producao.downscaling_solar_horario_para_15min(df)
        
        media_15 = df_15min.resample("H").mean()
        media_15 = media_15.loc[df.index]

        energia_15min = df_15min * 0.25
        energia_15min_total = float(energia_15min.sum())

        energia_1h_total = float(df.sum())

        # Then
        self.assertEqual(49, len(df_15min))
        # media preservada
        self.assertTrue(np.allclose(df['potencia'], media_15['potencia'], atol=0.01))
        # energia igual
        self.assertAlmostEqual(energia_1h_total, energia_15min_total, places=3)

    def test_converter_multiyear_com_downscaling_15min(self):
        # Given
        df = pd.DataFrame({
            'time' : ['2018-01-01 00:10', '2018-01-01 01:10', '2019-01-01 00:10', '2019-01-01 01:10'],
            'P': [500.0, 1000.0, 700.0, 1200.0],
            'poa_global': [10.0, 10.0, 10.0, 10.0],
        })
        df['time'] = pd.to_datetime(df['time'])
        df = df.set_index('time')
        dummy1 = []
        dummy2 = []
        pvgis_tuple = (df, dummy1, dummy2)

        # When
        prod = producao.converter_pvgis_multiyear_ts(pvgis_tuple, 2021, inclui_p90=False, downscale_para_15min=True)

        # Then
        self.assertEqual(5, len(prod))
        self.assertEqual(datetime(2021, 1, 1, 0, 0, 0), prod.index[0])
        self.assertEqual(datetime(2021, 1, 1, 0, 15, 0), prod.index[1])
        self.assertEqual(datetime(2021, 1, 1, 0, 30, 0), prod.index[2])
        self.assertEqual(datetime(2021, 1, 1, 0, 45, 0), prod.index[3])
        self.assertEqual(datetime(2021, 1, 1, 1, 0, 0), prod.index[-1])
        # media (P50)   
        self.assertAlmostEqual(0.15, prod['autoproducao'].iloc[0], 2)
        self.assertAlmostEqual(0.15, prod['autoproducao'].iloc[1], 2)
        self.assertAlmostEqual(0.15, prod['autoproducao'].iloc[2], 2)
        self.assertAlmostEqual(0.15, prod['autoproducao'].iloc[3], 2)
        self.assertAlmostEqual(0.275, prod['autoproducao'].iloc[-1], 2)
        # P90
        self.assertNotIn('autoproducao_p90', prod.columns)
                       