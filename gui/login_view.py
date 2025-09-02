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


class LoginView(ctk.CTk):
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
        self.title_bar = ctk.CTkFrame(self, height=35, fg_color="#16161D")
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
            logo_label.pack(side="left", padx=12, pady=6)
        except:
            # Si no se encuentra la imagen del logo, usar solo texto
            pass

        # Nombre de la app
        app_name = ctk.CTkLabel(self.title_bar, text="AMU", font=("Arial", 16, "bold"), text_color="#FFFFFF")
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
        # Frame principal sin padding para ocupar toda la ventana
        main_frame = ctk.CTkFrame(self, fg_color="transparent", corner_radius=0)
        main_frame.pack(fill="both", expand=True)

        # Columna izquierda - Panel de imagen
        left_frame = ctk.CTkFrame(main_frame, fg_color="#2D1B69", corner_radius=0)
        left_frame.pack(side="left", fill="both", expand=True)

        # Crear gradiente de fondo (simulado con frame)
        gradient_frame = ctk.CTkFrame(left_frame, fg_color="#2D1B69", corner_radius=0)
        gradient_frame.pack(fill="both", expand=True)

        # Imagen de fondo
        try:
            pt_image = self._get_patch("gui/img/img/hero1.jpg")
            bg_image = ctk.CTkImage(Image.open(pt_image), size=(500, 650))
            bg_label = ctk.CTkLabel(gradient_frame, image=bg_image, text="")
            bg_label.place(relx=0.5, rely=0.5, anchor="center")
        except:
            # Si no se encuentra la imagen, usar color sólido con texto
            placeholder_label = ctk.CTkLabel(gradient_frame, text="Background Image\n(hero1.jpg)", 
                                           font=("Arial", 16), text_color="#FFFFFF")
            placeholder_label.place(relx=0.5, rely=0.5, anchor="center")

        # Botón volver (esquina superior derecha) - SIN rgba
        back_btn = ctk.CTkButton(gradient_frame, text="← Back to website", 
                                fg_color="#4A4A6A",  # Color sólido en lugar de rgba
                                hover_color="#5A5A7A", 
                                corner_radius=20, width=140, height=32,
                                font=("Arial", 12), text_color="#FFFFFF",
                                border_width=1, border_color="#6A6A8A")
        back_btn.place(relx=0.85, rely=0.08, anchor="center")

        # Contenedor para el texto inferior
        bottom_content = ctk.CTkFrame(gradient_frame, fg_color="transparent")
        bottom_content.place(relx=0.5, rely=0.85, anchor="center")

        # Texto slogan
        slogan = ctk.CTkLabel(bottom_content, text="Capturing Moments,\nCreating Memories",
                              font=("Arial", 28, "bold"), text_color="#FFFFFF",
                              justify="center")
        slogan.pack(pady=(0, 20))

        # Indicadores de página (dots)
        dots_frame = ctk.CTkFrame(bottom_content, fg_color="transparent")
        dots_frame.pack()

        # Crear dots individuales
        dot1 = ctk.CTkFrame(dots_frame, width=8, height=8, corner_radius=4, fg_color="#6A6A8A")
        dot1.pack(side="left", padx=4)

        dot2 = ctk.CTkFrame(dots_frame, width=8, height=8, corner_radius=4, fg_color="#6A6A8A")
        dot2.pack(side="left", padx=4)

        dot3 = ctk.CTkFrame(dots_frame, width=8, height=8, corner_radius=4, fg_color="#FFFFFF")
        dot3.pack(side="left", padx=4)

        # Columna derecha - Formulario
        right_frame = ctk.CTkFrame(main_frame, fg_color="#1A1A1A", corner_radius=0, width=500)
        right_frame.pack(side="right", fill="both", padx=0, pady=0)
        right_frame.pack_propagate(False)

        # Contenedor del formulario con padding
        form_container = ctk.CTkFrame(right_frame, fg_color="transparent")
        form_container.pack(fill="both", expand=True, padx=40, pady=40)

        # Texto superior "Already have an account?"
        login_link_frame = ctk.CTkFrame(form_container, fg_color="transparent")
        login_link_frame.pack(fill="x", pady=(0, 30))

        login_text = ctk.CTkLabel(login_link_frame, text="Already have an account?", 
                                 font=("Arial", 13), text_color="#8B8B8B")
        login_text.pack(side="left")

        # Botón "Log in" SIN hover_color transparent
        login_link = ctk.CTkButton(login_link_frame, text="Log in", 
                                  font=("Arial", 13), text_color="#7C4DFF",
                                  fg_color="transparent", 
                                  # Removido hover_color="transparent" que causaba el error
                                  width=50, height=20)
        login_link.pack(side="left", padx=(5, 0))

        # Título principal
        title = ctk.CTkLabel(form_container, text="Create an account",
                            font=("Arial", 32, "bold"), text_color="#FFFFFF")
        title.pack(pady=(0, 40), anchor="w")

        # Frame para campos de nombre
        name_frame = ctk.CTkFrame(form_container, fg_color="transparent")
        name_frame.pack(fill="x", pady=(0, 20))

        # Campo First name
        self.first_name = ctk.CTkEntry(name_frame, placeholder_text="Fletcher", 
                                      corner_radius=8, height=50, font=("Arial", 14),
                                      fg_color="#2A2A2A", border_color="#3A3A3A",
                                      placeholder_text_color="#6B6B6B")
        self.first_name.pack(side="left", fill="x", expand=True, padx=(0, 10))

        # Campo Last name
        self.last_name = ctk.CTkEntry(name_frame, placeholder_text="Last name", 
                                     corner_radius=8, height=50, font=("Arial", 14),
                                     fg_color="#2A2A2A", border_color="#3A3A3A",
                                     placeholder_text_color="#6B6B6B")
        self.last_name.pack(side="left", fill="x", expand=True)

        # Campo Email
        self.email = ctk.CTkEntry(form_container, placeholder_text="Email", 
                                 corner_radius=8, height=50, font=("Arial", 14),
                                 fg_color="#2A2A2A", border_color="#3A3A3A",
                                 placeholder_text_color="#6B6B6B")
        self.email.pack(fill="x", pady=(0, 20))

        # Frame para campo de contraseña con icono
        password_frame = ctk.CTkFrame(form_container, fg_color="transparent")
        password_frame.pack(fill="x", pady=(0, 25))

        # Campo Password
        self.password = ctk.CTkEntry(password_frame, placeholder_text="Enter your password", 
                                    show="*", corner_radius=8, height=50, font=("Arial", 14),
                                    fg_color="#2A2A2A", border_color="#3A3A3A",
                                    placeholder_text_color="#6B6B6B")
        self.password.pack(side="left", fill="x", expand=True)

        # Botón para mostrar/ocultar contraseña
        eye_btn = ctk.CTkButton(password_frame, text="👁", width=50, height=50,
                               fg_color="transparent", hover_color="#3A3A3A",
                               command=self._toggle_password_visibility,
                               font=("Arial", 16))
        eye_btn.pack(side="right", padx=(10, 0))

        # Checkbox Terms & Conditions
        self.terms_checkbox = ctk.CTkCheckBox(form_container, 
                                             text="I agree to the Terms & Conditions",
                                             font=("Arial", 13), text_color="#CCCCCC",
                                             checkbox_width=18, checkbox_height=18,
                                             corner_radius=4, border_width=2,
                                             fg_color="#7C4DFF", hover_color="#6B3FE6")
        self.terms_checkbox.pack(anchor="w", pady=(0, 30))

        # Botón Create account
        create_btn = ctk.CTkButton(form_container, text="Create account",
                                  fg_color="#7C4DFF", hover_color="#6B3FE6", 
                                  corner_radius=8, height=50, font=("Arial", 16, "bold"))
        create_btn.pack(fill="x", pady=(0, 30))

        # Separador "Or register with"
        separator_frame = ctk.CTkFrame(form_container, fg_color="transparent")
        separator_frame.pack(fill="x", pady=(0, 25))

        # Línea izquierda
        line_left = ctk.CTkFrame(separator_frame, height=1, fg_color="#3A3A3A")
        line_left.pack(side="left", fill="x", expand=True, pady=10)

        # Texto separador
        sep_label = ctk.CTkLabel(separator_frame, text="Or register with", 
                                font=("Arial", 13), text_color="#8B8B8B")
        sep_label.pack(side="left", padx=15)

        # Línea derecha
        line_right = ctk.CTkFrame(separator_frame, height=1, fg_color="#3A3A3A")
        line_right.pack(side="left", fill="x", expand=True, pady=10)

        # Frame para botones sociales
        social_frame = ctk.CTkFrame(form_container, fg_color="transparent")
        social_frame.pack(fill="x")

        # Botón Google
        google_btn = ctk.CTkButton(social_frame, text="🔍 Google", 
                                  fg_color="#FFFFFF", text_color="#000000",
                                  hover_color="#F0F0F0", corner_radius=8, height=45,
                                  font=("Arial", 14, "bold"))
        google_btn.pack(side="left", fill="x", expand=True, padx=(0, 10))

        # Botón Apple
        apple_btn = ctk.CTkButton(social_frame, text="🍎 Apple", 
                                 fg_color="#000000", text_color="#FFFFFF",
                                 hover_color="#1A1A1A", corner_radius=8, height=45,
                                 font=("Arial", 14, "bold"), border_width=1,
                                 border_color="#3A3A3A")
        apple_btn.pack(side="left", fill="x", expand=True)


    # ---------------- Funciones de interacción ---------------- #
    def _toggle_password_visibility(self):
        if self.password_visible:
            self.password.configure(show="*")
            self.password_visible = False
        else:
            self.password.configure(show="")
            self.password_visible = True


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