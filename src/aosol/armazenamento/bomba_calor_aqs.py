""" Modelo de bomba de calor (BC) para águas quentes sanitárias (AQS).

==========
Introdução
==========

O modelo avalia a evolução da temperatura no depósito através da energia fornecida pela bomba de calor e
resistência e perdida tanto para o ambiente como retirada para AQS. A energia fornecida depende do modo de
operação e dos setpoints definidos.

O modelo de BC é modificado apartir do descrito em [1]_. O artigo apresenta um modelo para aquecimento ambiente
para uma BC com inversor e on-off. O modelo original é alterado para:

* considerar a energia extraida para AQS e não perdida pelo edificio.
* a BC funciona à potência e cop nominal ou está desligada, sendo que estes parâmetros podem ser retirados de qualquer prospecto comercial de BC
* a BC funciona de acordo com o modo de operação descrito abaixo e pode não fornecer energia enquanto estiver dentro dos setpoints. No modelo original a BC tenta sempre colmatar as perdas em cada intervalo.

==========
Definições
==========

Modos de funcionamento:

* ECO: apenas bomba de calor, setpoint SP1, hipotese de utilizar resistência abaixo da temperatura mínima :math:`T_{min,s}`:
* AUT: bomba de calor e resistência em simultâneo, setpoint SP2
* PV : bomba de calor e resistência em simultâneo, setpoint SP6

Setpoints:

* SP1 : setpoint em modo eco
* SP2 : setpoint em modo aut
* SP3 : setpoint activação resistência
* SP5 : setpoint paragem bomba calor
* SP6 : setpoint em modo pv
* r0 : diferencial de setpoint
* r7 : diferencial resistência em modo aut

Perdas de energia do depósito:

* :math:`E_{LOST,S}`: ara o ambiente, devido à differença de temperatura entre depósito (:math:`T_{s,room}`)
* :math:`E_{LOST,AQS}`: Extraido do depósito pelo perfil utilizado

Ganhos de energia pelo depósito:

* :math:`E_{HP}`: Energia térmica fornecida pela bomba de calor
* :math:`E_{BU}`: Energia fornecida pela resistência

Definição de temperaturas para os diferentes modos de operação:

**Modo ECO**:

* :math:`T_{max,s}`: e :math:`T_{max,bc}` temperatura máxima no depósito dado por SP1.
* :math:`T_{min,s}`: temperatura mínima no depósito, se utiliza resistência abaixo minimo então dado por SP3, caso contrário é :math:`T_{min,bc}`.
* :math:`T_{min,bc}`: histerese bomba calor, dado por :math:`SP1 - r0`.

**Modo AUT**:

* :math:`T_{max,s}`: Temperatura máxima do depósito dado por SP2.
* :math:`T_{max,bc}`: Temperatura máxima BC dada por :math:`min(T_{max,s}, SP5)`.
* :math:`T_{min,bc}`: Temperatura mínima BC dado por :math:`T_{max,bc} - r0`.
* :math:`T_{min,s}`: Temperatura mínima depósito dado por :math:`min(T_{max,s}-r7, T_{min,bc})`.

**Modo PV**:

* :math:`T_{max,s}`: Temperatura máximo do depósito dado por SP6
* :math:`T_{max,bc}`: Temperatura máxima BC dada por :math:`min(SP6, SP5)`
* :math:`T_{min,bc}`: Temperatura mínima BC dado por :math:`T_{max,bc}-r0`
* :math:`T_{min,s}`: Tempertara mínima depoósito dado por :math:`min(SP6-r7, T_{min.bc})`

======
Modelo
======

Modelo calcula a evolução da temperatura do depósito em intervalos horários.

Variáveis:

* :math:`T_s(i)`: Temperatura do depósito no intervalo actual.
* :math:`T_{s,room}`: Temperatura na sala onde está o depósito

Calcular energia perdida pelo depósito para o ambiente:

.. math:

    E_{LOST,S}(i) = U \\left[ T_s(i) - T_{s,room}\\right]

    U = 1.023 V_s + 1.293

A energia extraida para AQS é um parâmetro de entrada dada pelo perfil de extracção para a hora i de cálculo.

Energia no depósito:

.. math:: E_s(i) = \\rho_w V_s c_{pw} \\left[ T_s(i) - T_{min,s} \\right]

Para saber a energia fornecia é preciso com a temperatura actual :math:`T_s(i)` qual é o estado da bomba de calor. 
Sendo que apenas se considera uma BC On-Off, que ou está à potência nominal ou está desligada. 
Para cada um dos modos é calculado da seguinte forma:

**Para o modo ECO e AUT**:

* Quando a temperatura está a subir, a BC está ligada quando :math:`T_s(i) < T_{max,bc}`
* Quando a temperatura está a descer, a BC liga quando :math:`T_s(i) < T_{min,bc}`

**Para o modo PV**, adicionalmente aos anteriores:

* Se há uma mudança de modo de funcionamento a BC liga desde que :math:`T_s(i) < T_{max,bc}`

Sabend a potência da BC é possivel calcular temperatura no deposito (:math:`T_s^{'}`) fornecida bomba calor se esta funcionar todo o intervalo à potência designada:

.. math ::

    T_s^{'}(i) = T_s(i) + \\left[ P_{HP}(i)\\tau - E_{LOST,S}(i) - E_{LOST,AQS}(i) \\right]\\left(\\rho_w V_s c_{pw} \\right)^{-1}, \\tau=1hr

Calcula a energia termica fornecida pela BC, depende de não ultrapassar o setpoint maximo:

Se :math:`T_s^{'}(i) < T_{max,bc}`:

.. math:: E_{HP}(i) = P_{HP}(i)\\tau

Caso ultrapasse, então apenas fornece energia para colmatar perdas e chegar à temperatura máxima:

.. math::

    E_{HP,subida}(i) = E_{LOST,S} + E_{LOST,AQS} + \\rho_w V_s c_{pw}\\left[ T_{max,s} - T_s(i)\\right]

Pode dar-se o caso de a BC estar desligada quando :math:`T_s(i)` se encontra na zona de histerese mas com a perda de energia 
o :math:`T_s^{'}(i)` ficar abaixo da temperatura onde volta a ligar. Assim:

.. math ::

    E_{HP,descida}(i) = E_{LOST,S} + E_{LOST,AQS} + \\rho_w V_s c_{pw}\\left[ T_{min,bc} - T_s^{'}(i)\\right]

    E_{HP}(i) = max(E_{HP,subida}(i), E_{HP,descida}(i))

Com o valor final de :math:`E_{HP}(i)` calculamos novamente :math:`T_s^{'}(i)`. 

De seguida calculamos a contribuição da resistência, que é diferente para cada um dos modos:

**Modo ECO**:

* Se a resistência nunca ligar, então a contribuição é :math:`E_{BU} = 0`.
* Se a resistência ligar abaixo do SP3, então calculamos a energia no depósito :math:`E_s^{'}(i)` e se for negativa a resistência liga.

Com podemos calcular a energia no depósito, relativamente à temperatura mínima:

.. math:: $E_s^{'}(i) = \\rho_w V_s c_{pw} \\left[ T_s^{'}(i) - T_{min,s} \\right]

Se a energia no depósito for negativa e tivermos a opção de accionar a resistência abaixo de :math:`T_{min,s}` (SP3) sendo:

.. math:: E_{BU}(i) = min(E_s^{'}(i), P_{BU}\\tau), \\tau=1hr

caso contrário:

.. math:: E_{BU}(i) = 0

**Modo AUT e PV**:

Como a resistência funciona em paralelo, calculamos energia fornecida pela resistência (BU). 
A resistência está ligada se:

* temperatura esta a subir e :math:`T_s^{'}(i) < T_{max,s}`
* temperatura esta a descer e :math:`min(T_s^{'}(i), T_s(i)) < T_{min,s}`

A energia fornecida é o minimo entre:

.. math::

    E_{BU} = min(\\rho_w V_s c_{pw}\\left[ T_{max,bc} - T_s^{'}(i)\\right], P_{BU}\\tau), \\tau=1hr

Finalmente sabendo a energia adicionada e retirada do sistema podemos calcular a temperatura no próximo intervalo:

.. math::

    T_s(i+1) = T_s(i) + \\left[E_{HP}(i) + E_{BU}(i) - E_{LOST,S} - E_{LOST,AQS} \\right]\\left(\\rho_w V_s c_{pw} \\right)^{-1}

Uma vez que :math:`E_{HP}(i)$` é a energia térmica fornecida pela bomba de calor, queremos também saber qual a energia eléctrica consumida pela bomba de calor. 

Começamos por calcular o factor de capacidade :math:`CR(i)`:, racio entre a energia :math:`E_{HP}` e a potência à capacidade declarada :math:`P_{HP}`:

.. math::  CR = \\frac{E_{HP}}{P_{HP}}

Depois calculamos o factor de correcção do COP, como descrito na EN 14825, utilizando o factor de degradação :math:`C_c = 0.9`:

.. math:: f_{COP} = CR(i) / \\left[1-C_c + C_c*CR(i) \\right]

A energia electrica consumida pela BC é:

.. math:: E_{USED,BC}(i) = E_{HP}(i)/\\left[ COP*f_{COP}\\right]

.. [1] Naldi, Claudia & Morini, Gian & Zanchini, E.. (2014). A method for the choice of the optimal balance-point 
      temperature of air-to-water heat pumps for heating. Sustainable Cities and Society. 12. 10.1016/j.scs.2014.02.005. 
      See https://www.researchgate.net/publication/260393977_A_method_for_the_choice_of_the_optimal_balance-point_temperature_of_air-to-water_heat_pumps_for_heating
"""

import pandas as pd
import math
from enum import Enum
from dataclasses import dataclass

RHO_W = 1000.0
""" Densidade da água. [:math:`kg/m^3`]
"""
CPW = 4181.0
""" Calor específico da água. [:math:`J/Kg.ºC`]
"""
CPW_KW = CPW / (3600 * 1000)
""" Calor específico da água em kW. [:math:`kW/kg.ºC`]
"""
COEF_DEGRADACAO = 0.9
""" Coeficiente de degradação para cálculo do factor de correcção do COP de acordo com metodologia EN 14825. [-]
"""

class ModoOperacaoBombaCalor(Enum):
    """ Modo de operação da bomba de calor.

    Args
    ----
    ECO
        Modo economico
    AUT
        Modo conforto
    PV
        Modo fotovoltaico
    """
    ECO = 0 # Modo economico
    AUT = 1 # Modo conforto
    PV = 2   # Modo fotovoltaico

    def __sub__(self, other):
        if isinstance(other, ModoOperacaoBombaCalor):
            a = self.value[0] if isinstance(self.value, tuple) else self.value
            b = other.value[0] if isinstance(other.value, tuple) else other.value
            return a - b
        raise TypeError("Subtraccao de tipos incompativeis")

@dataclass
class ParametrosBombaCalor():
    """ Parametros controlador bomba de calor.

    Args
    ----
    SP1 : float
        Setpoint em modo economico. [ºC]
    SP2 : float
        Setpoint em modo conforto. [ºC]
    SP3 : float
        Setpoint activacao Boost. [ºC]
    SP5 : float
        Setpoint paragem bomba calor. [ºC]
    r0 : float
        Diferencial de setpoint. [ºC]
    usa_resist : bool
        Em modo economico se resistencia é activada abaixo SP3
    modo : ModoOperacaoBombaCalor
        Modo de operação.
    """
    SP1 : float = 52.0        # Setpoint em modo economico
    SP2 : float = 60.0        # Setpoint em modo conforto
    SP3 : float = 45.0        # Setpoint activacao Boost
    SP5 : float = 55.0        # Setpoint paragem bomba calor
    SP6 : float = 65.0        # Setpoint em modo PV
    r0 : float = 5.0          # Diferencial de setpoint
    r7 : float = 15.0         # Diferencial resistencia em modo conforto
    usa_resist : bool = False # Em modo economico se resistencia é activada abaixo SP3
    modo : ModoOperacaoBombaCalor = ModoOperacaoBombaCalor.ECO  # Modo operação

class BombaCalorAqs:
    """ Bomba de Calor para águas quentes sanitárias (AQS).
    """

    def __init__(self, pot_termica_bc, cop, pot_resist, params, vol, bu):
        """ Construtor.

        Parameters
        ----------
        pot_termica_bc : float
            Potência térmica nominal fornecida pela bomba de calor. [kW]
        cop : float
            Coeficiente de performance da bomba. [-]
        pot_resist : float
            Potência da resistência. [kW]
        params : ParametrosBombaCalor
            Parametros de configuração da bomba de calor.
        vol: float
            :math:`V_s`: Volume em m3, para converter de litros para m3 /1000.
        bu : float
            :math:`b_U`: factor de redução de temperatura.
        """
        self.pot_termica_bc = pot_termica_bc
        self.cop = cop
        self.pot_resist = pot_resist
        self.params = params
        self.poder_calorifico_deposito = RHO_W * vol * CPW_KW # kW/ºC
        self.u_kw = (1.023*vol+1.293)/1000 # kW/K
        self.bu = bu

    def _potencia_bomba_calor(self, deriv_t, t_actual, t_max_bc, t_min_bc, modo_op, modo_op_anterior):
        """ Potencia de funcionamento da bomba de calor.

        Parameters
        ----------
        deriv_t : float
            Derivada da temperatura entre intervalo actual e anterior. [ºC]
        t_actual : float
            Temperatura no depósito no intervalo actual. [ºC]
        t_max_bc : float
            Temperatura máxima no modo bomba de calor. [ºC]
        t_min_bc : float
            Temperatura mínima no modo bomba de calor. [ºC]
        modo_op : ModoOperacaoBombaCalor
            Modo de operação no intervalo actual.
        modo_op_anterior : ModoOperacaoBombaCalor
            Modo de operação no intervalo anterior.

        Returns
        -------
        p_hp : float
            Potência térmica que a bomba de calor fornece no intervalo actual. [kW]

        """
        # bomba calor ligada se:
        # * temperatura a subir (deriv_t > 0) e temperatura no deposito < t_max_bc, t_max_bc = min(SP1, SP5)
        bc_ligada_subida = (deriv_t >= 0) and (t_actual < t_max_bc)
        # * temperatura a descer (deriv_t < 0) e temperatura no depostito < t_max_bc-histerese
        bc_ligada_descida = (deriv_t < 0) and (t_actual < t_min_bc)
        # Se modo é maior que anterior ( PV > AUT > ECO )
        bc_ligada_mudanca_modo = (modo_op - modo_op_anterior > 0)

        bc_ligada = bc_ligada_subida or bc_ligada_descida or bc_ligada_mudanca_modo

        p_hp = 0
        if (bc_ligada):
            p_hp = self.pot_termica_bc
        return p_hp

    def _energia_resistencia(self, modo, deriv_t, t_prox_dep, t_max_s, t_min_s):
        """ Energia fornecida pela resistência no intervalo actual.

        Parameters
        ----------
        modo : ModoOperacaoBombaCalor
            Modo de operação no intervalo actual.
        deriv_t : float
            Derivada da temperatura entre intervalo actual e anterior. [ºC]
        t_prox_dep : float
            Temperatura no depoósito incluindo energia da bomba de calor. [ºC]
        t_max_s : float
            Temperatura máxima no depósito. [ºC]
        t_min_s : float
            Temperatura mínima no depósito. [ºC]

        Returns
        -------
        e_bu : float
            Energia fornecida pela resistência. [kWh]
        """
        if (modo == ModoOperacaoBombaCalor.ECO):
            # energia deposito E_s'
            e_prox_dep = self.poder_calorifico_deposito * (t_prox_dep - t_min_s)
            e_bu = 0
            if (self.params.usa_resist and e_prox_dep < 0):
                e_bu = min(abs(e_prox_dep), self.pot_resist)
        elif (modo == ModoOperacaoBombaCalor.AUT or modo == ModoOperacaoBombaCalor.PV):
            bu_ligada_subida = (deriv_t > 0) and (t_prox_dep < t_max_s) # so liga se estiver a subir, t_prox_dep é influenciada pelas perdas
            bu_ligada_descida = (deriv_t < 0) and (t_prox_dep < t_min_s)
            bu_ligada = bu_ligada_subida or bu_ligada_descida

            e_bu = 0
            if bu_ligada:
                e_bu = min( self.poder_calorifico_deposito*(t_max_s - t_prox_dep) , self.pot_resist)
        else:
            raise Exception('Control resistencia: modo desconhecido')

        return e_bu

    def calcula_temperatura_sala_deposito(self, t_int, t_ext):
        """ Calcula a temperatura na sala do depósito.

        Parameters
        ----------
        t_int : float
            Temperatura no interior. [ºC]
        t_ext : float
            Temperatura no exterior. [ºC]

        Returns
        -------
        t_sala : float
            Temperatura na sala. [ºC]
        """
        return t_int-self.bu*(t_int - t_ext)

    def calcula_temperatura_deposito_intervalo(self, t_sala, t_deposito_actual, t_deposito_anterior, e_extr_aqs, modo_op, modo_op_anterior):
        """ Calcula a evolução da temperatura no depósito para um intervalo. 
        Intervalo com duração de 1hr.

        Parameters
        ----------
        t_sala : float
            Temperatura na sala onde está o depósito. [ºC]
        t_deposito_actual : float
            Temperatura depósito actual. [ºC]
        t_deposito_anterior : float
            Temperatura depósito no intervalo anterior. [ºC]
        e_extr_aqs : float
            Energia extraida para AQS durante o intervalo. [kWh]
        modo_op : ModoOperacaoBombaCalor
            Modo de operação actual.
        modo_op_anterior : ModoOperacaoBombaCalor
            Modo de operação no intervalo anterior.

        Returns
        -------
        t_deposito_prox : float
            Temperatura no depósito no intervalo seguinte. [ºC]
        e_hp : float
            Energia térmica fornecida pela bomba calor. [kWh]
        e_bu : float
            Energia térmica/eléctrica fornecida/consumida pela resistência. [kWh]
        e_used_bc : float
            Energia eléctrica consumida pela bomba calor. [kWh]
        e_lost_s : float
            Energia perdida pela depósito para o ambiente durante o intervalo. [kWh]
        """
        # definicao temperaturas
        if (modo_op == ModoOperacaoBombaCalor.ECO):        
            t_max_s = self.params.SP1  # t max deposito
            t_max_bc = min(self.params.SP1, self.params.SP5) # t max bc == t max deposito em modo economico
            t_min_bc = t_max_bc - self.params.r0  # t min bc, histeres bc
            t_min_s = self.params.SP3 if self.params.usa_resist else t_min_bc  # t min deposito
        elif (modo_op == ModoOperacaoBombaCalor.AUT):
            t_max_s = self.params.SP2  # t max deposito        
            t_max_bc = min(self.params.SP2, self.params.SP5) # t max bomba calor
            t_min_bc = t_max_bc - self.params.r0  # t min bc, histeres bc
            t_min_s = min(self.params.SP2 - self.params.r7, t_min_bc)  # t min deposito
        elif (modo_op == ModoOperacaoBombaCalor.PV):
            t_max_s = self.params.SP6
            t_max_bc = min(self.params.SP6, self.params.SP5)
            t_min_bc = t_max_bc - self.params.r0
            t_min_s = min(t_max_s - self.params.r7, t_min_bc)
        else:
            raise Exception('Modo operação da BC desconhecido')
        
        # energia perdida deposito ambient
        e_lost_s = self.u_kw*(t_deposito_actual - t_sala)

        # control bomba calor
        deriv_t = t_deposito_actual - t_deposito_anterior
        p_hp = self._potencia_bomba_calor(deriv_t, t_deposito_actual, t_max_bc, t_min_bc, modo_op, modo_op_anterior)
        
        # energia fornecida pela BC
        t_prox_dep = t_deposito_actual + (p_hp - e_lost_s - e_extr_aqs)/self.poder_calorifico_deposito
        e_hp_subida = p_hp
        if (t_prox_dep > t_max_s):
            e_hp_subida = e_lost_s + e_extr_aqs + self.poder_calorifico_deposito*(t_max_bc - t_deposito_actual)

        e_hp_descida = 0
        if (t_prox_dep < t_min_bc):
            e_hp_descida = e_lost_s + e_extr_aqs + self.poder_calorifico_deposito*(t_min_bc - t_prox_dep)
            e_hp_descida = min(e_hp_descida, self.pot_termica_bc)

        e_hp = max(e_hp_subida, e_hp_descida)

        # t_s' com e_hp
        t_prox_dep = t_deposito_actual + (e_hp - e_lost_s - e_extr_aqs)/self.poder_calorifico_deposito

        # controlo resistencia
        e_bu = self._energia_resistencia(modo_op, deriv_t, t_prox_dep, t_max_s, t_min_s)

        # temperatura proximo timestep
        t_deposito_prox = t_deposito_actual + (e_hp + e_bu - e_lost_s - e_extr_aqs)/self.poder_calorifico_deposito

        # calcula energia electrica BC
        cr = min(e_hp / self.pot_termica_bc, 1.0)
        cc = 0.9
        f_cop = cr / (1-cc + cc*cr)
        e_used_bc = 0
        if f_cop > 0:
            e_used_bc = e_hp / (self.cop*f_cop)

        return t_deposito_prox, e_hp, e_bu, e_used_bc, e_lost_s
 