import pygame
from . import constantes as C

class ElementJeu:
    def __init__(self, grid_x, grid_y):
        """Classe de base pour les éléments du jeu positionnés sur une grille."""
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

    def start_move(self, target_grid_x, target_grid_y, taille_case_anim, animation_duration_frames):
        """Démarre une animation de mouvement vers une nouvelle position de grille."""
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

    def update_animation(self, taille_case_anim):
        """Met à jour la position de l'élément pendant une animation."""
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
        """Définit instantanément la position de l'élément sur la grille."""
        self.grid_x = new_grid_x
        self.grid_y = new_grid_y
        self.pixel_x = new_grid_x * C.TAILLE_CASE
        self.pixel_y = new_grid_y * C.TAILLE_CASE
        self.target_pixel_x = self.pixel_x
        self.target_pixel_y = self.pixel_y
        self.is_moving = False
        self.animation_steps_left = 0

    def dessiner(self, surface, images_zoomees, textures_active, taille_case_effective, offset_x=0, offset_y=0, image_key=None, fallback_color=C.ROUGE):
        """Dessine l'élément, avec ou sans textures, en tenant compte du zoom."""
        zoom_ratio = taille_case_effective / C.TAILLE_CASE if C.TAILLE_CASE > 0 else 1.0
        screen_draw_x = self.pixel_x * zoom_ratio + offset_x
        screen_draw_y = self.pixel_y * zoom_ratio + offset_y
        if textures_active and image_key and images_zoomees.get(image_key):
            surface.blit(images_zoomees[image_key], (screen_draw_x, screen_draw_y))
        else:
            pygame.draw.rect(surface, fallback_color, (screen_draw_x, screen_draw_y, taille_case_effective, taille_case_effective))

class Case(ElementJeu):
    def __init__(self, grid_x, grid_y, type_case):
        """Représente une case statique de la grille (mur, sol, cible)."""
        super().__init__(grid_x, grid_y)
        if type_case not in [C.MUR, C.SOL, C.CIBLE]:
            raise ValueError(f"Type de case inconnu: {type_case}")
        self.type_case = type_case

    def dessiner(self, surface, images_zoomees, textures_active, taille_case_effective, offset_x=0, offset_y=0):
        """Dessine la case, avec ou sans textures, en tenant compte du zoom."""
        screen_x = self.grid_x * taille_case_effective + offset_x
        screen_y = self.grid_y * taille_case_effective + offset_y
        rect_tuple = (screen_x, screen_y, taille_case_effective, taille_case_effective)
        pos_tuple = (screen_x, screen_y)

        if self.type_case == C.MUR:
            if textures_active and C.IMG_MUR in images_zoomees and images_zoomees[C.IMG_MUR]:
                surface.blit(images_zoomees[C.IMG_MUR], pos_tuple)
            else:
                pygame.draw.rect(surface, C.FALLBACK_MUR, rect_tuple)
        elif self.type_case == C.SOL:
            if textures_active and C.IMG_SOL in images_zoomees and images_zoomees[C.IMG_SOL]:
                surface.blit(images_zoomees[C.IMG_SOL], pos_tuple)
            else:
                pygame.draw.rect(surface, C.FALLBACK_SOL, rect_tuple)
        elif self.type_case == C.CIBLE:
            if textures_active:
                if C.IMG_SOL in images_zoomees and images_zoomees[C.IMG_SOL]:
                    surface.blit(images_zoomees[C.IMG_SOL], pos_tuple)
                else: pygame.draw.rect(surface, C.FALLBACK_SOL, rect_tuple)
                if C.IMG_CIBLE in images_zoomees and images_zoomees[C.IMG_CIBLE]:
                    surface.blit(images_zoomees[C.IMG_CIBLE], pos_tuple)
                else: pygame.draw.rect(surface, C.FALLBACK_CIBLE, rect_tuple)
            else:
                pygame.draw.rect(surface, C.FALLBACK_SOL, rect_tuple)
                pygame.draw.rect(surface, C.FALLBACK_CIBLE, rect_tuple)

class Caisse(ElementJeu):
    def __init__(self, grid_x, grid_y):
        """Représente une caisse déplaçable."""
        super().__init__(grid_x, grid_y)
        self.sur_cible = False

    def dessiner(self, surface, images_zoomees, textures_active, taille_case_effective, offset_x=0, offset_y=0):
        """Dessine la caisse, avec ou sans textures, en tenant compte du zoom."""
        img_key = C.IMG_CAISSE_SUR_CIBLE if self.sur_cible else C.IMG_CAISSE
        fallback_col = C.FALLBACK_CAISSE_SUR_CIBLE if self.sur_cible else C.FALLBACK_CAISSE
        super().dessiner(surface, images_zoomees, textures_active, taille_case_effective, offset_x, offset_y, img_key, fallback_col)

class Joueur(ElementJeu):
    def __init__(self, grid_x, grid_y):
        """Représente le joueur."""
        super().__init__(grid_x, grid_y)

    def dessiner(self, surface, images_zoomees, textures_active, taille_case_effective, offset_x=0, offset_y=0):
        """Dessine le joueur, avec ou sans textures, en tenant compte du zoom."""
        super().dessiner(surface, images_zoomees, textures_active, taille_case_effective, offset_x, offset_y, C.IMG_JOUEUR, C.FALLBACK_JOUEUR)

class Niveau:
    def __init__(self, nom_fichier_ou_contenu=None, est_contenu_direct=False):
        """Gère la structure d'un niveau, son chargement et ses éléments."""
        self.cases = {}
        self.caisses = []
        self.cibles = []
        self.joueur = None
        self.largeur = 0; self.hauteur = 0
        self.mouvements_historique = []
        self.nom_fichier = None; self.contenu_initial_str = None
        self.elements_en_animation = []
        if nom_fichier_ou_contenu:
            if est_contenu_direct: self.contenu_initial_str = nom_fichier_ou_contenu; self._charger_contenu(nom_fichier_ou_contenu)
            else: self.nom_fichier = nom_fichier_ou_contenu; self._charger_fichier(nom_fichier_ou_contenu)
        self._mettre_a_jour_caisses_sur_cibles()

    def _charger_fichier(self, nom_fichier):
        """Charge un niveau à partir d'un nom de fichier."""
        try:
            with open(nom_fichier, 'r') as f: self.contenu_initial_str = f.read(); self._charger_contenu(self.contenu_initial_str)
        except FileNotFoundError:
            self.contenu_initial_str = "###\n#@.#\n###"; self._charger_contenu(self.contenu_initial_str)

    def _charger_contenu(self, contenu_str):
        """Charge un niveau à partir d'une chaîne de caractères."""
        self.cases.clear(); self.caisses.clear(); self.cibles.clear(); self.joueur = None
        self.mouvements_historique = []; self.elements_en_animation.clear()
        lignes_brutes = contenu_str.split('\n')
        idx_derniere_non_vide = -1
        for i in range(len(lignes_brutes) - 1, -1, -1):
            if lignes_brutes[i].strip(): idx_derniere_non_vide = i; break
        lignes_filtrees = lignes_brutes[:idx_derniere_non_vide+1] if idx_derniere_non_vide != -1 else [" @ "]
        self.hauteur = len(lignes_filtrees)
        self.largeur = max(len(l) for l in lignes_filtrees) if lignes_filtrees else (len(lignes_filtrees[0]) if self.hauteur > 0 else 3)
        lignes_normalisees = [list(l.ljust(self.largeur, C.SOL)) for l in lignes_filtrees]
        for y, ligne_chars in enumerate(lignes_normalisees):
            for x, char_case in enumerate(ligne_chars):
                pos = (x,y)
                if char_case == C.MUR: self.cases[pos] = Case(x,y,C.MUR)
                elif char_case == C.CIBLE or char_case == C.JOUEUR_SUR_CIBLE or char_case == C.CAISSE_SUR_CIBLE:
                    self.cases[pos] = Case(x,y,C.CIBLE);
                    if pos not in self.cibles: self.cibles.append(pos)
                else: self.cases[pos] = Case(x,y,C.SOL)
                if char_case == C.JOUEUR or char_case == C.JOUEUR_SUR_CIBLE: self.joueur = Joueur(x,y)
                elif char_case == C.CAISSE or char_case == C.CAISSE_SUR_CIBLE: self.caisses.append(Caisse(x,y))
        if not self.joueur:
            for y_scan in range(self.hauteur):
                for x_scan in range(self.largeur):
                    if self.cases.get((x_scan,y_scan),Case(0,0,C.MUR)).type_case==C.SOL and not any(b.grid_x==x_scan and b.grid_y==y_scan for b in self.caisses):
                        self.joueur=Joueur(x_scan,y_scan); break
                if self.joueur: break
            if not self.joueur and self.largeur>0 and self.hauteur>0: self.joueur=Joueur(0,0); self.cases[(0,0)]=Case(0,0,C.SOL)
        self._mettre_a_jour_caisses_sur_cibles()

    def _get_element_a_position_grille(self, grid_x, grid_y):
        """Retourne l'élément (Caisse ou Case) à la position de grille donnée."""
        for caisse in self.caisses:
            if caisse.grid_x == grid_x and caisse.grid_y == grid_y: return caisse
        return self.cases.get((grid_x, grid_y))

    def _mettre_a_jour_caisses_sur_cibles(self):
        """Met à jour l'attribut 'sur_cible' de chaque caisse."""
        for caisse in self.caisses: caisse.sur_cible = (caisse.grid_x, caisse.grid_y) in self.cibles

    def deplacer_joueur(self, dx, dy, taille_case_effective, sons=None, animation_frames=0, simuler_seulement=False, son_active=True):
        """Gère le déplacement du joueur et la poussée des caisses."""
        if not self.joueur: return False
        if not simuler_seulement and (self.joueur.is_moving or any(c.is_moving for c in self.caisses)): return False
        j_orig_gx,j_orig_gy=self.joueur.grid_x,self.joueur.grid_y; n_j_gx,n_j_gy=j_orig_gx+dx,j_orig_gy+dy
        elem_dest = self._get_element_a_position_grille(n_j_gx,n_j_gy); mvt_ok=False; c_p_obj=None; c_p_pos_av=None
        if isinstance(elem_dest,Case) and elem_dest.type_case != C.MUR:
            if simuler_seulement: self.joueur.set_grid_position_instantly(n_j_gx,n_j_gy)
            else: self.joueur.start_move(n_j_gx,n_j_gy, taille_case_effective, animation_frames); self.elements_en_animation=[self.joueur]
            if son_active and sons and sons.get("deplacement") and not simuler_seulement: sons["deplacement"].play()
            mvt_ok=True
        elif isinstance(elem_dest,Caisse):
            c_a_p=elem_dest; n_c_gx,n_c_gy = c_a_p.grid_x+dx,c_a_p.grid_y+dy
            elem_der_c = self._get_element_a_position_grille(n_c_gx,n_c_gy)
            if isinstance(elem_der_c,Case) and elem_der_c.type_case != C.MUR and not isinstance(elem_der_c,Caisse):
                c_p_obj=c_a_p; c_p_pos_av=(c_a_p.grid_x,c_a_p.grid_y)
                if simuler_seulement: self.joueur.set_grid_position_instantly(n_j_gx,n_j_gy); c_a_p.set_grid_position_instantly(n_c_gx,n_c_gy)
                else:
                    self.joueur.start_move(n_j_gx,n_j_gy,taille_case_effective,animation_frames)
                    c_a_p.start_move(n_c_gx,n_c_gy,taille_case_effective,animation_frames)
                    self.elements_en_animation=[self.joueur,c_a_p]
                if son_active and sons and sons.get("pousse") and not simuler_seulement: sons["pousse"].play()
                mvt_ok=True
        if mvt_ok and not simuler_seulement: self.mouvements_historique.append({"joueur_avant_grille":(j_orig_gx,j_orig_gy),"caisse_poussee_objet":c_p_obj,"caisse_poussee_avant_grille":c_p_pos_av})
        if simuler_seulement and mvt_ok: self._mettre_a_jour_caisses_sur_cibles()
        return mvt_ok

    def update_animations_niveau(self, taille_case_effective):
        """Met à jour toutes les animations en cours dans le niveau."""
        anim_en_cours = False; still_moving = []
        for elem in self.elements_en_animation:
            if elem.update_animation(taille_case_effective): anim_en_cours=True; still_moving.append(elem)
        self.elements_en_animation = still_moving
        if not anim_en_cours and not self.elements_en_animation: self._mettre_a_jour_caisses_sur_cibles()
        return anim_en_cours

    def annuler_dernier_mouvement(self):
        """Annule le dernier mouvement effectué par le joueur."""
        if not self.mouvements_historique or self.elements_en_animation: return False
        dernier_mvt = self.mouvements_historique.pop()
        self.joueur.set_grid_position_instantly(*dernier_mvt["joueur_avant_grille"])
        c_p=dernier_mvt["caisse_poussee_objet"]
        if c_p and dernier_mvt["caisse_poussee_avant_grille"]: c_p.set_grid_position_instantly(*dernier_mvt["caisse_poussee_avant_grille"])
        self._mettre_a_jour_caisses_sur_cibles(); return True

    def verifier_victoire(self):
        """Vérifie si toutes les caisses sont sur des cibles."""
        if not self.cibles: return not self.caisses
        if not self.caisses or len(self.caisses) != len(self.cibles) or self.elements_en_animation: return False
        return all(caisse.sur_cible for caisse in self.caisses)

    def reinitialiser(self):
        """Réinitialise le niveau à son état initial."""
        if self.contenu_initial_str: self._charger_contenu(self.contenu_initial_str)
        elif self.nom_fichier: self._charger_fichier(self.nom_fichier)
        else: return
        self._mettre_a_jour_caisses_sur_cibles(); self.elements_en_animation.clear()

    def dessiner(self, surface, images_zoomees, textures_active, taille_case_effective, offset_x_vue=0, offset_y_vue=0):
        """Dessine tous les éléments du niveau."""
        for case_obj in self.cases.values():
            case_obj.dessiner(surface, images_zoomees, textures_active, taille_case_effective, offset_x_vue, offset_y_vue)
        for caisse_obj in self.caisses:
            caisse_obj.dessiner(surface, images_zoomees, textures_active, taille_case_effective, offset_x_vue, offset_y_vue)
        if self.joueur:
            self.joueur.dessiner(surface, images_zoomees, textures_active, taille_case_effective, offset_x_vue, offset_y_vue)

    def get_etat_pour_solveur(self):
        """Retourne une représentation de l'état actuel du niveau pour les solveurs."""
        if not self.joueur: return None
        pos_caisses_tuples = tuple(sorted([(c.grid_x,c.grid_y) for c in self.caisses]))
        return ((self.joueur.grid_x,self.joueur.grid_y),pos_caisses_tuples)

    def appliquer_etat_solveur(self, etat):
        """Applique un état donné (généralement par un solveur) au niveau."""
        if etat is None or not self.joueur: return
        (pos_j_tuple,pos_c_tuple_trie) = etat
        self.joueur.set_grid_position_instantly(*pos_j_tuple)
        if len(self.caisses) == len(pos_c_tuple_trie):
            caisses_triees = sorted(self.caisses, key=lambda c_obj: (c_obj.grid_x,c_obj.grid_y))
            for i, caisse_obj in enumerate(caisses_triees):
                caisse_obj.set_grid_position_instantly(*pos_c_tuple_trie[i])
        self._mettre_a_jour_caisses_sur_cibles()