from IPython.display import HTML, display
import pandas as pd

class indicadores_financeiros:
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
        """ Valor actual liquido
        """
        return self._val

    @property
    def tir(self):
        """ Taxa interna de rentabilidade
        """
        return self._tir

    @property
    def tempo_retorno(self):
        """ Tempo de retorno
        """
        return self._tempo_retorno

    @property
    def lcoe(self):
        """ levelized cost of energy (€/kWh)
        """
        return self._lcoe

    def as_frame(self):
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