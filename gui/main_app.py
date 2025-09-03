        
# Importacion de librerias
from utils.loggers import get_logger
from pathlib import Path
from PIL import Image, ImageTk
import customtkinter as ctk
import tkinter as tk
from tkinter import font
import os
import pystray
import threading

# Llamada al log 
logger = get_logger(__name__)

# Predefinimos nuestro thema
get_route_theme = os.path.join(os.path.dirname(__file__), "..", "config", "pydracula.json")
get_route_theme = os.path.normpath(get_route_theme)
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme(get_route_theme)


class MainApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        # Quitar barra nativa de Windows
        self.overrideredirect(True)

        # Tamaño inicial optimizado
        self.geometry("900x650")
        self.normal_geometry = "900x650"
        self.is_maximized = False
        self.tray_icon = None
        self.tray_thread = None

        # Configurar protocilo de cierre
        self.protocol("WM_DELETE_WINDOW", self._minimized_to_dray)

        # Crear barra superior personalizada
        self._title_navbar()
        self._create_ui()

        # Configuracion del system Dray cuando se cierra la ventana
        self.bind("<Destroy>", self._on_destroy)

        # Variables para campos de entrada
        self.password_visible = False


    # ---------------- Barra de navegación ---------------- #
    def _title_navbar(self):
        self.title_bar = ctk.CTkFrame(self, height=25, fg_color="#292934")
        self.title_bar.pack(fill="x", side="top")

        # Logo de la app
        try:
            img_patch = self._get_patch("gui/img/img/logo1.png")
            self.logo = ctk.CTkImage(
                light_image=Image.open(img_patch),
                dark_image=Image.open(img_patch),
                size=(22, 22)
            )
            logo_label = ctk.CTkLabel(self.title_bar, image=self.logo, text="")
            logo_label.pack(side="left", padx=6, pady=6)
        except:
            # Si no se encuentra la imagen del logo, usar solo texto
            pass

        # Nombre de la app
        app_name = ctk.CTkLabel(self.title_bar, text="Xentraders - Logout", font=("Arial", 14, "bold"), text_color="#FFFFFF")
        app_name.pack(side="left", padx=(12 if not hasattr(self, 'logo') else 0, 0))

        # Botones ventana
        try:
            min_ico = self._get_patch("gui/img/icons/icon_minimize.png")
            max_ico = self._get_patch("gui/img/icons/icon_maximize.png")
            close_ico = self._get_patch("gui/img/icons/icon_close.png")

            self.close_icon = ctk.CTkImage(Image.open(close_ico), size=(12, 12))
            close_btn = ctk.CTkButton(self.title_bar, image=self.close_icon, text="",
                                      fg_color="transparent", hover_color="#FF5555", width=35, height=35,
                                      command=self._close_wind, corner_radius=0)
            close_btn.pack(side="right")

            self.max_icon = ctk.CTkImage(Image.open(max_ico), size=(16, 16))
            max_btn = ctk.CTkButton(self.title_bar, image=self.max_icon, text="",
                                    fg_color="transparent", hover_color="#44475A", width=35, height=35,
                                    command=self._toggle_maximized, corner_radius=0)
            max_btn.pack(side="right")

            self.min_icon = ctk.CTkImage(Image.open(min_ico), size=(16, 16))
            min_btn = ctk.CTkButton(self.title_bar, image=self.min_icon, text="",
                                    fg_color="transparent", hover_color="#44475A", width=35, height=35,
                                    command=self._minimized_to_dray, corner_radius=0)
            min_btn.pack(side="right")
        except:
            # Si no se encuentran los iconos, usar botones de texto
            close_btn = ctk.CTkButton(self.title_bar, text="✕", 
                                      fg_color="transparent", hover_color="#FF5555", width=35, height=35,
                                      command=self._close_wind, corner_radius=0, font=("Arial", 12))
            close_btn.pack(side="right")

            max_btn = ctk.CTkButton(self.title_bar, text="□", 
                                    fg_color="transparent", hover_color="#44475A", width=35, height=35,
                                    command=self._toggle_maximized, corner_radius=0, font=("Arial", 12))
            max_btn.pack(side="right")

            min_btn = ctk.CTkButton(self.title_bar, text="−", 
                                    fg_color="transparent", hover_color="#44475A", width=35, height=35,
                                    command=self._minimized_to_dray, corner_radius=0, font=("Arial", 12))
            min_btn.pack(side="right")

        # Mover ventana
        self.title_bar.bind("<Button-1>", self._start_move)
        self.title_bar.bind("<B1-Motion>", self._do_move)

    # ---------------- Contenido principal ---------------- #
    def _create_ui(self):
        self.main_frame = ctk.CTkFrame(self, fg_color="transparent", corner_radius=0)
        self.main_frame.pack(fill="both", expand=True)

        self.notebook = ctk.CTkNotebook(self.main_frame)
        self.notebook.pack(fill="both", expand=True)

        # Crear pestañas directamente con su nombre
        tab1 = self.notebook.add("Inicio")
        tab2 = self.notebook.add("Opciones")
        tab3 = self.notebook.add("Logs")

        # Contenido de cada pestaña
        ctk.CTkLabel(tab1, text="Contenido de Inicio").pack(pady=20)
        ctk.CTkLabel(tab2, text="Aquí van configuraciones").pack(pady=20)
        ctk.CTkLabel(tab3, text="Mensajes y logs").pack(pady=20)
    
    
    # ---------------- Aqui van las funciones de la interface como componnentes ---------------- #
    def _add_tabs(self, root: any, title: str, contend: vars):
       frame = ctk.CTkFrame(self.notebook) 

    # ---------------- Fin de las funciones de la ui ---------------- #
    # ---------------- Eventos de movimiento ventana ---------------- #
    def _start_move(self, event):
        self.x = event.x
        self.y = event.y

    def _do_move(self, event):
        deltax = event.x - self.x
        deltay = event.y - self.y
        self.geometry(f"+{self.winfo_x() + deltax}+{self.winfo_y() + deltay}")


    # ---------------- Eventos de control ventana ---------------- #
    def _close_wind(self):
        if self.tray_icon:
            self.tray_icon.stop()
        self.destroy()

    def _minimized_to_dray(self):
        self.withdraw()
        self._create_system_tray()

    def _create_system_tray(self):
        if self.tray_icon is None:
            try:
                tray_imagen_patch = self._get_patch("gui/img/img/logo1.png")
                tray_image = Image.open(tray_imagen_patch)
                menu = pystray.Menu(
                    pystray.MenuItem("Restaurar", self._restore_from_tray),
                    pystray.MenuItem("Salir", self._close_wind)
                )
                self.tray_icon = pystray.Icon("xentrader", tray_image, "AMU App", menu=menu)
                self.tray_thread = threading.Thread(target=self.tray_icon.run, daemon=True)
                self.tray_thread.start()
            except Exception as e:
                logger.error(f"Error creating system tray: {e}")

    def _restore_from_tray(self):
        if self.tray_icon:
            self.tray_icon.stop()
            self.tray_icon = None
        self.deiconify()
        self.lift()
        self.focus_force()

    def _toggle_maximized(self):
        if self.is_maximized:
            self.geometry(self.normal_geometry)
            self.is_maximized = False
        else:
            self.normal_geometry = self.geometry()
            screen_width = self.winfo_screenwidth()
            screen_height = self.winfo_screenheight()
            self.geometry(f"{screen_width}x{screen_height}+0+0")
            self.is_maximized = True


    # ---------------- Helpers ---------------- #
    def _get_patch(self, relative_patch: str) -> str:
        base_dir = Path(__file__).parent.parent
        full_patch = base_dir / relative_patch
        if not full_patch.exists():
            logger.warning(f"Ruta no encontrada: {full_patch}")
            # Retornar una ruta por defecto o crear un placeholder
            return str(full_patch)
        return str(full_patch)

    def _on_destroy(self, event):
        if self.tray_icon:
            self.tray_icon.stop()

    def run(self):
        self.mainloop()