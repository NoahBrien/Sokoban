import pygame
from . import constantes as C


class ElementJeu:
    def __init__(self, x, y):
        self.x = x
        self.y = y

    def dessiner(self, surface, images, offset_x=0, offset_y=0):
        pass


class Case(ElementJeu):
    def __init__(self, x, y, type_case):
        super().__init__(x, y)
        if type_case not in [C.MUR, C.SOL, C.CIBLE]:
            raise ValueError(f"Type de case inconnu: {type_case}")
        self.type_case = type_case

    def dessiner(self, surface, images, offset_x=0, offset_y=0):
        img_key = self.type_case
        if self.type_case == C.CIBLE:
            img_key = C.CIBLE
        elif self.type_case == C.MUR:
            img_key = C.MUR
        else:
            img_key = C.SOL

        if img_key in images:
            surface.blit(images[img_key], (self.x * C.TAILLE_CASE + offset_x, self.y * C.TAILLE_CASE + offset_y))
        else:
            couleur = C.GRIS if self.type_case == C.MUR else C.GRIS_CLAIR if self.type_case == C.SOL else C.ROSE
            pygame.draw.rect(surface, couleur, (
            self.x * C.TAILLE_CASE + offset_x, self.y * C.TAILLE_CASE + offset_y, C.TAILLE_CASE, C.TAILLE_CASE))


class Caisse(ElementJeu):
    def __init__(self, x, y):
        super().__init__(x, y)
        self.sur_cible = False

    def dessiner(self, surface, images, offset_x=0, offset_y=0):
        img_key = C.CAISSE_SUR_CIBLE if self.sur_cible else C.CAISSE
        if img_key in images:
            surface.blit(images[img_key], (self.x * C.TAILLE_CASE + offset_x, self.y * C.TAILLE_CASE + offset_y))
        else:
            couleur = C.VERT if self.sur_cible else C.MARRON
            pygame.draw.rect(surface, couleur, (
            self.x * C.TAILLE_CASE + offset_x + 5, self.y * C.TAILLE_CASE + offset_y + 5, C.TAILLE_CASE - 10,
            C.TAILLE_CASE - 10))


class Joueur(ElementJeu):
    def __init__(self, x, y):
        super().__init__(x, y)

    def dessiner(self, surface, images, offset_x=0, offset_y=0):
        img_key = C.JOUEUR
        if img_key in images:
            surface.blit(images[img_key], (self.x * C.TAILLE_CASE + offset_x, self.y * C.TAILLE_CASE + offset_y))
        else:
            pygame.draw.circle(surface, C.BLEU, (self.x * C.TAILLE_CASE + C.TAILLE_CASE // 2 + offset_x,
                                                 self.y * C.TAILLE_CASE + C.TAILLE_CASE // 2 + offset_y),
                               C.TAILLE_CASE // 3)


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
            print(f"Fichier niveau {nom_fichier} introuvable.")
            self._charger_contenu(f"{C.MUR}{C.MUR}{C.MUR}\n{C.MUR}{C.JOUEUR}{C.MUR}\n{C.MUR}{C.MUR}{C.MUR}")

    def _charger_contenu(self, contenu_str):
        self.cases.clear();
        self.caisses.clear();
        self.cibles.clear()
        self.joueur = None;
        self.mouvements_historique = []

        lignes = contenu_str.strip().split('\n')
        self.hauteur = len(lignes)
        self.largeur = max(len(ligne) for ligne in lignes) if lignes else 0

        for y, ligne in enumerate(lignes):
            for x, caractere in enumerate(ligne):
                pos = (x, y)
                if caractere == C.MUR:
                    self.cases[pos] = Case(x, y, C.MUR)
                elif caractere == C.SOL:
                    self.cases[pos] = Case(x, y, C.SOL)
                elif caractere == C.CIBLE:
                    self.cases[pos] = Case(x, y, C.CIBLE)
                    self.cibles.append(pos)
                elif caractere == C.JOUEUR:
                    self.cases[pos] = Case(x, y, C.SOL)
                    self.joueur = Joueur(x, y)
                elif caractere == C.CAISSE:
                    self.cases[pos] = Case(x, y, C.SOL)
                    self.caisses.append(Caisse(x, y))
                elif caractere == C.JOUEUR_SUR_CIBLE:
                    self.cases[pos] = Case(x, y, C.CIBLE)
                    self.cibles.append(pos)
                    self.joueur = Joueur(x, y)
                elif caractere == C.CAISSE_SUR_CIBLE:
                    self.cases[pos] = Case(x, y, C.CIBLE)
                    self.cibles.append(pos)
                    c = Caisse(x, y);
                    c.sur_cible = True;
                    self.caisses.append(c)
                else:
                    self.cases[pos] = Case(x, y, C.SOL)
            for x_fill in range(len(ligne), self.largeur):
                self.cases[(x_fill, y)] = Case(x_fill, y, C.SOL)

    def _get_element_a_position(self, x, y):
        for caisse in self.caisses:
            if caisse.x == x and caisse.y == y: return caisse
        return self.cases.get((x, y))

    def _mettre_a_jour_caisses_sur_cibles(self):
        for caisse in self.caisses:
            caisse.sur_cible = (caisse.x, caisse.y) in self.cibles

    def deplacer_joueur(self, dx, dy, sons=None):
        if not self.joueur: return False
        ancienne_pos_joueur = (self.joueur.x, self.joueur.y)
        n_p_j_x, n_p_j_y = self.joueur.x + dx, self.joueur.y + dy
        elem_dest = self._get_element_a_position(n_p_j_x, n_p_j_y)
        mvt_ok = False;
        c_p_av = None;
        c_p_ap = None

        if isinstance(elem_dest, Case) and elem_dest.type_case != C.MUR:
            self.joueur.x = n_p_j_x;
            self.joueur.y = n_p_j_y;
            mvt_ok = True
            if sons and sons.get("deplacement"): sons["deplacement"].play()
        elif isinstance(elem_dest, Caisse):
            c_a_p = elem_dest
            n_p_c_x, n_p_c_y = c_a_p.x + dx, c_a_p.y + dy
            elem_der_c = self._get_element_a_position(n_p_c_x, n_p_c_y)
            if isinstance(elem_der_c, Case) and elem_der_c.type_case != C.MUR:
                c_p_av = (c_a_p.x, c_a_p.y)
                c_a_p.x = n_p_c_x;
                c_a_p.y = n_p_c_y
                self.joueur.x = n_p_j_x;
                self.joueur.y = n_p_j_y
                c_p_ap = (c_a_p.x, c_a_p.y);
                mvt_ok = True
                if sons and sons.get("pousse"): sons["pousse"].play()

        if mvt_ok:
            self.mouvements_historique.append({
                "joueur_avant": ancienne_pos_joueur, "joueur_apres": (self.joueur.x, self.joueur.y),
                "caisse_poussee_avant": c_p_av, "caisse_poussee_apres": c_p_ap})
            self._mettre_a_jour_caisses_sur_cibles()
        return mvt_ok

    def annuler_dernier_mouvement(self):
        if not self.mouvements_historique: return False
        dernier_mvt = self.mouvements_historique.pop()
        self.joueur.x, self.joueur.y = dernier_mvt["joueur_avant"]
        if dernier_mvt["caisse_poussee_avant"] and dernier_mvt["caisse_poussee_apres"]:
            pos_ap_x, pos_ap_y = dernier_mvt["caisse_poussee_apres"]
            c_trouvee = next((c for c in self.caisses if c.x == pos_ap_x and c.y == pos_ap_y), None)
            if c_trouvee: c_trouvee.x, c_trouvee.y = dernier_mvt["caisse_poussee_avant"]
        self._mettre_a_jour_caisses_sur_cibles();
        return True

    def verifier_victoire(self):
        if not self.caisses or not self.cibles: return False
        return all(caisse.sur_cible for caisse in self.caisses)

    def reinitialiser(self):
        if self.contenu_initial_str:
            self._charger_contenu(self.contenu_initial_str)
        elif self.nom_fichier:
            self._charger_fichier(self.nom_fichier)
        self._mettre_a_jour_caisses_sur_cibles()

    def dessiner(self, surface, images, offset_x=0, offset_y=0):
        surface.fill(C.NOIR)
        for case in self.cases.values(): case.dessiner(surface, images, offset_x, offset_y)
        for caisse in self.caisses: caisse.dessiner(surface, images, offset_x, offset_y)
        if self.joueur: self.joueur.dessiner(surface, images, offset_x, offset_y)

    def get_etat_pour_solveur(self):
        if not self.joueur: return None
        pos_j = (self.joueur.x, self.joueur.y)
        pos_c = tuple(sorted([(c.x, c.y) for c in self.caisses]))
        return (pos_j, pos_c)

    def appliquer_etat_solveur(self, etat):
        (pos_j, pos_c) = etat
        if self.joueur: self.joueur.x, self.joueur.y = pos_j
        if len(self.caisses) == len(pos_c):
            temp_pos_c = sorted(list(pos_c))
            for i, caisse in enumerate(self.caisses):
                if i < len(temp_pos_c): caisse.x, caisse.y = temp_pos_c[i]
        self._mettre_a_jour_caisses_sur_cibles()