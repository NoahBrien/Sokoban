from abc import ABC, abstractmethod
import collections
import heapq
from . import constantes as C


class Solveur(ABC):
    def __init__(self, niveau_initial_etat):
        self.niveau_initial_etat = niveau_initial_etat

    @abstractmethod
    def resoudre(self):
        pass

    def _reconstruire_chemin(self, etat_final, predecesseurs):
        chemin = []
        etat_actuel = etat_final
        while etat_actuel in predecesseurs and predecesseurs[etat_actuel] is not None:
            etat_prec, mouvement_symbole = predecesseurs[etat_actuel]
            chemin.append(mouvement_symbole)
            etat_actuel = etat_prec
        return chemin[::-1]


class SolveurBFS(Solveur):
    def resoudre(self, niveau_ref_pour_simulation):
        file_etats = collections.deque([(self.niveau_initial_etat, [])])
        visites = {self.niveau_initial_etat}
        max_iterations = 100000;
        iterations = 0

        while file_etats and iterations < max_iterations:
            iterations += 1
            etat_actuel, chemin_actuel = file_etats.popleft()
            niveau_ref_pour_simulation.appliquer_etat_solveur(etat_actuel)
            if niveau_ref_pour_simulation.verifier_victoire():
                print(f"BFS: Solution trouvée ({len(chemin_actuel)} mvts, {iterations} états).")
                return chemin_actuel

            for dx, dy, symbole_mvt in [(0, -1, 'H'), (0, 1, 'B'), (-1, 0, 'G'), (1, 0, 'D')]:
                niveau_ref_pour_simulation.appliquer_etat_solveur(etat_actuel)
                mvt_valide_ou_pousse = niveau_ref_pour_simulation.deplacer_joueur(dx, dy)

                if mvt_valide_ou_pousse is not False:
                    nouvel_etat = niveau_ref_pour_simulation.get_etat_pour_solveur()
                    if nouvel_etat not in visites:
                        visites.add(nouvel_etat)
                        nouveau_chemin = chemin_actuel + [symbole_mvt]
                        file_etats.append((nouvel_etat, nouveau_chemin))
                niveau_ref_pour_simulation.appliquer_etat_solveur(etat_actuel)
        print(f"BFS: Pas de solution ({iterations} états).")
        return None


class SolveurRetourArriere(Solveur):
    def resoudre(self, niveau_ref_pour_simulation, profondeur_max=C.PROFONDEUR_MAX_BACKTRACKING):
        self.solution_trouvee = None
        self.visites_dfs = set()
        self.iterations_dfs = 0
        self.max_iterations_dfs = 2000000

        self._backtrack_recursive(self.niveau_initial_etat, [], profondeur_max, niveau_ref_pour_simulation)

        if self.solution_trouvee:
            print(f"Backtracking: Solution trouvée ({len(self.solution_trouvee)} mvts, {self.iterations_dfs} états).")
        else:
            print(f"Backtracking: Pas de solution (prof={profondeur_max}, iters={self.iterations_dfs}).")
        return self.solution_trouvee

    def _backtrack_recursive(self, etat_actuel, chemin_actuel, profondeur_restante, niveau_sim):
        self.iterations_dfs += 1
        if self.solution_trouvee or profondeur_restante < 0 or self.iterations_dfs > self.max_iterations_dfs: return

        niveau_sim.appliquer_etat_solveur(etat_actuel)
        if niveau_sim.verifier_victoire(): self.solution_trouvee = chemin_actuel; return
        if etat_actuel in self.visites_dfs: return
        self.visites_dfs.add(etat_actuel)

        for dx, dy, symbole_mvt in [(0, -1, 'H'), (0, 1, 'B'), (-1, 0, 'G'), (1, 0, 'D')]:
            niveau_sim.appliquer_etat_solveur(etat_actuel)
            mvt_valide_ou_pousse = niveau_sim.deplacer_joueur(dx, dy)
            if mvt_valide_ou_pousse is not False:
                nouvel_etat = niveau_sim.get_etat_pour_solveur()
                self._backtrack_recursive(nouvel_etat, chemin_actuel + [symbole_mvt], profondeur_restante - 1,
                                          niveau_sim)
                if self.solution_trouvee: return
        if etat_actuel in self.visites_dfs: self.visites_dfs.remove(etat_actuel)