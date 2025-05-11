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
        pygame.init();
        pygame.mixer.init()
        self.largeur_fenetre, self.hauteur_fenetre = C.LARGEUR_MENU, C.HAUTEUR_MENU
        self.interface_graphique = interface.InterfaceGraphique(self.largeur_fenetre, self.hauteur_fenetre, self)
        self.horloge = pygame.time.Clock();
        self.etat_jeu = C.ETAT_MENU_PRINCIPAL;
        self.fonctionnement = True
        self.niveau_actuel, self.niveau_actuel_index_global, self.nom_niveau_affiche = None, -1, ""
        self.nb_mouvements, self.temps_debut_niveau, self.temps_ecoule_total_secondes = 0, 0, 0
        self.sons = utilitaires.charger_sons_sokoban();
        self.progression_joueur = utilitaires.charger_progression()
        self.chemins_niveaux_defaut = []
        self.chemins_niveaux_perso = []
        self.rafraichir_listes_niveaux();
        self.victoire_detectee = False
        self.solveur_solution_pas, self.solveur_index_pas_actuel, self.niveau_pour_visualisation = None, 0, None
        self.solveur_timer_dernier_pas, self.solveur_delai_entre_pas, self.solveur_en_cours, self.etat_avant_solveur = 0, 200, False, None
        self.solveur_type_en_cours = ""
        self.editeur_actif, self.mode_test_editeur = None, False

        self.hint_solution_pour_etat_actuel = None  # Solution BFS pour l'état courant du joueur
        self.hint_etat_pour_lequel_solution_calculee = None  # Pour savoir si la solution est toujours valide
        self.hint_next_move_display_pos = None  # (grid_x, grid_y) de la case à surligner
        self.hint_message = ""

        self.animation_active = False
        self.FRAMES_ANIMATION_JOUEUR = int(C.FPS * 0.20)

    def rafraichir_listes_niveaux(self):
        self.chemins_niveaux_defaut = utilitaires.obtenir_liste_niveaux_defaut();
        self.chemins_niveaux_perso = utilitaires.obtenir_chemins_niveaux_personnalises()
        if hasattr(self, 'interface_graphique') and self.interface_graphique:
            self.interface_graphique.boutons_selection_niveau = [];
            self.interface_graphique.scroll_offset_selection_niveau = 0;
            self.interface_graphique.btn_retour_sel_niveau = None

    def _adapter_taille_fenetre_pour_niveau(self):
        n_l, n_h = C.LARGEUR_MENU, C.HAUTEUR_MENU
        if self.etat_jeu == C.ETAT_JEU and self.niveau_actuel:
            n_l = max(C.LARGEUR_FENETRE_JEU, self.niveau_actuel.largeur * C.TAILLE_CASE + 100)
            n_h = max(C.HAUTEUR_FENETRE_JEU, self.niveau_actuel.hauteur * C.TAILLE_CASE + 100)
        elif self.etat_jeu == C.ETAT_EDITEUR:
            ed_i = self.interface_graphique.editeur_instance
            if ed_i:
                n_l = max(C.LARGEUR_MENU, ed_i.largeur_grille * C.TAILLE_CASE + 250);n_h = max(C.HAUTEUR_MENU,
                                                                                               ed_i.hauteur_grille * C.TAILLE_CASE + 150)
            else:
                n_l = C.LARGEUR_MENU + 200;n_h = C.HAUTEUR_MENU + 100
        if self.largeur_fenetre != n_l or self.hauteur_fenetre != n_h:
            self.largeur_fenetre, self.hauteur_fenetre = n_l, n_h
            self.interface_graphique.largeur, self.interface_graphique.hauteur = n_l, n_h
            self.interface_graphique.fenetre = pygame.display.set_mode((n_l, n_h))
            if self.etat_jeu == C.ETAT_MENU_PRINCIPAL: self.interface_graphique.boutons_menu = []

    def charger_niveau_par_specification(self, spec_niv):
        chemin_fichier = spec_niv["data"]
        self.niveau_actuel_index_global, self.nom_niveau_affiche = spec_niv["index_global"], spec_niv["nom_affiche"]
        self.niveau_actuel = classes.Niveau(nom_fichier_ou_contenu=chemin_fichier)
        self.reinitialiser_etat_niveau();
        self._adapter_taille_fenetre_pour_niveau()

    def charger_niveau_temporaire_pour_test(self, contenu_str, editeur_ref):
        self.editeur_actif, self.mode_test_editeur = editeur_ref, True
        self.niveau_actuel = classes.Niveau(nom_fichier_ou_contenu=contenu_str, est_contenu_direct=True)
        self.nom_niveau_affiche = "Test Editeur";
        self.reinitialiser_etat_niveau();
        self.etat_jeu = C.ETAT_JEU;
        self._adapter_taille_fenetre_pour_niveau()

    def reinitialiser_etat_niveau(self):
        self.nb_mouvements, self.temps_debut_niveau, self.temps_ecoule_total_secondes = 0, time.time(), 0
        self.victoire_detectee = False;
        self.interface_graphique.message_victoire_affiche_temps = 0
        if self.niveau_actuel: self.niveau_actuel.reinitialiser()
        # Réinitialiser l'indice
        self.hint_solution_pour_etat_actuel = None
        self.hint_etat_pour_lequel_solution_calculee = None
        self.hint_next_move_display_pos = None
        self.hint_message = ""
        self.animation_active = False

    def executer(self):
        while self.fonctionnement:
            if self.etat_jeu == C.ETAT_JEU and self.temps_debut_niveau > 0 and not self.victoire_detectee: self.temps_ecoule_total_secondes = time.time() - self.temps_debut_niveau
            if not self.animation_active:
                self.gerer_evenements()
            self.mettre_a_jour();
            self.dessiner();
            self.horloge.tick(C.FPS)
        utilitaires.sauvegarder_progression(self.progression_joueur);
        pygame.quit()

    def demander_indice(self):
        if not self.niveau_actuel or self.victoire_detectee or self.animation_active:
            self.hint_message = "";
            self.hint_next_move_display_pos = None;
            return

        etat_courant_jeu = self.niveau_actuel.get_etat_pour_solveur()

        # Si la solution d'indice n'existe pas ou a été calculée pour un état différent
        if not self.hint_solution_pour_etat_actuel or self.hint_etat_pour_lequel_solution_calculee != etat_courant_jeu:
            self.hint_message = "Calcul de l'indice (BFS)...";
            self.hint_next_move_display_pos = None
            self.interface_graphique.afficher_ecran_jeu(self.niveau_actuel, self.nb_mouvements,
                                                        self.temps_ecoule_total_secondes,
                                                        self.hint_next_move_display_pos, self.hint_message)
            pygame.display.flip();
            pygame.event.pump()

            # Créer une copie propre du niveau pour la simulation du solveur, dans l'état actuel du jeu
            niveau_sim = classes.Niveau(nom_fichier_ou_contenu=self.niveau_actuel.contenu_initial_str,
                                        est_contenu_direct=True)
            niveau_sim.appliquer_etat_solveur(etat_courant_jeu)  # Mettre la copie dans l'état actuel du jeu

            solveur = solveurs.SolveurBFS(etat_courant_jeu)  # Le solveur part de cet état
            self.hint_solution_pour_etat_actuel = solveur.resoudre(niveau_sim)  # Il simule sur la copie `niveau_sim`
            self.hint_etat_pour_lequel_solution_calculee = etat_courant_jeu  # Enregistrer pour quel état cette solution est valide

        if self.hint_solution_pour_etat_actuel and len(self.hint_solution_pour_etat_actuel) > 0:
            premier_mouvement_symbole = self.hint_solution_pour_etat_actuel[0]  # On ne montre que le premier pas
            dx, dy = 0, 0;
            direction_txt = "?"
            if premier_mouvement_symbole == 'H':
                dx, dy = 0, -1; direction_txt = "Haut"
            elif premier_mouvement_symbole == 'B':
                dx, dy = 0, 1; direction_txt = "Bas"
            elif premier_mouvement_symbole == 'G':
                dx, dy = -1, 0; direction_txt = "Gauche"
            elif premier_mouvement_symbole == 'D':
                dx, dy = 1, 0; direction_txt = "Droite"

            if self.niveau_actuel.joueur:
                # La position à surligner est la case où le joueur se déplacerait
                self.hint_next_move_display_pos = (
                self.niveau_actuel.joueur.grid_x + dx, self.niveau_actuel.joueur.grid_y + dy)
                self.hint_message = f"Indice: Aller {direction_txt}"
            else:  # Ne devrait pas arriver si le niveau est valide
                self.hint_message = "Erreur joueur indice.";
                self.hint_next_move_display_pos = None
        else:
            self.hint_message = "Aucun indice trouvé (BFS).";
            self.hint_next_move_display_pos = None
            self.hint_solution_pour_etat_actuel = None  # Réinitialiser pour forcer recalcul si redemandé

    def gerer_evenements(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT: self.fonctionnement = False
            if self.etat_jeu == C.ETAT_MENU_PRINCIPAL:
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    n_e = self.interface_graphique.gerer_clic_menu_principal(event.pos)
                    if n_e:
                        if n_e == C.ETAT_QUITTER:
                            self.fonctionnement = False
                        else:
                            self.etat_jeu = n_e;self._adapter_taille_fenetre_pour_niveau()
            elif self.etat_jeu == C.ETAT_SELECTION_NIVEAU:
                if event.type == pygame.MOUSEBUTTONDOWN:
                    n_e_a = self.interface_graphique.gerer_clic_selection_niveau(event.pos, event.button)
                    if n_e_a: self.etat_jeu = n_e_a;self._adapter_taille_fenetre_pour_niveau()
                elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    self.etat_jeu = C.ETAT_MENU_PRINCIPAL;
                    self.interface_graphique.boutons_selection_niveau = [];
                    self.interface_graphique.btn_retour_sel_niveau = None;
                    self._adapter_taille_fenetre_pour_niveau()
            elif self.etat_jeu == C.ETAT_JEU:
                if event.type == pygame.KEYDOWN:
                    if event.key != pygame.K_h:  # Si ce n'est pas une demande d'indice
                        self.hint_next_move_display_pos = None;
                        self.hint_message = ""
                        # Si le joueur fait un mouvement, la solution d'indice est invalidée
                        self.hint_solution_pour_etat_actuel = None
                        self.hint_etat_pour_lequel_solution_calculee = None
                    if not self.victoire_detectee:
                        m_e = False
                        key_map = {pygame.K_UP: 'u', pygame.K_w: 'u', pygame.K_z: 'u', pygame.K_DOWN: 'd',
                                   pygame.K_s: 'd',
                                   pygame.K_LEFT: 'l', pygame.K_a: 'l', pygame.K_q: 'l', pygame.K_RIGHT: 'r',
                                   pygame.K_d: 'r'}
                        if event.key in key_map:
                            moves = {'u': (0, -1), 'd': (0, 1), 'l': (-1, 0), 'r': (1, 0)}
                            if self.niveau_actuel.deplacer_joueur(*moves[key_map[event.key]], self.sons,
                                                                  self.FRAMES_ANIMATION_JOUEUR):
                                self.animation_active = True;
                                m_e = True
                        elif event.key == pygame.K_u:
                            if self.niveau_actuel.annuler_dernier_mouvement() and self.nb_mouvements > 0: self.nb_mouvements -= 1
                        if m_e: self.nb_mouvements += 1
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
                        self.hint_solution_pour_etat_actuel = None;
                        self._adapter_taille_fenetre_pour_niveau()
                    elif event.key == pygame.K_F1:
                        self.lancer_resolution_auto("bfs")
                    elif event.key == pygame.K_F2:
                        self.lancer_resolution_auto("backtracking")
            elif self.etat_jeu == C.ETAT_EDITEUR:  # ... (code identique)
                self.interface_graphique.gerer_evenement_editeur(event)
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    if self.interface_graphique.editeur_instance and self.interface_graphique.editeur_instance.input_nom_actif:
                        self.interface_graphique.editeur_instance.input_nom_actif = False;
                        self.interface_graphique.editeur_instance.temp_nom_niveau = self.interface_graphique.editeur_instance.nom_niveau_en_cours
                    else:
                        self.etat_jeu = C.ETAT_MENU_PRINCIPAL;self.interface_graphique.editeur_instance = None;self._adapter_taille_fenetre_pour_niveau()
            elif self.etat_jeu == C.ETAT_SCORES:  # ... (code identique)
                action_score = None
                if event.type == pygame.MOUSEBUTTONDOWN:
                    action_score = self.interface_graphique.gerer_clic_scores(event.pos, event.button, event.type)
                elif event.type == pygame.MOUSEBUTTONUP:
                    if event.button == 1: self.interface_graphique.gerer_clic_scores(event.pos, event.type, event.type)
                elif event.type == pygame.MOUSEMOTION:
                    if self.interface_graphique.dragging_scrollbar_scores: self.interface_graphique.gerer_clic_scores(
                        event.pos, event.type, event.rel)
                if action_score == C.ETAT_MENU_PRINCIPAL: self.etat_jeu = C.ETAT_MENU_PRINCIPAL; self._adapter_taille_fenetre_pour_niveau()
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE: self.etat_jeu = C.ETAT_MENU_PRINCIPAL; self.interface_graphique.scroll_offset_scores = 0; self._adapter_taille_fenetre_pour_niveau()
            elif self.etat_jeu == C.ETAT_VISUALISATION_SOLVEUR:  # ... (code identique)
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
                        self.etat_avant_solveur = None

    def mettre_a_jour(self):
        if self.etat_jeu == C.ETAT_JEU and self.niveau_actuel:
            self.animation_active = self.niveau_actuel.update_animations_niveau()
            if not self.animation_active and not self.victoire_detectee:
                if self.niveau_actuel.verifier_victoire():
                    self.victoire_detectee = True;
                    self.hint_next_move_display_pos = None;
                    self.hint_message = ""  # Nettoyer indice à la victoire
                    if not self.mode_test_editeur:
                        if self.sons and self.sons.get("victoire"): self.sons["victoire"].play()
                        self.enregistrer_score()
                    else:
                        if self.sons and self.sons.get("victoire"): self.sons["victoire"].play()
        elif self.etat_jeu == C.ETAT_VISUALISATION_SOLVEUR and self.solveur_solution_pas:
            if pygame.time.get_ticks() - self.solveur_timer_dernier_pas > self.solveur_delai_entre_pas: self.solveur_timer_dernier_pas = pygame.time.get_ticks()

    def dessiner(self):
        if self.etat_jeu == C.ETAT_MENU_PRINCIPAL:
            self.interface_graphique.afficher_menu_principal()
        elif self.etat_jeu == C.ETAT_SELECTION_NIVEAU:
            self.interface_graphique.afficher_selection_niveau(self.chemins_niveaux_defaut, self.chemins_niveaux_perso)
        elif self.etat_jeu == C.ETAT_JEU:
            self.interface_graphique.afficher_ecran_jeu(self.niveau_actuel, self.nb_mouvements,
                                                        self.temps_ecoule_total_secondes,
                                                        self.hint_next_move_display_pos, self.hint_message)
        elif self.etat_jeu == C.ETAT_EDITEUR:
            self.interface_graphique.afficher_editeur()
        elif self.etat_jeu == C.ETAT_SCORES:
            scores_tries = dict(sorted(self.progression_joueur.get("scores", {}).items(), key=lambda item: (
            item[1].get('mouvements', float('inf')), item[1].get('temps', float('inf')))))
            self.interface_graphique.afficher_scores(scores_tries)
        elif self.etat_jeu == C.ETAT_VISUALISATION_SOLVEUR:
            msg = "Résolution..."
            if self.solveur_en_cours:
                msg = f"Calcul ({self.solveur_type_en_cours})..."
            elif self.solveur_solution_pas:
                msg = f"Solution ({self.solveur_type_en_cours}) trouvée!"
                if self.solveur_index_pas_actuel >= len(
                    self.solveur_solution_pas or []): msg = "Visualisation terminée."
            else:
                msg = f"Aucune solution ({self.solveur_type_en_cours})."
            self.interface_graphique.afficher_visualisation_solveur(self.niveau_pour_visualisation,
                                                                    self.solveur_solution_pas,
                                                                    self.solveur_index_pas_actuel, msg)

    def enregistrer_score(self):
        if not self.niveau_actuel or self.mode_test_editeur: return
        cle_s = str(self.nom_niveau_affiche);
        scr_act = self.progression_joueur.setdefault("scores", {});
        scr_prec = scr_act.get(cle_s)
        m_s = False
        if scr_prec is None:
            m_s = True
        else:
            if self.nb_mouvements < scr_prec["mouvements"]:
                m_s = True
            elif self.nb_mouvements == scr_prec["mouvements"] and self.temps_ecoule_total_secondes < scr_prec["temps"]:
                m_s = True
        if m_s: scr_act[cle_s] = {"mouvements": self.nb_mouvements,
                                  "temps": round(self.temps_ecoule_total_secondes, 2)}; print(
            f"Nouveau record pour {cle_s}!")

    def passer_au_niveau_suivant_ou_menu(self):
        if self.mode_test_editeur:
            self.etat_jeu = C.ETAT_EDITEUR;
            self.niveau_actuel = None;
            self.mode_test_editeur = False
            self.interface_graphique.editeur_instance = self.editeur_actif
            if self.interface_graphique.editeur_instance:
                self.interface_graphique.editeur_instance.jeu_principal = self
                self.interface_graphique.editeur_instance.message_info = "Test terminé. Retour à l'éditeur."
                self.interface_graphique.editeur_instance.message_couleur = C.DARK_ACCENT_INFO
            self.editeur_actif = None
        else:
            self.etat_jeu = C.ETAT_SELECTION_NIVEAU;
            self.niveau_actuel = None
            self.interface_graphique.boutons_selection_niveau = [];
            self.interface_graphique.scroll_offset_selection_niveau = 0;
            self.interface_graphique.btn_retour_sel_niveau = None
        self.victoire_detectee = False;
        self.hint_next_move_display_pos = None;
        self.hint_message = "";
        self.hint_solution_pour_etat_actuel = None;
        self._adapter_taille_fenetre_pour_niveau()

    def lancer_resolution_auto(self, type_solveur="bfs"):
        if not self.niveau_actuel or self.animation_active: return
        self.etat_avant_solveur = self.niveau_actuel.get_etat_pour_solveur()
        self.niveau_pour_visualisation = classes.Niveau(nom_fichier_ou_contenu=self.niveau_actuel.contenu_initial_str,
                                                        est_contenu_direct=True)
        self.niveau_pour_visualisation.appliquer_etat_solveur(self.etat_avant_solveur)
        etat_init_sol = self.niveau_pour_visualisation.get_etat_pour_solveur()
        self.solveur_solution_pas = None;
        self.solveur_index_pas_actuel = 0;
        self.solveur_timer_dernier_pas = pygame.time.get_ticks();
        self.solveur_en_cours = True
        self.solveur_type_en_cours = type_solveur.upper()
        self.etat_jeu = C.ETAT_VISUALISATION_SOLVEUR
        pygame.display.flip()
        if type_solveur == "bfs":
            solv = solveurs.SolveurBFS(etat_init_sol); self.solveur_solution_pas = solv.resoudre(
                self.niveau_pour_visualisation)
        elif type_solveur == "backtracking":
            solv = solveurs.SolveurRetourArriere(etat_init_sol); self.solveur_solution_pas = solv.resoudre(
                self.niveau_pour_visualisation, C.PROFONDEUR_MAX_BACKTRACKING)
        else:
            print(
                f"Type de solveur inconnu: {type_solveur}");self.solveur_en_cours = False;self.etat_jeu = C.ETAT_JEU; self.niveau_actuel.appliquer_etat_solveur(
                self.etat_avant_solveur); return
        self.solveur_en_cours = False
        if self.solveur_solution_pas:
            print(
                f"Solution ({type_solveur}): {self.solveur_solution_pas}"); self.niveau_pour_visualisation.appliquer_etat_solveur(
                etat_init_sol)
        else:
            print(f"Aucune solution trouvée par {type_solveur}.")

    def avancer_pas_solveur(self):
        if self.solveur_solution_pas and self.niveau_pour_visualisation and self.solveur_index_pas_actuel < len(
                self.solveur_solution_pas):
            m_sym = self.solveur_solution_pas[self.solveur_index_pas_actuel];
            dx, dy = 0, 0
            if m_sym == 'H': dx, dy = 0, -1
            elif m_sym == 'B': dx, dy = 0, 1
            elif m_sym == 'G': dx, dy = -1, 0
            elif m_sym == 'D': dx, dy = 1, 0
            self.niveau_pour_visualisation.deplacer_joueur(dx, dy);
            self.solveur_index_pas_actuel += 1;
            self.solveur_timer_dernier_pas = pygame.time.get_ticks()  # Note: deplacer_joueur pour la visu n'anime pas
            if self.solveur_index_pas_actuel >= len(self.solveur_solution_pas): print("Visualisation terminée.")
        else:
            print("Fin de solution ou pas de solution.")

    def terminer_visualisation_solveur_rapidement(self):
        if self.solveur_solution_pas and self.niveau_pour_visualisation:
            while self.solveur_index_pas_actuel < len(self.solveur_solution_pas): self.avancer_pas_solveur()
            print("Solution appliquée rapidement.")