import pygame
from . import constantes as C
from .classes import Niveau, Case, Caisse, Joueur
from .utilitaires import sauvegarder_niveau_personnalise_en_fichier  # MODIFIÉ
from .ui_elements import Bouton
from . import solveurs


class EditeurNiveaux:
    def __init__(self, largeur_grille=15, hauteur_grille=10, jeu_principal_ref=None):
        self.largeur_grille = largeur_grille
        self.hauteur_grille = hauteur_grille
        self.grille = [[C.SOL for _ in range(largeur_grille)] for _ in range(hauteur_grille)]
        self.element_selectionne = C.MUR
        self.nom_niveau_en_cours = "MonNiveauPerso"
        self.message_info = "Bienvenue dans l'éditeur !"
        self.message_couleur = C.DARK_ACCENT_INFO
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
            font_pour_boutons = pygame.font.Font(C.POLICE_DEFAUT, C.TAILLE_POLICE_MENU)

        actions_boutons = [
            ("Sauvegarder", "sauver", 70), ("Tester", "tester", 120), ("Nom Niveau", "changer_nom", 170)
        ]
        for texte, action, y_offset in actions_boutons:
            btn = Bouton(ui_bouton_x_base, y_offset, 180, 40, texte, font=font_pour_boutons, action=action)
            self.boutons_editeur.append(btn)

        taille_btns_pos = [
            ("L+", "L+", ui_bouton_x_base, 230, 85, 35), ("L-", "L-", ui_bouton_x_base + 95, 230, 85, 35),
            ("H+", "H+", ui_bouton_x_base, 275, 85, 35), ("H-", "H-", ui_bouton_x_base + 95, 275, 85, 35)
        ]
        for texte, action, x, y, w, h in taille_btns_pos:
            btn = Bouton(x, y, w, h, texte, font=font_pour_boutons, action=action)
            self.boutons_editeur.append(btn)

    def definir_taille_grille(self, nouvelle_largeur, nouvelle_hauteur):
        nouvelle_largeur = max(5, min(30, nouvelle_largeur));
        nouvelle_hauteur = max(5, min(20, nouvelle_hauteur))
        ancienne_grille = self.grille
        self.grille = [[C.SOL for _ in range(nouvelle_largeur)] for _ in range(nouvelle_hauteur)]
        for y_idx in range(min(self.hauteur_grille, nouvelle_hauteur)):
            for x_idx in range(min(self.largeur_grille, nouvelle_largeur)):
                self.grille[y_idx][x_idx] = ancienne_grille[y_idx][x_idx]
        self.largeur_grille = nouvelle_largeur;
        self.hauteur_grille = nouvelle_hauteur
        self.message_info = f"Taille: {self.largeur_grille}x{self.hauteur_grille}";
        self.message_couleur = C.DARK_ACCENT_INFO
        self._creer_boutons_editeur()
        if self.jeu_principal: self.jeu_principal._adapter_taille_fenetre_pour_niveau()

    def placer_element(self, grid_x, grid_y):
        if 0 <= grid_x < self.largeur_grille and 0 <= grid_y < self.hauteur_grille:
            if self.element_selectionne == C.JOUEUR:
                for r, row in enumerate(self.grille):
                    for c, cell in enumerate(row):
                        if cell == C.JOUEUR or cell == C.JOUEUR_SUR_CIBLE:
                            self.grille[r][c] = C.CIBLE if self.grille[r][c] == C.JOUEUR_SUR_CIBLE else C.SOL
            case_actuelle = self.grille[grid_y][grid_x]
            if self.element_selectionne == C.JOUEUR:
                self.grille[grid_y][grid_x] = C.JOUEUR_SUR_CIBLE if case_actuelle in [C.CIBLE,
                                                                                      C.CAISSE_SUR_CIBLE] else C.JOUEUR
            elif self.element_selectionne == C.CAISSE:
                self.grille[grid_y][grid_x] = C.CAISSE_SUR_CIBLE if case_actuelle in [C.CIBLE,
                                                                                      C.JOUEUR_SUR_CIBLE] else C.CAISSE
            elif self.element_selectionne == C.CIBLE:
                if case_actuelle == C.JOUEUR:
                    self.grille[grid_y][grid_x] = C.JOUEUR_SUR_CIBLE
                elif case_actuelle == C.CAISSE:
                    self.grille[grid_y][grid_x] = C.CAISSE_SUR_CIBLE
                else:
                    self.grille[grid_y][grid_x] = C.CIBLE
            else:
                self.grille[grid_y][grid_x] = self.element_selectionne
            self.message_info = f"{self.element_selectionne} placé en ({grid_x},{grid_y})";
            self.message_couleur = C.DARK_ACCENT_INFO

    def get_contenu_niveau_str(self):
        return "\n".join("".join(row) for row in self.grille)

    def verifier_solvabilite(self):
        contenu_str = self.get_contenu_niveau_str()
        if C.JOUEUR not in contenu_str and C.JOUEUR_SUR_CIBLE not in contenu_str:
            self.message_info = "Erreur: Joueur requis pour vérifier solvabilité.";
            self.message_couleur = C.ROUGE
            return False

        num_caisses = contenu_str.count(C.CAISSE) + contenu_str.count(C.CAISSE_SUR_CIBLE)
        num_cibles = contenu_str.count(C.CIBLE) + contenu_str.count(C.CAISSE_SUR_CIBLE) + contenu_str.count(
            C.JOUEUR_SUR_CIBLE)

        if num_caisses == 0 and num_cibles > 0:
            self.message_info = "Avertissement: Aucune caisse pour les cibles.";
            self.message_couleur = C.DARK_ACCENT_WARN
        if num_caisses > 0 and num_cibles == 0:
            self.message_info = "Avertissement: Aucune cible pour les caisses.";
            self.message_couleur = C.DARK_ACCENT_WARN
        if num_caisses != num_cibles and num_caisses > 0 and num_cibles > 0:
            self.message_info = "Avertissement: Nombre de caisses et cibles différent.";
            self.message_couleur = C.DARK_ACCENT_WARN

        self.message_info = "Vérification (BFS) en cours...";
        self.message_couleur = C.DARK_ACCENT_INFO
        if self.jeu_principal and self.jeu_principal.interface_graphique:
            self.dessiner(self.jeu_principal.interface_graphique.fenetre,
                          self.jeu_principal.interface_graphique.images,
                          self.jeu_principal.interface_graphique.font_menu)
            pygame.display.flip()
            pygame.event.pump()

        niveau_test = Niveau(nom_fichier_ou_contenu=contenu_str, est_contenu_direct=True)
        if not niveau_test.joueur or (num_caisses > 0 and not niveau_test.caisses) or (
                num_cibles > 0 and not niveau_test.cibles):
            self.message_info = "Niveau invalide (joueur/caisse/cible manquant).";
            self.message_couleur = C.ROUGE
            return False

        if num_caisses == 0 and num_cibles == 0:
            self.message_info = "Niveau solvable (pas de caisses/cibles).";
            self.message_couleur = C.DARK_ACCENT_GOOD
            return True

        etat_initial = niveau_test.get_etat_pour_solveur()
        if not etat_initial:
            self.message_info = "État initial invalide pour le solveur.";
            self.message_couleur = C.ROUGE
            return False

        solveur = solveurs.SolveurBFS(etat_initial)
        solution = solveur.resoudre(niveau_test)

        if solution:
            self.message_info = "Niveau solvable (BFS) !";
            self.message_couleur = C.DARK_ACCENT_GOOD
            return True
        else:
            self.message_info = "ERREUR: Aucune solution trouvée (BFS).";
            self.message_couleur = C.ROUGE
            return False

    def sauvegarder_niveau(self):
        if not self.nom_niveau_en_cours.strip():
            self.message_info = "Erreur: Nom de niveau vide.";
            self.message_couleur = C.ROUGE
            return False

        if not self.verifier_solvabilite():
            return False

        contenu_str = self.get_contenu_niveau_str()
        # MODIFIÉ pour utiliser la nouvelle fonction de sauvegarde
        if sauvegarder_niveau_personnalise_en_fichier(self.nom_niveau_en_cours, contenu_str):
            self.message_info = f"'{self.nom_niveau_en_cours}' sauvegardé (solvable).";
            self.message_couleur = C.DARK_ACCENT_GOOD
            if self.jeu_principal: self.jeu_principal.rafraichir_listes_niveaux()
            return True
        else:
            self.message_info = f"Erreur sauvegarde fichier pour '{self.nom_niveau_en_cours}'.";
            self.message_couleur = C.ROUGE
            return False

    def tester_niveau(self):
        if not self.jeu_principal: self.message_info = "Erreur: Réf jeu manquante."; self.message_couleur = C.ROUGE; return
        contenu_str = self.get_contenu_niveau_str()
        if C.JOUEUR not in contenu_str and C.JOUEUR_SUR_CIBLE not in contenu_str: self.message_info = "Test: Joueur requis."; self.message_couleur = C.ROUGE; return
        self.jeu_principal.charger_niveau_temporaire_pour_test(contenu_str, self)
        self.message_info = "Mode Test. Echap pour revenir.";
        self.message_couleur = C.DARK_ACCENT_INFO

    def dessiner(self, surface, images, font):
        surface.fill(C.DARK_BACKGROUND)
        off_x_g, off_y_g = 20, 70
        for y_idx, row in enumerate(self.grille):
            for x_idx, cell_type in enumerate(row):
                px, py = x_idx * C.TAILLE_CASE + off_x_g, y_idx * C.TAILLE_CASE + off_y_g
                fond_t = C.SOL;
                if cell_type in [C.CIBLE, C.JOUEUR_SUR_CIBLE, C.CAISSE_SUR_CIBLE]: fond_t = C.CIBLE
                img_k_f = C.SOL;
                if fond_t == C.CIBLE: img_k_f = C.CIBLE
                if img_k_f in images:
                    surface.blit(images[img_k_f], (px, py))
                else:
                    pygame.draw.rect(surface, C.ROSE if fond_t == C.CIBLE else C.GRIS_CLAIR,
                                     (px, py, C.TAILLE_CASE, C.TAILLE_CASE))

                elem_k = None
                if cell_type == C.MUR:
                    elem_k = C.MUR
                elif cell_type == C.CAISSE:
                    elem_k = C.CAISSE
                elif cell_type == C.JOUEUR:
                    elem_k = C.JOUEUR
                elif cell_type == C.CAISSE_SUR_CIBLE:
                    elem_k = C.CAISSE_SUR_CIBLE
                elif cell_type == C.JOUEUR_SUR_CIBLE:
                    elem_k = C.JOUEUR
                if elem_k and elem_k in images: surface.blit(images[elem_k], (px, py))
                pygame.draw.rect(surface, C.DARK_GRID_LINE, (px, py, C.TAILLE_CASE, C.TAILLE_CASE), 1)

        self.palette_rects.clear();
        pal_x, pal_y = off_x_g, 15
        for i, item_t in enumerate(self.palette):
            rect = pygame.Rect(pal_x + i * (C.TAILLE_CASE + 5), pal_y, C.TAILLE_CASE, C.TAILLE_CASE)
            self.palette_rects.append(rect)
            if item_t in images: surface.blit(images[item_t], rect.topleft)
            if item_t == self.element_selectionne: pygame.draw.rect(surface, C.DARK_ACCENT_WARN, rect, 3)

        nom_d = self.temp_nom_niveau if self.input_nom_actif else self.nom_niveau_en_cours
        cur = "_" if self.input_nom_actif and pygame.time.get_ticks() % 1000 < 500 else ""
        nom_s = font.render(f"Nom: {nom_d}{cur}", True, C.DARK_TEXT_PRIMARY)
        nom_ry = pal_y + C.TAILLE_CASE // 2 - nom_s.get_height() // 2
        surface.blit(nom_s, (pal_x + len(self.palette) * (C.TAILLE_CASE + 5) + 20, nom_ry))

        info_s = font.render(self.message_info, True, self.message_couleur)
        info_y = self.hauteur_grille * C.TAILLE_CASE + off_y_g + 10
        surface.blit(info_s, (off_x_g, info_y if info_y < surface.get_height() - 50 else surface.get_height() - 50))
        instr_s = font.render("Clic: Placer | ESC: Quitter", True, C.DARK_TEXT_SECONDARY)
        surface.blit(instr_s, (off_x_g, surface.get_height() - 30))

        mouse_pos = pygame.mouse.get_pos()
        for btn in self.boutons_editeur: btn.verifier_survol(mouse_pos); btn.dessiner(surface)

    def gerer_evenement(self, event):
        if self.input_nom_actif:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    self.nom_niveau_en_cours = self.temp_nom_niveau.strip() or self.nom_niveau_en_cours
                    self.input_nom_actif = False;
                    self.message_info = f"Nom: {self.nom_niveau_en_cours}";
                    self.message_couleur = C.DARK_ACCENT_INFO
                elif event.key == pygame.K_BACKSPACE:
                    self.temp_nom_niveau = self.temp_nom_niveau[:-1]
                elif event.key == pygame.K_ESCAPE:
                    self.input_nom_actif = False; self.temp_nom_niveau = self.nom_niveau_en_cours
                elif len(self.temp_nom_niveau) < 25 and (event.unicode.isalnum() or event.unicode in ['-', '_', ' ']):
                    self.temp_nom_niveau += event.unicode
            return
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mouse_pos = event.pos
            for i, rect in enumerate(self.palette_rects):
                if rect.collidepoint(mouse_pos): self.element_selectionne = self.palette[
                    i]; self.message_info = f"Outil: {self.element_selectionne}"; self.message_couleur = C.DARK_ACCENT_INFO; return
            off_x_g, off_y_g = 20, 70
            if off_x_g <= mouse_pos[0] < off_x_g + self.largeur_grille * C.TAILLE_CASE and \
                    off_y_g <= mouse_pos[1] < off_y_g + self.hauteur_grille * C.TAILLE_CASE:
                gx = (mouse_pos[0] - off_x_g) // C.TAILLE_CASE;
                gy = (mouse_pos[1] - off_y_g) // C.TAILLE_CASE
                self.placer_element(gx, gy);
                return
            for btn in self.boutons_editeur:
                action = btn.verifier_clic(mouse_pos)
                if action:
                    actions_map = {"sauver": self.sauvegarder_niveau, "tester": self.tester_niveau,
                                   "L+": lambda: self.definir_taille_grille(self.largeur_grille + 1,
                                                                            self.hauteur_grille),
                                   "L-": lambda: self.definir_taille_grille(self.largeur_grille - 1,
                                                                            self.hauteur_grille),
                                   "H+": lambda: self.definir_taille_grille(self.largeur_grille,
                                                                            self.hauteur_grille + 1),
                                   "H-": lambda: self.definir_taille_grille(self.largeur_grille,
                                                                            self.hauteur_grille - 1)}
                    if action == "changer_nom":
                        self.input_nom_actif = True; self.temp_nom_niveau = self.nom_niveau_en_cours; self.message_info = "Saisir nom, puis Entrée."; self.message_couleur = C.DARK_ACCENT_INFO
                    elif action in actions_map:
                        actions_map[action]()
                    return