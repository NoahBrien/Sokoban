import pygame
from . import constantes as C
from .classes import Niveau, Case, Caisse, Joueur
from .utilitaires import sauvegarder_niveau_personnalise
from .ui_elements import Bouton  # Importe Bouton depuis son nouveau fichier


class EditeurNiveaux:
    def __init__(self, largeur_grille=15, hauteur_grille=10, jeu_principal_ref=None):
        self.largeur_grille = largeur_grille
        self.hauteur_grille = hauteur_grille
        self.grille = [[C.SOL for _ in range(largeur_grille)] for _ in range(hauteur_grille)]
        self.element_selectionne = C.MUR
        self.nom_niveau_en_cours = "MonNiveauPerso"
        self.message_info = "Bienvenue dans l'éditeur !"
        self.input_nom_actif = False
        self.temp_nom_niveau = self.nom_niveau_en_cours
        self.jeu_principal = jeu_principal_ref

        self.palette = [C.MUR, C.SOL, C.CAISSE, C.CIBLE, C.JOUEUR]
        self.palette_rects = []
        self.boutons_editeur = []
        self._creer_boutons_editeur()

    def _creer_boutons_editeur(self):
        self.boutons_editeur = []
        ui_bouton_x_base = self.largeur_grille * C.TAILLE_CASE + 40

        font_pour_boutons = None
        if self.jeu_principal and hasattr(self.jeu_principal,
                                          'interface_graphique') and self.jeu_principal.interface_graphique:
            font_pour_boutons = self.jeu_principal.interface_graphique.font_menu
        else:
            # print("Avertissement (Editeur): police par défaut pour boutons éditeur.") # Pour debug
            font_pour_boutons = pygame.font.Font(C.POLICE_DEFAUT, C.TAILLE_POLICE_MENU)

        btn_sauver = Bouton(ui_bouton_x_base, 70, 180, 40, "Sauvegarder", font=font_pour_boutons, action="sauver")
        self.boutons_editeur.append(btn_sauver)
        btn_tester = Bouton(ui_bouton_x_base, 120, 180, 40, "Tester", font=font_pour_boutons, action="tester")
        self.boutons_editeur.append(btn_tester)
        btn_nom = Bouton(ui_bouton_x_base, 170, 180, 40, "Nom Niveau", font=font_pour_boutons, action="changer_nom")
        self.boutons_editeur.append(btn_nom)

        btn_plus_L = Bouton(ui_bouton_x_base, 230, 85, 35, "L+", font=font_pour_boutons, action="L+")
        btn_moins_L = Bouton(ui_bouton_x_base + 95, 230, 85, 35, "L-", font=font_pour_boutons, action="L-")
        btn_plus_H = Bouton(ui_bouton_x_base, 275, 85, 35, "H+", font=font_pour_boutons, action="H+")
        btn_moins_H = Bouton(ui_bouton_x_base + 95, 275, 85, 35, "H-", font=font_pour_boutons, action="H-")
        self.boutons_editeur.extend([btn_plus_L, btn_moins_L, btn_plus_H, btn_moins_H])

    def definir_taille_grille(self, nouvelle_largeur, nouvelle_hauteur):
        nouvelle_largeur = max(5, min(30, nouvelle_largeur))
        nouvelle_hauteur = max(5, min(20, nouvelle_hauteur))

        ancienne_grille = self.grille
        self.grille = [[C.SOL for _ in range(nouvelle_largeur)] for _ in range(nouvelle_hauteur)]

        for y in range(min(self.hauteur_grille, nouvelle_hauteur)):
            for x in range(min(self.largeur_grille, nouvelle_largeur)):
                self.grille[y][x] = ancienne_grille[y][x]

        self.largeur_grille = nouvelle_largeur
        self.hauteur_grille = nouvelle_hauteur
        self.message_info = f"Taille: {self.largeur_grille}x{self.hauteur_grille}"
        self._creer_boutons_editeur()
        if self.jeu_principal:
            self.jeu_principal._adapter_taille_fenetre_pour_niveau()

    def placer_element(self, grid_x, grid_y):
        if 0 <= grid_x < self.largeur_grille and 0 <= grid_y < self.hauteur_grille:
            if self.element_selectionne == C.JOUEUR:
                for r_idx, row in enumerate(self.grille):
                    for c_idx, cell in enumerate(row):
                        if cell == C.JOUEUR or cell == C.JOUEUR_SUR_CIBLE:
                            self.grille[r_idx][c_idx] = C.CIBLE if self.grille[r_idx][
                                                                       c_idx] == C.JOUEUR_SUR_CIBLE else C.SOL

            case_actuelle = self.grille[grid_y][grid_x]
            if self.element_selectionne == C.JOUEUR:
                self.grille[grid_y][
                    grid_x] = C.JOUEUR_SUR_CIBLE if case_actuelle == C.CIBLE or case_actuelle == C.CAISSE_SUR_CIBLE else C.JOUEUR
            elif self.element_selectionne == C.CAISSE:
                self.grille[grid_y][
                    grid_x] = C.CAISSE_SUR_CIBLE if case_actuelle == C.CIBLE or case_actuelle == C.JOUEUR_SUR_CIBLE else C.CAISSE
            elif self.element_selectionne == C.CIBLE:
                if case_actuelle == C.JOUEUR:
                    self.grille[grid_y][grid_x] = C.JOUEUR_SUR_CIBLE
                elif case_actuelle == C.CAISSE:
                    self.grille[grid_y][grid_x] = C.CAISSE_SUR_CIBLE
                else:
                    self.grille[grid_y][grid_x] = C.CIBLE
            else:
                self.grille[grid_y][grid_x] = self.element_selectionne
            self.message_info = f"{self.element_selectionne} placé en ({grid_x},{grid_y})"

    def get_contenu_niveau_str(self):
        return "\n".join("".join(row) for row in self.grille)

    def sauvegarder_niveau(self):
        if not self.nom_niveau_en_cours.strip():
            self.message_info = "Erreur: Nom de niveau vide."
            return False
        contenu_str = self.get_contenu_niveau_str()
        if C.JOUEUR not in contenu_str and C.JOUEUR_SUR_CIBLE not in contenu_str:
            self.message_info = "Erreur: Le niveau doit contenir un joueur."
            return False

        sauvegarder_niveau_personnalise(self.nom_niveau_en_cours, contenu_str)
        self.message_info = f"'{self.nom_niveau_en_cours}' sauvegardé."
        if self.jeu_principal:
            self.jeu_principal.rafraichir_listes_niveaux()
        return True

    def tester_niveau(self):
        if not self.jeu_principal:
            self.message_info = "Erreur: Référence au jeu principal manquante pour tester."
            return
        contenu_str = self.get_contenu_niveau_str()
        if C.JOUEUR not in contenu_str and C.JOUEUR_SUR_CIBLE not in contenu_str:
            self.message_info = "Test: Aucun joueur défini."
            return
        self.jeu_principal.charger_niveau_temporaire_pour_test(contenu_str, self)
        self.message_info = "Mode Test. Echap pour revenir."

    def dessiner(self, surface, images, font_passee_par_interface):
        surface.fill(C.DARK_BACKGROUND)
        offset_x_grille = 20
        offset_y_grille = 70

        for y, row in enumerate(self.grille):
            for x, cell_type in enumerate(row):
                pos_x, pos_y = x * C.TAILLE_CASE + offset_x_grille, y * C.TAILLE_CASE + offset_y_grille

                fond_type = C.SOL
                if cell_type == C.CIBLE or cell_type == C.JOUEUR_SUR_CIBLE or cell_type == C.CAISSE_SUR_CIBLE:
                    fond_type = C.CIBLE

                img_key_fond = C.SOL  # Par défaut sol
                if fond_type == C.CIBLE: img_key_fond = C.CIBLE

                if img_key_fond in images:
                    surface.blit(images[img_key_fond], (pos_x, pos_y))
                else:
                    pygame.draw.rect(surface, C.ROSE if fond_type == C.CIBLE else C.GRIS_CLAIR,
                                     (pos_x, pos_y, C.TAILLE_CASE, C.TAILLE_CASE))

                element_img_key = None
                if cell_type == C.MUR:
                    element_img_key = C.MUR
                elif cell_type == C.CAISSE:
                    element_img_key = C.CAISSE
                elif cell_type == C.JOUEUR:
                    element_img_key = C.JOUEUR
                elif cell_type == C.CAISSE_SUR_CIBLE:
                    element_img_key = C.CAISSE_SUR_CIBLE
                elif cell_type == C.JOUEUR_SUR_CIBLE:
                    element_img_key = C.JOUEUR

                if element_img_key and element_img_key in images:
                    surface.blit(images[element_img_key], (pos_x, pos_y))
                elif element_img_key:
                    couleur_element = C.GRIS if cell_type == C.MUR else C.MARRON if cell_type == C.CAISSE else C.BLEU if cell_type == C.JOUEUR else None
                    if couleur_element: pygame.draw.rect(surface, couleur_element,
                                                         (pos_x + 5, pos_y + 5, C.TAILLE_CASE - 10, C.TAILLE_CASE - 10))
                pygame.draw.rect(surface, C.DARK_GRID_LINE, (pos_x, pos_y, C.TAILLE_CASE, C.TAILLE_CASE), 1)

        self.palette_rects.clear()
        palette_offset_x = offset_x_grille
        palette_offset_y = 15
        for i, item_type in enumerate(self.palette):
            rect = pygame.Rect(palette_offset_x + i * (C.TAILLE_CASE + 5), palette_offset_y, C.TAILLE_CASE,
                               C.TAILLE_CASE)
            self.palette_rects.append(rect)

            img_key_palette = item_type
            if item_type in images:
                surface.blit(images[img_key_palette], rect.topleft)
            else:
                pygame.draw.rect(surface, C.ROUGE, rect)

            if item_type == self.element_selectionne:
                pygame.draw.rect(surface, C.DARK_ACCENT_WARN, rect, 3)

        nom_display = self.temp_nom_niveau if self.input_nom_actif else self.nom_niveau_en_cours
        cursor_char = "_" if self.input_nom_actif and pygame.time.get_ticks() % 1000 < 500 else ""
        nom_texte_surface = font_passee_par_interface.render(f"Nom: {nom_display}{cursor_char}", True,
                                                             C.DARK_TEXT_PRIMARY)
        nom_rect_y_pos = palette_offset_y + C.TAILLE_CASE // 2 - nom_texte_surface.get_height() // 2
        surface.blit(nom_texte_surface,
                     (palette_offset_x + len(self.palette) * (C.TAILLE_CASE + 5) + 20, nom_rect_y_pos))

        info_texte = font_passee_par_interface.render(self.message_info, True, C.DARK_ACCENT_INFO)
        info_y_pos = self.hauteur_grille * C.TAILLE_CASE + offset_y_grille + 10
        surface.blit(info_texte, (
        offset_x_grille, info_y_pos if info_y_pos < surface.get_height() - 50 else surface.get_height() - 50))

        instr_texte = font_passee_par_interface.render("Clic: Placer | ESC: Quitter", True, C.DARK_TEXT_SECONDARY)
        surface.blit(instr_texte, (offset_x_grille, surface.get_height() - 30))

        pos_souris = pygame.mouse.get_pos()
        for btn in self.boutons_editeur:
            btn.verifier_survol(pos_souris)
            btn.dessiner(surface)

    def gerer_evenement(self, event):
        if self.input_nom_actif:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    self.nom_niveau_en_cours = self.temp_nom_niveau.strip() if self.temp_nom_niveau.strip() else self.nom_niveau_en_cours
                    self.input_nom_actif = False
                    self.message_info = f"Nom du niveau: {self.nom_niveau_en_cours}"
                elif event.key == pygame.K_BACKSPACE:
                    self.temp_nom_niveau = self.temp_nom_niveau[:-1]
                elif event.key == pygame.K_ESCAPE:
                    self.input_nom_actif = False
                    self.temp_nom_niveau = self.nom_niveau_en_cours
                else:
                    if event.unicode.isalnum() or event.unicode in ['-', '_', ' ']:
                        if len(self.temp_nom_niveau) < 25:
                            self.temp_nom_niveau += event.unicode
            return

        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                mouse_pos = event.pos
                for i, rect in enumerate(self.palette_rects):
                    if rect.collidepoint(mouse_pos):
                        self.element_selectionne = self.palette[i]
                        self.message_info = f"Outil: {self.element_selectionne}"
                        return
                offset_x_grille = 20;
                offset_y_grille = 70
                if offset_x_grille <= mouse_pos[0] < offset_x_grille + self.largeur_grille * C.TAILLE_CASE and \
                        offset_y_grille <= mouse_pos[1] < offset_y_grille + self.hauteur_grille * C.TAILLE_CASE:
                    grid_x = (mouse_pos[0] - offset_x_grille) // C.TAILLE_CASE
                    grid_y = (mouse_pos[1] - offset_y_grille) // C.TAILLE_CASE
                    self.placer_element(grid_x, grid_y)
                    return
                for btn in self.boutons_editeur:
                    action = btn.verifier_clic(mouse_pos)
                    if action:
                        if action == "sauver":
                            self.sauvegarder_niveau()
                        elif action == "tester":
                            self.tester_niveau()
                        elif action == "changer_nom":
                            self.input_nom_actif = True
                            self.temp_nom_niveau = self.nom_niveau_en_cours
                            self.message_info = "Saisissez le nom, puis Entrée."
                        elif action == "L+":
                            self.definir_taille_grille(self.largeur_grille + 1, self.hauteur_grille)
                        elif action == "L-":
                            self.definir_taille_grille(self.largeur_grille - 1, self.hauteur_grille)
                        elif action == "H+":
                            self.definir_taille_grille(self.largeur_grille, self.hauteur_grille + 1)
                        elif action == "H-":
                            self.definir_taille_grille(self.largeur_grille, self.hauteur_grille - 1)
                        return