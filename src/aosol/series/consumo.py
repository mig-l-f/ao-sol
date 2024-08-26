""" Contem metodos para processar e tratar dados de consumo
"""
import pandas as pd
import numpy as np
import datetime
import glob
import os
from dateutil.relativedelta import relativedelta 
import locale
locale.setlocale(locale.LC_TIME, "pt_PT") # processar datas em PT

def leitura_perfis_eredes(ficheiro, perfil):
    """ Leitura de ficheiro com perfis e-redes.

    Args:
    -----
    ficheiro: str
        Caminho para o ficheiro
    perfil: str
        Coluna ou colunas do ficheiro a guardar. Tipicamente 'BTN C', 'BTN A', 'BTN B', 'IP'

    Retuns:
    ------
    perfil: pandas.DataFrame
        Dataframe com o perfil ou perfis escolhidos
    """
    perfis_eredes = pd.read_csv(ficheiro, sep=';')

    # Converter para floats, ficheiros com/sem \t, 1a linha cobre os com tab, 2a os sem tab
    perfis_eredes = perfis_eredes.replace("\t0,","0.", regex=True)
    perfis_eredes = perfis_eredes.replace("0,","0.", regex=True)
    perfis_eredes['BTN A'] = perfis_eredes['BTN A'].astype(float)
    perfis_eredes['BTN B'] = perfis_eredes['BTN B'].astype(float)
    perfis_eredes['BTN C'] = perfis_eredes['BTN C'].astype(float)
    perfis_eredes['IP'] = perfis_eredes['IP'].astype(float)

    # Data e hora
    perfis_eredes['Data'] = perfis_eredes['Data'].str.replace("\.\/", "/", regex=True)
    # Converter data e hora as 24:00 para data + 1 dia e hora 00:00
    perfis_eredes['Timestamp'] = perfis_eredes[['Data', 'Hora']].apply(converter_timestamp_hora_24_para_hora_00, axis=1)
    perfis_eredes['Timestamp'] = pd.to_datetime(perfis_eredes['Timestamp'], format="%d/%b/%Y %H:%M")
    # Ultimo dia do ano passa o dia seguinte, retirar 1 ano
    perfis_eredes.loc[perfis_eredes.index[-1], 'Timestamp'] = perfis_eredes.loc[perfis_eredes.index[-1], 'Timestamp'] - relativedelta(years=1)

    perfis_eredes = perfis_eredes.set_index('Timestamp')
    perfis_eredes = perfis_eredes.sort_index()
    return perfis_eredes[perfil].to_frame(perfil)

def converter_timestamp_hora_24_para_hora_00(x):
    """ Converte um time stamp com formato dd/mmm/yyyy 24:00 para dd+1/mmm/yyyy 00:00

    Args:
    -----
    x: pandas.DataFrame
        Dataframe com coluna 'Data' 

    Returns:
    --------
    timestamp: str
        timestamp convertido
    """
    data = datetime.datetime.strptime(x['Data'], '%d/%b/%Y').date() # pd.to_datetime(x['Data'],'%d/%b/%Y')
    hora_str = x['Hora']
    if hora_str[0:2] == '24':
        hora_str = '00' + hora_str[2:]
        data += datetime.timedelta(days=1)

    return '{} {}'.format(data.strftime('%d/%b/%Y'), hora_str)

def ajustar_perfil_eredes_a_consumo_anual(perfis_eredes, consumo_anual_kwh, col, nome_col_consumo='Estimativa Consumo'):
    """ Ajustar o perfil e-redes a um valor de consumo anual.

    ..math:`Perfil_{Ajustado} = \\frac{Perfil_{E-Redes}*Consumo_{Anual}}{1000}`

    Args:
    -----
    perfis_eredes: pandas.DataFrame
        Perfil e-redes 15 min
    consumo_anual_kwh : float
        Consumo anual em kwh
    col: str
        Nome coluna do perfil
    nome_col_consumo: str, default: 'Estimativa Consumo'
        Nome coluna com consumo na resultado. Por defeiro é 'Estimativa Consumo'.

    Returns:
    -------
    perfil_consumo: pandas.DataFrame
        Dataframe com perfil horario ajustado na coluna indicada.
    """
    perfil_consumo = (perfis_eredes[col] * consumo_anual_kwh) / 1000
    #resample hourly
    perfil_consumo = perfil_consumo.resample('H').sum()
    return perfil_consumo.to_frame(nome_col_consumo)

def ajustar_perfil_eredes_a_consumo_mensal(perfis_eredes, col_perfis, consumo_mensal, col_consumo, nome_col_consumo='Estimativa Consumo'):
    """ Ajustar o perfil e-redes a um valor de consumo mensal
    
    ..math:`Perfil_{Ajustado} = \\frac{Perfil_{E-Redes}^{Mes} * Consumo_{Mes}}{\\sum Perfil_{E-Redes}^{Mes}}`

    Args:
    ----
    perfis_eredes: pandas.DataFrame
        Dataframe com perfil e-redes 15 min
    col_perfis: str
        Nome coluna do perfil a utilizar
    consumo_mensal: pandas.DataFrame
        Dataframe com indice mes e consumo em kwh respectivo para o ano em analise
    col_consumo: str
        Nome columa do consumo_mensal a utilizar
    nome_col_consumo: str, default: 'Estimativa Consumo'
        Nome coluna com consumo na resultado. Por defeiro é 'Estimativa Consumo'.        

    Returns:
    -------
    perfil: pandas.DataFrame
        Dataframe com perfil horario ajustado na coluna indicada.
    """
    # converter para horario
    perfil = perfis_eredes[col_perfis].resample('H').sum().to_frame(col_perfis)
    #perfil = perfis_eredes[col].to_frame(col)

    # soma mensal do perfil e-redes
    soma_mensal = perfil.resample('M').sum()
    soma_mensal = soma_mensal.rename(columns={col_perfis:'soma mensal'})
    soma_mensal['mes'] = soma_mensal.index.month
    soma_mensal = soma_mensal.set_index('mes')
    
    # bin por mes
    perfil['mes'] = pd.cut(perfil.index.month, soma_mensal.index.union([13]), labels=soma_mensal.index, right=False)
    perfil['mes'] = perfil['mes'].astype(int)

    perfil[nome_col_consumo] = perfil[col_perfis] * perfil['mes'].map(consumo_mensal[col_consumo]) / perfil['mes'].map(soma_mensal['soma mensal'])
    perfil = perfil.drop(['mes'], axis=1, errors='ignore')
    return perfil

def leitura_consumo_faturas(ficheiro, ano):
    """ Leitura valores faturas e calcular consumo mensal.

    Ler ficheiro tsv com valores Vazio, Cheias e Ponta e calcular valor de consumo mensal. Interpolar valor de
    consumo no ultimo dia do mes. Requer uma leitura no 1o dia do ano e uma no último ou após o mesmo

    Args:
    -----
    ficheiro: str
        Caminho para o ficheiro tsv com leituras
    ano: int
        Ano a processar

    Returns:
    --------
    consumos: pandas.DataFrame
        Dataframe com indice numero mes e coluna consumo com consumo nesse mes
    """
    leituras = pd.read_csv(ficheiro, sep='\t')
    leituras['Data'] = pd.to_datetime(leituras['Data'], format='%d/%m/%Y')
    leituras = leituras.set_index('Data')

    #filtrar ficheiro para o ano
    dia1_ano = datetime.datetime(ano, 1, 1)
    leituras = leituras[leituras.index >= dia1_ano]
    # garantir que temos o 1o dia do ano
    assert leituras.index.min().date() == dia1_ano.date(), "Leituras nao contem o 1o dia do ano: {}".format(dia1_ano.date())

    leituras['acumulado'] = leituras['Vazio'] + leituras['Cheias'] + leituras['Ponta']
    
    # lista de dias do ultimo dia do mes onde interpolar
    ultimo_dia_ano = dia1_ano + relativedelta(years=1) - relativedelta(days=1)
    fim_mes = pd.date_range(start=dia1_ano, end=ultimo_dia_ano, freq='M')
    leituras = leituras.reindex(leituras.index.union(fim_mes), fill_value=np.nan)
    leituras['acumulado'] = leituras['acumulado'].interpolate()
    
    # calcular consumo mensal, 
    consumos = leituras.loc[fim_mes.union(pd.DatetimeIndex([dia1_ano])),'acumulado'].to_frame('acumulado')
    consumos['consumo'] = consumos['acumulado'].diff()

    # limpar 1a linha com 1 dia do ano, colunas e indice no # mes
    consumos = consumos.iloc[1:]
    consumos = consumos.drop('acumulado', axis=1)
    consumos.index = consumos.index.month
    
    return consumos

def leitura_ficheiros_mensais_medicao_eredes(pasta, ano, col_consumo="Dados de Consumo kW", col_producao = "Dados de Producao kW", 
                                             resample_horario=True, worksheet="Leituras"):
    """ Leitura de ficheiros excel mensais de uma pasta no formato <mes>_<ano>.xlsx com os dados
    medidos de consumo obtidos do balcao digita e-redes.

    Args:
    -----
    pasta: str
        Caminho para a pasta onde estao os ficheiros
    ano: int
        Ano para o qual ler os ficheiros
    col_consumo : str, default: "Dados de Consumo kW"
        Nome da coluna com dados de consumo. Tem de existir no ficheiro.
    col_producao : str, default: "Dados de Producao kW"
        Nome da coluna com dados de produção. Pode não existir.
    resample_horario : bool, default: True
        Se queremos fazer resample dos dados para horario depois da conversão para energia. Utilizada soma. Defaul
    worksheet: str
        Nome da folha excel a ler, tem de ser o mesmo em todos os ficheiros

    Returns:
    df: pandas.DataFrame
        Dataframe com coluna 'consumo' com dados em kwh e 'producao' em kwh se estiver disponivel
    """
    #col_consumo = "Dados de Consumo kW"
    #col_producao = "Dados de Producao kW"
    list_of_files = sorted( glob.iglob(os.path.join(pasta, '*{}*'.format(ano))))
    li = []
    for fich in list_of_files:
        df = pd.read_excel(fich, worksheet, skiprows=8)
        li.append(df)

    df = pd.concat(li, axis=0, ignore_index=True)
    df["Timestamp"] = df["Data"] + " " + df["Hora"]
    df["Timestamp"] = pd.to_datetime(df["Timestamp"])
    df = df.set_index("Timestamp")
    df = df.drop("Data", axis=1)
    df = df.drop("Hora", axis=1)
    # renomear colunas
    df = df.rename(columns={col_consumo:'consumo'})
    if col_producao in df.columns:
        df = df.rename(columns={col_producao:'producao'})

    # converter para kwh
    df['consumo'] = df['consumo']*15/60

    if (resample_horario):
        # resample para horario
        df = df.resample('H').sum()
    return df

    