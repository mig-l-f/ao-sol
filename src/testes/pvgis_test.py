from datetime import datetime
import unittest
from aosol.series import pvgis
import pandas as pd

class TestPVGIS(unittest.TestCase):
    # Opcoes API PVGIS
    inicio_ano_pvgis = 2020
    fim_ano_pvgis = 2020 # PVGIS-SARAH2 na V5.2 (2005-2020)
    lat = 38.716
    lon = -9.148
    perdas = 14 # %

    def test_get_pvgis_hourly_data_db_sarah3(self):
        db = "PVGIS-SARAH3"
        self.inicio_ano_pvgis = 2023
        self.fim_ano_pvgis = 2023

        producao, inputs, metadata = pvgis.get_pvgis_hourly(self.lat, self.lon, self.inicio_ano_pvgis, self.fim_ano_pvgis, raddatabase=db, surface_tilt=30, surface_azimuth=0, peakpower=0.6, loss=self.perdas)

        self.assertEqual(8760, len(producao))
        self.assertEqual(datetime(2023, 1, 1, 00, 10, 00), producao.index[0])
        self.assertEqual(datetime(2023, 12, 31, 23, 10, 00), producao.index[-1])

        self.assertEqual('PVGIS-SARAH3', inputs["meteo_data"]["radiation_db"])
        self.assertEqual(2023, inputs["meteo_data"]["year_min"])
        self.assertEqual(2023, inputs["meteo_data"]["year_max"])
        

    def test_get_pvgis_hourly_data_db_era5(self):
        db = "PVGIS-ERA5"
        self.inicio_ano_pvgis = 2023
        self.fim_ano_pvgis = 2023

        producao, inputs, metadata = pvgis.get_pvgis_hourly(self.lat, self.lon, self.inicio_ano_pvgis, self.fim_ano_pvgis, raddatabase=db, surface_tilt=30, surface_azimuth=0, peakpower=0.6, loss=self.perdas)

        self.assertEqual(8760, len(producao))
        self.assertEqual(datetime(2023, 1, 1, 00, 30, 00), producao.index[0])
        self.assertEqual(datetime(2023, 12, 31, 23, 30, 00), producao.index[-1])

        self.assertEqual('PVGIS-ERA5', inputs["meteo_data"]["radiation_db"])
        self.assertEqual(2023, inputs["meteo_data"]["year_min"])
        self.assertEqual(2023, inputs["meteo_data"]["year_max"])