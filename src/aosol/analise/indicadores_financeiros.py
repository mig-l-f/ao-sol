""" Indicadores financeiros de um projecto.

Indicadores financeiros cálculos para um projecto, calculados para determinado
tempo de vida, custo inicial (capex) e custo de operação (opex) de um projecto:

====================== ======== ===========
Indicadores            Unidade  Descrição
====================== ======== ===========
VAL                    €        Valor actual líquido. [1]_
TIR                    %        Taxa interna de rentabilidade. [1]_, [2]_
tempo_retorno          anos     Tempo de retorno ou ROI. [1]_
LCOE                   €/kWh    Custo da energia produzida. [3]_
====================== ======== ===========

Os métodos de cálculo foram obtidos a partir das seguintes referências:

.. [1] Bloco 9 - Análise Investimentos, Universidade Evora. 
    Em https://dspace.uevora.pt/rdpc/bitstream/10174/6309/11/BLOCO9.pdf
.. [2] F Militão, J Alberto. "O Método de Newton-Raphson no Cálculo do TIR", 
    UNOPAR Cient. Exatas Tecnol., Londrina, v. 11, n. 1, p. 59-63, Nov. 2012
.. [3] SJ Andrews, B Smith, MG Deceglie, KA Horowitz, and TJ Silverman. “NREL Comparative PV LCOE Calculator.” 
    Version 2.0.0, August 2021. Em https://www.nrel.gov/pv/lcoe-calculator/documentation.html
"""
from IPython.display import HTML, display
import pandas as pd

class indicadores_financeiros:
    """ Classe que contêm os indicadores financeiros de um projecto.
    """
    def __init__(self, val, tir, tempo_retorno, capex, opex, tempo_vida, lcoe):
        self._val = val
        self._tir = tir
        self._tempo_retorno = tempo_retorno
        self._capex = capex
        self._opex = opex
        self._tempo_vida = tempo_vida
        #self._poupanca_anual = poupanca_anual
        self._lcoe = lcoe

    @property
    def val(self):
        """ Valor actual liquido. [€]

        Returns
        -------
        float
            VAL. [€]
        """
        return self._val

    @property
    def tir(self):
        """ Taxa interna de rentabilidade. [%]

        Returns
        -------
        float
            TIR. [%]
        """
        return self._tir

    @property
    def tempo_retorno(self):
        """ Tempo de retorno. [anos]

        Returns
        -------
        float
            Tempo de retorno. [anos]
        """
        return self._tempo_retorno

    @property
    def lcoe(self):
        """ Levelized cost of energy [€/kWh].

        Returns
        -------
        float
            LCOE. [€/kWh]
        """
        return self._lcoe

    def as_frame(self):
        """ Converte para dataframe.

        Returns
        -------
        pd.DataFrame
            Indicadores financeiros como dataframe.
        """
        df = pd.DataFrame({
            'indice' : ['Tempo vida util projecto [anos]', 'Custo instalação [€]', 'Custo manutenção anual [€/ano]',
             'VAL [€]', 'TIR [%]', 'Retorno do investimento [anos]', 'Lcoe [€/kWh]'],
            'valores': [self._tempo_vida, self._capex, self._opex, self._val, self._tir, self._tempo_retorno, self._lcoe]
        })
        df = df.set_index('indice')
        # df = df.style.format({
        #     'Tempo vida util projecto [anos]' : '{:.1f}',
        #     'Custo instalação [€]' : '{:.2f} €', 
        #     'Custo manutenção anual [€/ano]' : "{:.2f} €",
        #     'Poupança fatura electricidade anual [€]' : "{:.2f} €", 
        #     'VAL [€]' : "{:.2f} €",
        #     'TIR [%]' : "{:.2f} €",
        #     'Retorno do investimento [anos]' : '{:.1f}'
        # })
        return df

    def as_html(self):
        return HTML('<table style="font-size:16px">'
                    +'<tr><td>Tempo vida util projecto [anos]</td><td>{:.1f}</td></tr>'.format(self._tempo_vida)
                    +'<tr><td>Custo instalação [€]</td><td>{:.1f}</td></tr>'.format(self._capex)
                    +'<tr><td>Custo manutenção anual [€/ano]</td><td>{:.1f}</td></tr>'.format(self._opex)
                    #+'<tr><td>Custo total do projecto [€]</td><td>{:.1f}</td></tr>'.format(custo_total)
                    #+'<tr><td>Custo unitario energia PV [€/kWh]</td><td>{:.3f}</td></tr>'.format(lcoe)
                    #+'<tr><td>Poupança fatura electricidade anual [€]</td><td>{:.2f}</td></tr>'.format(self._poupanca_anual)
                    +'<tr><td>VAL [€]</td><td>{:.2f}</td></tr>'.format(self._val)
                    +'<tr><td>TIR [%]</td><td>{:.2f}</td></tr>'.format(self._tir)
                    +'<tr><td>Retorno do investimento [anos]</td><td>{:.1f}</td></tr>'.format(self._tempo_retorno)
                    +'<tr><td>LCOE [€/kWh]</td><td>{:.3f}</td></tr>'.format(self._lcoe)
                    +'</table>')    