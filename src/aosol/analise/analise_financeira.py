r""" Contem metodos para analise financeira de um projecto.

Notes
-----

Calculo do VAL, TIR, Tempo de retorno [1]_ [2]_ de um projecto e o LCOE (levelized cost of energy)
do sistema produtor.

.. math:: VAL_n = \sum_{k=0}^{n} \frac{CF_{(in)}(k) - CF_{(out)}(k)}{(1+i)^k}

.. math:: VAL_n = \sum_{k=0}^{n} \frac{CF_{(in)}(k) - CF_{(out)}(k)}{(1+TIR_n)^k} = 0

.. math:: VAL_n = \sum_{k=0}^{payback} \frac{CF_{(in)}(k) - CF_{(out)}(k)}{(1+TIR_n)^k} = 0

Calculo do LCOE pelo método descrito no simulador NREL [3]_.

.. [1] Bloco 9 - Análise Investimentos, Universidade Evora. 
    Em https://dspace.uevora.pt/rdpc/bitstream/10174/6309/11/BLOCO9.pdf
.. [2] F Militão, J Alberto. "O Método de Newton-Raphson no Cálculo do TIR", 
    UNOPAR Cient. Exatas Tecnol., Londrina, v. 11, n. 1, p. 59-63, Nov. 2012
.. [3] SJ Andrews, B Smith, MG Deceglie, KA Horowitz, and TJ Silverman. “NREL Comparative PV LCOE Calculator.” 
    Version 2.0.0, August 2021. Em https://www.nrel.gov/pv/lcoe-calculator/documentation.html
"""
import pandas as pd
import numpy as np
from calendar import month, monthrange

from sympy import elliptic_f
from .indicadores_financeiros import indicadores_financeiros
from . import analise_precos_energia as ape

MESES = {1:'jan', 2:'fev', 3:'mar', 4:'abr', 5:'mai', 6:'jun',
         7:'jul', 8:'ago', 9:'set', 10:'out', 11:'nov', 12:'dez'}
MESES_COMPLETO = {1: 'Janeiro', 2:'Fevereiro', 3: u'Março', 4:'Abril',
               5:'Maio', 6:'Junho', 7:'Julho', 8:'Agosto',
               9:'Setembro', 10:'Outubro', 11:'Novembro', 12:'Dezembro'}

def analise_poupanca_anual_fatura(energia
                                , tarifario
                                , precos_energia
                                , venda_rede
                                , nome_cols=['consumo', 'consumo_rede', 'injeccao_rede']
                                , ano_tarifario=0):
    """ Calcula os custos de fatura em cada mes e anual da com e sem UPAC, e a respectiva poupanca. Pode
    calcular também considerando a venda do excedente à rede.

    Parameters
    ----------
    energia : pandas.DataFrame
        Deve conter colunas para 'consumo' e 'consumo_rede'. Adicionalmente a coluna 'injeccao_rede'
        se a venda a rede for incluida. Nomes especificados em nome_cols
    tarifario: ape.Tarifario
        Tipo de tarifário a utilizar: simples, bihorario, trihorario
    precos_energia : ape.TarifarioEnergia
        Preços de energia e venda à rede. 
    venda_rede : bool
        True para considerar venda à rede, False para não
    nome_cols : list, default ['consumo', 'consumo_rede', 'injeccao_rede']
        List com nomes das colunas de consumo, consumo da rede e injeccao da rede.
    ano_tarifario: int, default: 0
        Ano do tarifario para cálculo do tarifario trihorario. So é relevante para esse tarifário.

    Returns
    -------
    mensal: pandas.DataFrame 
        Com os custos mensais e agregado anual.
    """
    if (len(nome_cols) != 2) & (len(nome_cols) != 3) & (~venda_rede):
        raise ValueError("nome_cols deve ter 2 ou 3 valores quando venda_rede=False.")
    elif (len(nome_cols) != 3) & (venda_rede):
        raise ValueError("nome_cols deve ter 3 valores quando venda_rede=True.")

    col_consumo = nome_cols[0]
    col_consumo_rede = nome_cols[1]
    col_injeccao = nome_cols[2] if venda_rede else ''

    # lambda energia e tarifario correspondente
    if (tarifario == ape.Tarifario.Simples):
        func_energia = lambda ener, col, ano : ape.calcula_energia_mensal_tarifario_simples(ener, col)
        # x contem energia mensal do tarifario simples, consumo esta na coluna 'consumo'
        func_calculo_faturas = lambda x : ape.calcula_fatura_tarifario_simples(x[col_consumo], \
            monthrange(x.name.year, x.name.month)[1], \
            precos_energia.custo_kwh_simples, \
            precos_energia.pot_contratada, \
            precos_energia.pot_contratada_custo_dia, \
            precos_energia.pot_contratada_termo_fixo_redes_custo_dia) 
    elif (tarifario == ape.Tarifario.Bihorario):
        func_energia = lambda ener, col, ano : ape.calcula_energia_mensal_tarifario_bihorario(ener, col)
        # x contem energia mensal do tarifario bihorario, consumos nas colunas 'fora_vazio' e 'vazio'
        func_calculo_faturas = lambda x : ape.calcula_fatura_tarifario_bihorario(x['fora_vazio'], x['vazio'], \
            monthrange(x.name.year, x.name.month)[1], \
            precos_energia.custo_bi_kwh_fora_vazio, precos_energia.custo_bi_kwh_vazio, \
            precos_energia.pot_contratada, \
            precos_energia.pot_contratada_custo_dia, \
            precos_energia.pot_contratada_termo_fixo_redes_custo_dia) 
    elif (tarifario == ape.Tarifario.Trihorario):
        func_energia = lambda ener, col, ano : ape.calcula_energia_mensal_tarifario_trihorario(ener, col, ano)
        func_calculo_faturas = lambda x : ape.calcula_fatura_tarifario_trihorario(x['ponta'], x['cheia'], x['vazio'], \
            monthrange(x.name.year, x.name.month)[1], \
            precos_energia.custo_tri_kwh_ponta, \
            precos_energia.custo_tri_kwh_cheia, \
            precos_energia.custo_tri_kwh_vazio, \
            precos_energia.pot_contratada, \
            precos_energia.pot_contratada_custo_dia, \
            precos_energia.pot_contratada_termo_fixo_redes_custo_dia) 

    if venda_rede:
        # venda rede usa funcao para multiplicar injeccao com preco directamente
        func_venda_rede = lambda energia, col: energia[col] * precos_energia.preco_venda_kwh

    # fatura sem upac
    energia_sem_upac_mensal = func_energia(energia, col_consumo, ano_tarifario)
    faturas_sem_upac = energia_sem_upac_mensal.apply(lambda ener_mensal : func_calculo_faturas(ener_mensal), \
         axis=1).to_frame('faturas_sem_upac')
    faturas_sem_upac[['sem_upac_c_iva', 'sem_upac_s_iva']] = pd.DataFrame(faturas_sem_upac['faturas_sem_upac'].to_list(), index=faturas_sem_upac.index)
    faturas_sem_upac = faturas_sem_upac.drop(columns=['faturas_sem_upac'])

    # fatura com upac
    energia_com_upac_mensal = func_energia(energia, col_consumo_rede, ano_tarifario)
    faturas_com_upac = energia_com_upac_mensal.apply(lambda ener_mensal : func_calculo_faturas(ener_mensal), \
        axis=1).to_frame('faturas_com_upac')
    faturas_com_upac[['com_upac_c_iva', 'com_upac_s_iva']] = pd.DataFrame(faturas_com_upac['faturas_com_upac'].to_list(), index=faturas_com_upac.index)
    faturas_com_upac = faturas_com_upac.drop(columns=['faturas_com_upac'])

    # calculo poupanca
    faturas = faturas_sem_upac['sem_upac_c_iva'].to_frame('fatura sem upac')
    faturas =  faturas.merge(faturas_com_upac['com_upac_c_iva'].to_frame('fatura com upac'), how='inner', left_index=True, right_index=True) #energia['custo'].copy()
    faturas['poupanca'] = faturas['fatura sem upac'] - faturas['fatura com upac']

    # venda a rede = injeccao rede
    if venda_rede:
        ganho = func_venda_rede(energia, col_injeccao)
        ganho = ganho.resample('M').sum().to_frame('venda a rede')
        faturas =  faturas.merge(ganho, how='inner', left_index=True, right_index=True) #energia['custo'].copy()
        faturas['poupanca'] = faturas['poupanca'] + faturas['venda a rede']

    mensal = faturas.groupby([faturas.index.month]).sum()
    mensal.index.names = ['mes']
    mensal.index = mensal.index.map(MESES_COMPLETO)
    mensal.loc['Anual'] = mensal.sum(axis=0)
    return mensal

def analise_financeira_projecto_faturas(energia 
                                      , capex
                                      , opex
                                      , taxa_actualizacao
                                      , ano_0
                                      , tempo_vida                               
                                      , taxa_degradacao_sistema
                                      , taxa_inflacao
                                      , tarifario
                                      , precos_energia
                                      , venda_rede
                                      , nome_cols=['consumo', 'consumo_rede', 'injeccao_rede']
                                      , indicadores_autoconsumo = None):
    """ Calcula VAL, TIR e Tempo de retorno de projecto, LCOE utilizando o método dos cash-flows descontados. 
    Poupança calculada a partir do valores da faturas.

    Parameters
    ----------
    energia: pandas.DataFrame
        Serie temporal de energia em kwh na coluna 'autoconsumo'. 
        Adicionalmente coluna 'injeccao_rede' quando incluido venda à rede.
    capex : float
        Custos iniciais em €
    opex : float
        Custos operação em €
    taxa_actualizacao : float
        Taxa de actualização em %
    ano_0 : int
        Ano 0 do projecto
    tempo_vida : int
        Tempo de vida do projecto
    taxa_degradacao_sistema : float
        Taxa degradação energia do sistema por ano em %
    taxa_inflacao : float
        Taxa de inflação do preços energia em %
    tarifario: ape.Tarifario
        Tipo de tarifário: simples, bihorario, trihorario
    precos_energia : ape.TarifarioEnergia
        Preços de energia e venda à rede.
    venda_rede : bool
        True para considerar venda excedentes à rede, False para não considerar.
    nome_cols : list, default ['consumo', 'consumo_rede', 'injeccao_rede']
        List com nomes das colunas de consumo, consumo da rede e injeccao da rede.
    indicadores_autoconsumo : indicadores_autoconsumo, default: None
        Necessario para calculo do lcoe, necessita da capacidade instalada e horas equivalentes.
        Se None o lcoe não é calculado

    Returns
    -------
    data: indicadores_financeiros
        Os indicadores financeiros val, tir, tempo retorno, capex, opex, tempo_vida e lcoe.
    financeiro: pd.DataFrame
        Fluxos de caixa anuais utilizados na analise.
    """
    if (len(nome_cols) != 2) & (len(nome_cols) != 3) & (~venda_rede):
        raise ValueError("nome_cols deve ter 2 ou 3 valores quando venda_rede=False.")
    elif (len(nome_cols) != 3) & (venda_rede):
        raise ValueError("nome_cols deve ter 3 valores quando venda_rede=True.")

    col_consumo = nome_cols[0]
    col_consumo_rede = nome_cols[1]
    col_injeccao = nome_cols[2] if venda_rede else ''

    financeiro = pd.DataFrame({'ano' : range(ano_0, ano_0+tempo_vida+1, 1)})
    financeiro['ano_projecto'] = range(tempo_vida+1)
    # ano 0 operacao é o 1o ano financeiro, n ha perda de energia no ano 0
    financeiro['ano_operacao'] = np.maximum(financeiro['ano_projecto']-1,0)

    # conversao taxas
    rd = taxa_degradacao_sistema / 100
    infl = taxa_inflacao / 100

    # Lambdas
    if (tarifario == ape.Tarifario.Simples):
        func_energia = lambda ener, col, ano : ape.calcula_energia_mensal_tarifario_simples(ener, col)
        # custo sem upac é o consumo total e precos alterados de inflacao
        func_custo_sem_upac_mensal_faturas = lambda cons_mensal, infl, ano_op, ano : \
            cons_mensal.apply(lambda y : ape.calcula_fatura_tarifario_simples(y[col_consumo], \
                                                 monthrange(int(ano), y.name.month)[1], \
                                                 precos_energia.custo_kwh_simples*(1+infl)**ano_op, \
                                                 precos_energia.pot_contratada, \
                                                 precos_energia.pot_contratada_custo_dia*(1+infl)**ano_op, \
                                                 precos_energia.pot_contratada_termo_fixo_redes_custo_dia*(1+infl)**ano_op)[0], axis=1)
        # custo com upac é a producao alterada pela degradacao e precos alterados pela inflacao
        func_custo_com_upac_mensal_faturas = lambda cons_mensal, prod_mensal, rd, infl, ano_op, ano : \
            (cons_mensal - prod_mensal*(1-rd*np.maximum(ano_op-0.5,0))).apply(lambda y : \
                ape.calcula_fatura_tarifario_simples(y[col_consumo], \
                                                    monthrange(int(ano), y.name.month)[1], \
                                                    precos_energia.custo_kwh_simples*(1+infl)**ano_op, \
                                                    precos_energia.pot_contratada, \
                                                    precos_energia.pot_contratada_custo_dia*(1+infl)**ano_op, \
                                                    precos_energia.pot_contratada_termo_fixo_redes_custo_dia*(1+infl)**ano_op)[0], axis=1)
    elif (tarifario == ape.Tarifario.Bihorario):
        func_energia = lambda ener, col, ano : ape.calcula_energia_mensal_tarifario_bihorario(ener, col)
        # custo sem upac é o consumo total e precos alterados de inflacao
        func_custo_sem_upac_mensal_faturas = lambda cons_mensal, infl, ano_op, ano : \
            cons_mensal.apply(lambda y : ape.calcula_fatura_tarifario_bihorario(y['fora_vazio'], y['vazio'], \
                                                 monthrange(int(ano), y.name.month)[1], \
                                                 precos_energia.custo_bi_kwh_fora_vazio*(1+infl)**ano_op, \
                                                 precos_energia.custo_bi_kwh_vazio**(1+infl)**ano_op, \
                                                 precos_energia.pot_contratada, \
                                                 precos_energia.pot_contratada_custo_dia*(1+infl)**ano_op, \
                                                 precos_energia.pot_contratada_termo_fixo_redes_custo_dia*(1+infl)**ano_op)[0], axis=1)
        # custo com upac é a producao alterada pela degradacao e precos alterados pela inflacao
        func_custo_com_upac_mensal_faturas = lambda cons_mensal, prod_mensal, rd, infl, ano_op, ano : \
            (cons_mensal - prod_mensal*(1-rd*np.maximum(ano_op-0.5,0))).apply(lambda y : \
                ape.calcula_fatura_tarifario_bihorario(y['fora_vazio'], y['vazio'], \
                                                 monthrange(int(ano), y.name.month)[1], \
                                                 precos_energia.custo_bi_kwh_fora_vazio*(1+infl)**ano_op, \
                                                 precos_energia.custo_bi_kwh_vazio**(1+infl)**ano_op, \
                                                 precos_energia.pot_contratada, \
                                                 precos_energia.pot_contratada_custo_dia*(1+infl)**ano_op, \
                                                 precos_energia.pot_contratada_termo_fixo_redes_custo_dia*(1+infl)**ano_op)[0], axis=1)
                                            
    elif (tarifario == ape.Tarifario.Trihorario):
        func_energia = lambda ener, col, ano : ape.calcula_energia_mensal_tarifario_trihorario(ener, col, ano)
        # custo sem upac é o consumo total e precos alterados de inflacao
        func_custo_sem_upac_mensal_faturas = lambda cons_mensal, infl, ano_op, ano : \
            cons_mensal.apply(lambda y : ape.calcula_fatura_tarifario_trihorario(y['ponta'], y['cheia'], y['vazio'], \
                                                 monthrange(int(ano), y.name.month)[1], \
                                                 precos_energia.custo_tri_kwh_ponta*(1+infl)**ano_op, \
                                                 precos_energia.custo_tri_kwh_cheia*(1+infl)**ano_op, \
                                                 precos_energia.custo_tri_kwh_vazio*(1+infl)**ano_op, \
                                                 precos_energia.pot_contratada, \
                                                 precos_energia.pot_contratada_custo_dia*(1+infl)**ano_op, \
                                                 precos_energia.pot_contratada_termo_fixo_redes_custo_dia*(1+infl)**ano_op)[0], axis=1)
        # custo com upac é a producao alterada pela degradacao e precos alterados pela inflacao
        func_custo_com_upac_mensal_faturas = lambda cons_mensal, prod_mensal, rd, infl, ano_op, ano : \
            (cons_mensal - prod_mensal*(1-rd*np.maximum(ano_op-0.5,0))).apply(lambda y : \
                ape.calcula_fatura_tarifario_trihorario(y['ponta'], y['cheia'], y['vazio'], \
                                                 monthrange(int(ano), y.name.month)[1], \
                                                 precos_energia.custo_tri_kwh_ponta*(1+infl)**ano_op, \
                                                 precos_energia.custo_tri_kwh_cheia*(1+infl)**ano_op, \
                                                 precos_energia.custo_tri_kwh_vazio*(1+infl)**ano_op, \
                                                 precos_energia.pot_contratada, \
                                                 precos_energia.pot_contratada_custo_dia*(1+infl)**ano_op, \
                                                 precos_energia.pot_contratada_termo_fixo_redes_custo_dia*(1+infl)**ano_op)[0], axis=1)


    # lambda venda rede
    if venda_rede:
        func_venda_rede = lambda energia, rd, infl, ano_op, col: (energia[col]*(1-rd*np.maximum(ano_op-0.5,0))*precos_energia.preco_venda_kwh*(1+infl)**ano_op).sum() 

    # consumo e autoconsumo mensal ano 0
    consumo_mensal_sem_upac = func_energia(energia, col_consumo, ano_0)
    consumo_mensal_com_upac = func_energia(energia, col_consumo_rede, ano_0)
    producao_mensal = consumo_mensal_sem_upac - consumo_mensal_com_upac

    # calculo poupanca energia
    financeiro['custo_anual_sem_upac'] = financeiro.apply(lambda x : func_custo_sem_upac_mensal_faturas(consumo_mensal_sem_upac, infl, x['ano_operacao'], x['ano']).sum(), axis=1)
    financeiro['custo_anual_com_upac'] = financeiro.apply(lambda x : func_custo_com_upac_mensal_faturas(consumo_mensal_sem_upac, producao_mensal, rd, infl, x['ano_operacao'], x['ano']).sum(), axis=1) 
    financeiro['cash flow in'] = financeiro['custo_anual_sem_upac'] - financeiro['custo_anual_com_upac']
    financeiro['cash flow in'].iat[0] = 0  # ano 0 não ha entrada de dinheiro

    # calcula venda a rede se incluido
    if venda_rede:
        financeiro['cash venda rede'] = financeiro.apply( lambda x : func_venda_rede(energia, rd, infl, x['ano_operacao'], col_injeccao), axis=1)
        financeiro['cash venda rede'].iat[0] = 0 # ano 0 não ha entrada dinheiro
        financeiro['cash flow in'] = financeiro['cash flow in'] + financeiro['cash venda rede']


    # saida
    financeiro['cash flow out'] = [opex for i in range(tempo_vida+1)]
    financeiro['cash flow out'].iat[0] = capex

    # cash flows
    financeiro['cash flow'] = financeiro['cash flow in'] - financeiro['cash flow out']
    financeiro['cash flow acumulado'] = financeiro['cash flow'].cumsum()

    # VAL
    val = _val(financeiro, taxa_actualizacao)

    # TIR
    tir = _tir(financeiro, 10, tempo_vida)

    # Tempo retorno
    tr = _tempo_retorno(financeiro, tempo_vida)

    # LCOE
    lcoe = 0
    if (indicadores_autoconsumo is not None):
        lcoe = _lcoe(tempo_vida, capex, opex, taxa_actualizacao, indicadores_autoconsumo.capacidade_instalada, indicadores_autoconsumo.horas_equivalentes, taxa_degradacao_sistema)

    return indicadores_financeiros(val, tir, tr, capex, opex, tempo_vida, lcoe), financeiro

def analise_financeira_projecto_indicadores_autoconsumo_faturas(indicadores_autoconsumo
                                                        , iac_a_considerar
                                                        , capex
                                                        , opex
                                                        , taxa_actualizacao
                                                        , ano_0
                                                        , tempo_vida
                                                        , taxa_degradacao_sistema
                                                        , taxa_inflacao                
                                                        , precos_energia
                                                        , venda_rede
                                                        , nome_cols=['consumo', 'consumo_rede', 'injeccao_rede']):
    """ Analise financeira de projecto a partir de indicador de autoconsumo (IAC) e dos valores de consumo e produção
    anuais. 
    
    A análise tem como objectivo saber como seria o projecto com um IAC teórico. Como a análise é feita sobre valores anuais 
    igualmente distribuidos pelos mêses, apenas é possível utilizar o tarifário simples. 
    Não é possível prever o consumo e produção em bihorario e trihorario.

    Parameters
    ----------
    indicadores_autoconsumo : indicadores_autoconsumo
        Utilização da energia anual consumida e produzida para a análise financeira. O iac é ignorado.
    iac_a_considerar: float
        Indicador de autoconsumo a utilizar na análise para calcular energia produzida e autoconsumida.
    capex : float
        Custos iniciais em €
    opex : float
        Custos operação em €
    taxa_actualizacao : float
        Taxa de actualização em %
    ano_0 : int
        Ano 0 do projecto
    tempo_vida : int
        Tempo de vida do projecto
    taxa_degradacao_sistema : float
        Taxa degradação energia do sistema por ano em %
    taxa_inflacao : float
        Taxa de inflação em %
    precos_energia :  ape.TarifarioEnergia
        Preços de energia e venda à rede.
    venda_rede : bool
        True para considerar venda excedentes à rede, False para não considerar.
    nome_cols : list, default ['consumo', 'consumo_rede', 'injeccao_rede']
        List com nomes das colunas de consumo, consumo da rede e injeccao da rede.
    """
    if (len(nome_cols) != 2) & (len(nome_cols) != 3) & (~venda_rede):
        raise ValueError("nome_cols deve ter 2 ou 3 valores quando venda_rede=False.")
    elif (len(nome_cols) != 3) & (venda_rede):
        raise ValueError("nome_cols deve ter 3 valores quando venda_rede=True.")

    col_consumo = nome_cols[0]
    col_consumo_rede = nome_cols[1]
    col_injeccao = nome_cols[2] if venda_rede else ''

    financeiro = pd.DataFrame({'ano' : range(ano_0, ano_0+tempo_vida+1, 1)})
    financeiro['ano_projecto'] = range(tempo_vida+1)
    # ano 0 operacao é o 1o ano financeiro, n ha perda de energia no ano 0
    financeiro['ano_operacao'] = np.maximum(financeiro['ano_projecto']-1,0)

    # conversao taxas
    rd = taxa_degradacao_sistema / 100
    infl = taxa_inflacao / 100

    # lambdas tarifario simples
    # custo sem upac é o consumo total e precos alterados de inflacao
    func_custo_sem_upac_mensal_faturas = lambda cons_mensal, infl, ano_op, ano : \
        cons_mensal.apply(lambda y : ape.calcula_fatura_tarifario_simples(y[col_consumo], \
                                                monthrange(int(ano), y.name.month)[1], \
                                                precos_energia.custo_kwh_simples*(1+infl)**ano_op, \
                                                precos_energia.pot_contratada, \
                                                precos_energia.pot_contratada_custo_dia*(1+infl)**ano_op, \
                                                precos_energia.pot_contratada_termo_fixo_redes_custo_dia*(1+infl)**ano_op)[0], axis=1)
    # custo com upac é a producao alterada pela degradacao e precos alterados pela inflacao
    func_custo_com_upac_mensal_faturas = lambda cons_mensal, prod_mensal, rd, infl, ano_op, ano : \
        (cons_mensal - prod_mensal*(1-rd*np.maximum(ano_op-0.5,0))).apply(lambda y : \
            ape.calcula_fatura_tarifario_simples(y[col_consumo], \
                                                monthrange(int(ano), y.name.month)[1], \
                                                precos_energia.custo_kwh_simples*(1+infl)**ano_op, \
                                                precos_energia.pot_contratada, \
                                                precos_energia.pot_contratada_custo_dia*(1+infl)**ano_op, \
                                                precos_energia.pot_contratada_termo_fixo_redes_custo_dia*(1+infl)**ano_op)[0], axis=1)
    

    # consumo e autoconsumo no ano0 em data frame
    datas = pd.date_range('{}-01-01'.format(ano_0),'{}-01-01'.format(ano_0+1) , freq='1M')-pd.offsets.MonthBegin(1)
    consumo_mensal_sem_upac_val = indicadores_autoconsumo.consumo_total / 12
    consumo_mensal_sem_upac = pd.DataFrame({'consumo':[consumo_mensal_sem_upac_val]*12}, index=datas)
    producao_mensal_val = indicadores_autoconsumo.energia_autoproduzida*(iac_a_considerar/100)/12
    producao_mensal = pd.DataFrame({'consumo':[producao_mensal_val]*12}, index=datas)

    # calculo poupanca energia
    financeiro['custo_anual_sem_upac'] = financeiro.apply(lambda x : func_custo_sem_upac_mensal_faturas(consumo_mensal_sem_upac, infl, x['ano_operacao'], x['ano']).sum(), axis=1)
    financeiro['custo_anual_com_upac'] = financeiro.apply(lambda x : func_custo_com_upac_mensal_faturas(consumo_mensal_sem_upac, producao_mensal, rd, infl, x['ano_operacao'], x['ano']).sum(), axis=1) 
    financeiro['cash flow in'] = financeiro['custo_anual_sem_upac'] - financeiro['custo_anual_com_upac']
    financeiro['cash flow in'].iat[0] = 0  # ano 0 não ha entrada de dinheiro

    # se venda rede
    if (venda_rede):
        energia_venda_rede = indicadores_autoconsumo.energia_autoproduzida*(1-rd*np.maximum(financeiro['ano_operacao']-0.5,0)) * ( 1.0 - iac_a_considerar / 100.0)
        financeiro['cash venda rede'] = energia_venda_rede * precos_energia.preco_venda_kwh * (1+infl)**financeiro['ano_operacao']
        financeiro['cash venda rede'].iloc[0] = 0 # ano 0 não ha entrada dinheiro
        financeiro['cash flow in'] = financeiro['cash flow in'] + financeiro['cash venda rede']

    # saida
    financeiro['cash flow out'] = [opex for i in range(tempo_vida+1)]
    financeiro['cash flow out'].iat[0] = capex

    # cash flows
    financeiro['cash flow'] = financeiro['cash flow in'] - financeiro['cash flow out']
    financeiro['cash flow acumulado'] = financeiro['cash flow'].cumsum()

    # VAL
    val = _val(financeiro, taxa_actualizacao)

    # TIR
    tir = _tir(financeiro, 10, tempo_vida)

    # Tempo retorno
    tr = _tempo_retorno(financeiro, tempo_vida)

    # LCOE
    lcoe = 0
    if (indicadores_autoconsumo is not None):
        lcoe = _lcoe(tempo_vida, capex, opex, taxa_actualizacao, indicadores_autoconsumo.capacidade_instalada, indicadores_autoconsumo.horas_equivalentes, taxa_degradacao_sistema)

    return indicadores_financeiros(val, tir, tr, capex, opex, tempo_vida, lcoe), financeiro

def custo_energia_prosumidor(energia, pot_instalada, cap_bat, tarifario, params_financeiros):
    """ Custo da energia na perspectiva do prosumidor.

    Custo da energia ao longo da vida do projecto englobando o investimento em UPAC/baterias, 
    energia consumida da rede e vendida à rede.

    Parameters
    ----------
    energia : pd.Dataframe
        Dataframe com coluna: 'consumo', 'consumo_rede', 'injeccao_rede' e 'descarga_bateria'
    pot_instalada : float
        Potencia da UPAC. [kWp]
    cap_bat : float
        Capacidade da bateria. [kWh]
    energia_rede : float
        Total de energia consumida da rede. [kWh]
    energia_injectada_rede : float
        Total de energia injectada na rede. [kWh]
    consumo_anual : float
        Total de consumo anual de energia. [kWh]
    tarifario : Tarifario
        Tipo de tarifario, so disponivel simples e bihorario.
    params_financeiros : dict
        Dicionario com os parametros financeiros, seguintes parametros:
        - tempo_vida: tempo de vida do projecto. [anos]
        - tempo_vida_bat: tempo de vida da bateria. [anos]
        - pv_por_kW: custo de cada kWp instalado de PV. [€/kW]
        - bat_fixo: custo fixo de instalação de bateria. [€]
        - bat_euro_por_kWh: custo por cada kWh de bateria instalado. [€/kWh]
        - perc_custo_manutencao: percentagem do investimento gasto em manutenção anual. [%]
        - taxa_actualização: taxa de actualização. [%]
        - simples_kwh: preço compra à rede em tarifário simples. Só usado quando tarifario = tarifario.Simples. [€/kWh]
        - vazio_kwh: preço de compra à rede em vazio no tarifario bihorario. Só usado quando tarifario = tarifario.Bihorario. [€/kWh]
        - fora_vazio_kwh: preço de compra à rede fora de vazio no tarifario bihorario. Só usado quando tarifario = tarifario.Bihorario .[€/kWh]
        - preco_venda_rede: Preco de venda da energia à rede. [€/kWh]

    Returns
    -------
    coe : float
        Custo da energia poderado de cada kWh consumido. [€/kWh]
    coa : float
        Custo de armazenamento por kWh consumido da bateria. [€/kWh]
    custo_medio_compra_rede : float
        Custo medio da energia comprada à rede. [€/kWh]
    """
    consumo_anual = energia["consumo"].sum()
    energia_injectada_rede = energia["injeccao_rede"].sum()
    if 'descarga_bateria' in energia.columns:
        energia_bateria = energia['descarga_bateria'].sum()
    else:
        energia_bateria = 0

    custo_medio_compra_rede = 0
    total_consumo_rede = energia["consumo_rede"].sum()
    if tarifario == ape.Tarifario.Simples:
        compra_rede = total_consumo_rede * params_financeiros["simples_kwh"]
        custo_medio_compra_rede = params_financeiros["simples_kwh"]
    elif tarifario == ape.Tarifario.Bihorario:
        energia = ape.identifica_periodo_tarifario_bihorario(energia)
        total_vazio = energia.loc[(energia['periodo tarifario'] == 'vazio'), 'consumo_rede'].sum()
        total_fora_vazio = energia.loc[(energia['periodo tarifario'] == 'fora vazio'), 'consumo_rede'].sum()
        compra_rede = total_vazio * params_financeiros["vazio_kwh"] + total_fora_vazio * params_financeiros["fora_vazio_kwh"]
        custo_medio_compra_rede = compra_rede / total_consumo_rede
    else:
        raise Exception('Custo de energia so aceita tarifario simples ou bihorario.')

    invest_pv = params_financeiros["pv_por_kW"] * pot_instalada
    om = params_financeiros["perc_custo_manutencao"] / 100.0
    i = params_financeiros["taxa_actualizacao"] / 100.0

    invest_bat = 0
    if cap_bat > 0:
        invest_bat = params_financeiros["bat_fixo"] + params_financeiros["bat_euro_por_kWh"]*cap_bat
        # taxa desconto e segundo investimento em bateria ao longo do tempo de vida
        invest_bat = invest_bat * (1 + 1/(pow(1+i, params_financeiros["tempo_vida_bat"])))

    crf = (i * pow(1.0+i, params_financeiros["tempo_vida"])) / (pow(1.0+i,params_financeiros["tempo_vida"]) - 1.0)
    a = (invest_pv + invest_bat) * (crf + om)
    coe = (a + (compra_rede) - (energia_injectada_rede*params_financeiros["preco_venda_rede"]))/consumo_anual
    
    a_bat = invest_bat * (crf + om)
    coa = 0
    if energia_bateria > 0:
        coa = a_bat / energia_bateria

    return coe, coa, custo_medio_compra_rede

def _val(cash_flows, taxa_actualizacao):
    """ Valor actulizado liquido pelo método dos fluxo de caixa descontados.

    Args:
    -----
    cash_flows: pandas.DataFrame 
        fluxo de caixa por ano na coluna 'cash flow'
    taxa_actualizacao: float
        Taxa de actualizacao em %

    Returns:
    --------
    val: float
        Valor actual liquido do projecto
    """
    cash_flows['cash flow actualizado'] = cash_flows['cash flow'] / (1 + taxa_actualizacao/100)**cash_flows['ano_projecto']

    return cash_flows['cash flow actualizado'].sum()

def _tir(cash_flows, tir0, t, n_iter = 10):
    """ Taxa interna de retorno. 

    Calcular atraves do metodo iterativo de newton-raphson com uma aproximcaçao de 0.001.

    Args:
    -----
    cash_flows: pandas.DataFrame 
        fluxo de caixa por ano na coluna 'cash flow'
    tir0: float 
        Estimativa inicial para a tir em %
    t: int
        Número anos do projecto
    n_iter: int, default: 10
        Número de iterações para encontrar a solução. Para quando o valor da raiz for inferior a 0.001 ou apos n_iter. 
    
    Returns:
    --------
    tir: float
        Taxa interna de retorno
    """
    cf = cash_flows['cash flow'].to_frame('cash flow')
    cf['ano'] = np.arange(t+1)
    
    val = 100
    tir = tir0/100
    iter = 0
    while iter < n_iter:

        if iter > 0:
            # proxima tir
            tir = tir - (val / deriv_val)

        # cash flow = \sum CF*(1+t)**(-ano)
        cf['cash flow actualizado'] = cf['cash flow']*((1+(tir))**(-cf['ano']))
        # deriv cash flow = \sum CF*(-ano)*(1+t)**(-ano-1)
        cf['deriv cash flow act'] = -cf['cash flow']*cf['ano']*((1+(tir))**(-cf['ano']-1))
    
        val = cf['cash flow actualizado'].sum()
        deriv_val = cf['deriv cash flow act'].sum()
        iter += 1
        if abs(val) < 0.001:
            break

    return tir * 100

def _tempo_retorno(financeiro, tempo_vida):
    """ Tempo de retorno do projecto pelo metodo dos fluxo de caixa descontado.

    Args:
    -----
    financeiro: pandas.DataFrame
        Fluxo de caixa descontado por ano na coluna 'cash flow actualizado'
    tempo_vida: int
        Tempo de vida do projecto

    Returns:
    --------
    periodo_retorno: float
        Tempo de retorno em anos do projecto
    """
    financeiro['cash flow actualizado acumulado'] = financeiro['cash flow actualizado'].cumsum()
    ultimo_ano_negativo = financeiro[financeiro['cash flow actualizado acumulado'] < 0].index.values.max()
    ano_fracional = 0
    if abs(tempo_vida - ultimo_ano_negativo) > 0.5:
        ano_fracional = -financeiro['cash flow actualizado acumulado'][ultimo_ano_negativo]/financeiro['cash flow actualizado'][ultimo_ano_negativo + 1]
        
    periodo = ultimo_ano_negativo + ano_fracional
    return round(periodo, 1)

def _lcoe(n_anos, capex, opex, taxa_actualizacao, capacidade_instalada, n_horas_equivalentes, taxa_degradacao_sistema):
    """ Levelized cost of energy (€/kWh).

    Args:
    -----
    n_anos: int
        Tempo de vida do projecto
    capex: float
        Custo de investimento do projecto em €
    opex: float
        Custo operacional anual em €
    taxa_actualizacao: float
        Taxa de actualização em %
    capacidade_instalada: float
        Capacidade instalada em kW
    n_horas_equivalentes: float
        Numero de horas equivalentes à potência nominal
    taxa_degradacao_sistema: float
        Taxa de degradação anual da produção do sistema em %

    Returns:
    --------
    lcoe: float
        Custo nivelado da energia em €/kWh
    """
    df = pd.DataFrame({'ano' : range(n_anos+1)})
    # custos
    df['custo'] = 0
    df['custo'].iloc[0] = capex / capacidade_instalada # €/kWp
    df['custo'].iloc[1:] = opex / capacidade_instalada # €/kWp
    e0 = n_horas_equivalentes # kWh/kWp
    Rd = (taxa_degradacao_sistema / 100)

    # energia
    df['energia'] = e0*(1-Rd*(df['ano']-0.5))
    df['energia'].iloc[0] = 0

    # aplicar taxa de actualizacao
    df['custo'] = df['custo'] / pow(1+(taxa_actualizacao/100), df['ano'])
    df['energia'] = df['energia'] / pow(1+(taxa_actualizacao/100), df['ano'])

    lcoe = df['custo'].sum() / df['energia'].sum()
    return lcoe