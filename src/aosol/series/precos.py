""" Funcoes para processamento de series temporais de precos.
"""
import pandas as pd

def ler_serie_omie_tfelicia(fich, coluna_preco='Portugal', unidades='€/MWh'):
    """ Ler serie temporal de preços da OMIE com registos de 15 em 15 minutos de ficheiro csv. 
    Obtidos no sites do Tiago Felícia, disponiveis em https://www.tiagofelicia.pt/omie.html.
    Se unidades são '€/MWh', os preços são convertidos para €/kWh.

    Args:
    -----
    fich: str
        Caminho para o ficheiro csv a ler.
    coluna_preco: str, default:'Portugal'
        Nome da coluna do ficheiro csv onde estão os preços.
    unidades: str, default:'€/MWh'
        Unidades dos preços no ficheiro csv. Se '€/MWh', os preços são convertidos para €/kWh.

    Returns:
    --------
    df: pandas.DataFrame
        Dataframe com coluna 'preco' em €/kWh e index de timestamps.
    """
    df = pd.read_csv(fich, sep=';', decimal=',', parse_dates=[0], dayfirst=True)

    # normalizar nomes e converter para €/kWh (÷1000)
    df = df.rename(columns={"Data e Hora (PT)": "datetime", "Portugal": "omie"})
    df.set_index('datetime', inplace=True)
    if unidades == '€/MWh':
        df["omie"] = df["omie"] / 1000.0
    return df