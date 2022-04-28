""" Funcoes para analisar os gastos e precos de energia para os diferentes ciclos horarios em BTN

Fonte: https://www.erse.pt/media/wijn0vgt/periodos-hor%C3%A1rios-de-energia-el%C3%A9trica-em-portugal.pdf
"""

from datetime import datetime
from turtle import left
from xml.etree.ElementInclude import include
import pandas as pd
pd.options.mode.chained_assignment = None
import calendar

def calcula_tarifario_simples(energia, custo_kwh, col):
    """ Calcula custo no tarifario simples

    Args:
        energia_df: data frame com a serie de energia
        custo_kwh: custo do kwh em tarifario simples
        col: coluna da df a qual aplicar o custo
    """
    energia['custo'] = energia[col] * custo_kwh
    return energia['custo'].sum(), energia['custo']

def calcula_tarifario_bihorario_diario(energia, custo_kwh_fora_vazio, custo_kwh_vazio, col):
    """ Calcula custo total no tarifario bihorario diario. Nao varia de dia da semana nem por
    inverno e verão.
    
    Args:
        energia : dataframe com energia [kWh]
        custo_kwh_fora_vazio : preco fora vazio [€/kWh]
        custo_kwh_vazio : preco vazio [€/kWh]
        col : coluna dataframe com a energia

    Returns:
        custo total da energia. data frame com coluna custo por timestamp
    """
    energia_df = energia.copy()
    # Hora legal inverno/verao:
    #  Vazio : 22:00 as 08:00
    #  Fora Vazio : 08:00 as 22:00
    bins = [0, 8, 22, 24]
    precos = pd.DataFrame({'bins': [1, 2, 3], 'preco': [custo_kwh_vazio, custo_kwh_fora_vazio, custo_kwh_vazio]})
    energia_df['bins'] = pd.cut(energia_df.index.hour, bins, labels=precos.bins, right=False)
    energia_df['custo'] = energia_df[col] * energia_df['bins'].map(precos.set_index('bins')['preco'])
    energia_df = energia_df.drop('bins', 1)
    
    return energia_df['custo'].sum(), energia_df['custo']

def calcula_tarifario_trihorario_diario(energia, ano, c_ponta, c_cheias, c_vazio, col):
    """ Calcula custo total tarifario tri-horario diario, Não varia de dia da semana. Varia por inverno e verão.

    Args:
        energia : dataframe com energia [kWh]
        ano : ano de calculo
        c_ponta : preco ponta [€/kWh]
        c_cheias : preco cheias [€/kWh]
        c_vazio : preco vazio [€/kWh]
        col : coluna dataframe com a energia
    Returns:
        custo total da energia. data frame com coluna custo por timestamp
    """
    energia_df = energia.copy()
    energia_df = energia_df.drop('custo', axis=1, errors='ignore')
    # Hora de Inverno:
    #  Vazio: [22:00, 08:00[ (1, 7)
    #  Cheias: [08:00, 08:30[ (2), [10:30, 18:00[ (4) e [20:30, 22:00[ (6)
    #  Ponta: [08:30, 10:30[ (3), [18:00, 20:30[ (5)
    # Hora de Verao:
    #  Vazio: [22:00, 08:00[ (1, 7)
    #  Cheias: [08:00, 10:30[ (2), [13:00, 19:30[ (4) e [21:00, 22:00[ (6)
    #  Ponta: [10:30, 13:00[ (3), [19:30, 21:00[ (5)

    # n intervalos e precos sao os mesmos, so mudam os limites
    precos = pd.DataFrame({'bins': [1, 2, 3, 4, 5, 6, 7], 
                            'preco': [c_vazio, c_cheias, c_ponta, c_cheias, c_ponta, c_cheias, c_vazio]})

    # verifica hora legal
    dom_mar, dom_out = datas_horario_legal(ano)   
    bins_hora_legal = [0, dom_mar.timetuple().tm_yday, dom_out.timetuple().tm_yday, 367]
    # inverno (1, 3), verao 2
    labels_hora_legal = [1, 2, 3]
    energia_df['hora_legal'] = pd.cut(energia_df.index.dayofyear, bins_hora_legal, labels=labels_hora_legal, right=False)

    # inverno
    bins_inv = [0, 8, 8.5, 10.5, 18, 20.5, 22, 24]
    df_inv = energia_df[(energia_df['hora_legal'] == 1) | (energia_df['hora_legal'] == 3)]
    df_inv['bins'] = pd.cut(df_inv.index.hour + df_inv.index.minute / 60, bins_inv, labels=precos.bins, right=False)
    df_inv['custo'] = df_inv[col] * df_inv['bins'].map(precos.set_index('bins')['preco'])
    
    # verao
    bins_ver = [0, 8, 10.5, 13, 19.5, 21, 22, 24]
    df_ver = energia_df[(energia_df['hora_legal'] == 2)]
    df_ver['bins'] = pd.cut(df_ver.index.hour + df_ver.index.minute / 60, bins_ver, labels=precos.bins, right=False)
    df_ver['custo'] = df_ver[col] * df_ver['bins'].map(precos.set_index('bins')['preco'])
    df_inv_ver = pd.concat([df_inv, df_ver])
    energia_df = energia_df.merge(df_inv_ver['custo'],how='inner',left_index=True, right_index=True, sort=True)

    #energia['custo'] = energia_df['custo']
    return energia_df['custo'].sum(), energia_df['custo']

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