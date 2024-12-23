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
import numpy as np

class indicadores_bomba_calor:
    """ Indicadores desempenho da bomba de calor.
    """
    def __init__(self, scop, e_term_bc, e_elec_usada_bc, e_elec_resist, e_perd_dep, frac_backup, n_horas_abaixo_min, n_dias):
        self._scop = scop
        self._e_term_bc = e_term_bc
        self._e_elec_bc = e_elec_usada_bc
        self._e_elec_resist = e_elec_resist
        self._e_perd_dep = e_perd_dep
        self._frac_backup = frac_backup
        self._n_horas_min = n_horas_abaixo_min
        self._n_dias = n_dias

    @property
    def scop(self):
        """ Factor de performance sazonal (SCOP/SPF). [-]
        """
        return self._scop
    
    @property
    def energia_term_bc(self):
        """ Total energia térmica produzida pela BC. [kWh]
        """
        return self._e_term_bc

    @property
    def energia_term_bc_p_dia(self):
        """ Energia térmica produzida pela BC por dia. [kWh/dia]
        """
        return self._e_term_bc / self._n_dias
    
    @property
    def energia_elec_bc(self):
        """ Total energia electrica consumida pela BC. [kWh]
        """
        return self._e_elec_bc
    
    @property
    def energia_elec_bc_p_dia(self):
        """ Energia electrica consumida pela BC por dia. [kWh/dia]
        """
        return self._e_elec_bc / self._n_dias

    @property
    def energia_elec_resist(self):
        """ Total energia electrica consumida pela resistência. [kWh]
        """
        return self._e_elec_resist
    
    @property
    def energia_elec_resist_p_dia(self):
        """ Energia electrica consumida pela resistência por dia. [kWh/dia]
        """
        return self._e_elec_resist / self._n_dias

    @property
    def energia_perd_dep(self):
        """ Total energia perdida pelo depósito para o ambiente. [kWh]
        """
        return self._e_perd_dep

    @property
    def energia_perd_dep_p_dia(self):
        """ Energia perdida depósito para o ambiente por dia. [kWh/dia]
        """
        return self._e_perd_dep / self._n_dias

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
    
    @property
    def n_dias(self):
        """ Numero de dias na análise.
        """
        return self._n_dias

    def to_frame(self, nome):
        """ Retorna indicadores numa dataframe.

        Parameters
        ----------
        nome : str
            Nome/identificado da análise.
        """
        stats = pd.DataFrame({
            "quant": ["Energia termica BC [kWh]", "Consumo electrico BC [kWh]", "Consumo electrico Resistencia [kWh]", "Perda ambient depósito [kWH]", "SCOP [-]", "Fraccao resistencia [-]", "Num horas abaixo temperatura min [-]"],
            nome: [self.energia_term_bc, self.energia_elec_bc, self.energia_elec_resist, self.energia_perd_dep, self.scop, self.frac_backup, self.n_horas_min],
            f"{nome} [p/dia]": [self.energia_term_bc_p_dia, self.energia_elec_bc_p_dia, self.energia_elec_resist_p_dia, self.energia_perd_dep_p_dia, None, None, None]
        })
        stats = stats.set_index("quant")
        return stats