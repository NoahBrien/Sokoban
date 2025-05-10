import pygame
from . import constantes as C  # Bouton a besoin des constantes pour les couleurs par défaut et la police


class Bouton:
    """Classe simple pour créer des boutons cliquables."""

    def __init__(self, x, y, largeur, hauteur, texte,
                 couleur_fond=C.DARK_BUTTON_BG,
                 couleur_survol=C.DARK_BUTTON_HOVER_BG,
                 couleur_texte=C.DARK_TEXT_PRIMARY,
                 font=None,  # La police sera passée par l'instance qui crée le bouton
                 action=None,
                 border_radius=5):  # Ajout du border_radius
        self.rect = pygame.Rect(x, y, largeur, hauteur)
        self.texte = texte
        self.couleur_fond_base = couleur_fond
        self.couleur_survol = couleur_survol
        self.couleur_texte = couleur_texte
        # La police doit être initialisée par l'appelant, car pygame.font.Font nécessite pygame.init()
        # et il est préférable de gérer les polices de manière centralisée (par ex. dans InterfaceGraphique)
        self.font = font  # Doit être un objet pygame.font.Font valide
        self.action = action
        self.survol = False
        self.border_radius = border_radius

    def dessiner(self, surface):
        if not self.font:  # Sécurité si la police n'a pas été passée
            print("Avertissement: Bouton dessiné sans police valide!")
            default_font = pygame.font.Font(C.POLICE_DEFAUT, C.TAILLE_POLICE_MENU)  # Fallback
            texte_surface = default_font.render(self.texte, True, self.couleur_texte)
        else:
            texte_surface = self.font.render(self.texte, True, self.couleur_texte)

        couleur_actuelle_fond = self.couleur_survol if self.survol else self.couleur_fond_base
        pygame.draw.rect(surface, couleur_actuelle_fond, self.rect, border_radius=self.border_radius)
        pygame.draw.rect(surface, C.DARK_GRID_LINE, self.rect, 2, border_radius=self.border_radius)  # Bordure

        texte_rect = texte_surface.get_rect(center=self.rect.center)
        surface.blit(texte_surface, texte_rect)

    def verifier_clic(self, pos_souris):
        if self.rect.collidepoint(pos_souris):
            if self.action:
                return self.action
        return None

    def verifier_survol(self, pos_souris):
        self.survol = self.rect.collidepoint(pos_souris)