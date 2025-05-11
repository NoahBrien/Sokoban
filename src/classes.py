import pygame
from . import constantes as C


class ElementJeu:
    def __init__(self, grid_x, grid_y):
        self.grid_x = grid_x
        self.grid_y = grid_y
        self.pixel_x = grid_x * C.TAILLE_CASE
        self.pixel_y = grid_y * C.TAILLE_CASE
        self.target_pixel_x = self.pixel_x
        self.target_pixel_y = self.pixel_y
        self.is_moving = False
        self.animation_steps_left = 0
        self.dx_step = 0
        self.dy_step = 0

    def start_move(self, target_grid_x, target_grid_y, animation_duration_frames):
        if self.grid_x == target_grid_x and self.grid_y == target_grid_y: return
        self.target_pixel_x = target_grid_x * C.TAILLE_CASE
        self.target_pixel_y = target_grid_y * C.TAILLE_CASE
        if animation_duration_frames <= 0:
            self.pixel_x = self.target_pixel_x
            self.pixel_y = self.target_pixel_y
            self.grid_x = target_grid_x
            self.grid_y = target_grid_y
            self.is_moving = False
            self.animation_steps_left = 0
            return
        self.is_moving = True
        self.animation_steps_left = animation_duration_frames
        total_dx_pixel = self.target_pixel_x - self.pixel_x
        total_dy_pixel = self.target_pixel_y - self.pixel_y
        self.dx_step = total_dx_pixel / animation_duration_frames
        self.dy_step = total_dy_pixel / animation_duration_frames

    def update_animation(self):
        if not self.is_moving or self.animation_steps_left <= 0:
            self.is_moving = False
            return False
        self.pixel_x += self.dx_step
        self.pixel_y += self.dy_step
        self.animation_steps_left -= 1
        if self.animation_steps_left <= 0:
            self.pixel_x = self.target_pixel_x
            self.pixel_y = self.target_pixel_y
            self.is_moving = False
            self.grid_x = self.target_pixel_x // C.TAILLE_CASE
            self.grid_y = self.target_pixel_y // C.TAILLE_CASE
            return False
        return True

    def set_grid_position_instantly(self, new_grid_x, new_grid_y):
        self.grid_x = new_grid_x
        self.grid_y = new_grid_y
        self.pixel_x = new_grid_x * C.TAILLE_CASE
        self.pixel_y = new_grid_y * C.TAILLE_CASE
        self.target_pixel_x = self.pixel_x
        self.target_pixel_y = self.pixel_y
        self.is_moving = False
        self.animation_steps_left = 0

    def dessiner(self, surface, images, textures_active, offset_x=0, offset_y=0, image_key=None,
                 fallback_color=C.ROUGE):
        screen_x = self.pixel_x + offset_x
        screen_y = self.pixel_y + offset_y

        if textures_active and image_key and images.get(image_key):
            surface.blit(images[image_key], (screen_x, screen_y))
        else:
            pygame.draw.rect(surface, fallback_color, (screen_x, screen_y, C.TAILLE_CASE, C.TAILLE_CASE))


class Case(ElementJeu):
    def __init__(self, grid_x, grid_y, type_case):
        super().__init__(grid_x, grid_y)
        if type_case not in [C.MUR, C.SOL, C.CIBLE]:
            raise ValueError(f"Type de case inconnu: {type_case}")
        self.type_case = type_case

    def dessiner(self, surface, images, textures_active, offset_x=0, offset_y=0):
        screen_x = self.grid_x * C.TAILLE_CASE + offset_x
        screen_y = self.grid_y * C.TAILLE_CASE + offset_y
        # 'rect_tuple' est utilisé pour pygame.draw.rect, qui attend un tuple ou un Rect.
        rect_tuple = (screen_x, screen_y, C.TAILLE_CASE, C.TAILLE_CASE)
        # 'pos_tuple' est utilisé pour surface.blit, qui attend un tuple (x,y) ou un Rect.
        pos_tuple = (screen_x, screen_y)

        if self.type_case == C.MUR:
            if textures_active and C.IMG_MUR in images:
                surface.blit(images[C.IMG_MUR], pos_tuple)
            else:
                pygame.draw.rect(surface, C.FALLBACK_MUR, rect_tuple)

        elif self.type_case == C.SOL:
            if textures_active and C.IMG_SOL in images:
                surface.blit(images[C.IMG_SOL], pos_tuple)
            else:
                pygame.draw.rect(surface, C.FALLBACK_SOL, rect_tuple)

        elif self.type_case == C.CIBLE:
            # Base (sol)
            if textures_active and C.IMG_SOL in images:
                surface.blit(images[C.IMG_SOL], pos_tuple)
            else:
                pygame.draw.rect(surface, C.FALLBACK_SOL, rect_tuple)
            # Cible par-dessus
            if textures_active and C.IMG_CIBLE in images:
                surface.blit(images[C.IMG_CIBLE], pos_tuple)
            else:
                pygame.draw.rect(surface, C.FALLBACK_CIBLE, rect_tuple)


class Caisse(ElementJeu):
    def __init__(self, grid_x, grid_y):
        super().__init__(grid_x, grid_y)
        self.sur_cible = False

    def dessiner(self, surface, images, textures_active, offset_x=0, offset_y=0):
        img_key = C.IMG_CAISSE_SUR_CIBLE if self.sur_cible else C.IMG_CAISSE
        fallback_col = C.FALLBACK_CAISSE_SUR_CIBLE if self.sur_cible else C.FALLBACK_CAISSE
        super().dessiner(surface, images, textures_active, offset_x, offset_y, img_key, fallback_col)


class Joueur(ElementJeu):
    def __init__(self, grid_x, grid_y):
        super().__init__(grid_x, grid_y)

    def dessiner(self, surface, images, textures_active, offset_x=0, offset_y=0):
        super().dessiner(surface, images, textures_active, offset_x, offset_y, C.IMG_JOUEUR, C.FALLBACK_JOUEUR)


class Niveau:
    def __init__(self, nom_fichier_ou_contenu=None, est_contenu_direct=False):
        self.cases = {}
        self.caisses = []
        self.cibles = []
        self.joueur = None
        self.largeur = 0
        self.hauteur = 0
        self.mouvements_historique = []
        self.nom_fichier = None
        self.contenu_initial_str = None
        self.elements_en_animation = []

        if nom_fichier_ou_contenu:
            if est_contenu_direct:
                self.contenu_initial_str = nom_fichier_ou_contenu
                self._charger_contenu(nom_fichier_ou_contenu)
            else:
                self.nom_fichier = nom_fichier_ou_contenu
                self._charger_fichier(nom_fichier_ou_contenu)
        self._mettre_a_jour_caisses_sur_cibles()

    def _charger_fichier(self, nom_fichier):
        try:
            with open(nom_fichier, 'r') as f:
                self.contenu_initial_str = f.read()
                self._charger_contenu(self.contenu_initial_str)
        except FileNotFoundError:
            print(f"Fichier {nom_fichier} introuvable. Chargement d'un niveau par défaut.")
            default_level_str = "###\n#@.#\n###"
            self.contenu_initial_str = default_level_str
            self._charger_contenu(default_level_str)

    def _charger_contenu(self, contenu_str):
        self.cases.clear();
        self.caisses.clear();
        self.cibles.clear();
        self.joueur = None
        self.mouvements_historique = [];
        self.elements_en_animation.clear()

        lignes_brutes = contenu_str.split('\n')
        idx_derniere_non_vide = -1
        for i in range(len(lignes_brutes) - 1, -1, -1):
            if lignes_brutes[i].strip():
                idx_derniere_non_vide = i
                break
        lignes_filtrees = lignes_brutes[:idx_derniere_non_vide + 1] if idx_derniere_non_vide != -1 else [" @ "]

        self.hauteur = len(lignes_filtrees)
        self.largeur = max(len(l) for l in lignes_filtrees) if lignes_filtrees else 0
        if self.largeur == 0 and self.hauteur > 0: self.largeur = len(lignes_filtrees[0])
        if self.largeur == 0: self.largeur = 3

        lignes_normalisees = [list(l.ljust(self.largeur, C.SOL)) for l in lignes_filtrees]

        for y, ligne_chars in enumerate(lignes_normalisees):
            for x, char_case in enumerate(ligne_chars):
                pos = (x, y)
                if char_case == C.MUR:
                    self.cases[pos] = Case(x, y, C.MUR)
                elif char_case == C.CIBLE or char_case == C.JOUEUR_SUR_CIBLE or char_case == C.CAISSE_SUR_CIBLE:
                    self.cases[pos] = Case(x, y, C.CIBLE)
                    if pos not in self.cibles: self.cibles.append(pos)
                else:
                    self.cases[pos] = Case(x, y, C.SOL)

                if char_case == C.JOUEUR or char_case == C.JOUEUR_SUR_CIBLE:
                    self.joueur = Joueur(x, y)
                elif char_case == C.CAISSE:
                    self.caisses.append(Caisse(x, y))
                elif char_case == C.CAISSE_SUR_CIBLE:
                    self.caisses.append(Caisse(x, y))

        if not self.joueur:
            # print("Avertissement: Aucun joueur défini. Placement auto.")
            for y_scan in range(self.hauteur):
                for x_scan in range(self.largeur):
                    if self.cases.get((x_scan, y_scan), Case(0, 0, C.MUR)).type_case == C.SOL:
                        is_box = any(b.grid_x == x_scan and b.grid_y == y_scan for b in self.caisses)
                        if not is_box:
                            self.joueur = Joueur(x_scan, y_scan);
                            break
                if self.joueur: break
            if not self.joueur and self.largeur > 0 and self.hauteur > 0:
                self.joueur = Joueur(0, 0)
                if (0, 0) not in self.cases or self.cases[(0, 0)].type_case == C.MUR:
                    self.cases[(0, 0)] = Case(0, 0, C.SOL)
        self._mettre_a_jour_caisses_sur_cibles()

    def _get_element_a_position_grille(self, grid_x, grid_y):
        for caisse in self.caisses:
            if caisse.grid_x == grid_x and caisse.grid_y == grid_y:
                return caisse
        return self.cases.get((grid_x, grid_y))

    def _mettre_a_jour_caisses_sur_cibles(self):
        for caisse in self.caisses:
            caisse.sur_cible = (caisse.grid_x, caisse.grid_y) in self.cibles

    def deplacer_joueur(self, dx, dy, sons=None, animation_frames=0, simuler_seulement=False, son_active=True):
        if not self.joueur: return False
        if not simuler_seulement and (self.joueur.is_moving or any(c.is_moving for c in self.caisses)):
            return False

        joueur_orig_gx, joueur_orig_gy = self.joueur.grid_x, self.joueur.grid_y
        nouvelle_joueur_gx, nouvelle_joueur_gy = joueur_orig_gx + dx, joueur_orig_gy + dy

        element_destination = self._get_element_a_position_grille(nouvelle_joueur_gx, nouvelle_joueur_gy)
        mouvement_logique_possible = False
        caisse_poussee_objet = None
        caisse_poussee_pos_avant = None

        if isinstance(element_destination, Case) and element_destination.type_case != C.MUR:
            if simuler_seulement:
                self.joueur.set_grid_position_instantly(nouvelle_joueur_gx, nouvelle_joueur_gy)
            else:
                self.joueur.start_move(nouvelle_joueur_gx, nouvelle_joueur_gy, animation_frames)
                self.elements_en_animation = [self.joueur]
            if son_active and sons and sons.get("deplacement") and not simuler_seulement:
                sons["deplacement"].play()
            mouvement_logique_possible = True
        elif isinstance(element_destination, Caisse):
            caisse_a_pousser = element_destination
            nouvelle_caisse_gx, nouvelle_caisse_gy = caisse_a_pousser.grid_x + dx, caisse_a_pousser.grid_y + dy
            element_derriere_caisse = self._get_element_a_position_grille(nouvelle_caisse_gx, nouvelle_caisse_gy)
            pas_mur_derriere = isinstance(element_derriere_caisse, Case) and element_derriere_caisse.type_case != C.MUR
            pas_autre_caisse_derriere = not isinstance(element_derriere_caisse, Caisse)
            if pas_mur_derriere and pas_autre_caisse_derriere:
                caisse_poussee_objet = caisse_a_pousser
                caisse_poussee_pos_avant = (caisse_a_pousser.grid_x, caisse_a_pousser.grid_y)
                if simuler_seulement:
                    self.joueur.set_grid_position_instantly(nouvelle_joueur_gx, nouvelle_joueur_gy)
                    caisse_a_pousser.set_grid_position_instantly(nouvelle_caisse_gx, nouvelle_caisse_gy)
                else:
                    self.joueur.start_move(nouvelle_joueur_gx, nouvelle_joueur_gy, animation_frames)
                    caisse_a_pousser.start_move(nouvelle_caisse_gx, nouvelle_caisse_gy, animation_frames)
                    self.elements_en_animation = [self.joueur, caisse_a_pousser]
                if son_active and sons and sons.get("pousse") and not simuler_seulement:
                    sons["pousse"].play()
                mouvement_logique_possible = True

        if mouvement_logique_possible and not simuler_seulement:
            self.mouvements_historique.append({
                "joueur_avant_grille": (joueur_orig_gx, joueur_orig_gy),
                "caisse_poussee_objet": caisse_poussee_objet,
                "caisse_poussee_avant_grille": caisse_poussee_pos_avant
            })
        if simuler_seulement and mouvement_logique_possible:
            self._mettre_a_jour_caisses_sur_cibles()
        return mouvement_logique_possible

    def update_animations_niveau(self):
        animation_globale_en_cours = False
        elements_encore_en_mouvement = []
        for elem in self.elements_en_animation:
            if elem.update_animation():
                animation_globale_en_cours = True
                elements_encore_en_mouvement.append(elem)
        self.elements_en_animation = elements_encore_en_mouvement
        if not animation_globale_en_cours and not self.elements_en_animation:
            self._mettre_a_jour_caisses_sur_cibles()
        return animation_globale_en_cours

    def annuler_dernier_mouvement(self):
        if not self.mouvements_historique or self.elements_en_animation:
            return False
        dernier_mouvement = self.mouvements_historique.pop()
        self.joueur.set_grid_position_instantly(*dernier_mouvement["joueur_avant_grille"])
        caisse_poussee = dernier_mouvement["caisse_poussee_objet"]
        if caisse_poussee and dernier_mouvement["caisse_poussee_avant_grille"]:
            caisse_poussee.set_grid_position_instantly(*dernier_mouvement["caisse_poussee_avant_grille"])
        self._mettre_a_jour_caisses_sur_cibles()
        return True

    def verifier_victoire(self):
        if not self.cibles: return not self.caisses
        if not self.caisses: return False
        if len(self.caisses) != len(self.cibles): return False
        if self.elements_en_animation: return False
        return all(caisse.sur_cible for caisse in self.caisses)

    def reinitialiser(self):
        if self.contenu_initial_str:
            self._charger_contenu(self.contenu_initial_str)
        elif self.nom_fichier:
            self._charger_fichier(self.nom_fichier)
        else:
            # print("Erreur: Tentative de réinitialisation d'un niveau sans contenu initial.") # Peut être trop verbeux
            return
        self._mettre_a_jour_caisses_sur_cibles()
        self.elements_en_animation.clear()

    def dessiner(self, surface, images, textures_active, offset_x=0, offset_y=0):
        for case_obj in self.cases.values():
            case_obj.dessiner(surface, images, textures_active, offset_x, offset_y)

        for caisse_obj in self.caisses:
            caisse_obj.dessiner(surface, images, textures_active, offset_x, offset_y)

        if self.joueur:
            self.joueur.dessiner(surface, images, textures_active, offset_x, offset_y)

    def get_etat_pour_solveur(self):
        if not self.joueur: return None
        positions_caisses_tuples = tuple(sorted([(c.grid_x, c.grid_y) for c in self.caisses]))
        return ((self.joueur.grid_x, self.joueur.grid_y), positions_caisses_tuples)

    def appliquer_etat_solveur(self, etat):
        if etat is None or not self.joueur:
            return
        (pos_joueur_tuple, pos_caisses_tuple_trie) = etat
        self.joueur.set_grid_position_instantly(*pos_joueur_tuple)

        if len(self.caisses) == len(pos_caisses_tuple_trie):
            # Pour plus de robustesse, on pourrait vouloir recréer les objets Caisse ou utiliser une table de hachage,
            # mais pour Sokoban standard, trier les caisses existantes et leur assigner les positions triées de l'état
            # devrait suffire si le nombre de caisses est constant.
            caisses_actuelles_triees = sorted(self.caisses, key=lambda c_obj: (c_obj.grid_x, c_obj.grid_y))
            for i, caisse_obj in enumerate(caisses_actuelles_triees):
                caisse_obj.set_grid_position_instantly(*pos_caisses_tuple_trie[i])
        # else:
        # print(f"Erreur: Incohérence du nombre de caisses lors de l'application de l'état solveur.")
        self._mettre_a_jour_caisses_sur_cibles()