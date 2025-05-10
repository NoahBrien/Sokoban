import unittest
from src.classes import Caisse

class TestCaisse(unittest.TestCase):
    def test_creation(self):
        """Test la création d'une caisse"""
        caisse = Caisse(5, 6)
        self.assertEqual(caisse.x, 5)
        self.assertEqual(caisse.y, 6)
        self.assertFalse(caisse.sur_cible)
    
    def test_sur_cible(self):
        """Test la modification de l'état sur cible"""
        caisse = Caisse(1, 2)
        caisse.sur_cible = True
        self.assertTrue(caisse.sur_cible)

if __name__ == '__main__':
    unittest.main()
