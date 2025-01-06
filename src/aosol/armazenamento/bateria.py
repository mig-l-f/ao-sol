import numpy as np

class bateria:
    """ Funcionamento de bateria
    """

    def __init__(self, capacidade, soc_min_perc, soc_max_perc, ef_bat=1, pot_maxima=1E15):
        """ Bateria.

        Parameters
        ----------
        capacidade : float
            Capacidade total da bateria. [kWh]
        soc_min_perc : float
            Estado de carga minima da capacidade. Valor entre 0 e 1. 
        soc_max_perc : float
            Estado de carga máxima da capacidade. Valor entre 0 e 1.
        ef_bat : float, default: 1
            Eficiência carga e descarga (roundtrip) da bateria. Valor entre 0 e 1.
        pot_maxima : float, default: 1E15
            Potencia instânea máxima de carga/descarga que a bateria suporta. [kW]
            Por defeito considera que pode ser carregada/descarregada qualquer potencia.
        """
        self._capacidade_total = capacidade
        self._soc_min = soc_min_perc
        self._soc_max = soc_max_perc
        self._ef_bat = ef_bat
        self._pot_maxima = pot_maxima

    @property
    def capacidade_total(self):
        """ Capacidade total da bateria. [kWh]
        """
        return self._capacidade_total
    
    @property
    def profundidade_descarga(self):
        """ Profundidade de descarga da bateria. [kWh]
        """
        return (self._soc_max - self._soc_min)*self.capacidade_total
    
    @property    
    def ef_bat(self):
        """ Eficiencia da bateria.
        """
        return self._ef_bat
    
    @property
    def potencia_maxima(self):
        """ Potencia maxima de carga/descarga. [kW]
        """
        return self._pot_maxima

    def calcula_energia_maximiza_autoconsumo(self, soc_anterior, demanda_dc, intervalo):
        """ Calcula comportamento da bateria no intervalo para maximizar auto consumo.

        Parameters
        ----------
        soc_anterior : float
            Estado de carga no inicio do intervalo. [kWh]
        demanda_dc : float
            Potencia necessária do lado DC (já com eficiencia do inversor). [kW]
            Se >0 produção pv não cobre a carga.
            Se <0 produção pv excede a carga.
        intervalo : float
            Duração do intervalo. [h]

        Returns
        -------
        soc : float
            Estado de carga no final do intervalo. [kWh]
        pot_carga : float
            Potencia de carregamento da bateria. [kW]
        pot_descarga : float
            Potencia de descarregamento da bateria. [kW]
        """
        max_descarga = np.minimum(self.potencia_maxima, soc_anterior*self.ef_bat/intervalo)
        max_carga = np.minimum(self.potencia_maxima, (self.profundidade_descarga - soc_anterior)/intervalo)

        pot_descarga = np.minimum(max_descarga, np.maximum(0, demanda_dc))
        pot_carga = np.minimum(max_carga, np.maximum(0, -demanda_dc))
        soc = soc_anterior + pot_carga*intervalo - pot_descarga/self.ef_bat*intervalo

        return soc, pot_carga, pot_descarga