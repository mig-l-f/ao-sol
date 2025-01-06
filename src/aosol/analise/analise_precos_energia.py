""" Funcoes para analisar o preço da faturas [1]_ e precos de energia para os diferentes ciclos horarios em BTN [2]_.

.. [1] ERSE. Aplicação do IVA na factura da electricidade.
    Em https://www.erse.pt/media/yodok3zt/ersexplica_aplica%C3%A7%C3%A3o-do-iva.pdf
    Versão implementada Dezembro 2020.

.. [2] ERSE. Períodos horários na energia em Portugal.
    Em https://www.erse.pt/media/wijn0vgt/periodos-hor%C3%A1rios-de-energia-el%C3%A9trica-em-portugal.pdf

"""

from datetime import datetime
from turtle import left
from xml.etree.ElementInclude import include
import pandas as pd
pd.options.mode.chained_assignment = None
import calendar
from typing import NamedTuple
from enum import Enum

class Tarifario(Enum):
    Simples = 1,
    Bihorario = 2,
    Trihorario = 3

class PotenciaContratada(Enum):
    kVA_1_15 = 1,
    kVA_2_3 = 2,
    kVA_3_45 = 3,
    kVA_4_6 = 4,
    kVA_5_75 = 5,
    kVA_6_9 = 6

class TarifarioEnergia(NamedTuple):
    custo_kwh_simples : float = 0.0
    custo_bi_kwh_fora_vazio : float = 0.0
    custo_bi_kwh_vazio : float = 0.0
    custo_tri_kwh_ponta : float = 0.0
    custo_tri_kwh_cheia : float = 0.0
    custo_tri_kwh_vazio : float = 0.0
    preco_venda_kwh : float = 0.0
    pot_contratada : PotenciaContratada = PotenciaContratada.kVA_3_45
    pot_contratada_custo_dia : float = 0.0
    pot_contratada_termo_fixo_redes_custo_dia : float = 0.0

class _TermosFatura(Enum):
    PotContratadaTermoFixo = 1,
    PotContratadaTermoVariavel = 2,
    EnergiaAteLimiar = 3,
    EnegiaAcimaLimiar = 4

def datas_horario_legal(ano):
    """ Horario legal de verao é do ultimo domingo de março ao ultimo domingo de outubro. O Horario legal de inverno
    vai do ultimo domingo de outubro ao ultimo domingo de março.

    Args:
        ano: ano
    Returns:
        [domingo de março, domingo de outubro]
    """
    cal = calendar.Calendar(firstweekday=0)
    mar = cal.monthdayscalendar(ano, 3)
    dom_mar = datetime(ano, 3, max([week[6] for week in mar if week[0]>0]))

    out = cal.monthdayscalendar(ano, 10)
    dom_out = datetime(ano, 10, max([week[6] for week in out if week[0]>0]))
    return dom_mar, dom_out

def _taxas_iva(termo_fatura, pot_contratada):
    """ Taxas de iva aplicadas aos varios termos da fatura dada a potencia contratada

    Args:
        termo_fatura: TermoFatura
            Enum com o termo da fatura para o qual queremos a taxa de iva
        pot_contratada: PotenciaContratada
            Enum com a potencia contratada
    Returns:
        taxa_iva : float
            Taxa de iva [0-1]
    """
    if termo_fatura == _TermosFatura.PotContratadaTermoVariavel \
        or termo_fatura == _TermosFatura.EnegiaAcimaLimiar:
        return 0.23

    if pot_contratada == PotenciaContratada.kVA_1_15 \
        or pot_contratada == PotenciaContratada.kVA_2_3 \
        or pot_contratada == PotenciaContratada.kVA_3_45:
        if termo_fatura == _TermosFatura.PotContratadaTermoFixo:
            return 0.06
        elif termo_fatura == _TermosFatura.EnergiaAteLimiar:
            return 0.13
    else:
        if termo_fatura == _TermosFatura.PotContratadaTermoFixo:
            return 0.23
        elif termo_fatura == _TermosFatura.EnergiaAteLimiar:
            return 0.13

def calcula_fatura_tarifario_simples(consumo, n_dias, custo_kwh, pot_contratada, pot_contratada_custo_dia, termo_fixo_redes_custo_dia):
    """ Calcula fatura de energia completa com iva e todos os termos para tarifario simples

    Fonte: https://www.erse.pt/media/pzievesl/ersexplica_aplica%C3%A7%C3%A3o-do-iva.pdf

    Args:
        consumo : float
            Consumo em kWh durante o periodo de faturacao
        n_dias : int
            Numero de dias do periodo de faturacao
        custo_kwh : float
            Preco de kWh em €
        pot_contratada : PotenciaContratada
            Enum com a potencia contratada em kVA
        pot_contratada_custo_dia : float
            Termo potência contratada em valor €/dia
        termo_fixo_redes_custo_dia : float
            Termo fixo de acesso às redes da potência contratada. Valor em €/dia
    Returns:
        total_c_iva : float
            Custo total da fatura com IVA em €
        total_s_iva : float
            Custo total da fatura sem IVA em €
    """
    # valores fixos
    limiar_consumo_30_dias = 100 # limiar de consumo em 30 dias em tarifario simples para taxa de iva intermedia
    imposto_especial_consumo = 0.001 # €/kWh
    contibuicao_audiovisual = 2.85 # em € valor fixo por mês
    taxa_dgeg = 0.07 # em € valor fixo por mês

    limiar_consumo = round((n_dias / 30) * limiar_consumo_30_dias)
    # termo energia
    custo_energia_ate_limiar = min(consumo, limiar_consumo) * custo_kwh
    iva_energia_ate_limiar = custo_energia_ate_limiar * _taxas_iva(_TermosFatura.EnergiaAteLimiar, pot_contratada)
    custo_energia_acima_limiar = max(0, consumo-limiar_consumo) * custo_kwh
    iva_energia_acima_limiar = custo_energia_acima_limiar * _taxas_iva(_TermosFatura.EnegiaAcimaLimiar, pot_contratada)

    # termo potencia contratada
    custo_pot_contratada_termo_fixo = n_dias * termo_fixo_redes_custo_dia
    iva_pot_contratada_termo_fixo = custo_pot_contratada_termo_fixo * _taxas_iva(_TermosFatura.PotContratadaTermoFixo, pot_contratada)
    custo_pot_contratada_termo_var = n_dias * (pot_contratada_custo_dia - termo_fixo_redes_custo_dia)
    iva_pot_contratada_termo_var = custo_pot_contratada_termo_var * _taxas_iva(_TermosFatura.PotContratadaTermoVariavel, pot_contratada)
    
    # impostos
    custo_imposto_especial_consumo = consumo * imposto_especial_consumo
    iva_imposto_especial_consumo = custo_imposto_especial_consumo * 0.23
    iva_contribuicao_audiovisual = contibuicao_audiovisual * 0.06
    iva_taxa_dgeg = taxa_dgeg * 0.23

    total_s_iva = custo_energia_ate_limiar + custo_energia_acima_limiar \
                + custo_pot_contratada_termo_fixo + custo_pot_contratada_termo_var \
                + custo_imposto_especial_consumo + contibuicao_audiovisual + taxa_dgeg
    total_iva = iva_energia_ate_limiar + iva_energia_acima_limiar \
              + iva_pot_contratada_termo_fixo + iva_pot_contratada_termo_var \
              + iva_imposto_especial_consumo + iva_contribuicao_audiovisual + iva_taxa_dgeg
    total_c_iva = total_s_iva + total_iva 
    return round(total_c_iva, 2), round(total_s_iva, 2)

def calcula_fatura_tarifario_bihorario(consumo_fora_vazio, consumo_vazio, n_dias, custo_kwh_fora_vazio, custo_kwh_vazio, pot_contratada, pot_contratada_custo_dia, termo_fixo_redes_custo_dia):
    """ Calcula fatura de energia completa com iva e todos os termos para tarifario bi-horario

    Parameters
    ----------
    consumo_fora_vazio : float
        Consumo em kWh durante o periodo fora de vazio. [kWh]
    consumo_vazio : float
        Consumo em kWh durante o periodo de vazio. [kWh]
    n_dias : int
        Numero de dias do periodo de faturacao. [-]
    custo_kwh_fora_vazio : float
        Preco de kWh periodo fora de vazio. [€]
    custo_kwh_vazio : float
        Preco de kWh periodo vazio. [€]
    pot_contratada : PotenciaContratada
        Enum com a potencia contratada em kVA
    pot_contratada_custo_dia : float
        Termo potência contratada. [€/dia]
    termo_fixo_redes_custo_dia : float
        Termo fixo de acesso às redes da potência contratada. [€/dia]

    Returns
    -------
    total_c_iva : float
        Custo total da fatura com IVA. [€]
    total_s_iva : float
        Custo total da fatura sem IVA. [€]
    """
    limiar_consumo_30_dias = 100 #
    imposto_especial_consumo = 0.001 # €/kWh
    contibuicao_audiovisual = 2.85 # em € valor fixo por mês
    taxa_dgeg = 0.07 # em € valor fixo por mês

    # limiar de consumo, 1º ajustar ao numero de dias de faturacao
    # para multi-horario: a taxa de IVA intermédia é aplicável até aos limiares de consumo de cada
    #  período horário, na proporção do consumo efetivamente faturado em cada período horário 
    limiar_consumo = round(n_dias/30)*limiar_consumo_30_dias
    # proporcao consumo em cada periodo horario
    total_consumo = consumo_fora_vazio + consumo_vazio
    prop_fora_vazio = consumo_fora_vazio / total_consumo 
    prop_vazio = consumo_vazio / total_consumo
    limiar_consumo_fora_vazio = round(prop_fora_vazio * limiar_consumo)
    limiar_consumo_vazio = round(prop_vazio * limiar_consumo)

    # termo energia
    custo_energia_fora_vazio_ate_limiar = min(consumo_fora_vazio, limiar_consumo_fora_vazio) * custo_kwh_fora_vazio
    iva_energia_fora_vazio_ate_limiar = custo_energia_fora_vazio_ate_limiar * _taxas_iva(_TermosFatura.EnergiaAteLimiar, pot_contratada)
    custo_energia_fora_vazio_acima_limiar = max(0, consumo_fora_vazio-limiar_consumo_fora_vazio) * custo_kwh_fora_vazio
    iva_energia_fora_vazio_acima_limiar = custo_energia_fora_vazio_acima_limiar * _taxas_iva(_TermosFatura.EnegiaAcimaLimiar, pot_contratada)

    custo_energia_vazio_ate_limiar = min(consumo_vazio, limiar_consumo_vazio) * custo_kwh_vazio
    iva_energia_vazio_ate_limiar = custo_energia_vazio_ate_limiar * _taxas_iva(_TermosFatura.EnergiaAteLimiar, pot_contratada)
    custo_energia_vazio_acima_limiar = max(0, consumo_vazio-limiar_consumo_vazio) * custo_kwh_vazio
    iva_energia_vazio_acima_limiar = custo_energia_vazio_acima_limiar * _taxas_iva(_TermosFatura.EnegiaAcimaLimiar, pot_contratada)

    # termo potencia contratada
    custo_pot_contratada_termo_fixo = n_dias * termo_fixo_redes_custo_dia
    iva_pot_contratada_termo_fixo = custo_pot_contratada_termo_fixo * _taxas_iva(_TermosFatura.PotContratadaTermoFixo, pot_contratada)
    custo_pot_contratada_termo_var = n_dias * (pot_contratada_custo_dia - termo_fixo_redes_custo_dia)
    iva_pot_contratada_termo_var = custo_pot_contratada_termo_var * _taxas_iva(_TermosFatura.PotContratadaTermoVariavel, pot_contratada)
    
    # impostos
    custo_imposto_especial_consumo = total_consumo * imposto_especial_consumo
    iva_imposto_especial_consumo = custo_imposto_especial_consumo * 0.23
    iva_contribuicao_audiovisual = contibuicao_audiovisual * 0.06
    iva_taxa_dgeg = taxa_dgeg * 0.23

    total_s_iva = custo_energia_fora_vazio_ate_limiar + custo_energia_fora_vazio_acima_limiar \
                + custo_energia_vazio_ate_limiar + custo_energia_vazio_acima_limiar \
                + custo_pot_contratada_termo_fixo + custo_pot_contratada_termo_var \
                + custo_imposto_especial_consumo + contibuicao_audiovisual + taxa_dgeg
    total_iva = iva_energia_fora_vazio_ate_limiar + iva_energia_fora_vazio_acima_limiar \
              + iva_energia_vazio_ate_limiar + iva_energia_vazio_acima_limiar \
              + iva_pot_contratada_termo_fixo + iva_pot_contratada_termo_var \
              + iva_imposto_especial_consumo + iva_contribuicao_audiovisual + iva_taxa_dgeg
    total_c_iva = total_s_iva + total_iva
    return round(total_c_iva, 2), round(total_s_iva, 2)

def calcula_fatura_tarifario_trihorario(consumo_ponta, consumo_cheia, consumo_vazio, n_dias, c_ponta, c_cheias, c_vazio, pot_contratada, pot_contratada_custo_dia, termo_fixo_redes_custo_dia):
    """ Calcula fatura de energia completa com iva e todos os termos para tarifario tri-horario

    Fonte: https://www.erse.pt/media/pzievesl/ersexplica_aplica%C3%A7%C3%A3o-do-iva.pdf

    Args:
        consumo_ponta : float
            Consumo em kWh durante o periodo de ponta
        consumo_cheia : float
            Consumo em kWh durante o periodo de cheia
        consumo_vazio : float
            Consumo em kWh durante o periodo de vazio
        n_dias : int
            Numero de dias do periodo de faturacao
        c_ponta : float
            Preco de kWh periodo ponta em €
        c_cheias : float
            Preco de kWh periodo cheia em €
        c_vazio : float
            Preco de kWh periodo vazio em €
        pot_contratada : PotenciaContratada
            Enum com a potencia contratada em kVA
        pot_contratada_custo_dia : float
            Termo potência contratada em valor €/dia
        termo_fixo_redes_custo_dia : float
            Termo fixo de acesso às redes da potência contratada. Valor em €/dia
    """
    limiar_consumo_30_dias = 100 #
    imposto_especial_consumo = 0.001 # €/kWh
    contibuicao_audiovisual = 2.85 # em € valor fixo por mês
    taxa_dgeg = 0.07 # em € valor fixo por mês

    # limiar de consumo, 1º ajustar ao numero de dias de faturacao
    # para multi-horario: a taxa de IVA intermédia é aplicável até aos limiares de consumo de cada
    #  período horário, na proporção do consumo efetivamente faturado em cada período horário 
    limiar_consumo = round(n_dias/30)*limiar_consumo_30_dias
    # proporcao consumo em cada periodo horario
    total_consumo = consumo_ponta+consumo_cheia+consumo_vazio
    prop_ponta = consumo_ponta / total_consumo
    prop_cheia = consumo_cheia / total_consumo
    prop_vazio = consumo_vazio / total_consumo
    limiar_consumo_ponta = round(prop_ponta * limiar_consumo)
    limiar_consumo_cheia = round(prop_cheia * limiar_consumo)
    limiar_consumo_vazio = round(prop_vazio * limiar_consumo)

    # termo energia
    custo_energia_ponta_ate_limiar = min(consumo_ponta, limiar_consumo_ponta) * c_ponta
    iva_energia_ponta_ate_limiar = custo_energia_ponta_ate_limiar * _taxas_iva(_TermosFatura.EnergiaAteLimiar, pot_contratada)
    custo_energia_ponta_acima_limiar = max(0, consumo_ponta-limiar_consumo_ponta) * c_ponta
    iva_energia_ponta_acima_limiar = custo_energia_ponta_acima_limiar * _taxas_iva(_TermosFatura.EnegiaAcimaLimiar, pot_contratada)

    custo_energia_cheia_ate_limiar = min(consumo_cheia, limiar_consumo_cheia) * c_cheias
    iva_energia_cheia_ate_limiar = custo_energia_cheia_ate_limiar * _taxas_iva(_TermosFatura.EnergiaAteLimiar, pot_contratada)
    custo_energia_cheia_acima_limiar = max(0, consumo_cheia-limiar_consumo_cheia) * c_cheias
    iva_energia_cheia_acima_limiar = custo_energia_cheia_acima_limiar * _taxas_iva(_TermosFatura.EnegiaAcimaLimiar, pot_contratada)

    custo_energia_vazio_ate_limiar = min(consumo_vazio, limiar_consumo_vazio) * c_vazio
    iva_energia_vazio_ate_limiar = custo_energia_vazio_ate_limiar * _taxas_iva(_TermosFatura.EnergiaAteLimiar, pot_contratada)
    custo_energia_vazio_acima_limiar = max(0, consumo_vazio-limiar_consumo_vazio) * c_vazio
    iva_energia_vazio_acima_limiar = custo_energia_vazio_acima_limiar * _taxas_iva(_TermosFatura.EnegiaAcimaLimiar, pot_contratada)

    # termo potencia contratada
    custo_pot_contratada_termo_fixo = n_dias * termo_fixo_redes_custo_dia
    iva_pot_contratada_termo_fixo = custo_pot_contratada_termo_fixo * _taxas_iva(_TermosFatura.PotContratadaTermoFixo, pot_contratada)
    custo_pot_contratada_termo_var = n_dias * (pot_contratada_custo_dia - termo_fixo_redes_custo_dia)
    iva_pot_contratada_termo_var = custo_pot_contratada_termo_var * _taxas_iva(_TermosFatura.PotContratadaTermoVariavel, pot_contratada)

    # impostos
    custo_imposto_especial_consumo = total_consumo * imposto_especial_consumo
    iva_imposto_especial_consumo = custo_imposto_especial_consumo * 0.23
    iva_contribuicao_audiovisual = contibuicao_audiovisual * 0.06
    iva_taxa_dgeg = taxa_dgeg * 0.23

    total_s_iva = custo_energia_ponta_ate_limiar + custo_energia_ponta_acima_limiar \
                + custo_energia_cheia_ate_limiar + custo_energia_cheia_acima_limiar \
                + custo_energia_ponta_ate_limiar + custo_energia_ponta_acima_limiar \
                + custo_pot_contratada_termo_fixo + custo_pot_contratada_termo_var \
                + custo_imposto_especial_consumo + contibuicao_audiovisual + taxa_dgeg
    total_iva = iva_energia_ponta_ate_limiar + iva_energia_ponta_acima_limiar \
              + iva_energia_cheia_ate_limiar + iva_energia_cheia_acima_limiar \
              + iva_energia_vazio_ate_limiar + iva_energia_vazio_acima_limiar \
              + iva_pot_contratada_termo_fixo + iva_pot_contratada_termo_var \
              + iva_imposto_especial_consumo + iva_contribuicao_audiovisual + iva_taxa_dgeg
    total_c_iva = total_s_iva + total_iva  

    return round(total_c_iva, 2), round(total_s_iva, 2)

def calcula_energia_mensal_tarifario_simples(energia, col):
    """ Calcula o consumo em cada mes da series temporal de energia. 
    Valor a ser utilizado para calcular o tarifario simples.

    Parameters
    ----------
    energia : pandas.DataFrame
        Dataframe com as series temporais de energia
    col : str
        coluna da dataframe com a serie de energia

    Returns
    -------
    energia_mensal : pandas.DataFrame
        Dataframe com serie mensal de consumo em coluna consumo.
    """
    consumo_mensal = energia[col].resample('M').sum().to_frame('consumo')
    return consumo_mensal

def calcula_energia_mensal_tarifario_bihorario(energia, col):
    """ Calcula o consumo em periodo vazio e fora vazio em cada mes da series temporal de energia. 
    Valor a ser utilizado para calcular o tarifario bihorario.

    Parameters
    ----------
    energia : pandas.DataFrame
        Dataframe com as series temporais de energia.
    col : str
        coluna da dataframe com a serie de energia.

    Returns
    -------
    energia_mensal : pandas.DataFrame
        Dataframe com serie mensal de consumo em colunas vazio e fora_vazio.
    """
    energia_df = energia.copy()

    energia_df = identifica_periodo_tarifario_bihorario(energia_df)
    consumo_vazio = energia_df.loc[energia_df['periodo tarifario']=='vazio', col].resample('M').sum().to_frame('vazio')
    consumo_mensal = energia_df.loc[energia_df['periodo tarifario']=='fora vazio', col].resample('M').sum().to_frame('fora_vazio')
    consumo_mensal = consumo_mensal.join(consumo_vazio, how="outer")
    return consumo_mensal

def calcula_energia_mensal_tarifario_trihorario(energia, col, ano):
    """ Calcula o consumo em periodo ponta, cheia e vazio em cada mes da series temporal de energia. 
    Valor a ser utilizado para calcular o tarifario trihorario.

    Parameters
    ----------
    energia : pandas.DataFrame
        Dataframe com as series temporais de energia.
    col : str
        coluna da dataframe com a serie de energia.
    ano : int
        ano para o qual estamos a calcular.

    Returns
    -------
    energia_mensal : pandas.DataFrame
        Dataframe com serie mensal de consumo em colunas 'ponta', 'cheia' e 'vazio'.
    """
    energia_df = energia.copy()
    energia_df = identifica_periodo_tarifario_trihorario(energia_df, ano)

    # calcular valores mensais
    consumo_vazio = energia_df.loc[(energia_df['periodo tarifario'] == 'vazio'), col].resample('M').sum().to_frame('vazio')
    consumo_cheia = energia_df.loc[(energia_df['periodo tarifario'] == 'cheia'), col].resample('M').sum().to_frame('cheia')
    consumo_mensal = energia_df.loc[(energia_df['periodo tarifario'] == 'ponta'), col].resample('M').sum().to_frame('ponta')
    consumo_mensal = consumo_mensal.join(consumo_cheia, how="outer")
    consumo_mensal = consumo_mensal.join(consumo_vazio, how="outer")
    return consumo_mensal
    
def identifica_periodo_tarifario_bihorario(energia):
    """ Identifica os periodos bihorarios na dataframe.

    Identifica e marca os periodos bihorarios na dataframe numa nova coluna 'periodo tarifario'. Os periodos
    bihorários na hora legal de inverno/verão são:
    - vazio: 22:00 ás 08:00
    - fora vazio: 08:00 ás 22:00 

    Parameters
    ----------
    energia: pd.Dataframe
        Dataframe com as horas no indice.

    Returns
    -------
    energia : pd.Dataframe
        A dataframe original com nova columa 'periodo tarifario' identificando periodos:'vazio' e 'fora vazio'
    """
    bins = [0, 8, 22, 24]
    energia['bins'] = pd.cut(energia.index.hour, bins, labels=[1, 2, 3], right=False)
    energia['periodo tarifario'] = 'fora vazio'
    energia.loc[(energia['bins'] == 1) | (energia['bins'] == 3),'periodo tarifario'] = 'vazio'
    energia = energia.drop('bins', axis=1)
    return energia
    
def identifica_periodo_tarifario_trihorario(energia, ano):
    """ Identifica os periodos trihorarios na dataframe.

    Identifica e marca os periodos bihorarios na dataframe numa nova coluna 'periodo tarifario'. Os periodos
    trihorários são os seguintes:
    - Hora de Inverno:
        - Vazio: [22:00, 08:00[
        - Cheias: [08:00, 08:30[, [10:30, 18:00[ e [20:30, 22:00[
        - Ponta: [08:30, 10:30[, [18:00, 20:30[
    - Hora de Verao:
        - Vazio: [22:00, 08:00[
        - Cheias: [08:00, 10:30[, [13:00, 19:30[ e [21:00, 22:00[
        - Ponta: [10:30, 13:00[, [19:30, 21:00[

    Parameters
    ----------
    energia: pd.DataFrame
        Dataframe com horas no indice.
    ano: int
        Ano a que diz respeito o cálculo.

    Returns
    -------
    energia: pd.Dataframe
        Dataframe original com coluna 'periodo tarifario' identificando periodos: 'vazio', 'cheia' e 'ponta'.
    """
    # Periodos e respectivos bins
    # Hora de Inverno:
    #  Vazio: [22:00, 08:00[ (1, 7)
    #  Cheias: [08:00, 08:30[ (2), [10:30, 18:00[ (4) e [20:30, 22:00[ (6)
    #  Ponta: [08:30, 10:30[ (3), [18:00, 20:30[ (5)
    # Hora de Verao:
    #  Vazio: [22:00, 08:00[ (1, 7)
    #  Cheias: [08:00, 10:30[ (2), [13:00, 19:30[ (4) e [21:00, 22:00[ (6)
    #  Ponta: [10:30, 13:00[ (3), [19:30, 21:00[ (5)
        # verifica hora legal
    dom_mar, dom_out = datas_horario_legal(ano)   
    bins_hora_legal = [0, dom_mar.timetuple().tm_yday, dom_out.timetuple().tm_yday, 367]
    # inverno (1, 3), verao 2
    labels_hora_legal = [1, 2, 3]
    energia['hora_legal'] = pd.cut(energia.index.dayofyear, bins_hora_legal, labels=labels_hora_legal, right=False)

    # inverno
    # bins: 1 = vazio, 2 = cheia, 3 = ponta, 4 = cheia, 5 = ponta, 6 = cheia, 7 = vazio
    bins_inv = [0, 8, 8.5, 10.5, 18, 20.5, 22, 24]
    df_inv = energia[(energia['hora_legal'] == 1) | (energia['hora_legal'] == 3)]
    df_inv['bins'] = pd.cut(df_inv.index.hour + df_inv.index.minute / 60, bins_inv, labels=[1, 2, 3, 4, 5, 6, 7], right=False)
    
    # verao
    bins_ver = [0, 8, 10.5, 13, 19.5, 21, 22, 24]
    df_ver = energia[(energia['hora_legal'] == 2)]
    df_ver['bins'] = pd.cut(df_ver.index.hour + df_ver.index.minute / 60, bins_ver, labels=[1, 2, 3, 4, 5, 6, 7], right=False)

    # juntar periodo inverno e verao e fazer merge da coluna bin na df com energia
    df_inv_ver = pd.concat([df_inv, df_ver])
    energia = energia.merge(df_inv_ver['bins'],how='inner',left_index=True, right_index=True, sort=True)

    # marcar todos como vazio
    energia['periodo tarifario'] = 'vazio'
    # alterar a ponta e cheia
    energia.loc[(energia['bins'] == 2) | (energia['bins'] == 4) | (energia['bins'] == 6), 'periodo tarifario'] = 'cheia'
    energia.loc[(energia['bins'] == 3) | (energia['bins'] == 5), 'periodo tarifario'] = 'ponta'

    return energia
