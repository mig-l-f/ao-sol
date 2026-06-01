""" Módulo para optimização da UPAC.
"""
import numpy as np
import pandas as pd
from scipy import optimize
import pyomo.environ as pyo
import aosol.analise.analise_energia as ae
import aosol.analise.analise_financeira as af
from aosol.armazenamento.bateria import bateria


def optimiza_autoconsumo_sem_bateria(consumo, producao, params_sistema, params_financeiros, tarifario, max_RPV=10):
    """ Optimização de sistema de autoconsumo sem bateria.

    Optimização o sistem de autoconsumo. Com os parametros dados encontra o sistema PV sem bateria que minimiza o LCOE.
    A optimização é feita usando a função minimize do scipy.optimize. Utiliza o método Nelder-Mead e um despacho
    que consome da bateria quando a carga é maior que produção e quando há disponibilidade de energia na bateria.

    Baseado no trabalho de [1]_ e o código pode ser consultado em [2]_. 
    
    Parameters
    ----------
    consumo : DataFrame
        Série temporal do consumo na coluna 'consumo'. [kWh]
    producao : DataFrame
        Série temporal da produção na coluna 'autoproducao'. [kWh]
    params_sistema : dict
        Dicionario com parametros do sistema sem bateria:

        - consumo_anual: total anual. [kWh]
        - eficiencia_inversor : entre [0, 1]. [-]
    params_financeiros : dict
        Dicionario com parametros financeiros para calculo custo energia:

        - tempo_vida: tempo de vida do projecto. [anos]
        - tempo_vida_bat: tempo de vida da bateria. [anos]
        - pv_por_kW: custo de cada kWp instalado de PV. [€/kW]
        - bat_por_kWh: custo de cada kWh instalado de bateria. [€/kWh]
        - reinvestir_bat: considerar reinvestimento numa 2a bateria. [bool]
        - perc_custo_manutencao: percentagem do investimento gasto em manutenção anual. [%]
        - taxa_actualização: taxa de actualização. [%]
        - simples_kWh: preço compra à rede em tarifário simples. Só usado quando tarifario = tarifario.Simples. [€/kWh]
        - vazio_kWh: preço de compra à rede em vazio no tarifario bihorario. Só usado quando tarifario = tarifario.Bihorario. [€/kWh]
        - fora_vazio_kWh: preço de compra à rede fora de vazio no tarifario bihorario. Só usado quando tarifario = tarifario.Bihorario .[€/kWh]
        - preco_venda_rede: Preco de venda da energia à rede. [€/kWh]
    tarifario : ape.Tarifario
        Simples ou Bihorario.
    max_RPV : float, optional
        Limite máximo para o r_pv. The default is 10. [-]

    Returns
    -------
    r_pv : float
        Tamanho do sistema PV. Razão entre produção anual (kWh) e consumo anual (kWh). [-] 
    LCOE : float
        Custo nivelado de energia do sistema. [€/kWh]

    References
    ----------
    .. [1] S. Quoilin, K. Kavvadias, A. Mercier, I. Pappone, A. Zucker, Quantifying self-consumption linked to solar home battery systems: statistical analysis and economic assessment, Applied Energy, 2016
    .. [2] https://github.com/squoilin/Self-Consumption
    """
    neps = producao["autoproducao"].sum()

    def f_optim_nobat(c):
        """ Função objectivo com PV e sem Bateria.

        LCOE do sistema com PV e sem bateria.

        Parameters
        ----------
        c : list
            [r_pv]

        Returns
        -------
        LCOE : float
            Custo nivelado de energia do sistema. [€/kWh]

        Notes
        -----
        São usadas variaveis globais:

        - neps: número equivalente de horas de sol. [h]
        - consumo: série temporal do consumo. [kWh]
        - producao: série temporal da produção. [kWh]
        - params_sistema: dicionario com parametros do sistema.
        - params_financeiros: dicionario com parametros financeiros.
        - tarifario: tarifario usado.
        """
        r_pv = c[0]
        r_bat = 0
        # if the ratios are negative, set them to zero and add a penalty to the objective function
        penalty_PV = - 1E10 * np.minimum(0,r_pv)
        penalty_bat = - 1E10 * np.minimum(0,r_bat)
        r_pv = np.maximum(0,r_pv)
        r_bat = np.maximum(0,r_bat)
        
        tot_producao = r_pv * params_sistema["consumo_anual"]
        pot_instalada = tot_producao / neps

        energia = consumo.copy()
        energia["autoproducao"] = producao["autoproducao"] * pot_instalada

        energia = ae.analisa_upac_sem_armazenamento(energia)
        indicadores = ae.calcula_indicadores_autoconsumo(energia, pot_instalada, params_sistema["eficiencia_inversor"])
        lcoe, _, _= af.custo_energia_prosumidor(indicadores, tarifario, params_financeiros)
        
        #print 'PV = ' + str(r_PV) + ', BAT = ' + str(r_bat) + ', PR = ' + str(PR) + ', LCOE = ' + str(LCOE)
        return lcoe + penalty_PV + penalty_bat    
  
    def f_optim_maxpv(c):
        r_pv = max_RPV
        r_bat = 0
        # if the ratios are negative, set them to zero and add a penalty to the objective function
        penalty_PV = - 1E10 * np.minimum(0,r_pv)
        penalty_bat = - 1E10 * np.minimum(0,r_bat)
        r_pv = np.maximum(0,r_pv)
        r_bat = np.maximum(0,r_bat)
        
        tot_producao = r_pv * params_sistema["consumo_anual"]
        pot_instalada = tot_producao / neps
        energia = consumo.copy()
        energia["autoproducao"] = producao["autoproducao"] * pot_instalada

        energia = ae.analisa_upac_sem_armazenamento(energia)
        indicadores = ae.calcula_indicadores_autoconsumo(energia, pot_instalada, params_sistema["eficiencia_inversor"])
        lcoe, _, _= af.custo_energia_prosumidor(indicadores, tarifario, params_financeiros)
        
        #print 'PV = ' + str(r_PV) + ', BAT = ' + str(r_bat) + ', PR = ' + str(PR) + ', LCOE = ' + str(LCOE)
        return lcoe + penalty_PV + penalty_bat    

    # Constraints:
    cons = ({'type': 'ineq', 'fun': lambda x: x[0]})
    bnds = ((0, max_RPV),)

    # Com PV sem bateria
    # x0 = [0.4]
    result = optimize.minimize(f_optim_nobat, [0.4], method='Nelder-Mead', tol=1e-5, bounds=bnds)# .values()
    # Lcoe compra só à rede, sem PV nem bateria
    energia = consumo.copy()
    energia["autoproducao"] = producao["autoproducao"] * 0
    energia = ae.analisa_upac_sem_armazenamento(energia)
    indicadores = ae.calcula_indicadores_autoconsumo(energia, 0, params_sistema["eficiencia_inversor"])
    params_financeiros["invest_pv"] = 0
    params_financeiros["invest_bat"] = 0
    lcoe_sem_pv, _, _ = af.custo_energia_prosumidor(indicadores, tarifario, params_financeiros)

    if lcoe_sem_pv <= result.fun:
        r_pv = 0
        LCOE = lcoe_sem_pv
    else:
        r_pv = result.x[0]
        LCOE = result.fun

    if r_pv > max_RPV:  
        result_maxpv = optimize.minimize(f_optim_maxpv, [0.0], method='Nelder-Mead', tol=1e-5, bounds=bnds) #.values()

        tot_producao = r_pv * params_sistema["consumo_anual"]
        pot_instalada = tot_producao / neps
        energia = consumo.copy()
        energia["autoproducao"] = producao["autoproducao"] * pot_instalada
        energia = ae.analisa_upac_sem_armazenamento(energia)
        indicadores = ae.calcula_indicadores_autoconsumo(energia, pot_instalada, params_sistema["eficiencia_inversor"])
        params_financeiros["invest_pv"] = params_financeiros["pv_por_kW"] * pot_instalada
        params_financeiros["invest_bat"] = 0
        lcoe_maxpv, _, _ = af.custo_energia_prosumidor(indicadores, tarifario, params_financeiros)

        if lcoe_maxpv <= result_maxpv[3]:
            r_pv = max_RPV
            LCOE = lcoe_maxpv
        else:
            r_pv = max_RPV
            LCOE = result_maxpv[4]

    return [r_pv, LCOE]

def optimiza_autoconsumo_com_bateria(consumo, producao, params_sistema, params_financeiros, tarifario_periodo_horario, tipo_tarifario=ape.TipoTarifario.Fixo, max_RPV=10): 
    """ Optimização de sistema de autoconsumo.

    Optimização o sistem de autoconsumo. Com os parametros dados encontra o sistema PV com ou sem bateria que minimiza o LCOE.
    A optimização é feita usando a função minimize do scipy.optimize. Utiliza o método Nelder-Mead e um despacho
    que consome da bateria quando a carga é maior que produção e quando há disponibilidade de energia na bateria.
    
    Parameters
    ----------
    consumo : DataFrame
        Série temporal do consumo na coluna 'consumo'. [kWh]
    producao : DataFrame
        Série temporal da produção na coluna 'autoproducao'. [kWh]
    params_sistema : dict
        Dicionario com parametros do sistema com bateria:

        - consumo_anual: total anual. [kWh]
        - eficiencia_inversor : entre [0, 1]. [-]
        - eficiencia_bateria : eficiencia entre carga e descarga, entre [0, 1]. [-]
        - soc_min : estado de carga minimo em fraccao da capacidade, entre [0, 1]. [-]
        - soc_max : estado de carga máximo em fraccao da capacidade, entre [0, 1]. [-]
        - pot_maxima : potencia máxima que pode ser fornecida/retirada da bateria. [kW]
    params_financeiros : dict
        Dicionario com parametros financeiros para calculo custo energia:

        - tempo_vida: tempo de vida do projecto. [anos]
        - tempo_vida_bat: tempo de vida da bateria. [anos]
        - pv_por_kW: custo de cada kWp instalado de PV. [€/kW]
        - bat_por_kWh: custo de cada kWh instalado de bateria. [€/kWh]
        - reinvestir_bat: considerar reinvestimento numa 2a bateria. [bool]
        - perc_custo_manutencao: percentagem do investimento gasto em manutenção anual. [%]
        - taxa_actualização: taxa de actualização. [%]
        - simples_kWh: preço compra à rede em tarifário simples. Só usado quando tarifario = tarifario.Simples. [€/kWh]
        - vazio_kWh: preço de compra à rede em vazio no tarifario bihorario. Só usado quando tarifario = tarifario.Bihorario. [€/kWh]
        - fora_vazio_kWh: preço de compra à rede fora de vazio no tarifario bihorario. Só usado quando tarifario = tarifario.Bihorario .[€/kWh]
        - preco_venda_rede: Preco de venda da energia à rede. [€/kWh]
    tarifario : ape.TarifarioPeriodoHorario
        Simples ou Bihorario.
    tipo_tarifario : ape.TipoTarifario, optional
        Tipo de tarifário. The default is ape.TipoTarifario.Fixo.
    max_RPV : float, optional
        Limite máximo para o r_pv. The default is 10. [-]

    Returns
    -------
    r_pv : float
        Tamanho do sistema PV. Razão entre produção anual (kWh) e consumo anual (kWh). [-] 
    r_bat : float
        Tamanho da bateria. Razão entre capacidade da bateria (kWh) e consumo anual (MWh). [-]
    LCOE : float
        Custo nivelado de energia do sistema. [€/kWh]
    """
    
    neps = producao["autoproducao"].sum()
    
    # Definição das duas funções objectivo da optimização
    def f_optim(c):
        """ Função objectivo com PV e Bateria.

        LCOE do sistema com PV e bateria.

        Parameters
        ----------
        c : list
            [r_pv, r_bat]

        Returns
        -------
        LCOE : float
            Custo nivelado de energia do sistema. [€/kWh]

        Notes
        -----
        São usadas variaveis globais:

        - neps: número equivalente de horas de sol. [h]
        - consumo: série temporal do consumo. [kWh]
        - producao: série temporal da produção. [kWh]
        - params_sistema: dicionario com parametros do sistema.
        - params_financeiros: dicionario com parametros financeiros.
        - tarifario: tarifario usado.
        """
        [r_pv,r_bat] = c
        # if the ratios are negative, set them to zero and add a penalty to the objective function
        penalty_PV = - 1E10 * np.minimum(0,r_pv)
        penalty_bat = - 1E10 * np.minimum(0,r_bat)
        r_pv = np.maximum(0,r_pv)
        r_bat = np.maximum(0,r_bat)
        
        # Calculos
        tot_producao = r_pv * params_sistema["consumo_anual"]
        pot_instalada = tot_producao / neps

        cap_bat = r_bat * (params_sistema["consumo_anual"]/1000)
        bat = bateria(cap_bat, params_sistema["soc_min"], params_sistema["soc_max"], params_sistema["eficiencia_bateria"], params_sistema["pot_maxima"])
        energia = consumo.copy()
        energia["autoproducao"] = producao["autoproducao"] * pot_instalada

        energia = ae.analisa_upac_com_armazenamento(energia, bat, eficiencia_inversor=params_sistema["eficiencia_inversor"])
        indicadores = ae.calcula_indicadores_autoconsumo(energia, pot_instalada, params_sistema["eficiencia_inversor"], bat)
        lcoe, lcos, _ = af.custo_energia_prosumidor(indicadores, energia["consumo_rede"], tarifario_periodo_horario, tipo_tarifario, params_financeiros)
        
        #print 'PV = ' + str(r_PV) + ', BAT = ' + str(r_bat) + ', PR = ' + str(PR) + ', LCOE = ' + str(LCOE)
        return lcoe + penalty_PV + penalty_bat
            
    def f_optim_nobat(c):
        """ Função objectivo com PV e sem Bateria.

        LCOE do sistema com PV e sem bateria.

        Parameters
        ----------
        c : list
            [r_pv]

        Returns
        -------
        LCOE : float
            Custo nivelado de energia do sistema. [€/kWh]

        Notes
        -----
        São usadas variaveis globais:

        - neps: número equivalente de horas de sol. [h]
        - consumo: série temporal do consumo. [kWh]
        - producao: série temporal da produção. [kWh]
        - params_sistema: dicionario com parametros do sistema.
        - params_financeiros: dicionario com parametros financeiros.
        - tarifario: tarifario usado.
        """
        r_pv = c[0]
        r_bat = 0
        # if the ratios are negative, set them to zero and add a penalty to the objective function
        penalty_PV = - 1E10 * np.minimum(0,r_pv)
        penalty_bat = - 1E10 * np.minimum(0,r_bat)
        r_pv = np.maximum(0,r_pv)
        r_bat = np.maximum(0,r_bat)
        
        tot_producao = r_pv * params_sistema["consumo_anual"]
        pot_instalada = tot_producao / neps

        energia = consumo.copy()
        energia["autoproducao"] = producao["autoproducao"] * pot_instalada

        energia = ae.analisa_upac_sem_armazenamento(energia)
        indicadores = ae.calcula_indicadores_autoconsumo(energia, pot_instalada, params_sistema["eficiencia_inversor"])
        lcoe, _, _= af.custo_energia_prosumidor(indicadores, energia["consumo_rede"], tarifario_periodo_horario, tipo_tarifario, params_financeiros)
        
        #print 'PV = ' + str(r_PV) + ', BAT = ' + str(r_bat) + ', PR = ' + str(PR) + ', LCOE = ' + str(LCOE)
        return lcoe + penalty_PV + penalty_bat    
  
    def f_optim_maxpv(c):
        """ Função objectivo com PV máximo e bateria.

        LCOE do sistema com PV fixo no valor máximo (max_rpv) e bateria.

        Parameters
        ----------
        c : list
            [r_bat]

        Returns
        -------
        LCOE : float
            Custo nivelado de energia do sistema. [€/kWh]

        Notes
        -----
        São usadas variaveis globais:

        - neps: número equivalente de horas de sol. [h]
        - consumo: série temporal do consumo. [kWh]
        - producao: série temporal da produção. [kWh]
        - params_sistema: dicionario com parametros do sistema.
        - params_financeiros: dicionario com parametros financeiros.
        - tarifario: tarifario usado.
        - max_rpv: valor máximo para r_pv. [-]
        """
        r_pv = max_RPV
        [r_bat] = c
        # if the ratios are negative, set them to zero and add a penalty to the objective function
        penalty_PV = - 1E10 * np.minimum(0,r_pv)
        penalty_bat = - 1E10 * np.minimum(0,r_bat)
        r_pv = np.maximum(0,r_pv)
        r_bat = np.maximum(0,r_bat)
        
        tot_producao = r_pv * params_sistema["consumo_anual"]
        pot_instalada = tot_producao / neps

        cap_bat = r_bat * (params_sistema["consumo_anual"]/1000)
        bat = bateria(cap_bat, params_sistema["soc_min"], params_sistema["soc_max"], params_sistema["eficiencia_bateria"], params_sistema["pot_maxima"])
        energia = consumo.copy()
        energia["autoproducao"] = producao["autoproducao"] * pot_instalada

        energia = ae.analisa_upac_com_armazenamento(energia, bat, eficiencia_inversor=params_sistema["eficiencia_inversor"])
        indicadores = ae.calcula_indicadores_autoconsumo(energia, pot_instalada, params_sistema["eficiencia_inversor"], bat)

        lcoe, lcos, _ = af.custo_energia_prosumidor(indicadores, energia["consumo_rede"], tarifario_periodo_horario, tipo_tarifario, params_financeiros)
        
        #print 'PV = ' + str(r_PV) + ', BAT = ' + str(r_bat) + ', PR = ' + str(PR) + ', LCOE = ' + str(LCOE)
        return lcoe + penalty_PV + penalty_bat    
    
    # Constraints:
    cons = ({'type': 'ineq', 'fun': lambda x: x[0]},
            {'type': 'ineq', 'fun': lambda x: x[1]})
    bnds = ((0, max_RPV), (0, 10))

    # Since there are 3 discrete variants of the problem, the optimization is performed 3 times and the best one is selected
    # With PV and Battery:
    # x0 = [0.4, 1.1 ]
    result = optimize.minimize(f_optim, [0.4, 1.1], method='Nelder-Mead', tol=1e-5, constraints=cons, bounds=bnds) #.values()
    # With PV, without Battery
    # x0 = [0.4]
    result2 = optimize.minimize(f_optim_nobat, [0.4], method='Nelder-Mead', tol=1e-5, constraints=cons, bounds=bnds)# .values()
    # Without PV, without battery:
    energia = consumo.copy()
    energia["autoproducao"] = producao["autoproducao"] * 0
    energia = ae.analisa_upac_sem_armazenamento(energia)
    indicadores = ae.calcula_indicadores_autoconsumo(energia, 0, params_sistema["eficiencia_inversor"])
    params_financeiros["invest_pv"] = 0
    params_financeiros["invest_bat"] = 0
    lcoe_sem_pv, _, _ = af.custo_energia_prosumidor(indicadores, energia["consumo_rede"], tarifario_periodo_horario, tipo_tarifario, params_financeiros)

    # Selecting the best solution:
    if lcoe_sem_pv <= result2.fun and lcoe_sem_pv <= result.fun:
        r_pv = 0
        r_bat = 0
        LCOE = lcoe_sem_pv
    elif result2.fun <= lcoe_sem_pv and result2.fun <= result.fun:
        r_pv = result2.x[0]
        r_bat = 0
        LCOE = result2.fun
    elif result.fun <= lcoe_sem_pv and result.fun <= result2.fun:
        r_pv = result.x[0]
        r_bat = result.x[1]
        LCOE = result.fun

    # if r_PV is unbounded, do the univariate optimization with its max value
    if r_pv > max_RPV:  
        result_maxpv = optimize.minimize(f_optim_maxpv, [1.1], method='Nelder-Mead', tol=1e-5, constraints=cons, bounds=bnds) #.values()
        
        tot_producao = r_pv * params_sistema["consumo_anual"]
        pot_instalada = tot_producao / neps
        energia = consumo.copy()
        energia["autoproducao"] = producao["autoproducao"] * pot_instalada
        energia = ae.analisa_upac_sem_armazenamento(energia)
        indicadores = ae.calcula_indicadores_autoconsumo(energia, pot_instalada, params_sistema["eficiencia_inversor"])
        params_financeiros["invest_pv"] = params_financeiros["pv_por_kW"] * pot_instalada
        params_financeiros["invest_bat"] = 0
        lcoe_maxpv, _, _ = af.custo_energia_prosumidor(indicadores, energia["consumo_rede"], tarifario_periodo_horario, tipo_tarifario, params_financeiros)
        
        if lcoe_maxpv <= result_maxpv[3]:
            r_pv = max_RPV
            r_bat = 0
            LCOE = lcoe_maxpv
        else:
            r_pv = max_RPV
            r_bat = result_maxpv[5][0]
            LCOE = result_maxpv[4]

    return [r_pv, r_bat, LCOE]  

def crf(r, n):
    """Calcula o CRF (Capital Recovery Factor) para uma taxa de desconto r e um número de anos n.
    
    Parameters
    ----------
    r : float
        Taxa de desconto (em decimal, por exemplo, 0.05 para 5%)
    n : int
        Número de anos do projeto

    Returns
    -------
    crf : float
        O CRF correspondente à taxa de desconto e ao número de anos fornecidos
    """
    return r * (1 + r)**n / ((1 + r)**n - 1)

def optimiza_sistema(df, params):
    """ Optimiza o sistema de autoconsumo utilizando programação linear inteira mista (MILP) com Pyomo.

    Parameters
    ----------
    df : pd.DataFrame
        DataFrame contendo os dados do sistema com as seguintes colunas: 
            - 'preco': preço da energia em cada intervalo de tempo [€/kWh]
            - 'autoproducao_kW': produção de energia solar em cada intervalo de tempo [kW]
            - 'consumo_kW': consumo de energia em cada intervalo de tempo [kW]
            - 'e_vazio': indicador de período vazio [0 ou 1]
    params : dict
        Dicionário com os parâmetros do modelo:
            - 'dt': duração de cada intervalo de tempo em horas (por exemplo, 0.25 para 15 minutos)
            - 'r': taxa de desconto anual (em decimal, por exemplo, 0.05 para 5%)
            - 'preco_venda_rede': preço de venda da energia para a rede [€/kWh]

            - 'kWp': potência instalada do sistema fotovoltaico em kWp
            - 'n_pv': vida útil do sistema fotovoltaico em anos
            - 'capex_pv': custo de investimento do sistema fotovoltaico [€]
            - 'opex_pv': custo operacional anual do sistema fotovoltaico [€/ano]
            - 'Y': produção anual estimada do sistema fotovoltaico por kWp [kWh/kWp]

            - 'capacidade_bat': capacidade do sistema de armazenamento [kWh]
            - 'n_bat': vida útil do sistema de armazenamento em anos
            - 'capex_bat': custo de investimento do sistema de armazenamento [€]
            - 'ciclos_bat_ano': número de ciclos de carga/descarga do sistema de armazenamento por ano
            - 'DoD': profundidade de descarga do sistema de armazenamento (em decimal, por exemplo, 0.8 para 80%)
            - 'Pmax': potência máxima de carga/descarga do sistema de armazenamento [kW]
            - 'ef_carga_bat': eficiência de carga do sistema de armazenamento (em decimal, por exemplo, 0.9 para 90%)
            - 'ef_descarga_bat': eficiência de descarga do sistema de armazenamento (em decimal, por exemplo, 0.9 para 90%)
            - 'permite_descarga_vazio': booleano indicando se é permitido descarregar a bateria durante períodos vazios

            - 'potencia_max_rede': potência máxima contratada da rede [kW]            
            - 'custo_pot_contratada': custo potência contratada por dia [€/dia]
            
    """
    T = range(len(df))
    dt = params["dt"]

    model = pyo.ConcreteModel()

    # =========================
    # PARÂMETROS
    # =========================
    preco = df["preco"].values
    pv = df["autoproducao_kW"].values
    carga = df["consumo_kW"].values
    vazio = df["e_vazio"].values

    # Custos nivelados
    CRF_pv = crf(params["taxa_actualizacao"] / 100, params["tempo_vida"])
    # custo nivelado do PV por kWh produzido
    C_pv = (params["capex_pv"] * CRF_pv + params["opex_pv"]) / params["Y"]

    # Custo marginal bateria Cbat = (Capex_bat * CRF_bat) / (ciclos_bat_ano * capacidade_bat * DoD)
    CRF_bat = crf(params["taxa_actualizacao"] / 100, params["tempo_vida_bat"])
    # Cbat < spread_tarifario para que a bateria seja despachada, caso contrario rende mais manter bateria sempre carregada.
    ## throughput anual esperado (aprox inicial)
    #E_throughput = params["ciclos_bat_ano"] * params["capacidade_bat"] * params["DoD"]
    ## custo nivelado da bateria por kWh throughput
    #C_bat = (params["capex_bat"] * CRF_bat) / E_throughput
    
    # Utilizar Cdeg como "quanto valorizas preservar ciclos".
    # Cdeg entre [0, 0.01] => estrategia agressiva
    # Cdeg entre [0.02, 0.05] => estrategia normal
    # Cdeg entre [0.06, 0.1] => estrategia conservadora 
    Cdeg = params["Cdeg"]
    

    # =========================
    # VARIÁVEIS
    # =========================
    model.carga_bateria = pyo.Var(T, bounds=(0, params["Pmax"]))
    model.descarga_bateria = pyo.Var(T, bounds=(0, params["Pmax"]))
    soc_min = (1-params["DoD"]) * params["capacidade_bat"]
    model.soc = pyo.Var(T, bounds=(soc_min, params["capacidade_bat"]))
    model.consumo_rede = pyo.Var(T, bounds=(0, params["potencia_max_rede"]))
    model.injeccao_rede = pyo.Var(T, bounds=(0, params["kWp"]))
    # divisao PV
    model.pv_para_carga = pyo.Var(T, bounds=(0, params["kWp"]))
    model.pv_para_bateria = pyo.Var(T, bounds=(0, params["kWp"]))
    # binária (evitar simultâneo)
    #model.a_carregar = pyo.Var(T, within=pyo.Binary)
    # potência contratada
    model.potencia_max_rede = pyo.Var(bounds=(0, params["potencia_max_rede"]))

    # =========================
    # OBJETIVO
    # =========================
    def obj(m):
        custo_energia_rede = sum(
            m.consumo_rede[t] * preco[t] * dt
            for t in T
        )
        custo_energia_pv = sum(
            pv[t] * C_pv * dt
            for t in T
        )
        custo_energia_bateria = sum(
            #(m.carga_bateria[t] + m.descarga_bateria[t]) * C_bat * dt
            m.descarga_bateria[t] * Cdeg * dt
            for t in T
        )
        custo_potencia_contratada = (
            m.potencia_max_rede * params["custo_pot_contratada"] * 365
        )
        ganho_venda_rede = sum(
            m.injeccao_rede[t] * params["preco_venda_rede"] * dt
            for t in T
        )
        return custo_energia_rede + custo_energia_pv + custo_energia_bateria + custo_potencia_contratada - ganho_venda_rede

    model.obj = pyo.Objective(rule=obj)

    # =========================
    # CONSTRAINTS
    # =========================

    # SOC
    def regra_soc(m, t):
        if t == 0:
            return m.soc[t] == params["capacidade_bat"] * 0.5
        return m.soc[t] == m.soc[t-1] + (
            m.carga_bateria[t] * params["ef_carga_bat"]
            - m.descarga_bateria[t] / params["ef_descarga_bat"]
        ) * dt
    model.regra_soc = pyo.Constraint(T, rule=regra_soc)

    # Balanço energético
    def regra_balanco(m, t):
        return (
            pv[t]
            + m.consumo_rede[t]
            + m.descarga_bateria[t]
            ==
            carga[t]
            + m.carga_bateria[t]
            + m.injeccao_rede[t]
        )
    model.regra_balanco = pyo.Constraint(T, rule=regra_balanco)

    # divisao PV
    def regra_divisao_pv(m, t):
        return pv[t] == m.pv_para_carga[t] + m.pv_para_bateria[t] + m.injeccao_rede[t]
    model.regra_divisao_pv = pyo.Constraint(T, rule=regra_divisao_pv)

    # ligar PV ao balanço
    def regra_uso_pv(m, t):
        return m.pv_para_carga[t] <= carga[t]
    model.regra_uso_pv = pyo.Constraint(T, rule=regra_uso_pv)

    # carga da bateria pode vir de PV ou rede
    def regra_carga_bateria(m, t):
        return m.carga_bateria[t] >= m.pv_para_bateria[t]
    model.regra_carga_bateria = pyo.Constraint(T, rule=regra_carga_bateria)

    # Peak shaving
    def regra_peak_shaving(m, t):
        return m.consumo_rede[t] <= m.potencia_max_rede
    model.regra_peak_shaving = pyo.Constraint(T, rule=regra_peak_shaving)

    # Sem descarga em vazio
    def regra_sem_descarga_vazio(m, t):
        if vazio[t] and not params["permite_descarga_vazio"]:
            return m.descarga_bateria[t] == 0
        return pyo.Constraint.Skip
    model.regra_sem_descarga_vazio = pyo.Constraint(T, rule=regra_sem_descarga_vazio)

#    # evitar charge/discharge simultâneo
#    def regra_limite_carga(m, t):
#        return m.carga_bateria[t] <= params["Pmax"] * m.a_carregar[t]
#
#    def regra_limite_descarga(m, t):
#        return m.descarga_bateria[t] <= params["Pmax"] * (1 - m.a_carregar[t])
#    model.regra_limite_carga = pyo.Constraint(T, rule=regra_limite_carga)
#    model.regra_limite_descarga = pyo.Constraint(T, rule=regra_limite_descarga)

    # =========================
    # SOLVER
    # =========================
    solver = pyo.SolverFactory("glpk", executable="/usr/local/bin/glpsol")  # ou glpk
    #solver = pyo.SolverFactory("highs", executable="/usr/local/bin/highs")
    solver.solve(model, tee=False)

    # =========================
    # RESULTADOS
    # =========================
    resultados = pd.DataFrame({
        "consumo": [carga[t] for t in T],
        "consumo_rede": [pyo.value(model.consumo_rede[t]) for t in T],
        "injeccao_rede": [pyo.value(model.injeccao_rede[t]) for t in T],
        #"autoconsumo": [pyo.value(model.pv_para_carga[t] + model.descarga_bateria[t]) for t in T],
        #"autoconsumo": [pyo.value(model.pv_para_carga[t]) for t in T],
        "autoconsumo": [np.max([0, carga[t] - pyo.value(model.consumo_rede[t])]) for t in T],
        "autoproducao": [pv[t] for t in T],
        "soc": [pyo.value(model.soc[t]) for t in T],
        "carga_bateria": [pyo.value(model.carga_bateria[t]) for t in T],
        "descarga_bateria": [pyo.value(model.descarga_bateria[t]) for t in T]
    })

    lcoe = pyo.value(model.obj)
    potencia_max_rede = pyo.value(model.potencia_max_rede)

    return resultados, lcoe, potencia_max_rede
