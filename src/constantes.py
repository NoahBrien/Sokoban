TAILLE_CASE = 40
LARGEUR_FENETRE_JEU = 800
HAUTEUR_FENETRE_JEU = 600
LARGEUR_MENU = 700 # Minimum pour affichage correct
HAUTEUR_MENU = 600 # Augmenté pour plus d'espace dans les options
FPS = 60

DARK_BACKGROUND = (30, 30, 30)
DARK_SURFACE = (50, 50, 50)
DARK_BUTTON_BG = (60, 60, 60)
DARK_BUTTON_HOVER_BG = (90, 90, 90)
DARK_TEXT_PRIMARY = (220, 220, 220)
DARK_TEXT_SECONDARY = (180, 180, 180)
DARK_ACCENT_GOOD = (0, 180, 100)
DARK_ACCENT_INFO = (0, 150, 200)
DARK_ACCENT_WARN = (200, 150, 0)
DARK_GRID_LINE = (80, 80, 80)
DARK_HINT_COLOR = (255, 100, 255)
DARK_DEADLOCK_WARN_COLOR = (255, 0, 0)

# Couleurs pour le slider
SLIDER_TRACK_COLOR = (45, 45, 45)
SLIDER_HANDLE_COLOR = (110, 110, 110)
SLIDER_HANDLE_HOVER_COLOR = (140, 140, 140)

# Couleurs de fallback pour le mode sans textures
FALLBACK_MUR = (80, 80, 80)
FALLBACK_SOL = (180, 180, 180)
FALLBACK_CIBLE = (255, 223, 186) # Pêche clair
FALLBACK_CAISSE = (160, 82, 45) # Sienne
FALLBACK_CAISSE_SUR_CIBLE = (139, 69, 19) # Marron plus foncé
FALLBACK_JOUEUR = (65, 105, 225) # Bleu roi

NOIR = (0, 0, 0)
BLANC = (255, 255, 255)
GRIS = (100, 100, 100) # Utilisé par Case si C.IMG_MUR non trouvé (même avec textures)
GRIS_CLAIR = (200, 200, 200) # Utilisé par Case si C.IMG_SOL non trouvé
BLEU = (0, 0, 255)
ROUGE = (255, 0, 0)
VERT = (0, 255, 0)
JAUNE = (255, 255, 0)
ROSE = (255, 182, 193) # Utilisé par Case si C.IMG_CIBLE non trouvé
MARRON = (139, 69, 19)

ETAT_MENU_PRINCIPAL = "menu_principal"
ETAT_SELECTION_NIVEAU = "selection_niveau"
ETAT_JEU = "jeu"
ETAT_EDITEUR = "editeur"
ETAT_VISUALISATION_SOLVEUR = "visualisation_solveur"
ETAT_SCORES = "scores"
ETAT_OPTIONS = "options"
ETAT_QUITTER = "quitter"

CHEMIN_IMAGES = "assets/images/"
CHEMIN_SONS = "assets/sons/"
CHEMIN_NIVEAUX_DEFAUT = "niveaux/"
CHEMIN_NIVEAUX_PERSO = "niveaux/personnalises/"
CHEMIN_SAUVEGARDES = "sauvegardes/"

MUR = '#'
SOL = ' '
CAISSE = '$'
CIBLE = '.'
JOUEUR = '@'
CAISSE_SUR_CIBLE = '*'
JOUEUR_SUR_CIBLE = '+'

IMG_MUR = "wall"
IMG_SOL = "floor"
IMG_CAISSE = "box"
IMG_CIBLE = "goal"
IMG_JOUEUR = "player"
IMG_CAISSE_SUR_CIBLE = "box_ok"
IMG_ICONE = "icon"

SON_DEPLACEMENT = "deplacement.wav"
SON_POUSSE = "pousse.wav"
SON_VICTOIRE = "victoire.wav"

POLICE_DEFAUT = None
TAILLE_POLICE_MENU = 28
TAILLE_POLICE_JEU = 22
TAILLE_POLICE_TITRE = 40
TAILLE_POLICE_OPTIONS_LABEL = 24
TAILLE_POLICE_SLIDER_VALEUR = 18


PROFONDEUR_MAX_BACKTRACKING = 30