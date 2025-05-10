import pygame
import os
import json
from . import constantes as C

pygame.mixer.init() # Initialiser le mixer pour les sons

def charger_image(nom_fichier, alpha=True):
    """Charge une image depuis le dossier des images, avec gestion de la transparence."""
    chemin_complet = os.path.join(C.CHEMIN_IMAGES, nom_fichier + ".png")
    try:
        image = pygame.image.load(chemin_complet)
        if alpha:
            image = image.convert_alpha()
        else:
            image = image.convert()
        return pygame.transform.scale(image, (C.TAILLE_CASE, C.TAILLE_CASE))
    except pygame.error as e:
        print(f"Erreur lors du chargement de l'image {chemin_complet}: {e}")
        surface = pygame.Surface((C.TAILLE_CASE, C.TAILLE_CASE))
        surface.fill(C.ROUGE) # Image de remplacement en cas d'erreur
        return surface

def charger_images_sokoban():
    """Charge toutes les images nécessaires pour le jeu Sokoban."""
    images = {
        C.MUR: charger_image(C.IMG_MUR),
        C.SOL: charger_image(C.IMG_SOL),
        C.CAISSE: charger_image(C.IMG_CAISSE),
        C.CIBLE: charger_image(C.IMG_CIBLE),
        C.JOUEUR: charger_image(C.IMG_JOUEUR),
        C.CAISSE_SUR_CIBLE: charger_image(C.IMG_CAISSE_SUR_CIBLE),
        # JOUEUR_SUR_CIBLE n'a pas d'image distincte, on superpose joueur et cible
    }
    # Pour l'icône, ne pas redimensionner à TAILLE_CASE
    try:
        images['icon'] = pygame.image.load(os.path.join(C.CHEMIN_IMAGES, C.IMG_ICONE + ".png")).convert_alpha()
    except pygame.error:
        images['icon'] = None # Gérer l'absence d'icône
        print(f"Avertissement: Impossible de charger l'icône {C.IMG_ICONE}.png")
    return images

def charger_son(nom_fichier):
    """Charge un son depuis le dossier des sons."""
    chemin_complet = os.path.join(C.CHEMIN_SONS, nom_fichier)
    try:
        return pygame.mixer.Sound(chemin_complet)
    except pygame.error as e:
        print(f"Erreur lors du chargement du son {chemin_complet}: {e}")
        return None

def charger_sons_sokoban():
    """Charge tous les sons nécessaires pour le jeu."""
    sons = {
        "deplacement": charger_son(C.SON_DEPLACEMENT),
        "pousse": charger_son(C.SON_POUSSE),
        "victoire": charger_son(C.SON_VICTOIRE),
    }
    return sons

def sauvegarder_progression(donnees_sauvegarde):
    """Sauvegarde la progression du joueur et les scores au format JSON."""
    if not os.path.exists(C.CHEMIN_SAUVEGARDES):
        os.makedirs(C.CHEMIN_SAUVEGARDES)
    chemin_fichier = os.path.join(C.CHEMIN_SAUVEGARDES, "progression.json")
    try:
        with open(chemin_fichier, 'w') as f:
            json.dump(donnees_sauvegarde, f, indent=4)
    except IOError as e:
        print(f"Erreur lors de la sauvegarde de la progression: {e}")

def charger_progression():
    """Charge la progression du joueur et les scores depuis un fichier JSON."""
    chemin_fichier = os.path.join(C.CHEMIN_SAUVEGARDES, "progression.json")
    if os.path.exists(chemin_fichier):
        try:
            with open(chemin_fichier, 'r') as f:
                return json.load(f)
        except (IOError, json.JSONDecodeError) as e:
            print(f"Erreur lors du chargement de la progression: {e}. Création d'une nouvelle sauvegarde.")
    return {"joueur": {"nom": "Joueur1", "niveaux_completes": []}, "scores": {}, "niveaux_personnalises": []}


def sauvegarder_niveau_personnalise(nom_niveau, contenu_niveau_str):
    """Sauvegarde un niveau personnalisé."""
    progression = charger_progression()
    # Vérifier si le nom existe déjà pour éviter les doublons ou permettre l'écrasement
    niveau_existant = next((n for n in progression.get("niveaux_personnalises", []) if n["nom"] == nom_niveau), None)
    if niveau_existant:
        niveau_existant["contenu"] = contenu_niveau_str
    else:
        progression.setdefault("niveaux_personnalises", []).append({"nom": nom_niveau, "contenu": contenu_niveau_str})
    sauvegarder_progression(progression)

def obtenir_liste_niveaux_defaut():
    """Retourne la liste des fichiers de niveaux par défaut."""
    try:
        fichiers = [f for f in os.listdir(C.CHEMIN_NIVEAUX_DEFAUT) if f.startswith("map") and f.endswith(".txt")]
        # Trie les niveaux, par exemple map0.txt, map1.txt, etc.
        fichiers.sort(key=lambda x: int(x.replace("map", "").replace(".txt", "")))
        return [os.path.join(C.CHEMIN_NIVEAUX_DEFAUT, f) for f in fichiers]
    except FileNotFoundError:
        print(f"Le dossier des niveaux par défaut {C.CHEMIN_NIVEAUX_DEFAUT} est introuvable.")
        return []

def obtenir_niveaux_personnalises():
    """Retourne une liste de dictionnaires {'nom': ..., 'contenu': ...} pour les niveaux personnalisés."""
    progression = charger_progression()
    return progression.get("niveaux_personnalises", [])