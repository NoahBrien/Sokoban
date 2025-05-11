import pygame
from src import jeu, constantes as C


def main():
    pygame.init()
    pygame.mixer.init()  # S'assurer que le mixer est initialisé

    # Initialiser le module de polices de Pygame si ce n'est pas déjà fait ailleurs (ex: Jeu.__init__)
    # pygame.font.init() # Normalement pygame.init() le fait.

    mon_jeu = jeu.Jeu()
    mon_jeu.executer()

    pygame.quit()


if __name__ == "__main__":
    main()