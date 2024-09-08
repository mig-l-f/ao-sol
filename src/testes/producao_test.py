from datetime import datetime
import unittest
from ..aosol.series import producao, pvgis
import pandas as pd

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

    def test_converter_multiyear_ts(self):
        # Given
        df = pd.DataFrame({
            'time' : ['2018-01-01 00:10', '2018-12-31 23:10', '2019-01-01 00:10', '2019-12-31 23:10'],
            'P': [500.0, 1000.0, 700.0, 1200.0],
            'poa_global': [10.0, 10.0, 10.0, 10.0]
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
        self.assertAlmostEqual(0.491, prod['autoproducao_p90'].iloc[0], 2)
        self.assertAlmostEqual(0.900, prod['autoproducao_p90'].iloc[-1], 2)

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
