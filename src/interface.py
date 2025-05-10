import pygame
import os
from . import constantes as C
from . import utilitaires
from . import classes
from . import editeur  # editeur sera importé ici
from . import solveurs
from .ui_elements import Bouton  # Importe Bouton depuis son nouveau fichier


class InterfaceGraphique:
    """Gère l'affichage général, les menus, et les interactions de base."""

    def __init__(self, largeur, hauteur, jeu_principal):
        self.largeur = largeur
        self.hauteur = hauteur
        self.fenetre = pygame.display.set_mode((largeur, hauteur))
        pygame.display.set_caption("Sokoban")

        self.images = utilitaires.charger_images_sokoban()
        if self.images.get('icon'):
            pygame.display.set_icon(self.images['icon'])

        self.font_titre = pygame.font.Font(C.POLICE_DEFAUT, C.TAILLE_POLICE_TITRE)
        self.font_menu = pygame.font.Font(C.POLICE_DEFAUT, C.TAILLE_POLICE_MENU)
        self.font_jeu = pygame.font.Font(C.POLICE_DEFAUT, C.TAILLE_POLICE_JEU)

        self.jeu_principal = jeu_principal
        self.boutons_menu = []
        self.boutons_selection_niveau = []
        self.scroll_offset_selection_niveau = 0
        self.hauteur_contenu_selection_niveau = 0
        self.btn_retour_sel_niveau = None  # Pour garder une référence au bouton retour

        self.message_victoire_affiche_temps = 0
        self.editeur_instance = None
        self.temp_bouton_retour_scores = None  # Pour le bouton retour des scores

    def _creer_boutons_menu_principal(self):
        self.boutons_menu = []
        btn_largeur, btn_hauteur = 300, 55
        espace = 25
        x_centre = self.largeur // 2 - btn_largeur // 2
        nb_boutons = 4
        y_total_boutons = nb_boutons * btn_hauteur + (nb_boutons - 1) * espace
        y_debut = self.hauteur // 2 - y_total_boutons // 2 + 30

        actions = [
            ("Nouvelle Partie", C.ETAT_SELECTION_NIVEAU),
            ("Éditeur de Niveaux", C.ETAT_EDITEUR),
            ("Scores", C.ETAT_SCORES),
            ("Quitter", C.ETAT_QUITTER)
        ]
        for i, (texte, action_id) in enumerate(actions):
            btn = Bouton(x_centre, y_debut + i * (btn_hauteur + espace), btn_largeur, btn_hauteur, texte,
                         font=self.font_menu, action=action_id)
            self.boutons_menu.append(btn)

    def afficher_menu_principal(self):
        self.fenetre.fill(C.DARK_BACKGROUND)
        titre_surface = self.font_titre.render("Sokoban", True, C.DARK_TEXT_PRIMARY)
        titre_rect = titre_surface.get_rect(center=(self.largeur // 2, self.hauteur // 4))
        self.fenetre.blit(titre_surface, titre_rect)

        if not self.boutons_menu:
            self._creer_boutons_menu_principal()

        pos_souris = pygame.mouse.get_pos()
        for btn in self.boutons_menu:
            btn.verifier_survol(pos_souris)
            btn.dessiner(self.fenetre)
        pygame.display.flip()

    def gerer_clic_menu_principal(self, pos_souris):
        for btn in self.boutons_menu:
            action = btn.verifier_clic(pos_souris)
            if action:
                return action
        return None

    def _preparer_boutons_selection_niveau(self, niveaux_defaut, niveaux_perso):
        self.boutons_selection_niveau = []
        tous_niveaux_specs = []
        idx_courant = 0
        for path in niveaux_defaut:
            nom_affiche = os.path.basename(path).replace(".txt", f" (D{idx_courant})")
            tous_niveaux_specs.append(
                {"type_charge": "defaut_chemin", "data": path, "index_global": idx_courant, "nom_affiche": nom_affiche})
            idx_courant += 1

        offset_index_perso = idx_courant
        for i, perso_data in enumerate(niveaux_perso):
            nom_affiche = f"{perso_data['nom']} (P{i})"
            tous_niveaux_specs.append(
                {"type_charge": "perso_contenu", "data": perso_data['contenu'], "index_global": offset_index_perso + i,
                 "nom_affiche": nom_affiche})

        btn_largeur, btn_hauteur = 300, 45
        espace_v = 15
        x_pos_col1 = self.largeur // 2 - btn_largeur - 20
        x_pos_col2 = self.largeur // 2 + 20
        y_pos_debut = 120  # Position Y de départ pour les boutons dans la surface scrollable

        self.hauteur_contenu_selection_niveau = 0

        for i, spec in enumerate(tous_niveaux_specs):
            col_idx = i % 2
            row_idx = i // 2
            current_x = x_pos_col1 if col_idx == 0 else x_pos_col2
            current_y = y_pos_debut + row_idx * (btn_hauteur + espace_v)  # Y relatif au début de la zone scrollable

            action = {"type_charge": spec["type_charge"], "data": spec["data"], "index_global": spec["index_global"],
                      "nom_affiche": spec["nom_affiche"].split(" (")[0]}
            # Les positions des boutons sont relatives au début de la zone scrollable (y_pos_debut)
            # mais Bouton a besoin de coordonnées absolues par rapport à sa surface de dessin.
            # Ici, on stocke les boutons avec des y qui seront ajustés par le scroll lors du dessin.
            # Pour la création du Bouton, on peut utiliser les y relatifs à la *surface scrollable*.
            # Donc, on soustrait y_pos_debut pour que le premier bouton soit à y=0 sur la surface scrollable.
            btn = Bouton(current_x, current_y - y_pos_debut, btn_largeur, btn_hauteur, spec["nom_affiche"],
                         font=self.font_menu, action=action)
            self.boutons_selection_niveau.append(btn)
            if (current_y - y_pos_debut) + btn_hauteur > self.hauteur_contenu_selection_niveau:
                self.hauteur_contenu_selection_niveau = (current_y - y_pos_debut) + btn_hauteur

        self.btn_retour_sel_niveau = Bouton(self.largeur // 2 - 100, self.hauteur - 70, 200, 50, "Retour Menu",
                                            font=self.font_menu, action="retour_menu")

    def afficher_selection_niveau(self, niveaux_defaut, niveaux_perso):
        self.fenetre.fill(C.DARK_BACKGROUND)
        titre_surface = self.font_titre.render("Sélectionnez un Niveau", True, C.DARK_TEXT_PRIMARY)
        titre_rect = titre_surface.get_rect(center=(self.largeur // 2, 60))
        self.fenetre.blit(titre_surface, titre_rect)

        if not self.boutons_selection_niveau or not self.btn_retour_sel_niveau:  # Si les boutons ne sont pas préparés
            self._preparer_boutons_selection_niveau(niveaux_defaut, niveaux_perso)

        # Zone scrollable
        y_zone_scroll_debut = 120
        hauteur_visible_zone_scroll = self.hauteur - y_zone_scroll_debut - 80

        surface_scrollable = pygame.Surface((self.largeur, self.hauteur_contenu_selection_niveau))
        surface_scrollable.fill(C.DARK_BACKGROUND)

        pos_souris_absolue = pygame.mouse.get_pos()

        for btn in self.boutons_selection_niveau:  # Ces boutons ont des positions relatives à la surface_scrollable
            # Pour la vérification du survol, on doit considérer la position du bouton sur l'écran
            # après scrolling.
            rect_sur_ecran = pygame.Rect(btn.rect.x,
                                         btn.rect.y - self.scroll_offset_selection_niveau + y_zone_scroll_debut,
                                         btn.rect.width, btn.rect.height)
            if rect_sur_ecran.collidepoint(pos_souris_absolue):
                btn.survol = True
            else:
                btn.survol = False
            btn.dessiner(surface_scrollable)

        self.fenetre.blit(surface_scrollable, (0, y_zone_scroll_debut),
                          (0, self.scroll_offset_selection_niveau, self.largeur, hauteur_visible_zone_scroll))

        if self.btn_retour_sel_niveau:
            self.btn_retour_sel_niveau.verifier_survol(pos_souris_absolue)
            self.btn_retour_sel_niveau.dessiner(self.fenetre)

        pygame.display.flip()

    def gerer_clic_selection_niveau(self, pos_souris_absolue, event_button):
        y_zone_scroll_debut = 120
        hauteur_visible_zone_scroll = self.hauteur - y_zone_scroll_debut - 80

        if event_button == 4:
            self.scroll_offset_selection_niveau = max(0, self.scroll_offset_selection_niveau - 30)
            return None
        elif event_button == 5:
            max_scroll = max(0, self.hauteur_contenu_selection_niveau - hauteur_visible_zone_scroll)
            self.scroll_offset_selection_niveau = min(max_scroll, self.scroll_offset_selection_niveau + 30)
            return None

        if event_button == 1:
            if self.btn_retour_sel_niveau and self.btn_retour_sel_niveau.verifier_clic(pos_souris_absolue):
                self.boutons_selection_niveau = []
                self.scroll_offset_selection_niveau = 0
                self.btn_retour_sel_niveau = None
                return C.ETAT_MENU_PRINCIPAL

            # Vérifier les clics sur les boutons dans la zone scrollable
            # Transformer la position de la souris en coordonnées relatives à la surface scrollable *entière*
            souris_x_rel_surface_scroll = pos_souris_absolue[0]
            souris_y_rel_surface_scroll = pos_souris_absolue[
                                              1] - y_zone_scroll_debut + self.scroll_offset_selection_niveau

            for btn in self.boutons_selection_niveau:
                if btn.rect.collidepoint((souris_x_rel_surface_scroll, souris_y_rel_surface_scroll)):
                    action = btn.action  # L'action est déjà vérifiée par collidepoint dans Bouton
                    if isinstance(action, dict):
                        self.jeu_principal.charger_niveau_par_specification(action)
                        self.boutons_selection_niveau = []
                        self.scroll_offset_selection_niveau = 0
                        self.btn_retour_sel_niveau = None
                        return C.ETAT_JEU
        return None

    def afficher_ecran_jeu(self, niveau_actuel, nb_mouvements, temps_ecoule_secondes):
        if not niveau_actuel: return

        niveau_largeur_px = niveau_actuel.largeur * C.TAILLE_CASE
        niveau_hauteur_px = niveau_actuel.hauteur * C.TAILLE_CASE

        surface_jeu = pygame.Surface((niveau_largeur_px, niveau_hauteur_px))
        niveau_actuel.dessiner(surface_jeu, self.images)

        offset_x_global = (self.largeur - niveau_largeur_px) // 2
        offset_y_global = (self.hauteur - niveau_hauteur_px - 60) // 2
        if offset_x_global < 0: offset_x_global = 0
        if offset_y_global < 0: offset_y_global = 0

        self.fenetre.fill(C.NOIR)
        self.fenetre.blit(surface_jeu, (offset_x_global, offset_y_global))

        hud_y_pos = 15
        hud_texte_mvt = self.font_jeu.render(f"Mouvements: {nb_mouvements}", True, C.DARK_TEXT_PRIMARY)
        self.fenetre.blit(hud_texte_mvt, (20, hud_y_pos))

        minutes = int(temps_ecoule_secondes // 60)
        secondes = int(temps_ecoule_secondes % 60)
        hud_texte_temps = self.font_jeu.render(f"Temps: {minutes:02d}:{secondes:02d}", True, C.DARK_TEXT_PRIMARY)
        self.fenetre.blit(hud_texte_temps, (self.largeur - hud_texte_temps.get_width() - 20, hud_y_pos))

        instr_text = "R: Recommencer | U: Annuler | ESC: Menu | F1: Résoudre"
        instr_surface = self.font_jeu.render(instr_text, True, C.JAUNE)
        self.fenetre.blit(instr_surface, (20, self.hauteur - instr_surface.get_height() - 15))

        if self.jeu_principal.victoire_detectee and self.message_victoire_affiche_temps == 0:
            self.message_victoire_affiche_temps = pygame.time.get_ticks()

        if self.message_victoire_affiche_temps > 0:
            self.afficher_message_victoire()
            if pygame.time.get_ticks() - self.message_victoire_affiche_temps > 2500:
                self.message_victoire_affiche_temps = 0
                self.jeu_principal.passer_au_niveau_suivant_ou_menu()

        pygame.display.flip()

    def afficher_message_victoire(self):
        texte_victoire = self.font_titre.render("NIVEAU TERMINÉ !", True, C.DARK_ACCENT_GOOD)
        rect_victoire = texte_victoire.get_rect(center=(self.largeur // 2, self.hauteur // 2))

        s = pygame.Surface((rect_victoire.width + 40, rect_victoire.height + 30), pygame.SRCALPHA)
        s.fill((C.DARK_SURFACE[0], C.DARK_SURFACE[1], C.DARK_SURFACE[2], 220))
        pygame.draw.rect(s, C.DARK_ACCENT_GOOD, s.get_rect(), 2, border_radius=5)
        self.fenetre.blit(s, (rect_victoire.left - 20, rect_victoire.top - 15))

        self.fenetre.blit(texte_victoire, rect_victoire)

    def afficher_editeur(self):
        if self.editeur_instance is None:
            self.editeur_instance = editeur.EditeurNiveaux(15, 10, jeu_principal_ref=self.jeu_principal)

        self.editeur_instance.dessiner(self.fenetre, self.images, self.font_menu)
        pygame.display.flip()

    def gerer_evenement_editeur(self, event):
        if self.editeur_instance:
            self.editeur_instance.gerer_evenement(event)

    def afficher_scores(self, scores_data):
        self.fenetre.fill(C.DARK_BACKGROUND)
        titre_surface = self.font_titre.render("Meilleurs Scores", True, C.DARK_TEXT_PRIMARY)
        titre_rect = titre_surface.get_rect(center=(self.largeur // 2, 60))
        self.fenetre.blit(titre_surface, titre_rect)

        y_offset = 130
        x_offset = 70
        for nom_niveau, score_info in scores_data.items():
            mvt = score_info.get('mouvements', 'N/A')
            temps_s = score_info.get('temps', 'N/A')
            temps_str = f"{int(temps_s // 60):02d}:{int(temps_s % 60):02d}" if isinstance(temps_s,
                                                                                          (int, float)) else 'N/A'

            score_text = f"Niv. {nom_niveau}: {mvt} mvts, {temps_str}"
            score_surface = self.font_menu.render(score_text, True, C.DARK_TEXT_SECONDARY)
            self.fenetre.blit(score_surface, (x_offset, y_offset))
            y_offset += 45
            if y_offset > self.hauteur - 100:
                texte_plus = self.font_menu.render("...", True, C.DARK_TEXT_SECONDARY)
                self.fenetre.blit(texte_plus, (x_offset, y_offset))
                break

        self.temp_bouton_retour_scores = Bouton(self.largeur // 2 - 100, self.hauteur - 70, 200, 50, "Retour Menu",
                                                font=self.font_menu, action=C.ETAT_MENU_PRINCIPAL)

        pos_souris = pygame.mouse.get_pos()
        self.temp_bouton_retour_scores.verifier_survol(pos_souris)
        self.temp_bouton_retour_scores.dessiner(self.fenetre)

        pygame.display.flip()

    def gerer_clic_scores(self, pos_souris):
        if self.temp_bouton_retour_scores:
            return self.temp_bouton_retour_scores.verifier_clic(pos_souris)
        return None

    def afficher_visualisation_solveur(self, niveau_visu, solution_pas_a_pas, index_pas_actuel, message=""):
        if not niveau_visu: return

        self.fenetre.fill(C.DARK_SURFACE)

        niveau_largeur_px = niveau_visu.largeur * C.TAILLE_CASE
        niveau_hauteur_px = niveau_visu.hauteur * C.TAILLE_CASE
        surface_jeu_visu = pygame.Surface((niveau_largeur_px, niveau_hauteur_px))
        niveau_visu.dessiner(surface_jeu_visu, self.images)

        offset_x_global = (self.largeur - niveau_largeur_px) // 2
        offset_y_global = (self.hauteur - niveau_hauteur_px - 90) // 2
        self.fenetre.blit(surface_jeu_visu, (offset_x_global, offset_y_global))

        total_pas = len(solution_pas_a_pas) if solution_pas_a_pas else 0
        info_pas = f"Pas: {index_pas_actuel + 1} / {total_pas}"
        info_surface = self.font_jeu.render(info_pas, True, C.DARK_TEXT_PRIMARY)
        self.fenetre.blit(info_surface, (30, 25))

        message_surface = self.font_jeu.render(message, True, C.DARK_ACCENT_INFO)
        self.fenetre.blit(message_surface, (30, 55))

        instr_surface = self.font_jeu.render("ESPACE: Suivant | ENTRÉE: Terminer | ESC: Annuler", True,
                                             C.DARK_ACCENT_WARN)
        self.fenetre.blit(instr_surface, (30, self.hauteur - instr_surface.get_height() - 20))

        pygame.display.flip()