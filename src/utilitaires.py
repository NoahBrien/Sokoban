import pygame
import os
import json
from . import constantes as C

pygame.mixer.init()


def charger_image(nom_fichier, alpha=True):
    chemin_complet = os.path.join(C.CHEMIN_IMAGES, nom_fichier + ".png")
    try:
        image = pygame.image.load(chemin_complet)
        if alpha:
            image = image.convert_alpha()
        else:
            image = image.convert()
        return pygame.transform.scale(image, (C.TAILLE_CASE, C.TAILLE_CASE))
    except pygame.error as e:
        print(f"Erreur chargement image {chemin_complet}: {e}")
        surface = pygame.Surface((C.TAILLE_CASE, C.TAILLE_CASE))
        surface.fill(C.ROUGE)
        return surface


def charger_images_sokoban():
    images = {
        C.MUR: charger_image(C.IMG_MUR),
        C.SOL: charger_image(C.IMG_SOL),
        C.CAISSE: charger_image(C.IMG_CAISSE),
        C.CIBLE: charger_image(C.IMG_CIBLE),
        C.JOUEUR: charger_image(C.IMG_JOUEUR),
        C.CAISSE_SUR_CIBLE: charger_image(C.IMG_CAISSE_SUR_CIBLE),
    }
    try:
        images['icon'] = pygame.image.load(os.path.join(C.CHEMIN_IMAGES, C.IMG_ICONE + ".png")).convert_alpha()
    except pygame.error:
        images['icon'] = None
        print(f"Avertissement: Icone {C.IMG_ICONE}.png introuvable.")
    return images


def charger_son(nom_fichier):
    chemin_complet = os.path.join(C.CHEMIN_SONS, nom_fichier)
    try:
        return pygame.mixer.Sound(chemin_complet)
    except pygame.error as e:
        print(f"Erreur chargement son {chemin_complet}: {e}")
        return None


def charger_sons_sokoban():
    sons = {
        "deplacement": charger_son(C.SON_DEPLACEMENT),
        "pousse": charger_son(C.SON_POUSSE),
        "victoire": charger_son(C.SON_VICTOIRE),
    }
    return sons


def sauvegarder_progression(donnees_sauvegarde):
    if not os.path.exists(C.CHEMIN_SAUVEGARDES):
        os.makedirs(C.CHEMIN_SAUVEGARDES)
    chemin_fichier = os.path.join(C.CHEMIN_SAUVEGARDES, "progression.json")
    try:
        with open(chemin_fichier, 'w') as f:
            json.dump(donnees_sauvegarde, f, indent=4)
    except IOError as e:
        print(f"Erreur sauvegarde progression: {e}")


def charger_progression():
    chemin_fichier = os.path.join(C.CHEMIN_SAUVEGARDES, "progression.json")
    valeur_defaut = {"joueur": {"nom": "Joueur1", "niveaux_completes": []}, "scores": {}}
    if os.path.exists(chemin_fichier):
        try:
            with open(chemin_fichier, 'r') as f:
                data = json.load(f)
                # S'assurer que les clés attendues existent, sinon utiliser les valeurs par défaut
                if "joueur" not in data: data["joueur"] = valeur_defaut["joueur"]
                if "scores" not in data: data["scores"] = valeur_defaut["scores"]
                # La clé "niveaux_personnalises" n'est plus stockée ici
                return data
        except (IOError, json.JSONDecodeError) as e:
            print(f"Erreur chargement progression: {e}. Nouvelle sauvegarde créée.")
    return valeur_defaut  # Retourne la structure sans niveaux_personnalises


def sauvegarder_niveau_personnalise_en_fichier(nom_niveau, contenu_niveau_str):
    """Sauvegarde un niveau personnalisé dans son propre fichier .txt."""
    if not os.path.exists(C.CHEMIN_NIVEAUX_PERSO):
        os.makedirs(C.CHEMIN_NIVEAUX_PERSO)

    # Nettoyer le nom du niveau pour l'utiliser comme nom de fichier
    nom_fichier_base = "".join(c if c.isalnum() or c in [' ', '-', '_'] else '' for c in nom_niveau).rstrip()
    if not nom_fichier_base:
        nom_fichier_base = "niveau_sans_nom"
    nom_fichier = nom_fichier_base + ".txt"

    chemin_complet = os.path.join(C.CHEMIN_NIVEAUX_PERSO, nom_fichier)

    try:
        with open(chemin_complet, 'w') as f:
            f.write(contenu_niveau_str)
        print(f"Niveau personnalisé '{nom_niveau}' sauvegardé dans '{chemin_complet}'")
        return True
    except IOError as e:
        print(f"Erreur lors de la sauvegarde du niveau personnalisé '{nom_niveau}': {e}")
        return False


def obtenir_liste_niveaux_defaut():
    try:
        fichiers = [f for f in os.listdir(C.CHEMIN_NIVEAUX_DEFAUT) if f.startswith("map") and f.endswith(".txt")]
        fichiers.sort(key=lambda x: int(x.replace("map", "").replace(".txt", "")))
        return [os.path.join(C.CHEMIN_NIVEAUX_DEFAUT, f) for f in fichiers]
    except FileNotFoundError:
        print(f"Dossier niveaux par défaut {C.CHEMIN_NIVEAUX_DEFAUT} introuvable.")
        return []


def obtenir_chemins_niveaux_personnalises():
    """Retourne une liste de chemins vers les fichiers .txt des niveaux personnalisés."""
    chemins_niveaux = []
    if not os.path.exists(C.CHEMIN_NIVEAUX_PERSO):
        return chemins_niveaux  # Retourne une liste vide si le dossier n'existe pas

    try:
        for nom_fichier in os.listdir(C.CHEMIN_NIVEAUX_PERSO):
            if nom_fichier.endswith(".txt"):
                chemins_niveaux.append(os.path.join(C.CHEMIN_NIVEAUX_PERSO, nom_fichier))
        chemins_niveaux.sort()  # Trier alphabétiquement par nom de fichier
        return chemins_niveaux
    except FileNotFoundError:  # Le dossier pourrait être supprimé entre le os.path.exists et os.listdir
        print(f"Dossier niveaux personnalisés {C.CHEMIN_NIVEAUX_PERSO} introuvable lors du listage.")
        return []