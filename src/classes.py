import pygame
from . import constantes as C


class ElementJeu:
    def __init__(self, grid_x, grid_y):
        self.grid_x = grid_x;
        self.grid_y = grid_y
        self.pixel_x = grid_x * C.TAILLE_CASE;
        self.pixel_y = grid_y * C.TAILLE_CASE
        self.target_pixel_x = self.pixel_x;
        self.target_pixel_y = self.pixel_y
        self.is_moving = False;
        self.animation_steps_left = 0
        self.dx_step = 0;
        self.dy_step = 0

    def start_move(self, target_grid_x, target_grid_y, animation_duration_frames):
        if self.grid_x == target_grid_x and self.grid_y == target_grid_y: return
        self.target_pixel_x = target_grid_x * C.TAILLE_CASE;
        self.target_pixel_y = target_grid_y * C.TAILLE_CASE
        if animation_duration_frames <= 0:
            self.pixel_x = self.target_pixel_x;
            self.pixel_y = self.target_pixel_y
            self.grid_x = target_grid_x;
            self.grid_y = target_grid_y
            self.is_moving = False;
            self.animation_steps_left = 0;
            return
        self.is_moving = True;
        self.animation_steps_left = animation_duration_frames
        total_dx_pixel = self.target_pixel_x - self.pixel_x;
        total_dy_pixel = self.target_pixel_y - self.pixel_y
        self.dx_step = total_dx_pixel / animation_duration_frames;
        self.dy_step = total_dy_pixel / animation_duration_frames

    def update_animation(self):
        if not self.is_moving or self.animation_steps_left <= 0: self.is_moving = False; return False
        self.pixel_x += self.dx_step;
        self.pixel_y += self.dy_step;
        self.animation_steps_left -= 1
        if self.animation_steps_left <= 0:
            self.pixel_x = self.target_pixel_x;
            self.pixel_y = self.target_pixel_y
            self.is_moving = False
            self.grid_x = self.target_pixel_x // C.TAILLE_CASE;
            self.grid_y = self.target_pixel_y // C.TAILLE_CASE
            return False
        return True

    def set_grid_position_instantly(self, new_grid_x, new_grid_y):  # Pour les solveurs et l'annulation
        self.grid_x = new_grid_x;
        self.grid_y = new_grid_y
        self.pixel_x = new_grid_x * C.TAILLE_CASE;
        self.pixel_y = new_grid_y * C.TAILLE_CASE
        self.target_pixel_x = self.pixel_x;
        self.target_pixel_y = self.pixel_y
        self.is_moving = False;
        self.animation_steps_left = 0

    def dessiner(self, surface, images, offset_x=0, offset_y=0, image_key=None):
        if image_key and image_key in images:
            surface.blit(images[image_key], (self.pixel_x + offset_x, self.pixel_y + offset_y))


class Case(ElementJeu):
    def __init__(self, grid_x, grid_y, type_case):
        super().__init__(grid_x, grid_y)
        if type_case not in [C.MUR, C.SOL, C.CIBLE]: raise ValueError(f"Type de case inconnu: {type_case}")
        self.type_case = type_case

    def dessiner(self, surface, images, offset_x=0, offset_y=0):
        img_key = C.SOL;
        if self.type_case == C.CIBLE:
            img_key = C.CIBLE
        elif self.type_case == C.MUR:
            img_key = C.MUR
        if img_key in images:
            surface.blit(images[img_key],
                         (self.grid_x * C.TAILLE_CASE + offset_x, self.grid_y * C.TAILLE_CASE + offset_y))
        else:
            pygame.draw.rect(surface,
                             C.GRIS if self.type_case == C.MUR else C.GRIS_CLAIR if self.type_case == C.SOL else C.ROSE,
                             (self.grid_x * C.TAILLE_CASE + offset_x, self.grid_y * C.TAILLE_CASE + offset_y,
                              C.TAILLE_CASE, C.TAILLE_CASE))


class Caisse(ElementJeu):
    def __init__(self, grid_x, grid_y): super().__init__(grid_x, grid_y); self.sur_cible = False

    def dessiner(self, surface, images, offset_x=0, offset_y=0): super().dessiner(surface, images, offset_x, offset_y,
                                                                                  C.CAISSE_SUR_CIBLE if self.sur_cible else C.CAISSE)


class Joueur(ElementJeu):
    def __init__(self, grid_x, grid_y): super().__init__(grid_x, grid_y)

    def dessiner(self, surface, images, offset_x=0, offset_y=0): super().dessiner(surface, images, offset_x, offset_y,
                                                                                  C.JOUEUR)


class Niveau:
    def __init__(self, nom_fichier_ou_contenu=None, est_contenu_direct=False):
        self.cases = {};
        self.caisses = [];
        self.cibles = [];
        self.joueur = None;
        self.largeur = 0;
        self.hauteur = 0
        self.mouvements_historique = [];
        self.nom_fichier = None;
        self.contenu_initial_str = None;
        self.elements_en_animation = []
        if nom_fichier_ou_contenu:
            if est_contenu_direct:
                self.contenu_initial_str = nom_fichier_ou_contenu;self._charger_contenu(nom_fichier_ou_contenu)
            else:
                self.nom_fichier = nom_fichier_ou_contenu;self._charger_fichier(nom_fichier_ou_contenu)
        self._mettre_a_jour_caisses_sur_cibles()

    def _charger_fichier(self, nom_fichier):
        try:
            with open(nom_fichier, 'r') as f:
                self.contenu_initial_str = f.read();self._charger_contenu(self.contenu_initial_str)
        except FileNotFoundError:
            print(f"Fichier {nom_fichier} introuvable.");self._charger_contenu(
                f"{C.MUR * 3}\n{C.MUR}{C.JOUEUR}{C.MUR}\n{C.MUR * 3}")

    def _charger_contenu(self, contenu_str):
        self.cases.clear();
        self.caisses.clear();
        self.cibles.clear();
        self.joueur = None;
        self.mouvements_historique = []
        l_b = contenu_str.split('\n');
        l_f = [];
        [l_f.append(l) for l_r in reversed(l_b) if not (l_r.strip() == "" and not l_f) for l in [l_r]];
        l_f.reverse()
        if not l_f: l_f = [C.SOL * 5]
        self.hauteur = len(l_f);
        self.largeur = max(len(l) for l in l_f) if l_f else 0
        if self.largeur == 0: self.largeur = 5;[l_f.__setitem__(i, C.SOL * self.largeur) for i in range(len(l_f)) if
                                                not l_f[i].strip()]
        for y, ligne_brute in enumerate(l_f):
            for x in range(self.largeur):
                pos = (x, y);
                char = C.SOL;
                if x < len(ligne_brute): char = ligne_brute[x]
                action_map = {C.MUR: lambda: self.cases.update({pos: Case(x, y, C.MUR)}),
                              C.SOL: lambda: self.cases.update({pos: Case(x, y, C.SOL)}),
                              C.CIBLE: lambda: (self.cases.update({pos: Case(x, y, C.CIBLE)}), self.cibles.append(pos)),
                              C.JOUEUR: lambda: (
                              self.cases.update({pos: Case(x, y, C.SOL)}), setattr(self, 'joueur', Joueur(x, y))),
                              C.CAISSE: lambda: (
                              self.cases.update({pos: Case(x, y, C.SOL)}), self.caisses.append(Caisse(x, y))),
                              C.JOUEUR_SUR_CIBLE: lambda: (
                              self.cases.update({pos: Case(x, y, C.CIBLE)}), self.cibles.append(pos),
                              setattr(self, 'joueur', Joueur(x, y))),
                              C.CAISSE_SUR_CIBLE: lambda: (
                              self.cases.update({pos: Case(x, y, C.CIBLE)}), self.cibles.append(pos),
                              self.caisses.append(type('c', (Caisse,), {'sur_cible': True})(x, y)))}
                action_map.get(char, lambda: self.cases.update({pos: Case(x, y, C.SOL)}))()
        self.elements_en_animation.clear()

    def _get_element_a_position_grille(self, grid_x, grid_y):
        return next((c for c in self.caisses if c.grid_x == grid_x and c.grid_y == grid_y),
                    self.cases.get((grid_x, grid_y)))

    def _mettre_a_jour_caisses_sur_cibles(self):
        [setattr(c, 'sur_cible', (c.grid_x, c.grid_y) in self.cibles) for c in self.caisses]

    def deplacer_joueur(self, dx, dy, sons=None, animation_frames=0,
                        simuler_seulement=False):  # Ajout de simuler_seulement
        if not self.joueur: return False
        if not simuler_seulement and (self.joueur.is_moving or any(c.is_moving for c in self.caisses)): return False

        j_gx_orig, j_gy_orig = self.joueur.grid_x, self.joueur.grid_y
        n_j_gx, n_j_gy = j_gx_orig + dx, j_gy_orig + dy
        elem_dest = self._get_element_a_position_grille(n_j_gx, n_j_gy)
        mvt_logique_ok = False;
        caisse_poussee_obj = None;
        c_p_pos_grille_av = None

        if isinstance(elem_dest, Case) and elem_dest.type_case != C.MUR:
            if simuler_seulement:
                self.joueur.set_grid_position_instantly(n_j_gx, n_j_gy)
            else:
                self.joueur.start_move(n_j_gx, n_j_gy, animation_frames); self.elements_en_animation = [self.joueur]
            if sons and sons.get("deplacement") and not simuler_seulement: sons["deplacement"].play()
            mvt_logique_ok = True
        elif isinstance(elem_dest, Caisse):
            c_a_p = elem_dest;
            n_c_gx, n_c_gy = c_a_p.grid_x + dx, c_a_p.grid_y + dy
            elem_der_c = self._get_element_a_position_grille(n_c_gx, n_c_gy)
            if isinstance(elem_der_c, Case) and elem_der_c.type_case != C.MUR:
                caisse_poussee_obj = c_a_p;
                c_p_pos_grille_av = (c_a_p.grid_x, c_a_p.grid_y)
                if simuler_seulement:
                    self.joueur.set_grid_position_instantly(n_j_gx, n_j_gy)
                    c_a_p.set_grid_position_instantly(n_c_gx, n_c_gy)
                else:
                    self.joueur.start_move(n_j_gx, n_j_gy, animation_frames)
                    c_a_p.start_move(n_c_gx, n_c_gy, animation_frames)
                    self.elements_en_animation = [self.joueur, c_a_p]
                if sons and sons.get("pousse") and not simuler_seulement: sons["pousse"].play()
                mvt_logique_ok = True

        if mvt_logique_ok and not simuler_seulement:  # Historique seulement pour les vrais mouvements
            self.mouvements_historique.append({"joueur_avant_grille": (j_gx_orig, j_gy_orig),
                                               "caisse_poussee_objet": caisse_poussee_obj,
                                               "caisse_poussee_avant_grille": c_p_pos_grille_av})
        if simuler_seulement and mvt_logique_ok:  # Mettre à jour état des caisses pour la simulation
            self._mettre_a_jour_caisses_sur_cibles()

        return mvt_logique_ok  # Si le mouvement logique est possible

    def update_animations_niveau(self):
        anim_en_cours_glob = False;
        still_moving = []
        for elem in self.elements_en_animation:
            if elem.update_animation(): anim_en_cours_glob = True; still_moving.append(elem)
        self.elements_en_animation = still_moving
        if not anim_en_cours_glob and not self.elements_en_animation: self._mettre_a_jour_caisses_sur_cibles()
        return anim_en_cours_glob

    def annuler_dernier_mouvement(self):
        if not self.mouvements_historique or self.elements_en_animation: return False
        dernier_mvt = self.mouvements_historique.pop()
        self.joueur.set_grid_position_instantly(*dernier_mvt["joueur_avant_grille"])
        c_p = dernier_mvt["caisse_poussee_objet"]
        if c_p and dernier_mvt["caisse_poussee_avant_grille"]: c_p.set_grid_position_instantly(
            *dernier_mvt["caisse_poussee_avant_grille"])
        self._mettre_a_jour_caisses_sur_cibles();
        return True

    def verifier_victoire(self):
        if not self.caisses or not self.cibles or self.elements_en_animation: return False
        return all(c.sur_cible for c in self.caisses)

    def reinitialiser(self):
        if self.contenu_initial_str:
            self._charger_contenu(self.contenu_initial_str)
        elif self.nom_fichier:
            self._charger_fichier(self.nom_fichier)
        self._mettre_a_jour_caisses_sur_cibles();
        self.elements_en_animation.clear()

    def dessiner(self, surface, images, offset_x=0, offset_y=0):
        surface.fill(C.NOIR)
        [case.dessiner(surface, images, offset_x, offset_y) for case in self.cases.values()]
        [caisse.dessiner(surface, images, offset_x, offset_y) for caisse in self.caisses]
        if self.joueur: self.joueur.dessiner(surface, images, offset_x, offset_y)

    def get_etat_pour_solveur(self):
        if not self.joueur: return None
        return ((self.joueur.grid_x, self.joueur.grid_y), tuple(sorted([(c.grid_x, c.grid_y) for c in self.caisses])))

    def appliquer_etat_solveur(self, etat):
        (pos_j, pos_c) = etat
        if self.joueur: self.joueur.set_grid_position_instantly(*pos_j)
        if len(self.caisses) == len(pos_c):
            temp_pos_c = sorted(list(pos_c))
            # Il faut s'assurer que les objets Caisse sont mis à jour correctement.
            # Si l'ordre des caisses change ou si les objets sont différents,
            # il faut une correspondance plus robuste.
            # Pour l'instant, on assume que self.caisses est dans un ordre qui peut être mappé.
            # Le plus simple est de les trier par position actuelle puis d'assigner.
            self.caisses.sort(key=lambda c_obj: (c_obj.grid_x, c_obj.grid_y))
            for i, caisse_obj in enumerate(self.caisses):
                if i < len(temp_pos_c): caisse_obj.set_grid_position_instantly(*temp_pos_c[i])
        self._mettre_a_jour_caisses_sur_cibles()