""" Contem metodos para processar dados de producao
"""
import pandas as pd

def converter_pvgis_data(pvgis_tuple, ano):
    """ Converte um tuplo do pvgis para uma dataframe de autoproduco. 
    Isola o sinal de potencia, converte para kW e translada o ano para o ano pedido.

    Args:
    -----
    pvgis_tuple: tuple
        Tuple obtido dos metodos pvgis
    ano: int
        Ano para o qual queremos converter os timestamps

    Returns:
    --------
    df: pandas.DataFrame
        Dataframe com coluna 'autoproducao' em kW
    """
    # obter coluna de interesse, converter para kw
    df = pvgis_tuple[0]['P'].to_frame('autoproducao') / 1000.0

    # converter anos
    ultimo_ano = df.index[-1].year
    diff_anos = ano - ultimo_ano
    df.index = df.index  + pd.DateOffset(years=diff_anos) #- pd.DateOffset(minutes=10)

    # converter offset minutos
    offset_minutos = df.index[-1].minute
    df.index = df.index - pd.DateOffset(minutes=offset_minutos)

    return df