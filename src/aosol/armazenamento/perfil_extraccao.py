""" Perfis de extracção normalizados de acordo com EN 16147:2011
"""
from enum import Enum
import os
import pandas as pd
from datetime import timedelta

class TipoPerfil(Enum):
    S = 0,
    M = 1,
    L = 2

class PerfilExtraccao:
    def __init__(self, tipo_perfil):
        """ Perfil de extracção.

        Args
        ----
        tipo_perfil: TipoPerfil
            O tipo de perfil a utilizar.
        """
        self.tipo = tipo_perfil
        arquivo_perfis = os.path.join(os.path.dirname(__file__), 'perfil_extraccao.csv')
        if not os.path.isfile(arquivo_perfis):
            raise Exception(f"PerfilExtraccao requer ficheiro csv {arquivo_perfis}.")
        
        df = pd.read_csv(arquivo_perfis)
        df['Hora inicio'] = pd.to_datetime(df['Hora inicio'], format='%H:%M').dt.time
        self.perfis = df.set_index('Hora inicio')

    def extraccao_aqs_intervalo(self, timestamp_inicio, duracao=1):
        """ Obtem o valor de extracção AQS [kWh] para o periodo de 1hr com inicio no timstamp
        para o perfil escolhido.

        Args
        ----
        timestamp_inicio : datetime
            Hora de inicio da extracção.
        duracao : int, default: 1
            Duração da extracção em horas. [h]
            
        Returns
        -------
        float
            Energia extraida para AQS durante o periodo indicado para o perfil escolhido.
        """
        hora_1 = timestamp_inicio.time()
        hora_2 = (timestamp_inicio + timedelta(hours=duracao)).time()
        
        return self.perfis[(self.perfis.index >= hora_1) & (self.perfis.index < hora_2)][self.tipo.name].sum()

    #     datetime_obj = datetime.combine(datetime.min, hora_1)
    #     datetime_obj = datetime_obj + timedelta(hours=1)
    #     hora_2 = datetime_obj.time()