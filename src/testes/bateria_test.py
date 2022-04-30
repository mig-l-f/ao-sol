import unittest
from ..aosol.armazenamento import bateria

class TestBateria(unittest.TestCase):
    def test_criar_bateria(self):
        b = bateria.bateria(1.2, 20, 80)
        self.assertEqual(0, b.get_soc())
        self.assertEqual(20, b.get_soc_min())
        self.assertEqual(80, b.get_soc_max())

    def test_carregar_bateria_com_excesso(self):
        b = bateria.bateria(1.2, 20, 80)
        energia_carregada = b.carrega_bateria(1.2)

        self.assertEqual(0.96, energia_carregada) # 1.2 * 0.8 = 0.96
        self.assertEqual(80, b.get_soc())
        
    def test_carregar_bateria_com_menos_que_maximo(self):
        b = bateria.bateria(1.2, 20, 80)
        energia_carregada = b.carrega_bateria(0.6)

        self.assertEqual(0.6, energia_carregada)
        self.assertEqual(50, b.get_soc())

    def test_carregamentos_successivos(self):
        b = bateria.bateria(1.2, 20, 80)
        # 1º carregamento soc a 50%
        energia_carregada = b.carrega_bateria(0.6)
        self.assertEqual(0.6, energia_carregada)
        self.assertEqual(50, b.get_soc())

        # 2º carregamento soc a 75%
        energia_carregada = b.carrega_bateria(0.3)
        self.assertEqual(0.3, energia_carregada)
        self.assertEqual(75, b.get_soc())

        # 3º carregamento soc a 80%, energia a mais
        energia_carregada = b.carrega_bateria(0.2)
        self.assertEqual(0.06, energia_carregada)
        self.assertEqual(80, b.get_soc())

        # 4º carregamento, nao carrega
        energia_carregada = b.carrega_bateria(0.1)
        self.assertEqual(0, energia_carregada)
        self.assertEqual(80, b.get_soc())

    def test_descarregar_bateria_com_excesso(self):
        b = bateria.bateria(1.2, 20, 80)
        energia_carregada = b.carrega_bateria(1.2)

        energia_descarregada = b.descarrega_bateria(1.2)
        self.assertEqual(0.72, energia_descarregada) # descarga 60% => 1.2 * 0.6 = 
        self.assertEqual(20, b.get_soc())

    def test_descarregar_bateria_com_menos_que_maximo(self):
        b = bateria.bateria(1.2, 20, 80)
        energia_carregada = b.carrega_bateria(1.2)

        # descarrega 40% => 1.2 * 0.4 = 0.48
        energia_descarregada = b.descarrega_bateria(0.48)
        self.assertEqual(0.48, energia_descarregada)
        self.assertEqual(40, b.get_soc())

    def test_descarregamentos_sucessivos(self):
        b = bateria.bateria(1.2, 20, 80)
        energia_carregada = b.carrega_bateria(1.2)

        # 1º descarga 30% => 1.2 * 0.3 = 0.36
        energia_descarregada = b.descarrega_bateria(0.36)
        self.assertEqual(0.36, energia_descarregada)
        self.assertEqual(50, b.get_soc())

        # 2a descarga 20% => 1.2 * 0.2 = 0.24
        energia_descarregada = b.descarrega_bateria(0.24)
        self.assertEqual(0.24, energia_descarregada)
        self.assertEqual(30, b.get_soc())

        # 3a descarga max 10% => 1.2 * 0.1 = 0.12
        energia_descarregada = b.descarrega_bateria(0.24)
        self.assertEqual(0.12, energia_descarregada)
        self.assertEqual(20, b.get_soc())

        # 4a descarga, nao descarrega
        energia_descarregada = b.descarrega_bateria(0.1)
        self.assertEqual(0, energia_descarregada)
        self.assertEqual(20, b.get_soc())

    def test_carregar_e_descarregar(self):
        b = bateria.bateria(1.2, 20, 80)

        # carrega a 50%
        energia = b.carrega_bateria(0.6)
        self.assertEqual(0.6, energia)
        self.assertEqual(50, b.get_soc())

        # descarrega 10%
        energia = b.descarrega_bateria(0.12)
        self.assertEqual(0.12, energia)
        self.assertEqual(40, b.get_soc())

        # carrega mais q maximo, maximo 40% => 1.2 * 0.4
        energia = b.carrega_bateria(1.2)
        self.assertEqual(0.48, energia)
        self.assertEqual(80, b.get_soc())

        # descarrega 50% fica a 30%
        energia = b.descarrega_bateria(0.6)
        self.assertEqual(0.6, energia)
        self.assertEqual(30, b.get_soc())

        # descarrega 50%, apenas descarrega 10%
        energia = b.descarrega_bateria(0.6)
        self.assertEqual(0.12, energia)
        self.assertEqual(20, b.get_soc())

    def test_numero_ciclos_apos_carregamento(self):
        b = bateria.bateria(1, 20, 80)
        
        self.assertEqual(0, b.get_ciclos_carregamento())
        
        # carrega 80%
        energia_carregada = b.carrega_bateria(1)
        self.assertEqual(0.8, energia_carregada)
        self.assertEqual(0, b.get_ciclos_carregamento())

        # descarrega 50%
        energia_descarregada = b.descarrega_bateria(0.5)
        self.assertEqual(0.5, energia_descarregada)
        self.assertEqual(0, b.get_ciclos_carregamento())

        # carrega 50% -> 1 ciclo, ja carregou 80+50 
        energia_carregada = b.carrega_bateria(0.5)
        self.assertEqual(0.5, energia_carregada)
        self.assertEqual(1, b.get_ciclos_carregamento())

    def test_dois_ciclos_carregamento(self):
        b = bateria.bateria(1.4, 20, 80)

        # carrega ate maximo (80%)
        energia_carregada = b.carrega_bateria(1.4)
        self.assertEqual(1.4*0.8, energia_carregada)
        self.assertAlmostEqual(80, b.get_soc(), 2)
        self.assertEqual(0, b.get_ciclos_carregamento())
        
        # descarrega (60%)
        energia_descarregada = b.descarrega_bateria(1.4*0.6)
        self.assertEqual(1.4*0.6, energia_descarregada)
        self.assertAlmostEqual(20, b.get_soc(), 2)

        # carrega (60%)
        energia_carregada = b.carrega_bateria(1.4)
        self.assertEqual(1.4*0.6, energia_carregada)
        self.assertAlmostEqual(80, b.get_soc(), 2)
        self.assertEqual(1, b.get_ciclos_carregamento()) # 80 + 60 = 140%

        # descarrega (60%)
        energia_descarregada = b.descarrega_bateria(1.4*0.6)
        self.assertEqual(1.4*0.6, energia_descarregada)
        self.assertAlmostEqual(20, b.get_soc(), 2)

        # carrega (60%)
        energia_carregada = b.carrega_bateria(1.4)
        self.assertEqual(1.4*0.6, energia_carregada)
        self.assertAlmostEqual(80, b.get_soc(), 2)
        self.assertEqual(2, b.get_ciclos_carregamento()) # 80 + 60 + 60 = 200%