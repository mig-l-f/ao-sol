import unittest
import aosol.analise.analise_energia as ae
from aosol.armazenamento import bateria
from parameterized import parameterized
import pandas as pd

class AnaliseEnergiaTest(unittest.TestCase):
    
    @parameterized.expand([
        # sem perdas
        (pd.DataFrame({"consumo":[1], "autoproducao":[2]}), 0.5, 1.0, 1.0,
         1.0, 0.5, 0.0, 0.0, 0.5, 1.0), # pv > consumo
        (pd.DataFrame({"consumo":[2], "autoproducao":[1]}), 0.5, 1.0, 1.0,
         1.5, 0.0, 0.5, 0.5, 0.0, 0.0),  # pv < consumo
        (pd.DataFrame({"consumo":[1], "autoproducao":[1.25]}), 0.5, 1.0, 1.0,
         1.0, 0.25, 0.0, 0.0, 0.0, 0.75), # pv > consumo, carrega bat
        (pd.DataFrame({"consumo":[1.25], "autoproducao":[1]}), 0.5, 1.0, 1.0,
         1.25, 0.0, 0.25, 0.0, 0.0, 0.25), # pv < consumo, descarrega bat
        # com perdas bateria
        (pd.DataFrame({"consumo":[1.], "autoproducao":[0.5]}), 1.0, 1.0, 0.9,
         1.0, 0.0, 0.5, 0.0, 0.0, 0.444), # descarrega bat (0.5/0.9 = 0.56) com ef_bat
        (pd.DataFrame({"consumo":[1.], "autoproducao":[0.5]}), 0.4, 1.0, 0.9,
         0.86, 0.0, 0.36, 0.14, 0.0, 0.0), # soc_0 nao e suficiente devido a perdas, consumo rede
        (pd.DataFrame({"consumo":[1.], "autoproducao":[1.5]}), 0.4, 1.0, 0.9,
         1.0, 0.5, 0.0, 0.0, 0.0, 0.9), # perdas nao afectam carga
        # com perdas inversor
        (pd.DataFrame({"consumo":[1.], "autoproducao":[1.]}), 0.0, 0.9, 1.0,
         0.9, 0.0, 0.0, 0.1, 0.0, 0.0), # bateria descarregada, obtem da rede
        (pd.DataFrame({"consumo":[1.], "autoproducao":[1.]}), 1.0, 0.9, 1.0,
         1.0, 0.0, 0.111, 0.0, 0.0, 0.889), # descarga da bateria afectada pela perda inversor soc = soc0 - 0.1/0.9
        # com perdas bateria e inversor
        (pd.DataFrame({"consumo":[1.], "autoproducao":[1.]}), 0.1, 0.9, 0.9,
         0.981, 0.0, 0.09, 0.019, 0.0, 0.0), # carga na bateria nao e suficiente devido a perdas
    ])
    def test_despacho_bateria(self, energia, soc_0, ef_inv, ef_bat,
        exp_autoconsumo, exp_carrega_bat, exp_descarrega_bat, exp_consumo_rede, exp_inj_rede, exp_soc):
        bat = bateria.bateria(1.25, 0.1, 0.9, ef_bat) # capacidade util 1kWh

        energia = ae.analisa_upac_com_armazenamento(energia, bat, soc_0=soc_0, eficiencia_inversor=ef_inv)

        self.assertAlmostEqual(exp_autoconsumo, energia["autoconsumo"].values[0], 3)
        self.assertAlmostEqual(exp_carrega_bat, energia["carga_bateria"].values[0], 3)
        self.assertAlmostEqual(exp_descarrega_bat, energia["descarga_bateria"].values[0], 3)
        self.assertAlmostEqual(exp_inj_rede, energia["injeccao_rede"].values[0], 3)
        self.assertAlmostEqual(exp_consumo_rede, energia["consumo_rede"].values[0], 3)
        self.assertAlmostEqual(exp_soc, energia["soc"].values[0], 3)

    @parameterized.expand([
        # sem eficiencia inversor
        (pd.DataFrame({"consumo":[1.], "autoproducao":[1.5]}), 1.0,
         1.0, 0.0, 0.5), # pv > consumo
        (pd.DataFrame({"consumo":[1.], "autoproducao":[0.5]}), 1.0,
         0.5, 0.5, 0.0), # pv < consumo
        # com eficiencia inversor
        (pd.DataFrame({"consumo":[1.], "autoproducao":[1.5]}), 0.9,
         1.0, 0.0, 0.35), # pv > consumo
        (pd.DataFrame({"consumo":[1.], "autoproducao":[0.5]}), 0.9,
         0.45, 0.55, 0.0) # pv < consumo
    ])
    def test_despacho_sem_bateria(self, energia, ef_inv,
        exp_autoconsumo, exp_consumo_rede, exp_inj_rede):
        
        energia = ae.analisa_upac_sem_armazenamento(energia, eficiencia_inversor=ef_inv)

        self.assertAlmostEqual(exp_autoconsumo, energia["autoconsumo"].values[0], 3)
        self.assertAlmostEqual(exp_consumo_rede, energia["consumo_rede"].values[0], 3)
        self.assertAlmostEqual(exp_inj_rede, energia["injeccao_rede"].values[0], 3)
        
    @parameterized.expand([
        (pd.DataFrame({"consumo":[0.5], "autoproducao":[2.0]}), 1.0, 1.0, 0.9,
         0.5, 1.0, 0.0, 0.0, 0.4, 1.0),
        (pd.DataFrame({"consumo":[0.5], "autoproducao":[2.0]}), 1.0, 0.25, 1.0,
         0.5, 0.25, 0.0, 0.0, 1.25, 0.25)
    ])
    def test_pot_maxima_bateria(self, energia, pot_max, intervalo, ef_inv,
        exp_autoconsumo, exp_carrega_bat, exp_descarrega_bat, exp_consumo_rede, exp_inj_rede, exp_soc):
        
        bat = bateria.bateria(1.25, 0.1, 0.9, 1.0, pot_maxima=pot_max)

        energia = ae.analisa_upac_com_armazenamento(energia, bat, soc_0=0., eficiencia_inversor=ef_inv, intervalo=intervalo)

        self.assertAlmostEqual(exp_autoconsumo, energia["autoconsumo"].values[0], 3)
        self.assertAlmostEqual(exp_carrega_bat, energia["carga_bateria"].values[0], 3)
        self.assertAlmostEqual(exp_descarrega_bat, energia["descarga_bateria"].values[0], 3)
        self.assertAlmostEqual(exp_inj_rede, energia["injeccao_rede"].values[0], 3)
        self.assertAlmostEqual(exp_consumo_rede, energia["consumo_rede"].values[0], 3)
        self.assertAlmostEqual(exp_soc, energia["soc"].values[0], 3)


    @parameterized.expand([
        (1.0, 0.0, 1.0, 2.0), # DoD = 1kWh, carrega 2kWh
        (1.0, 0.2, 0.8, 1.2)  # DoD = 0.6 kWh, carrega 1.2kWh
    ])
    def test_ciclos_bateria(self, cap_total, soc_min, soc_max, exp_n_ciclos):
        energia = pd.DataFrame({
            "time": ["2010-10-10 06:00", "2010-10-10 12:00", "2010-10-10 18:00", "2010-10-10 22:00"],
            "consumo":[0., 2., 0., 2.],
            "autoproducao":[4., 0., 4., 0.],
        })
        energia["time"] = pd.to_datetime(energia["time"])
        energia = energia.set_index("time")

        bat = bateria.bateria(cap_total, soc_min, soc_max)
        energia = ae.analisa_upac_com_armazenamento(energia, bateria=bat, soc_0=0)
        ind = ae.calcula_indicadores_autoconsumo(energia, 2., 1.0, bat)

        self.assertAlmostEqual(exp_n_ciclos, ind.num_ciclos_bateria, 1)
    
    def test_indicadores_autoconsumo(self):
        energia = pd.DataFrame({
            "time": ["2010-10-10 06:00", "2010-10-10 12:00"],
            "consumo":[1., 2.],
            "autoproducao":[3., 1.],
            "autoconsumo":[1., 1.9],
            "consumo_rede":[0., 0.1],
            "injeccao_rede":[1., 0.],
            "carga_bateria":[1., 0.],
            "descarga_bateria":[0., 0.9],
            "soc":[1.0, 0.0]
        })
        energia["time"] = pd.to_datetime(energia["time"])
        energia = energia.set_index("time")

        bat = bateria.bateria(1.0, 0.0, 1.0, 0.9)

        ind = ae.calcula_indicadores_autoconsumo(energia, 1.0, 0.98, bat, 1.0)

        self.assertAlmostEqual(4.0, ind.energia_autoproduzida, 1)
        self.assertAlmostEqual(2.9, ind.energia_autoconsumida, 1)
        self.assertAlmostEqual(4.0, ind.horas_equivalentes, 1)
        self.assertAlmostEqual(0.08, ind.energia_perdida_inversor, 2)
        self.assertAlmostEqual(0.1, ind.energia_perdida_bateria, 2)
        self.assertAlmostEqual(0.9, ind.energia_fornecida_bateria, 1)

        ind.print_markdown()

    def test_indicadores_autoconsumo_bihorario(self):
        energia = pd.DataFrame({
            "time": ["2010-10-10 06:00", "2010-10-10 12:00"],
            "consumo":[2., 3.],
            "autoproducao":[3., 1.],
            "autoconsumo":[1., 1.9],
            "consumo_rede":[1., 1.1],
            "injeccao_rede":[1., 0.],
            "carga_bateria":[1., 0.],
            "descarga_bateria":[0., 0.9],
            "soc":[1.0, 0.0]
        })
        energia["time"] = pd.to_datetime(energia["time"])
        energia = energia.set_index("time")

        bat = bateria.bateria(1.0, 0.0, 1.0, 0.9)

        ind = ae.calcula_indicadores_autoconsumo(energia, 1.0, 0.98, bat, 1.0)

        self.assertAlmostEqual(5.0, ind.consumo_total, 1)
        self.assertAlmostEqual(2.1, ind.energia_rede, 1)
        self.assertAlmostEqual(1.0, ind.energia_rede_vazio, 1)
        self.assertAlmostEqual(1.1, ind.energia_rede_fora_vazio, 1)