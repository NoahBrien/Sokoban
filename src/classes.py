import pygame
from . import constantes as C
from . import utilitaires


class ElementJeu:
    """Classe de base pour les éléments du jeu comme Case, Caisse, Joueur."""

    def __init__(self, x, y):
        self.x = x  # Position en grille
        self.y = y  # Position en grille

    def dessiner(self, surface, images, offset_x=0, offset_y=0):
        """Méthode de dessin générique, à surcharger."""
        pass  # Doit être implémenté par les classes filles


class Case(ElementJeu):
    """Représente une case du plateau de jeu (mur, sol, cible)."""

    def __init__(self, x, y, type_case):
        super().__init__(x, y)
        if type_case not in [C.MUR, C.SOL, C.CIBLE]:
            raise ValueError(f"Type de case inconnu: {type_case}")
        self.type_case = type_case  # C.MUR, C.SOL, C.CIBLE

    def dessiner(self, surface, images, offset_x=0, offset_y=0):
        """Dessine la case sur la surface donnée."""
        img_key = self.type_case
        if self.type_case == C.CIBLE:
            img_key = C.CIBLE
        elif self.type_case == C.MUR:
            img_key = C.MUR
        else:  # Sol
            img_key = C.SOL

        if img_key in images:
            surface.blit(images[img_key], (self.x * C.TAILLE_CASE + offset_x, self.y * C.TAILLE_CASE + offset_y))
        else:  # Fallback si image non trouvée
            couleur = C.GRIS if self.type_case == C.MUR else C.GRIS_CLAIR if self.type_case == C.SOL else C.ROSE
            pygame.draw.rect(surface, couleur, (
            self.x * C.TAILLE_CASE + offset_x, self.y * C.TAILLE_CASE + offset_y, C.TAILLE_CASE, C.TAILLE_CASE))


class Caisse(ElementJeu):
    """Représente une caisse qui peut être déplacée."""

    def __init__(self, x, y):
        super().__init__(x, y)
        self.sur_cible = False

    def dessiner(self, surface, images, offset_x=0, offset_y=0):
        """Dessine la caisse."""
        img_key = C.CAISSE_SUR_CIBLE if self.sur_cible else C.CAISSE
        if img_key in images:
            surface.blit(images[img_key], (self.x * C.TAILLE_CASE + offset_x, self.y * C.TAILLE_CASE + offset_y))
        else:  # Fallback
            couleur = C.VERT if self.sur_cible else C.MARRON
            pygame.draw.rect(surface, couleur, (
            self.x * C.TAILLE_CASE + offset_x + 5, self.y * C.TAILLE_CASE + offset_y + 5, C.TAILLE_CASE - 10,
            C.TAILLE_CASE - 10))


class Joueur(ElementJeu):
    """Représente le personnage contrôlé par l'utilisateur."""

    def __init__(self, x, y):
        super().__init__(x, y)
        # self.sur_cible = False # Géré par la case sous le joueur

    def dessiner(self, surface, images, offset_x=0, offset_y=0):
        """Dessine le joueur."""
        img_key = C.JOUEUR
        if img_key in images:
            surface.blit(images[img_key], (self.x * C.TAILLE_CASE + offset_x, self.y * C.TAILLE_CASE + offset_y))
        else:  # Fallback
            pygame.draw.circle(surface, C.BLEU, (self.x * C.TAILLE_CASE + C.TAILLE_CASE // 2 + offset_x,
                                                 self.y * C.TAILLE_CASE + C.TAILLE_CASE // 2 + offset_y),
                               C.TAILLE_CASE // 3)


class Niveau:
    """Gère la structure d'un niveau et ses interactions."""

    def __init__(self, nom_fichier_ou_contenu=None, est_contenu_direct=False):
        self.cases = {}  # Dictionnaire (x, y) -> Case
        self.caisses = []
        self.cibles = []
        self.joueur = None
        self.largeur = 0  # En nombre de cases
        self.hauteur = 0  # En nombre de cases
        self.mouvements_historique = []  # Pour la fonction undo
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
        """Charge un niveau à partir d'un fichier texte."""
        try:
            with open(nom_fichier, 'r') as f:
                self.contenu_initial_str = f.read()
                self._charger_contenu(self.contenu_initial_str)
        except FileNotFoundError:
            print(f"Fichier niveau {nom_fichier} introuvable.")
            # Créer un niveau vide ou par défaut
            self._charger_contenu(f"{C.MUR}{C.MUR}{C.MUR}\n{C.MUR}{C.JOUEUR}{C.MUR}\n{C.MUR}{C.MUR}{C.MUR}")

    def _charger_contenu(self, contenu_str):
        """Charge un niveau à partir d'une chaîne de caractères."""
        self.cases.clear()
        self.caisses.clear()
        self.cibles.clear()
        self.joueur = None
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
                    self.cases[pos] = Case(x, y, C.SOL)  # Joueur est sur un sol
                    self.joueur = Joueur(x, y)
                elif caractere == C.CAISSE:
                    self.cases[pos] = Case(x, y, C.SOL)  # Caisse est sur un sol
                    self.caisses.append(Caisse(x, y))
                elif caractere == C.JOUEUR_SUR_CIBLE:  # Joueur sur une cible
                    self.cases[pos] = Case(x, y, C.CIBLE)
                    self.cibles.append(pos)
                    self.joueur = Joueur(x, y)
                elif caractere == C.CAISSE_SUR_CIBLE:  # Caisse sur une cible
                    self.cases[pos] = Case(x, y, C.CIBLE)
                    self.cibles.append(pos)
                    c = Caisse(x, y)
                    c.sur_cible = True
                    self.caisses.append(c)
                else:  # Si caractère inconnu ou espace manquant, considérer comme sol
                    self.cases[pos] = Case(x, y, C.SOL)
            # Compléter les lignes plus courtes avec du sol (ou des murs si on veut encadrer)
            for x_fill in range(len(ligne), self.largeur):
                self.cases[(x_fill, y)] = Case(x_fill, y, C.SOL)  # ou C.MUR

    def _get_element_a_position(self, x, y):
        """Retourne la case, une caisse, ou None à la position (x,y)."""
        for caisse in self.caisses:
            if caisse.x == x and caisse.y == y:
                return caisse
        return self.cases.get((x, y))

    def _mettre_a_jour_caisses_sur_cibles(self):
        """Met à jour l'état 'sur_cible' de toutes les caisses."""
        for caisse in self.caisses:
            caisse.sur_cible = (caisse.x, caisse.y) in self.cibles

    def deplacer_joueur(self, dx, dy, sons=None):
        """Déplace le joueur et pousse les caisses si nécessaire. Retourne True si le mouvement est effectué."""
        if not self.joueur: return False

        ancienne_pos_joueur = (self.joueur.x, self.joueur.y)
        nouvelle_pos_joueur_x, nouvelle_pos_joueur_y = self.joueur.x + dx, self.joueur.y + dy

        element_destination = self._get_element_a_position(nouvelle_pos_joueur_x, nouvelle_pos_joueur_y)

        mouvement_effectue = False
        caisse_poussee_ancienne_pos = None
        caisse_poussee_nouvelle_pos = None

        if isinstance(element_destination, Case) and element_destination.type_case != C.MUR:
            # Mouvement vers une case vide (sol ou cible)
            self.joueur.x = nouvelle_pos_joueur_x
            self.joueur.y = nouvelle_pos_joueur_y
            mouvement_effectue = True
            if sons and sons.get("deplacement"): sons["deplacement"].play()

        elif isinstance(element_destination, Caisse):
            # Tentative de pousser une caisse
            caisse_a_pousser = element_destination
            nouvelle_pos_caisse_x, nouvelle_pos_caisse_y = caisse_a_pousser.x + dx, caisse_a_pousser.y + dy
            element_derriere_caisse = self._get_element_a_position(nouvelle_pos_caisse_x, nouvelle_pos_caisse_y)

            if isinstance(element_derriere_caisse, Case) and element_derriere_caisse.type_case != C.MUR:
                # La caisse peut être poussée
                caisse_poussee_ancienne_pos = (caisse_a_pousser.x, caisse_a_pousser.y)

                caisse_a_pousser.x = nouvelle_pos_caisse_x
                caisse_a_pousser.y = nouvelle_pos_caisse_y
                self.joueur.x = nouvelle_pos_joueur_x
                self.joueur.y = nouvelle_pos_joueur_y

                caisse_poussee_nouvelle_pos = (caisse_a_pousser.x, caisse_a_pousser.y)
                mouvement_effectue = True
                if sons and sons.get("pousse"): sons["pousse"].play()

        if mouvement_effectue:
            self.mouvements_historique.append({
                "joueur_avant": ancienne_pos_joueur,
                "joueur_apres": (self.joueur.x, self.joueur.y),
                "caisse_poussee_avant": caisse_poussee_ancienne_pos,  # Peut être None
                "caisse_poussee_apres": caisse_poussee_nouvelle_pos  # Peut être None
            })
            self._mettre_a_jour_caisses_sur_cibles()

        return mouvement_effectue

    def annuler_dernier_mouvement(self):
        """Annule le dernier mouvement effectué."""
        if not self.mouvements_historique:
            return False

        dernier_mouvement = self.mouvements_historique.pop()

        self.joueur.x, self.joueur.y = dernier_mouvement["joueur_avant"]

        if dernier_mouvement["caisse_poussee_avant"] and dernier_mouvement["caisse_poussee_apres"]:
            # Trouver la caisse qui a été poussée à "caisse_poussee_apres" et la remettre à "caisse_poussee_avant"
            pos_apres_x, pos_apres_y = dernier_mouvement["caisse_poussee_apres"]
            caisse_trouvee = None
            for caisse in self.caisses:
                if caisse.x == pos_apres_x and caisse.y == pos_apres_y:
                    caisse_trouvee = caisse
                    break
            if caisse_trouvee:
                caisse_trouvee.x, caisse_trouvee.y = dernier_mouvement["caisse_poussee_avant"]

        self._mettre_a_jour_caisses_sur_cibles()
        return True

    def verifier_victoire(self):
        """Vérifie si toutes les caisses sont sur des cibles."""
        if not self.caisses or not self.cibles: return False  # Pas de caisses ou pas de cibles, pas de victoire possible
        if len(self.caisses) != len(self.cibles):  # Cas particulier mais possible si mal conçu
            # print("Attention: Nombre de caisses différent du nombre de cibles.")
            pass  # On continue, peut-être que toutes les caisses doivent être sur *certaines* cibles

        for caisse in self.caisses:
            if not caisse.sur_cible:
                return False
        return True

    def reinitialiser(self):
        """Réinitialise le niveau à son état initial."""
        if self.contenu_initial_str:
            self._charger_contenu(self.contenu_initial_str)
        elif self.nom_fichier:
            self._charger_fichier(self.nom_fichier)
        self._mettre_a_jour_caisses_sur_cibles()

    def dessiner(self, surface, images, offset_x=0, offset_y=0):
        """Dessine le niveau complet (cases, caisses, joueur)."""
        surface.fill(C.NOIR)  # Fond noir par défaut

        # Calculer l'offset pour centrer le niveau si plus petit que la fenêtre
        # Pour l'instant, on dessine depuis (0,0) de la surface de jeu

        for case in self.cases.values():
            case.dessiner(surface, images, offset_x, offset_y)

        for caisse in self.caisses:
            caisse.dessiner(surface, images, offset_x, offset_y)

        if self.joueur:
            self.joueur.dessiner(surface, images, offset_x, offset_y)

    def get_etat_pour_solveur(self):
        """Retourne un tuple représentant l'état actuel du niveau (positions joueur et caisses)."""
        if not self.joueur: return None
        pos_joueur = (self.joueur.x, self.joueur.y)
        # Trier les positions des caisses pour que l'état soit unique regardless de l'ordre des objets Caisse
        pos_caisses = tuple(sorted([(c.x, c.y) for c in self.caisses]))
        return (pos_joueur, pos_caisses)

    def appliquer_etat_solveur(self, etat):
        """Applique un état donné (positions joueur et caisses) au niveau."""
        (pos_joueur, pos_caisses) = etat
        if self.joueur:
            self.joueur.x, self.joueur.y = pos_joueur

        if len(self.caisses) == len(pos_caisses):
            # Attention : ceci suppose que l'ordre des caisses dans pos_caisses correspond
            # à l'ordre dans self.caisses si on les trie. C'est pourquoi get_etat_pour_solveur trie.
            # Une meilleure approche serait de recréer les objets caisses ou de les mapper.
            # Pour la simplicité de la visualisation, on fait une attribution directe.
            # Si on ne trie pas dans get_etat_pour_solveur, il faut s'assurer que l'ordre est cohérent.

            # Pour être robuste, il faudrait recréer les caisses ou les réassigner intelligemment.
            # Ici, on assume que self.caisses est déjà trié ou que l'ordre ne change pas.
            # Ou, plus simplement, on fait correspondre par index si le nombre est identique.
            temp_pos_caisses = sorted(list(pos_caisses))  # Assurer l'ordre

            # Trier self.caisses une fois (ou maintenir trié) peut être utile
            # self.caisses.sort(key=lambda c: (c.x, c.y)) # Si on veut trier pour correspondre

            for i, caisse in enumerate(self.caisses):  # Pas idéal si l'ordre de self.caisses change
                # Si self.caisses n'est pas trié comme pos_caisses, cette boucle ne marchera pas.
                # Pour l'instant, on va faire simple et assumer que l'ordre est stable.
                # Alternative:
                # self.caisses = [Caisse(px, py) for px, py in pos_caisses]
                # Ou une mise à jour plus complexe.
                # Pour l'instant, on suppose que la liste self.caisses est dans un ordre fixe
                # et que le solveur renvoie les positions dans le même ordre implicite.
                # C'est souvent le cas si on clone le niveau et qu'on modifie les mêmes objets.
                if i < len(temp_pos_caisses):
                    caisse.x, caisse.y = temp_pos_caisses[i]

        self._mettre_a_jour_caisses_sur_cibles()