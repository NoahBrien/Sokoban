import unittest
from src.classes import Niveau

class TestNiveau(unittest.TestCase):
    def test_chargement_contenu(self):
        """Test le chargement d'un niveau depuis une chaîne"""
        contenu = """
#####
#.$ #
# @ #
#####
"""
        niveau = Niveau(contenu=contenu)
        self.assertEqual(niveau.largeur, 5)
        self.assertEqual(niveau.hauteur, 4)
        self.assertEqual(len(niveau.caisses), 1)
        self.assertEqual(len(niveau.cibles), 1)
        self.assertIsNotNone(niveau.joueur)
        self.assertEqual(niveau.joueur.x, 2)
        self.assertEqual(niveau.joueur.y, 2)
    
    def test_deplacement_joueur_valide(self):
        """Test un déplacement valide du joueur"""
        contenu = """
#####
#   #
# @ #
#####
"""
        niveau = Niveau(contenu=contenu)
        resultat = niveau.deplacer_joueur(1, 0)  # Déplacement vers la droite
        self.assertTrue(resultat)
        self.assertEqual(niveau.joueur.x, 3)
        self.assertEqual(niveau.joueur.y, 2)
    
    def test_deplacement_joueur_invalide_mur(self):
        """Test un déplacement invalide du joueur contre un mur"""
        contenu = """
#####
#   #
#@  #
#####
"""
        niveau = Niveau(contenu=contenu)
        resultat = niveau.deplacer_joueur(0, -1)  # Déplacement vers le haut (mur)
        self.assertFalse(resultat)
        self.assertEqual(niveau.joueur.x, 1)
        self.assertEqual(niveau.joueur.y, 2)
    
    def test_pousser_caisse(self):
        """Test la poussée d'une caisse"""
        contenu = """
#####
#   #
#@$ #
#####
"""
        niveau = Niveau(contenu=contenu)
        resultat = niveau.deplacer_joueur(1, 0)  # Pousser la caisse
        self.assertTrue(resultat)
        self.assertEqual(niveau.joueur.x, 2)
        self.assertEqual(niveau.joueur.y, 2)
        self.assertEqual(niveau.caisses[0].x, 3)
        self.assertEqual(niveau.caisses[0].y, 2)
    
    def test_pousser_caisse_impossible(self):
        """Test la poussée impossible d'une caisse contre un mur"""
        contenu = """
#####
#   #
#@$##
#####
"""
        niveau = Niveau(contenu=contenu)
        resultat = niveau.deplacer_joueur(1, 0)  # Pousser la caisse (impossible)
        self.assertFalse(resultat)
        self.assertEqual(niveau.joueur.x, 1)
        self.assertEqual(niveau.joueur.y, 2)
        self.assertEqual(niveau.caisses[0].x, 2)
        self.assertEqual(niveau.caisses[0].y, 2)
    
    def test_detection_victoire(self):
        """Test la détection de victoire"""
        contenu = """
#####
#   #
#@*.#
#####
"""
        niveau = Niveau(contenu=contenu)
        # La caisse est déjà sur une cible
        self.assertFalse(niveau.verifier_victoire())  # Il reste une cible vide
        
        # Créons un niveau avec toutes les caisses sur des cibles
        contenu = """
#####
#   #
#@* #
#####
"""
        niveau = Niveau(contenu=contenu)
        self.assertTrue(niveau.verifier_victoire())
    
    def test_annuler_mouvement(self):
        """Test l'annulation d'un mouvement"""
        contenu = """
#####
#   #
#@$ #
#####
"""
        niveau = Niveau(contenu=contenu)
        
        # Effectuer un mouvement, puis l'annuler
        niveau.deplacer_joueur(1, 0)
        self.assertEqual(niveau.joueur.x, 2)
        self.assertEqual(niveau.caisses[0].x, 3)
        
        niveau.annuler_mouvement()
        self.assertEqual(niveau.joueur.x, 1)
        self.assertEqual(niveau.caisses[0].x, 2)

if __name__ == '__main__':
    unittest.main()
