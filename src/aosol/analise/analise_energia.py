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
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import matplotlib
import matplotlib.cm as cm
import warnings
from .indicadores_autoconsumo import indicadores_autoconsumo
from ..armazenamento.bateria import bateria
from .analise_financeira import custo_energia_prosumidor
from .analise_precos_energia import identifica_periodo_tarifario_bihorario

def calcula_indicadores_autoconsumo(energia, pot_instalada, ef_inv, bat=None, intervalo=1):
    """ Calcula indicadores de autoconsumo com armazenamento.

    A partir de um dataframe com os resultados de uma simulação, calcula os
    seguintes indicadores:

    - iac : indice auto consumo. [%]
    - ias : indice auto suficiencia. [%]
    - ier : indice entrega a rede. [%]
    - energia_autoconsumida : total energia autoconsumida. [kWh]
    - energia_rede : total energia consumida da rede. [kWh]
    - energia_rede_vazio : total energia consumida da rede no periodo vazio. [kWh]
    - energia_rede_fora_vazio : total energia consumida da rede no periodo fora de vazio. [kWh]
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

    energia = identifica_periodo_tarifario_bihorario(energia)
    total_vazio = energia.loc[(energia['periodo tarifario'] == 'vazio'), 'consumo_rede'].sum()
    total_fora_vazio = energia.loc[(energia['periodo tarifario'] == 'fora vazio'), 'consumo_rede'].sum()

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
                                   total_consumo_rede, total_vazio, total_fora_vazio,
                                   total_injeccao_rede, total_consumo, perdas_inversor, residuo,
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

    - A bateria é carregada quando produção PV > carga e enquanto não está totalmente carregada.
    - A bateria é descarregada quando produção PV < carga e enquanto não está totalmente descarregada.
    
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

def calcula_12x24(energia, col, func='mean'):
    """ Calcula matriz 12 meses x 24 horas.

    Parameters
    ----------
    energia: pandas.Dataframe
        Dataframe com a serie temporal de energia.
    col: str 
        Nome da coluna a calcular.
    func: str, default='mean'
        Função a aplicar, por defeito média.
    
    Returns
    -------
    pd.DataFrame
        Dataframe com médias de energia por hora por mes.
    """
    d_12x24 = energia.groupby([energia.index.month, energia.index.hour])[col].agg(func) #.mean()
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
    
    if plot_descarga:
        # autoconsumo directo (% consumo)        
        autoconsumo_directo = energia_mensal[col_auto] - energia_mensal[col_descarga]
        label_auto = f"{col_auto.replace('_',' ')} directo (% consumo)"
        a = ax.bar(energia_mensal.index.month-offset, autoconsumo_directo, width=width, bottom=bottom, label=label_auto, color=cores[auto_idx_cor])
        per_auto = autoconsumo_directo.div(consumo_mensal, axis=0).mul(100).round(0)
        labels = [f'{v.get_height():.0f}\n({row:.0f}%)' if v.get_height() > 0 else '' for v, row in zip(a, per_auto)]
        ax.bar_label(a, labels=labels, label_type='center', fontsize=font)
        bottom += autoconsumo_directo

        # descarga bateria (% consumo)
        label_descarga = f"{col_descarga.replace('_',' ')} (% consumo)"
        d = ax.bar(energia_mensal.index.month-offset, energia_mensal[col_descarga], width=width, bottom=bottom, label=label_descarga, color=cores[descarga_idx_cor])
        per_descarga = energia_mensal[col_descarga].div(consumo_mensal, axis=0).mul(100).round(0)
        labels = [f'{v.get_height():.0f}\n({row:.0f}%)' if v.get_height() > 0 else '' for v, row in zip(d, per_descarga)]
        ax.bar_label(d, labels=labels, label_type='center', fontsize=font)
        bottom += energia_mensal[col_descarga]
    else:
        # autoconsumo (% consumo)
        label_auto = f"{col_auto.replace('_',' ')} (% consumo)"
        a = ax.bar(energia_mensal.index.month-offset, energia_mensal[col_auto], width=width, bottom=bottom, label=label_auto, color=cores[auto_idx_cor])
        per_auto = energia_mensal[col_auto].div(consumo_mensal, axis=0).mul(100).round(0)
        labels = [f'{v.get_height():.0f}\n({row:.0f}%)' if v.get_height() > 0 else '' for v, row in zip(a, per_auto)]
        ax.bar_label(a, labels=labels, label_type='center', fontsize=font)
        bottom += energia_mensal[col_auto]

    # injeccao rede (% de autoproducao)    
    label_inj = f"{col_inj.replace('_', ' ')} (% producao)"
    i = ax.bar(energia_mensal.index.month-offset, energia_mensal[col_inj], width=width, bottom=bottom, label=label_inj, color=cores[inj_idx_cor])
    per_inj = energia_mensal[col_inj].div(producao_mensal, axis=0).mul(100).round(0)
    labels = [f'{v.get_height():.0f}\n({row:.0f}%)' if v.get_height() > 0 else '' for v, row in zip(i, per_inj)]
    ax.bar_label(i, labels=labels, label_type='center', fontsize=font)

    ax.legend(bbox_to_anchor =(0.5,-0.27), loc='lower center')
    ax.set_ylabel('Enegia [kWh]')
    ax.set_xlabel('mes')

def plot_despacho_energia(energia, semana):
    """ Plot do despacho de energia para a semana indicada.

    Parameters
    ----------
    energia : pd.DataFrame
        Dataframe com series temporais.
    semana : int
        Numero da semana. Entre 1 e 52
    """

    mascara_semana = (energia.index.isocalendar().week == semana)

    producao = energia.loc[mascara_semana, 'autoproducao']
    carga = energia.loc[mascara_semana, 'consumo']
    autoconsumo = energia.loc[mascara_semana, 'autoconsumo']
    injeccao_rede = energia.loc[mascara_semana, 'injeccao_rede']
    consumo_rede = energia.loc[mascara_semana, 'consumo_rede']
    bat = False
    if 'descarga_bateria' in energia.columns:
        bat = True
        descarga_bateria = energia.loc[mascara_semana, 'descarga_bateria']
        estado_carga = energia.loc[mascara_semana, 'soc']

    fig, ax = plt.subplots(nrows=3, ncols=1, sharex=True, figsize=(13, 4*3), frameon=True,
                             gridspec_kw={'height_ratios': [2, 1, 1], 'hspace': 0.04})
    
    ax[0].plot(carga.index, carga, color='black', lw=2, label='carga')
    ax[0].fill_between(autoconsumo.index, 0, autoconsumo, color='orange', alpha=.2, label='autoconsumo')
    ax[0].fill_between(producao.index, autoconsumo, producao , color='yellow', alpha=.3, label='producao')
    if bat:
        ax[0].fill_between(descarga_bateria.index,
                        producao,
                        descarga_bateria + producao, color='blue',alpha=.2, hatch='//', label='bateria')
        # ax[0].fill_between(consumo_rede.index,
        #                 producao + descarga_bateria,
        #                 consumo_rede + producao + descarga_bateria, color='grey', alpha=.2)
    ax[0].plot(consumo_rede.index, consumo_rede, color='red', lw=1, label='rede')
    ax[0].set_ylim([0, ax[0].get_ylim()[1] ])
    ax[0].set_ylabel('Energia (kWh)')
    ax[0].grid()

    ax[1].set_ylabel('Estado de carga (kWh)')
    if bat:
        ax[1].fill_between(estado_carga.index, 0, estado_carga, color='grey', alpha=.2)
        ax[1].grid()

    ax[2].fill_between(consumo_rede.index, 0, consumo_rede, color='green', alpha=.2)
    ax[2].fill_between(injeccao_rede.index, 0, -injeccao_rede, color='red', alpha=.2)
    ax[2].set_ylabel('Consumo/Injeccao rede (kWh)')
    ax[2].grid()

    ax[2].xaxis.set_major_locator(mdates.DayLocator())  # Ticks principais a cada dia
    ax[2].xaxis.set_minor_locator(mdates.HourLocator(byhour=[0, 6, 12, 18]))
    ax[2].xaxis.set_major_formatter(mdates.DateFormatter('%b %d'))

def estudo_upac_sem_bateria(consumo, producao, params_sistema, tarifario, params_financeiros, r_pv_max=3):
    """ Estudo parametrico de UPAC sem bateria.

    Variação do parametro r_pv para calculo do IAS (auto-suficiência) e custo de energia.

    .. math:: r_{pv} = \\frac{Producao_{PV}}{Consumo} \\left[ \\frac{kWh}{kWh} \\right]

    Parameters
    ----------
    consumo : pd.DataFrame
        Serie temporal com coluna 'consumo'. [kWh]
    producao : pd.DataFrame
        Serie temporal com coluna 'autoproducao' para PV com 1kWp de capacidade. [kWh]
    params_sistema : dict
        Dicionario com parametros do sistema sem bateria:

        - consumo_anual: total anual. [kWh]
        - eficiencia_inversor : entre [0, 1]. [-]
    tarifario : ape.Tarifario
        Simples ou Bihorario.
    params_financeiros : dict
        Dicionario com parametros financeiros para calculo custo energia:

        - tempo_vida: tempo de vida do projecto. [anos]
        - tempo_vida_bat: tempo de vida da bateria. [anos]
        - pv_por_kW: custo de cada kWp instalado de PV. [€/kW]
        - bat_fixo: custo fixo de instalação de bateria. [€]
        - bat_euro_por_kWh: custo por cada kWh de bateria instalado. [€/kWh]
        - perc_custo_manutencao: percentagem do investimento gasto em manutenção anual. [%]
        - taxa_actualização: taxa de actualização. [%]
        - simples_kWh: preço compra à rede em tarifário simples. Só usado quando tarifario = tarifario.Simples. [€/kWh]
        - vazio_kWh: preço de compra à rede em vazio no tarifario bihorario. Só usado quando tarifario = tarifario.Bihorario. [€/kWh]
        - fora_vazio_kWh: preço de compra à rede fora de vazio no tarifario bihorario. Só usado quando tarifario = tarifario.Bihorario .[€/kWh]
        - preco_venda_rede: Preco de venda da energia à rede. [€/kWh]

    r_pv_max : int, default: 3
        Factor maximo.

    Returns
    -------
    resultados : pd.DataFrame
        Indicadores de energia para cada r_pv
    custo_medio_sem_pv : float
        Custo da energia sem sistema PV (r_pv = 0)
    """
    r_pv = np.linspace(0, r_pv_max, r_pv_max*10)
    warnings.filterwarnings('ignore') 
    neps = producao["autoproducao"].sum()

    resultados = pd.DataFrame()
    custo_medio_sem_pv = 0
    preco_venda_rede = params_financeiros["preco_venda_rede"]

    for i in range(len(r_pv)):
        tot_producao = r_pv[i] * params_sistema["consumo_anual"]
        pot_instalada = tot_producao / neps

        energia = consumo.copy()
        energia["autoproducao"] = producao["autoproducao"] * pot_instalada

        energia = analisa_upac_sem_armazenamento(energia)
        indicadores = calcula_indicadores_autoconsumo(energia, pot_instalada, params_sistema["eficiencia_inversor"])
        
        # calcula custos prosumidor
        params_financeiros["invest_pv"] = params_financeiros["pv_por_kW"] * pot_instalada
        params_financeiros["invest_bat"] = 0
        params_financeiros["preco_venda_rede"] = 0.0
        lcoe_s_venda, _, custo_medio_rede = custo_energia_prosumidor(indicadores, tarifario, params_financeiros)
        params_financeiros["preco_venda_rede"] = preco_venda_rede
        lcoe_c_venda, _, _ = custo_energia_prosumidor(indicadores, tarifario, params_financeiros)

        # guarda com frame
        indicadores = indicadores.to_frame()
        indicadores["r_pv"] = r_pv[i]
        indicadores["lcoe s/ venda"] = lcoe_s_venda
        indicadores["lcoe c/ venda"] = lcoe_c_venda

        if r_pv[i] == 0.0:
            custo_medio_sem_pv = custo_medio_rede

        resultados = pd.concat([resultados, indicadores])

    resultados = resultados.set_index("r_pv")
    return resultados, custo_medio_sem_pv

def plot_estudo_sem_bateria(resultados, ax, titulo):
    """ Plot dos resultados de estudo sem bateria.

    Parameters
    ----------
    resultados : pd.DataFrame
        Dataframe com indicadores e custo de energia para cada r_pv.
    ax : axis
        Eixos
    titulo : str
        Titulo a usar.
    """
    idx_min_s_venda = resultados["lcoe s/ venda"].idxmin()
    min_lcoe_s_venda = resultados.loc[idx_min_s_venda]['lcoe s/ venda']
    min_ias_s_venda = resultados.loc[idx_min_s_venda]['IAS: Contributo PV [%]']
    min_pv_s_venda = resultados.loc[idx_min_s_venda]['Potencia instalada [kW]']

    idx_min_c_venda = resultados["lcoe c/ venda"].idxmin()
    min_lcoe_c_venda = resultados.loc[idx_min_c_venda]['lcoe c/ venda']
    min_ias_c_venda = resultados.loc[idx_min_c_venda]['IAS: Contributo PV [%]']
    min_pv_c_venda = resultados.loc[idx_min_c_venda]['Potencia instalada [kW]']


    resultados.plot(y=["lcoe s/ venda", "lcoe c/ venda"], style='--', legend=False, ax=ax)
    ax.set_xlabel("Racio PV")
    ax.set_ylabel("LCOE [€/kWh]")
    ax.grid()    
    ax.set_title(titulo)

    ax1 = ax.twinx()
    resultados.plot(y=["IAS: Contributo PV [%]", "IAC: Indice Auto consumo [%]"], ax=ax1, legend=False)
    ax1.set_ylabel('Indicadores [%]')

    print(f'Sem venda rede: {round(min_pv_s_venda,1)} kWp com custo energia = {round(min_lcoe_s_venda,2)} €/kWh para IAS = {round(min_ias_s_venda,1)} %')
    print(f'Com venda rede: {round(min_pv_c_venda,1)} kWp com custo energia = {round(min_lcoe_c_venda,2)} €/kWh para IAS = {round(min_ias_c_venda,1)} %')
    ax.axvline(x=idx_min_s_venda, color='grey', linestyle='--')
    ax.scatter([idx_min_s_venda],[min_lcoe_s_venda])
    ax.annotate(
        f'({round(idx_min_s_venda, 2)}, {round(min_lcoe_s_venda,2)})',
        xy=(idx_min_s_venda, min_lcoe_s_venda))
    ax1.scatter([idx_min_s_venda],[min_ias_s_venda])
    ax1.annotate(
        f'({round(idx_min_s_venda,2)}, {round(min_ias_s_venda,1)})',
        xy=(idx_min_s_venda, min_ias_s_venda))


    ax.axvline(x=idx_min_c_venda, color='grey', linestyle='--')
    ax.scatter([idx_min_c_venda],[min_lcoe_c_venda])
    ax.annotate(
        f'({round(idx_min_c_venda, 2)}, {round(min_lcoe_c_venda,2)})',
        xy=(idx_min_c_venda, min_lcoe_c_venda))
    ax1.scatter([idx_min_c_venda], [min_ias_c_venda])
    ax1.annotate(
        f'({round(idx_min_c_venda,2)}, {round(min_ias_c_venda,1)})',
        xy=(idx_min_c_venda, min_ias_c_venda))

    handles1, labels1 = ax.get_legend_handles_labels()
    handles2, labels2 = ax1.get_legend_handles_labels()
    handles = handles1 + handles2
    labels = labels1 + labels2
    ax.legend(handles, labels, loc='upper center', bbox_to_anchor=(0.5, -0.1), ncol=2)

def estudo_upac_com_bateria(consumo, producao, params_sistema, tarifario, params_financeiros):
    """ Estudo paramétrico de UPAC com bateria.

    Variação de parâmetros r_pv [0, 2] e r_bat [0.5, 2.5] relativos ao total de consumo e
    calcular IAS (auto-suficiência) e custo de energia.

    .. math:: r_{pv} = \\frac{Producao_{PV}}{Consumo} \\left[ \\frac{kWh}{kWh} \\right]

    .. math:: r_{bat} = \\frac{CAP_{bat}}{Consumo} \\left[ \\frac{kWh}{MWh} \\right]

    Parameters
    ----------
    consumo : pd.DataFrame
        Serie temporal com coluna 'consumo'. [kWh]
    producao : pd.DataFrame
        Serie temporal com coluna 'autoproducao' para PV com 1kWp de capacidade. [kWh]
    params_sistema : dict
        Dicionario com parametros do sistema sem bateria:

        - consumo_anual: total anual. [kWh]
        - eficiencia_inversor : entre [0, 1]. [-]
        - eficiencia_bateria : eficiencia entre carga e descarga, entre [0, 1]. [-]
        - soc_min : estado de carga minimo em fraccao da capacidade, entre [0, 1]. [-]
        - soc_max : estado de carga máximo em fraccao da capacidade, entre [0, 1]. [-]
        - pot_maxima : potencia máxima que pode ser fornecida/retirada da bateria. [kW]

    tarifario : ape.Tarifario
        Simples ou Bihorario.
    params_financeiros : dict
        Dicionario com parametros financeiros para calculo custo energia:

        - tempo_vida: tempo de vida do projecto. [anos]
        - tempo_vida_bat: tempo de vida da bateria. [anos]
        - pv_por_kW: custo de cada kWp instalado de PV. [€/kW]
        - bat_fixo: custo fixo de instalação de bateria. [€]
        - bat_euro_por_kWh: custo por cada kWh de bateria instalado. [€/kWh]
        - perc_custo_manutencao: percentagem do investimento gasto em manutenção anual. [%]
        - taxa_actualização: taxa de actualização. [%]
        - simples_kWh: preço compra à rede em tarifário simples. Só usado quando tarifario = tarifario.Simples. [€/kWh]
        - vazio_kWh: preço de compra à rede em vazio no tarifario bihorario. Só usado quando tarifario = tarifario.Bihorario. [€/kWh]
        - fora_vazio_kWh: preço de compra à rede fora de vazio no tarifario bihorario. Só usado quando tarifario = tarifario.Bihorario .[€/kWh]
        - preco_venda_rede: Preco de venda da energia à rede. [€/kWh]

    Returns
    -------
    resultados : pd.DataFrame
        Dataframe com indicadores de energia para os vários r_pv e r_bat.
    """
    ratios_pv = np.linspace(0.5, 2.5, 20)
    ratios_bat = np.linspace(0, 2, 20)

    neps = producao["autoproducao"].sum()
    resultados = pd.DataFrame()
    preco_venda_rede = params_financeiros["preco_venda_rede"]

    for i in range(len(ratios_pv)):
        for j in range(len(ratios_bat)):
            r_pv = ratios_pv[i]
            r_bat = ratios_bat[j]

            tot_producao = r_pv * params_sistema["consumo_anual"]
            pot_instalada = tot_producao / neps

            cap_bat = r_bat * (params_sistema["consumo_anual"]/1000)
            bat = bateria(cap_bat, params_sistema["soc_min"], params_sistema["soc_max"], params_sistema["eficiencia_bateria"], params_sistema["pot_maxima"])
            energia = consumo.copy()
            energia["autoproducao"] = producao["autoproducao"] * pot_instalada

            energia = analisa_upac_com_armazenamento(energia, bat, eficiencia_inversor=params_sistema["eficiencia_inversor"])
            indicadores = calcula_indicadores_autoconsumo(energia, pot_instalada, params_sistema["eficiencia_inversor"], bat)

            # calcula custos prosumidor
            params_financeiros["invest_pv"] = params_financeiros["pv_por_kW"] * pot_instalada
            params_financeiros["invest_bat"] = params_financeiros["bat_fixo"] + params_financeiros["bat_euro_por_kWh"]*cap_bat
            params_financeiros["preco_venda_rede"] = 0.0
            lcoe_s_venda, lcos_s_venda, _ = custo_energia_prosumidor(indicadores, tarifario, params_financeiros)
            params_financeiros["preco_venda_rede"] = preco_venda_rede
            lcoe_c_venda, lcos_c_venda, _ = custo_energia_prosumidor(indicadores, tarifario, params_financeiros)

            # guarda como dataframe
            indicadores = indicadores.to_frame()
            indicadores["r_pv"] = r_pv
            indicadores["r_bat"] = r_bat
            indicadores["lcoe s/ venda"] = lcoe_s_venda
            indicadores["lcos s/ venda"] = lcos_s_venda
            indicadores["lcoe c/ venda"] = lcoe_c_venda
            indicadores["lcos c/ venda"] = lcos_c_venda
            resultados = pd.concat([resultados, indicadores])

    return resultados

def plot_estudo_com_bateria(resultados, plot_c_venda_rede, ax, titulo):
    """ Plot dos resultados do estudo com bateria.

    Parameters
    ----------
    resultados : pd.DataFrame
        Dataframe com os resultados para os vários r_pv e r_bat.
    plot_c_venda_rede : bool
        Se True utiliza os resultados com venda à rede, caso False utiliza sem.
    ax : axis
        Matplotlib axis onde fazer a plot.
    titulo : str
        Titulo da plot.
    """
    r_pv = np.array(resultados["r_pv"].unique())
    r_bat = np.array(resultados["r_bat"].unique())
    PV, BAT = np.meshgrid(r_pv, r_bat)
    IAS = resultados["IAS: Contributo PV [%]"].values.reshape(len(r_pv), len(r_bat))
    if (plot_c_venda_rede):
        LCOE = resultados["lcoe c/ venda"].values.reshape(len(r_pv), len(r_bat))
    else:
        LCOE = resultados["lcoe s/ venda"].values.reshape(len(r_pv), len(r_bat))

    matplotlib.rcParams['xtick.direction'] = 'out'
    matplotlib.rcParams['ytick.direction'] = 'out'

    levels = np.arange(0.10,0.30,0.01)
    levels_ias = np.arange(30, 100, 5)

    CS1 = ax.contour(PV, BAT, IAS, colors='black', linewidths=1., linestyles='--', levels=levels_ias)
    CS = ax.contour(PV, BAT, LCOE, colors='black', linewidths=1.,levels=levels)
    CS2 = ax.contourf(PV, BAT, LCOE, cmap=cm.Purples, alpha=0.5,levels=levels)
    ax.grid()
    ax.clabel(CS, inline=1, fontsize=10)
    ax.clabel(CS1, inline=1, fontsize=10)
    ax.set_title(titulo)
    ax.set_xlabel('PV [kWh/kWh]')
    ax.set_ylabel('BATERIA [kWh/MWh]')