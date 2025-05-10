# Dimensions
TAILLE_CASE = 40
LARGEUR_FENETRE_JEU = 800
HAUTEUR_FENETRE_JEU = 600
LARGEUR_MENU = 700 # Un peu plus large pour le menu sélection
HAUTEUR_MENU = 550
FPS = 60

# --- Couleurs Thème Sombre ---
DARK_BACKGROUND = (30, 30, 30)
DARK_SURFACE = (50, 50, 50) # Pour les boutons ou éléments un peu plus clairs
DARK_BUTTON_BG = (60, 60, 60)
DARK_BUTTON_HOVER_BG = (90, 90, 90)
DARK_TEXT_PRIMARY = (220, 220, 220)
DARK_TEXT_SECONDARY = (180, 180, 180)
DARK_ACCENT_GOOD = (0, 180, 100)  # Vert pour la victoire, etc.
DARK_ACCENT_INFO = (0, 150, 200)  # Cyan/Bleu clair pour infos
DARK_ACCENT_WARN = (200, 150, 0)  # Orange/Jaune pour avertissements ou sélection
DARK_GRID_LINE = (80, 80, 80)

# Couleurs originales (gardées pour référence ou éléments spécifiques du jeu si besoin)
NOIR = (0, 0, 0)
BLANC = (255, 255, 255)
GRIS = (100, 100, 100) # Utilisé par l'éditeur pour certains fallback
GRIS_CLAIR = (200, 200, 200) # Utilisé par l'éditeur
BLEU = (0, 0, 255)
ROUGE = (255, 0, 0)
VERT = (0, 255, 0)
JAUNE = (255, 255, 0) # Toujours utile pour le HUD
ROSE = (255, 182, 193) # Utilisé par l'éditeur
MARRON = (139, 69, 19) # Utilisé par l'éditeur

# États du jeu
ETAT_MENU_PRINCIPAL = "menu_principal"
ETAT_SELECTION_NIVEAU = "selection_niveau"
ETAT_JEU = "jeu"
ETAT_EDITEUR = "editeur"
ETAT_VISUALISATION_SOLVEUR = "visualisation_solveur"
ETAT_SCORES = "scores"
ETAT_QUITTER = "quitter"

# Chemins des ressources
CHEMIN_IMAGES = "assets/images/"
CHEMIN_SONS = "assets/sons/"
CHEMIN_NIVEAUX_DEFAUT = "niveaux/"
CHEMIN_NIVEAUX_PERSO = "niveaux/personnalises/"
CHEMIN_SAUVEGARDES = "sauvegardes/"

# Éléments du niveau
MUR = '#'
SOL = ' '
CAISSE = '$'
CIBLE = '.'
JOUEUR = '@'
CAISSE_SUR_CIBLE = '*'
JOUEUR_SUR_CIBLE = '+'

# Noms des images
IMG_MUR = "wall"
IMG_SOL = "floor"
IMG_CAISSE = "box"
IMG_CIBLE = "goal"
IMG_JOUEUR = "player"
IMG_CAISSE_SUR_CIBLE = "box_ok"
IMG_ICONE = "icon"

# Sons
SON_DEPLACEMENT = "deplacement.wav"
SON_POUSSE = "pousse.wav"
SON_VICTOIRE = "victoire.wav"

# Textes UI
POLICE_DEFAUT = None # Utilise la police système par défaut de Pygame
TAILLE_POLICE_MENU = 28 # Ajusté
TAILLE_POLICE_JEU = 22  # Ajusté
TAILLE_POLICE_TITRE = 40

# Limites pour solveurs
PROFONDEUR_MAX_BACKTRACKING = 30