""" Indicadores de autoconsumo.

Os indicadores para todos os sistemas são:

======================== ======== ===========
Indicadores              Unidade  Descrição
======================== ======== ===========
iac                      %        Indice auto consumo. Quanta da energia produzida é autoconsumida.
ias                      %        Indice auto suficiência. Quanta da energia total é coberta por autoconsumo.
ier                      %        Indice entrega a rede [%]. Quanta da energia produzia é entregue à rede.
energia_autoconsumida    kWh      Total energia autoconsumida.
energia_rede             kWh      Total energia consumida da rede.
energia_rede_vazio       kWh      Total energia consumida da rede em periodo vazio.
energia_rede_fora_vazio  kWh      Total energia consumida da rede em periodo fora de vazio.
consumo_total            kWh      Total energia consumida.
injeccao_rede            kWh      Total energia injectada na rede.
perdas_inversor          kWh      Total energia perdida na conversão do inversor.
residuo                  kWh      Residuo entre energia gerada (autoproducao+consumo_rede) e consumida (injeccao_rede+perdas_inversor+perdas_bateria+consumo).
======================== ======== ===========

Adicionalmente, sistimas com bateria têm os seguintes indicadores:

====================== ======== ===========
Indicadores            Unidade  Descrição
====================== ======== ===========
fornecido_bateria      kWh      Total de energia fornecida pela bateria.
perdas_bateria         kWh      Total de energia perdida na conversão da bateria.
num_ciclos             -        Número de ciclos de carregamento da bateria em 1 ano.
====================== ======== ===========
"""
from IPython.display import HTML, display
from tabulate import tabulate
import pandas as pd

class indicadores_autoconsumo:
    """ Classe que contêm os indicadores de autoconsumo.
    """
    def __init__(self, iac, ias, ier, capacidade_instalada, energia_autoproduzida, energia_autoconsumida, 
                 energia_rede, energia_rede_vazio, energia_rede_fora_vazio, 
                 energia_injectada_rede, consumo_total, perdas_inversor, residuo,
                 armazenamento=False, fornecido_bateria=0, perdas_bateria=0, num_ciclos_bateria=0, capacidade_bateria=0):
        self._iac = iac
        self._ias = ias
        self._ier = ier
        self._capacidade_instalada = capacidade_instalada
        self._energia_autoproduzida = energia_autoproduzida
        self._energia_autoconsumida = energia_autoconsumida
        self._energia_rede = energia_rede
        self._energia_rede_vazio = energia_rede_vazio
        self._energia_rede_fora_vazio = energia_rede_fora_vazio
        self._energia_injectada_rede = energia_injectada_rede
        self._consumo_total = consumo_total
        self._perdas_inversor = perdas_inversor
        self._residuo = residuo
        self._com_armazenamento = armazenamento
        self._fornecido_bateria = fornecido_bateria
        self._perdas_bateria = perdas_bateria
        self._n_ciclos_bat = num_ciclos_bateria
        self._capacidade_bateria = capacidade_bateria

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
    def energia_rede_vazio(self):
        """ Energia consumida da rede em periodo vazio em kWh.
        """
        return self._energia_rede_vazio

    @property
    def energia_rede_fora_vazio(self):
        """ Energia consumida da rede em periodo fora de vazio em kWh.
        """
        return self._energia_rede_fora_vazio

    @property
    def energia_injectada_rede(self):
        """ Energia injectada na rede em kWh
        """
        return self._energia_injectada_rede

    @property
    def consumo_total(self):
        """ Total de energia consumida em kWh
        """
        return self._consumo_total

    @property
    def energia_perdida_inversor(self):
        """ Energia perdida na conversão no inversor em kWh.
        """
        return self._perdas_inversor

    @property
    def com_armazenamento(self):
        """ Se contem indicadores de armazenamento ou não
        """
        return self._com_armazenamento

    @property
    def energia_fornecida_bateria(self):
        """ Energia fornecida pela bateria em kWh
        """
        return self._fornecido_bateria

    @property
    def energia_perdida_bateria(self):
        """ Energia perdida na conversão na bateria em kWh.
        """
        return self._perdas_bateria

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

    @property
    def capacidade_bateria(self):
        """ Capacidade da bateria em kWh
        """
        return self._capacidade_bateria

    def to_frame(self, label="indicadores"):
        """ Dataframe com indicadores.
        """

        ind = pd.DataFrame()
        ind["label"]=[label]
        ind["Potencia instalada [kW]"]=[self.capacidade_instalada]
        ind["IAS: Contributo PV [%]"]=[self.ias] 
        ind["IAC: Indice Auto consumo [%]"]=[self.iac]
        ind["IER: Producao PV desperdicada [%]"]=[self.ier]
        ind["Energia consumida [kWh]"]=[self.consumo_total]
        ind["Energia Autoproduzida [kWh]"]=[self.energia_autoproduzida]
        ind["Energia Autoconsumida [kWh]"]=[self.energia_autoconsumida]
        ind["Energia consumida rede [kWh]"]=[self.energia_rede]
        ind["Energia injectada rede [kWh]"]=[self.energia_injectada_rede]
        ind["Perdas inversor [kWh]"]=[self.energia_perdida_inversor]
        ind["Numero de horas equivalentes [h/ano]"]=[self.horas_equivalentes]
        
        if self.com_armazenamento:
            ind["Capacidade bateria [kWh]"] = [self.capacidade_bateria]
            ind["Energia fornecida bateria [kWh]"] = [self.energia_fornecida_bateria]
            ind["Perdas bateria [kWh]"] = [self.energia_perdida_bateria]
            ind["Ciclos da bateria"] = [self.num_ciclos_bateria]

        ind["residuo"] = [self._residuo]
        ind = ind.set_index("label")
        return ind

    def print_markdown(self, label="indicadores"):
        tabela = self.to_frame(label)

        print(tabulate(tabela.T, tablefmt="github", floatfmt=('.1f')))

    def print_html(self, label="indicadores"):
        tabela = self.to_frame(label).T
        display(HTML(tabela.to_html(index=True, float_format="%.1f")))