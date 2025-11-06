import customtkinter as ctk
from tkinter import messagebox
import math

class TooltipLabel(ctk.CTkLabel):
    """Label personnalisé avec tooltip au survol"""
    def __init__(self, master, text, tooltip_text="", **kwargs):
        super().__init__(master, text=text, **kwargs)
        self.tooltip_text = tooltip_text
        self.tooltip = None
        self.hide_job = None
        self.check_job = None
        
        #self.bind("<Enter>", self.show_tooltip)
        #self.bind("<Leave>", self.schedule_hide_tooltip)
    
    def show_tooltip(self, event):
        # Annuler les jobs programmés
        if self.hide_job:
            self.after_cancel(self.hide_job)
            self.hide_job = None
        if self.check_job:
            self.after_cancel(self.check_job)
            self.check_job = None
        
        if self.tooltip_text and not self.tooltip:
            x = self.winfo_rootx() + 20
            y = self.winfo_rooty() + 20
            
            self.tooltip = ctk.CTkToplevel(self)
            self.tooltip.wm_overrideredirect(True)
            self.tooltip.wm_geometry(f"+{x}+{y}")
            
            label = ctk.CTkLabel(
                self.tooltip, 
                text=self.tooltip_text,
                fg_color=("#dbdbdb", "#2b2b2b"),
                corner_radius=6,
                padx=10,
                pady=5
            )
            label.pack()
            
            # Démarrer la vérification de la position de la souris
            self.check_mouse_position()
    
    def check_mouse_position(self):
        """Vérifie si la souris est toujours sur le label"""
        if self.tooltip:
            # Récupérer la position de la souris
            x, y = self.winfo_pointerxy()
            # Récupérer les coordonnées du label
            label_x = self.winfo_rootx()
            label_y = self.winfo_rooty()
            label_width = self.winfo_width()
            label_height = self.winfo_height()
            
            # Vérifier si la souris est sur le label
            if not (label_x <= x <= label_x + label_width and 
                    label_y <= y <= label_y + label_height):
                # La souris n'est plus sur le label, programmer la disparition
                if not self.hide_job:
                    self.hide_job = self.after(150, self.hide_tooltip_now)
            else:
                # La souris est toujours sur le label, vérifier à nouveau
                self.check_job = self.after(50, self.check_mouse_position)
    
    def schedule_hide_tooltip(self, event):
        """Programme la disparition du tooltip après 150ms"""
        if self.tooltip and not self.hide_job:
            self.hide_job = self.after(150, self.hide_tooltip_now)
    
    def hide_tooltip_now(self):
        """Cache immédiatement le tooltip"""
        if self.tooltip:
            self.tooltip.destroy()
            self.tooltip = None
        if self.check_job:
            self.after_cancel(self.check_job)
            self.check_job = None
        self.hide_job = None


class UEFrame(ctk.CTkFrame):
    """Frame pour une UE avec champs de saisie"""
    def __init__(self, master, numero, **kwargs):
        super().__init__(master, **kwargs)
        self.numero = numero
        
        # Nom de l'UE
        self.label_nom = TooltipLabel(
            self, 
            text=f"UE {numero}:",
            tooltip_text="Nom de l'unité d'enseignement",
            font=("Roboto", 12, "bold")
        )
        self.label_nom.grid(row=0, column=0, padx=10, pady=5, sticky="w")
        
        self.entry_nom = ctk.CTkEntry(self, placeholder_text="Ex: Mathématiques", width=200)
        self.entry_nom.grid(row=0, column=1, padx=10, pady=5)
        
        # Niveau de lacunes
        self.label_lacunes = TooltipLabel(
            self,
            text="Lacunes:",
            tooltip_text="Évaluez vos difficultés : 1 (peu) → 5 (beaucoup)",
            font=("Roboto", 11)
        )
        self.label_lacunes.grid(row=0, column=2, padx=10, pady=5)
        
        self.slider_lacunes = ctk.CTkSlider(
            self, 
            from_=1, 
            to=5, 
            number_of_steps=4,
            width=120
        )
        self.slider_lacunes.set(3)
        self.slider_lacunes.grid(row=0, column=3, padx=10, pady=5)
        
        self.value_lacunes = ctk.CTkLabel(self, text="3", font=("Roboto", 11, "bold"))
        self.value_lacunes.grid(row=0, column=4, padx=5, pady=5)
        self.slider_lacunes.configure(command=self.update_lacunes)
        
        # Pourcentage examen
        self.label_pourcentage = TooltipLabel(
            self,
            text="% Examen:",
            tooltip_text="Poids de l'examen dans la note finale de l'UE",
            font=("Roboto", 11)
        )
        self.label_pourcentage.grid(row=0, column=5, padx=10, pady=5)
        
        self.entry_pourcentage = ctk.CTkEntry(self, placeholder_text="70", width=60)
        self.entry_pourcentage.grid(row=0, column=6, padx=5, pady=5)
        
        self.label_pct = ctk.CTkLabel(self, text="%", font=("Roboto", 11))
        self.label_pct.grid(row=0, column=7, padx=5, pady=5)
    
    def update_lacunes(self, value):
        self.value_lacunes.configure(text=str(int(value)))
    
    def get_data(self):
        """Récupère les données de l'UE"""
        try:
            nom = self.entry_nom.get().strip()
            if not nom:
                raise ValueError(f"Le nom de l'UE {self.numero} est vide")
            
            lacunes = int(self.slider_lacunes.get())
            
            pourcentage = self.entry_pourcentage.get().strip()
            if not pourcentage:
                raise ValueError(f"Le pourcentage pour '{nom}' est vide")
            pourcentage = int(pourcentage)
            
            if not (0 <= pourcentage <= 100):
                raise ValueError(f"Le pourcentage pour '{nom}' doit être entre 0 et 100")
            
            return {
                'nom': nom,
                'lacunes': lacunes,
                'pourcentage': pourcentage
            }
        except ValueError as e:
            raise ValueError(str(e))


class ResultFrame(ctk.CTkFrame):
    """Frame pour afficher un résultat d'UE"""
    def __init__(self, master, ue_data, max_priorite, **kwargs):
        super().__init__(master, **kwargs)
        
        # Calcul de la couleur en fonction de la priorité
        couleur = self.get_color_for_priority(ue_data['priorite'], max_priorite)
        self.configure(fg_color=couleur, corner_radius=10)
        
        # Rang
        rang_label = ctk.CTkLabel(
            self,
            text=f"#{ue_data['rang']}",
            font=("Roboto", 24, "bold"),
            text_color="white"
        )
        rang_label.grid(row=0, column=0, rowspan=2, padx=20, pady=10)
        
        # Nom UE
        nom_label = ctk.CTkLabel(
            self,
            text=ue_data['nom'],
            font=("Roboto", 16, "bold"),
            text_color="white"
        )
        nom_label.grid(row=0, column=1, sticky="w", padx=10, pady=(10, 0))
        
        # Détails
        details = f"Lacunes: {ue_data['lacunes']}/5  •  Examen: {ue_data['pourcentage']}%  •  Score: {ue_data['priorite']}"
        details_label = TooltipLabel(
            self,
            text=details,
            tooltip_text=f"Priorité calculée : {ue_data['priorite']}\nPlus le score est élevé, plus la révision est prioritaire",
            font=("Roboto", 11),
            text_color="white"
        )
        details_label.grid(row=1, column=1, sticky="w", padx=10, pady=(0, 5))
        
        # Heures recommandées
        heures_label = ctk.CTkLabel(
            self,
            text=f"⏱️  {ue_data['heures_recommandees']}h recommandées",
            font=("Roboto", 12, "bold"),
            text_color="white"
        )
        heures_label.grid(row=0, column=2, rowspan=2, padx=20, pady=10)
        
        # Configuration de la grille
        self.grid_columnconfigure(1, weight=1)
    
    def get_color_for_priority(self, priorite, max_priorite):
        """Calcule la couleur en fonction de la priorité (bleu → rouge)"""
        if max_priorite == 0:
            ratio = 0
        else:
            ratio = priorite / max_priorite
        
        # Interpolation de bleu (#2E86AB) à rouge foncé (#A4031F)
        r = int(46 + (164 - 46) * ratio)
        g = int(134 + (3 - 134) * ratio)
        b = int(171 + (31 - 171) * ratio)
        
        return f"#{r:02x}{g:02x}{b:02x}"


class RevisionApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        # Configuration de la fenêtre
        self.title("📚 Gestionnaire de Priorités de Révision")
        self.geometry("1000x750")
        
        # Thème
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        
        # Nombre d'UE
        self.nb_ue = 5
        self.ue_frames = []
        
        self.create_widgets()
    
    def create_widgets(self):
        # En-tête
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=20, pady=20)
        
        title = ctk.CTkLabel(
            header,
            text="📚 Gestionnaire de Priorités de Révision",
            font=("Roboto", 28, "bold")
        )
        title.pack()
        
        subtitle = ctk.CTkLabel(
            header,
            text="Organisez vos révisions en fonction de vos lacunes et du poids des examens",
            font=("Roboto", 12),
            text_color="gray"
        )
        subtitle.pack(pady=(5, 0))
        
        # Frame de saisie (scrollable)
        self.scroll_frame = ctk.CTkScrollableFrame(self, label_text="📝 Vos UE à réviser")
        self.scroll_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        # Nombre d'UE et heures disponibles
        config_frame = ctk.CTkFrame(self.scroll_frame)
        config_frame.pack(fill="x", padx=10, pady=10)
        
        # Nombre d'UE
        nb_label = TooltipLabel(
            config_frame,
            text="Nombre d'UE:",
            tooltip_text="Combien d'unités d'enseignement devez-vous réviser ?",
            font=("Roboto", 12, "bold")
        )
        nb_label.grid(row=0, column=0, padx=10, pady=5)
        
        self.nb_entry = ctk.CTkEntry(config_frame, placeholder_text="5", width=60)
        self.nb_entry.insert(0, "5")
        self.nb_entry.grid(row=0, column=1, padx=5, pady=5)
        
        update_btn = ctk.CTkButton(
            config_frame,
            text="Actualiser",
            command=self.update_ue_fields,
            width=100
        )
        update_btn.grid(row=0, column=2, padx=10, pady=5)
        
        # Heures disponibles
        heures_label = TooltipLabel(
            config_frame,
            text="Heures disponibles:",
            tooltip_text="Nombre total d'heures que vous pouvez consacrer aux révisions",
            font=("Roboto", 12, "bold")
        )
        heures_label.grid(row=0, column=3, padx=(30, 10), pady=5)
        
        self.heures_entry = ctk.CTkEntry(config_frame, placeholder_text="40", width=60)
        self.heures_entry.insert(0, "40")
        self.heures_entry.grid(row=0, column=4, padx=5, pady=5)
        
        heures_unit = ctk.CTkLabel(config_frame, text="heures", font=("Roboto", 11))
        heures_unit.grid(row=0, column=5, padx=5, pady=5)
        
        # Conteneur des UE
        self.ue_container = ctk.CTkFrame(self.scroll_frame)
        self.ue_container.pack(fill="both", expand=True, padx=10, pady=10)
        
        self.create_ue_fields(self.nb_ue)
        
        # Bouton de calcul
        calc_btn = ctk.CTkButton(
            self,
            text="🎯 Calculer les priorités",
            command=self.calculer_priorites,
            height=40,
            font=("Roboto", 14, "bold")
        )
        calc_btn.pack(pady=20)
    
    def create_ue_fields(self, nombre):
        """Crée les champs pour saisir les UE"""
        # Nettoyer les anciens champs
        for frame in self.ue_frames:
            frame.destroy()
        self.ue_frames.clear()
        
        # Créer les nouveaux champs
        for i in range(1, nombre + 1):
            ue_frame = UEFrame(self.ue_container, i, fg_color=("#E0E0E0", "#2b2b2b"), corner_radius=10)
            ue_frame.pack(fill="x", padx=5, pady=5)
            self.ue_frames.append(ue_frame)
    
    def update_ue_fields(self):
        """Met à jour le nombre de champs UE"""
        try:
            nb = int(self.nb_entry.get())
            if nb <= 0:
                messagebox.showerror("Erreur", "Le nombre d'UE doit être positif")
                return
            if nb > 20:
                messagebox.showerror("Erreur", "Maximum 20 UE")
                return
            self.nb_ue = nb
            self.create_ue_fields(nb)
        except ValueError:
            messagebox.showerror("Erreur", "Veuillez entrer un nombre valide")
    
    def repartir_heures(self, ue_liste, heures_totales):
        """Répartit les heures proportionnellement aux scores de priorité"""
        somme_priorites = sum(ue['priorite'] for ue in ue_liste)
        
        if somme_priorites == 0:
            # Si toutes les priorités sont à 0, répartir équitablement
            heures_par_ue = heures_totales / len(ue_liste)
            for ue in ue_liste:
                ue['heures_recommandees'] = round(heures_par_ue, 1)
        else:
            # Répartir proportionnellement aux priorités
            heures_restantes = heures_totales
            for i, ue in enumerate(ue_liste):
                if i == len(ue_liste) - 1:
                    # Dernière UE : lui donner ce qui reste pour éviter les erreurs d'arrondi
                    ue['heures_recommandees'] = round(heures_restantes, 1)
                else:
                    heures = (ue['priorite'] / somme_priorites) * heures_totales
                    ue['heures_recommandees'] = round(heures, 1)
                    heures_restantes -= ue['heures_recommandees']
    
    def calculer_priorites(self):
        """Calcule et affiche les priorités"""
        try:
            # Récupérer le nombre d'heures disponibles
            heures_totales = float(self.heures_entry.get())
            if heures_totales <= 0:
                messagebox.showerror("Erreur", "Le nombre d'heures doit être positif")
                return
            
            # Récupérer les données
            ue_liste = []
            for ue_frame in self.ue_frames:
                data = ue_frame.get_data()
                # Calcul de la priorité
                priorite = (data['lacunes'] * 10) + (data['pourcentage'] / 10)
                data['priorite'] = round(priorite, 1)
                ue_liste.append(data)
            
            # Trier par priorité
            ue_liste_triee = sorted(ue_liste, key=lambda x: x['priorite'], reverse=True)
            
            # Répartir les heures
            self.repartir_heures(ue_liste_triee, heures_totales)
            
            # Ajouter le rang
            for i, ue in enumerate(ue_liste_triee, 1):
                ue['rang'] = i
            
            # Afficher les résultats
            self.afficher_resultats(ue_liste_triee, heures_totales)
            
        except ValueError as e:
            messagebox.showerror("Erreur de saisie", str(e))
    
    def afficher_resultats(self, ue_liste, heures_totales):
        """Affiche les résultats dans une nouvelle fenêtre"""
        result_window = ctk.CTkToplevel(self)
        result_window.title("🎯 Résultats - Priorités de Révision")
        result_window.geometry("900x650")
        
        # En-tête
        header = ctk.CTkFrame(result_window, fg_color="transparent")
        header.pack(fill="x", padx=20, pady=20)
        
        title = ctk.CTkLabel(
            header,
            text="🎯 Vos Priorités de Révision",
            font=("Roboto", 24, "bold")
        )
        title.pack()
        
        info_frame = ctk.CTkFrame(header, fg_color="transparent")
        info_frame.pack(pady=(5, 0))
        
        legende = ctk.CTkLabel(
            info_frame,
            text="🔵 Faible priorité → 🔴 Haute priorité",
            font=("Roboto", 11),
            text_color="gray"
        )
        legende.pack(side="left", padx=10)
        
        total_heures = ctk.CTkLabel(
            info_frame,
            text=f"⏱️  Total: {heures_totales}h de révision",
            font=("Roboto", 11, "bold"),
            text_color="gray"
        )
        total_heures.pack(side="left", padx=10)
        
        # Frame scrollable pour les résultats
        scroll = ctk.CTkScrollableFrame(result_window)
        scroll.pack(fill="both", expand=True, padx=20, pady=10)
        
        # Trouver la priorité max
        max_priorite = max(ue['priorite'] for ue in ue_liste) if ue_liste else 1
        
        # Afficher chaque UE
        for ue in ue_liste:
            result_frame = ResultFrame(scroll, ue, max_priorite)
            result_frame.pack(fill="x", padx=10, pady=8)
        
        # Conseils
        conseil_frame = ctk.CTkFrame(result_window, fg_color=("#E8F4F8", "#1a3a4a"), corner_radius=10)
        conseil_frame.pack(fill="x", padx=20, pady=(10, 20))
        
        conseil_title = ctk.CTkLabel(
            conseil_frame,
            text="💡 Conseil",
            font=("Roboto", 12, "bold")
        )
        conseil_title.pack(anchor="w", padx=15, pady=(10, 5))
        
        conseil_text = ctk.CTkLabel(
            conseil_frame,
            text="Concentrez votre temps de révision sur les UE en rouge/orange (scores élevés).\n"
                 "Les heures sont réparties proportionnellement à l'importance de chaque UE.\n"
                 "N'oubliez pas de faire des pauses régulières ! 🎓",
            font=("Roboto", 11),
            justify="left"
        )
        conseil_text.pack(anchor="w", padx=15, pady=(0, 10))


if __name__ == "__main__":
    app = RevisionApp()
    app.mainloop()