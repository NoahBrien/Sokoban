import pygame
from . import constantes as C
from .classes import Niveau
from .utilitaires import sauvegarder_niveau_personnalise_en_fichier
from .ui_elements import Bouton
from . import solveurs


class EditeurNiveaux:
    def __init__(self, largeur_grille=15, hauteur_grille=10, jeu_principal_ref=None):
        """Initialise l'éditeur de niveaux."""
        self.largeur_grille = largeur_grille
        self.hauteur_grille = hauteur_grille
        self.grille = [[C.SOL for _x in range(self.largeur_grille)] for _y in range(self.hauteur_grille)]
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
        """Crée ou recrée les boutons de l'interface de l'éditeur."""
        self.boutons_editeur = []
        taille_case_pour_ui_pos = C.TAILLE_CASE
        if self.jeu_principal and hasattr(self.jeu_principal, 'taille_case_effective'):
            taille_case_pour_ui_pos = self.jeu_principal.taille_case_effective

        ui_bouton_x_base = 20 + self.largeur_grille * taille_case_pour_ui_pos + 40

        font_pour_boutons = self.jeu_principal.interface_graphique.font_menu if self.jeu_principal and hasattr(
            self.jeu_principal, 'interface_graphique') else pygame.font.Font(C.POLICE_DEFAUT, C.TAILLE_POLICE_MENU)
        actions_boutons = [("Sauvegarder", "sauver", 70), ("Tester", "tester", 120), ("Nom Niveau", "changer_nom", 170)]
        for texte, action, y_offset in actions_boutons:
            self.boutons_editeur.append(
                Bouton(ui_bouton_x_base, y_offset, 180, 40, texte, font=font_pour_boutons, action=action))
        taille_btns_pos = [
            ("L+", "L+", ui_bouton_x_base, 230, 85, 35), ("L-", "L-", ui_bouton_x_base + 95, 230, 85, 35),
            ("H+", "H+", ui_bouton_x_base, 275, 85, 35), ("H-", "H-", ui_bouton_x_base + 95, 275, 85, 35)
        ]
        for texte, action, x, y, w, h in taille_btns_pos:
            self.boutons_editeur.append(Bouton(x, y, w, h, texte, font=font_pour_boutons, action=action))

    def definir_taille_grille(self, nouvelle_largeur, nouvelle_hauteur):
        """Définit une nouvelle taille pour la grille de l'éditeur."""
        nouvelle_largeur = max(5, min(50, nouvelle_largeur))
        nouvelle_hauteur = max(5, min(30, nouvelle_hauteur))
        ancienne_grille_contenu = self.grille
        ancienne_h, ancienne_l = self.hauteur_grille, self.largeur_grille
        self.grille = [[C.SOL for _ in range(nouvelle_largeur)] for _ in range(nouvelle_hauteur)]
        for y in range(min(ancienne_h, nouvelle_hauteur)):
            for x in range(min(ancienne_l, nouvelle_largeur)):
                self.grille[y][x] = ancienne_grille_contenu[y][x]
        self.largeur_grille, self.hauteur_grille = nouvelle_largeur, nouvelle_hauteur
        self.message_info = f"Taille: {self.largeur_grille}x{self.hauteur_grille}";
        self.message_couleur = C.DARK_ACCENT_INFO
        if self.jeu_principal:
            self._creer_boutons_editeur()
            self.jeu_principal._adapter_taille_fenetre_pour_niveau()

    def placer_element(self, grid_x, grid_y):
        """Place l'élément actuellement sélectionné sur la grille de l'éditeur."""
        if 0 <= grid_x < self.largeur_grille and 0 <= grid_y < self.hauteur_grille:
            if self.element_selectionne == C.JOUEUR:
                for r in range(self.hauteur_grille):
                    for c in range(self.largeur_grille):
                        if self.grille[r][c] == C.JOUEUR:
                            self.grille[r][c] = C.SOL
                        elif self.grille[r][c] == C.JOUEUR_SUR_CIBLE:
                            self.grille[r][c] = C.CIBLE
            case_existante = self.grille[grid_y][grid_x]
            if self.element_selectionne == C.JOUEUR:
                self.grille[grid_y][
                    grid_x] = C.JOUEUR_SUR_CIBLE if case_existante == C.CIBLE or case_existante == C.CAISSE_SUR_CIBLE else C.JOUEUR
            elif self.element_selectionne == C.CAISSE:
                self.grille[grid_y][
                    grid_x] = C.CAISSE_SUR_CIBLE if case_existante == C.CIBLE or case_existante == C.JOUEUR_SUR_CIBLE else C.CAISSE
            elif self.element_selectionne == C.CIBLE:
                if case_existante == C.JOUEUR:
                    self.grille[grid_y][grid_x] = C.JOUEUR_SUR_CIBLE
                elif case_existante == C.CAISSE:
                    self.grille[grid_y][grid_x] = C.CAISSE_SUR_CIBLE
                else:
                    self.grille[grid_y][grid_x] = C.CIBLE
            elif self.element_selectionne == C.MUR:
                self.grille[grid_y][grid_x] = C.MUR
            elif self.element_selectionne == C.SOL:
                if case_existante == C.JOUEUR_SUR_CIBLE or case_existante == C.CAISSE_SUR_CIBLE:
                    self.grille[grid_y][grid_x] = C.CIBLE
                else:
                    self.grille[grid_y][grid_x] = C.SOL
            else:
                self.grille[grid_y][grid_x] = self.element_selectionne
            self.message_info = f"{self.element_selectionne} placé en ({grid_x},{grid_y})";
            self.message_couleur = C.DARK_ACCENT_INFO

    def get_contenu_niveau_str(self):
        """Retourne le contenu actuel de la grille de l'éditeur sous forme de chaîne de caractères."""
        return "\n".join("".join(ligne_caracteres).rstrip() for ligne_caracteres in self.grille).strip('\n')

    def verifier_conditions_base(self):
        """Vérifie les conditions de base pour un niveau valide (joueur unique, etc.)."""
        contenu_str = self.get_contenu_niveau_str()
        nb_joueurs = contenu_str.count(C.JOUEUR) + contenu_str.count(C.JOUEUR_SUR_CIBLE)
        if nb_joueurs == 0: self.message_info = "Erreur: Joueur requis."; self.message_couleur = C.ROUGE; return False
        if nb_joueurs > 1: self.message_info = "Erreur: Un seul joueur."; self.message_couleur = C.ROUGE; return False
        num_caisses = contenu_str.count(C.CAISSE) + contenu_str.count(C.CAISSE_SUR_CIBLE)
        num_cibles = contenu_str.count(C.CIBLE) + contenu_str.count(C.CAISSE_SUR_CIBLE) + contenu_str.count(
            C.JOUEUR_SUR_CIBLE)
        if num_caisses == 0 and num_cibles == 0: return True
        if num_caisses != num_cibles: self.message_info = "Info: Nb caisses != Nb cibles."; self.message_couleur = C.DARK_ACCENT_WARN
        if num_caisses > 0 and num_cibles == 0: self.message_info = "Info: Caisses sans cibles."; self.message_couleur = C.DARK_ACCENT_WARN
        if num_cibles > 0 and num_caisses == 0: self.message_info = "Info: Cibles sans caisses."; self.message_couleur = C.DARK_ACCENT_WARN
        return True

    def verifier_solvabilite(self):
        """Vérifie si le niveau actuellement édité est solvable en utilisant BFS."""
        if not self.verifier_conditions_base(): return False
        contenu_str = self.get_contenu_niveau_str()
        niveau_test = Niveau(nom_fichier_ou_contenu=contenu_str, est_contenu_direct=True)
        if not niveau_test.joueur: self.message_info = "Erreur interne: Joueur non chargé."; self.message_couleur = C.ROUGE; return False
        if not niveau_test.caisses and not niveau_test.cibles: self.message_info = "Solvable (pas de caisses/cibles)."; self.message_couleur = C.DARK_ACCENT_GOOD; return True
        self.message_info = "Vérification (BFS)...";
        self.message_couleur = C.DARK_ACCENT_INFO
        if self.jeu_principal and self.jeu_principal.interface_graphique:
            taille_case_eff = self.jeu_principal.taille_case_effective
            textures_act = self.jeu_principal.textures_active
            view_offset_x, view_offset_y = (
            self.jeu_principal.view_offset_x, self.jeu_principal.view_offset_y) if self.jeu_principal else (0, 0)
            self.dessiner(self.jeu_principal.interface_graphique.fenetre,
                          self.jeu_principal.interface_graphique.images_zoomees,
                          self.jeu_principal.interface_graphique.font_menu,
                          textures_act, taille_case_eff, view_offset_x, view_offset_y)
            pygame.display.flip();
            pygame.event.pump()
        etat_initial = niveau_test.get_etat_pour_solveur()
        if not etat_initial: self.message_info = "État initial invalide."; self.message_couleur = C.ROUGE; return False
        solveur = solveurs.SolveurBFS(etat_initial)
        solution, _ = solveur.resoudre(niveau_test)
        if solution is not None:
            self.message_info = "Niveau solvable (BFS)!"; self.message_couleur = C.DARK_ACCENT_GOOD; return True
        else:
            self.message_info = "Solveur BFS: Non solvable."; self.message_couleur = C.ROUGE; return False

    def sauvegarder_niveau(self):
        """Sauvegarde le niveau actuel dans un fichier personnalisé."""
        if not self.nom_niveau_en_cours.strip(): self.message_info = "Erreur: Nom vide."; self.message_couleur = C.ROUGE; return False
        if not self.verifier_conditions_base(): return False
        if not self.verifier_solvabilite(): return False
        contenu_str = self.get_contenu_niveau_str()
        if sauvegarder_niveau_personnalise_en_fichier(self.nom_niveau_en_cours, contenu_str):
            self.message_info = f"'{self.nom_niveau_en_cours}' sauvegardé!";
            self.message_couleur = C.DARK_ACCENT_GOOD
            if self.jeu_principal: self.jeu_principal.rafraichir_listes_niveaux()
            return True
        else:
            self.message_info = f"Erreur sauvegarde."; self.message_couleur = C.ROUGE; return False

    def tester_niveau(self):
        """Passe en mode test pour le niveau actuellement édité."""
        if not self.jeu_principal: self.message_info = "Erreur: Réf jeu."; self.message_couleur = C.ROUGE; return
        if not self.verifier_conditions_base(): return
        contenu_str = self.get_contenu_niveau_str()
        self.jeu_principal.charger_niveau_temporaire_pour_test(contenu_str, self)
        self.message_info = "Mode Test. ESC pour revenir.";
        self.message_couleur = C.DARK_ACCENT_INFO

    def dessiner(self, surface, images_zoomees, font, textures_active, taille_case_effective, view_offset_x=0,
                 view_offset_y=0):
        """Dessine l'interface de l'éditeur, y compris la grille, la palette et les boutons."""
        surface.fill(C.DARK_BACKGROUND)
        offset_x_grille_base, offset_y_grille_base = 20, 70
        for y_idx in range(self.hauteur_grille):
            for x_idx in range(self.largeur_grille):
                cell_char = self.grille[y_idx][x_idx]
                pos_x = x_idx * taille_case_effective + offset_x_grille_base - view_offset_x
                pos_y = y_idx * taille_case_effective + offset_y_grille_base - view_offset_y
                rect_cell_tuple = (pos_x, pos_y, taille_case_effective, taille_case_effective)

                fallback_fond_color = C.FALLBACK_SOL
                img_key_fond = C.IMG_SOL
                if cell_char in [C.CIBLE, C.JOUEUR_SUR_CIBLE, C.CAISSE_SUR_CIBLE]:
                    img_key_fond = C.IMG_CIBLE
                    fallback_fond_color = C.FALLBACK_CIBLE
                if textures_active and C.IMG_SOL in images_zoomees and images_zoomees[C.IMG_SOL]:
                    surface.blit(images_zoomees[C.IMG_SOL], (pos_x, pos_y))
                else:
                    pygame.draw.rect(surface, C.FALLBACK_SOL, rect_cell_tuple)
                if img_key_fond == C.IMG_CIBLE:
                    if textures_active and C.IMG_CIBLE in images_zoomees and images_zoomees[C.IMG_CIBLE]:
                        surface.blit(images_zoomees[C.IMG_CIBLE], (pos_x, pos_y))
                    else:
                        pygame.draw.rect(surface, C.FALLBACK_CIBLE, rect_cell_tuple)

                img_key_element, fallback_element_color = None, None
                if cell_char == C.MUR:
                    img_key_element, fallback_element_color = C.IMG_MUR, C.FALLBACK_MUR
                elif cell_char == C.JOUEUR:
                    img_key_element, fallback_element_color = C.IMG_JOUEUR, C.FALLBACK_JOUEUR
                elif cell_char == C.CAISSE:
                    img_key_element, fallback_element_color = C.IMG_CAISSE, C.FALLBACK_CAISSE
                elif cell_char == C.JOUEUR_SUR_CIBLE:
                    img_key_element, fallback_element_color = C.IMG_JOUEUR, C.FALLBACK_JOUEUR
                elif cell_char == C.CAISSE_SUR_CIBLE:
                    img_key_element, fallback_element_color = C.IMG_CAISSE_SUR_CIBLE, C.FALLBACK_CAISSE_SUR_CIBLE
                if img_key_element:
                    if textures_active and img_key_element in images_zoomees and images_zoomees.get(img_key_element):
                        surface.blit(images_zoomees[img_key_element], (pos_x, pos_y))
                    elif fallback_element_color:
                        pygame.draw.rect(surface, fallback_element_color, rect_cell_tuple)
                pygame.draw.rect(surface, C.DARK_GRID_LINE, rect_cell_tuple, 1)

        self.palette_rects.clear()
        pal_x_start, pal_y_start = offset_x_grille_base - view_offset_x, 15  # Palette relative à la vue aussi
        taille_case_palette = C.TAILLE_CASE
        map_char_to_imgkey = {C.MUR: C.IMG_MUR, C.SOL: C.IMG_SOL, C.CAISSE: C.IMG_CAISSE, C.CIBLE: C.IMG_CIBLE,
                              C.JOUEUR: C.IMG_JOUEUR}
        map_char_to_fallback = {C.MUR: C.FALLBACK_MUR, C.SOL: C.FALLBACK_SOL, C.CAISSE: C.FALLBACK_CAISSE,
                                C.CIBLE: C.FALLBACK_CIBLE, C.JOUEUR: C.FALLBACK_JOUEUR}
        for i, item_char_palette in enumerate(self.palette):
            rect_p = pygame.Rect(pal_x_start + i * (taille_case_palette + 5), pal_y_start, taille_case_palette,
                                 taille_case_palette)
            self.palette_rects.append(rect_p)
            img_key_pal = map_char_to_imgkey.get(item_char_palette)
            if textures_active and img_key_pal and self.jeu_principal and self.jeu_principal.interface_graphique.images_base.get(
                    img_key_pal):
                if self.jeu_principal.interface_graphique.images_base.get(C.IMG_SOL):
                    surface.blit(self.jeu_principal.interface_graphique.images_base[C.IMG_SOL], rect_p.topleft)
                surface.blit(self.jeu_principal.interface_graphique.images_base[img_key_pal], rect_p.topleft)
            else:
                fallback_color_pal = map_char_to_fallback.get(item_char_palette, C.ROUGE)
                if item_char_palette == C.CIBLE: pygame.draw.rect(surface, C.FALLBACK_SOL, rect_p)
                pygame.draw.rect(surface, fallback_color_pal, rect_p)
            if item_char_palette == self.element_selectionne:
                pygame.draw.rect(surface, C.DARK_ACCENT_WARN, rect_p, 3)

        nom_display = self.temp_nom_niveau if self.input_nom_actif else self.nom_niveau_en_cours
        cursor = "_" if self.input_nom_actif and pygame.time.get_ticks() % 1000 < 500 else ""
        nom_s = font.render(f"Nom: {nom_display}{cursor}", True, C.DARK_TEXT_PRIMARY)
        nom_x_pos = pal_x_start + len(self.palette) * (taille_case_palette + 5) + 20
        nom_ry = pal_y_start + taille_case_palette // 2 - nom_s.get_height() // 2
        surface.blit(nom_s, (nom_x_pos, nom_ry))
        info_s = font.render(self.message_info, True, self.message_couleur)
        info_y = offset_y_grille_base + self.hauteur_grille * taille_case_effective + 10 - view_offset_y
        surface.blit(info_s, (offset_x_grille_base - view_offset_x, min(info_y, surface.get_height() - 50)))
        instr_s = font.render("Clic: Placer | ESC: Quitter / Annuler | Molette: Zoom", True, C.DARK_TEXT_SECONDARY)
        surface.blit(instr_s, (offset_x_grille_base - view_offset_x, surface.get_height() - 30))
        mouse_pos = pygame.mouse.get_pos()

        # Boutons de l'éditeur: Positionnés à droite de la grille DESSINÉE
        ui_bouton_x_base_dessin = offset_x_grille_base + self.largeur_grille * taille_case_effective + 40 - view_offset_x

        # Recréer les boutons si leur X attendu a changé à cause du zoom/view_offset
        # (Alternative: mettre à jour les rects des boutons existants)
        # Simple check sur le premier bouton pour décider de recréer:
        recreer_boutons_editeur = not self.boutons_editeur
        if self.boutons_editeur and self.boutons_editeur[0].rect.x != ui_bouton_x_base_dessin:
            recreer_boutons_editeur = True

        if recreer_boutons_editeur:
            self.boutons_editeur_sauvegarde = []  # Pour stocker les attributs d'origine
            font_pour_boutons = self.jeu_principal.interface_graphique.font_menu if self.jeu_principal else pygame.font.Font(
                C.POLICE_DEFAUT, C.TAILLE_POLICE_MENU)
            actions_boutons = [("Sauvegarder", "sauver", 70), ("Tester", "tester", 120),
                               ("Nom Niveau", "changer_nom", 170)]
            for texte, action, y_offset in actions_boutons:
                self.boutons_editeur_sauvegarde.append(
                    {'x': ui_bouton_x_base_dessin, 'y': y_offset, 'w': 180, 'h': 40, 'txt': texte,
                     'font': font_pour_boutons, 'act': action})
            taille_btns_pos_orig = [
                (ui_bouton_x_base_dessin, 230, 85, 35), (ui_bouton_x_base_dessin + 95, 230, 85, 35),
                (ui_bouton_x_base_dessin, 275, 85, 35), (ui_bouton_x_base_dessin + 95, 275, 85, 35)
            ]
            actions_taille = ["L+", "L-", "H+", "H-"]
            textes_taille = ["L+", "L-", "H+", "H-"]
            for i, (x, y, w, h) in enumerate(taille_btns_pos_orig):
                self.boutons_editeur_sauvegarde.append(
                    {'x': x, 'y': y, 'w': w, 'h': h, 'txt': textes_taille[i], 'font': font_pour_boutons,
                     'act': actions_taille[i]})

            self.boutons_editeur = []
            for b_data in self.boutons_editeur_sauvegarde:
                self.boutons_editeur.append(
                    Bouton(b_data['x'], b_data['y'], b_data['w'], b_data['h'], b_data['txt'], font=b_data['font'],
                           action=b_data['act']))

        for btn in self.boutons_editeur: btn.verifier_survol(mouse_pos); btn.dessiner(surface)

    def gerer_evenement(self, event, taille_case_effective):
        """Gère les événements pour l'éditeur, en tenant compte de la taille de case effective."""
        if self.input_nom_actif:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    self.nom_niveau_en_cours = self.temp_nom_niveau.strip() if self.temp_nom_niveau.strip() else "NiveauSansNom"
                    self.input_nom_actif = False;
                    self.message_info = f"Nom: {self.nom_niveau_en_cours}";
                    self.message_couleur = C.DARK_ACCENT_INFO
                elif event.key == pygame.K_BACKSPACE:
                    self.temp_nom_niveau = self.temp_nom_niveau[:-1]
                elif event.key == pygame.K_ESCAPE:
                    self.input_nom_actif = False; self.temp_nom_niveau = self.nom_niveau_en_cours; self.message_info = "Saisie nom annulée."; self.message_couleur = C.DARK_ACCENT_WARN
                elif len(self.temp_nom_niveau) < 30 and (event.unicode.isalnum() or event.unicode in ['-', '_', ' ']):
                    self.temp_nom_niveau += event.unicode
            return
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mouse_pos = event.pos
            for i, rect_pal in enumerate(self.palette_rects):
                if rect_pal.collidepoint(mouse_pos):
                    self.element_selectionne = self.palette[i];
                    self.message_info = f"Outil: {self.element_selectionne}";
                    self.message_couleur = C.DARK_ACCENT_INFO;
                    return

            offset_x_grille_base, offset_y_grille_base = 20, 70
            view_offset_x, view_offset_y = (
            self.jeu_principal.view_offset_x, self.jeu_principal.view_offset_y) if self.jeu_principal else (0, 0)
            grille_abs_x = offset_x_grille_base - view_offset_x
            grille_abs_y = offset_y_grille_base - view_offset_y
            zone_grille_x_fin = grille_abs_x + self.largeur_grille * taille_case_effective
            zone_grille_y_fin = grille_abs_y + self.hauteur_grille * taille_case_effective

            if grille_abs_x <= mouse_pos[0] < zone_grille_x_fin and \
                    grille_abs_y <= mouse_pos[1] < zone_grille_y_fin:
                grid_x = (mouse_pos[0] - grille_abs_x) // taille_case_effective
                grid_y = (mouse_pos[1] - grille_abs_y) // taille_case_effective
                if 0 <= grid_x < self.largeur_grille and 0 <= grid_y < self.hauteur_grille:
                    self.placer_element(grid_x, grid_y);
                    return

            for btn in self.boutons_editeur:
                action = btn.verifier_clic(mouse_pos)
                if action:
                    if action == "sauver":
                        self.sauvegarder_niveau()
                    elif action == "tester":
                        self.tester_niveau()
                    elif action == "changer_nom":
                        self.input_nom_actif = True; self.temp_nom_niveau = self.nom_niveau_en_cours; self.message_info = "Saisir nom (Entrée/ESC)"; self.message_couleur = C.DARK_ACCENT_INFO
                    elif action == "L+":
                        self.definir_taille_grille(self.largeur_grille + 1, self.hauteur_grille)
                    elif action == "L-":
                        self.definir_taille_grille(self.largeur_grille - 1, self.hauteur_grille)
                    elif action == "H+":
                        self.definir_taille_grille(self.largeur_grille, self.hauteur_grille + 1)
                    elif action == "H-":
                        self.definir_taille_grille(self.largeur_grille, self.hauteur_grille - 1)
                    return