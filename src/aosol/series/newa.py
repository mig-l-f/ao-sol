"""

Get, read, and parse data from `NEWA <https://wps.neweuropeanwindatlas.eu/api/mesoscale-ts/v1/docs#/>`.

"""
import pandas as pd
import netCDF4
from datetime import datetime
import requests
import os
import tempfile

BASE_URL = 'https://wps.neweuropeanwindatlas.eu/api/mesoscale-ts/v1'

def get_newa_single_location_at_10m(latitude, longitude, dt_start=None, dt_end=None):
    """ Obter serie temporal com frequência de 30 min da NEWA para uma única localização 
    e variáveis WS10 e WD10.

    Dados NEWA disponiveis gratuitamente em [1]_. Documentação da API disponivel em [2]_.

    Parameters
    ----------
    latitude: float
        Em graus decimais no intervalo [31.807278, 72.17796]
    longitude: float
        Em graus decimais no intervalo [-19.420776, 46.992065]
    dt_start: datetime, default: None
        Datetime de inicio do periodo, no intervalo [2005-01-01T00:00:00, 2018-12-31T23:30:00]. Por defeito é tomado o inicio do período.
    dt_end: datetime, default: None
        Datetime de fim do período, no intervalo [2005-01-01T00:00:00, 2018-12-31T23:30:00]. Por defeiro é tomado o fim do período.

    Returns
    -------
    df: pandas.DataFrame
        Serie temporal de WS10 e WD10 para o periodo.
    lat: float
        Em graus decimais do ponto que foi descarregado, ponto mais proximo ao pedido.
    lon: float
        Em graus decimais do ponto que foi descarregado, ponto mais proximo ao pedido.

    References
    ----------
    .. [1] `NEWA <https://map.neweuropeanwindatlas.eu/>`_
    .. [2] `NEWA API docs <https://wps.neweuropeanwindatlas.eu/api/mesoscale-ts/v1/docs/>`_
    """
    if not dt_start:
        dt_start = datetime(2005, 1, 1, 0, 0, 0)
    if not dt_end:
        dt_end = datetime(2018, 12, 31, 23, 30, 0)
    
    params = [
            ('latitude', latitude),
            ('longitude', longitude),
            ('dt_start', dt_start),
            ('dt_stop', dt_end),
            ('variable', 'WS10'),
            ('variable', 'WD10')
        ]
    #variables = ['WS10', 'WD10']
    #for var in variables:
    #    params.append(
    #        ('variable', var)
    #    )
    fich_nc = _call_newa_api(params)
    df, lon, lat = _parse_newa_nc_file(fich_nc)
    os.remove(fich_nc)

    return df, lon, lat

def _call_newa_api(params, timeout=60):
    """ Chama API NEWA e cria ficheiro netcdf.

    Parameters
    ----------
    params: list of pairs
        List of pairs with API call parameters.

    Returns
    -------
    fich_nc: str
        Ficheiro netcdf em pasta temporária
    """
    res = requests.get(BASE_URL + '/get-data-point', params=params, timeout=60)
    if not res.ok:
        try:
            err_msg = res.json()
        except Exception:
            res.raise_for_status()
        else:
            raise requests.HTTPError(err_msg['message'])
        
    content_disposition = res.headers.get('Content-Disposition')
    if content_disposition:
        # Extract the filename from 'Content-Disposition' header if available
        if 'filename=' in content_disposition:
            filename = content_disposition.split('filename=')[1].strip('"')
        else:
            # Fallback if the filename is not provided in the header
            filename = 'downloaded_attachment'
    else:
        print('NEWA API: header content-disposition nao esta presente.')
        filename = 'downloaded_attachment'

    print(f'NEWA API: descarregar para ficheiro: {filename}')
    # Save the file locally
    fich_nc = os.path.join(tempfile.gettempdir(), filename)
    with open(fich_nc, 'wb') as f:
        # Write the response content in chunks to avoid memory issues for large files
        for chunk in res.iter_content(chunk_size=8192):
            if chunk:  # Filter out keep-alive chunks
                f.write(chunk)

    return fich_nc

def _parse_newa_nc_file(fich_nc):
    """ Le ficheiro netcdf (nc) da NEWA. Deve apenas conter 1 ponto.

    Parameters
    ----
    fich_nc: str
        Caminho para ficheiro netcdf

    Returns
    -------
    df: pandas.DataFrame
        Dataframe com dados newa para o ponto pedido.
        'ws10' com velocidade horizontal vento aos 10m
        'wd10' com direcção do vento aos 10m
    lat: float
        latitude do ponto retornado
    lon: float
        longitude do ponto retornado
    """
    with netCDF4.Dataset(fich_nc, 'r') as dataset: # 'r' significa abrir o arquivo em modo de leitura
        if 'time' not in dataset.variables or 'WS10' not in dataset.variables or 'WD10' not in dataset.variables:
            raise Exception('Erro: NETCDF variaveis time e/ou WS10 e/ou WD10 não constam do ficheiro.') 
        time = dataset.variables['time'][:]
        ws10 = dataset.variables['WS10'][:]
        wd10 = dataset.variables['WD10'][:]
        data_referencia = '1989-01-01'
        timestamps = pd.to_datetime(data_referencia) + pd.to_timedelta(time, unit='min')

        if 'XLON' not in dataset.variables or 'XLAT' not in dataset.variables:
            print('WARN: XLON e/ou XLAT nao existem. Valores lat e lon = 0.0')
            lon = 0.0
            lat = 0.0
        else:
            xlon = dataset.variables['XLON']
            if xlon.shape == ():
                lon = xlon.getValue()
            else:
                print('WARN: longitude nao e escalar. valor de 0.0')
                lon = 0.0
            
            xlat = dataset.variables['XLAT']
            if xlat.shape == ():
                lat = xlat.getValue()
            else:
                print('WARN: latitude nao e escalar. valor de 0.0')
                lat = 0.0

    df = pd.DataFrame({
            'time': timestamps,
            'ws10': ws10,
            'wd10': wd10
        })
    df = df.set_index('time')
    return df, lat, lon
