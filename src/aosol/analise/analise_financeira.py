""" Contem metodos para analise financeira de um projecto.

Calculo do VAL, TIR, Tempo de retorno de um projecto e o LCOE (levelized cost of energy)
do sistema produtor

.. math:
    VAL_n = \sum_{k=0}^{n} \frac{CF_{(in)}(k) - CF_{(out)}(k)}{(1+i)^k}

.. math:
    VAL_n = \sum_{k=0}^{n} \frac{CF_{(in)}(k) - CF_{(out)}(k)}{(1+TIR_n)^k} = 0

.. math:
    VAL_n = \sum_{k=0}^{payback} \frac{CF_{(in)}(k) - CF_{(out)}(k)}{(1+TIR_n)^k} = 0

Calculo do LCOE pelo método descrito no simulador NREL [2].

[1] Bloco 9 - Análise Investimentos, Universidade Evora.
    Em https://dspace.uevora.pt/rdpc/bitstream/10174/6309/11/BLOCO9.pdf
[2] F Militão, J Alberto. "O Método de Newton-Raphson no Cálculo do TIR", 
    UNOPAR Cient. Exatas Tecnol., Londrina, v. 11, n. 1, p. 59-63, Nov. 2012
[3] SJ Andrews, B Smith, MG Deceglie, KA Horowitz, and TJ Silverman. “NREL Comparative PV LCOE Calculator.” 
    Version 2.0.0, August 2021
"""
import pandas as pd
import numpy as np
#from aosol_project.src.aosol.analise.indicadores_financeiros import indicadores_financeiros
from .indicadores_financeiros import indicadores_financeiros

MESES = {1:'jan', 2:'fev', 3:'mar', 4:'abr', 5:'mai', 6:'jun',
         7:'jul', 8:'ago', 9:'set', 10:'out', 11:'nov', 12:'dez'}
MESES_COMPLETO = {1: 'Janeiro', 2:'Fevereiro', 3: u'Março', 4:'Abril',
               5:'Maio', 6:'Junho', 7:'Julho', 8:'Agosto',
               9:'Setembro', 10:'Outubro', 11:'Novembro', 12:'Dezembro'}

def analise_poupanca_anual(energia
                          , func_tarifario
                          , func_venda_rede=None):
    """ Calcula os custos em cada mes e anual da fatura sem UPAC e com UPAC, e a poupanca. Pode
    calcular também considerando a venda do excedente à rede.

    Args:
    -----
    energia : pandas.DataFrame
        Deve conter colunas 'consumo' e 'consumo_rede'. Adicionalmente a coluna 'injeccao_rede'
        se a venda a rede for incluida.
    func_tarifario : lambda
        Função que calcula o custo do tarifário dado a energia. 
        Lambda que recebe 3 argumentos energia, ano, coluna : calcula_tarifario_bihorario_diario(energia, custo_fora_vazio, custo_vazio, coluna) 
    func_venda_rede : lambda, default: None
        Função que calcula o valor recebido pela venda à rede do excesso de energia
        Lambda que recebe 2 argumentos energia, coluna : calcula_tarifario_simples(energia, preco_venda, coluna)

    Returns:
    -------
    mensal: pandas.DataFrame 
        Com os custos mensais e agregado anual
    """
    # fatura sem upac = consumo total
    _, custo = func_tarifario(energia, 'consumo')
    faturas = custo.to_frame('fatura sem upac')

    # fatura com upac = consumo rede
    _, custo = func_tarifario(energia, 'consumo_rede')
    faturas =  faturas.merge(custo.to_frame('fatura com upac'), how='inner', left_index=True, right_index=True) #energia['custo'].copy()
    faturas['poupanca'] = faturas['fatura sem upac'] - faturas['fatura com upac']

    # venda a rede = injeccao rede
    if (func_venda_rede is not None):
        _, ganho = func_venda_rede(energia, 'injeccao_rede')
        faturas =  faturas.merge(ganho.to_frame('venda a rede'), how='inner', left_index=True, right_index=True) #energia['custo'].copy()
        faturas['poupanca'] = faturas['poupanca'] + faturas['venda a rede']
    
    mensal = faturas.groupby([faturas.index.month]).sum()
    mensal.index.names = ['mes']
    mensal.index = mensal.index.map(MESES_COMPLETO)
    mensal.loc['Anual'] = mensal.sum(axis=0)
    return mensal
    
def analise_financeira_projecto(energia
                               , capex
                               , opex
                               , taxa_actualizacao
                               , ano_0
                               , tempo_vida                               
                               , taxa_degradacao_sistema
                               , func_tarifario
                               , indicadores_autoconsumo = None
                               , func_venda_rede = None):
    """ Calcula VAL, TIR e Tempo de retorno de projecto, LCOE utilizando o método dos cash-flows descontados.

    Args:
    -----
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
    func_tarifario : lambda
        Funcao que calcula o que se poupa com a energia autoconsumida. 
        O lambda recebe 3 argumentos energia, ano, coluna
    indicadores_autoconsumo : indicadores_autoconsumo, default: None
        Necessario para calculo do lcoe, necessita da capacidade instalada e horas equivalentes.
        Se None o lcoe não é calculado
    func_venda_rede : lambda, default: None
        Funcao que calcula o que se ganha com a venda do excesso à rede. Por defeito nao é incluido
        O lambda recebe 2 argumentos energia, col.

    Returns:
    --------
    data: indicadores_financeiros
        Os indicadores financeiros val, tir, tempo retorno, capex, opex, tempo_vida e lcoe
    financeiro: pd.DataFrame
        Fluxos de caixa anuais utilizados na analise
    """
    financeiro = pd.DataFrame({'ano' : range(ano_0, ano_0+tempo_vida+1, 1)})
    financeiro['ano_projecto'] = range(tempo_vida+1)
    
    # entradas
    rd = taxa_degradacao_sistema / 100
    # ano 0 operacao é o 1o ano financeiro, n ha perda de energia no ano 0
    financeiro['ano_operacao'] = np.maximum(financeiro['ano_projecto']-1,0)
    # aplica taxa degradacao a energia 
    financeiro['cash flow in'] = financeiro.apply(lambda x : func_tarifario(energia*(1-rd*(x['ano_operacao']-0.5)), x['ano'], 'autoconsumo')[0], axis=1)
    financeiro['cash flow in'].iloc[0] = 0  # ano 0 não ha entrada de dinheiro
    # calcula venda a rede se incluido
    if (func_venda_rede is not None):
        financeiro['cash venda rede'] = financeiro.apply( lambda x : func_venda_rede(energia*(1-rd*(x['ano_operacao']-0.5)), 'injeccao_rede')[0], axis=1)
        financeiro['cash venda rede'].iloc[0] = 0 # ano 0 não ha entrada dinheiro
        financeiro['cash flow in'] = financeiro['cash flow in'] + financeiro['cash venda rede']

    # saida
    financeiro['cash flow out'] = [opex for i in range(tempo_vida+1)]
    financeiro['cash flow out'].iloc[0] = capex

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
        lcoe = _lcoe(tempo_vida, capex, opex, taxa_actualizacao, indicadores_autoconsumo, taxa_degradacao_sistema)

    return indicadores_financeiros(val, tir, tr, capex, opex, tempo_vida, lcoe), financeiro

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

def _lcoe(n_anos, capex, opex, taxa_actualizacao, indicadores_autoconsumo, taxa_degradacao_sistema):
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
    indicadores_autoconsumo: indicadores_autoconsumo
        Indicadores de capacidade_instalada e horas_equivalentes
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
    df['custo'].iloc[0] = capex / indicadores_autoconsumo.capacidade_instalada # €/kWp
    df['custo'].iloc[1:] = opex / indicadores_autoconsumo.capacidade_instalada # €/kWp
    e0 = indicadores_autoconsumo.horas_equivalentes # kWh/kWp
    Rd = (taxa_degradacao_sistema / 100)

    # energia
    df['energia'] = e0*(1-Rd*(df['ano']-0.5))
    df['energia'].iloc[0] = 0

    # aplicar taxa de actualizacao
    df['custo'] = df['custo'] / pow(1+(taxa_actualizacao/100), df['ano'])
    df['energia'] = df['energia'] / pow(1+(taxa_actualizacao/100), df['ano'])

    lcoe = df['custo'].sum() / df['energia'].sum()
    return lcoe