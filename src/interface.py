import pygame
import os
from . import constantes as C
from . import utilitaires
from . import editeur
from . import solveurs  # Non utilisé directement ici, mais bon à garder si des infos solveur passent
from .ui_elements import Bouton, Slider  # Ajout de Slider


class InterfaceGraphique:
    def __init__(self, largeur, hauteur, jeu_principal):
        self.largeur = largeur;
        self.hauteur = hauteur
        self.fenetre = pygame.display.set_mode((largeur, hauteur))
        pygame.display.set_caption("Sokoban Deluxe")  # Titre mis à jour
        self.images = utilitaires.charger_images_sokoban()
        if self.images.get(C.IMG_ICONE): pygame.display.set_icon(self.images[C.IMG_ICONE])

        pygame.font.init()
        self.font_titre = pygame.font.Font(C.POLICE_DEFAUT, C.TAILLE_POLICE_TITRE)
        self.font_menu = pygame.font.Font(C.POLICE_DEFAUT, C.TAILLE_POLICE_MENU)
        self.font_jeu = pygame.font.Font(C.POLICE_DEFAUT, C.TAILLE_POLICE_JEU)
        self.font_options_label = pygame.font.Font(C.POLICE_DEFAUT, C.TAILLE_POLICE_OPTIONS_LABEL)
        self.font_slider_valeur = pygame.font.Font(C.POLICE_DEFAUT, C.TAILLE_POLICE_SLIDER_VALEUR)

        self.jeu_principal = jeu_principal

        self.boutons_menu = [];
        self.boutons_selection_niveau = []
        self.scroll_offset_selection_niveau = 0;
        self.hauteur_contenu_selection_niveau = 0
        self.btn_retour_sel_niveau = None  # Pour la sélection de niveau

        self.message_victoire_affiche_temps = 0;
        self.editeur_instance = None

        # Éléments pour l'écran des Options
        self.elements_options = {  # Dictionnaire pour stocker boutons et sliders des options
            "boutons": [],
            "sliders": {}  # Keyed by action string, e.g., "volume_slider"
        }
        self.bouton_retour_options_scores = None  # Bouton commun pour quitter Scores/Options

        self.scroll_offset_scores = 0;
        self.hauteur_contenu_scores = 0
        self.scrollbar_scores_rect = None;
        self.scrollbar_scores_poignee_rect = None
        self.dragging_scrollbar_scores = False

    def _creer_boutons_menu_principal(self):
        self.boutons_menu = []
        btn_w, btn_h, espace, nb_btns = 300, 55, 20, 5  # Espace réduit, 5 boutons
        x_c = self.largeur // 2 - btn_w // 2
        y_tot_b = nb_btns * btn_h + (nb_btns - 1) * espace
        y_start = self.hauteur // 2 - y_tot_b // 2 + 20
        actions = [
            ("Nouvelle Partie", C.ETAT_SELECTION_NIVEAU), ("Éditeur de Niveaux", C.ETAT_EDITEUR),
            ("Scores", C.ETAT_SCORES), ("Options", C.ETAT_OPTIONS), ("Quitter", C.ETAT_QUITTER)
        ]
        for i, (txt, act_id) in enumerate(actions):
            self.boutons_menu.append(
                Bouton(x_c, y_start + i * (btn_h + espace), btn_w, btn_h, txt, font=self.font_menu, action=act_id))

    def afficher_menu_principal(self):
        self.fenetre.fill(C.DARK_BACKGROUND)
        tit_s = self.font_titre.render("Sokoban Deluxe", True, C.DARK_TEXT_PRIMARY)
        tit_r = tit_s.get_rect(center=(self.largeur // 2, self.hauteur // 6));
        self.fenetre.blit(tit_s, tit_r)
        if not self.boutons_menu: self._creer_boutons_menu_principal()
        mouse_pos = pygame.mouse.get_pos()
        for btn in self.boutons_menu: btn.verifier_survol(mouse_pos); btn.dessiner(self.fenetre)
        pygame.display.flip()

    def gerer_clic_menu_principal(self, p_s):
        return next((b.verifier_clic(p_s) for b in self.boutons_menu if b.verifier_clic(p_s)), None)

    def _preparer_boutons_selection_niveau(self, chemins_niveaux_defaut, chemins_niveaux_perso):
        self.boutons_selection_niveau = [];
        tous_n_s = [];
        idx_g_c = 0
        for i, path in enumerate(chemins_niveaux_defaut):
            nom_b = os.path.basename(path);
            nom_a = nom_b.replace(".txt", f" (Défaut {i + 1})")
            spec = {"type_charge": "fichier_chemin", "data": path, "index_global": idx_g_c,
                    "nom_affiche": nom_b.replace(".txt", "")}
            tous_n_s.append({"nom_pour_bouton": nom_a, "action_spec": spec});
            idx_g_c += 1
        for i, path in enumerate(chemins_niveaux_perso):
            nom_b = os.path.basename(path);
            nom_a = nom_b.replace(".txt", f" (Perso {i + 1})")
            spec = {"type_charge": "fichier_chemin", "data": path, "index_global": idx_g_c,
                    "nom_affiche": nom_b.replace(".txt", "")}
            tous_n_s.append({"nom_pour_bouton": nom_a, "action_spec": spec});
            idx_g_c += 1
        btn_w, btn_h, esp_v, marge_liste = 300, 45, 15, 50
        largeur_dispo = self.largeur - 2 * marge_liste;
        nb_cols = max(1, largeur_dispo // (btn_w + esp_v))
        x_pos_cols = [];
        largeur_tot_cols = nb_cols * btn_w + (nb_cols - 1) * esp_v;
        x_debut_tot = (self.largeur - largeur_tot_cols) // 2
        for i in range(nb_cols): x_pos_cols.append(x_debut_tot + i * (btn_w + esp_v))
        y_p_d_rel = 0;
        self.hauteur_contenu_selection_niveau = 0
        for i, niv_spec_b in enumerate(tous_n_s):
            col_i = i % nb_cols;
            row_i = i // nb_cols;
            curr_x = x_pos_cols[col_i];
            curr_y_rel = y_p_d_rel + row_i * (btn_h + esp_v)
            self.boutons_selection_niveau.append(
                Bouton(curr_x, curr_y_rel, btn_w, btn_h, niv_spec_b["nom_pour_bouton"], font=self.font_menu,
                       action=niv_spec_b["action_spec"]))
            if curr_y_rel + btn_h > self.hauteur_contenu_selection_niveau: self.hauteur_contenu_selection_niveau = curr_y_rel + btn_h
        if self.boutons_selection_niveau: self.hauteur_contenu_selection_niveau += esp_v
        self.btn_retour_sel_niveau = Bouton(self.largeur // 2 - 100, self.hauteur - 70, 200, 50, "Retour Menu",
                                            font=self.font_menu, action="retour_menu")

    def afficher_selection_niveau(self, chemins_niveaux_defaut, chemins_niveaux_perso):
        self.fenetre.fill(C.DARK_BACKGROUND)
        tit_s = self.font_titre.render("Sélectionnez un Niveau", True, C.DARK_TEXT_PRIMARY)
        tit_r = tit_s.get_rect(center=(self.largeur // 2, 60));
        self.fenetre.blit(tit_s, tit_r)
        if not self.boutons_selection_niveau or not self.btn_retour_sel_niveau:
            self._preparer_boutons_selection_niveau(chemins_niveaux_defaut, chemins_niveaux_perso)
        y_z_s_d = 120;
        h_v_z_s = self.hauteur - y_z_s_d - 80
        surf_scroll = pygame.Surface((self.largeur, self.hauteur_contenu_selection_niveau));
        surf_scroll.fill(C.DARK_BACKGROUND)
        mouse_pos_abs = pygame.mouse.get_pos()
        for btn in self.boutons_selection_niveau:
            rect_btn_ecran = pygame.Rect(btn.rect.x, btn.rect.y - self.scroll_offset_selection_niveau + y_z_s_d,
                                         btn.rect.width, btn.rect.height)
            zone_vis_rect = pygame.Rect(0, y_z_s_d, self.largeur, h_v_z_s)
            btn.survol = rect_btn_ecran.collidepoint(mouse_pos_abs) and zone_vis_rect.collidepoint(mouse_pos_abs)
            btn.dessiner(surf_scroll)
        self.fenetre.blit(surf_scroll, (0, y_z_s_d), (0, self.scroll_offset_selection_niveau, self.largeur, h_v_z_s))
        if self.btn_retour_sel_niveau: self.btn_retour_sel_niveau.verifier_survol(
            mouse_pos_abs); self.btn_retour_sel_niveau.dessiner(self.fenetre)
        pygame.display.flip()

    def gerer_clic_selection_niveau(self, p_s_a, ev_b):
        y_z_s_d = 120;
        h_v_z_s = self.hauteur - y_z_s_d - 80
        if ev_b == 4:
            self.scroll_offset_selection_niveau = max(0, self.scroll_offset_selection_niveau - 30); return None
        elif ev_b == 5:
            max_s = max(0, self.hauteur_contenu_selection_niveau - h_v_z_s); self.scroll_offset_selection_niveau = min(
                max_s, self.scroll_offset_selection_niveau + 30); return None
        if ev_b == 1:
            if self.btn_retour_sel_niveau and self.btn_retour_sel_niveau.verifier_clic(p_s_a):
                self.boutons_selection_niveau = [];
                self.scroll_offset_selection_niveau = 0;
                self.btn_retour_sel_niveau = None;
                return C.ETAT_MENU_PRINCIPAL
            zone_vis_rect = pygame.Rect(0, y_z_s_d, self.largeur, h_v_z_s)
            if zone_vis_rect.collidepoint(p_s_a):
                s_x_rel, s_y_rel = p_s_a[0], p_s_a[1] - y_z_s_d + self.scroll_offset_selection_niveau
                for btn in self.boutons_selection_niveau:
                    if btn.rect.collidepoint((s_x_rel, s_y_rel)):
                        action = btn.action
                        if isinstance(action, dict):
                            self.jeu_principal.charger_niveau_par_specification(action)
                            self.boutons_selection_niveau = [];
                            self.scroll_offset_selection_niveau = 0;
                            self.btn_retour_sel_niveau = None;
                            return C.ETAT_JEU
        return None

    def afficher_ecran_jeu(self, niv_act, nom_niv_affiche, nb_mvt, tps_ec_s, textures_active, hint_pos=None,
                           hint_msg="", deadlock_msg=""):  # Ajout textures_active
        if not niv_act: return
        niv_l_px, niv_h_px = niv_act.largeur * C.TAILLE_CASE, niv_act.hauteur * C.TAILLE_CASE
        min_marge_x, min_marge_y, hud_bas_h = 50, 50, 50
        zone_jeu_dispo_l = self.largeur - 2 * min_marge_x;
        zone_jeu_dispo_h = self.hauteur - min_marge_y - hud_bas_h
        off_x_g = min_marge_x + max(0, (zone_jeu_dispo_l - niv_l_px) // 2);
        off_y_g = min_marge_y + max(0, (zone_jeu_dispo_h - niv_h_px) // 2)

        surf_jeu = pygame.Surface((niv_l_px, niv_h_px));
        surf_jeu.fill(C.DARK_BACKGROUND)  # Remplir la surface de jeu
        niv_act.dessiner(surf_jeu, self.images, textures_active)  # Passer textures_active

        if hint_pos:
            h_x, h_y = hint_pos;
            rect_hint = pygame.Rect(h_x * C.TAILLE_CASE + 3, h_y * C.TAILLE_CASE + 3, C.TAILLE_CASE - 6,
                                    C.TAILLE_CASE - 6)
            pygame.draw.rect(surf_jeu, C.DARK_HINT_COLOR, rect_hint, 3, border_radius=5)

        self.fenetre.fill(C.DARK_BACKGROUND);
        self.fenetre.blit(surf_jeu, (off_x_g, off_y_g))
        y_hud1, y_hud2 = 15, 40
        nom_surf = self.font_jeu.render(f"Niveau: {nom_niv_affiche}", True, C.DARK_TEXT_PRIMARY);
        self.fenetre.blit(nom_surf, (20, y_hud1))
        mvt_surf = self.font_jeu.render(f"Mouvements: {nb_mvt}", True, C.DARK_TEXT_PRIMARY)
        x_mvt = nom_surf.get_width() + 40;
        y_mvt_final = y_hud1
        if x_mvt + mvt_surf.get_width() > self.largeur - 200: x_mvt = 20; y_mvt_final = y_hud2; y_hud2 += 25
        self.fenetre.blit(mvt_surf, (x_mvt, y_mvt_final))
        mins, secs = int(tps_ec_s // 60), int(tps_ec_s % 60);
        tps_surf = self.font_jeu.render(f"Temps: {mins:02d}:{secs:02d}", True, C.DARK_TEXT_PRIMARY)
        self.fenetre.blit(tps_surf, (self.largeur - tps_surf.get_width() - 20, y_hud1))
        if hint_msg:
            msg_surf = self.font_jeu.render(hint_msg, True, C.DARK_HINT_COLOR); self.fenetre.blit(msg_surf,
                                                                                                  (20, y_hud2))
        elif deadlock_msg:
            msg_surf = self.font_jeu.render(deadlock_msg, True, C.DARK_DEADLOCK_WARN_COLOR); self.fenetre.blit(msg_surf,
                                                                                                               (20,
                                                                                                                y_hud2))
        instr_s = self.font_jeu.render("R:Recomm|U:Annul|ESC:Menu|F1:BFS|F2:Bktrk|H:Indice", True, C.DARK_ACCENT_WARN)
        self.fenetre.blit(instr_s, (20, self.hauteur - instr_s.get_height() - 15))
        if self.jeu_principal.victoire_detectee and self.message_victoire_affiche_temps == 0: self.message_victoire_affiche_temps = pygame.time.get_ticks()
        if self.message_victoire_affiche_temps > 0:
            self.afficher_message_victoire()
            if pygame.time.get_ticks() - self.message_victoire_affiche_temps > 3500: self.message_victoire_affiche_temps = 0; self.jeu_principal.passer_au_niveau_suivant_ou_menu()
        pygame.display.flip()

    def afficher_message_victoire(self):
        txt_vic = self.font_titre.render("NIVEAU TERMINÉ !", True, C.DARK_ACCENT_GOOD)
        r_vic = txt_vic.get_rect(centerx=self.largeur // 2, y=self.hauteur // 2 - 80)
        mvt, tps_s = self.jeu_principal.nb_mouvements, self.jeu_principal.temps_ecoule_total_secondes
        min, sec = int(tps_s // 60), int(tps_s % 60)
        txt_mvt_s = self.font_jeu.render(f"Mouvements: {mvt}", True, C.DARK_TEXT_PRIMARY)
        r_mvt_s = txt_mvt_s.get_rect(centerx=self.largeur // 2, y=r_vic.bottom + 20)
        txt_tps_s = self.font_jeu.render(f"Temps: {min:02d}:{sec:02d}", True, C.DARK_TEXT_PRIMARY)
        r_tps_s = txt_tps_s.get_rect(centerx=self.largeur // 2, y=r_mvt_s.bottom + 10)
        h_tot_txt = r_vic.h + r_mvt_s.h + r_tps_s.h + 60;
        l_max_txt = max(r_vic.w, r_mvt_s.w, r_tps_s.w)
        l_fond, h_fond = l_max_txt + 80, h_tot_txt + 60
        r_fond = pygame.Rect(0, 0, l_fond, h_fond);
        r_fond.center = (self.largeur // 2, self.hauteur // 2)
        s = pygame.Surface((l_fond, h_fond), pygame.SRCALPHA);
        s.fill((*C.DARK_SURFACE, 230))
        pygame.draw.rect(s, C.DARK_ACCENT_GOOD, s.get_rect(), 3, border_radius=10);
        self.fenetre.blit(s, r_fond.topleft)
        self.fenetre.blit(txt_vic, (r_fond.centerx - txt_vic.get_width() // 2, r_fond.top + 30))
        self.fenetre.blit(txt_mvt_s, (r_fond.centerx - txt_mvt_s.get_width() // 2, r_fond.top + 30 + r_vic.h + 20))
        self.fenetre.blit(txt_tps_s, (
        r_fond.centerx - txt_tps_s.get_width() // 2, r_fond.top + 30 + r_vic.h + 20 + r_mvt_s.h + 10))

    def afficher_editeur(self):  # Doit passer textures_active
        if self.editeur_instance is None:
            self.editeur_instance = editeur.EditeurNiveaux(15, 10, jeu_principal_ref=self.jeu_principal)
        textures_act = self.jeu_principal.textures_active if self.jeu_principal else True
        self.editeur_instance.dessiner(self.fenetre, self.images, self.font_menu, textures_act)
        pygame.display.flip()

    def gerer_evenement_editeur(self, event):
        if self.editeur_instance: self.editeur_instance.gerer_evenement(event)

    def afficher_scores(self, scores_data):
        self.fenetre.fill(C.DARK_BACKGROUND)
        tit_s = self.font_titre.render("Meilleurs Scores", True, C.DARK_TEXT_PRIMARY);
        tit_r = tit_s.get_rect(center=(self.largeur // 2, 60));
        self.fenetre.blit(tit_s, tit_r)
        marge_lat, marge_haut, marge_bas_btn, item_h = 50, 120, 80, 40
        zone_y_debut = marge_haut;
        zone_h_vis = self.hauteur - marge_haut - marge_bas_btn
        zone_l = self.largeur - 2 * marge_lat - (20 if len(scores_data) * item_h > zone_h_vis else 0)
        self.hauteur_contenu_scores = len(scores_data) * item_h
        surf_sc_scroll = pygame.Surface((zone_l, self.hauteur_contenu_scores));
        surf_sc_scroll.fill(C.DARK_BACKGROUND)
        y_item_rel = 0
        for nom, scr in scores_data.items():
            mvt, tps = scr.get('mouvements', 'N/A'), scr.get('temps', 'N/A')
            tps_str = f"{int(tps // 60):02d}:{int(tps % 60):02d}" if isinstance(tps, (int, float)) else 'N/A'
            txt = f"Niv. {nom}: {mvt} mvts, {tps_str}";
            s_txt = self.font_menu.render(txt, True, C.DARK_TEXT_SECONDARY)
            surf_sc_scroll.blit(s_txt, (10, y_item_rel + (item_h - s_txt.get_height()) // 2));
            y_item_rel += item_h
        self.fenetre.blit(surf_sc_scroll, (marge_lat, zone_y_debut), (0, self.scroll_offset_scores, zone_l, zone_h_vis))
        if self.hauteur_contenu_scores > zone_h_vis:
            sb_x = marge_lat + zone_l + 5;
            self.scrollbar_scores_rect = pygame.Rect(sb_x, zone_y_debut, 15, zone_h_vis)
            pygame.draw.rect(self.fenetre, C.DARK_SURFACE, self.scrollbar_scores_rect, border_radius=3)
            h_poignee = max(20, zone_h_vis * (
                        zone_h_vis / self.hauteur_contenu_scores)) if self.hauteur_contenu_scores > 0 else zone_h_vis
            ratio_sc = self.scroll_offset_scores / (self.hauteur_contenu_scores - zone_h_vis) if (
                                                                                                             self.hauteur_contenu_scores - zone_h_vis) > 0 else 0
            py = zone_y_debut + ratio_sc * (zone_h_vis - h_poignee)
            self.scrollbar_scores_poignee_rect = pygame.Rect(sb_x, py, 15, h_poignee)
            pygame.draw.rect(self.fenetre, C.DARK_BUTTON_HOVER_BG, self.scrollbar_scores_poignee_rect, border_radius=3)

        # Bouton Retour commun
        if not self.bouton_retour_options_scores:
            self.bouton_retour_options_scores = Bouton(self.largeur // 2 - 100, self.hauteur - 60, 200, 50,
                                                       "Retour Menu", font=self.font_menu, action=C.ETAT_MENU_PRINCIPAL)
        self.bouton_retour_options_scores.verifier_survol(pygame.mouse.get_pos());
        self.bouton_retour_options_scores.dessiner(self.fenetre)
        pygame.display.flip()

    def gerer_evenements_scores(self, event):  # Gère les events spécifiques aux Scores
        mouse_pos = event.pos if hasattr(event, 'pos') else pygame.mouse.get_pos()

        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:  # Clic gauche
                if self.bouton_retour_options_scores and self.bouton_retour_options_scores.verifier_clic(mouse_pos):
                    self.scroll_offset_scores = 0  # Reset scroll
                    self.bouton_retour_options_scores = None  # Clear pour recréation
                    return C.ETAT_MENU_PRINCIPAL
                if self.scrollbar_scores_poignee_rect and self.scrollbar_scores_poignee_rect.collidepoint(mouse_pos):
                    self.dragging_scrollbar_scores = True
            elif event.button == 4:  # Molette haut
                zone_h_vis = self.hauteur - 120 - 80
                self.scroll_offset_scores = max(0, self.scroll_offset_scores - 30)
            elif event.button == 5:  # Molette bas
                zone_h_vis = self.hauteur - 120 - 80
                max_s = max(0, self.hauteur_contenu_scores - zone_h_vis)
                self.scroll_offset_scores = min(max_s, self.scroll_offset_scores + 30)

        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1: self.dragging_scrollbar_scores = False

        elif event.type == pygame.MOUSEMOTION:
            if self.dragging_scrollbar_scores and self.scrollbar_scores_poignee_rect:
                zone_h_vis = self.hauteur - 120 - 80
                mouv_y = event.rel[1];
                h_poignee = self.scrollbar_scores_poignee_rect.height
                if (zone_h_vis - h_poignee) > 0 and (self.hauteur_contenu_scores - zone_h_vis) > 0:
                    delta_scroll = (mouv_y / (zone_h_vis - h_poignee)) * (self.hauteur_contenu_scores - zone_h_vis)
                    self.scroll_offset_scores = max(0, min(self.scroll_offset_scores + delta_scroll,
                                                           self.hauteur_contenu_scores - zone_h_vis))
        return None

    def afficher_visualisation_solveur(self, niv_visu, sol_pas, idx_pas_act, iterations_solveur, textures_active,
                                       msg=""):  # Ajout textures_active
        if not niv_visu: return
        self.fenetre.fill(C.DARK_BACKGROUND)
        niv_l_px, niv_h_px = niv_visu.largeur * C.TAILLE_CASE, niv_visu.hauteur * C.TAILLE_CASE
        off_x_g = (self.largeur - niv_l_px) // 2;
        off_y_g = (self.hauteur - niv_h_px - 120) // 2 + 20
        if off_x_g < 0: off_x_g = 5;
        if off_y_g < 50: off_y_g = 50
        surf_jeu_visu = pygame.Surface((niv_l_px, niv_h_px));
        surf_jeu_visu.fill(C.DARK_BACKGROUND)
        niv_visu.dessiner(surf_jeu_visu, self.images, textures_active)  # Passer textures_active
        self.fenetre.blit(surf_jeu_visu, (off_x_g, off_y_g))
        y_info = 15;
        type_s_txt = self.jeu_principal.solveur_type_en_cours if self.jeu_principal.solveur_type_en_cours else "Solveur"
        tit_visu_s = self.font_jeu.render(f"Visualisation - {type_s_txt.upper()}", True, C.DARK_TEXT_PRIMARY);
        self.fenetre.blit(tit_visu_s, (20, y_info));
        y_info += 25
        etat_s_txt = f"Calcul... Iter: {iterations_solveur}" if self.jeu_principal.solveur_en_cours else (
            f"Solution! Iter: {iterations_solveur}" if sol_pas else f"Pas de solution. Iter: {iterations_solveur}")
        etat_s = self.font_jeu.render(etat_s_txt, True, C.DARK_ACCENT_INFO);
        self.fenetre.blit(etat_s, (20, y_info));
        y_info += 25
        tot_p, pas_a_s, tot_p_s = (len(sol_pas) if sol_pas else 0), (str(idx_pas_act) if sol_pas else "-"), (
            str(len(sol_pas) if sol_pas else 0) if sol_pas else "-")
        suf_p = " (Fin)" if sol_pas and idx_pas_act >= tot_p else ""
        txt_pas_i = f"Pas: {pas_a_s} / {tot_p_s}{suf_p}";
        info_pas_s = self.font_jeu.render(txt_pas_i, True, C.DARK_TEXT_PRIMARY);
        self.fenetre.blit(info_pas_s, (20, y_info))
        instr_s = self.font_jeu.render("ESPACE: Suivant | ENTRÉE: Auto | ESC: Quitter", True, C.DARK_ACCENT_WARN);
        self.fenetre.blit(instr_s, (20, self.hauteur - instr_s.get_height() - 20))
        pygame.display.flip()

    def _creer_elements_options(self):
        self.elements_options["boutons"] = []
        self.elements_options["sliders"] = {}  # Vider pour recréation

        btn_w, btn_h, slider_w, slider_track_h = 350, 50, 300, 8
        x_centre_options = self.largeur // 2
        y_courant = self.hauteur // 2 - 120  # Démarrer plus haut

        # Slider Volume
        slider_volume = Slider(x_centre_options - slider_w // 2, y_courant, slider_w, slider_track_h,
                               0.0, 1.0, self.jeu_principal.volume_son,
                               label="Volume:", label_font=self.font_options_label, valeur_font=self.font_slider_valeur,
                               action_on_change="set_volume")
        self.elements_options["sliders"]["volume_slider"] = slider_volume
        y_courant += 70  # Espace pour le slider et son label/valeur

        # Bouton Textures
        texte_textures = "Textures: Activées" if self.jeu_principal.textures_active else "Textures: Désactivées"
        btn_textures = Bouton(x_centre_options - btn_w // 2, y_courant, btn_w, btn_h, texte_textures,
                              font=self.font_menu, action="toggle_textures")
        self.elements_options["boutons"].append(btn_textures)
        y_courant += btn_h + 30

        # Bouton Retour Menu (commun)
        if not self.bouton_retour_options_scores:
            self.bouton_retour_options_scores = Bouton(self.largeur // 2 - 100, self.hauteur - 70, 200, 50,
                                                       "Retour Menu", font=self.font_menu, action=C.ETAT_MENU_PRINCIPAL)

    def afficher_options(self):
        self.fenetre.fill(C.DARK_BACKGROUND)
        tit_s = self.font_titre.render("Options", True, C.DARK_TEXT_PRIMARY)
        tit_r = tit_s.get_rect(center=(self.largeur // 2, 80));
        self.fenetre.blit(tit_s, tit_r)

        # Recréer les éléments si la liste est vide (ex: premier affichage, ou après changement de taille fenetre)
        if not self.elements_options["boutons"] and not self.elements_options["sliders"]:
            self._creer_elements_options()

        mouse_pos = pygame.mouse.get_pos()

        for btn in self.elements_options["boutons"]:
            btn.verifier_survol(mouse_pos);
            btn.dessiner(self.fenetre)

        for slider_key in self.elements_options["sliders"]:
            slider = self.elements_options["sliders"][slider_key]
            # La vérification de survol est gérée dans handle_event pour les sliders
            slider.dessiner(self.fenetre)

        if self.bouton_retour_options_scores:
            self.bouton_retour_options_scores.verifier_survol(mouse_pos)
            self.bouton_retour_options_scores.dessiner(self.fenetre)

        pygame.display.flip()

    def gerer_evenements_options(self, event):
        mouse_pos = event.pos if hasattr(event, 'pos') else pygame.mouse.get_pos()
        action_retournee = None

        # Gérer les boutons
        for btn in self.elements_options["boutons"]:
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                action = btn.verifier_clic(mouse_pos)
                if action == "toggle_textures":
                    self.jeu_principal.toggle_textures()
                    self._creer_elements_options()  # Recréer pour màj texte bouton
                    return  # Consommer l'événement
            btn.verifier_survol(mouse_pos)  # Pour l'affichage

        # Gérer les sliders
        for slider_key, slider_obj in self.elements_options["sliders"].items():
            action_slider, nouvelle_valeur = slider_obj.handle_event(event, mouse_pos)
            if action_slider == "set_volume" and nouvelle_valeur is not None:
                self.jeu_principal.set_volume(nouvelle_valeur)
                # Pas besoin de recréer les éléments pour le slider, sa propre méthode dessiner met à jour la valeur

        # Gérer le bouton Retour Menu
        if self.bouton_retour_options_scores:
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                action_retour = self.bouton_retour_options_scores.verifier_clic(mouse_pos)
                if action_retour == C.ETAT_MENU_PRINCIPAL:
                    self.elements_options = {"boutons": [], "sliders": {}}  # Vider
                    self.bouton_retour_options_scores = None
                    self.jeu_principal.etat_jeu = C.ETAT_MENU_PRINCIPAL  # Changer l'état dans Jeu
                    self.jeu_principal._adapter_taille_fenetre_pour_niveau()
                    return  # Consommer l'événement
            self.bouton_retour_options_scores.verifier_survol(mouse_pos)