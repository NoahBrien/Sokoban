import pygame
import time
import os
from . import constantes as C
from . import utilitaires
from . import classes
from . import interface  # interface importe editeur, qui importe ui_elements
from . import solveurs


# from . import editeur # Pas besoin d'importer editeur directement ici, il est géré via interface

class Jeu:
    """Gère la logique principale du jeu, les états et la progression."""

    def __init__(self):
        pygame.init()
        pygame.mixer.init()

        self.largeur_fenetre = C.LARGEUR_MENU
        self.hauteur_fenetre = C.HAUTEUR_MENU

        self.interface_graphique = interface.InterfaceGraphique(self.largeur_fenetre, self.hauteur_fenetre, self)
        self.horloge = pygame.time.Clock()
        self.etat_jeu = C.ETAT_MENU_PRINCIPAL
        self.fonctionnement = True

        self.niveau_actuel = None
        self.niveau_actuel_index_global = -1
        self.nom_niveau_affiche = ""

        self.nb_mouvements = 0
        self.temps_debut_niveau = 0
        self.temps_ecoule_total_secondes = 0

        self.sons = utilitaires.charger_sons_sokoban()
        self.progression_joueur = utilitaires.charger_progression()
        self.rafraichir_listes_niveaux()

        self.victoire_detectee = False

        self.solveur_solution_pas = None
        self.solveur_index_pas_actuel = 0
        self.niveau_pour_visualisation = None
        self.solveur_timer_dernier_pas = 0
        self.solveur_delai_entre_pas = 200
        self.solveur_en_cours = False  # Pour afficher "Calcul en cours"
        self.etat_avant_solveur = None  # Pour restaurer l'état si on annule la visu

        self.editeur_actif = None  # Utilisé pour restaurer l'état de l'éditeur après test
        self.mode_test_editeur = False

    def rafraichir_listes_niveaux(self):
        self.niveaux_defaut_fichiers = utilitaires.obtenir_liste_niveaux_defaut()
        self.niveaux_personnalises_data = utilitaires.obtenir_niveaux_personnalises()
        if self.interface_graphique:  # S'assurer que l'interface est initialisée
            self.interface_graphique.boutons_selection_niveau = []
            self.interface_graphique.scroll_offset_selection_niveau = 0
            self.interface_graphique.btn_retour_sel_niveau = None

    def _adapter_taille_fenetre_pour_niveau(self):
        nouvelle_largeur, nouvelle_hauteur = C.LARGEUR_MENU, C.HAUTEUR_MENU  # Par défaut

        if self.etat_jeu == C.ETAT_JEU and self.niveau_actuel:
            nouvelle_largeur = max(C.LARGEUR_FENETRE_JEU, self.niveau_actuel.largeur * C.TAILLE_CASE + 100)
            nouvelle_hauteur = max(C.HAUTEUR_FENETRE_JEU, self.niveau_actuel.hauteur * C.TAILLE_CASE + 100)
        elif self.etat_jeu == C.ETAT_EDITEUR:
            ed_inst = self.interface_graphique.editeur_instance
            if ed_inst:  # Utiliser la taille de la grille de l'éditeur + UI
                nouvelle_largeur = max(C.LARGEUR_MENU, ed_inst.largeur_grille * C.TAILLE_CASE + 250)
                nouvelle_hauteur = max(C.HAUTEUR_MENU, ed_inst.hauteur_grille * C.TAILLE_CASE + 150)
            else:  # Si l'éditeur n'est pas encore instancié, prévoir une taille
                nouvelle_largeur = C.LARGEUR_MENU + 200
                nouvelle_hauteur = C.HAUTEUR_MENU + 100

        if self.largeur_fenetre != nouvelle_largeur or self.hauteur_fenetre != nouvelle_hauteur:
            self.largeur_fenetre = nouvelle_largeur
            self.hauteur_fenetre = nouvelle_hauteur
            self.interface_graphique.largeur = nouvelle_largeur
            self.interface_graphique.hauteur = nouvelle_hauteur
            self.interface_graphique.fenetre = pygame.display.set_mode((nouvelle_largeur, nouvelle_hauteur))
            if self.etat_jeu == C.ETAT_MENU_PRINCIPAL:
                self.interface_graphique.boutons_menu = []

    def charger_niveau_par_specification(self, spec_niveau):
        type_charge = spec_niveau["type_charge"]
        data = spec_niveau["data"]
        self.niveau_actuel_index_global = spec_niveau["index_global"]
        self.nom_niveau_affiche = spec_niveau["nom_affiche"]

        if type_charge == "defaut_chemin":
            self.niveau_actuel = classes.Niveau(nom_fichier_ou_contenu=data)
        elif type_charge == "perso_contenu":
            self.niveau_actuel = classes.Niveau(nom_fichier_ou_contenu=data, est_contenu_direct=True)

        self.reinitialiser_etat_niveau()
        self._adapter_taille_fenetre_pour_niveau()

    def charger_niveau_temporaire_pour_test(self, contenu_str, editeur_ref):
        self.editeur_actif = editeur_ref
        self.mode_test_editeur = True
        self.niveau_actuel = classes.Niveau(nom_fichier_ou_contenu=contenu_str, est_contenu_direct=True)
        self.nom_niveau_affiche = "Test Editeur"
        self.reinitialiser_etat_niveau()
        self.etat_jeu = C.ETAT_JEU
        self._adapter_taille_fenetre_pour_niveau()

    def reinitialiser_etat_niveau(self):
        self.nb_mouvements = 0
        self.temps_debut_niveau = time.time()
        self.temps_ecoule_total_secondes = 0
        self.victoire_detectee = False
        self.interface_graphique.message_victoire_affiche_temps = 0
        if self.niveau_actuel:
            self.niveau_actuel.reinitialiser()

    def executer(self):
        while self.fonctionnement:
            if self.etat_jeu == C.ETAT_JEU and self.temps_debut_niveau > 0 and not self.victoire_detectee:
                self.temps_ecoule_total_secondes = time.time() - self.temps_debut_niveau

            self.gerer_evenements()
            self.mettre_a_jour()
            self.dessiner()
            self.horloge.tick(C.FPS)

        utilitaires.sauvegarder_progression(self.progression_joueur)
        pygame.quit()

    def gerer_evenements(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.fonctionnement = False

            if self.etat_jeu == C.ETAT_MENU_PRINCIPAL:
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    nouvel_etat = self.interface_graphique.gerer_clic_menu_principal(event.pos)
                    if nouvel_etat:
                        if nouvel_etat == C.ETAT_QUITTER:
                            self.fonctionnement = False
                        else:
                            self.etat_jeu = nouvel_etat
                        self._adapter_taille_fenetre_pour_niveau()

            elif self.etat_jeu == C.ETAT_SELECTION_NIVEAU:
                if event.type == pygame.MOUSEBUTTONDOWN:
                    nouvel_etat_ou_action = self.interface_graphique.gerer_clic_selection_niveau(event.pos,
                                                                                                 event.button)
                    if nouvel_etat_ou_action:
                        self.etat_jeu = nouvel_etat_ou_action
                        self._adapter_taille_fenetre_pour_niveau()
                elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    self.etat_jeu = C.ETAT_MENU_PRINCIPAL
                    self.interface_graphique.boutons_selection_niveau = []
                    self.interface_graphique.btn_retour_sel_niveau = None
                    self._adapter_taille_fenetre_pour_niveau()

            elif self.etat_jeu == C.ETAT_JEU:
                if event.type == pygame.KEYDOWN:
                    if not self.victoire_detectee:
                        mouvement_effectue = False
                        if event.key in [pygame.K_UP, pygame.K_w, pygame.K_z]:
                            mouvement_effectue = self.niveau_actuel.deplacer_joueur(0, -1, self.sons)
                        elif event.key in [pygame.K_DOWN, pygame.K_s]:
                            mouvement_effectue = self.niveau_actuel.deplacer_joueur(0, 1, self.sons)
                        elif event.key in [pygame.K_LEFT, pygame.K_a, pygame.K_q]:
                            mouvement_effectue = self.niveau_actuel.deplacer_joueur(-1, 0, self.sons)
                        elif event.key in [pygame.K_RIGHT, pygame.K_d]:
                            mouvement_effectue = self.niveau_actuel.deplacer_joueur(1, 0, self.sons)
                        elif event.key == pygame.K_u:
                            if self.niveau_actuel.annuler_dernier_mouvement():
                                if self.nb_mouvements > 0: self.nb_mouvements -= 1

                        if mouvement_effectue:
                            self.nb_mouvements += 1
                            if self.niveau_actuel.verifier_victoire():
                                self.victoire_detectee = True
                                if self.sons and self.sons.get("victoire"): self.sons["victoire"].play()
                                self.enregistrer_score()

                    if event.key == pygame.K_r:
                        self.reinitialiser_etat_niveau()
                    elif event.key == pygame.K_ESCAPE:
                        if self.mode_test_editeur:
                            self.etat_jeu = C.ETAT_EDITEUR
                            self.niveau_actuel = None
                            self.mode_test_editeur = False
                            self.interface_graphique.editeur_instance = self.editeur_actif
                            if self.interface_graphique.editeur_instance:
                                self.interface_graphique.editeur_instance.jeu_principal = self
                            self.editeur_actif = None
                        else:
                            self.etat_jeu = C.ETAT_MENU_PRINCIPAL
                        self._adapter_taille_fenetre_pour_niveau()

                    elif event.key == pygame.K_F1:
                        self.lancer_resolution_auto("bfs")

            elif self.etat_jeu == C.ETAT_EDITEUR:
                self.interface_graphique.gerer_evenement_editeur(
                    event)  # Passe l'event à l'interface qui le passe à l'éditeur
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    if self.interface_graphique.editeur_instance and self.interface_graphique.editeur_instance.input_nom_actif:
                        self.interface_graphique.editeur_instance.input_nom_actif = False
                        self.interface_graphique.editeur_instance.temp_nom_niveau = self.interface_graphique.editeur_instance.nom_niveau_en_cours
                    else:
                        self.etat_jeu = C.ETAT_MENU_PRINCIPAL
                        self.interface_graphique.editeur_instance = None
                        self._adapter_taille_fenetre_pour_niveau()

            elif self.etat_jeu == C.ETAT_SCORES:
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    action = self.interface_graphique.gerer_clic_scores(event.pos)
                    if action == C.ETAT_MENU_PRINCIPAL:
                        self.etat_jeu = C.ETAT_MENU_PRINCIPAL
                        self._adapter_taille_fenetre_pour_niveau()
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    self.etat_jeu = C.ETAT_MENU_PRINCIPAL
                    self._adapter_taille_fenetre_pour_niveau()

            elif self.etat_jeu == C.ETAT_VISUALISATION_SOLVEUR:
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_SPACE:
                        self.avancer_pas_solveur()
                    elif event.key == pygame.K_RETURN:
                        self.terminer_visualisation_solveur_rapidement()
                    elif event.key == pygame.K_ESCAPE:
                        self.etat_jeu = C.ETAT_JEU
                        if self.niveau_actuel and self.etat_avant_solveur:
                            self.niveau_actuel.appliquer_etat_solveur(self.etat_avant_solveur)
                        self.solveur_solution_pas = None
                        self.niveau_pour_visualisation = None
                        self.etat_avant_solveur = None

    def mettre_a_jour(self):
        if self.etat_jeu == C.ETAT_VISUALISATION_SOLVEUR and self.solveur_solution_pas:
            maintenant = pygame.time.get_ticks()
            if maintenant - self.solveur_timer_dernier_pas > self.solveur_delai_entre_pas:
                self.solveur_timer_dernier_pas = maintenant

    def dessiner(self):
        if self.etat_jeu == C.ETAT_MENU_PRINCIPAL:
            self.interface_graphique.afficher_menu_principal()
        elif self.etat_jeu == C.ETAT_SELECTION_NIVEAU:
            self.interface_graphique.afficher_selection_niveau(self.niveaux_defaut_fichiers,
                                                               self.niveaux_personnalises_data)
        elif self.etat_jeu == C.ETAT_JEU:
            self.interface_graphique.afficher_ecran_jeu(self.niveau_actuel, self.nb_mouvements,
                                                        self.temps_ecoule_total_secondes)
        elif self.etat_jeu == C.ETAT_EDITEUR:
            self.interface_graphique.afficher_editeur()
        elif self.etat_jeu == C.ETAT_SCORES:
            scores_affiches = {}
            for cle_niveau, details_score in self.progression_joueur.get("scores", {}).items():
                scores_affiches[cle_niveau] = details_score
            self.interface_graphique.afficher_scores(scores_affiches)
        elif self.etat_jeu == C.ETAT_VISUALISATION_SOLVEUR:
            msg = "Résolution..."
            if self.solveur_en_cours:
                msg = "Calcul de la solution..."
            elif self.solveur_solution_pas:
                msg = "Solution trouvée!"
                if self.solveur_index_pas_actuel >= len(self.solveur_solution_pas):
                    msg = "Visualisation terminée."
            else:
                msg = "Aucune solution trouvée."

            self.interface_graphique.afficher_visualisation_solveur(
                self.niveau_pour_visualisation,
                self.solveur_solution_pas,
                self.solveur_index_pas_actuel,
                msg
            )

    def enregistrer_score(self):
        if not self.niveau_actuel: return
        cle_score = str(self.nom_niveau_affiche)

        scores_actuels = self.progression_joueur.setdefault("scores", {})
        score_precedent = scores_actuels.get(cle_score)

        meilleur_score = False
        if score_precedent is None:
            meilleur_score = True
        else:
            if self.nb_mouvements < score_precedent["mouvements"]:
                meilleur_score = True
            elif self.nb_mouvements == score_precedent["mouvements"] and self.temps_ecoule_total_secondes < \
                    score_precedent["temps"]:
                meilleur_score = True

        if meilleur_score:
            scores_actuels[cle_score] = {"mouvements": self.nb_mouvements,
                                         "temps": round(self.temps_ecoule_total_secondes, 2)}
            print(f"Nouveau record pour {cle_score}!")

    def passer_au_niveau_suivant_ou_menu(self):
        self.etat_jeu = C.ETAT_SELECTION_NIVEAU
        self.niveau_actuel = None
        self.victoire_detectee = False
        self.interface_graphique.boutons_selection_niveau = []
        self.interface_graphique.scroll_offset_selection_niveau = 0
        self.interface_graphique.btn_retour_sel_niveau = None
        self._adapter_taille_fenetre_pour_niveau()

    def lancer_resolution_auto(self, type_solveur="bfs"):
        if not self.niveau_actuel: return
        self.etat_avant_solveur = self.niveau_actuel.get_etat_pour_solveur()

        self.niveau_pour_visualisation = classes.Niveau(
            nom_fichier_ou_contenu=self.niveau_actuel.contenu_initial_str,
            est_contenu_direct=True
        )
        self.niveau_pour_visualisation.appliquer_etat_solveur(self.etat_avant_solveur)
        etat_initial_solveur = self.niveau_pour_visualisation.get_etat_pour_solveur()

        self.solveur_solution_pas = None
        self.solveur_index_pas_actuel = 0
        self.solveur_timer_dernier_pas = pygame.time.get_ticks()
        self.solveur_en_cours = True
        self.etat_jeu = C.ETAT_VISUALISATION_SOLVEUR

        pygame.display.flip()

        if type_solveur == "bfs":
            solveur = solveurs.SolveurBFS(etat_initial_solveur)
            self.solveur_solution_pas = solveur.resoudre(self.niveau_pour_visualisation)
        elif type_solveur == "backtracking":
            solveur = solveurs.SolveurRetourArriere(etat_initial_solveur)
            self.solveur_solution_pas = solveur.resoudre(self.niveau_pour_visualisation, C.PROFONDEUR_MAX_BACKTRACKING)

        self.solveur_en_cours = False
        if self.solveur_solution_pas:
            print(f"Solution: {self.solveur_solution_pas}")
            self.niveau_pour_visualisation.appliquer_etat_solveur(etat_initial_solveur)
        else:
            print("Aucune solution trouvée par le solveur.")

    def avancer_pas_solveur(self):
        if self.solveur_solution_pas and self.niveau_pour_visualisation and \
                self.solveur_index_pas_actuel < len(self.solveur_solution_pas):

            mouvement_symbole = self.solveur_solution_pas[self.solveur_index_pas_actuel]
            dx, dy = 0, 0
            if mouvement_symbole == 'H':
                dx, dy = 0, -1
            elif mouvement_symbole == 'B':
                dx, dy = 0, 1
            elif mouvement_symbole == 'G':
                dx, dy = -1, 0
            elif mouvement_symbole == 'D':
                dx, dy = 1, 0

            self.niveau_pour_visualisation.deplacer_joueur(dx, dy)
            self.solveur_index_pas_actuel += 1
            self.solveur_timer_dernier_pas = pygame.time.get_ticks()

            if self.solveur_index_pas_actuel >= len(self.solveur_solution_pas):
                print("Visualisation terminée.")
        else:
            print("Fin de solution ou pas de solution.")

    def terminer_visualisation_solveur_rapidement(self):
        if self.solveur_solution_pas and self.niveau_pour_visualisation:
            while self.solveur_index_pas_actuel < len(self.solveur_solution_pas):
                self.avancer_pas_solveur()
            print("Solution appliquée rapidement.")