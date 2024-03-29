from IPython.display import HTML, display

class indicadores_autoconsumo:
    def __init__(self, iac, ias, ier, capacidade_instalada, energia_autoproduzida, energia_autoconsumida, energia_rede, consumo_total, armazenamento=False, horas_carga_min=0, horas_carga_max=0, num_ciclos_bateria=0):
        self._iac = iac
        self._ias = ias
        self._ier = ier
        self._capacidade_instalada = capacidade_instalada
        self._energia_autoproduzida = energia_autoproduzida
        self._energia_autoconsumida = energia_autoconsumida
        self._energia_rede = energia_rede
        self._consumo_total = consumo_total
        self._com_armazenamento = armazenamento
        self._horas_carga_min = horas_carga_min
        self._horas_carga_max = horas_carga_max
        self._n_ciclos_bat = num_ciclos_bateria

    @property
    def iac(self):
        """ Indice de auto consumo [%].

        Percentagem da autoproducao que é consumida
        """
        return self._iac

    @property
    def ias(self):
        """ Indice de auto suficiencia [%].

        Percentagem do consumo que é autoconsumo.
        """
        return self._ias

    @property
    def ier(self):
        """ Indice de entrega à rede [%].

        Percentagem da autoprodução que é entregue a rede.
        """
        return self._ier

    @property
    def capacidade_instalada(self):
        """ Capacidade instalada em kWp
        """
        return self._capacidade_instalada

    @property
    def energia_autoproduzida(self):
        """ Energia autoproduzida em kWh
        """
        return self._energia_autoproduzida

    @property
    def energia_autoconsumida(self):
        """ Energia autoconsumida em kWh
        """
        return self._energia_autoconsumida

    @property
    def energia_rede(self):
        """ Energia consumida da rede em kWh
        """
        return self._energia_rede

    @property
    def consumo_total(self):
        """ Total de energia consumida em kWh
        """
        return self._consumo_total

    @property
    def num_horas_carga_min(self):
        """ Numero de horas da bateria à carga minima (SOC min)
        """
        return self._horas_carga_min

    @property
    def perc_horas_carga_min(self):
        """ Percentagem do ano da bateria em carga mínima [%]
        """
        return (self._horas_carga_min / 8760) * 100

    @property
    def num_horas_carga_max(self):
        """ Numero de horas da bateria à carga máxima (SOC max)
        """
        return self._horas_carga_max

    @property
    def perc_horas_carga_max(self):
        """ Percentagem do ano da bateria em carga máxima [%]
        """
        return (self._horas_carga_max / 8760) * 100

    @property
    def num_ciclos_bateria(self):
        """ Numero de ciclos de carregamento da bateria em 1 ano.
        """
        return self._n_ciclos_bat

    @property
    def horas_equivalentes(self):
        """ Numero de horas equivalentes à potência nominal (h/ano)
        """
        return self._energia_autoproduzida / self._capacidade_instalada

    def print_html(self):
        """ print as a html table
        """
        tabela = '<table style="font-size:16px">' \
        +'<tr><td>Potencia Instalada</td><td>{:.2f} kW</td></tr>'.format(self._capacidade_instalada) \
        +'<tr></tr>' \
        +'<tr><td>Energia Autoproduzida [kWh]</td><td>{:.1f}</td></tr>'.format(self._energia_autoproduzida) \
        +'<tr><td>Energia Autoconsumida [kWh]</td><td>{:.1f}</td></tr>'.format(self._energia_autoconsumida) \
        +'<tr><td>Energia consumida rede [kWh]</td><td>{:.1f}</td></tr>'.format(self._energia_rede) \
        +'<tr><td>Energia consumida [kWh]</td><td>{:.1f}</td></tr>'.format(self._consumo_total) \
        +'<tr></tr>' \
        +'<tr><td>Numero de horas equivalentes [h/ano]</td><td>{:.1f}</td></tr>'.format(self.horas_equivalentes) \
        +'<tr><td>IAS: Contributo PV [%]</td><td>{:.1f}</td></tr>'.format(self._ias) \
        +'<tr><td>IAC: Indice Auto consumo [%]</td><td>{:.1f}</td></tr>'.format(self._iac) \
        +'<tr><td>IER: Producao PV desperdicada [%]</td><td>{:.1f}</td></tr>'.format(self._ier) 
        if (self._com_armazenamento):
            tabela += '<tr><td>Bateria:</td><td></td><td></td></tr>' \
            + '<tr><td>Em carga minima</td><td>{:.1f} hr</td><td>{:.2f} %</td></tr>'.format(self._horas_carga_min, self.perc_horas_carga_min) \
            + '<tr><td>Em carga máxima</td><td>{:.1f} hr</td><td>{:.2f} %</td></tr>'.format(self._horas_carga_max, self.perc_horas_carga_max) \
            + '<tr><td>Ciclos da bateria</td><td>{}</td><td></td></tr>' .format(self._n_ciclos_bat)
        tabela += '</table>'
        display(HTML(tabela))