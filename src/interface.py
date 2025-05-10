import pygame
import os
from . import constantes as C
from . import utilitaires
from . import classes
from . import editeur
from . import solveurs
from .ui_elements import Bouton


class InterfaceGraphique:
    def __init__(self, largeur, hauteur, jeu_principal):
        self.largeur = largeur;
        self.hauteur = hauteur
        self.fenetre = pygame.display.set_mode((largeur, hauteur))
        pygame.display.set_caption("Sokoban")
        self.images = utilitaires.charger_images_sokoban()
        if self.images.get('icon'): pygame.display.set_icon(self.images['icon'])
        self.font_titre = pygame.font.Font(C.POLICE_DEFAUT, C.TAILLE_POLICE_TITRE)
        self.font_menu = pygame.font.Font(C.POLICE_DEFAUT, C.TAILLE_POLICE_MENU)
        self.font_jeu = pygame.font.Font(C.POLICE_DEFAUT, C.TAILLE_POLICE_JEU)
        self.jeu_principal = jeu_principal
        self.boutons_menu = [];
        self.boutons_selection_niveau = []
        self.scroll_offset_selection_niveau = 0;
        self.hauteur_contenu_selection_niveau = 0
        self.btn_retour_sel_niveau = None
        self.message_victoire_affiche_temps = 0;
        self.editeur_instance = None
        self.temp_bouton_retour_scores = None

    def _creer_boutons_menu_principal(self):
        self.boutons_menu = []
        btn_w, btn_h, espace, nb_btns = 300, 55, 25, 4
        x_c = self.largeur // 2 - btn_w // 2
        y_tot_b = nb_btns * btn_h + (nb_btns - 1) * espace
        y_start = self.hauteur // 2 - y_tot_b // 2 + 30
        actions = [("Nouvelle Partie", C.ETAT_SELECTION_NIVEAU), ("Éditeur de Niveaux", C.ETAT_EDITEUR),
                   ("Scores", C.ETAT_SCORES), ("Quitter", C.ETAT_QUITTER)]
        for i, (txt, act_id) in enumerate(actions):
            self.boutons_menu.append(
                Bouton(x_c, y_start + i * (btn_h + espace), btn_w, btn_h, txt, font=self.font_menu, action=act_id))

    def afficher_menu_principal(self):
        self.fenetre.fill(C.DARK_BACKGROUND)
        tit_s = self.font_titre.render("Sokoban", True, C.DARK_TEXT_PRIMARY)
        tit_r = tit_s.get_rect(center=(self.largeur // 2, self.hauteur // 4))
        self.fenetre.blit(tit_s, tit_r)
        if not self.boutons_menu: self._creer_boutons_menu_principal()
        mouse_pos = pygame.mouse.get_pos()
        for btn in self.boutons_menu: btn.verifier_survol(mouse_pos); btn.dessiner(self.fenetre)
        pygame.display.flip()

    def gerer_clic_menu_principal(self, p_s):
        return next((b.verifier_clic(p_s) for b in self.boutons_menu if b.verifier_clic(p_s)), None)

    def _preparer_boutons_selection_niveau(self, chemins_niveaux_defaut,
                                           chemins_niveaux_perso):  # MODIFIÉ pour accepter chemins
        self.boutons_selection_niveau = []
        tous_n_s = [];
        idx_g_c = 0

        for i, path in enumerate(chemins_niveaux_defaut):  # Utilise chemins_niveaux_defaut
            nom_b = os.path.basename(path);
            nom_a = nom_b.replace(".txt", f" (Défaut {i + 1})")
            spec = {"type_charge": "fichier_chemin", "data": path, "index_global": idx_g_c,
                    "nom_affiche": nom_b.replace(".txt", "")}  # type_charge est maintenant fichier_chemin
            tous_n_s.append({"nom_pour_bouton": nom_a, "action_spec": spec});
            idx_g_c += 1

        for i, path in enumerate(chemins_niveaux_perso):  # Utilise chemins_niveaux_perso
            nom_b = os.path.basename(path);
            nom_a = nom_b.replace(".txt", f" (Perso {i + 1})")  # On utilise le nom de fichier
            spec = {"type_charge": "fichier_chemin", "data": path, "index_global": idx_g_c,
                    "nom_affiche": nom_b.replace(".txt", "")}  # type_charge est fichier_chemin
            tous_n_s.append({"nom_pour_bouton": nom_a, "action_spec": spec});
            idx_g_c += 1

        btn_w, btn_h, esp_v = 300, 45, 15
        nb_cols = 2 if self.largeur > (btn_w * 2 + 100) else 1
        x_pos_cols = []
        if nb_cols == 1:
            x_pos_cols.append(self.largeur // 2 - btn_w // 2)
        else:
            l_tot_b_e = btn_w * 2 + 60; x_dep_tot = self.largeur // 2 - l_tot_b_e // 2; x_pos_cols.extend(
                [x_dep_tot + 20, x_dep_tot + btn_w + 40])
        y_p_d_rel = 0;
        self.hauteur_contenu_selection_niveau = 0
        for i, niv_spec_b in enumerate(tous_n_s):
            col_i = i % nb_cols;
            row_i = i // nb_cols
            curr_x = x_pos_cols[col_i];
            curr_y_rel = y_p_d_rel + row_i * (btn_h + esp_v)
            nom_b_txt = niv_spec_b["nom_pour_bouton"];
            act_p_b = niv_spec_b["action_spec"]
            self.boutons_selection_niveau.append(
                Bouton(curr_x, curr_y_rel, btn_w, btn_h, nom_b_txt, font=self.font_menu, action=act_p_b))
            if curr_y_rel + btn_h > self.hauteur_contenu_selection_niveau: self.hauteur_contenu_selection_niveau = curr_y_rel + btn_h
        if self.boutons_selection_niveau: self.hauteur_contenu_selection_niveau += esp_v
        self.btn_retour_sel_niveau = Bouton(self.largeur // 2 - 100, self.hauteur - 70, 200, 50, "Retour Menu",
                                            font=self.font_menu, action="retour_menu")

    def afficher_selection_niveau(self, chemins_niveaux_defaut, chemins_niveaux_perso):  # MODIFIÉ
        self.fenetre.fill(C.DARK_BACKGROUND)
        tit_s = self.font_titre.render("Sélectionnez un Niveau", True, C.DARK_TEXT_PRIMARY)
        tit_r = tit_s.get_rect(center=(self.largeur // 2, 60));
        self.fenetre.blit(tit_s, tit_r)
        if not self.boutons_selection_niveau or not self.btn_retour_sel_niveau: self._preparer_boutons_selection_niveau(
            chemins_niveaux_defaut, chemins_niveaux_perso)  # MODIFIÉ
        y_z_s_d = 120;
        h_v_z_s = self.hauteur - y_z_s_d - 80
        surf_scroll = pygame.Surface((self.largeur, self.hauteur_contenu_selection_niveau));
        surf_scroll.fill(C.DARK_BACKGROUND)
        mouse_pos_abs = pygame.mouse.get_pos()
        for btn in self.boutons_selection_niveau:
            rect_ecran = pygame.Rect(btn.rect.x, btn.rect.y - self.scroll_offset_selection_niveau + y_z_s_d,
                                     btn.rect.width, btn.rect.height)
            btn.survol = rect_ecran.collidepoint(mouse_pos_abs)
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
            s_x_rel = p_s_a[0];
            s_y_rel = p_s_a[1] - y_z_s_d + self.scroll_offset_selection_niveau
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

    def afficher_ecran_jeu(self, niv_act, nb_mvt, tps_ec_s):
        if not niv_act: return
        niv_l_px, niv_h_px = niv_act.largeur * C.TAILLE_CASE, niv_act.hauteur * C.TAILLE_CASE
        surf_jeu = pygame.Surface((niv_l_px, niv_h_px));
        niv_act.dessiner(surf_jeu, self.images)
        off_x_g = (self.largeur - niv_l_px) // 2;
        off_y_g = (self.hauteur - niv_h_px - 60) // 2
        if off_x_g < 0: off_x_g = 0;
        if off_y_g < 0: off_y_g = 0
        self.fenetre.fill(C.NOIR);
        self.fenetre.blit(surf_jeu, (off_x_g, off_y_g))
        hud_y = 15;
        hud_mvt_s = self.font_jeu.render(f"Mouvements: {nb_mvt}", True, C.DARK_TEXT_PRIMARY);
        self.fenetre.blit(hud_mvt_s, (20, hud_y))
        mins, secs = int(tps_ec_s // 60), int(tps_ec_s % 60)
        hud_tps_s = self.font_jeu.render(f"Temps: {mins:02d}:{secs:02d}", True, C.DARK_TEXT_PRIMARY);
        self.fenetre.blit(hud_tps_s, (self.largeur - hud_tps_s.get_width() - 20, hud_y))
        instr_text = "R:Recommencer|U:Annuler|ESC:Menu|F1:BFS|F2:Backtrack"
        instr_surface = self.font_jeu.render(instr_text, True, C.JAUNE)
        self.fenetre.blit(instr_surface, (20, self.hauteur - instr_surface.get_height() - 15))
        if self.jeu_principal.victoire_detectee and self.message_victoire_affiche_temps == 0: self.message_victoire_affiche_temps = pygame.time.get_ticks()
        if self.message_victoire_affiche_temps > 0:
            self.afficher_message_victoire()
            if pygame.time.get_ticks() - self.message_victoire_affiche_temps > 2500: self.message_victoire_affiche_temps = 0; self.jeu_principal.passer_au_niveau_suivant_ou_menu()
        pygame.display.flip()

    def afficher_message_victoire(self):
        txt_vic = self.font_titre.render("NIVEAU TERMINÉ !", True, C.DARK_ACCENT_GOOD)
        r_vic = txt_vic.get_rect(center=(self.largeur // 2, self.hauteur // 2))
        s = pygame.Surface((r_vic.width + 40, r_vic.height + 30), pygame.SRCALPHA);
        s.fill((C.DARK_SURFACE[0], C.DARK_SURFACE[1], C.DARK_SURFACE[2], 220))
        pygame.draw.rect(s, C.DARK_ACCENT_GOOD, s.get_rect(), 2, border_radius=5);
        self.fenetre.blit(s, (r_vic.left - 20, r_vic.top - 15))
        self.fenetre.blit(txt_vic, r_vic)

    def afficher_editeur(self):
        if self.editeur_instance is None: self.editeur_instance = editeur.EditeurNiveaux(15, 10,
                                                                                         jeu_principal_ref=self.jeu_principal)
        self.editeur_instance.dessiner(self.fenetre, self.images, self.font_menu);
        pygame.display.flip()

    def gerer_evenement_editeur(self, event):
        if self.editeur_instance: self.editeur_instance.gerer_evenement(event)

    def afficher_scores(self, scores_data):
        self.fenetre.fill(C.DARK_BACKGROUND)
        tit_s = self.font_titre.render("Meilleurs Scores", True, C.DARK_TEXT_PRIMARY);
        tit_r = tit_s.get_rect(center=(self.largeur // 2, 60));
        self.fenetre.blit(tit_s, tit_r)
        y_off, x_off = 130, 70
        for nom_niv, scr_info in scores_data.items():
            mvt, tps_s = scr_info.get('mouvements', 'N/A'), scr_info.get('temps', 'N/A')
            tps_str = f"{int(tps_s // 60):02d}:{int(tps_s % 60):02d}" if isinstance(tps_s, (int, float)) else 'N/A'
            scr_txt = f"Niv. {nom_niv}: {mvt} mvts, {tps_str}"
            scr_s = self.font_menu.render(scr_txt, True, C.DARK_TEXT_SECONDARY);
            self.fenetre.blit(scr_s, (x_off, y_off));
            y_off += 45
            if y_off > self.hauteur - 100: txt_plus = self.font_menu.render("...", True,
                                                                            C.DARK_TEXT_SECONDARY); self.fenetre.blit(
                txt_plus, (x_off, y_off)); break
        self.temp_bouton_retour_scores = Bouton(self.largeur // 2 - 100, self.hauteur - 70, 200, 50, "Retour Menu",
                                                font=self.font_menu, action=C.ETAT_MENU_PRINCIPAL)
        mouse_pos = pygame.mouse.get_pos();
        self.temp_bouton_retour_scores.verifier_survol(mouse_pos);
        self.temp_bouton_retour_scores.dessiner(self.fenetre)
        pygame.display.flip()

    def gerer_clic_scores(self, p_s):
        return self.temp_bouton_retour_scores.verifier_clic(p_s) if self.temp_bouton_retour_scores else None

    def afficher_visualisation_solveur(self, niv_visu, sol_pas, idx_pas_act, msg=""):
        if not niv_visu: return
        self.fenetre.fill(C.DARK_SURFACE)
        niv_l_px, niv_h_px = niv_visu.largeur * C.TAILLE_CASE, niv_visu.hauteur * C.TAILLE_CASE
        surf_jeu_visu = pygame.Surface((niv_l_px, niv_h_px));
        niv_visu.dessiner(surf_jeu_visu, self.images)
        off_x_g = (self.largeur - niv_l_px) // 2;
        off_y_g = (self.hauteur - niv_h_px - 90) // 2;
        self.fenetre.blit(surf_jeu_visu, (off_x_g, off_y_g))
        tot_pas = len(sol_pas) if sol_pas else 0
        info_pas_s = self.font_jeu.render(f"Pas: {idx_pas_act + 1} / {tot_pas}", True, C.DARK_TEXT_PRIMARY);
        self.fenetre.blit(info_pas_s, (30, 25))
        msg_s = self.font_jeu.render(msg, True, C.DARK_ACCENT_INFO);
        self.fenetre.blit(msg_s, (30, 55))
        instr_s = self.font_jeu.render("ESPACE: Suivant | ENTRÉE: Terminer | ESC: Annuler", True, C.DARK_ACCENT_WARN);
        self.fenetre.blit(instr_s, (30, self.hauteur - instr_s.get_height() - 20))
        pygame.display.flip()