import unittest
from unittest.mock import patch, mock_open, MagicMock
import pygame
import os
import shutil
import tempfile
import json
import sys

# Add the project root to sys.path to ensure src modules can be found
PROJECT_ROOT_FOR_TESTS = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, PROJECT_ROOT_FOR_TESTS)

from src import constantes as C
from src.classes import Niveau, Joueur, Caisse, Case, \
    ElementJeu  # Ensure these are imported after sys.path modification
from src.editeur import EditeurNiveaux
from src.solveurs import SolveurBFS
from src.jeu import Jeu
from src.ui_elements import Bouton, Slider
from src.utilitaires import (
    sauvegarder_progression, charger_progression,
    sauvegarder_niveau_personnalise_en_fichier,
    obtenir_liste_niveaux_defaut, obtenir_chemins_niveaux_personnalises
)

# Helper: Sample level strings (cleaned to avoid leading/trailing newlines in content)
LEVEL_SIMPLE_SOLVABLE = """###
#@.#
#$ #
###"""

LEVEL_SIMPLE_UNSOLVABLE = """###
#@$#
####"""

LEVEL_COMPLEX_SOLVABLE = """#####
#@  #
# $ #
# . #
#####"""

LEVEL_NO_BOXES_TARGETS = """#####
#   #
# @ #
#   #
#####"""

LEVEL_PUSH_TO_SOL = """###
#@ #
#$ #
#  #
####"""


class TestElementJeu(unittest.TestCase):
    def setUp(self):
        self.element = ElementJeu(1, 2)

    def test_init(self):
        self.assertEqual(self.element.grid_x, 1)
        self.assertEqual(self.element.grid_y, 2)
        self.assertEqual(self.element.pixel_x, 1 * C.TAILLE_CASE)
        self.assertEqual(self.element.pixel_y, 2 * C.TAILLE_CASE)
        self.assertFalse(self.element.is_moving)

    def test_start_move(self):
        self.element.start_move(3, 4, C.TAILLE_CASE, 10)
        self.assertTrue(self.element.is_moving)
        self.assertEqual(self.element.animation_steps_left, 10)
        self.assertEqual(self.element.target_pixel_x, 3 * C.TAILLE_CASE)
        self.assertEqual(self.element.target_pixel_y, 4 * C.TAILLE_CASE)

    def test_update_animation(self):
        self.element.start_move(1, 3, C.TAILLE_CASE, 2)  # Move one step down
        self.assertTrue(self.element.update_animation(C.TAILLE_CASE))  # Step 1
        self.assertEqual(self.element.animation_steps_left, 1)
        self.assertNotEqual(self.element.pixel_y, 3 * C.TAILLE_CASE)  # Still moving

        self.assertFalse(self.element.update_animation(C.TAILLE_CASE))  # Step 2 (final)
        self.assertEqual(self.element.animation_steps_left, 0)
        self.assertFalse(self.element.is_moving)
        self.assertEqual(self.element.pixel_y, 3 * C.TAILLE_CASE)
        self.assertEqual(self.element.grid_y, 3)

    def test_set_grid_position_instantly(self):
        self.element.set_grid_position_instantly(5, 5)
        self.assertEqual(self.element.grid_x, 5)
        self.assertEqual(self.element.grid_y, 5)
        self.assertEqual(self.element.pixel_x, 5 * C.TAILLE_CASE)
        self.assertFalse(self.element.is_moving)


class TestNiveau(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()

    @classmethod
    def tearDownClass(cls):
        pygame.quit()

    def setUp(self):
        self.niveau = Niveau(nom_fichier_ou_contenu=LEVEL_SIMPLE_SOLVABLE, est_contenu_direct=True)

    def test_chargement_contenu_direct(self):
        self.assertIsNotNone(self.niveau.joueur)
        self.assertEqual(self.niveau.joueur.grid_x, 1)
        self.assertEqual(self.niveau.joueur.grid_y, 1)
        self.assertEqual(len(self.niveau.caisses), 1)
        self.assertEqual(self.niveau.caisses[0].grid_x, 1)
        self.assertEqual(self.niveau.caisses[0].grid_y, 2)
        self.assertEqual(len(self.niveau.cibles), 1)
        self.assertEqual(self.niveau.cibles[0], (2, 1))
        self.assertEqual(self.niveau.largeur, 4)
        self.assertEqual(self.niveau.hauteur, 4)

    def test_chargement_fichier_inexistant(self):
        niv = Niveau(nom_fichier_ou_contenu="fichier_qui_n_existe_pas.txt")
        self.assertIsNotNone(niv.joueur)
        self.assertEqual(niv.largeur, 4)
        self.assertEqual(niv.hauteur, 3)

    def test_mouvement_joueur_libre(self):
        self.assertTrue(self.niveau.deplacer_joueur(1, 0, C.TAILLE_CASE))
        self.assertEqual(self.niveau.joueur.grid_x, 2)
        self.assertEqual(self.niveau.joueur.grid_y, 1)

    def test_mouvement_joueur_mur(self):
        self.assertFalse(self.niveau.deplacer_joueur(0, -1, C.TAILLE_CASE))
        self.assertEqual(self.niveau.joueur.grid_x, 1)
        self.assertEqual(self.niveau.joueur.grid_y, 1)

    def test_pousser_caisse_espace_libre(self):
        niv = Niveau(nom_fichier_ou_contenu=LEVEL_PUSH_TO_SOL, est_contenu_direct=True)
        caisse = niv.caisses[0]
        self.assertEqual(niv.joueur.grid_x, 1)
        self.assertEqual(niv.joueur.grid_y, 1)
        self.assertEqual(caisse.grid_x, 1)
        self.assertEqual(caisse.grid_y, 2)

        target_behind_box_case = niv.cases.get((1, 3))
        self.assertIsNotNone(target_behind_box_case, "Case behind box should exist")
        self.assertEqual(target_behind_box_case.type_case, C.SOL, "Space behind box should be SOL")

        move_successful = niv.deplacer_joueur(0, 1, C.TAILLE_CASE)
        self.assertTrue(move_successful, "Player push should be successful")

        self.assertEqual(niv.joueur.grid_x, 1)
        self.assertEqual(niv.joueur.grid_y, 2)
        self.assertEqual(caisse.grid_x, 1)
        self.assertEqual(caisse.grid_y, 3)

    def test_pousser_caisse_mur(self):
        niv = Niveau(nom_fichier_ou_contenu=LEVEL_SIMPLE_UNSOLVABLE, est_contenu_direct=True)

        self.assertEqual(niv.joueur.grid_x, 1)
        self.assertEqual(niv.joueur.grid_y, 1)
        self.assertEqual(niv.caisses[0].grid_x, 2)
        self.assertEqual(niv.caisses[0].grid_y, 1)

        self.assertFalse(niv.deplacer_joueur(1, 0, C.TAILLE_CASE))

        self.assertEqual(niv.joueur.grid_x, 1)
        self.assertEqual(niv.joueur.grid_y, 1)
        self.assertEqual(niv.caisses[0].grid_x, 2)
        self.assertEqual(niv.caisses[0].grid_y, 1)

    def test_victoire(self):
        win_level_str = "##@##\n##$##\n##.##\n#####"
        win_niv = Niveau(nom_fichier_ou_contenu=win_level_str, est_contenu_direct=True)
        self.assertFalse(win_niv.verifier_victoire())

        win_niv.deplacer_joueur(0, 1, C.TAILLE_CASE)
        while win_niv.update_animations_niveau(C.TAILLE_CASE): pass

        self.assertTrue(win_niv.verifier_victoire())

    def test_pas_victoire_caisse_pas_sur_cible(self):
        self.assertFalse(self.niveau.verifier_victoire())

    def test_annuler_mouvement_joueur(self):
        initial_player_x = self.niveau.joueur.grid_x
        initial_player_y = self.niveau.joueur.grid_y
        self.assertEqual(initial_player_x, 1)
        self.assertEqual(initial_player_y, 1)

        self.assertTrue(self.niveau.deplacer_joueur(1, 0, C.TAILLE_CASE), "Move should be successful")

        self.assertEqual(self.niveau.joueur.grid_x, 2, "Player should have moved to x=2 after deplacer_joueur")
        self.assertEqual(self.niveau.joueur.grid_y, 1, "Player should have moved to y=1 after deplacer_joueur")

        self.niveau.annuler_dernier_mouvement()
        self.assertEqual(self.niveau.joueur.grid_y, initial_player_y, "Undo failed to restore player y")

    def test_annuler_poussee_caisse(self):
        niv_push = Niveau(nom_fichier_ou_contenu=LEVEL_PUSH_TO_SOL, est_contenu_direct=True)
        caisse_push = niv_push.caisses[0]
        orig_j_x_p, orig_j_y_p = niv_push.joueur.grid_x, niv_push.joueur.grid_y
        orig_c_x_p, orig_c_y_p = caisse_push.grid_x, caisse_push.grid_y

        self.assertTrue(niv_push.deplacer_joueur(0, 1, C.TAILLE_CASE), "Push should be successful for undo test")

        self.assertEqual(niv_push.joueur.grid_x, 1)
        self.assertEqual(niv_push.joueur.grid_y, 2, "Player y should be 2 after push")
        self.assertEqual(caisse_push.grid_x, 1)
        self.assertEqual(caisse_push.grid_y, 3, "Box y should be 3 after push")

        niv_push.annuler_dernier_mouvement()

        self.assertEqual(niv_push.joueur.grid_x, orig_j_x_p, "Undo failed to restore player x after push")

    def test_get_etat_pour_solveur(self):
        etat = self.niveau.get_etat_pour_solveur()
        self.assertEqual(etat, ((1, 1), ((1, 2),)))

    def test_appliquer_etat_solveur(self):
        nouvel_etat = ((2, 2), ((3, 3),))
        self.niveau.appliquer_etat_solveur(nouvel_etat)
        self.assertEqual(self.niveau.joueur.grid_x, 2)
        self.assertEqual(self.niveau.joueur.grid_y, 2)
        self.assertEqual(self.niveau.caisses[0].grid_x, 3)
        self.assertEqual(self.niveau.caisses[0].grid_y, 3)

    def test_reinitialiser(self):
        self.niveau.deplacer_joueur(1, 0, C.TAILLE_CASE)
        self.niveau.reinitialiser()
        self.assertEqual(self.niveau.joueur.grid_x, 1)
        self.assertEqual(self.niveau.joueur.grid_y, 1)
        self.assertEqual(len(self.niveau.mouvements_historique), 0)


class TestSolveurBFS(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()

    @classmethod
    def tearDownClass(cls):
        pygame.quit()

    def setUp(self):
        self.niveau_solvable = Niveau(nom_fichier_ou_contenu=LEVEL_COMPLEX_SOLVABLE, est_contenu_direct=True)
        self.niveau_unsolvable = Niveau(nom_fichier_ou_contenu=LEVEL_SIMPLE_UNSOLVABLE, est_contenu_direct=True)

    def test_resoudre_simple_solvable(self):
        etat_initial = self.niveau_solvable.get_etat_pour_solveur()
        solveur = SolveurBFS(etat_initial)
        solution, iterations = solveur.resoudre(self.niveau_solvable)
        self.assertIsNotNone(solution)
        self.assertTrue(len(solution) > 0)

    def test_resoudre_simple_unsolvable(self):
        etat_initial = self.niveau_unsolvable.get_etat_pour_solveur()
        solveur = SolveurBFS(etat_initial)
        solution, iterations = solveur.resoudre(self.niveau_unsolvable)
        self.assertIsNone(solution)

    def test_resoudre_etat_initial_none(self):
        solveur = SolveurBFS(None)
        solution, iterations = solveur.resoudre(self.niveau_solvable)
        self.assertIsNone(solution)
        self.assertEqual(iterations, 0)

    def test_resoudre_no_boxes_no_targets(self):
        niv = Niveau(nom_fichier_ou_contenu=LEVEL_NO_BOXES_TARGETS, est_contenu_direct=True)
        etat_initial = niv.get_etat_pour_solveur()
        solveur = SolveurBFS(etat_initial)
        solution, iterations = solveur.resoudre(niv)
        self.assertIsNotNone(solution)
        self.assertEqual(len(solution), 0)


class TestEditeurNiveaux(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()

    @classmethod
    def tearDownClass(cls):
        pygame.quit()

    def setUp(self):
        self.mock_jeu_principal = MagicMock()
        self.mock_jeu_principal.taille_case_effective = C.TAILLE_CASE
        self.mock_jeu_principal.interface_graphique.font_menu = pygame.font.Font(None, 20)
        self.mock_jeu_principal.interface_graphique.images_base = {}

        self.editeur = EditeurNiveaux(jeu_principal_ref=self.mock_jeu_principal)
        self.editeur.jeu_principal = self.mock_jeu_principal

    def test_init(self):
        self.assertEqual(self.editeur.largeur_grille, 15)
        self.assertEqual(self.editeur.hauteur_grille, 10)
        self.assertEqual(self.editeur.element_selectionne, C.MUR)
        self.assertTrue(all(c == C.SOL for row in self.editeur.grille for c in row))

    def test_definir_taille_grille(self):
        self.editeur.definir_taille_grille(20, 12)
        self.assertEqual(self.editeur.largeur_grille, 20)
        self.assertEqual(self.editeur.hauteur_grille, 12)
        self.mock_jeu_principal._adapter_taille_fenetre_pour_niveau.assert_called_once()

    def test_placer_element(self):
        self.editeur.element_selectionne = C.MUR
        self.editeur.placer_element(0, 0)
        self.assertEqual(self.editeur.grille[0][0], C.MUR)

        self.editeur.element_selectionne = C.JOUEUR
        self.editeur.placer_element(1, 1)
        self.assertEqual(self.editeur.grille[1][1], C.JOUEUR)

        self.editeur.placer_element(2, 2)
        self.assertEqual(self.editeur.grille[1][1], C.SOL)
        self.assertEqual(self.editeur.grille[2][2], C.JOUEUR)

    def test_placer_joueur_sur_cible(self):
        self.editeur.element_selectionne = C.CIBLE
        self.editeur.placer_element(1, 0)
        self.assertEqual(self.editeur.grille[0][1], C.CIBLE)

        self.editeur.element_selectionne = C.JOUEUR
        self.editeur.placer_element(1, 0)
        self.assertEqual(self.editeur.grille[0][1], C.JOUEUR_SUR_CIBLE)

    def test_get_contenu_niveau_str(self):
        self.editeur.grille = [[C.MUR, C.MUR], [C.JOUEUR, C.SOL]]
        self.editeur.largeur_grille = 2
        self.editeur.hauteur_grille = 2
        expected_str = "##\n@"
        self.assertEqual(self.editeur.get_contenu_niveau_str(), expected_str)

    def test_verifier_conditions_base(self):
        self.assertFalse(self.editeur.verifier_conditions_base())
        self.assertIn("Joueur requis", self.editeur.message_info)

        self.editeur.element_selectionne = C.JOUEUR
        self.editeur.placer_element(1, 1)
        self.assertTrue(self.editeur.verifier_conditions_base(), self.editeur.message_info)

        self.editeur.element_selectionne = C.CAISSE
        self.editeur.placer_element(2, 2)
        self.editeur.verifier_conditions_base()
        self.assertIn("Info: Caisses sans cibles.", self.editeur.message_info)

        self.editeur.element_selectionne = C.CIBLE
        self.editeur.placer_element(3, 3)
        self.assertTrue(self.editeur.verifier_conditions_base(), self.editeur.message_info)

    @patch('src.editeur.sauvegarder_niveau_personnalise_en_fichier')
    @patch('src.editeur.solveurs.SolveurBFS.resoudre')
    def test_sauvegarder_niveau(self, mock_solveur_resoudre, mock_sauvegarder_fichier):
        mock_solveur_resoudre.return_value = (['D'], 1)
        mock_sauvegarder_fichier.return_value = True

        self.editeur.nom_niveau_en_cours = "TestSave"
        self.editeur.element_selectionne = C.JOUEUR
        self.editeur.placer_element(0, 0)

        self.assertTrue(self.editeur.sauvegarder_niveau())
        mock_sauvegarder_fichier.assert_called_once()
        args, _ = mock_sauvegarder_fichier.call_args
        self.assertEqual(args[0], "TestSave")
        self.assertIn(C.JOUEUR, args[1])

    def test_tester_niveau(self):
        self.editeur.element_selectionne = C.JOUEUR
        self.editeur.placer_element(0, 0)
        self.editeur.tester_niveau()
        self.mock_jeu_principal.charger_niveau_temporaire_pour_test.assert_called_once()


class TestUtilitaires(unittest.TestCase):
    def setUp(self):
        self.temp_dir_obj = tempfile.TemporaryDirectory()
        self.temp_dir = self.temp_dir_obj.name

        self.progression_file = os.path.join(self.temp_dir, "progression.json")
        self.niveaux_perso_dir_abs = os.path.join(self.temp_dir, "niveaux_perso")
        os.makedirs(self.niveaux_perso_dir_abs, exist_ok=True)

        self.patcher_sauvegardes = patch('src.constantes.CHEMIN_SAUVEGARDES', self.temp_dir + os.sep)
        self.patcher_niveaux_perso = patch('src.constantes.CHEMIN_NIVEAUX_PERSO', self.niveaux_perso_dir_abs + os.sep)

        self.patcher_sauvegardes.start()
        self.patcher_niveaux_perso.start()

    def tearDown(self):
        self.patcher_sauvegardes.stop()
        self.patcher_niveaux_perso.stop()
        self.temp_dir_obj.cleanup()

    def test_sauvegarder_charger_progression(self):
        data = {"joueur": {"nom": "Test Player", "niveaux_completes": ["lvl1"]},
                "scores": {"lvl1": {"mouvements": 10, "temps": 60}},
                "options_jeu": {"volume_son": 0.5, "textures_active": False}}
        sauvegarder_progression(data)
        self.assertTrue(os.path.exists(self.progression_file))

        loaded_data = charger_progression()
        self.assertEqual(loaded_data["joueur"]["nom"], "Test Player")
        self.assertEqual(loaded_data["options_jeu"]["volume_son"], 0.5)

    def test_charger_progression_inexistante_ou_corrompue(self):
        loaded_data = charger_progression()
        self.assertEqual(loaded_data["joueur"]["nom"], "Joueur1")
        self.assertEqual(loaded_data["options_jeu"]["volume_son"], 1.0)

        with open(self.progression_file, 'w') as f:
            f.write("ceci n'est pas du json")
        loaded_data = charger_progression()
        self.assertEqual(loaded_data["joueur"]["nom"], "Joueur1")
        self.assertEqual(loaded_data["options_jeu"]["volume_son"], 1.0)

    def test_sauvegarder_niveau_personnalise(self):
        nom_niveau = "Mon Super Niveau Perso"
        contenu = "@.#"
        self.assertTrue(sauvegarder_niveau_personnalise_en_fichier(nom_niveau, contenu))

        expected_filename = "Mon_Super_Niveau_Perso.txt"
        expected_filepath = os.path.join(self.niveaux_perso_dir_abs, expected_filename)
        self.assertTrue(os.path.exists(expected_filepath))

        with open(expected_filepath, 'r') as f:
            self.assertEqual(f.read(), contenu)

    def test_obtenir_chemins_niveaux_personnalises(self):
        expected_filename1 = "Perso1.txt"
        expected_filename2 = "Perso2.txt"

        self.assertTrue(sauvegarder_niveau_personnalise_en_fichier("Perso1", "P"))
        self.assertTrue(sauvegarder_niveau_personnalise_en_fichier("Perso2", "P"))

        paths = obtenir_chemins_niveaux_personnalises()

        self.assertEqual(len(paths), 2,
                         f"Expected 2 paths, got {len(paths)}. Contents of '{self.niveaux_perso_dir_abs}': {os.listdir(self.niveaux_perso_dir_abs)}")

        path_basenames = [os.path.basename(p) for p in paths]
        self.assertIn(expected_filename1, path_basenames)
        self.assertIn(expected_filename2, path_basenames)


class TestUIElements(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()

    @classmethod
    def tearDownClass(cls):
        pygame.quit()

    def setUp(self):
        self.font = pygame.font.Font(None, 24)

    def test_bouton_init_et_clic(self):
        bouton = Bouton(10, 20, 100, 50, "Click Me", font=self.font, action="test_action")
        self.assertEqual(bouton.rect, pygame.Rect(10, 20, 100, 50))
        self.assertEqual(bouton.texte, "Click Me")
        self.assertEqual(bouton.action, "test_action")

        self.assertEqual(bouton.verifier_clic((50, 30)), "test_action")
        self.assertIsNone(bouton.verifier_clic((0, 0)))

    def test_slider_init_et_valeur(self):
        slider = Slider(10, 10, 200, 10, 0, 100, 50, label="Volume", action_on_change="set_volume")
        self.assertEqual(slider.current_val, 50)

        slider.current_val = 75
        self.assertEqual(slider.current_val, 75)
        expected_handle_center_x = 10 + 0.75 * 200
        self.assertEqual(slider.rect_handle.centerx, expected_handle_center_x)

        slider.current_val = 200
        self.assertEqual(slider.current_val, 100)

    @patch('pygame.mouse.get_pos')
    def test_slider_handle_event_drag(self, mock_mouse_get_pos):
        slider = Slider(0, 0, 100, 10, 0, 1, 0.5, action_on_change="vol_change")

        mock_mouse_get_pos.return_value = (10, 5)
        event_down = pygame.event.Event(pygame.MOUSEBUTTONDOWN, {'button': 1, 'pos': (10, 5)})
        action, value = slider.handle_event(event_down, (10, 5))

        self.assertTrue(slider.dragging)
        self.assertEqual(action, "vol_change")
        self.assertAlmostEqual(value, 0.1)

        mock_mouse_get_pos.return_value = (80, 5)
        event_motion = pygame.event.Event(pygame.MOUSEMOTION, {'buttons': (1, 0, 0), 'pos': (80, 5), 'rel': (70, 0)})
        action, value = slider.handle_event(event_motion, (80, 5))

        self.assertEqual(action, "vol_change")
        self.assertAlmostEqual(value, 0.8)

        event_up = pygame.event.Event(pygame.MOUSEBUTTONUP, {'button': 1, 'pos': (80, 5)})
        action, value = slider.handle_event(event_up, (80, 5))
        self.assertFalse(slider.dragging)
        self.assertEqual(action, "vol_change")
        self.assertAlmostEqual(value, 0.8)


class TestJeu(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()
        cls.patcher_ig_afficher = patch('src.interface.InterfaceGraphique.afficher_menu_principal')
        cls.patcher_ig_zoomees = patch('src.interface.InterfaceGraphique._regenerer_images_zoomees')
        cls.patcher_ig_icon = patch('pygame.display.set_icon')
        cls.patcher_charger_images = patch('src.utilitaires.charger_images_sokoban',
                                           return_value={C.IMG_ICONE: MagicMock()})
        cls.patcher_charger_sons = patch('src.utilitaires.charger_sons_sokoban',
                                         return_value={"deplacement": MagicMock(),
                                                       "pousse": MagicMock(),
                                                       "victoire": MagicMock()})

        cls.mock_ig_afficher = cls.patcher_ig_afficher.start()
        cls.mock_ig_zoomees = cls.patcher_ig_zoomees.start()
        cls.mock_ig_icon = cls.patcher_ig_icon.start()
        cls.mock_charger_images = cls.patcher_charger_images.start()
        cls.mock_charger_sons = cls.patcher_charger_sons.start()

    @classmethod
    def tearDownClass(cls):
        cls.patcher_ig_afficher.stop()
        cls.patcher_ig_zoomees.stop()
        cls.patcher_ig_icon.stop()
        cls.mock_charger_images.stop()
        cls.mock_charger_sons.stop()
        pygame.quit()

    def setUp(self):
        self.patcher_save_prog = patch('src.utilitaires.sauvegarder_progression')
        self.patcher_load_prog = patch('src.utilitaires.charger_progression')
        self.mock_save_prog = self.patcher_save_prog.start()

        self.default_progression = {
            "joueur": {"nom": "TestJoueur", "niveaux_completes": []},
            "scores": {},
            "options_jeu": {"volume_son": 1.0, "textures_active": True}
        }
        self.mock_load_prog = self.patcher_load_prog.start()
        self.mock_load_prog.return_value = self.default_progression

        self.patcher_util_listdir = patch('src.utilitaires.os.listdir')
        self.mock_util_listdir = self.patcher_util_listdir.start()

        def listdir_side_effect_for_jeu(path):
            if path == C.CHEMIN_NIVEAUX_DEFAUT:
                return ['map1.txt']
            return os.listdir(path)  # Call original for other paths (e.g. for TestUtilitaires temp dirs)
            # This assumes os.listdir is imported as 'os.listdir' in utilitaires.
            # If it's 'from os import listdir', then patch 'src.utilitaires.listdir'.
            # Or, more robustly, stop this patch in tearDown and TestUtilitaires has its own setup.
            # For now, this should work if TestUtilitaires doesn't rely on os.listdir directly after TestJeu runs.
            # Let's make it safer:
            if hasattr(os, 'actual_listdir'):  # Check if we've already wrapped it
                return os.actual_listdir(path)
            return []  # Default for Jeu test if not CHEMIN_NIVEAUX_DEFAUT

        # To be absolutely safe and avoid interference between TestJeu and TestUtilitaires,
        # it's better if TestJeu's listdir mock is very specific or that TestUtilitaires
        # doesn't rely on a global os.listdir state that TestJeu might have altered.
        # The current patch in TestUtilitaires for C.CHEMIN_NIVEAUX_PERSO handles its own needs.
        # The TestJeu patch should only affect C.CHEMIN_NIVEAUX_DEFAUT.

        self.mock_util_listdir.side_effect = lambda p: ['map1.txt'] if p == C.CHEMIN_NIVEAUX_DEFAUT else []

        self.jeu = Jeu()

    def tearDown(self):
        self.patcher_save_prog.stop()
        self.patcher_load_prog.stop()
        self.patcher_util_listdir.stop()

    def test_init_options(self):
        self.assertEqual(self.jeu.volume_son, 1.0)
        self.assertTrue(self.jeu.textures_active)
        self.assertEqual(self.jeu.etat_jeu, C.ETAT_MENU_PRINCIPAL)

    def test_set_volume(self):
        self.jeu.set_volume(0.5)
        self.assertEqual(self.jeu.volume_son, 0.5)
        self.assertTrue(self.jeu.progression_joueur["options_jeu"]["volume_son"] == 0.5)

        self.jeu.set_volume(1.5)
        self.assertEqual(self.jeu.volume_son, 1.0)

    def test_toggle_textures(self):
        initial_textures_state = self.jeu.textures_active
        self.jeu.toggle_textures()
        self.assertEqual(self.jeu.textures_active, not initial_textures_state)
        self.assertEqual(self.jeu.progression_joueur["options_jeu"]["textures_active"], not initial_textures_state)

    @patch('src.classes.Niveau._charger_fichier')
    def test_charger_niveau_par_specification(self, mock_charger_fichier):
        spec = {"index_global": 0, "nom_affiche": "Test Level", "data": "dummy_path.txt"}
        self.jeu.charger_niveau_par_specification(spec)
        self.assertIsNotNone(self.jeu.niveau_actuel)
        self.assertEqual(self.jeu.nom_niveau_affiche, "Test Level")
        self.assertEqual(self.jeu.nb_mouvements, 0)

    @patch('src.classes.Niveau._charger_contenu')
    def test_charger_niveau_temporaire_pour_test(self, mock_charger_contenu):
        mock_editeur = MagicMock()
        contenu_str = "@."
        self.jeu.charger_niveau_temporaire_pour_test(contenu_str, mock_editeur)
        self.assertTrue(self.jeu.mode_test_editeur)
        self.assertEqual(self.jeu.editeur_actif, mock_editeur)
        self.assertEqual(self.jeu.etat_jeu, C.ETAT_JEU)
        mock_charger_contenu.assert_called_with(contenu_str)

    def test_enregistrer_score(self):
        self.jeu.niveau_actuel = Niveau(nom_fichier_ou_contenu=LEVEL_SIMPLE_SOLVABLE, est_contenu_direct=True)
        self.jeu.nom_niveau_affiche = "SimpleSolvable"
        self.jeu.nb_mouvements = 10
        self.jeu.temps_ecoule_total_secondes = 120.5
        self.jeu.mode_test_editeur = False

        self.jeu.enregistrer_score()

        self.assertIn("SimpleSolvable", self.jeu.progression_joueur["scores"])
        score_entry = self.jeu.progression_joueur["scores"]["SimpleSolvable"]
        self.assertEqual(score_entry["mouvements"], 10)
        self.assertEqual(score_entry["temps"], 120.5)
        self.assertIn("SimpleSolvable", self.jeu.progression_joueur["joueur"]["niveaux_completes"])

        self.jeu.nb_mouvements = 5
        self.jeu.temps_ecoule_total_secondes = 60.0
        self.jeu.enregistrer_score()
        score_entry = self.jeu.progression_joueur["scores"]["SimpleSolvable"]
        self.assertEqual(score_entry["mouvements"], 5)
        self.assertEqual(score_entry["temps"], 60.0)

    @patch('pygame.display.flip')
    @patch('src.solveurs.SolveurBFS.resoudre')
    def test_demander_indice(self, mock_bfs_resoudre, mock_flip):
        with patch.object(Niveau, 'dessiner', MagicMock()):
            self.jeu.niveau_actuel = Niveau(nom_fichier_ou_contenu=LEVEL_COMPLEX_SOLVABLE, est_contenu_direct=True)
            self.jeu.etat_jeu = C.ETAT_JEU

            mock_bfs_resoudre.return_value = (['D', 'R'], 2)

            self.jeu.demander_indice()

            self.assertIsNotNone(self.jeu.hint_solution_pour_etat_actuel)
            self.assertEqual(self.jeu.hint_solution_pour_etat_actuel, ['D', 'R'])
            self.assertIsNotNone(self.jeu.hint_next_move_display_pos)
            self.assertIn("Droite", self.jeu.hint_message)
            mock_bfs_resoudre.assert_called_once()

    @patch('pygame.display.flip')
    @patch('src.solveurs.SolveurBFS.resoudre')
    def test_lancer_resolution_auto_bfs(self, mock_bfs_resoudre, mock_flip):
        with patch.object(Niveau, 'dessiner', MagicMock()):
            self.jeu.niveau_actuel = Niveau(nom_fichier_ou_contenu=LEVEL_COMPLEX_SOLVABLE, est_contenu_direct=True)
            self.jeu.etat_jeu = C.ETAT_JEU

            mock_bfs_resoudre.return_value = (['D'], 1)
            self.jeu.lancer_resolution_auto("bfs")

            self.assertEqual(self.jeu.etat_jeu, C.ETAT_VISUALISATION_SOLVEUR)
            self.assertFalse(self.jeu.solveur_en_cours)
            self.assertEqual(self.jeu.solveur_solution_pas, ['D'])
            self.assertEqual(self.jeu.solveur_iterations, 1)
            mock_bfs_resoudre.assert_called_once()

    def test_gerer_evenements_quitter(self):
        event_quit = pygame.event.Event(pygame.QUIT)
        self.jeu.fonctionnement = True
        self.gerer_evenements_wrapper_for_test([event_quit])
        self.assertFalse(self.jeu.fonctionnement)

    def gerer_evenements_wrapper_for_test(self, events):
        with patch('pygame.event.get', return_value=events):
            self.jeu.gerer_evenements()


if __name__ == '__main__':
    unittest.main(verbosity=2)