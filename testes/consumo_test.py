import unittest
import pandas as pd
import os
from ..src.aosol.series import consumo
import locale
locale.setlocale(locale.LC_TIME, "pt_PT") # processar datas em PT

class TestConsumo(unittest.TestCase):
    
    def test_converter_timestamp_com_hora_24(self):
        # data 24 horas
        t = pd.DataFrame({'Data':['5/jan/2022', '31/jan/2022', '15/abr/2021'], 'Hora':['24:00','24:00','16:30']})

        t['Timestamp'] = t[['Data', 'Hora']].apply(consumo.converter_timestamp_hora_24_para_hora_00, axis=1)

        self.assertEqual('06/Jan/2022 00:00', t['Timestamp'].iloc[0])
        self.assertEqual('01/Fev/2022 00:00', t['Timestamp'].iloc[1])
        self.assertEqual('15/Abr/2021 16:30', t['Timestamp'].iloc[2])

    def test_leitura_perfis_eredes(self):
        fich = os.path.join(os.getcwd(),"aosol_project", "testes", "teste_perfis_eredes.csv")
        perfil = consumo.leitura_perfis_eredes(fich, 'BTN C')
        self.assertEqual(0.0369790, perfil['BTN C'].values[0])
        self.assertEqual(0.0367390, perfil['BTN C'].values[1])
        self.assertEqual(0.0391448, perfil['BTN C'].values[-1])

    def teste_ajuste_mensal_perfil(self):
        perfil = pd.DataFrame({'Timestamp':[
            '05/jan/2021 10:00', '05/fev/2021 10:00', '05/mar/2021 10:00', '05/abr/2021 10:00',
            '05/mai/2021 10:00', '05/jun/2021 10:00', '05/jul/2021 10:00', '05/ago/2021 10:00',
            '05/set/2021 10:00', '05/out/2021 10:00', '05/nov/2021 10:00', '05/dez/2021 10:00' 
        ], 'BTN C': [1, 1, 1, 1, 2, 2, 2, 2, 3, 3, 3, 3]})
        perfil['Timestamp'] = pd.to_datetime(perfil['Timestamp'],format='%d/%b/%Y %H:%M')
        perfil = perfil.set_index('Timestamp')

        cons = pd.DataFrame({'mes':pd.Series([1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12], dtype='int64'), 
                             'consumo':pd.Series([2, 2, 2, 2, 3, 3, 3, 3, 2, 2, 2, 2], dtype='float')})
        cons = cons.set_index('mes')
        ajustado = consumo.ajustar_perfil_eredes_a_consumo_mensal(perfil, 'BTN C', cons, 'consumo')
        self.assertEqual(cons['consumo'].sum(), ajustado['Estimativa Consumo'].sum())

    def test_leitura_faturas(self):
        fich = os.path.join(os.getcwd(), "aosol_project", "testes", "teste_leitura_faturas.tsv")
        leituras = consumo.leitura_consumo_faturas(fich, 2021)

        print(leituras)
        self.assertEqual(12, len((leituras.index)))