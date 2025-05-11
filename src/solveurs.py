from abc import ABC, abstractmethod
import collections
from . import constantes as C

class Solveur(ABC):
    def __init__(self, niveau_initial_etat):
        """Classe abstraite de base pour les solveurs de Sokoban."""
        self.niveau_initial_etat = niveau_initial_etat

    @abstractmethod
    def resoudre(self, niveau_ref_pour_simulation):
        """Méthode abstraite pour résoudre le niveau. Doit retourner (chemin, iterations)."""
        pass

class SolveurBFS(Solveur):
    def resoudre(self, niveau_ref_pour_simulation):
        """Résout le niveau en utilisant l'algorithme BFS."""
        if self.niveau_initial_etat is None: return None, 0
        file_etats = collections.deque([(self.niveau_initial_etat, [])])
        visites = {self.niveau_initial_etat}
        max_iter = 50000; iterations = 0
        while file_etats and iterations < max_iter:
            iterations += 1
            etat_actuel, chemin_actuel = file_etats.popleft()
            niveau_ref_pour_simulation.appliquer_etat_solveur(etat_actuel)
            if niveau_ref_pour_simulation.verifier_victoire():
                return chemin_actuel, iterations
            for dx, dy, sym_mvt in [(0,-1,'H'),(0,1,'B'),(-1,0,'G'),(1,0,'D')]:
                niveau_ref_pour_simulation.appliquer_etat_solveur(etat_actuel)
                if niveau_ref_pour_simulation.deplacer_joueur(dx,dy,C.TAILLE_CASE,simuler_seulement=True):
                    nouvel_etat = niveau_ref_pour_simulation.get_etat_pour_solveur()
                    if nouvel_etat and nouvel_etat not in visites:
                        visites.add(nouvel_etat)
                        file_etats.append((nouvel_etat, chemin_actuel + [sym_mvt]))
        return None, iterations

class SolveurRetourArriere(Solveur):
    def _est_impasse_simple(self, etat_caisses_tuple, niveau_sim):
        """Vérifie les impasses simples (caisse dans un coin non-cible)."""
        for cx, cy in etat_caisses_tuple:
            if (cx,cy) in niveau_sim.cibles: continue
            mur_h = niveau_sim.cases.get((cx,cy-1)) and niveau_sim.cases[(cx,cy-1)].type_case == C.MUR
            mur_b = niveau_sim.cases.get((cx,cy+1)) and niveau_sim.cases[(cx,cy+1)].type_case == C.MUR
            mur_g = niveau_sim.cases.get((cx-1,cy)) and niveau_sim.cases[(cx-1,cy)].type_case == C.MUR
            mur_d = niveau_sim.cases.get((cx+1,cy)) and niveau_sim.cases[(cx+1,cy)].type_case == C.MUR
            if (mur_h and mur_g) or (mur_h and mur_d) or \
               (mur_b and mur_g) or (mur_b and mur_d):
                return True
        return False

    def resoudre(self, niveau_ref_pour_simulation, profondeur_max=C.PROFONDEUR_MAX_BACKTRACKING):
        """Résout le niveau en utilisant l'algorithme de retour arrière (DFS)."""
        if self.niveau_initial_etat is None: return None, 0
        self.solution_trouvee = None; self.visites_dfs = set(); self.iterations_dfs = 0
        self.max_iterations_dfs_limite = 2000000
        self._backtrack_recursive(self.niveau_initial_etat, [], profondeur_max, niveau_ref_pour_simulation)
        return self.solution_trouvee, self.iterations_dfs

    def _backtrack_recursive(self, etat_actuel, chemin_actuel, profondeur_restante, niveau_sim):
        """Fonction récursive pour l'algorithme de retour arrière."""
        self.iterations_dfs += 1
        if self.solution_trouvee or profondeur_restante < 0 or self.iterations_dfs >= self.max_iterations_dfs_limite:
            return
        niveau_sim.appliquer_etat_solveur(etat_actuel)
        if niveau_sim.verifier_victoire():
            self.solution_trouvee = list(chemin_actuel); return
        _joueur_pos, caisses_pos_tuple = etat_actuel
        if self._est_impasse_simple(caisses_pos_tuple, niveau_sim): return
        if etat_actuel in self.visites_dfs: return 
        self.visites_dfs.add(etat_actuel)
        for dx, dy, sym_mvt in [(0,-1,'H'),(0,1,'B'),(-1,0,'G'),(1,0,'D')]:
            niveau_sim.appliquer_etat_solveur(etat_actuel)
            if niveau_sim.deplacer_joueur(dx,dy,C.TAILLE_CASE,simuler_seulement=True):
                nouvel_etat = niveau_sim.get_etat_pour_solveur()
                if nouvel_etat:
                    chemin_actuel.append(sym_mvt)
                    self._backtrack_recursive(nouvel_etat, chemin_actuel, profondeur_restante - 1, niveau_sim)
                    chemin_actuel.pop() 
                    if self.solution_trouvee: return
        self.visites_dfs.remove(etat_actuel)