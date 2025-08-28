# Arranque de interfaces

# Importacion de librerias
import tkinter as tk
from tkinter import ttk
from utils.loggers import get_logger

# Configuracion de envios de logs
logger = get_logger(__name__)

# Clase principal 
class MainApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Xentrader Bot - PyDracula (paso 1)")
        self.root.geometry("900x600")
        self.root.configure(bg="#1e1e2e")

        # Un pequeño log de prueba
        logger.info("Aplicacion iniciada con exito")
        
        # Notebook como navegacion 
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill="both", expand=True)

        # Creacion de pestañas basias
        self._add_tab("Dashboard")
        self._add_tab("Manual Trading")
        self._add_tab("Auto Trading")
        self._add_tab("Charts")
        self._add_tab("Logs")


    # Sub funciones de la clase
    # Funcion privada para crear pestañas 
    def _add_tab(self, title):
        frame  = tk.Frame(self.notebook, bg="#2a2a40")
        self.notebook.add(frame, text=title)

    # Funcion para correr interface
    def run(self):
        self.root.mainloop()
        
