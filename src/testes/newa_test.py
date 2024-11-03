from datetime import datetime
import unittest
from ..aosol.series import newa
import pandas as pd
import netCDF4
import os
import requests
import tempfile

class TestNewa(unittest.TestCase):
    
    def test_parse_newa_file_to_dataframe(self):
        arquivo = os.path.join(os.getcwd(),"aosol_project", "src", "testes", "mesoscale-ts.nc")

        df, lon, lat = newa._parse_newa_nc_file(arquivo)

        self.assertEqual(datetime(2018, 12, 1, 0, 0, 0), df.index[0])
        self.assertEqual(datetime(2018, 12, 31, 23, 30, 0), df.index[-1])
        self.assertAlmostEqual(1.9882, df['ws10'].iloc[0], 3)
        self.assertAlmostEqual(113.9194, df['wd10'].iloc[0], 3)
        self.assertAlmostEqual(4.2011, df['ws10'].iloc[-1], 3)
        self.assertAlmostEqual(106.5856, df['wd10'].iloc[-1], 3)
    # 2018-12-01 00:00:00  1.988205  113.919434
    # 2018-12-31 23:30:00  4.201182  106.585876
    # 1488        

    def test_call_newa_api(self):
        params = [
            ('latitude', 38.8938),
            ('longitude', -9.355455),
            ('dt_start', datetime(2018, 12, 1, 0, 0, 0)),
            ('dt_stop', datetime(2018, 12, 31, 23, 30, 0)),
            ('variable', 'WS10'),
            ('variable', 'WD10')
        ]

        fich_nc = newa._call_newa_api(params)        
        print(f'fich_nc: {fich_nc}')

        self.assertTrue(os.path.isfile(fich_nc))
        os.remove(fich_nc)

    @unittest.skip
    def test_list_nc_file(self):        
        arquivo = os.path.join(os.getcwd(),"aosol_project", "src", "testes", "mesoscale-ts.nc")
        dataset = netCDF4.Dataset(arquivo, 'r')  # 'r' significa abrir o arquivo em modo de leitura

        # Liste as variáveis no ficheiro
        for var_name in dataset.variables.keys():
            var = dataset.variables[var_name]
            print(f"Variável: {var_name}")
            print(f"Dimensões: {var.dimensions}")
            print(f"Tamanho das dimensões: {var.shape}")
            print()  # Linha em branco para separação entre variáveis

        dataset.close()

    @unittest.skip
    def test_valores_escalares(self):
        arquivo = os.path.join(os.getcwd(),"aosol_project", "src", "testes", "mesoscale-ts.nc")
        dataset = netCDF4.Dataset(arquivo, 'r')  # 'r' significa abrir o arquivo em modo de leitura

        scalar = ["XLAT", "XLON", "south_north", "west_east", "time"]
        for s in scalar:
            if s in dataset.variables:
                var = dataset.variables[s]     
                if var.shape == ():           
                    valor_escalar = var.getValue()
                    print(f'{s} = {valor_escalar}')
                else:
                    print(f'var {s} nao e escalar')
            else:
                print(f'Nao encontrou {s}')

        dataset.close()

    @unittest.skip
    def test_vars_dataframe(self):
        arquivo = os.path.join(os.getcwd(),"aosol_project", "src", "testes", "mesoscale-ts.nc")
        dataset = netCDF4.Dataset(arquivo, 'r')  # 'r' significa abrir o arquivo em modo de leitura
        time = dataset.variables['time'][:]
        ws10 = dataset.variables['WS10'][:]
        wd10 = dataset.variables['WD10'][:]
        data_referencia = '1989-01-01'
        timestamps = pd.to_datetime(data_referencia) + pd.to_timedelta(time, unit='min')
        dataset.close()

        df = pd.DataFrame({
            'time': timestamps,
            'ws10': ws10,
            'wd10': wd10
        })
        print(df.head())
        print(df.tail())

    @unittest.skip
    def test_atributos_netcdf(self):
        arquivo = os.path.join(os.getcwd(),"aosol_project", "src", "testes", "mesoscale-ts.nc")
        dataset = netCDF4.Dataset(arquivo, 'r')  # 'r' significa abrir o arquivo em modo de leitura
        for atributo in dataset.ncattrs():
            print(f"{atributo}: {dataset.getncattr(atributo)}")
        #lat = dataset.getncattr('southBoundLatitude')
        #lon = dataset.getncattr('westBoundLongitude')
        #print(f"Lat: {lat} Lon: {lon}")

        nome_variavel = 'time'
        if nome_variavel in dataset.variables:
            var = dataset.variables[nome_variavel]
            print(f"Atributos da variável '{nome_variavel}':")
            for atributo in var.ncattrs():
                print(f"{atributo}: {var.getncattr(atributo)}")

        dataset.close()

    @unittest.skip
    def test_request_newa_dataset(self):
        url = 'https://wps.neweuropeanwindatlas.eu/api/mesoscale-ts/v1/get-data-point'
        latitude = 38.8938
        longitude = -9.355455
        variables = ['WS10', 'WD10']
        dt_start = datetime(2018, 12, 1, 0, 0, 0)
        dt_end = datetime(2018, 12, 31, 23, 30, 0)

        params = [
            ('latitude', latitude),
            ('longitude', longitude),
            ('dt_start', dt_start),
            ('dt_stop', dt_end)
        ]
        for var in variables:
            params.append(
                ('variable', var)
            )

        #print(params)
        res = requests.get(url, params=params, timeout=60)
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

            print(filename)
            # Save the file locally
            current_directory = os.path.dirname(os.path.abspath(__file__))
            with open(os.path.join(current_directory, filename), 'wb') as f:
                # Write the response content in chunks to avoid memory issues for large files
                for chunk in res.iter_content(chunk_size=8192):
                    if chunk:  # Filter out keep-alive chunks
                        f.write(chunk)
        else:
            print('no content-disposition')


