import unittest
import time
from src.classes import Niveau
from src.solveurs import SolveurRetourArriere, SolveurBFS

class TestSolveurs(unittest.TestCase):
    def setUp(self):
        # Niveau simple pour les tests
        self.contenu_niveau_simple = """
#####
#   #
#@$ #
##. #
#####
"""
        self.niveau_simple = Niveau(contenu=self.contenu_niveau_simple)
    
    def test_solveur_bfs(self):
        """Test la résolution avec BFS"""
        solveur = SolveurBFS(self.niveau_simple)
        solution = solveur.resoudre()
        
        # Vérifier que la solution a été trouvée
        self.assertIsNotNone(solution)
        self.assertGreater(len(solution), 0)
        
        # Appliquer la solution pour vérifier qu'elle mène à la victoire
        niveau_test = Niveau(contenu=self.contenu_niveau_simple)
        directions = {
            'H': (0, -1),
            'B': (0, 1),
            'G': (-1, 0),
            'D': (1, 0)
        }
        
        for mouvement in solution:
            if mouvement in directions:
                dx, dy = directions[mouvement]
                niveau_test.deplacer_joueur(dx, dy)
        
        # Vérifier que la solution mène à la victoire
        self.assertTrue(niveau_test.verifier_victoire())
    
    def test_solveur_backtracking(self):
        """Test la résolution avec backtracking"""
        solveur = SolveurRetourArriere(self.niveau_simple)
        solution = solveur.resoudre(profondeur_max=50)
        
        # Vérifier que la solution a été trouvée
        self.assertIsNotNone(solution)
        self.assertGreater(len(solution), 0)
        
        # Appliquer la solution pour vérifier qu'elle mène à la victoire
        niveau_test = Niveau(contenu=self.contenu_niveau_simple)
        directions = {
            'H': (0, -1),
            'B': (0, 1),
            'G': (-1, 0),
            'D': (1, 0)
        }
        
        for mouvement in solution:
            if mouvement in directions:
                dx, dy = directions[mouvement]
                niveau_test.deplacer_joueur(dx, dy)
        
        # Vérifier que la solution mène à la victoire
        self.assertTrue(niveau_test.verifier_victoire())
    
    def test_comparaison_performance(self):
        """Compare les performances des deux solveurs"""
        # Mesure du temps pour BFS
        debut = time.time()
        solveur_bfs = SolveurBFS(self.niveau_simple)
        solution_bfs = solveur_bfs.resoudre()
        temps_bfs = time.time() - debut
        
        # Mesure du temps pour backtracking
        debut = time.time()
        solveur_bt = SolveurRetourArriere(self.niveau_simple)
        solution_bt = solveur_bt.resoudre(profondeur_max=50)
        temps_bt = time.time() - debut
        
        # Les deux solutions devraient être valides
        self.assertIsNotNone(solution_bfs)
        self.assertIsNotNone(solution_bt)
        
        # Comparer les longueurs des solutions
        print(f"Longueur BFS: {len(solution_bfs)}, Temps: {temps_bfs:.5f}s")
        print(f"Longueur Backtracking: {len(solution_bt)}, Temps: {temps_bt:.5f}s")
        
        # Note: ce n'est pas un vrai test, juste des informations comparatives
        # On ne vérifie pas vraiment une condition spécifique ici

if __name__ == '__main__':
    unittest.main()
