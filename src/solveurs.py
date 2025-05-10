from abc import ABC, abstractmethod
import collections  # Pour deque (file pour BFS)
import heapq  # Pour A* (non demandé mais structure similaire à BFS avec priorité)
from . import constantes as C


# from .classes import Niveau # Import circulaire si Niveau importe Solveur. Passer état.

class Solveur(ABC):
    """Classe de base abstraite pour les algorithmes de résolution."""

    def __init__(self, niveau_initial_etat):
        self.niveau_initial_etat = niveau_initial_etat  # Un tuple (pos_joueur, pos_caisses_tuple)

    @abstractmethod
    def resoudre(self):
        """Tente de résoudre le niveau. Retourne une liste de mouvements ou None."""
        pass

    def _get_mouvements_possibles(self, etat_joueur, etat_caisses, niveau_obj_temp):
        """
        Retourne les mouvements possibles (dx, dy, est_poussee) depuis un état.
        Nécessite un objet Niveau temporaire pour simuler.
        """
        mouvements = []
        # Il faut un moyen de simuler les mouvements sans modifier l'objet Niveau principal
        # ou en clonant l'objet Niveau. Pour l'instant, on suppose que cette logique
        # serait implémentée ici en utilisant les informations de `niveau_obj_temp`.
        # C'est la partie la plus complexe à interfacer proprement avec la classe Niveau.

        # Exemple simplifié :
        # niveau_obj_temp.appliquer_etat_solveur((etat_joueur, etat_caisses))
        # for dx, dy in [(0, -1), (0, 1), (-1, 0), (1, 0)]:
        #     copie_niveau = niveau_obj_temp.clone() # Méthode à créer dans Niveau
        #     if copie_niveau.deplacer_joueur(dx, dy): # Suppose que deplacer_joueur retourne info si caisse poussée
        #          mouvements.append( ((dx,dy), copie_niveau.get_etat_pour_solveur()) )
        return mouvements  # Liste de ( (dx,dy), nouvel_etat )

    def _reconstruire_chemin(self, etat_final, predecesseurs):
        """Reconstruit le chemin (série de mouvements) à partir des prédécesseurs."""
        chemin = []
        etat_actuel = etat_final
        while etat_actuel in predecesseurs and predecesseurs[etat_actuel] is not None:
            etat_prec, mouvement_symbole = predecesseurs[etat_actuel]
            chemin.append(mouvement_symbole)  # Mouvement symbolique comme 'H', 'B', 'G', 'D'
            etat_actuel = etat_prec
        return chemin[::-1]  # Inverser pour avoir le chemin du début à la fin


class SolveurBFS(Solveur):
    """Implémente l'algorithme de recherche en largeur (Breadth-First Search)."""

    def resoudre(self, niveau_ref_pour_simulation):  # Passe une réf pour simuler
        """
        Tente de résoudre le niveau en utilisant BFS.
        `niveau_ref_pour_simulation` est un objet Niveau sur lequel on peut appeler `appliquer_etat_solveur`
        et `deplacer_joueur` pour tester les mouvements.
        """
        file_etats = collections.deque([(self.niveau_initial_etat, [])])  # (etat, chemin_actuel)
        visites = {self.niveau_initial_etat}  # Ensemble des états visités pour éviter les cycles

        max_iterations = 100000  # Limite pour éviter les boucles infinies sur des niveaux complexes
        iterations = 0

        while file_etats and iterations < max_iterations:
            iterations += 1
            etat_actuel, chemin_actuel = file_etats.popleft()

            niveau_ref_pour_simulation.appliquer_etat_solveur(etat_actuel)  # Mettre le niveau dans cet état
            if niveau_ref_pour_simulation.verifier_victoire():
                print(f"BFS: Solution trouvée en {len(chemin_actuel)} mouvements, {iterations} états explorés.")
                return chemin_actuel  # Liste de mouvements symboliques ('H', 'B', 'G', 'D')

            # Générer les prochains états possibles
            # (joueur_pos, caisses_pos) = etat_actuel
            for dx, dy, symbole_mvt in [(0, -1, 'H'), (0, 1, 'B'), (-1, 0, 'G'), (1, 0, 'D')]:
                # Cloner l'état ou le niveau pour simuler le mouvement
                # C'est la partie délicate. Il faut une copie profonde ou une simulation réversible.
                # Créons une instance temporaire de Niveau pour la simulation
                from .classes import Niveau  # Import local pour éviter import circulaire global

                # Méthode 1: Recharger le niveau à chaque fois (lent)
                # niveau_sim = Niveau(contenu_str=niveau_ref_pour_simulation.contenu_initial_str, est_contenu_direct=True)

                # Méthode 2: Utiliser une copie (nécessite une méthode clone() dans Niveau)
                # Si Niveau.clone() est bien implémenté:
                # niveau_sim = niveau_ref_pour_simulation.clone() # A implementer dans Niveau
                # niveau_sim.appliquer_etat_solveur(etat_actuel)

                # Méthode 3: Utiliser la référence et annuler (plus simple mais modifie la ref)
                niveau_ref_pour_simulation.appliquer_etat_solveur(etat_actuel)  # S'assurer d'être dans le bon état
                a_pousse = niveau_ref_pour_simulation.deplacer_joueur(dx,
                                                                      dy)  # deplacer_joueur doit indiquer si une caisse a été poussée

                if a_pousse is not False:  # Si le mouvement est valide (False si mur, True si simple, objet Caisse si poussée)
                    nouvel_etat = niveau_ref_pour_simulation.get_etat_pour_solveur()
                    if nouvel_etat not in visites:
                        visites.add(nouvel_etat)
                        nouveau_chemin = chemin_actuel + [symbole_mvt]
                        file_etats.append((nouvel_etat, nouveau_chemin))

                # Annuler le mouvement sur niveau_ref_pour_simulation si on l'a modifié
                # Si deplacer_joueur a été fait sur une copie, pas besoin d'annuler.
                # Sinon, il faut une méthode Niveau.annuler_dernier_mouvement_simulation()
                # ou re-appliquer etat_actuel
                niveau_ref_pour_simulation.appliquer_etat_solveur(
                    etat_actuel)  # Revenir à l'état avant la simulation du mouvement

        print(f"BFS: Pas de solution trouvée après {iterations} états explorés.")
        return None


class SolveurRetourArriere(Solveur):
    """Implémente l'algorithme de retour arrière (Backtracking/DFS)."""

    def resoudre(self, niveau_ref_pour_simulation, profondeur_max=C.PROFONDEUR_MAX_BACKTRACKING):
        """
        Tente de résoudre le niveau en utilisant le retour arrière.
        Solution récursive.
        """
        self.solution_trouvee = None
        self.visites_dfs = set()  # Pour éviter les cycles dans la branche actuelle
        self.iterations_dfs = 0
        self.max_iterations_dfs = 200000  # Limite globale

        self._backtrack_recursive(self.niveau_initial_etat, [], profondeur_max, niveau_ref_pour_simulation)

        if self.solution_trouvee:
            print(
                f"Backtracking: Solution trouvée en {len(self.solution_trouvee)} mouvements, {self.iterations_dfs} états explorés.")
        else:
            print(f"Backtracking: Pas de solution trouvée (prof={profondeur_max}, iters={self.iterations_dfs}).")
        return self.solution_trouvee

    def _backtrack_recursive(self, etat_actuel, chemin_actuel, profondeur_restante, niveau_sim):
        self.iterations_dfs += 1
        if self.solution_trouvee or profondeur_restante < 0 or self.iterations_dfs > self.max_iterations_dfs:
            return

        niveau_sim.appliquer_etat_solveur(etat_actuel)
        if niveau_sim.verifier_victoire():
            self.solution_trouvee = chemin_actuel
            return

        # Ajout de la détection de cycle pour DFS
        if etat_actuel in self.visites_dfs:
            return  # Déjà visité dans cette branche
        self.visites_dfs.add(etat_actuel)

        for dx, dy, symbole_mvt in [(0, -1, 'H'), (0, 1, 'B'), (-1, 0, 'G'), (1, 0, 'D')]:
            niveau_sim.appliquer_etat_solveur(etat_actuel)  # Réappliquer l'état avant chaque test de mouvement

            a_pousse = niveau_sim.deplacer_joueur(dx, dy)

            if a_pousse is not False:  # Mouvement valide
                nouvel_etat = niveau_sim.get_etat_pour_solveur()
                self._backtrack_recursive(nouvel_etat, chemin_actuel + [symbole_mvt], profondeur_restante - 1,
                                          niveau_sim)
                if self.solution_trouvee:
                    # Nettoyer visites_dfs avant de remonter si on veut permettre de revisiter par un autre chemin
                    # self.visites_dfs.remove(etat_actuel) # Si on le remet ici, on explore plus mais c'est plus lent
                    return

                    # Si on modifie directement niveau_sim, il faudrait annuler le mouvement ici.
            # Plus simple: appliquer_etat_solveur(etat_actuel) au début de chaque itération de la boucle for.

        # Retirer de visites_dfs en remontant la pile d'appel pour permettre d'autres chemins vers cet état
        if etat_actuel in self.visites_dfs:  # Vérifier car on a pu le remove si solution trouvée dans une sous-branche
            self.visites_dfs.remove(etat_actuel)