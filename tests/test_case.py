import unittest
from src.classes import Case

class TestCase(unittest.TestCase):
    def test_creation(self):
        """Test la création d'une case"""
        case = Case(3, 4, 'mur')
        self.assertEqual(case.x, 3)
        self.assertEqual(case.y, 4)
        self.assertEqual(case.type, 'mur')
    
    def test_type_valide(self):
        """Test les types de case valides"""
        types_valides = ['mur', 'sol', 'cible']
        for type_case in types_valides:
            case = Case(0, 0, type_case)
            self.assertEqual(case.type, type_case)

if __name__ == '__main__':
    unittest.main()
