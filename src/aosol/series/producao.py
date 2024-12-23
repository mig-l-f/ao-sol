""" Contem metodos para processar dados de producao
"""
import pandas as pd
import calendar

mapa_colunas_pvgis = { 
    'P': 'autoproducao', 
    'temp_air': 'temperatura'
}

def converter_pvgis_data(pvgis_tuple, ano, inclui_temp=False):
    """ Converte um tuplo do pvgis para uma dataframe de autoproduco. 
    Isola o sinal de potencia, converte para kW e translada o ano para o ano pedido.

    Args:
    -----
    pvgis_tuple: tuple
        Tuple obtido dos metodos pvgis
    ano: int
        Ano para o qual queremos converter os timestamps
    inclui_temp: bool, default:False
        Se conversão deve incluir o sinal de temperatura.
        
    Returns:
    --------
    df: pandas.DataFrame
        Dataframe com coluna 'autoproducao' em kW, e 'temperatura' em graus C se inclui_temp é True.
    """
    # obter coluna de interesse, converter para kw
    df = pvgis_tuple[0]['P'].to_frame('autoproducao') / 1000.0
    if inclui_temp:
        df[mapa_colunas_pvgis['temp_air']] = pvgis_tuple[0]['temp_air']

    # converter anos
    ultimo_ano = df.index[-1].year
    diff_anos = ano - ultimo_ano
    df.index = df.index  + pd.DateOffset(years=diff_anos) #- pd.DateOffset(minutes=10)

    # converter offset minutos
    offset_minutos = df.index[-1].minute
    df.index = df.index - pd.DateOffset(minutes=offset_minutos)

    return df

def converter_pvgis_multiyear_ts(pvgis_tuple, ano, inclui_temp=False):
    """ Converter um tuplo pvgis com varios anos de dados calculando a potência média (P50) e P90
    Assume que serie temporal tem valores horários. Isola os sinais de potência, converte para kW e translada para o ano pedido.

    Fonte: https://solargis.com/resources/blog/best-practices/how-to-calculate-p90-or-other-pxx-pv-energy-yield-estimates
    
    Args:
    -----
    pvgis_tuple: tuple
        Tuple com mais de 1 ano de dados obtido dos métodos pvgis
    ano: int
        Ano para qual queremos os timestamps finais.
    inclui_temp: bool, default:False
        Se conversão deve incluir o sinal de temperatura.

    Returns:
    --------
    df: pandas.DataFrame
        Dataframe com colunas:
          'autoproducao' em kW com média (P50) em cada registo
          'autoproducao_p90' em kW com P90 em cada registo
        caso inclui_temp então contêm também:
          'temperatura' em ºC com média (P50) em cada registo.
          'temperatura' em ºC ccom P90 em cada registo
    """
    # obter coluna de interesse, converter para kw
    df = pvgis_tuple[0]['P'].to_frame('autoproducao') / 1000.0
    if inclui_temp:
        df[mapa_colunas_pvgis['temp_air']] = pvgis_tuple[0]['temp_air']

    # retirar offset minutos e por inicio hora
    offset_minutos = df.index[-1].minute
    df.index = df.index - pd.DateOffset(minutes=offset_minutos)

    # groupby mes-dia hora
    df = df.groupby('{:%m-%d %H}'.format).agg(['mean', 'std'])
    # calcular P90 = P50 - P90 incerteza
    #  P90 incerteza = 1.282 * std
    df[('autoproducao','p90')] = df[('autoproducao','mean')] - 1.282*df[('autoproducao','std')]
    if inclui_temp:
        df[('temperatura','p90')] = df[('temperatura','mean')] - 1.282*df[('temperatura','std')]

    # renomear colunas
    df.columns = list(map('_'.join, df.columns.values))
    df.rename(columns={'autoproducao_mean':'autoproducao'}, inplace=True)        
    # drop std
    df.drop(['autoproducao_std'], axis=1, inplace=True)

    if inclui_temp:
        df.rename(columns={'temperatura_mean':'temperatura'}, inplace=True)
        df.drop(['temperatura_std'], axis=1, inplace=True)

    # verificar se existe 29 Fev
    df['mes'] = df.index.str[0:2]
    df['dia'] = df.index.str[3:5]
    df['hora'] = df.index.str[6:8]
    has_29fev = ('02' in df['mes'].values) and ('29' in df['dia'].values)
    
    if has_29fev and (not calendar.isleap(ano)):
        # remove dia 29 se ano alvo não é bisexto
        df['a_remover'] = df['mes'].isin(['02']) & df['dia'].isin(['29'])
        df = df[df['a_remover'] == False]
        df.drop(['a_remover'], axis=1, inplace=True)

    # converte index para formato %Y-%m-%d %H:%M
    df.index = pd.to_datetime(str(ano) + '-' + df['mes'] + '-' + df['dia'] + ' ' + df['hora'] + ':00', format='%Y-%m-%d %H:%M')

    df.drop(['mes', 'dia', 'hora'], axis=1, inplace=True)
    return df
