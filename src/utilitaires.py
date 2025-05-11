import pygame
import os
import json
from . import constantes as C


def charger_image(nom_fichier_sans_extension, alpha=True):
    chemin_complet = os.path.join(C.CHEMIN_IMAGES, nom_fichier_sans_extension + ".png")
    try:
        image = pygame.image.load(chemin_complet)
        image = image.convert_alpha() if alpha else image.convert()
        return pygame.transform.scale(image, (C.TAILLE_CASE, C.TAILLE_CASE))
    except pygame.error as e:
        print(f"Erreur chargement image {chemin_complet}: {e}")
        surface = pygame.Surface((C.TAILLE_CASE, C.TAILLE_CASE))
        if nom_fichier_sans_extension == C.IMG_SOL:
            surface.fill(C.GRIS_CLAIR)
        elif nom_fichier_sans_extension == C.IMG_MUR:
            surface.fill(C.GRIS)
        else:
            surface.fill(C.ROUGE)
        return surface


def charger_images_sokoban():
    images = {
        C.IMG_MUR: charger_image(C.IMG_MUR),
        C.IMG_SOL: charger_image(C.IMG_SOL),
        C.IMG_CAISSE: charger_image(C.IMG_CAISSE),
        C.IMG_CIBLE: charger_image(C.IMG_CIBLE),
        C.IMG_JOUEUR: charger_image(C.IMG_JOUEUR),
        C.IMG_CAISSE_SUR_CIBLE: charger_image(C.IMG_CAISSE_SUR_CIBLE),
    }
    try:
        icon_img = pygame.image.load(os.path.join(C.CHEMIN_IMAGES, C.IMG_ICONE + ".png"))
        images[C.IMG_ICONE] = icon_img.convert_alpha()
    except pygame.error:
        images[C.IMG_ICONE] = None
        print(f"Avertissement: Icone du jeu '{C.IMG_ICONE}.png' introuvable.")
    return images


def charger_son(nom_fichier):
    chemin_complet = os.path.join(C.CHEMIN_SONS, nom_fichier)
    try:
        return pygame.mixer.Sound(chemin_complet)
    except pygame.error as e:
        print(f"Erreur chargement son {chemin_complet}: {e}")
        return None


def charger_sons_sokoban():
    # Le volume sera appliqué après chargement par la classe Jeu
    sons = {
        "deplacement": charger_son(C.SON_DEPLACEMENT),
        "pousse": charger_son(C.SON_POUSSE),
        "victoire": charger_son(C.SON_VICTOIRE),
    }
    return sons


def sauvegarder_progression(donnees_sauvegarde):
    if not os.path.exists(C.CHEMIN_SAUVEGARDES):
        try:
            os.makedirs(C.CHEMIN_SAUVEGARDES)
        except OSError as e:
            print(f"Erreur création dossier sauvegardes {C.CHEMIN_SAUVEGARDES}: {e}")
            return

    chemin_fichier = os.path.join(C.CHEMIN_SAUVEGARDES, "progression.json")
    try:
        with open(chemin_fichier, 'w') as f:
            json.dump(donnees_sauvegarde, f, indent=4, sort_keys=True)
        # print(f"Progression sauvegardée dans {chemin_fichier}") # Peut devenir verbeux
    except IOError as e:
        print(f"Erreur sauvegarde progression: {e}")


def charger_progression():
    chemin_fichier = os.path.join(C.CHEMIN_SAUVEGARDES, "progression.json")
    valeur_defaut = {
        "joueur": {"nom": "Joueur1", "niveaux_completes": []},
        "scores": {},
        "options_jeu": {  # Nouvelle section pour les options
            "volume_son": 1.0,
            "textures_active": True
        }
    }
    if os.path.exists(chemin_fichier):
        try:
            with open(chemin_fichier, 'r') as f:
                data = json.load(f)

                # Fusionner avec les valeurs par défaut pour assurer que toutes les clés existent
                if "joueur" not in data:
                    data["joueur"] = valeur_defaut["joueur"]
                else:
                    if "nom" not in data["joueur"]: data["joueur"]["nom"] = valeur_defaut["joueur"]["nom"]
                    if "niveaux_completes" not in data["joueur"]: data["joueur"]["niveaux_completes"] = []

                if "scores" not in data: data["scores"] = valeur_defaut["scores"]

                if "options_jeu" not in data:
                    data["options_jeu"] = valeur_defaut["options_jeu"]
                else:
                    if "volume_son" not in data["options_jeu"]:
                        data["options_jeu"]["volume_son"] = valeur_defaut["options_jeu"]["volume_son"]
                    if "textures_active" not in data["options_jeu"]:
                        data["options_jeu"]["textures_active"] = valeur_defaut["options_jeu"]["textures_active"]

                # print(f"Progression chargée depuis {chemin_fichier}")
                return data
        except (IOError, json.JSONDecodeError) as e:
            print(f"Erreur chargement progression ({chemin_fichier}): {e}. Utilisation des valeurs par défaut.")
    # else:
    # print(f"Fichier de progression non trouvé. Utilisation des valeurs par défaut.")
    return valeur_defaut


def sauvegarder_niveau_personnalise_en_fichier(nom_niveau, contenu_niveau_str):
    if not os.path.exists(C.CHEMIN_NIVEAUX_PERSO):
        try:
            os.makedirs(C.CHEMIN_NIVEAUX_PERSO)
        except OSError as e:
            print(f"Erreur création dossier niveaux perso {C.CHEMIN_NIVEAUX_PERSO}: {e}")
            return False

    nom_fichier_base = "".join(c if c.isalnum() or c in [' ', '-', '_'] else '' for c in nom_niveau).strip()
    if not nom_fichier_base: nom_fichier_base = "niveau_perso_sans_nom"
    nom_fichier_base = nom_fichier_base.replace(' ', '_')
    nom_fichier = nom_fichier_base + ".txt"
    chemin_complet = os.path.join(C.CHEMIN_NIVEAUX_PERSO, nom_fichier)

    try:
        with open(chemin_complet, 'w') as f:
            f.write(contenu_niveau_str)
        print(f"Niveau personnalisé '{nom_niveau}' sauvegardé: '{chemin_complet}'")
        return True
    except IOError as e:
        print(f"Erreur sauvegarde niveau personnalisé '{nom_niveau}': {e}")
        return False


def obtenir_liste_niveaux_defaut():
    chemins_complets = []
    if not os.path.exists(C.CHEMIN_NIVEAUX_DEFAUT):
        print(f"AVERTISSEMENT: Dossier des niveaux par défaut introuvable: {C.CHEMIN_NIVEAUX_DEFAUT}")
        return chemins_complets

    try:
        fichiers = [f for f in os.listdir(C.CHEMIN_NIVEAUX_DEFAUT)
                    if os.path.isfile(os.path.join(C.CHEMIN_NIVEAUX_DEFAUT, f))
                    and f.endswith(".txt")]
        try:
            fichiers.sort(key=lambda x: int(x.lower().replace("map", "").replace(".txt", "")))
        except ValueError:
            fichiers.sort()

        return [os.path.join(C.CHEMIN_NIVEAUX_DEFAUT, f) for f in fichiers]
    except Exception as e:
        print(f"Erreur lors du listage des niveaux par défaut dans {C.CHEMIN_NIVEAUX_DEFAUT}: {e}")
        return []


def obtenir_chemins_niveaux_personnalises():
    chemins_niveaux = []
    if not os.path.exists(C.CHEMIN_NIVEAUX_PERSO):
        return chemins_niveaux

    try:
        for nom_fichier in os.listdir(C.CHEMIN_NIVEAUX_PERSO):
            if nom_fichier.endswith(".txt") and os.path.isfile(os.path.join(C.CHEMIN_NIVEAUX_PERSO, nom_fichier)):
                chemins_niveaux.append(os.path.join(C.CHEMIN_NIVEAUX_PERSO, nom_fichier))
        chemins_niveaux.sort()
        return chemins_niveaux
    except Exception as e:
        print(f"Erreur lors du listage des niveaux personnalisés dans {C.CHEMIN_NIVEAUX_PERSO}: {e}")
        return []