import pygame
from src import jeu

def main():
    """Initialise Pygame, crée l'objet Jeu et lance la boucle principale."""
    pygame.init()
    pygame.mixer.init()
    mon_jeu = jeu.Jeu()
    mon_jeu.executer()
    pygame.quit()

if __name__ == "__main__":
    main()