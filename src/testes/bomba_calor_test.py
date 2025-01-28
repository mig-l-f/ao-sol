from datetime import datetime
import unittest
from parameterized import parameterized
from aosol.armazenamento.bomba_calor_aqs import BombaCalorAqs, ParametrosBombaCalor, ModoOperacaoBombaCalor
from aosol.armazenamento.perfil_extraccao import PerfilExtraccao, TipoPerfil
from aosol.analise import analise_bomba_calor as abc
import pandas as pd
from datetime import datetime, timedelta

class TestBombaCalor(unittest.TestCase):

    def test_temperatura_sala_diferentes_locais(self):
        # diferentes bU
        bU_int = 0
        bU_nao_aquecido = 0.5
        bU_ext = 1

        # when
        bc_int = BombaCalorAqs(0.0, 0.0, 0.0, None, 0.0, bU_int)
        bc_nao_aquec = BombaCalorAqs(0.0, 0.0, 0.0, None, 0.0, bU_nao_aquecido)
        bc_ext = BombaCalorAqs(0.0, 0.0, 0.0, None, 0.0, bU_ext)

        # then
        self.assertAlmostEqual(20.0, bc_int.calcula_temperatura_sala_deposito(20.0, 7.04), 2)
        self.assertAlmostEqual(13.52, bc_nao_aquec.calcula_temperatura_sala_deposito(20.0, 7.04), 2)
        self.assertAlmostEqual(7.04, bc_ext.calcula_temperatura_sala_deposito(20.0, 7.04), 2)

    def test_analise_bomba_calor_2_timesteps_modo_eco(self):
        # dataframe que simula 2 timestamp em modo ECO
        df = pd.DataFrame({
            'Timestamp': ['05/jan/2021 00:00', '05/jan/2021 01:00'],
            'autoproducao': [0.0, 0.0],
            't_ext': [8.0, 7.04],
            'modo_op': [ModoOperacaoBombaCalor.ECO, ModoOperacaoBombaCalor.ECO]
        })
        df['Timestamp'] = pd.to_datetime(df['Timestamp'])
        df = df.set_index('Timestamp')

        params = ParametrosBombaCalor()
        params.SP1 = 50.0
        params.SP3 = 45.0
        bc = BombaCalorAqs(1.55, 3.6, 1.5, params, 0.152, 0.5)
        t_int = 20.0
        perfilL = PerfilExtraccao(TipoPerfil.L)

        # when
        df = abc.analisa_consumo_bomba_calor(df, bc, t_int, perfilL)
        
        # then
        self.assertEqual(2, df.size / len(df.columns))

        # timestep 0
        self.assertAlmostEqual(14.0, df['t_deposito'].iloc[0], 3)           # T_s(i+1)
        self.assertAlmostEqual(14.0, df['t_sala'].iloc[0], 2)            # T_room,s
        #self.assertAlmostEqual(0.0, df['energia_dep'].iloc[0], 3)    # E_s(i)
        self.assertAlmostEqual(0.0, df['energia_perd_dep'].iloc[0], 4) # E_lost,s
        self.assertAlmostEqual(0.0, df['energia_extr_aqs'].iloc[0], 2)    # E_lost,aqs
        self.assertAlmostEqual(1.55, df['energia_bc'].iloc[0], 2)         # E_hp(i)
        self.assertAlmostEqual(0.0, df['energia_resist'].iloc[0], 2)
        self.assertAlmostEqual(0.431, df['energia_usada_bc'].iloc[0], 3)

        # timestep 1
        self.assertAlmostEqual(22.78, df['t_deposito'].iloc[1], 2)           # T_s(i+1)
        self.assertAlmostEqual(13.52, df['t_sala'].iloc[1], 2)            # T_room,s
        #self.assertAlmostEqual(0.0, df['energia_dep'].iloc[1], 3)    # E_s(i)
        self.assertAlmostEqual(0.0134, df['energia_perd_dep'].iloc[1], 4) # E_lost,s
        self.assertAlmostEqual(0.0, df['energia_extr_aqs'].iloc[1], 2)    # E_lost,aqs
        self.assertAlmostEqual(1.55, df['energia_bc'].iloc[1], 2)         # E_hp(i)
        self.assertAlmostEqual(0.0, df['energia_resist'].iloc[1], 2)
        self.assertAlmostEqual(0.431, df['energia_usada_bc'].iloc[1], 3)

    def test_avalia_1_timestep_com_extraccao_temp_abaixo_limite(self):
        df = pd.DataFrame({
            'Timestamp': ['05/jan/2021 07:00'],
            'autoproducao': [0.0],
            't_ext': [6.8]
        })

        params = ParametrosBombaCalor()
        params.SP1 = 50.0
        params.SP3 = 45.0
        bc = BombaCalorAqs(1.55, 3.6, 1.5, params, 0.152, 0.5)

        # When
        t_sala = bc.calcula_temperatura_sala_deposito(20.0, df['t_ext'].iloc[0])
        t_deposito_ant = 50.0
        t_deposito = 49.69680353
        energia_extr_aqs = 1.715
        ts_prox, energia_bc, energia_resist, energia_usada_bc, \
        energia_perd_dep = bc.calcula_temperatura_deposito_intervalo(t_sala, t_deposito, t_deposito_ant, \
                                                      energia_extr_aqs, ModoOperacaoBombaCalor.ECO, ModoOperacaoBombaCalor.ECO)

        # Then
        self.assertAlmostEqual(48.46, ts_prox, 2)
        self.assertAlmostEqual(0.053, energia_perd_dep, 3)
        self.assertAlmostEqual(1.55, energia_bc, 2)
        self.assertAlmostEqual(0.0, energia_resist, 2)
        self.assertAlmostEqual(0.431, energia_usada_bc, 3)

    def test_perfil_extraccao_s(self):
        # given
        perfil = PerfilExtraccao(TipoPerfil.S)

        # when
        self.assertAlmostEqual(0.210, perfil.extraccao_aqs_intervalo(datetime(2010, 10, 10, 7, 00, 00)), 3)
        self.assertAlmostEqual(0.42, perfil.extraccao_aqs_intervalo(datetime(2010, 10, 10, 20, 30, 00)), 3)
        self.assertAlmostEqual(2.1, perfil.extraccao_aqs_intervalo(datetime(2010, 10, 10, 7, 00, 00), 15), 3) # dia completo

    def test_perfil_extraccao_m(self):
        perfil = PerfilExtraccao(TipoPerfil.M)

        self.assertAlmostEqual(1.610, perfil.extraccao_aqs_intervalo(datetime(2010, 10, 10, 7, 00, 00)), 3)
        self.assertAlmostEqual(5.845, perfil.extraccao_aqs_intervalo(datetime(2010, 10, 10, 7, 00, 00), 15), 3) # dia completo

    def test_perfil_extraccao_l(self):
        perfil = PerfilExtraccao(TipoPerfil.L)

        self.assertAlmostEqual(4.13, perfil.extraccao_aqs_intervalo(datetime(2010, 10, 10, 8, 00, 00), 2), 3)
        self.assertAlmostEqual(11.655, perfil.extraccao_aqs_intervalo(datetime(2010, 10, 10, 7, 00, 00), 15), 3) # dia completo

    def test_calcula_indicadores_bc(self):
        df = pd.DataFrame({
            "time": ['2010-01-01 10:00:00', '2010-01-02 10:00:00', '2010-01-03 10:00:00'],
            "t_deposito": [50.0, 45.0, 39.0],
            "energia_extr_aqs": [5.0, 5.0, 5.0],
            "energia_bc" : [4.0, 4.0, 4.0],
            "energia_resist": [1.0, 1.0, 1.0],
            "energia_usada_bc": [0.5, 0.5, 0.5],
            "energia_perd_dep": [0.05, 0.04, 0.01]
        })

        df["time"] = pd.to_datetime(df["time"])
        df = df.set_index("time")

        ind = abc.calcula_indicadores_bomba_calor(df, 40.0)

        self.assertEqual(3, ind.n_dias)
        self.assertAlmostEqual(3.33, ind.scop, 2)
        self.assertAlmostEqual(12.0, ind.energia_term_bc, 1)
        self.assertAlmostEqual(1.5, ind.energia_elec_bc, 1)
        self.assertAlmostEqual(3.0, ind.energia_elec_resist, 1)
        self.assertAlmostEqual(0.1, ind.energia_perd_dep, 1)
        self.assertAlmostEqual(0.2, ind.frac_backup)
        # Quantidades por dia
        self.assertAlmostEqual(4.0, ind.energia_term_bc_p_dia, 1)
        self.assertAlmostEqual(0.5, ind.energia_elec_bc_p_dia, 1)
        self.assertAlmostEqual(1.0, ind.energia_elec_resist_p_dia, 1)
        self.assertAlmostEqual(0.033, ind.energia_perd_dep_p_dia, 3)

        self.assertEqual(1, ind.n_horas_min)

    @parameterized.expand([
        (30.0, 1, True),
        (51.0, 1, True), # Perto do maximo
        (52.0, 1, False), # Já no máximo
        (50.0, -1, False), # Ainda dentro da hysterese
        (46.5, -1, True) # Ja abaixo hysterese 
    ])
    def test_control_bc_sem_resist(self, t_dep, t_dep_deriv, expec_bc_on):
        params = ParametrosBombaCalor()
        params.SP1 = 52.0
        params.r0 = 5.0 # 47.0
        params.SP3 = 45.0
        params.usa_resist = False

        bc = BombaCalorAqs(1.55, 3.6, 1.5, params, 0.152, 0.5)
        pot_bc = bc._potencia_bomba_calor(t_dep_deriv, t_dep, params.SP1, params.SP1-params.r0, ModoOperacaoBombaCalor.ECO, ModoOperacaoBombaCalor.ECO)

        if (expec_bc_on):
            self.assertAlmostEqual(1.55, pot_bc, 2)
        else:
            self.assertAlmostEqual(0.0, pot_bc, 2)



