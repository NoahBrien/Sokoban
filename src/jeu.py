import pygame
import time
import os
from . import constantes as C
from . import utilitaires
from . import classes
from . import interface
from . import solveurs


class Jeu:
    def __init__(self):
        self.largeur_fenetre, self.hauteur_fenetre = C.LARGEUR_MENU, C.HAUTEUR_MENU

        self.progression_joueur = utilitaires.charger_progression()
        options_chargees = self.progression_joueur.get("options_jeu", {})
        self.volume_son = float(options_chargees.get("volume_son", 1.0))
        self.textures_active = bool(options_chargees.get("textures_active", True))
        self.son_active = self.volume_son > 0.001

        self.zoom_factor = 1.0
        # Définir taille_case_effective AVANT d'initialiser InterfaceGraphique
        self.taille_case_effective = int(C.TAILLE_CASE * self.zoom_factor)
        # _recalculer_taille_case_effective() sera appelé dans InterfaceGraphique si nécessaire,
        # mais avoir une valeur initiale ici est crucial.

        self.view_offset_x = 0
        self.view_offset_y = 0

        # Maintenant, InterfaceGraphique peut accéder à taille_case_effective
        self.interface_graphique = interface.InterfaceGraphique(self.largeur_fenetre, self.hauteur_fenetre, self)

        self.horloge = pygame.time.Clock();
        self.etat_jeu = C.ETAT_MENU_PRINCIPAL;
        self.fonctionnement = True

        self.niveau_actuel, self.niveau_actuel_index_global, self.nom_niveau_affiche = None, -1, ""
        self.nb_mouvements, self.temps_debut_niveau, self.temps_ecoule_total_secondes = 0, 0, 0

        self.sons = utilitaires.charger_sons_sokoban();
        self.appliquer_volume_sons()

        self.chemins_niveaux_defaut = []
        self.chemins_niveaux_perso = []
        self.rafraichir_listes_niveaux();

        self.victoire_detectee = False
        self.solveur_solution_pas, self.solveur_index_pas_actuel, self.solveur_iterations = None, 0, 0
        self.niveau_pour_visualisation = None
        self.solveur_timer_dernier_pas, self.solveur_delai_entre_pas = 0, 200
        self.solveur_en_cours, self.etat_avant_solveur = False, None
        self.solveur_type_en_cours = ""

        self.editeur_actif, self.mode_test_editeur = None, False
        self.hint_solution_pour_etat_actuel, self.hint_etat_pour_lequel_solution_calculee = None, None
        self.hint_next_move_display_pos, self.hint_message, self.deadlock_message = None, "", ""
        self.animation_active = False
        self.FRAMES_ANIMATION_JOUEUR = int(C.FPS * 0.15)

        # S'assurer que les images zoomées sont initialisées avec la bonne taille au démarrage
        self._recalculer_taille_case_effective()  # Appeler ici pour que _regenerer_images_zoomees soit appelé

    def _recalculer_taille_case_effective(self):
        self.taille_case_effective = int(C.TAILLE_CASE * self.zoom_factor)
        if self.taille_case_effective <= 0: self.taille_case_effective = 1
        # S'assurer que interface_graphique existe avant d'appeler ses méthodes
        if hasattr(self, 'interface_graphique') and self.interface_graphique:
            self.interface_graphique._regenerer_images_zoomees(self.taille_case_effective)

    def appliquer_zoom(self, zoom_direction, pos_souris_ecran_absolue=None):
        old_zoom_factor = self.zoom_factor
        if zoom_direction > 0:
            self.zoom_factor = min(C.ZOOM_MAX, self.zoom_factor + C.ZOOM_STEP)
        else:
            self.zoom_factor = max(C.ZOOM_MIN, self.zoom_factor - C.ZOOM_STEP)
        if abs(self.zoom_factor - old_zoom_factor) > 0.001:
            self._recalculer_taille_case_effective()
            pass

    def appliquer_volume_sons(self):
        if self.sons:
            for cle_son in self.sons:
                if self.sons[cle_son]:
                    self.sons[cle_son].set_volume(self.volume_son if self.son_active else 0.0)

    def set_volume(self, nouveau_volume):
        self.volume_son = max(0.0, min(1.0, float(nouveau_volume)))
        self.son_active = self.volume_son > 0.001
        self.appliquer_volume_sons()
        if "options_jeu" not in self.progression_joueur:
            self.progression_joueur["options_jeu"] = {}
        self.progression_joueur["options_jeu"]["volume_son"] = self.volume_son

    def toggle_textures(self):
        self.textures_active = not self.textures_active
        if "options_jeu" not in self.progression_joueur:
            self.progression_joueur["options_jeu"] = {}
        self.progression_joueur["options_jeu"]["textures_active"] = self.textures_active

    def rafraichir_listes_niveaux(self):
        self.chemins_niveaux_defaut = utilitaires.obtenir_liste_niveaux_defaut();
        self.chemins_niveaux_perso = utilitaires.obtenir_chemins_niveaux_personnalises()
        if hasattr(self, 'interface_graphique') and self.interface_graphique:
            self.interface_graphique.boutons_selection_niveau = [];
            self.interface_graphique.scroll_offset_selection_niveau = 0;
            self.interface_graphique.btn_retour_sel_niveau = None

    def _adapter_taille_fenetre_pour_niveau(self):
        n_l, n_h = C.LARGEUR_MENU, C.HAUTEUR_MENU
        current_taille_case = self.taille_case_effective

        if self.etat_jeu == C.ETAT_JEU and self.niveau_actuel:
            marge_h, marge_v = 100, 120
            contenu_l = self.niveau_actuel.largeur * current_taille_case
            contenu_h = self.niveau_actuel.hauteur * current_taille_case
            n_l = max(C.LARGEUR_FENETRE_JEU, contenu_l + marge_h)
            n_h = max(C.HAUTEUR_FENETRE_JEU, contenu_h + marge_v)
        elif self.etat_jeu == C.ETAT_EDITEUR:
            ed_i = self.interface_graphique.editeur_instance if hasattr(self.interface_graphique,
                                                                        'editeur_instance') else None
            grille_l_ed = ed_i.largeur_grille if ed_i else 15
            grille_h_ed = ed_i.hauteur_grille if ed_i else 10
            marge_ed_ui_d, marge_ed_ui_b = 280, 150
            contenu_l = grille_l_ed * current_taille_case
            contenu_h = grille_h_ed * current_taille_case
            n_l = max(C.LARGEUR_MENU, contenu_l + marge_ed_ui_d + 20)
            n_h = max(C.HAUTEUR_MENU, contenu_h + marge_ed_ui_b + 70)

        n_l = max(n_l, C.LARGEUR_MENU);
        n_h = max(n_h, C.HAUTEUR_MENU)

        if self.largeur_fenetre != n_l or self.hauteur_fenetre != n_h:
            self.largeur_fenetre, self.hauteur_fenetre = n_l, n_h
            if hasattr(self, 'interface_graphique') and self.interface_graphique:  # S'assurer que l'objet existe
                self.interface_graphique.largeur, self.interface_graphique.hauteur = n_l, n_h
                self.interface_graphique.fenetre = pygame.display.set_mode((n_l, n_h))
                if self.etat_jeu == C.ETAT_MENU_PRINCIPAL: self.interface_graphique.boutons_menu = []
                if self.etat_jeu == C.ETAT_SELECTION_NIVEAU: self.interface_graphique.boutons_selection_niveau = []
                if self.etat_jeu == C.ETAT_OPTIONS: self.interface_graphique.elements_options = {"boutons": [],
                                                                                                 "sliders": {}}
                if self.etat_jeu == C.ETAT_EDITEUR and self.interface_graphique.editeur_instance:
                    self.interface_graphique.editeur_instance._creer_boutons_editeur()

    def charger_niveau_par_specification(self, spec_niv):
        self.niveau_actuel_index_global = spec_niv["index_global"]
        self.nom_niveau_affiche = spec_niv["nom_affiche"]
        self.niveau_actuel = classes.Niveau(nom_fichier_ou_contenu=spec_niv["data"])
        self.reinitialiser_etat_niveau();
        self.zoom_factor = 1.0
        self._recalculer_taille_case_effective()
        self.view_offset_x = 0
        self.view_offset_y = 0
        self._adapter_taille_fenetre_pour_niveau()

    def charger_niveau_temporaire_pour_test(self, contenu_str, editeur_ref):
        self.editeur_actif = editeur_ref
        self.mode_test_editeur = True
        self.niveau_actuel = classes.Niveau(nom_fichier_ou_contenu=contenu_str, est_contenu_direct=True)
        self.nom_niveau_affiche = "Test Editeur";
        self.reinitialiser_etat_niveau();
        self.zoom_factor = 1.0
        self._recalculer_taille_case_effective()
        self.view_offset_x = 0
        self.view_offset_y = 0
        self.etat_jeu = C.ETAT_JEU;
        self._adapter_taille_fenetre_pour_niveau()

    def reinitialiser_etat_niveau(self):
        self.nb_mouvements, self.temps_debut_niveau, self.temps_ecoule_total_secondes = 0, time.time(), 0
        self.victoire_detectee = False;
        if hasattr(self, 'interface_graphique'):
            self.interface_graphique.message_victoire_affiche_temps = 0
        if self.niveau_actuel: self.niveau_actuel.reinitialiser()
        self.hint_solution_pour_etat_actuel, self.hint_etat_pour_lequel_solution_calculee = None, None
        self.hint_next_move_display_pos, self.hint_message, self.deadlock_message = None, "", ""
        self.animation_active = False

    def executer(self):
        while self.fonctionnement:
            if self.etat_jeu == C.ETAT_JEU and self.temps_debut_niveau > 0 and not self.victoire_detectee:
                self.temps_ecoule_total_secondes = time.time() - self.temps_debut_niveau
            self.gerer_evenements()
            if self.animation_active and self.etat_jeu == C.ETAT_JEU and self.niveau_actuel:
                self.animation_active = self.niveau_actuel.update_animations_niveau(self.taille_case_effective)
            self.mettre_a_jour();
            self.dessiner();
            self.horloge.tick(C.FPS)
        utilitaires.sauvegarder_progression(self.progression_joueur);

    def demander_indice(self):
        if not self.niveau_actuel or self.victoire_detectee or self.animation_active:
            self.hint_message = "";
            self.hint_next_move_display_pos = None;
            return
        etat_courant_jeu = self.niveau_actuel.get_etat_pour_solveur()
        if not self.hint_solution_pour_etat_actuel or self.hint_etat_pour_lequel_solution_calculee != etat_courant_jeu:
            self.hint_message = "Calcul de l'indice (BFS)...";
            self.hint_next_move_display_pos = None
            self.interface_graphique.afficher_ecran_jeu(self.niveau_actuel, self.nom_niveau_affiche, self.nb_mouvements,
                                                        self.temps_ecoule_total_secondes, self.textures_active,
                                                        self.taille_case_effective,
                                                        self.view_offset_x, self.view_offset_y,
                                                        self.hint_next_move_display_pos, self.hint_message,
                                                        self.deadlock_message)
            pygame.display.flip();
            pygame.event.pump()
            niveau_sim = classes.Niveau(nom_fichier_ou_contenu=self.niveau_actuel.contenu_initial_str,
                                        est_contenu_direct=True)
            if etat_courant_jeu: niveau_sim.appliquer_etat_solveur(etat_courant_jeu)
            solveur = solveurs.SolveurBFS(etat_courant_jeu)
            solution_bfs, _ = solveur.resoudre(niveau_sim)
            self.hint_solution_pour_etat_actuel = solution_bfs
            self.hint_etat_pour_lequel_solution_calculee = etat_courant_jeu
        if self.hint_solution_pour_etat_actuel and len(self.hint_solution_pour_etat_actuel) > 0:
            mvt_sym = self.hint_solution_pour_etat_actuel[0];
            dx, dy, dir_txt = 0, 0, "?"
            if mvt_sym == 'H':
                dx, dy, dir_txt = 0, -1, "Haut"
            elif mvt_sym == 'B':
                dx, dy, dir_txt = 0, 1, "Bas"
            elif mvt_sym == 'G':
                dx, dy, dir_txt = -1, 0, "Gauche"
            elif mvt_sym == 'D':
                dx, dy, dir_txt = 1, 0, "Droite"
            if self.niveau_actuel.joueur:
                self.hint_next_move_display_pos = (
                self.niveau_actuel.joueur.grid_x + dx, self.niveau_actuel.joueur.grid_y + dy)
                self.hint_message = f"Indice: Aller {dir_txt}"
        else:
            self.hint_message = "Aucun indice (BFS)."; self.hint_next_move_display_pos = None; self.hint_solution_pour_etat_actuel = None

    def gerer_evenements(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT: self.fonctionnement = False

            if self.etat_jeu == C.ETAT_OPTIONS:
                self.interface_graphique.gerer_evenements_options(event)
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    self.etat_jeu = C.ETAT_MENU_PRINCIPAL
                    self._adapter_taille_fenetre_pour_niveau()
                continue

            if self.etat_jeu == C.ETAT_JEU or self.etat_jeu == C.ETAT_EDITEUR:
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 4:
                        self.appliquer_zoom(1, event.pos)
                    elif event.button == 5:
                        self.appliquer_zoom(-1, event.pos)

            if self.etat_jeu == C.ETAT_MENU_PRINCIPAL:
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    n_e = self.interface_graphique.gerer_clic_menu_principal(event.pos)
                    if n_e:
                        if n_e == C.ETAT_QUITTER:
                            self.fonctionnement = False
                        else:
                            self.etat_jeu = n_e; self.zoom_factor = 1.0; self._recalculer_taille_case_effective(); self._adapter_taille_fenetre_pour_niveau()
            elif self.etat_jeu == C.ETAT_SELECTION_NIVEAU:
                if event.type == pygame.MOUSEBUTTONDOWN:
                    n_e_a = self.interface_graphique.gerer_clic_selection_niveau(event.pos, event.button)
                    if n_e_a: self.etat_jeu = n_e_a; self.zoom_factor = 1.0; self._recalculer_taille_case_effective(); self._adapter_taille_fenetre_pour_niveau()
                elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    self.etat_jeu = C.ETAT_MENU_PRINCIPAL;
                    self.interface_graphique.boutons_selection_niveau = [];
                    self.interface_graphique.btn_retour_sel_niveau = None;
                    self._adapter_taille_fenetre_pour_niveau()
            elif self.etat_jeu == C.ETAT_JEU:
                if not self.animation_active:
                    if event.type == pygame.KEYDOWN:
                        if event.key != pygame.K_h: self.hint_next_move_display_pos = None; self.hint_message = ""; self.hint_solution_pour_etat_actuel = None
                        if not self.victoire_detectee:
                            key_map = {pygame.K_UP: 'u', pygame.K_w: 'u', pygame.K_z: 'u', pygame.K_DOWN: 'd',
                                       pygame.K_s: 'd', pygame.K_LEFT: 'l', pygame.K_a: 'l', pygame.K_q: 'l',
                                       pygame.K_RIGHT: 'r', pygame.K_d: 'r'}
                            if event.key in key_map:
                                moves = {'u': (0, -1), 'd': (0, 1), 'l': (-1, 0), 'r': (1, 0)}
                                dx_dy = moves[key_map[event.key]]
                                if self.niveau_actuel.deplacer_joueur(*dx_dy, self.taille_case_effective, self.sons,
                                                                      self.FRAMES_ANIMATION_JOUEUR,
                                                                      son_active=self.son_active):
                                    self.animation_active = True;
                                    self.nb_mouvements += 1
                                    etat_apres_mvt = self.niveau_actuel.get_etat_pour_solveur()
                                    if etat_apres_mvt:
                                        _jp, caisses_pt = etat_apres_mvt;
                                        temp_s = solveurs.SolveurRetourArriere(None)
                                        self.deadlock_message = "Attention: Impasse possible !" if temp_s._est_impasse_simple(
                                            caisses_pt, self.niveau_actuel) else ""
                                    else:
                                        self.deadlock_message = ""
                            elif event.key == pygame.K_u:
                                if self.niveau_actuel.annuler_dernier_mouvement():
                                    if self.nb_mouvements > 0: self.nb_mouvements -= 1
                                    self.deadlock_message = ""
                        if event.key == pygame.K_h:
                            self.demander_indice()
                        elif event.key == pygame.K_r:
                            self.reinitialiser_etat_niveau()
                        elif event.key == pygame.K_ESCAPE:
                            if self.mode_test_editeur:
                                self.etat_jeu = C.ETAT_EDITEUR;
                                self.niveau_actuel = None;
                                self.mode_test_editeur = False
                                self.interface_graphique.editeur_instance = self.editeur_actif
                                if self.interface_graphique.editeur_instance: self.interface_graphique.editeur_instance.jeu_principal = self
                                self.editeur_actif = None
                            else:
                                self.etat_jeu = C.ETAT_MENU_PRINCIPAL
                            self.hint_next_move_display_pos = None;
                            self.hint_message = "";
                            self.deadlock_message = "";
                            self.hint_solution_pour_etat_actuel = None;
                            self._adapter_taille_fenetre_pour_niveau()
                        elif event.key == pygame.K_F1:
                            self.lancer_resolution_auto("bfs")
                        elif event.key == pygame.K_F2:
                            self.lancer_resolution_auto("backtracking")
            elif self.etat_jeu == C.ETAT_EDITEUR:
                if not (event.type == pygame.MOUSEBUTTONDOWN and event.button in [4, 5]):
                    self.interface_graphique.gerer_evenement_editeur(event)
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    if not (
                            self.interface_graphique.editeur_instance and self.interface_graphique.editeur_instance.input_nom_actif):
                        self.etat_jeu = C.ETAT_MENU_PRINCIPAL;
                        self.interface_graphique.editeur_instance = None;
                        self.zoom_factor = 1.0;
                        self._recalculer_taille_case_effective();
                        self._adapter_taille_fenetre_pour_niveau()
            elif self.etat_jeu == C.ETAT_SCORES:
                action_res = self.interface_graphique.gerer_evenements_scores(event)
                if action_res == C.ETAT_MENU_PRINCIPAL:
                    self.etat_jeu = C.ETAT_MENU_PRINCIPAL
                    self._adapter_taille_fenetre_pour_niveau()
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    self.etat_jeu = C.ETAT_MENU_PRINCIPAL
                    self.interface_graphique.scroll_offset_scores = 0
                    self._adapter_taille_fenetre_pour_niveau()
            elif self.etat_jeu == C.ETAT_VISUALISATION_SOLVEUR:
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_SPACE:
                        self.avancer_pas_solveur()
                    elif event.key == pygame.K_RETURN:
                        self.terminer_visualisation_solveur_rapidement()
                    elif event.key == pygame.K_ESCAPE:
                        self.etat_jeu = C.ETAT_JEU
                        if self.niveau_actuel and self.etat_avant_solveur: self.niveau_actuel.appliquer_etat_solveur(
                            self.etat_avant_solveur)
                        self.solveur_solution_pas = None;
                        self.niveau_pour_visualisation = None;
                        self.etat_avant_solveur = None;
                        self.solveur_iterations = 0

    def mettre_a_jour(self):
        if self.etat_jeu == C.ETAT_JEU and self.niveau_actuel:
            if not self.animation_active and not self.victoire_detectee:
                if self.niveau_actuel.verifier_victoire():
                    self.victoire_detectee = True;
                    self.hint_next_move_display_pos = None;
                    self.hint_message = "";
                    self.deadlock_message = ""
                    if not self.mode_test_editeur:
                        if self.sons and self.sons.get("victoire") and self.son_active: self.sons["victoire"].play()
                        self.enregistrer_score()
                    else:
                        if self.sons and self.sons.get("victoire") and self.son_active: self.sons["victoire"].play()
        elif self.etat_jeu == C.ETAT_VISUALISATION_SOLVEUR and self.solveur_en_cours:
            pass

    def dessiner(self):
        if self.etat_jeu == C.ETAT_MENU_PRINCIPAL:
            self.interface_graphique.afficher_menu_principal()
        elif self.etat_jeu == C.ETAT_SELECTION_NIVEAU:
            self.interface_graphique.afficher_selection_niveau(self.chemins_niveaux_defaut, self.chemins_niveaux_perso)
        elif self.etat_jeu == C.ETAT_JEU:
            self.interface_graphique.afficher_ecran_jeu(self.niveau_actuel, self.nom_niveau_affiche, self.nb_mouvements,
                                                        self.temps_ecoule_total_secondes, self.textures_active,
                                                        self.taille_case_effective,
                                                        self.view_offset_x, self.view_offset_y,
                                                        self.hint_next_move_display_pos, self.hint_message,
                                                        self.deadlock_message)
        elif self.etat_jeu == C.ETAT_EDITEUR:
            self.interface_graphique.afficher_editeur(self.taille_case_effective, self.view_offset_x,
                                                      self.view_offset_y)

        elif self.etat_jeu == C.ETAT_SCORES:
            scores_tries = dict(sorted(self.progression_joueur.get("scores", {}).items(), key=lambda item: (
            item[1].get('mouvements', float('inf')), item[1].get('temps', float('inf')))))
            self.interface_graphique.afficher_scores(scores_tries)
        elif self.etat_jeu == C.ETAT_OPTIONS:
            self.interface_graphique.afficher_options()
        elif self.etat_jeu == C.ETAT_VISUALISATION_SOLVEUR:
            self.interface_graphique.afficher_visualisation_solveur(self.niveau_pour_visualisation,
                                                                    self.solveur_solution_pas,
                                                                    self.solveur_index_pas_actuel,
                                                                    self.solveur_iterations,
                                                                    self.textures_active,
                                                                    C.TAILLE_CASE)

    def enregistrer_score(self):
        if not self.niveau_actuel or self.mode_test_editeur or not self.nom_niveau_affiche: return
        cle_score_niveau = str(self.nom_niveau_affiche)
        scores_globaux = self.progression_joueur.setdefault("scores", {})
        score_precedent = scores_globaux.get(cle_score_niveau)
        maj_score = False
        if score_precedent is None or \
                self.nb_mouvements < score_precedent.get("mouvements", float('inf')) or \
                (self.nb_mouvements == score_precedent.get("mouvements", float('inf')) and \
                 self.temps_ecoule_total_secondes < score_precedent.get("temps", float('inf'))):
            maj_score = True
        if maj_score:
            scores_globaux[cle_score_niveau] = {"mouvements": self.nb_mouvements,
                                                "temps": round(self.temps_ecoule_total_secondes, 2)}
        joueur_data = self.progression_joueur.setdefault("joueur", {"nom": "Joueur1", "niveaux_completes": []})
        if "niveaux_completes" not in joueur_data: joueur_data["niveaux_completes"] = []
        if cle_score_niveau not in joueur_data["niveaux_completes"]:
            joueur_data["niveaux_completes"].append(cle_score_niveau)

    def passer_au_niveau_suivant_ou_menu(self):
        if self.mode_test_editeur:
            self.etat_jeu = C.ETAT_EDITEUR;
            self.niveau_actuel = None;
            self.mode_test_editeur = False
            self.interface_graphique.editeur_instance = self.editeur_actif
            if self.interface_graphique.editeur_instance:
                self.interface_graphique.editeur_instance.jeu_principal = self
                self.interface_graphique.editeur_instance.message_info = "Test terminé. Retour éditeur."
            self.editeur_actif = None
        else:
            self.etat_jeu = C.ETAT_SELECTION_NIVEAU;
            self.niveau_actuel = None
            self.interface_graphique.boutons_selection_niveau = [];
            self.interface_graphique.btn_retour_sel_niveau = None
        self.victoire_detectee = False;
        self.hint_next_move_display_pos = None;
        self.hint_message = "";
        self.deadlock_message = "";
        self.hint_solution_pour_etat_actuel = None;
        self.zoom_factor = 1.0;
        self._recalculer_taille_case_effective()
        self.view_offset_x = 0;
        self.view_offset_y = 0
        self._adapter_taille_fenetre_pour_niveau()

    def lancer_resolution_auto(self, type_solveur="bfs"):
        if not self.niveau_actuel or self.animation_active: return
        self.etat_avant_solveur = self.niveau_actuel.get_etat_pour_solveur()
        self.niveau_pour_visualisation = classes.Niveau(nom_fichier_ou_contenu=self.niveau_actuel.contenu_initial_str,
                                                        est_contenu_direct=True)
        if self.etat_avant_solveur: self.niveau_pour_visualisation.appliquer_etat_solveur(self.etat_avant_solveur)
        etat_init_pour_solveur = self.niveau_pour_visualisation.get_etat_pour_solveur()
        self.solveur_solution_pas, self.solveur_index_pas_actuel, self.solveur_iterations = None, 0, 0
        self.solveur_timer_dernier_pas = pygame.time.get_ticks();
        self.solveur_en_cours = True
        self.solveur_type_en_cours = type_solveur.upper();
        self.etat_jeu = C.ETAT_VISUALISATION_SOLVEUR
        self.dessiner();
        pygame.event.pump()
        solution_algo, iterations_algo = None, 0
        if type_solveur == "bfs":
            solv = solveurs.SolveurBFS(etat_init_pour_solveur); solution_algo, iterations_algo = solv.resoudre(
                self.niveau_pour_visualisation)
        elif type_solveur == "backtracking":
            solv = solveurs.SolveurRetourArriere(
                etat_init_pour_solveur); solution_algo, iterations_algo = solv.resoudre(self.niveau_pour_visualisation,
                                                                                        C.PROFONDEUR_MAX_BACKTRACKING)
        else:
            self.solveur_en_cours = False;
            self.etat_jeu = C.ETAT_JEU
            if self.niveau_actuel and self.etat_avant_solveur: self.niveau_actuel.appliquer_etat_solveur(
                self.etat_avant_solveur)
            return
        self.solveur_en_cours = False;
        self.solveur_solution_pas = solution_algo;
        self.solveur_iterations = iterations_algo
        if self.solveur_solution_pas: self.niveau_pour_visualisation.appliquer_etat_solveur(etat_init_pour_solveur)

    def avancer_pas_solveur(self):
        if self.solveur_solution_pas and self.niveau_pour_visualisation and self.solveur_index_pas_actuel < len(
                self.solveur_solution_pas):
            m_sym = self.solveur_solution_pas[self.solveur_index_pas_actuel];
            dx, dy = 0, 0
            if m_sym == 'H':
                dx, dy = 0, -1
            elif m_sym == 'B':
                dx, dy = 0, 1
            elif m_sym == 'G':
                dx, dy = -1, 0
            elif m_sym == 'D':
                dx, dy = 1, 0
            self.niveau_pour_visualisation.deplacer_joueur(dx, dy, C.TAILLE_CASE, simuler_seulement=True);
            self.solveur_index_pas_actuel += 1;
            self.solveur_timer_dernier_pas = pygame.time.get_ticks()

    def terminer_visualisation_solveur_rapidement(self):
        if self.solveur_solution_pas and self.niveau_pour_visualisation:
            while self.solveur_index_pas_actuel < len(self.solveur_solution_pas): self.avancer_pas_solveur()