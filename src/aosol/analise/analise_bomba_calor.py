""" Análise ao desempenho de bomba de calor para AQS.

References
----------

.. [6] Naldi, Claudia & Morini, Gian & Zanchini, E.. (2014). 
       A method for the choice of the optimal balance-point temperature of air-to-water heat pumps for heating. 
       Sustainable Cities and Society. Em https://doi.org/10.1016/j.scs.2014.02.005
"""
import aosol.armazenamento.bomba_calor_aqs
import aosol.armazenamento.perfil_extraccao
from aosol.analise.indicadores_bomba_calor import indicadores_bomba_calor
import sys

def analisa_consumo_bomba_calor(energia, bc, t_int, perfil_extraccao, t_deposito_inicial=-1.0, col_temp_ext='t_ext'):
      """ Analisa o consumo eléctrico da bomba de calor (BC) a partir de dados de temperatura exterior 
      num intervalo horário aplicando um modelo semelhante a [6]_.

      Se a dataframe já contêm dados de consumo, o consumo da BC é adicionado ao mesmo caso contrário é criada essa coluna.
      A dataframe deve conter as colunas:

      - t_ext : temperatura exterior [ºC]

      Produz uma dataframe com as seguintes colunas:

      - consumo : consumo electrico da BC [kWh].
      - t_deposito : tempetura do depósito [ºC].
      - t_sala : temperatura do local onde está o depósito [ºC].
      - energia_perd_dep : energia perdida pelo depósito [kWh].
      - energia_extr_aqs : energia extraida para AQS [kWh].
      - energia_bc : energia térmica fornecida pela BC [kWh].
      - energia_resist : energia fornecida pela resistência eléctrica [kWh].
      - energia_usada_bc : energia eléctrica consumida pela BC [kWh].

      Parameters
      ----------
      energia: pd.DataFrame
            Dataframe com serie de temperatura exterior.
      bc : BombaCalor
            A bomba de calor a simular.
      t_int : float
            Temperatura no interior do edificio [ºC]. Mantido constante durante toda a simulação.
      perfil_extraccao : PerfilExtraccao
            Perfil de extraccao AQS.
      t_deposito_inicial : float, default: -1.0
            Temperatura inicial do depósito, para inicializar o modelo. [ºC]
            Caso seja negativa é assumido a temperatura na sala onde está o depósito.
      col_temp_ext : str, default: t_ext
            Nome da coluna com temperatura exterior, por defeito é t_ext.

      Returns
      -------
      pd.Dataframe
            Dataframe com as colunas indicadas acima.
      """
      i = 0
      for index, row in energia.iterrows():
            t_sala = bc.calcula_temperatura_sala_deposito(t_int, row[col_temp_ext])
            if (i == 0):
                  if (t_deposito_inicial < 0.0):
                        t_deposito_ant = t_sala
                        t_deposito = t_sala
                  else:
                        t_deposito_ant = t_deposito_inicial
                        t_deposito = t_deposito_inicial
                  modo_op_anterior = row['modo_op']
                  modo_op = row['modo_op'] 
            else:
                  t_deposito_ant = t_deposito
                  t_deposito = ts_prox
                  modo_op_anterior = modo_op
                  modo_op = row['modo_op']

            energia_extr_aqs = perfil_extraccao.extraccao_aqs_intervalo(index)
            ts_prox, energia_bc, energia_resist, energia_usada_bc, \
            energia_perd_dep = bc.calcula_temperatura_deposito_intervalo(t_sala, t_deposito, t_deposito_ant, energia_extr_aqs, modo_op, modo_op_anterior)

            energia.loc[index, 't_deposito'] = t_deposito
            energia.loc[index, 't_sala'] = t_sala
            energia.loc[index, 'energia_perd_dep'] = energia_perd_dep
            energia.loc[index, 'energia_extr_aqs'] = energia_extr_aqs
            energia.loc[index, 'energia_bc'] = energia_bc
            energia.loc[index, 'energia_resist'] = energia_resist
            energia.loc[index, 'energia_usada_bc'] = energia_usada_bc

            i += 1

      return energia

def calcula_indicadores_bomba_calor(energia_bc, t_consumo=40):
      """ Calcula indicadores da bomba de calor.

      Parameters
      ----------
      energia_bc : pd.Dataframe
            Resultado da análise da bomba de calor.
      t_consumo : float, default: 40
            Temperatura de agua de consumo. [ºC]

      Returns
      -------
      indicadores_bomba_calor
            Indicadores obtidos da análise da bomba calor.
      """     
      e_tot_usada_bc = energia_bc["energia_usada_bc"].sum()
      e_tot_resist = energia_bc["energia_resist"].sum()
      e_extraida_bc = energia_bc["energia_extr_aqs"].sum()
      e_termica_bc = energia_bc["energia_bc"].sum()
      e_tot_perd_dep = energia_bc["energia_perd_dep"].sum()

      scop = e_extraida_bc / (e_tot_resist + e_tot_usada_bc)
      frac_resist = e_tot_resist / (e_termica_bc + e_tot_resist)
      n_horas_abaixo_min = (energia_bc['t_deposito'] < t_consumo-1e-5).sum()
      n_dias = (energia_bc.index[-1] - energia_bc.index[0]).days + 1 #inclusive

      return indicadores_bomba_calor(scop, e_termica_bc, e_tot_usada_bc, e_tot_resist, e_tot_perd_dep, frac_resist, n_horas_abaixo_min, n_dias)
                                   