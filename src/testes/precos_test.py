import unittest
import os
import pandas as pd 
from aosol.series import precos


class TestPrecos(unittest.TestCase):
    def test_ler_ficheiro_omie_tfelicia(self):
        fich = os.path.join(os.path.dirname(__file__), "omie.csv")

        precos_serie = precos.ler_serie_omie_tfelicia(fich, coluna_preco='Portugal', unidades='€/MWh')

        self.assertIsInstance(precos_serie, pd.DataFrame)
        self.assertIn('omie', precos_serie.columns)
        self.assertEqual(0.13159, precos_serie['omie'].iloc[0])
        self.assertEqual(0.13149, precos_serie['omie'].iloc[7])

    def test_ler_ficheiro_omie_tfelicia_unidades_kwh(self):
        fich = os.path.join(os.path.dirname(__file__), "omie.csv")

        precos_serie = precos.ler_serie_omie_tfelicia(fich, unidades='€/kWh')

        self.assertIsInstance(precos_serie, pd.DataFrame)
        self.assertIn('omie', precos_serie.columns)
        self.assertEqual(131.59, precos_serie['omie'].iloc[0])
        self.assertEqual(131.49, precos_serie['omie'].iloc[7])