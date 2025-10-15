# pages/dashboard_view.py

import customtkinter as ctk
from PIL import Image
import os
from pathlib import Path

class DashboardView(ctk.CTkFrame):
    def __init__(self, parent, balance, profit_loss, open_positions):
        super().__init__(parent, fg_color="transparent")
        
        # Configurar grid layout principal
        self.main_frame = ctk.CTkFrame(self, fg_color="#7757C8")
        self.main_frame.pack(fill="both", expand=True)

        # Secion de tikers
        self.section_tikers()
        self.section_metadata()
        self.section_metrics()
    
    def section_tikers(self):
        box_tikers = ctk.CTkFrame(self.main_frame, border_width=0, corner_radius=0, fg_color="transparent")
        box_tikers.pack(fill="x", pady=10)

        # Live tikers
        lv_1 = ctk.CTkFrame(box_tikers, fg_color="#0B1D2C")
        lv_1.pack(side="left", expand=True, fill="both", padx=10)
        # Título
        title_label = ctk.CTkLabel(
            lv_1,
            text="🎫 Live Tickets",
            font=("Segoe UI", 17, "bold"),
            text_color="#69A2FE"
        )
        title_label.pack(pady=(15, 10), side="top", padx=15)

        # Tickets principales
        fr=ctk.CTkFrame(lv_1, height=50, fg_color="transparent")
        fr.pack(fill="x", padx=20)
        fr2=ctk.CTkFrame(lv_1, height=50, fg_color="transparent")
        fr2.pack(fill="x", padx=20)

        ctk.CTkLabel(
            fr,
            text="23",
            font=("Segoe UI", 26, "bold"),
            text_color="#CDD6F4"
        ).pack(side="left",padx=5)
        ctk.CTkLabel(
            fr,
            text="Operaciones abiertas",
            font=("Segoe UI", 16),
            text_color="#7E83A3"
        ).pack(side="left",padx=(5, 0))

        # Tickets no asignados
        ctk.CTkLabel(
            fr2,
            text="16",
            font=("Segoe UI", 22, "bold"),
            text_color="#F38BA8"
        ).pack(side="left", padx=5)
        
        ctk.CTkLabel(
            fr2,
            text="Cerradas",
            font=("Segoe UI", 16),
            text_color="#7E83A3"
        ).pack(side="left", padx=(6,0))

        lv_2 = ctk.CTkFrame(box_tikers, fg_color="#0B1D2C")
        lv_2.pack(side="left", expand=True, fill="both")
        lv_3 = ctk.CTkFrame(box_tikers, fg_color="#0B1D2C")
        lv_3.pack(side="left", expand=True, fill="both", padx=10)
    
    def section_metadata(self):
        box_tikers = ctk.CTkFrame(self.main_frame, border_width=0, corner_radius=0)
        box_tikers.pack(fill="x")
    
    def section_metrics(self):
        box_tikers = ctk.CTkFrame(self.main_frame, border_width=0, corner_radius=0)
        box_tikers.pack(fill="x")