# """ Contem funcoes para efectuar a analise energetica e calcular indicadores em pandas dataframes

# Colunas esperadas:
# para todos os sistemas:
#     consumo : consumo total [kWh]
#     autoproducao : producao total do sistema autoconsumo [kWh]
#     autoconsumo: quantidade produzida que é efectivamente consumida [kWh]
#     injeccao_rede: quantidade produzida que não é aproveitada ou injectada na rede [kWh]
#     consumo_rede: quantidade consumida da rede [kWh]
# para sistemas com armazenamento:
#     carga_bateria : energia armazenada na bateria
#     descarga_bateria : energia descarregada da bateria
#     soc : estado de carga da bateria no final to timestep
# """
import numpy as np
import pandas as pd
from IPython.display import display
from .indicadores_autoconsumo import indicadores_autoconsumo

def calcula_indicadores_autoconsumo(energia, capacidade_instalada):
    """ Calcula indicadores de autoconsumo:
        iac : indice auto consumo [%]
        ias : indice auto suficiencia [%]
        ier : indice entrega a rede [%]
        energia_autoconsumida : total energia autoconsumida [kWh]
        energia_rede : total energia consumida da rede [kWh]
        consumo_total : total energia consumida [kWh]

    Args:
    -----
    energia : pandas.DataFrame
        Series temporais energia. Colunas necessarias: consumo, autoproducao, autoconsumo, consumo_rede
    capacidade_instalada : float
        Capacidade instalada em kWp

    Returns:
    --------
    ind: indicadores de autoconsumo
        Indicadores de autoconsumo
    """
    # indice auto consumo
    iac = (energia["autoconsumo"].sum() / energia["autoproducao"].sum()) * 100.0

    # indice de auto suficiencia
    ias = (energia["autoconsumo"].sum() / energia["consumo"].sum()) * 100.0

    # indice entrega a rede
    ier = 100.0 - iac

    # total energia auto consumida
    energia_autoproduzida = energia["autoproducao"].sum()
    energia_autoconsumida = energia["autoconsumo"].sum()
    energia_rede = energia["consumo_rede"].sum()
    consumo_total = energia["consumo"].sum()
    return indicadores_autoconsumo(iac, ias, ier, capacidade_instalada, energia_autoproduzida, energia_autoconsumida, energia_rede, consumo_total)

def calcula_indicadores_autoconsumo_com_armazenamento(energia_armaz, bat, capacidade_instalada):
    """ Calcula indicadores de autoconsumo com armazenamento:
    
    Calcula os indicadores de autoconsumo mais os correspondentes à bateria:
        horas_carga_min : numero de horas da bateria à carga minima (SOC min)
        perc_carga_min : percentagem do ano à carga miniam [%]
        horas_carga_max : numero de horas da bateria à carga máxima (SOC max)
        perc_carga_max : percenragem do ano à carga máxima [%]
        num_ciclos : numero de ciclos de carregamento da bateria em 1 ano

    Args:
        energia_armaz : dataframe de energia e armazenamento: Colunas necessarias: consumo, autoproducao, autoconsumo, consumo_rede, soc
        bat: objecto bateria
        capacidade_instalada : capacidade instalada em kWp
    Returns:
        indicadores de autoconsumo
    """
    # indicadores sem armazenamento
    sem = calcula_indicadores_autoconsumo(energia_armaz, capacidade_instalada)

    # numero de horas à carga minima
    n_horas_min = energia_armaz[energia_armaz['soc'] <= bat.get_soc_min()].shape[0]
    n_horas_max = energia_armaz[energia_armaz['soc'] >= bat.get_soc_max()].shape[0]
    n_ciclos = bat.get_ciclos_carregamento()

    return indicadores_autoconsumo(sem.iac, sem.ias, sem.ier, sem.capacidade_instalada, sem.energia_autoproduzida, sem.energia_autoconsumida, sem.energia_rede, sem.consumo_total, True, n_horas_min, n_horas_max, n_ciclos)

def analisa_upac_sem_armazenamento(energia):
    """ Analisa uma UPAC sem armazenamento.

    Algoritmo para autoconsumo sem armazenamento. Fonte: J Carvalho (2018) Armazenamento em Auto Consumo
    Dadas as series de:
        - consumo : consumo total [kWh]
        - autoproducao : producao total do sistema autoconsumo [kWh]
    Calcula:
        - autoconsumo: quantidade produzida que é efectivamente consumida [kWh]
        - injeccao_rede: quantidade produzida que não é aproveitada [kWh]
        - consumo_rede: quantidade consumida da rede [kWh]

    Args:
        energia : data frame com as series de consumo e autoproducao
    Returns:
        A data frame original com as series de autoconsumo, injeccao_rede e consumo_rede
    """
    # Algoritmo:
    #     Autoconsumo:
    #     If (consumo > autoproducao)
    #     {
    #         autoconsumo = autoproducao
    #     }
    #     Else
    #     {
    #         autoconsumo = consumo 
    #     }
    #
    #     Injeccao_rede:
    #     If (autoproducao - consumo > 0)
    #     {
    #         injeccao_rede = autoproducao - consumo
    #     }
    #     Else
    #     {
    #         injeccao_rede = 0
    #     }
    #
    #     Consumo_rede:
    #     If (consumo - autoproducao > 0)
    #     {
    #         consumo_rede = consumo - autoproducao
    #     }
    #     Else
    #     {
    #         consumo_rede = 0
    #     }

    # Auto consumo
    energia['autoconsumo'] = np.where(energia['consumo'] > energia['autoproducao'], energia['autoproducao'], energia['consumo'])

    # Injeccao na rede, energia nao utilizada
    energia['injeccao_rede'] = np.where(energia['autoproducao'] - energia['consumo'] > 0, energia['autoproducao'] - energia['consumo'], 0.0)

    # Consumo rede
    energia['consumo_rede'] = np.where(energia['consumo'] - energia['autoproducao'] > 0, energia['consumo'] - energia['autoproducao'], 0.0)
    return energia

def analisa_upac_com_armazenamento(energia, bateria):
    """ Analisa uma UPAC com armazenamento.

    Algoritmo para autoconsumo com armazenamento. Fonte: J Carvalho (2018) Armazenamento em Auto Consumo
    Dadas as series de:
        - consumo : consumo total [kWh]
        - autoproducao : producao total do sistema autoconsumo [kWh]
    Calcula:
        - autoconsumo : energia autoconsumida (PV + bateria)
        - injeccao_rede : energia desperdicada
        - consumo_rede : energia consumida da rede
        - carga_bateria : energia armazenada na bateria
        - descarga_bateria : energia descarregada da bateria
        - soc : estado de carga da bateria no final to timestep

    Args:
        energia : data frame com as series consumo e autoproducao
        bateria : objecto bateria com capacidade e soc_min e soc_max
    Returns:
        data frame com as series calculadas
    """
    # Algoritmo:
    # If (autoproducao > consumo)
    # {
    #     excesso = autoproducao - consumo
    #     if (soc < SOC_max)
    #     {
    #         carga_bateria = carrega_bateria(excesso)
    #         if (excesso - carga_bateria > 0)
    #         {
    #             injeccao_rede = excesso - carga_bateria
    #         }
    #     }
    #     else
    #     {
    #         carga_bateria = 0
    #         injeccao_rede = excesso
    #     }
    # }
    # Else
    # {
    #     deficit = consumo - autoproducao
    #     if (soc > SOC_min)
    #     {
    #         descarga_bateria = descarrega_bateria(deficit)
    #         if (deficit - descarga_bateria > 0)
    #         {
    #             consumo_rede = deficit - descarga_bateria
    #         }
    #     }
    #     else
    #     {
    #         descarga_bateria = 0
    #         consumo_rede = deficit
    #     }
    # }
    #
    # Autoconsumo:
    # If (consumo > autoproducao)
    # {
    #     autoconsumo = autoproducao + descarga_bateria
    # }
    # Else
    # {
    #     autoconsumo = consumo
    # }
    
    for index, row in energia.iterrows():
        descarga_bateria = 0
        carga_bateria = 0
        soc_bateria = bateria.get_soc()
        injeccao_rede = 0
        consumo_rede = 0
        # calcula comportamento bateria
        if (row['autoproducao'] > row['consumo']):
            excesso = row['autoproducao'] - row['consumo']
            if (soc_bateria < bateria.get_soc_max()):
                carga_bateria = bateria.carrega_bateria(excesso)
                soc_bateria = bateria.get_soc()
                # conseguimos guardar tudo na bateria ou enviamos para a rede            
                if (carga_bateria - excesso > 0):
                    injeccao_rede = carga_bateria - excesso
            else:
                carga_bateria = 0
                injeccao_rede = excesso
        else: # caso descarga bateria
            deficit = row['consumo'] - row['autoproducao']
            #
            consumo_rede = 0
            soc_bateria = bateria.get_soc()
            if (soc_bateria > bateria.get_soc_min()):
                descarga_bateria = bateria.descarrega_bateria(deficit)
                soc_bateria = bateria.get_soc()
                if (deficit - descarga_bateria > 0):
                    consumo_rede = deficit - descarga_bateria
            else:
                descarga_bateria = 0
                consumo_rede = deficit
        # calcula autoconsumo
        autoconsumo = 0
        consumo_pv = 0
        if (row['consumo'] > row['autoproducao']):
            consumo_pv = row['autoproducao']
            autoconsumo = row['autoproducao'] + descarga_bateria
        else:
            consumo_pv = row['consumo']
            autoconsumo = row['consumo']

        # guardar na dataframe
        energia.loc[index, 'autoconsumo'] = autoconsumo
        energia.loc[index, 'consumo_pv'] = consumo_pv
        energia.loc[index, 'injeccao_rede'] = injeccao_rede
        energia.loc[index, 'consumo_rede'] = consumo_rede
        energia.loc[index, 'carga_bateria'] = carga_bateria
        energia.loc[index, 'descarga_bateria'] = descarga_bateria
        energia.loc[index, 'soc'] = soc_bateria

    return energia

def calcula_12x24(energia, col):
    """ Calcula matriz 12 meses x 24 horas
    Args:
        energia: dataframe com a serie temporal de enerugia
        col: nome da coluna a calcular
    Return:
        dataframe com medias energia por hora por mes
    """
    d_12x24 = energia.groupby([energia.index.month, energia.index.hour])[col].mean()
    d_12x24.index.names = ["mes", "hora"]
    d_12x24 = d_12x24.unstack("mes")
    return d_12x24

def calcula_7x24(energia, col):
    """ Calcula matriz 7 dias x 24 horas

    Args:
        energia: dataframe com a serie temporal de enerugia
        col: nome da coluna a calcular
    Return:
        dataframe com medias energia por hora por dia da semana

    """
    d_7x24 = energia.groupby([energia.index.day_name(), energia.index.hour])[col].mean()
    d_7x24.index.names = ["dia", "hora"]
    d_7x24 = d_7x24.unstack().T
    d_7x24 = d_7x24[['Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday']]
    return d_7x24
    
def print_matriz(mat, cmap='bwr'):
    """ Display da matriz 12x24 com color map

    Args:
        d_12x24: dataframe matriz 12x24 ou 7x24
        cmap: colormap, por defeito bwr (blue white green), outra opcao RdYlGn
    """
    # outro colormap 'RdYlGn' - red yellow green
    display(mat.style.format("{:.3f}").background_gradient(cmap, axis=None))

