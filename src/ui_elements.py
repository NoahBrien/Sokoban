import pygame
from . import constantes as C


class Bouton:
    def __init__(self, x, y, largeur, hauteur, texte,
                 couleur_fond=C.DARK_BUTTON_BG,
                 couleur_survol=C.DARK_BUTTON_HOVER_BG,
                 couleur_texte=C.DARK_TEXT_PRIMARY,
                 font=None,
                 action=None,
                 border_radius=5):
        self.rect = pygame.Rect(x, y, largeur, hauteur)
        self.texte = texte
        self.couleur_fond_base = couleur_fond
        self.couleur_survol = couleur_survol
        self.couleur_texte = couleur_texte
        self.font = font
        self.action = action
        self.survol = False
        self.border_radius = border_radius

    def dessiner(self, surface):
        if not self.font:
            current_font = pygame.font.Font(None, C.TAILLE_POLICE_MENU)
        else:
            current_font = self.font

        texte_surface = current_font.render(self.texte, True, self.couleur_texte)

        couleur_actuelle_fond = self.couleur_survol if self.survol else self.couleur_fond_base
        pygame.draw.rect(surface, couleur_actuelle_fond, self.rect, border_radius=self.border_radius)
        pygame.draw.rect(surface, C.DARK_GRID_LINE, self.rect, 2, border_radius=self.border_radius)

        texte_rect = texte_surface.get_rect(center=self.rect.center)
        surface.blit(texte_surface, texte_rect)

    def verifier_clic(self, pos_souris):
        if self.rect.collidepoint(pos_souris):
            if self.action:
                return self.action
        return None

    def verifier_survol(self, pos_souris):
        self.survol = self.rect.collidepoint(pos_souris)