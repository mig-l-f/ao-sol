""" Módulo com as funções para efectuar a análise de energia, a partir das séries de consumo e autoprodução tanto
para UPAC com e sem bateria. Os algoritmos para análise da energia são baseados em [1]_.

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
soc                      kWh      estado de carga da bateria no final to timestep
======================== ======== ==========================

References
----------

.. [1] S. Quoilin, K. Kavvadias, A. Mercier, I. Pappone, A. Zucker, 
       Quantifying self-consumption linked to solar home battery systems: statistical analysis and economic assessment, 
       Applied Energy, 2016
"""

import numpy as np
import pandas as pd
from IPython.display import HTML, display
from tabulate import tabulate
from .indicadores_autoconsumo import indicadores_autoconsumo

def calcula_indicadores_autoconsumo(energia, pot_instalada, ef_inv, bat=None, intervalo=1):
    """ Calcula indicadores de autoconsumo com armazenamento.

    A partir de um dataframe com os resultados de uma simulação, calcula os
    seguintes indicadores:
    - iac : indice auto consumo. [%]
    - ias : indice auto suficiencia. [%]
    - ier : indice entrega a rede. [%]
    - energia_autoconsumida : total energia autoconsumida. [kWh]
    - energia_rede : total energia consumida da rede. [kWh]
    - consumo_total : total energia consumida. [kWh]
    - perdas_inversor : perdas de energia na conversão do inversor. [kWh]
    - residuo : diferenca de control entre toda energia gerada (PV+rede) e consumida (carga+inj_rede+perdas_bat+perdas_inv)
    
    Se a bateria for fornecida então calcula também os indicadores da baterias:
    - consumo_bateria : total de energia fornecida pela bateria. [kWh]
    - perdas_bateria : perdas de energia na conversão da bateria. [kWh]
    - num_ciclos : numero de ciclos de carregamento da bateria em 1 ano
    """
    total_consumo = energia["consumo"].sum()
    total_consumo_rede = energia["consumo_rede"].sum()
    total_injeccao_rede = energia["injeccao_rede"].sum()
    total_autoconsumo = energia["autoconsumo"].sum()
    total_autoproducao = energia["autoproducao"].sum()

    ias = (total_autoconsumo / total_consumo)*100      # %
    iac = (total_autoconsumo / total_autoproducao)*100 # %
    ier = 100 - iac
    
    com_bateria = bat is not None
    n_ciclos = 0
    cap_bat = 0 # kWh
    total_descarga_bateria = 0  # kWh
    perdas_bateria = 0 # kWh
    if com_bateria:
        # num ciclos
        media_ciclos = np.sum(energia["descarga_bateria"]*intervalo)/(365*bat.capacidade_total)
        n_ciclos = 365*media_ciclos
        cap_bat = bat.capacidade_total
        total_descarga_bateria = energia["descarga_bateria"].sum()
        perdas_bateria = energia["carga_bateria"].sum() - total_descarga_bateria

    perdas_inversor = (total_autoproducao - perdas_bateria)*(1-ef_inv)
    residuo = total_autoproducao + total_consumo_rede - \
        total_injeccao_rede - perdas_inversor - perdas_bateria - total_consumo

    return indicadores_autoconsumo(iac, ias, ier, pot_instalada, total_autoproducao, total_autoconsumo, 
                                   total_consumo_rede, total_injeccao_rede, total_consumo, perdas_inversor, residuo,
                                   com_bateria, total_descarga_bateria, perdas_bateria, n_ciclos, cap_bat)
    
def analisa_upac_sem_armazenamento(energia, eficiencia_inversor=1, intervalo=1):
    """ Analisa uma UPAC sem armazenamento.

    Algoritmo para autoconsumo sem armazenamento. Fonte: [1]_
    Dadas as series de:
    - consumo : consumo total [kWh]
    - autoproducao : producao total do sistema autoconsumo [kWh]
    - autoproducao_p90 : produção P90 da UPAC [kWh] (opcional)
    Calcula:
    - autoconsumo : quantidade produzida que é efectivamente consumida [kWh]
    - injeccao_rede : quantidade produzida que não é aproveitada [kWh]
    - consumo_rede : quantidade consumida da rede [kWh]

    Parameters
    ----------
    energia : pd.Dataframe
        Dataframe com as series de consumo e autoproducao.
    eficiencia_inversor : float, default: 1
        Eficiencia do inversor. Valor entre 0 e 1.
    intervalo : float, default: 1
        Intervalo temporal entre cada registo. [h]

    Returns
    -------
    pd.Dataframe
        A data frame original com as series adicionadas de autoconsumo, injeccao_rede e consumo_rede.
    """
    pv = energia["autoproducao"].values / intervalo  # kW
    carga = energia["consumo"].values / intervalo    # kW

    energia_bidireccional_rede = (carga - pv*eficiencia_inversor)*intervalo  # kWh

    energia["consumo_rede"] = np.maximum(0, energia_bidireccional_rede)
    energia["injeccao_rede"] = np.maximum(0, -energia_bidireccional_rede)
    energia["autoconsumo"] = energia["consumo"] - energia["consumo_rede"]

    return energia

def analisa_upac_com_armazenamento(energia, bateria, intervalo=1, eficiencia_inversor=1, soc_0=None):
    """ Analisa uma UPAC com armazenamento

    Algoritmo para autoconsumo com armazenamento [1]_, método que maximiza o auto-consumo.
    A bateria é carregada quando produção PV > carga e enquanto não está totalmente carregada.
    A bateria é descarregada quando produção PV < carga e enquanto não está totalmente descarregada.
    
    Parameters
    ----------
    energia : pd.DataFrame
        Data frame com as series consumo e autoproducao.
    bateria : bateria
        Objecto bateria com capacidade e soc_min e soc_max
    eficiencia_inversor : float, default: 1
        Eficiencia inversor, valores entre [0, 1].
    soc_0 : float, default: None
        Estado de carga da bateria no 1o instante. Se None então soc_0 é igual 50%.
    intervalo : float, default: 1
        Intervalo temporal entre cada registo. [hr]

    Returns
    -------
    pd.DataFrame
        Data frame com as series calculadas.

    Notes
    -----
    Dadas as series de:
    - consumo : consumo total [kWh]
    - autoproducao : producao total do sistema autoconsumo [kWh]
    Calcula:
    - autoconsumo : energia autoconsumida (PV + bateria) [kWh]
    - injeccao_rede : energia desperdicada [kWh]
    - consumo_rede : energia consumida da rede [kWh]
    - carga_bateria : energia consumida pela bateria [kWh]
    - descarga_bateria : energia fornecida pela bateria [kWh]
    - soc : estado de carga da bateria no final to timestep [kWh]

    References
    ----------
    .. [1] Sylvain Quoilin, Konstantinos Kavvadias, Arnaud Mercier, Irene Pappone, Andreas Zucker, 
           Quantifying self-consumption linked to solar home battery systems: Statistical analysis and economic assessment,
           Applied Energy, Volume 182, 2016, Pages 58-67.
    """
    pv = energia["autoproducao"].values / intervalo  # kW
    carga = energia["consumo"].values / intervalo    # kW

    n = len(pv)
    soc = np.zeros(n)
    energia_bidireccional_rede = np.zeros(n)  # < 0 : energia injectada, > 0 energia consumida rede
    carga_bateria = np.zeros(n)    # fornecimento bateria
    descarga_bateria = np.zeros(n) # consumo bateria

    if soc_0 is None:
        soc_0 = bateria.profundidade_descarga / 2
    demanda_dc = carga/eficiencia_inversor - pv  # kW

    for i in range(0, n):
        soc_anterior = soc_0
        if i > 0:
            soc_anterior = soc[i-1]

        soc_actual, pot_carga, pot_descarga = bateria.calcula_energia_maximiza_autoconsumo(soc_anterior, demanda_dc[i], intervalo)

        soc[i] = soc_actual # kWh
        energia_bidireccional_rede[i] = (carga[i] - (pv[i] + pot_descarga - pot_carga)*eficiencia_inversor)*intervalo  # kWh
        descarga_bateria[i] = pot_descarga*intervalo # kWh
        carga_bateria[i] = pot_carga*intervalo       # kWh

    energia["consumo_rede"] = np.maximum(0, energia_bidireccional_rede)
    energia["injeccao_rede"] = np.maximum(0, -energia_bidireccional_rede)
    energia["autoconsumo"] = energia["consumo"] - energia["consumo_rede"]
    energia["carga_bateria"] = carga_bateria
    energia["descarga_bateria"] = descarga_bateria
    energia["soc"] = soc
    
    return energia

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