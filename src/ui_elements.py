import pygame
from . import constantes as C


class Bouton:
    def __init__(self, x, y, largeur, hauteur, texte,
                 couleur_fond=C.DARK_BUTTON_BG,
                 couleur_survol=C.DARK_BUTTON_HOVER_BG,
                 couleur_texte=C.DARK_TEXT_PRIMARY,
                 font=None,
                 action=None,
                 border_radius=5,
                 enabled=True):  # Ajout de l'état activé/désactivé
        self.rect = pygame.Rect(x, y, largeur, hauteur)
        self.texte = texte
        self.couleur_fond_base = couleur_fond
        self.couleur_survol = couleur_survol
        self.couleur_texte = couleur_texte
        self.font = font if font else pygame.font.Font(C.POLICE_DEFAUT, C.TAILLE_POLICE_MENU)
        self.action = action
        self.survol = False
        self.border_radius = border_radius
        self.enabled = enabled

    def dessiner(self, surface):
        couleur_fond_actuelle = self.couleur_fond_base
        couleur_texte_actuelle = self.couleur_texte

        if not self.enabled:
            # Assombrir si désactivé
            couleur_fond_actuelle = tuple(c // 1.5 for c in self.couleur_fond_base)
            couleur_texte_actuelle = tuple(c // 1.5 for c in self.couleur_texte)
        elif self.survol:
            couleur_fond_actuelle = self.couleur_survol

        pygame.draw.rect(surface, couleur_fond_actuelle, self.rect, border_radius=self.border_radius)
        pygame.draw.rect(surface, C.DARK_GRID_LINE, self.rect, 2, border_radius=self.border_radius)

        if self.texte:
            texte_surface = self.font.render(self.texte, True, couleur_texte_actuelle)
            texte_rect = texte_surface.get_rect(center=self.rect.center)
            surface.blit(texte_surface, texte_rect)

    def verifier_clic(self, pos_souris):
        if self.enabled and self.rect.collidepoint(pos_souris):
            return self.action
        return None

    def verifier_survol(self, pos_souris):
        if self.enabled:
            self.survol = self.rect.collidepoint(pos_souris)
            return self.survol
        self.survol = False
        return False


class Slider:
    def __init__(self, x, y, largeur, hauteur_track, min_val, max_val, initial_val,
                 label="", label_font=None, valeur_font=None,
                 action_on_change=None):  # action_on_change est un ID ou une fonction callback
        self.rect_track = pygame.Rect(x, y, largeur, hauteur_track)
        self.min_val = float(min_val)
        self.max_val = float(max_val)
        self._current_val = float(initial_val)  # Stockage interne

        self.largeur_handle = 14  # Légèrement plus large
        self.hauteur_handle = hauteur_track * 2.8
        self.rect_handle = pygame.Rect(0, 0, self.largeur_handle, self.hauteur_handle)  # Initialisé dans update_pos
        self._update_handle_pos_from_value()  # Positionne la poignée

        self.label = label
        self.label_font = label_font if label_font else pygame.font.Font(C.POLICE_DEFAUT, C.TAILLE_POLICE_OPTIONS_LABEL)
        self.valeur_font = valeur_font if valeur_font else pygame.font.Font(C.POLICE_DEFAUT,
                                                                            C.TAILLE_POLICE_SLIDER_VALEUR)

        self.dragging = False
        self.survol_handle = False
        self.action_on_change = action_on_change  # Action à retourner/exécuter lors du changement

    @property
    def current_val(self):
        return self._current_val

    @current_val.setter
    def current_val(self, value):
        self._current_val = max(self.min_val, min(self.max_val, float(value)))
        self._update_handle_pos_from_value()

    def _update_handle_pos_from_value(self):
        val_range = self.max_val - self.min_val
        ratio = (self._current_val - self.min_val) / val_range if val_range != 0 else 0

        # La poignée se déplace sur la longueur du track
        handle_center_x = self.rect_track.x + ratio * self.rect_track.width

        self.rect_handle.centerx = handle_center_x
        self.rect_handle.centery = self.rect_track.centery

    def _update_value_from_mouse_x(self, mouse_x):
        relative_x = mouse_x - self.rect_track.x
        ratio = relative_x / self.rect_track.width
        ratio = max(0.0, min(1.0, ratio))  # Clamp [0, 1]

        new_val = self.min_val + ratio * (self.max_val - self.min_val)
        # Arrondir à 2 décimales pour éviter les fluctuations minimes dues aux flottants
        new_val = round(new_val, 2)

        if self._current_val != new_val:
            self._current_val = new_val
            self._update_handle_pos_from_value()
            return True  # Value changed
        return False  # No change

    def handle_event(self, event, mouse_pos):
        val_changed_by_event = False
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            # Clic sur le track ou la poignée pour commencer le drag ou sauter
            if self.rect_track.collidepoint(mouse_pos) or self.rect_handle.collidepoint(mouse_pos):
                self.dragging = True
                val_changed_by_event = self._update_value_from_mouse_x(mouse_pos[0])
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            if self.dragging:
                self.dragging = False
                # La valeur a déjà été mise à jour pendant le drag,
                # mais on confirme le changement ici.
                val_changed_by_event = True  # Indique que le drag est terminé
        elif event.type == pygame.MOUSEMOTION:
            self.survol_handle = self.rect_handle.collidepoint(mouse_pos)
            if self.dragging:
                val_changed_by_event = self._update_value_from_mouse_x(mouse_pos[0])

        if val_changed_by_event and self.action_on_change:
            # Retourne l'action et la nouvelle valeur pour que le jeu puisse la traiter
            return self.action_on_change, self.current_val
        return None, None  # Pas d'action ou pas de changement

    def dessiner(self, surface):
        # Label
        if self.label:
            label_surf = self.label_font.render(self.label, True, C.DARK_TEXT_PRIMARY)
            # Positionner le label à gauche du track
            label_y = self.rect_track.centery - label_surf.get_height() // 2
            surface.blit(label_surf, (self.rect_track.x - label_surf.get_width() - 10, label_y))

        # Track
        pygame.draw.rect(surface, C.SLIDER_TRACK_COLOR, self.rect_track, border_radius=self.rect_track.height // 2)

        # Handle
        handle_color_actual = C.SLIDER_HANDLE_COLOR
        if self.dragging or self.survol_handle:
            handle_color_actual = C.SLIDER_HANDLE_HOVER_COLOR
        pygame.draw.rect(surface, handle_color_actual, self.rect_handle, border_radius=3)

        # Valeur (ex: 75%)
        valeur_text = f"{int(self._current_val * 100)}%"
        valeur_surf = self.valeur_font.render(valeur_text, True, C.DARK_TEXT_SECONDARY)
        valeur_rect = valeur_surf.get_rect(midleft=(self.rect_track.right + 15, self.rect_track.centery))
        surface.blit(valeur_surf, valeur_rect)