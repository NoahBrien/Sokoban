import pygame
import os
from . import constantes as C
from . import utilitaires
from . import classes
from . import editeur
from . import solveurs
from .ui_elements import Bouton

class InterfaceGraphique:
    # ... (le début de la classe est identique à la version précédente) ...
    def __init__(self, largeur, hauteur, jeu_principal): # Copié de la version précédente
        self.largeur = largeur; self.hauteur = hauteur
        self.fenetre = pygame.display.set_mode((largeur, hauteur))
        pygame.display.set_caption("Sokoban")
        self.images = utilitaires.charger_images_sokoban()
        if self.images.get('icon'): pygame.display.set_icon(self.images['icon'])
        self.font_titre = pygame.font.Font(C.POLICE_DEFAUT, C.TAILLE_POLICE_TITRE)
        self.font_menu = pygame.font.Font(C.POLICE_DEFAUT, C.TAILLE_POLICE_MENU)
        self.font_jeu = pygame.font.Font(C.POLICE_DEFAUT, C.TAILLE_POLICE_JEU)
        self.jeu_principal = jeu_principal
        self.boutons_menu = []; self.boutons_selection_niveau = []
        self.scroll_offset_selection_niveau = 0; self.hauteur_contenu_selection_niveau = 0
        self.btn_retour_sel_niveau = None
        self.message_victoire_affiche_temps = 0; self.editeur_instance = None
        self.temp_bouton_retour_scores = None
        self.scroll_offset_scores = 0; self.hauteur_contenu_scores = 0
        self.scrollbar_scores_rect = None; self.scrollbar_scores_poignee_rect = None
        self.dragging_scrollbar_scores = False


    def _creer_boutons_menu_principal(self): # Copié
        self.boutons_menu = []
        btn_w, btn_h, espace, nb_btns = 300,55,25,4
        x_c = self.largeur//2 - btn_w//2; y_tot_b = nb_btns*btn_h + (nb_btns-1)*espace
        y_start = self.hauteur//2 - y_tot_b//2 + 30
        actions = [("Nouvelle Partie",C.ETAT_SELECTION_NIVEAU),("Éditeur de Niveaux",C.ETAT_EDITEUR),
                   ("Scores",C.ETAT_SCORES),("Quitter",C.ETAT_QUITTER)]
        for i, (txt, act_id) in enumerate(actions):
            self.boutons_menu.append(Bouton(x_c, y_start+i*(btn_h+espace), btn_w,btn_h,txt,font=self.font_menu,action=act_id))

    def afficher_menu_principal(self): # Copié
        self.fenetre.fill(C.DARK_BACKGROUND)
        tit_s = self.font_titre.render("Sokoban",True,C.DARK_TEXT_PRIMARY)
        tit_r = tit_s.get_rect(center=(self.largeur//2, self.hauteur//4)); self.fenetre.blit(tit_s,tit_r)
        if not self.boutons_menu: self._creer_boutons_menu_principal()
        mouse_pos = pygame.mouse.get_pos()
        for btn in self.boutons_menu: btn.verifier_survol(mouse_pos); btn.dessiner(self.fenetre)
        pygame.display.flip()

    def gerer_clic_menu_principal(self,p_s): return next((b.verifier_clic(p_s) for b in self.boutons_menu if b.verifier_clic(p_s)),None) # Copié

    def _preparer_boutons_selection_niveau(self, chemins_niveaux_defaut, chemins_niveaux_perso): # Copié
        self.boutons_selection_niveau = [] ; tous_n_s = [] ; idx_g_c = 0
        for i, path in enumerate(chemins_niveaux_defaut):
            nom_b = os.path.basename(path); nom_a = nom_b.replace(".txt",f" (Défaut {i+1})")
            spec={"type_charge":"fichier_chemin","data":path,"index_global":idx_g_c,"nom_affiche":nom_b.replace(".txt","")}
            tous_n_s.append({"nom_pour_bouton":nom_a, "action_spec":spec}); idx_g_c+=1
        for i, path in enumerate(chemins_niveaux_perso):
            nom_b = os.path.basename(path); nom_a = nom_b.replace(".txt",f" (Perso {i+1})")
            spec={"type_charge":"fichier_chemin","data":path,"index_global":idx_g_c,"nom_affiche":nom_b.replace(".txt","")}
            tous_n_s.append({"nom_pour_bouton":nom_a, "action_spec":spec}); idx_g_c+=1
        btn_w,btn_h,esp_v=300,45,15; nb_cols=2 if self.largeur>(btn_w*2+100) else 1; x_pos_cols=[]
        if nb_cols==1: x_pos_cols.append(self.largeur//2-btn_w//2)
        else: l_tot_b_e=btn_w*2+60; x_dep_tot=self.largeur//2-l_tot_b_e//2; x_pos_cols.extend([x_dep_tot+20, x_dep_tot+btn_w+40])
        y_p_d_rel=0; self.hauteur_contenu_selection_niveau=0
        for i, niv_spec_b in enumerate(tous_n_s):
            col_i=i%nb_cols; row_i=i//nb_cols
            curr_x=x_pos_cols[col_i]; curr_y_rel=y_p_d_rel+row_i*(btn_h+esp_v)
            nom_b_txt=niv_spec_b["nom_pour_bouton"]; act_p_b=niv_spec_b["action_spec"]
            self.boutons_selection_niveau.append(Bouton(curr_x,curr_y_rel,btn_w,btn_h,nom_b_txt,font=self.font_menu,action=act_p_b))
            if curr_y_rel+btn_h > self.hauteur_contenu_selection_niveau: self.hauteur_contenu_selection_niveau=curr_y_rel+btn_h
        if self.boutons_selection_niveau: self.hauteur_contenu_selection_niveau+=esp_v
        self.btn_retour_sel_niveau=Bouton(self.largeur//2-100,self.hauteur-70,200,50,"Retour Menu",font=self.font_menu,action="retour_menu")

    def afficher_selection_niveau(self, chemins_niveaux_defaut, chemins_niveaux_perso): # Copié
        self.fenetre.fill(C.DARK_BACKGROUND)
        tit_s=self.font_titre.render("Sélectionnez un Niveau",True,C.DARK_TEXT_PRIMARY)
        tit_r=tit_s.get_rect(center=(self.largeur//2,60)); self.fenetre.blit(tit_s,tit_r)
        if not self.boutons_selection_niveau or not self.btn_retour_sel_niveau: self._preparer_boutons_selection_niveau(chemins_niveaux_defaut, chemins_niveaux_perso)
        y_z_s_d=120; h_v_z_s=self.hauteur-y_z_s_d-80
        surf_scroll=pygame.Surface((self.largeur,self.hauteur_contenu_selection_niveau)); surf_scroll.fill(C.DARK_BACKGROUND)
        mouse_pos_abs=pygame.mouse.get_pos()
        for btn in self.boutons_selection_niveau:
            rect_ecran=pygame.Rect(btn.rect.x, btn.rect.y-self.scroll_offset_selection_niveau+y_z_s_d, btn.rect.width,btn.rect.height)
            btn.survol = rect_ecran.collidepoint(mouse_pos_abs); btn.dessiner(surf_scroll)
        self.fenetre.blit(surf_scroll,(0,y_z_s_d),(0,self.scroll_offset_selection_niveau,self.largeur,h_v_z_s))
        if self.btn_retour_sel_niveau: self.btn_retour_sel_niveau.verifier_survol(mouse_pos_abs); self.btn_retour_sel_niveau.dessiner(self.fenetre)
        pygame.display.flip()

    def gerer_clic_selection_niveau(self,p_s_a,ev_b): # Copié
        y_z_s_d=120; h_v_z_s=self.hauteur-y_z_s_d-80
        if ev_b==4: self.scroll_offset_selection_niveau=max(0,self.scroll_offset_selection_niveau-30); return None
        elif ev_b==5: max_s=max(0,self.hauteur_contenu_selection_niveau-h_v_z_s); self.scroll_offset_selection_niveau=min(max_s,self.scroll_offset_selection_niveau+30); return None
        if ev_b==1:
            if self.btn_retour_sel_niveau and self.btn_retour_sel_niveau.verifier_clic(p_s_a):
                self.boutons_selection_niveau=[];self.scroll_offset_selection_niveau=0;self.btn_retour_sel_niveau=None; return C.ETAT_MENU_PRINCIPAL
            s_x_rel=p_s_a[0]; s_y_rel=p_s_a[1]-y_z_s_d+self.scroll_offset_selection_niveau
            for btn in self.boutons_selection_niveau:
                if btn.rect.collidepoint((s_x_rel,s_y_rel)):
                    action = btn.action
                    if isinstance(action,dict):
                        self.jeu_principal.charger_niveau_par_specification(action)
                        self.boutons_selection_niveau=[];self.scroll_offset_selection_niveau=0;self.btn_retour_sel_niveau=None; return C.ETAT_JEU
        return None

    def afficher_ecran_jeu(self,niv_act,nb_mvt,tps_ec_s, hint_pos=None, hint_msg=""):
        if not niv_act: return
        niv_l_px,niv_h_px=niv_act.largeur*C.TAILLE_CASE,niv_act.hauteur*C.TAILLE_CASE
        surf_jeu=pygame.Surface((niv_l_px,niv_h_px)); niv_act.dessiner(surf_jeu,self.images)
        if hint_pos:
            h_x, h_y = hint_pos
            rect_hint = pygame.Rect(h_x * C.TAILLE_CASE + 5, h_y * C.TAILLE_CASE + 5, C.TAILLE_CASE - 10, C.TAILLE_CASE - 10)
            pygame.draw.rect(surf_jeu, C.DARK_HINT_COLOR, rect_hint, 3, border_radius=4)
        off_x_g=(self.largeur-niv_l_px)//2; off_y_g=(self.hauteur-niv_h_px-80)//2
        if off_x_g<0:off_x_g=0;
        if off_y_g<0:off_y_g=0
        self.fenetre.fill(C.NOIR); self.fenetre.blit(surf_jeu,(off_x_g,off_y_g))
        hud_y=15; hud_mvt_s=self.font_jeu.render(f"Mouvements: {nb_mvt}",True,C.DARK_TEXT_PRIMARY); self.fenetre.blit(hud_mvt_s,(20,hud_y))
        mins,secs=int(tps_ec_s//60),int(tps_ec_s%60)
        hud_tps_s=self.font_jeu.render(f"Temps: {mins:02d}:{secs:02d}",True,C.DARK_TEXT_PRIMARY); self.fenetre.blit(hud_tps_s,(self.largeur-hud_tps_s.get_width()-20,hud_y))
        if hint_msg:
            hint_msg_surf = self.font_jeu.render(hint_msg, True, C.DARK_HINT_COLOR)
            self.fenetre.blit(hint_msg_surf, (20, hud_y + 25)) # Affichage du message d'indice
        instr_text = "R:Recomm|U:Annul|ESC:Menu|F1:BFS|F2:Bktrk|H:Indice"
        instr_surface = self.font_jeu.render(instr_text, True, C.JAUNE)
        self.fenetre.blit(instr_surface,(20,self.hauteur-instr_surface.get_height()-15))
        if self.jeu_principal.victoire_detectee and self.message_victoire_affiche_temps==0: self.message_victoire_affiche_temps=pygame.time.get_ticks()
        if self.message_victoire_affiche_temps>0:
            self.afficher_message_victoire()
            if pygame.time.get_ticks()-self.message_victoire_affiche_temps > 3500: self.message_victoire_affiche_temps=0; self.jeu_principal.passer_au_niveau_suivant_ou_menu()
        pygame.display.flip()

    def afficher_message_victoire(self): # Copié
        texte_victoire = self.font_titre.render("NIVEAU TERMINÉ !", True, C.DARK_ACCENT_GOOD)
        rect_victoire = texte_victoire.get_rect(centerx=self.largeur // 2, y=self.hauteur // 2 - 60)
        nb_mouvements = self.jeu_principal.nb_mouvements; temps_ecoule_secondes = self.jeu_principal.temps_ecoule_total_secondes
        minutes = int(temps_ecoule_secondes // 60); secondes = int(temps_ecoule_secondes % 60)
        texte_stats_mvt = self.font_jeu.render(f"Mouvements: {nb_mouvements}", True, C.DARK_TEXT_PRIMARY)
        rect_stats_mvt = texte_stats_mvt.get_rect(centerx=self.largeur // 2, y=rect_victoire.bottom + 10)
        texte_stats_temps = self.font_jeu.render(f"Temps: {minutes:02d}:{secondes:02d}", True, C.DARK_TEXT_PRIMARY)
        rect_stats_temps = texte_stats_temps.get_rect(centerx=self.largeur // 2, y=rect_stats_mvt.bottom + 5)
        hauteur_totale_texte = rect_victoire.height + rect_stats_mvt.height + rect_stats_temps.height + 25
        largeur_maximale_texte = max(rect_victoire.width, rect_stats_mvt.width, rect_stats_temps.width)
        largeur_fond = largeur_maximale_texte + 60; hauteur_fond = hauteur_totale_texte + 40
        rect_fond = pygame.Rect(0,0, largeur_fond, hauteur_fond); rect_fond.center = (self.largeur // 2, self.hauteur // 2)
        s = pygame.Surface((largeur_fond, hauteur_fond), pygame.SRCALPHA); s.fill((C.DARK_SURFACE[0], C.DARK_SURFACE[1], C.DARK_SURFACE[2], 230))
        pygame.draw.rect(s, C.DARK_ACCENT_GOOD, s.get_rect(), 3, border_radius=8); self.fenetre.blit(s, rect_fond.topleft)
        self.fenetre.blit(texte_victoire, (rect_fond.centerx - texte_victoire.get_width()//2, rect_fond.top + 20))
        self.fenetre.blit(texte_stats_mvt, (rect_fond.centerx - texte_stats_mvt.get_width()//2, rect_fond.top + 20 + rect_victoire.height + 10))
        self.fenetre.blit(texte_stats_temps, (rect_fond.centerx - texte_stats_temps.get_width()//2, rect_fond.top + 20 + rect_victoire.height + 10 + rect_stats_mvt.height + 5))

    def afficher_editeur(self): # Copié
        if self.editeur_instance is None: self.editeur_instance = editeur.EditeurNiveaux(15,10,jeu_principal_ref=self.jeu_principal)
        self.editeur_instance.dessiner(self.fenetre,self.images,self.font_menu); pygame.display.flip()

    def gerer_evenement_editeur(self,event): # Copié
        if self.editeur_instance: self.editeur_instance.gerer_evenement(event)

    def afficher_scores(self, scores_data): # Copié
        self.fenetre.fill(C.DARK_BACKGROUND)
        tit_s=self.font_titre.render("Meilleurs Scores",True,C.DARK_TEXT_PRIMARY); tit_r=tit_s.get_rect(center=(self.largeur//2,60)); self.fenetre.blit(tit_s,tit_r)
        marge_laterale = 50; marge_haut = 120; marge_bas_bouton = 80; hauteur_item_score = 40
        zone_scores_y_debut = marge_haut; zone_scores_hauteur_visible = self.hauteur - marge_haut - marge_bas_bouton
        zone_scores_largeur = self.largeur - 2 * marge_laterale - 20
        self.hauteur_contenu_scores = len(scores_data) * hauteur_item_score
        surface_scores_scrollable = pygame.Surface((zone_scores_largeur, self.hauteur_contenu_scores)); surface_scores_scrollable.fill(C.DARK_BACKGROUND)
        y_item_relatif = 0
        for nom_niv,scr_info in scores_data.items():
            mvt,tps_s=scr_info.get('mouvements','N/A'),scr_info.get('temps','N/A')
            tps_str=f"{int(tps_s//60):02d}:{int(tps_s%60):02d}" if isinstance(tps_s,(int,float)) else 'N/A'
            scr_txt=f"Niv. {nom_niv}: {mvt} mvts, {tps_str}"
            scr_s=self.font_menu.render(scr_txt,True,C.DARK_TEXT_SECONDARY)
            surface_scores_scrollable.blit(scr_s,(10, y_item_relatif + (hauteur_item_score - scr_s.get_height()) // 2)); y_item_relatif += hauteur_item_score
        self.fenetre.blit(surface_scores_scrollable, (marge_laterale, zone_scores_y_debut), (0, self.scroll_offset_scores, zone_scores_largeur, zone_scores_hauteur_visible))
        if self.hauteur_contenu_scores > zone_scores_hauteur_visible:
            scrollbar_x = marge_laterale + zone_scores_largeur + 5
            self.scrollbar_scores_rect = pygame.Rect(scrollbar_x, zone_scores_y_debut, 15, zone_scores_hauteur_visible)
            pygame.draw.rect(self.fenetre, C.DARK_SURFACE, self.scrollbar_scores_rect, border_radius=3)
            hauteur_poignee = max(20, zone_scores_hauteur_visible * (zone_scores_hauteur_visible / self.hauteur_contenu_scores)) if self.hauteur_contenu_scores > 0 else zone_scores_hauteur_visible
            ratio_scroll = self.scroll_offset_scores / (self.hauteur_contenu_scores - zone_scores_hauteur_visible) if (self.hauteur_contenu_scores - zone_scores_hauteur_visible) > 0 else 0
            poignee_y = zone_scores_y_debut + ratio_scroll * (zone_scores_hauteur_visible - hauteur_poignee)
            self.scrollbar_scores_poignee_rect = pygame.Rect(scrollbar_x, poignee_y, 15, hauteur_poignee)
            pygame.draw.rect(self.fenetre, C.DARK_BUTTON_HOVER_BG, self.scrollbar_scores_poignee_rect, border_radius=3)
        self.temp_bouton_retour_scores=Bouton(self.largeur//2-100,self.hauteur-60,200,50,"Retour Menu",font=self.font_menu,action=C.ETAT_MENU_PRINCIPAL)
        mouse_pos=pygame.mouse.get_pos(); self.temp_bouton_retour_scores.verifier_survol(mouse_pos); self.temp_bouton_retour_scores.dessiner(self.fenetre)
        pygame.display.flip()

    def gerer_clic_scores(self,p_s_a, ev_b, rel_mouse_move_tuple=(0,0)): # Copié
        zone_scores_y_debut = 120; zone_scores_hauteur_visible = self.hauteur - 120 - 80
        if ev_b == 1:
            if self.temp_bouton_retour_scores and self.temp_bouton_retour_scores.verifier_clic(p_s_a): self.scroll_offset_scores = 0; return C.ETAT_MENU_PRINCIPAL
            if self.scrollbar_scores_poignee_rect and self.scrollbar_scores_poignee_rect.collidepoint(p_s_a): self.dragging_scrollbar_scores = True; return None
        elif ev_b == pygame.MOUSEBUTTONUP and pygame.mouse.get_pressed()[0] == 0 : self.dragging_scrollbar_scores = False; return None
        elif ev_b == pygame.MOUSEMOTION and self.dragging_scrollbar_scores:
            if self.hauteur_contenu_scores > zone_scores_hauteur_visible and self.scrollbar_scores_poignee_rect :
                mouvement_souris_y = rel_mouse_move_tuple[1]; hauteur_poignee = self.scrollbar_scores_poignee_rect.height
                if (zone_scores_hauteur_visible - hauteur_poignee) > 0 :
                    delta_scroll = (mouvement_souris_y / (zone_scores_hauteur_visible - hauteur_poignee)) * (self.hauteur_contenu_scores - zone_scores_hauteur_visible)
                    self.scroll_offset_scores = max(0, min(self.scroll_offset_scores + delta_scroll, self.hauteur_contenu_scores - zone_scores_hauteur_visible))
            return None
        if isinstance(ev_b, int):
            if ev_b==4: self.scroll_offset_scores=max(0,self.scroll_offset_scores-30)
            elif ev_b==5: max_s=max(0,self.hauteur_contenu_scores-zone_scores_hauteur_visible); self.scroll_offset_scores=min(max_s,self.scroll_offset_scores+30)
        return None

    def afficher_visualisation_solveur(self,niv_visu,sol_pas,idx_pas_act,msg=""): # Copié
        if not niv_visu: return
        self.fenetre.fill(C.DARK_SURFACE)
        niv_l_px,niv_h_px=niv_visu.largeur*C.TAILLE_CASE,niv_visu.hauteur*C.TAILLE_CASE
        surf_jeu_visu=pygame.Surface((niv_l_px,niv_h_px)); niv_visu.dessiner(surf_jeu_visu,self.images)
        off_x_g=(self.largeur-niv_l_px)//2; off_y_g=(self.hauteur-niv_h_px-90)//2; self.fenetre.blit(surf_jeu_visu,(off_x_g,off_y_g))
        tot_pas = len(sol_pas) if sol_pas else 0
        display_step_number_str, display_total_steps_str = "-", "-"; texte_pas_suffix = ""
        if tot_pas > 0:
            display_total_steps_str = str(tot_pas)
            display_step_number_str = str(idx_pas_act)
            if idx_pas_act == tot_pas:
                texte_pas_suffix = " (Fin)"
        texte_pas_info = f"Pas: {display_step_number_str} / {display_total_steps_str}{texte_pas_suffix}"
        info_pas_s=self.font_jeu.render(texte_pas_info,True,C.DARK_TEXT_PRIMARY)
        self.fenetre.blit(info_pas_s,(30,25))
        msg_s=self.font_jeu.render(msg,True,C.DARK_ACCENT_INFO); self.fenetre.blit(msg_s,(30,55))
        instr_s=self.font_jeu.render("ESPACE: Suivant | ENTRÉE: Terminer | ESC: Annuler",True,C.DARK_ACCENT_WARN); self.fenetre.blit(instr_s,(30,self.hauteur-instr_s.get_height()-20))
        pygame.display.flip()