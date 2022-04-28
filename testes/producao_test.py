from datetime import datetime
import unittest
from ..src.aosol.series import producao
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