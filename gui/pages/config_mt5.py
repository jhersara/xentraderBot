# Codigo para las configuraciones necesarias de mt5
# pages/config_mt5.py

import customtkinter as ctk

class ConfigMT5Page(ctk.CTkFrame):
    def __init__(self, parent ):
        super().__init__(parent, fg_color="transparent")

        label = ctk.CTkLabel(self, text="Configuraciones de MT5",font=("Segoe UI", 20, "bold"))
        label.pack(pady=20)

        # Ejemplo de campo
        entry = ctk.CTkEntry(self, placeholder_text="Servidor MT5")
        entry.pack(pady=10)

        save_btn = ctk.CTkButton(self, text="Guardar configuración", command=lambda: print("Guardado!"))
        save_btn.pack(pady=10)