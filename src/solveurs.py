from abc import ABC, abstractmethod
import collections
try:
    from . import constantes as C
except ImportError:
    import constantes as C

class Solveur(ABC):
    """Classe de base pour tous les solveurs de Sokoban."""
    def __init__(self, niveau_initial_etat):
        self.niveau_initial_etat = niveau_initial_etat

    @abstractmethod
    def resoudre(self, niveau_ref_pour_simulation):
        """Résout le niveau et retourne (chemin, itérations) ou (None, itérations)."""
        pass

class SolveurBFS(Solveur):
    """Résout en utilisant Breadth-First Search (cherche le chemin le plus court)."""
    def resoudre(self, niveau_ref_pour_simulation):
        """Retourne le plus court chemin en mouvements ou None si échec."""
        if self.niveau_initial_etat is None:
            return None, 0
        file_etats = collections.deque([(self.niveau_initial_etat, [])])
        visites = {self.niveau_initial_etat}
        iterations = 0
        while file_etats:
            iterations += 1
            etat, chemin = file_etats.popleft()
            niveau_ref_pour_simulation.appliquer_etat_solveur(etat)
            if niveau_ref_pour_simulation.verifier_victoire():
                return chemin, iterations
            for dx, dy, sym in [(0,-1,'H'),(0,1,'B'),(-1,0,'G'),(1,0,'D')]:
                niveau_ref_pour_simulation.appliquer_etat_solveur(etat)
                if niveau_ref_pour_simulation.deplacer_joueur(dx, dy, C.TAILLE_CASE, simuler_seulement=True):
                    nv = niveau_ref_pour_simulation.get_etat_pour_solveur()
                    if nv and nv not in visites:
                        visites.add(nv)
                        file_etats.append((nv, chemin+[sym]))
        return None, iterations

class SolveurRetourArriere(Solveur):
    """Résout en DFS backtracking optimisé avec borne initiale BFS."""
    def __init__(self, niveau_initial_etat):
        super().__init__(niveau_initial_etat)
        self.best_solution = None
        self.best_length = float('inf')
        self.iterations = 0
        self.cibles = None

    def _heuristique(self, etat):
        """Heuristique: somme des distances Manhattan caisse→plus proche cible."""
        _, caisses = etat
        return sum(min(abs(bx-gx)+abs(by-gy) for gx,gy in self.cibles) for bx,by in caisses)

    def resoudre(self, niveau_ref_pour_simulation, Max):
        """Lance d'abord un BFS pour la borne, puis backtracking optimisé."""
        if self.niveau_initial_etat is None:
            return None, 0
        bfs = SolveurBFS(self.niveau_initial_etat)
        bfs_path, bfs_iters = bfs.resoudre(niveau_ref_pour_simulation)
        self.iterations = bfs_iters
        if bfs_path:
            self.best_solution = bfs_path.copy()
            self.best_length = len(bfs_path)
        else:
            self.best_solution = None
        self.cibles = niveau_ref_pour_simulation.cibles
        self.visites = set()
        self._dfs(self.niveau_initial_etat, [], 0, niveau_ref_pour_simulation)
        return self.best_solution, self.iterations

    def _dfs(self, etat, chemin, depth, niveau_sim):
        """Fonction récursive DFS avec pruning heuristique et détection d'impasse."""
        self.iterations += 1
        if depth + self._heuristique(etat) >= self.best_length:
            return
        if etat in self.visites:
            return
        self.visites.add(etat)
        niveau_sim.appliquer_etat_solveur(etat)
        if niveau_sim.verifier_victoire():
            self.best_solution = chemin.copy()
            self.best_length = depth
            self.visites.remove(etat)
            return
        if self._est_impasse(etat[1], niveau_sim):
            self.visites.remove(etat)
            return
        for dx, dy, sym in [(0,-1,'H'),(0,1,'B'),(-1,0,'G'),(1,0,'D')]:
            niveau_sim.appliquer_etat_solveur(etat)
            if niveau_sim.deplacer_joueur(dx, dy, C.TAILLE_CASE, simuler_seulement=True):
                nv = niveau_sim.get_etat_pour_solveur()
                if nv:
                    chemin.append(sym)
                    self._dfs(nv, chemin, depth+1, niveau_sim)
                    chemin.pop()
        self.visites.remove(etat)

    def _est_impasse(self, caisses, niveau_sim):
        """Détecte les impasses simples (coin) et freeze deadlocks."""
        cibles_set = set(niveau_sim.cibles)
        murs_set = {pos for pos,case in niveau_sim.cases.items() if case.type_case==C.MUR}
        for cx,cy in caisses:
            if (cx,cy) in cibles_set:
                continue
            h = (cx,cy-1) in murs_set; b = (cx,cy+1) in murs_set
            g = (cx-1,cy) in murs_set; d = (cx+1,cy) in murs_set
            if (h and g) or (h and d) or (b and g) or (b and d):
                return True
        return False