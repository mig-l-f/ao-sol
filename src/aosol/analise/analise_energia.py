""" Módulo com as funções para efectuar a análise de energia, a partir das séries de consumo e autoprodução tanto
para UPAC com e sem bateria.

Contêm também as funções para calcular os indicadores de autoconsumo, produzir matrizes 12x24 e 7x12 e fazer
gráfico de barras com os vários usos da energia e imprimir tabelas em formaro html e markdown.

Notes
-----
As funções operam sobre dataframes pandas onde são esperadas as seguintes colunas

======================== ======== ==========================
Colunas                  Unidade  Descrição
======================== ======== ==========================
Para todos os tipos de sistemas:
------------------------------------------------------------
consumo                  kWh      consumo total
autoproducao             kWh      producao da UPAC
autoconsumo              kWh      energia produzida que é efectivamente consumida
injeccao_rede            kWh      energia produzida que não é aproveitada e é injectada na rede
consumo_rede             kWh      energia consumida da rede.
------------------------------------------------------------
Para sistemas com armazenamento:
------------------------------------------------------------
carga_bateria            kWh      energia armazenada na bateria
descarga_bateria         kWh      energia descarregada da bateria
soc                      %        estado de carga da bateria no final to timestep
======================== ======== ==========================
"""

import numpy as np
import pandas as pd
from IPython.display import HTML, display
from tabulate import tabulate
from .indicadores_autoconsumo import indicadores_autoconsumo

def calcula_indicadores_autoconsumo(energia, capacidade_instalada, calcula_p90=False):
    """ Calcula indicadores de autoconsumo para UPAC sem bateria.

    A partir de uma dataframe com as colunas para um sistema sem armazenamento, calcula
    os seguintes indicadores de autoconsumo calculados:
    - iac : indice auto consumo [%]
    - ias : indice auto suficiencia [%]
    - ier : indice entrega a rede [%]
    - energia_autoconsumida : total energia autoconsumida [kWh]
    - energia_rede : total energia consumida da rede [kWh]
    - consumo_total : total energia consumida [kWh]

    Parameters
    ----------
    energia : pandas.DataFrame
        Series temporais energia. Colunas necessarias: consumo, autoproducao, autoconsumo, consumo_rede
    capacidade_instalada : float
        Capacidade instalada em kWp
    calcula_p90: bool, default:False
        True para calcular os indicadores para P90, False para não calcular

    Returns
    -------
    ind : indicadores_autoconsumo
        Indicadores de autoconsumo para P50.
    ind_p90 : indicadores_autoconsumo
        Indicadores de autoconsumo para P90 se calcular_p90 é True, caso contrário None.
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

    ia = indicadores_autoconsumo(iac, ias, ier, capacidade_instalada, energia_autoproduzida, energia_autoconsumida, energia_rede, consumo_total)
    ia_p90 = None
    if calcula_p90:
        iac_p90 = (energia["autoconsumo_p90"].sum() / energia["autoproducao_p90"].sum()) * 100.0
        ias_p90 = (energia["autoconsumo_p90"].sum() / energia["consumo"].sum()) * 100.0
        ier_p90 = 100.0 - iac_p90
        energia_autoproduzida_p90 = energia["autoproducao_p90"].sum()
        energia_autoconsumida_p90 = energia["autoconsumo_p90"].sum()
        energia_rede_p90 = energia["consumo_rede_p90"].sum()
        ia_p90 = indicadores_autoconsumo(iac_p90, ias_p90, ier_p90, capacidade_instalada, energia_autoproduzida_p90, energia_autoconsumida_p90, energia_rede_p90, consumo_total)
    return ia, ia_p90

def calcula_indicadores_autoconsumo_com_armazenamento(energia_armaz, bat, capacidade_instalada, calcula_p90=False, bat_p90=None):
    """ Calcula indicadores de autoconsumo com armazenamento.

    A partir de um dataframe com as colunas para um sistema de armazenamento, 
    calcula os indicadores de autoconsumo mais os correspondentes à bateria:
    - horas_carga_min : numero de horas da bateria à carga minima (SOC min)
    - perc_carga_min : percentagem do ano à carga miniam [%]
    - horas_carga_max : numero de horas da bateria à carga máxima (SOC max)
    - perc_carga_max : percenragem do ano à carga máxima [%]
    - num_ciclos : numero de ciclos de carregamento da bateria em 1 ano

    Parameters
    ----------
    energia_armaz : pd.Dataframe
        Dataframe de energia e armazenamento: Colunas necessarias: consumo, autoproducao, autoconsumo, consumo_rede, soc
    bat : bateria
        Bateria para P50
    capacidade_instalada : float
        Capacidade instalada.  [kWp]
    calcula_p90 : bool, default: False
        Se calcula indicadores para P90.
    bat_p90 : bateria
        Bateria para P90 necessário se calcula_p90 = True

    Returns
    -------
    ind : indicadores de autoconsumo
        Indicadores de autoconsumo para P50.
    ind_p90 : indicadores de autoconsumo, optional
        Indicadors de autoconsumo para P90 se calcular_p90 é True, caso contrário none.
    """
    # indicadores sem armazenamento
    sem, sem_p90 = calcula_indicadores_autoconsumo(energia_armaz, capacidade_instalada, calcula_p90)

    # numero de horas à carga minima
    n_horas_min = energia_armaz[energia_armaz['soc'] <= bat.get_soc_min()].shape[0]
    n_horas_max = energia_armaz[energia_armaz['soc'] >= bat.get_soc_max()].shape[0]
    n_ciclos = bat.get_ciclos_carregamento()

    ia = indicadores_autoconsumo(sem.iac, sem.ias, sem.ier, sem.capacidade_instalada, sem.energia_autoproduzida, \
        sem.energia_autoconsumida, sem.energia_rede, sem.consumo_total, True, n_horas_min, n_horas_max, n_ciclos, bat.get_capacidade_bateria())
    ia_p90 = None
    if calcula_p90:
        n_horas_min_p90 = energia_armaz[energia_armaz['soc_p90'] <= bat_p90.get_soc_min()].shape[0]
        n_horas_max_p90 = energia_armaz[energia_armaz['soc_p90'] >= bat_p90.get_soc_max()].shape[0]
        n_ciclos_p90 = bat_p90.get_ciclos_carregamento()

        ia_p90 = indicadores_autoconsumo(sem_p90.iac, sem_p90.ias, sem_p90.ier, sem_p90.capacidade_instalada, \
            sem_p90.energia_autoproduzida, sem_p90.energia_autoconsumida, sem_p90.energia_rede, sem_p90.consumo_total, True, \
            n_horas_min_p90, n_horas_max_p90, n_ciclos_p90, bat_p90.get_capacidade_bateria())

    return ia, ia_p90

def analisa_upac_sem_armazenamento(energia):
    """ Analisa uma UPAC sem armazenamento.

    Algoritmo para autoconsumo sem armazenamento. Fonte: J Carvalho (2018) Armazenamento em Auto Consumo
    Dadas as series de:
    - consumo : consumo total [kWh]
    - autoproducao : producao total do sistema autoconsumo [kWh]
    - autoproducao_p90 : produção P90 da UPAC [kWh] (opcional)
    Calcula:
    - autoconsumo : quantidade produzida que é efectivamente consumida [kWh]
    - injeccao_rede : quantidade produzida que não é aproveitada [kWh]
    - consumo_rede : quantidade consumida da rede [kWh]
    Se autoproducao_p90 existir, calcula tb
    - autoconsumo_p90 : quantidade produzida que é efectivamente consumida [kWh]
    - injeccao_rede_p90 : quantidade produzida que não é aproveitada [kWh]
    - consumo_rede_90 : quantidade consumida da rede [kWh]

    Parameters
    ----------
    energia : pd.Dataframe
        Dataframe com as series de consumo e autoproducao.

    Returns
    -------
    pd.Dataframe
        A data frame original com as series adicionadas de autoconsumo, injeccao_rede e consumo_rede.
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
    col_autoprod = 'autoproducao'
    col_autoprod_p90 = 'autoproducao_p90'
    calcula_p90 = (col_autoprod_p90 in energia.columns)

    # Auto consumo
    energia['autoconsumo'] = np.where(energia['consumo'] > energia[col_autoprod], energia[col_autoprod], energia['consumo'])

    # Injeccao na rede, energia nao utilizada
    energia['injeccao_rede'] = np.where(energia[col_autoprod] - energia['consumo'] > 0, energia[col_autoprod] - energia['consumo'], 0.0)

    # Consumo rede
    energia['consumo_rede'] = np.where(energia['consumo'] - energia[col_autoprod] > 0, energia['consumo'] - energia[col_autoprod], 0.0)

    if calcula_p90:
        energia['autoconsumo_p90'] = np.where(energia['consumo'] > energia[col_autoprod_p90], energia[col_autoprod_p90], energia['consumo'])
        energia['injeccao_rede_p90'] = np.where(energia[col_autoprod_p90] - energia['consumo'] > 0, energia[col_autoprod_p90] - energia['consumo'], 0.0)    
        energia['consumo_rede_p90'] = np.where(energia['consumo'] - energia[col_autoprod_p90] > 0, energia['consumo'] - energia[col_autoprod_p90], 0.0)

    return energia

def analisa_upac_com_armazenamento(energia, bateria, calcula_p90=False, bateria_p90=None):
    """ Analisa uma UPAC com armazenamento.

    Algoritmo para autoconsumo com armazenamento. Fonte: J Carvalho (2018) Armazenamento em Auto Consumo
    Dadas as series de:
    - consumo : consumo total [kWh]
    - autoproducao : producao total do sistema autoconsumo [kWh]
    Calcula:
    - autoconsumo : energia autoconsumida (PV + bateria) [kWh]
    - injeccao_rede : energia desperdicada [kWh]
    - consumo_rede : energia consumida da rede [kWh]
    - carga_bateria : energia armazenada na bateria [kWh]
    - descarga_bateria : energia descarregada da bateria [kWh]
    - soc : estado de carga da bateria no final to timestep [%]

    Parameters
    ----------
    energia : pd.DataFrame
        Data frame com as series consumo e autoproducao.
    bateria : bateria
        Objecto bateria com capacidade e soc_min e soc_max
    calcula_p90 : bool, default: False
        Se devemos calcular series P90, necessita coluna autoproducao_p90
    bateria_p90 : bateria, default: None
        Objecto bateria com capacidade e soc_min e soc_max para calculos P90. Tem de ser especificado se calcula_p90 = True

    Returns
    -------
    pd.DataFrame
        Data frame com as series calculadas.
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
        autoconsumo, consumo_pv, injeccao_rede, consumo_rede, \
        carga_bateria, descarga_bateria, soc_bateria = _calcula_timestep_upac_com_armazenamento(row, 'consumo', 'autoproducao', bateria)

        # guardar na dataframe
        energia.loc[index, 'autoconsumo'] = autoconsumo
        energia.loc[index, 'consumo_pv'] = consumo_pv
        energia.loc[index, 'injeccao_rede'] = injeccao_rede
        energia.loc[index, 'consumo_rede'] = consumo_rede
        energia.loc[index, 'carga_bateria'] = carga_bateria
        energia.loc[index, 'descarga_bateria'] = descarga_bateria
        energia.loc[index, 'soc'] = soc_bateria

        if calcula_p90:
            autoconsumo_p90, consumo_pv_p90, injeccao_rede_p90, consumo_rede_p90, \
            carga_bateria_p90, descarga_bateria_p90, soc_bateria_p90 = _calcula_timestep_upac_com_armazenamento(row, 'consumo', 'autoproducao_p90', bateria_p90)

            # guardar na dataframe
            energia.loc[index, 'autoconsumo_p90'] = autoconsumo_p90
            energia.loc[index, 'consumo_pv_p90'] = consumo_pv_p90
            energia.loc[index, 'injeccao_rede_p90'] = injeccao_rede_p90
            energia.loc[index, 'consumo_rede_p90'] = consumo_rede_p90
            energia.loc[index, 'carga_bateria_p90'] = carga_bateria_p90
            energia.loc[index, 'descarga_bateria_p90'] = descarga_bateria_p90
            energia.loc[index, 'soc_p90'] = soc_bateria_p90

    return energia

def _calcula_timestep_upac_com_armazenamento(row, col_consumo, col_autoproducao, bateria):
    """ Calcula comportamento bateria em um timestep.
    """
    descarga_bateria = 0
    carga_bateria = 0
    soc_bateria = bateria.get_soc()
    injeccao_rede = 0
    consumo_rede = 0
    # calcula comportamento bateria
    if (row[col_autoproducao] > row[col_consumo]):
        excesso = row[col_autoproducao] - row[col_consumo]
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
        deficit = row[col_consumo] - row[col_autoproducao]
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
    if (row[col_consumo] > row[col_autoproducao]):
        consumo_pv = row[col_autoproducao]
        autoconsumo = row[col_autoproducao] + descarga_bateria
    else:
        consumo_pv = row[col_consumo]
        autoconsumo = row[col_consumo]
    
    return autoconsumo, consumo_pv, injeccao_rede, consumo_rede, carga_bateria, descarga_bateria, soc_bateria

def calcula_12x24(energia, col):
    """ Calcula matriz 12 meses x 24 horas.

    Parameters
    ----------
    energia: pandas.Dataframe
        Dataframe com a serie temporal de energia.
    col: str 
        Nome da coluna a calcular.
    
    Returns
    -------
    pd.DataFrame
        Dataframe com médias de energia por hora por mes.
    """
    d_12x24 = energia.groupby([energia.index.month, energia.index.hour])[col].mean()
    d_12x24.index.names = ["mes", "hora"]
    d_12x24 = d_12x24.unstack("mes")
    return d_12x24

def calcula_7x24(energia, col):
    """ Calcula matriz 7 dias x 24 horas

    Parameters
    ----------
    energia: pd.Dataframe
        Dataframe com a serie temporal de energia.
    col: str
        Nome da coluna a calcular

    Returns
    -------
    pd.DataFrame
        Dataframe com médias de energia por hora por dia da semana.
    """
    d_7x24 = energia.groupby([energia.index.day_name(), energia.index.hour])[col].mean()
    d_7x24.index.names = ["dia", "hora"]
    d_7x24 = d_7x24.unstack().T
    d_7x24 = d_7x24[['Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday']]
    return d_7x24
    
def print_matriz(mat, cmap='bwr'):
    """ Display da matriz 12x24 com color map.

    Parameters
    ----------
    d_12x24: pd.Dataframe
        Dataframe matriz 12x24 ou 7x24
    cmap: str, default: 'bwr'
        Colormap, por defeito bwr (blue white red), outra opcao RdYlGn
    """
    # outro colormap 'RdYlGn' - red yellow green
    display(mat.style.format("{:.3f}").background_gradient(cmap, axis=None))

def plot_energia_mensal_bars(ax, energia_mensal, consumo_mensal, producao_mensal, nome_cols=["consumo_rede", "autoconsumo", "injeccao_rede"], width=0.5, offset=0, font=8):
    """ Bar plot de consumo rede, autoconsumo e injeccao na rede para cada mes.

    Parameters
    ----------
    ax : plt.axes
        Objecto axes onde plotar.
    energia_mensal : pd.Dataframe
        Dataframe com valores de energia em kWh para cada mês para cada uma das colunas em nome_cols.
    consumo_mensal : pd.Dataframe
        Dataframe com valores de consumo energia para cada mês em kWh. Só pode ter 1 coluna.
    producao_mensal : pd.Dataframe
        Dataframe com valores de producao da UPAC para cada mês em kWh. Só pode ter 1 coluna.
    nome_cols : list, optional
        Lista com nome da colunas para consumo_rede, autoconsumo, injeccao_rede, descarga_bateria (opcional)
    """
    # colunas
    col_consumo = str(nome_cols[0])
    consumo_idx_cor = 0
    col_auto = str(nome_cols[1])
    auto_idx_cor = 1
    col_inj = str(nome_cols[2])
    inj_idx_cor = 2
    col_descarga = ''
    plot_descarga = False
    if len(nome_cols) == 4:
        plot_descarga = True
        col_descarga = str(nome_cols[3])
        descarga_idx_cor = 2
        inj_idx_cor = 3

    # cores
    cores = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728']

    # consumo rede (% consumo)
    label_consumo = f"{col_consumo.replace('_', ' ')} (% consumo)"
    c = ax.bar(energia_mensal.index.month-offset, energia_mensal[col_consumo], width=width, label=label_consumo, color=cores[consumo_idx_cor])
    per_cons = energia_mensal[col_consumo].div(consumo_mensal, axis=0).mul(100).round(0)
    labels = [f'{v.get_height():.0f}\n({row:.0f}%)' if v.get_height() > 0 else '' for v, row in zip(c, per_cons)]
    ax.bar_label(c, labels=labels, label_type='center', fontsize=font)
    bottom = energia_mensal[col_consumo]

    # autoconsumo (% consumo)
    label_auto = f"{col_auto.replace('_',' ')} (% consumo)"
    a = ax.bar(energia_mensal.index.month-offset, energia_mensal[col_auto], width=width, bottom=bottom, label=label_auto, color=cores[auto_idx_cor])
    per_auto = energia_mensal[col_auto].div(consumo_mensal, axis=0).mul(100).round(0)
    labels = [f'{v.get_height():.0f}\n({row:.0f}%)' if v.get_height() > 0 else '' for v, row in zip(a, per_auto)]
    ax.bar_label(a, labels=labels, label_type='center', fontsize=font)
    bottom += energia_mensal[col_auto]

    # descarga bateria (% de autoproducao) caso seja especificado
    if plot_descarga:
        label_descarga = f"{col_descarga.replace('_',' ')} (% consumo)"
        d = ax.bar(energia_mensal.index.month-offset, energia_mensal[col_descarga], width=width, bottom=bottom, label=label_descarga, color=cores[descarga_idx_cor])
        per_descarga = energia_mensal[col_descarga].div(consumo_mensal, axis=0).mul(100).round(0)
        labels = [f'{v.get_height():.0f}\n({row:.0f}%)' if v.get_height() > 0 else '' for v, row in zip(d, per_descarga)]
        ax.bar_label(d, labels=labels, label_type='center', fontsize=font)
        bottom += energia_mensal[col_descarga]

    # injeccao rede (% de autoproducao)    
    label_inj = f"{col_inj.replace('_', ' ')} (% producao)"
    i = ax.bar(energia_mensal.index.month-offset, energia_mensal[col_inj], width=width, bottom=bottom, label=label_inj, color=cores[inj_idx_cor])
    per_inj = energia_mensal[col_inj].div(producao_mensal, axis=0).mul(100).round(0)
    labels = [f'{v.get_height():.0f}\n({row:.0f}%)' if v.get_height() > 0 else '' for v, row in zip(i, per_inj)]
    ax.bar_label(i, labels=labels, label_type='center', fontsize=font)

    ax.legend(bbox_to_anchor =(0.5,-0.27), loc='lower center')
    ax.set_ylabel('Enegia [kWh]')
    ax.set_xlabel('mes')

def print_tabela_indicadores_html(ia, ia_p90 = None):
    """ Print tabela de indicadores de autoconsumo em formato html. Se especificado inclui coluna com P90.

    Parameters
    ----------
    ia : indicadores_autoconsumo
        Indicadores P50
    ia_p90 : indicadores_autoconsumo, default: None
        Indicadores P90, se especificado é adicionada coluna
    """
    print_p90 = (ia_p90 is not None)
    tabela = '<table style="font-size:16px">'
    tabela +='<tr>'
    tabela +='<td></td><td>P50</td>'
    if print_p90:
        tabela +='<td>P90</td>'    
    tabela +='</tr>'
    tabela +='<tr>'
    tabela +='<td>Potencia Instalada</td><td>{:.2f} kW</td>'.format(ia.capacidade_instalada)
    if print_p90:
        tabela +='<td>{:.2f} kW</td>'.format(ia_p90.capacidade_instalada)
    tabela +='</tr>'
    tabela +='<tr></tr>'
    tabela +='<tr>'
    tabela +='<td>Energia Autoproduzida [kWh]</td><td>{:.1f}</td>'.format(ia.energia_autoproduzida)
    if print_p90:
        tabela +='<td>{:.1f}</td>'.format(ia_p90.energia_autoproduzida)
    tabela +='</tr>'
    tabela +='<tr>'
    tabela +='<td>Energia Autoconsumida [kWh]</td><td>{:.1f}</td>'.format(ia.energia_autoconsumida)
    if print_p90:
        tabela +='<td>{:.1f}</td>'.format(ia_p90.energia_autoconsumida)
    tabela +='</tr>'
    tabela +='<tr>'
    tabela +='<td>Energia consumida rede [kWh]</td><td>{:.1f}</td>'.format(ia.energia_rede)
    if print_p90:
        tabela +='<td>{:.1f}</td>'.format(ia_p90.energia_rede)
    tabela +='</tr>'
    tabela +='<tr>'
    tabela +='<td>Energia consumida [kWh]</td><td>{:.1f}</td>'.format(ia.consumo_total)
    if print_p90:
        tabela +='<td>{:.1f}</td>'.format(ia_p90.consumo_total)
    tabela +='</tr>'
    tabela +='<tr></tr>'
    tabela +='<tr>'
    tabela +='<td>Numero de horas equivalentes [h/ano]</td><td>{:.1f}</td>'.format(ia.horas_equivalentes)
    if print_p90:
        tabela +='<td>{:.1f}</td>'.format(ia_p90.horas_equivalentes)
    tabela +='</tr>'
    tabela +='<tr>'
    tabela +='<td>IAS: Contributo PV [%]</td><td>{:.1f}</td>'.format(ia.ias)
    if print_p90:
        tabela +='<td>{:.1f}</td>'.format(ia_p90.ias)
    tabela +='</tr>'
    tabela +='<tr>'
    tabela +='<td>IAC: Indice Auto consumo [%]</td><td>{:.1f}</td>'.format(ia.iac)
    if print_p90:
        tabela +='<td>{:.1f}</td>'.format(ia_p90.iac)
    tabela +='</tr>'
    tabela +='<tr>'
    tabela +='<td>IER: Producao PV desperdicada [%]</td><td>{:.1f}</td>'.format(ia.ier)
    if print_p90:
        tabela +='<td>{:.1f}</td>'.format(ia_p90.ier)
    tabela +='</tr>'
    if (ia.com_armazenamento):
        tabela += '<tr><td>Bateria:</td><td></td><td></td></tr>'
        tabela += '<tr>'
        tabela += '<td>Capacidade [kWh]</td><td>{:.2f}</td>'.format(ia.capacidade_bateria)
        if print_p90:
            tabela += '<td>{:.2f}</td>'.format(ia_p90.capacidade_bateria)
        tabela += '</tr>'
        tabela += '<tr>'
        tabela += '<td>Em carga minima</td><td>{:.1f} hr ({:.2f} %)</td>'.format(ia.num_horas_carga_min, ia.perc_horas_carga_min)
        if print_p90:
            tabela += '<td>{:.1f} hr ({:.2f} %)</td>'.format(ia_p90.num_horas_carga_min, ia_p90.perc_horas_carga_min)
        tabela += '</tr>'
        tabela += '<tr>'
        tabela += '<td>Em carga máxima</td><td>{:.1f} hr ({:.2f} %)</td>'.format(ia.num_horas_carga_max, ia.perc_horas_carga_max)
        if print_p90:
            tabela += '<td>{:.1f} hr ({:.2f} %)</td>'.format(ia_p90.num_horas_carga_max, ia_p90.perc_horas_carga_max)
        tabela += '</tr>'
        tabela += '<tr>'
        tabela += '<td>Ciclos da bateria</td><td>{}</td>'.format(ia.num_ciclos_bateria)
        if print_p90:
            tabela += '<td>{}</td>'.format(ia_p90.num_ciclos_bateria)
        tabela += '</tr>'
    tabela += '</table>'
    display(HTML(tabela))

def print_tabela_indicadores_markdown(ia, ia_p90=None):
    """ Print tabela de indicadores de autoconsumo em formato markdown. Se especificado inclui coluna com P90.

    Parameters
    ----------
    ia : indicadores_autoconsumo
        Indicadores P50.
    ia_p90 : indicadores_autoconsumo, default: None
        Indicadores P90, se especificado é adicionada coluna.
    """
    print_p90 = (ia_p90 is not None)
    headers = ['', 'P50']
    tabela = [
        ['Potencia Instalada [kW]', '{:.2f}'.format(ia.capacidade_instalada)],
        ['Energia Autoproduzida [kWh]', '{:.1f}'.format(ia.energia_autoproduzida)],
        ['Energia Autoconsumida [kWh]', '{:.1f}'.format(ia.energia_autoconsumida)],
        ['Energia consumida rede [kWh]', '{:.1f}'.format(ia.energia_rede)],
        ['Energia consumida [kWh]', '{:.1f}'.format(ia.consumo_total)],      
        ['Numero de horas equivalentes [h/ano]', '{:.1f}'.format(ia.horas_equivalentes)],
        ['IAS: Contributo PV [%]', '{:.1f}'.format(ia.ias)],
        ['IAC: Indice Auto consumo [%]', '{:.1f}'.format(ia.iac)],
        ['IER: Producao PV desperdicada [%]', '{:.1f}'.format(ia.ier)]
    ]
    if print_p90:
        headers.append('P90')
        tabela[0].append('{:.2f}'.format(ia_p90.capacidade_instalada))
        tabela[1].append('{:.1f}'.format(ia_p90.energia_autoproduzida))
        tabela[2].append('{:.1f}'.format(ia_p90.energia_autoconsumida))
        tabela[3].append('{:.1f}'.format(ia_p90.energia_rede))
        tabela[4].append('{:.1f}'.format(ia_p90.consumo_total))
        tabela[5].append('{:.1f}'.format(ia_p90.horas_equivalentes))
        tabela[6].append('{:.1f}'.format(ia_p90.ias))
        tabela[7].append('{:.1f}'.format(ia_p90.iac))
        tabela[8].append('{:.1f}'.format(ia_p90.ier))
    print(tabulate(tabela, tablefmt="github", headers=headers))

    if (ia.com_armazenamento):
        headers = ['Bateria:','P50']
        bateria = [
            ['Capacidade [kWh]', '{:.2f}'.format(ia.capacidade_bateria)],
            ['Em carga minima','{:.1f} hr ({:.2f} %)'.format(ia.num_horas_carga_min, ia.perc_horas_carga_min)],
            ['Em carga máxima','{:.1f} hr ({:.2f} %)'.format(ia.num_horas_carga_max, ia.perc_horas_carga_max)],
            ['Ciclos da bateria','{}'.format(ia.num_ciclos_bateria)]
        ]
        if print_p90:
            headers.append('P90')
            bateria[0].append('{:.2f}'.format(ia_p90.capacidade_bateria))
            bateria[1].append('{:.1f} hr ({:.2f} %)'.format(ia_p90.num_horas_carga_min, ia_p90.perc_horas_carga_min))
            bateria[2].append('{:.1f} hr ({:.2f} %)'.format(ia_p90.num_horas_carga_max, ia_p90.perc_horas_carga_max))
            bateria[3].append('{}'.format(ia_p90.num_ciclos_bateria))
        print(tabulate(bateria, tablefmt="github", headers=headers))