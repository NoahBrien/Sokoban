from abc import ABC, abstractmethod
import collections
from . import constantes as C


# from .classes import Niveau # Éviter import direct pour contourner dépendance circulaire si Niveau importe Solveur

class Solveur(ABC):
    def __init__(self, niveau_initial_etat):
        self.niveau_initial_etat = niveau_initial_etat  # ((jx,jy), ((c1x,c1y), (c2x,c2y)...))

    @abstractmethod
    def resoudre(self, niveau_ref_pour_simulation):
        """
        Doit retourner un tuple (chemin_solution, iterations)
        où chemin_solution est une liste de mouvements ['H', 'B', 'G', 'D'] ou None.
        iterations est un entier comptant les étapes/états explorés.
        """
        pass

    # _reconstruire_chemin n'est plus utilisé car les solveurs construisent le chemin directement.
    # Si besoin, il pourrait être réintégré.


class SolveurBFS(Solveur):
    def resoudre(self, niveau_ref_pour_simulation):
        if self.niveau_initial_etat is None:
            print("BFS: État initial non valide.")
            return None, 0

        file_etats = collections.deque([(self.niveau_initial_etat, [])])  # (etat, chemin_pour_etat)
        visites = {self.niveau_initial_etat}

        # Limite d'itérations pour éviter les recherches trop longues sur des niveaux complexes/insolubles
        max_iter = 50000  # Réduit pour tests rapides, peut être augmenté
        iterations = 0

        while file_etats and iterations < max_iter:
            iterations += 1
            etat_actuel, chemin_actuel = file_etats.popleft()

            niveau_ref_pour_simulation.appliquer_etat_solveur(etat_actuel)  # Appliquer l'état à simuler

            if niveau_ref_pour_simulation.verifier_victoire():
                print(f"BFS: Solution trouvée en {len(chemin_actuel)} mouvements, {iterations} iterations.")
                return chemin_actuel, iterations

            # Simuler les 4 mouvements possibles
            for dx, dy, sym_mvt in [(0, -1, 'H'), (0, 1, 'B'), (-1, 0, 'G'), (1, 0, 'D')]:
                niveau_ref_pour_simulation.appliquer_etat_solveur(
                    etat_actuel)  # Réappliquer l'état actuel avant chaque test de mouvement

                if niveau_ref_pour_simulation.deplacer_joueur(dx, dy, simuler_seulement=True):
                    nouvel_etat = niveau_ref_pour_simulation.get_etat_pour_solveur()
                    if nouvel_etat and nouvel_etat not in visites:
                        visites.add(nouvel_etat)
                        file_etats.append((nouvel_etat, chemin_actuel + [sym_mvt]))

        if iterations >= max_iter:
            print(f"BFS: Limite d'itérations ({max_iter}) atteinte. Pas de solution trouvée.")
        else:
            print(f"BFS: Pas de solution trouvée après {iterations} iterations.")
        return None, iterations


class SolveurRetourArriere(Solveur):
    def _est_impasse_simple(self, etat_caisses_tuple, niveau_sim):
        # Vérifie si une caisse est dans un coin non-cible
        for cx, cy in etat_caisses_tuple:
            if (cx, cy) in niveau_sim.cibles:  # Caisse sur une cible, OK pour cette caisse
                continue

            # Vérifier les cases adjacentes pour les murs
            mur_haut = niveau_sim.cases.get((cx, cy - 1)) and niveau_sim.cases[(cx, cy - 1)].type_case == C.MUR
            mur_bas = niveau_sim.cases.get((cx, cy + 1)) and niveau_sim.cases[(cx, cy + 1)].type_case == C.MUR
            mur_gauche = niveau_sim.cases.get((cx - 1, cy)) and niveau_sim.cases[(cx - 1, cy)].type_case == C.MUR
            mur_droit = niveau_sim.cases.get((cx + 1, cy)) and niveau_sim.cases[(cx + 1, cy)].type_case == C.MUR

            # Si dans un coin formé par deux murs
            if (mur_haut and mur_gauche) or \
                    (mur_haut and mur_droit) or \
                    (mur_bas and mur_gauche) or \
                    (mur_bas and mur_droit):
                # print(f"Impasse détectée: caisse en ({cx},{cy}) dans un coin non-cible.")
                return True
        return False

    def resoudre(self, niveau_ref_pour_simulation, profondeur_max=C.PROFONDEUR_MAX_BACKTRACKING):
        if self.niveau_initial_etat is None:
            print("Backtracking: État initial non valide.")
            return None, 0

        self.solution_trouvee = None
        self.visites_dfs = set()  # Stocke les états (joueur_pos, caisses_pos_tuple) visités pour la profondeur actuelle
        self.iterations_dfs = 0
        self.max_iterations_dfs_limite = 2000000  # Limite globale pour éviter blocage

        self._backtrack_recursive(self.niveau_initial_etat, [], profondeur_max, niveau_ref_pour_simulation)

        if self.solution_trouvee:
            print(
                f"Backtracking: Solution trouvée en {len(self.solution_trouvee)} mouvements, {self.iterations_dfs} itérations.")
        else:
            msg_fin = "Pas de solution trouvée"
            if self.iterations_dfs >= self.max_iterations_dfs_limite:
                msg_fin += " (limite d'itérations atteinte)"
            elif profondeur_max <= 0:
                msg_fin += f" (profondeur max {profondeur_max} atteinte)"
            else:
                msg_fin += f" (profondeur {profondeur_max})"

            print(f"Backtracking: {msg_fin} après {self.iterations_dfs} itérations.")
        return self.solution_trouvee, self.iterations_dfs

    def _backtrack_recursive(self, etat_actuel, chemin_actuel, profondeur_restante, niveau_sim):
        self.iterations_dfs += 1
        if self.solution_trouvee or profondeur_restante < 0 or self.iterations_dfs >= self.max_iterations_dfs_limite:
            return

        niveau_sim.appliquer_etat_solveur(etat_actuel)
        if niveau_sim.verifier_victoire():
            self.solution_trouvee = list(chemin_actuel)  # Copier le chemin
            return

        _joueur_pos, caisses_pos_tuple = etat_actuel
        if self._est_impasse_simple(caisses_pos_tuple, niveau_sim):
            return  # Élague cette branche

        # Visites pour éviter les cycles dans la même branche de recherche (DFS)
        # Pour DFS, on ajoute l'état en entrant et on le retire en sortant de la récursion pour ce chemin
        if etat_actuel in self.visites_dfs:
            return
        self.visites_dfs.add(etat_actuel)

        for dx, dy, sym_mvt in [(0, -1, 'H'), (0, 1, 'B'), (-1, 0, 'G'), (1, 0, 'D')]:
            niveau_sim.appliquer_etat_solveur(etat_actuel)  # Ré-appliquer état avant chaque test de mouvement

            if niveau_sim.deplacer_joueur(dx, dy, simuler_seulement=True):
                nouvel_etat = niveau_sim.get_etat_pour_solveur()
                if nouvel_etat:  # S'assurer que l'état est valide
                    chemin_actuel.append(sym_mvt)
                    self._backtrack_recursive(nouvel_etat, chemin_actuel, profondeur_restante - 1, niveau_sim)
                    chemin_actuel.pop()  # Backtrack: retirer le dernier mouvement essayé
                    if self.solution_trouvee: return

        self.visites_dfs.remove(etat_actuel)  # Retirer de visites en sortant de la récursion pour cet état