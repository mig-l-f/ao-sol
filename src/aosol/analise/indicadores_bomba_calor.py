""" Indicadores Bomba Calor

======================== ======== ===========
Indicadores              Unidade  Descrição
======================== ======== ===========
SCOP/SPF                 -        Factor de desempenho sazonal.
:math:`E_{TOT,USADA,BC}` kWh      Energia eléctrica consumida pela Bomba Calor.
:math:`E_{TOT,RESIST}`   kWh      Energia consumida pela resistência
Frac_backup :math:`\phi` -        Fracção da energia térmica que foi fornecida pela resistência.
N horas minimo           h        Número de horas em que a temperatura do depósito está abaixo do mínimo.
======================== ======== ===========
"""

import pandas as pd

class indicadores_bomba_calor:
    """ Indicadores desempenho da bomba de calor.
    """
    def __init__(self, scop, e_term_bc, e_elec_usada_bc, e_elec_resist, frac_backup, n_horas_abaixo_min):
        self._scop = scop
        self._e_term_bc = e_term_bc
        self._e_elec_bc = e_elec_usada_bc
        self._e_elec_resist = e_elec_resist
        self._frac_backup = frac_backup
        self._n_horas_min = n_horas_abaixo_min

    @property
    def scop(self):
        """ Factor de performance sazonal (SCOP/SPF). [-]
        """
        return self._scop
    
    @property
    def energia_term_bc(self):
        """ Energia térmica produzida pela BC. [kWh]
        """
        return self._e_term_bc

    @property
    def energia_elec_bc(self):
        """ Energia electrica consumida pela BC. [kWh]
        """
        return self._e_elec_bc
    
    @property
    def energia_elec_resist(self):
        """ Energia electrica consumida pela resistência. [kWh]
        """
        return self._e_elec_resist
    
    @property
    def frac_backup(self):
        """ Fracção da energia térmica fornecida pela resistência. [-]
        """
        return self._frac_backup
    
    @property
    def n_horas_min(self):
        """ Numero de horas que temperatura está abaixo do mínimo. [h]
        """
        return self._n_horas_min
    
    def to_frame(self, nome):
        """ Retorna indicadores numa dataframe.

        Parameters
        ----------
        nome : str
            Nome/identificado da análise.
        """
        stats = pd.DataFrame({
            "quant": ["e_term_bc [kWh]", "e_elec_bc [kWh]", "e_elec_resist [kWh]", "scop [-]", "frac_resist [-]", "n horas < t_min_s [-]"],
            nome: [self._e_term_bc, self._e_elec_bc, self._e_elec_resist, self._scop, self._frac_backup, self._n_horas_min]
        })
        stats = stats.set_index("quant")
        return stats