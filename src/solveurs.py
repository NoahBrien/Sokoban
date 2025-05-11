from abc import ABC, abstractmethod
import collections
from . import constantes as C


# Importer Niveau pour type hinting et accès aux constantes de cases si besoin direct
# from .classes import Niveau # Mais on l'évite pour l'import circulaire, on se fie aux méthodes de niveau_sim

class Solveur(ABC):
    def __init__(self, niveau_initial_etat):
        self.niveau_initial_etat = niveau_initial_etat

    @abstractmethod
    def resoudre(self, niveau_ref_pour_simulation): pass

    def _reconstruire_chemin(self, etat_final, predecesseurs):
        chemin = [];
        etat_actuel = etat_final
        while etat_actuel in predecesseurs and predecesseurs[etat_actuel] is not None:
            etat_prec, mvt_sym = predecesseurs[etat_actuel];
            chemin.append(mvt_sym);
            etat_actuel = etat_prec
        return chemin[::-1]


class SolveurBFS(Solveur):  # Reste inchangé
    def resoudre(self, niveau_ref_pour_simulation):
        file_etats = collections.deque([(self.niveau_initial_etat, [])]);
        visites = {self.niveau_initial_etat}
        max_iter = 100000;
        iterations = 0
        while file_etats and iterations < max_iter:
            iterations += 1;
            etat_actuel, chemin_actuel = file_etats.popleft()
            niveau_ref_pour_simulation.appliquer_etat_solveur(etat_actuel)
            if niveau_ref_pour_simulation.verifier_victoire():
                print(f"BFS: Sol ({len(chemin_actuel)}m, {iterations}e).");
                return chemin_actuel
            for dx, dy, sym_mvt in [(0, -1, 'H'), (0, 1, 'B'), (-1, 0, 'G'), (1, 0, 'D')]:
                niveau_ref_pour_simulation.appliquer_etat_solveur(etat_actuel)
                if niveau_ref_pour_simulation.deplacer_joueur(dx, dy, simuler_seulement=True):
                    nouvel_etat = niveau_ref_pour_simulation.get_etat_pour_solveur()
                    if nouvel_etat not in visites:
                        visites.add(nouvel_etat);
                        file_etats.append((nouvel_etat, chemin_actuel + [sym_mvt]))
        print(f"BFS: No sol ({iterations}e).");
        return None


class SolveurRetourArriere(Solveur):
    def _est_impasse_simple(self, etat_caisses_tuple, niveau_sim):
        """
        Vérifie les impasses simples comme une caisse dans un coin non-cible.
        `niveau_sim` doit être un objet Niveau pour vérifier les murs et cibles.
        """
        # `niveau_sim.cases` contient les objets Case.
        # `niveau_sim.cibles` est une liste de (x,y) des cibles.

        for cx, cy in etat_caisses_tuple:
            if (cx, cy) in niveau_sim.cibles:
                continue  # Caisse sur une cible, pas une impasse pour CETTE caisse

            # Vérifier les 4 coins possibles
            # Coin Haut-Gauche
            est_mur_haut = niveau_sim.cases.get((cx, cy - 1), None)
            mur_h = est_mur_haut and est_mur_haut.type_case == C.MUR

            est_mur_bas = niveau_sim.cases.get((cx, cy + 1), None)
            mur_b = est_mur_bas and est_mur_bas.type_case == C.MUR

            est_mur_gauche = niveau_sim.cases.get((cx - 1, cy), None)
            mur_g = est_mur_gauche and est_mur_gauche.type_case == C.MUR

            est_mur_droit = niveau_sim.cases.get((cx + 1, cy), None)
            mur_d = est_mur_droit and est_mur_droit.type_case == C.MUR

            # Caisse dans un coin (non-cible)
            if (mur_h and mur_g) or \
                    (mur_h and mur_d) or \
                    (mur_b and mur_g) or \
                    (mur_b and mur_d):
                # print(f"Impasse détectée: caisse en ({cx},{cy}) dans un coin non-cible.")
                return True  # Impasse trouvée

        return False  # Aucune impasse simple détectée

    def resoudre(self, niveau_ref_pour_simulation, profondeur_max=C.PROFONDEUR_MAX_BACKTRACKING):
        self.solution_trouvee = None;
        self.visites_dfs = set();
        self.iterations_dfs = 0;
        self.max_iterations_dfs = 5000000  # Augmenté un peu la limite

        # Important: l'objet niveau_ref_pour_simulation est utilisé pour vérifier les murs/cibles.
        # Il doit être dans un état "propre" (chargé depuis le contenu initial) avant de commencer la recherche,
        # car _est_impasse_simple a besoin de la structure fixe du niveau.
        # L'état actuel du jeu (pos joueur, pos caisses) est dans self.niveau_initial_etat.
        # On va appliquer cet état initial à une copie du niveau pour la simulation.

        # Créer une instance de Niveau propre pour que `_est_impasse_simple` ait la carte de base.
        # On suppose que `niveau_ref_pour_simulation` passé en argument est déjà une telle instance.
        # Si ce n'est pas le cas, il faudrait la charger ici.
        # Pour que `_est_impasse_simple` fonctionne, `niveau_ref_pour_simulation.cases` et `niveau_ref_pour_simulation.cibles`
        # doivent refléter la structure statique du niveau.
        # `appliquer_etat_solveur` ne modifie que les positions des éléments mobiles, pas les cases/cibles.

        self._backtrack_recursive(self.niveau_initial_etat, [], profondeur_max, niveau_ref_pour_simulation)

        if self.solution_trouvee:
            print(f"Bktrk: Sol ({len(self.solution_trouvee)}m, {self.iterations_dfs}e).")
        else:
            print(
                f"Bktrk: No sol (p={profondeur_max}, i_max_atteintes={self.iterations_dfs >= self.max_iterations_dfs}).")
        return self.solution_trouvee

    def _backtrack_recursive(self, etat_actuel, chemin_actuel, profondeur_restante, niveau_sim):
        self.iterations_dfs += 1
        if self.solution_trouvee or profondeur_restante < 0 or self.iterations_dfs > self.max_iterations_dfs: return

        niveau_sim.appliquer_etat_solveur(etat_actuel)  # Applique pos joueur et caisses
        if niveau_sim.verifier_victoire(): self.solution_trouvee = chemin_actuel; return

        # Vérification d'impasse APRÈS avoir appliqué l'état (pour avoir les pos des caisses)
        _joueur_pos, caisses_pos_tuple = etat_actuel
        if self._est_impasse_simple(caisses_pos_tuple, niveau_sim):
            return  # Élague cette branche car c'est une impasse

        if etat_actuel in self.visites_dfs: return
        self.visites_dfs.add(etat_actuel)

        for dx, dy, sym_mvt in [(0, -1, 'H'), (0, 1, 'B'), (-1, 0, 'G'), (1, 0, 'D')]:
            niveau_sim.appliquer_etat_solveur(etat_actuel)  # Réappliquer l'état avant chaque simulation de mouvement
            if niveau_sim.deplacer_joueur(dx, dy, simuler_seulement=True):
                nouvel_etat = niveau_sim.get_etat_pour_solveur()
                self._backtrack_recursive(nouvel_etat, chemin_actuel + [sym_mvt], profondeur_restante - 1, niveau_sim)
                if self.solution_trouvee: return

        if etat_actuel in self.visites_dfs: self.visites_dfs.remove(etat_actuel)