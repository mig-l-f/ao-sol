import numpy as np

class bateria:
    """ Representa o funcionamento de uma bateria
    """

    def __init__(self, capacidade, soc_min, soc_max):
        """ Construtor de bateria

        Args:
        -----
        capacidade: float
            Capacidade bateria em kWh
        soc_min: float
            Estado de carga minimo em percentagem (%)
        soc_max: float
            Estado de carga maximo em percentagem (%)
        """
        self.capacidade = capacidade # capacidade da bateria em kWh
        self.soc = 0.0 # estado de carga inicial
        self.soc_min = soc_min # estado de carga minimo (%)
        self.soc_max = soc_max # estado de carga maximo (%)
        self.num_ciclos = 0 # ciclos de carregamento da bateria
        self._acumulado_carregamento = 0.0 # acumulado carregamento para contagem de ciclos

    def get_soc(self):
        """ Obter o estado de carga da bateria (%)

        Returns:
        --------
        soc: float
            Estado de carga em %
        """
        return self.soc
        
    def get_soc_min(self):
        """ Obter o estado de carga minimo (%)

        Returns:
        --------
        soc_min: float
            Estado de carga minímo em %
        """
        return self.soc_min

    def get_soc_max(self):
        """ Obter o estado de carga maximo (%)

        Returns:
        --------
        soc_max: float
            Estado de carga máximo em %
        """
        return self.soc_max

    def get_ciclos_carregamento(self):
        """ Obter o numero de ciclos de carragamento da bateria

        Returns:
        --------
        ciclos carregamento: int
            Número de ciclos de carregamento da bateria
        """
        return self.num_ciclos

    def carrega_bateria(self, energia_a_carregar):
        """ Carrega a bateria com a quantidade de energia a carregar

        Args:
        -----
        energia_a_carregar: float
            Energia a carregar na bateria em kWh

        Returns:
        --------
        energia_carregada: float
            Quantidade de carga que foi armazenada na bateria
        """
        # soc que conseguimos carregar
        soc_possivel = np.max(self.soc_max - self.soc, 0)
        # energia que conseguimos carregar
        energia_possivel = (soc_possivel / 100) * self.capacidade
        # carregar
        if (energia_a_carregar > energia_possivel):
            # carregamos a energia possivel
            self.soc = self.soc_max
            # ciclos carregamento
            self._acumula_ciclos_carregamento(energia_possivel)
            return energia_possivel
        else:
            # carregamos a energia a carregar
            energia_actual = (self.soc / 100) * self.capacidade
            energia_carregada = energia_actual + energia_a_carregar
            self.soc = (energia_carregada / self.capacidade) * 100
            # ciclos de carregamento
            self._acumula_ciclos_carregamento(energia_a_carregar)
            return energia_a_carregar

    def _acumula_ciclos_carregamento(self, energia_a_carregar):
        """ Verifica acumulado de carragemanto para contagem de ciclos

        Args:
        -----
        energia_a_carregar: float
            Energia a carregar na bateria em kWh        
        """
        self._acumulado_carregamento += energia_a_carregar
        if (self._acumulado_carregamento >= self.capacidade):
            self.num_ciclos += 1
            # reset do acumulado
            self._acumulado_carregamento -= self.capacidade

    def descarrega_bateria(self, energia_a_descarregar):
        """ Descarrega a bateria com a quantidade de energia a descarregar

        Args:
        -----
        energia_a_descarregar: float
            Energia a descarregar da bateria

        Returns:
        --------
        energia_descarregada: float
            Quantidade de carga que foi descarregada da bateria
        """
        # soc que conseguimos descarregar
        soc_possivel = np.max(self.soc - self.soc_min, 0)
        # energia que conseguimos descarregar
        energia_possivel = (soc_possivel  / 100) * self.capacidade
        # descarregar
        if (energia_a_descarregar > energia_possivel):
            # descarregamos a energia possivel
            self.soc = self.soc_min
            return energia_possivel
        else:
            # descarregamos a energia a descarregar
            energia_actual = (self.soc / 100) * self.capacidade
            energia_descarregada = energia_actual - energia_a_descarregar
            self.soc = (energia_descarregada / self.capacidade) * 100
            return energia_a_descarregar
