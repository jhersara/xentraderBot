# Importacion de librerias
from utils.loggers import get_logger
from utils.auth import sign_in, sign_up, sign_in_with_provider
from pathlib import Path
from PIL import Image, ImageTk
import customtkinter as ctk
from typing import Callable, Optional
import tkinter as tk
from tkinter import font
import os
import pystray
import threading

# Variables de desarrollo
x = "x"
y = "y"
left = "left"
right = "right"

# Llamada al log 
logger = get_logger(__name__)

# Predefinimos nuestro thema
get_route_theme = os.path.join(os.path.dirname(__file__), "..", "config", "pydracula.json")
get_route_theme = os.path.normpath(get_route_theme)
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme(get_route_theme)


class LoginView(ctk.CTk):
    def __init__(self, on_login_sucess: Callable = None):
        super().__init__()

        # Guardar el Callback 
        self.on_login_sucess = on_login_sucess

        # Quitar barra nativa de Windows
        self.overrideredirect(True)

        # Tamaño inicial optimizado
        self.geometry("900x650")
        self.normal_geometry = "900x650"
        self.resizable(None, None)
        self.is_maximized = False
        self.tray_icon = None
        self.tray_thread = None

        # Configurar protocilo de cierre
        self.protocol("WM_DELETE_WINDOW", self._minimized_to_dray)

        # Variables para campos de entrada
        self.password_visible = False
        self.login = True

        # Crear barra superior personalizada
        self._title_navbar()
        self._create_ui()

        # Configuracion del system Dray cuando se cierra la ventana
        self.bind("<Destroy>", self._on_destroy)

        # Variables de desarrollo dentro de funciones


        


    # ---------------- Barra de navegación ---------------- #
    def _title_navbar(self):
        self.title_bar = ctk.CTkFrame(self, height=30, fg_color="#323243", border_width=0, corner_radius=0)
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
            logo_label.pack(side="left", pady=4)
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
                                      fg_color="transparent", hover_color="#FF5555", width=35, height=30,
                                      command=self._close_wind, corner_radius=0)
            close_btn.pack(side="right")

            self.max_icon = ctk.CTkImage(Image.open(max_ico), size=(16, 16))
            max_btn = ctk.CTkButton(self.title_bar, image=self.max_icon, text="",
                                    fg_color="transparent", hover_color="#44475A", width=35, height=30,
                                    command=self._toggle_maximized, corner_radius=0)
            max_btn.pack(side="right")

            self.min_icon = ctk.CTkImage(Image.open(min_ico), size=(16, 16))
            min_btn = ctk.CTkButton(self.title_bar, image=self.min_icon, text="",
                                    fg_color="transparent", hover_color="#44475A", width=35, height=30,
                                    command=self._minimized_to_dray, corner_radius=0)
            min_btn.pack(side="right")
        except:
            # Si no se encuentran los iconos, usar botones de texto
            close_btn = ctk.CTkButton(self.title_bar, text="✕", 
                                      fg_color="transparent", hover_color="#FF5555", width=35, height=30,
                                      command=self._close_wind, corner_radius=0, font=("Arial", 12))
            close_btn.pack(side="right")

            max_btn = ctk.CTkButton(self.title_bar, text="□", 
                                    fg_color="transparent", hover_color="#44475A", width=35, height=30,
                                    command=self._toggle_maximized, corner_radius=0, font=("Arial", 12))
            max_btn.pack(side="right")

            min_btn = ctk.CTkButton(self.title_bar, text="−", 
                                    fg_color="transparent", hover_color="#44475A", width=35, height=30,
                                    command=self._minimized_to_dray, corner_radius=0, font=("Arial", 12))
            min_btn.pack(side="right")

        # Mover ventana
        self.title_bar.bind("<Button-1>", self._start_move)
        self.title_bar.bind("<B1-Motion>", self._do_move)


    # ---------------- Contenido principal ---------------- #
    def _create_ui(self):
        # Frame principal sin padding para ocupar toda la ventana
        main_frame = ctk.CTkFrame(self, corner_radius=0)
        main_frame.pack(fill="both", expand=True, pady=0, padx=0)

        if self.login == False:
            # Columna izquierdo - Panel de imagen
            left_frame = ctk.CTkFrame(main_frame, corner_radius=0, width=400, fg_color="transparent")
            left_frame.pack(side="left", fill="y", padx=0, pady=0)
            left_frame.pack_propagate(False)

            # Imagen de portada Proximamente un carrusel
            try:
                hr_img = self._get_patch("gui/img/img/hero2.jpg")
                bg_img = ctk.CTkImage(Image.open(hr_img), size=(320, 620))
                bg_label = ctk.CTkLabel(left_frame, image=bg_img, text="", corner_radius=15)
                bg_label.pack(expand=True, fill="y", pady=0, padx=0)
            except:
                # En caso de que no encuentre la imagen
                placeholder_label= ctk.CTkLabel(left_frame, text="Background Image\n(hero1.jpg)", font=("Arial", 16), text_color="#FFFFFF")
                placeholder_label.place(relx=0.5, rely=0.5, anchor="center")



            # Columna Derecha - Panel de formulario
            right_frame = ctk.CTkFrame(main_frame, fg_color="#1A1A1A", corner_radius=10)
            right_frame.pack(side="right", expand=True, fill="both", pady=(10,10))
            right_frame.pack_propagate(False)

            # Contenedor del fromulario con padding
            form_ctn = ctk.CTkFrame(right_frame, fg_color="transparent")
            form_ctn.pack(fill="both", expand=True, pady=20, padx=40)

            # Texto de si se tiene una cuenta
            login_link_fm = ctk.CTkFrame(form_ctn, fg_color="transparent")
            login_link_fm.pack(fill="x", pady=(0,30))

            login_link_txt = ctk.CTkLabel(login_link_fm, text="¿Ya tienes una cuenta?", font=("Arial", 13), text_color="#8B8B8B")
            login_link_txt.pack(side="left")

            # Botón "Log in" SIN hover_color transparent
            login_link_btn = ctk.CTkButton(login_link_fm, text="Ingresar.", font=("Arial", 13, "bold"), fg_color="transparent", text_color="#7C4DFF",text_color_disabled="#ffffff", width=50, height=20, hover_color="#272727", command=self._mode_login)
            login_link_btn.pack(padx=(5,0), side="left")

            # Titulo principal
            title_frame = ctk.CTkLabel(form_ctn, text="Crear una Cuenta", font=("Arial", 28, "bold"), text_color="#FFFFFF")
            title_frame.pack(anchor="w", pady=(0,10))

            # Frame para campos de nombre
            name_fm = ctk.CTkFrame(form_ctn, fg_color="transparent")
            name_fm.pack(fill=x,  pady=(0, 20))

            # Campos de nombres 
            self.first_name = ctk.CTkEntry(name_fm, placeholder_text="Primer Nombre",corner_radius=8, height=40, font=("Arial", 14, "bold"), fg_color="#2A2A2A", border_color="#3A3A3A", placeholder_text_color="#6B6B6B")
            self.first_name.pack(side=left, fill=x, expand=True, padx=(0, 10))
            self.last_name = ctk.CTkEntry(name_fm, placeholder_text="Segundo Nombre",corner_radius=8, height=40, font=("Arial", 14, "bold"), fg_color="#2A2A2A", border_color="#3A3A3A", placeholder_text_color="#6B6B6B")
            self.last_name.pack(side=left, fill=x, expand=True)

            # Campo del email
            self.email = ctk.CTkEntry(form_ctn, placeholder_text="Email",corner_radius=8, height=40, font=("Arial", 14, "bold"), fg_color="#2A2A2A", border_color="#3A3A3A", placeholder_text_color="#6B6B6B")
            self.email.pack(fill=x, pady=(0,15))
            self.email_verify = ctk.CTkEntry(form_ctn, placeholder_text="Confirmar Email",corner_radius=8, height=40, font=("Arial", 14, "bold"), fg_color="#2A2A2A", border_color="#3A3A3A", placeholder_text_color="#6B6B6B")
            self.email_verify.pack(fill=x, pady=(0, 20))

            # Frame para el campo de contraseña mas icono
            password_fm = ctk.CTkFrame(form_ctn, fg_color="transparent")
            password_fm.pack(fill=x, pady=(0, 20))

            self.password = ctk.CTkEntry(password_fm, placeholder_text="Contraseña:", show="*", corner_radius=8, height=40, font=("Arial", 14, "bold"), fg_color="#2A2A2A", border_color="#3A3A3A", placeholder_text_color="#6B6B6B")
            self.password.pack(side=left, fill=x, expand=True, padx=(0,10))
            self.password_confirm = ctk.CTkEntry(password_fm, placeholder_text="Repetir Contraseña:", show="*", corner_radius=8, height=40, font=("Arial", 14, "bold"), fg_color="#2A2A2A", border_color="#3A3A3A", placeholder_text_color="#6B6B6B")
            self.password_confirm.pack(side=left, fill=x, expand=True, padx=(0,10))

            # Seccion para el boton de ver u ocultar
            uri_patch = self._get_patch("gui/img/icons/cil-lock-unlocked.png")
            uri_patch2 = self._get_patch("gui/img/icons/cil-lock-locked.png")
            self.view_unable = ctk.CTkImage(Image.open(uri_patch2), size=(20, 20))
            self.view_enable = ctk.CTkImage(Image.open(uri_patch), size=(20, 20))
            self.eye_btn = ctk.CTkButton(password_fm,image=self.view_enable, text="", width=40, height=40, fg_color="transparent", hover_color="#3A3A3A", corner_radius=10, command=self._toggle_password_visibility)
            self.eye_btn.pack(side=right)
    
            # CheckBox Terms & Condiction
            self.terms_check = ctk.CTkCheckBox(form_ctn, text="Estoy de acuerdo con los Términos y Condiciones", font=("Arial", 13), text_color="#CCCCCC", checkbox_width=18, checkbox_height=18, corner_radius=4, border_width=2, fg_color="#7C4DFF", hover_color="#6B3FE6", border_color="#CCCCCC")
            self.terms_check.pack(anchor="w", pady=(0, 25))

            # Boton de crear cuenta
            self.send_btn = ctk.CTkButton(form_ctn, text="Crear Cuenta",fg_color="#7C4DFF", hover_color="#6B3FE6", corner_radius=8, height=40, font=("Arial", 16, "bold") )
            self.send_btn.pack(fill=x, pady=(0, 25))
            self.send_btn.configure(command=self._on_create_account)

            # Separador "Or register Width "
            separate_fm = ctk.CTkFrame(form_ctn, fg_color="transparent")
            separate_fm.pack(fill=x, pady=(0,25))

            # Linea Izquierda 
            ln_left = ctk.CTkFrame(separate_fm, height=2, fg_color="#3A3A3A")
            ln_left.pack(side=left, fill=x, expand=True, pady=10)

            # Texto separador
            sep_label = ctk.CTkLabel(separate_fm, text="Or register with", font=("Arial", 16), text_color="#8B8B8B")
            sep_label.pack(side="left", padx=10)

            ln_right = ctk.CTkFrame(separate_fm, height=2, fg_color="#3A3A3A")
            ln_right.pack(side=right, fill=x, expand=True, pady=10)

            # Frame para botones de redes sociales
            social_fm = ctk.CTkFrame(form_ctn, fg_color="transparent")
            social_fm.pack(fill=x)

            # Imagenes de facebook e Google
            uri_patch = self._get_patch("gui/img/png/google.png")
            uri_patch2 = self._get_patch("gui/img/png/facebook.png")
            self.google_img = ctk.CTkImage(Image.open(uri_patch), size=(40, 40))
            self.facebook_img = ctk.CTkImage(Image.open(uri_patch2), size=(40, 40))

            # Boton de Google
            self.google_btn = ctk.CTkButton(social_fm, image=self.google_img, text="Google", fg_color="#FFFFFF", text_color="#000000", hover_color="#D3CFFB", corner_radius=8, height=40, font=("Arial", 14, "bold"), border_width=1, border_color="#3A3A3A")
            self.google_btn.pack(side=left, fill=x, expand=True, padx=(0, 10))
            self.google_btn.configure(command=lambda: sign_in_with_provider("google"))


            # Boton de Facebook
            self.facebook_btn = ctk.CTkButton(social_fm, image=self.facebook_img, text="Facebook", fg_color="#FFFFFF", text_color="#000000", hover_color="#D3CFFB", corner_radius=8, height=40, font=("Arial", 14, "bold"),  border_width=1, border_color="#3A3A3A")
            self.facebook_btn.pack(side=left, fill=x, expand=True)
            self.facebook_btn.configure(command=lambda: sign_in_with_provider("facebook"))

        else:
            # Columna izquierdo - Panel de imagen
            left_frame = ctk.CTkFrame(main_frame, corner_radius=0, width=400, fg_color="transparent")
            left_frame.pack(side="left", fill="y", padx=0, pady=0)
            left_frame.pack_propagate(False)

            # Imagen de portada Proximamente un carrusel
            try:
                hr_img = self._get_patch("gui/img/img/hero2.jpg")
                bg_img = ctk.CTkImage(Image.open(hr_img), size=(320, 620))
                bg_label = ctk.CTkLabel(left_frame, image=bg_img, text="", corner_radius=15)
                bg_label.pack(expand=True, fill="y", pady=0, padx=0)
            except:
                # En caso de que no encuentre la imagen
                placeholder_label= ctk.CTkLabel(left_frame, text="Background Image\n(hero1.jpg)", font=("Arial", 16), text_color="#FFFFFF")
                placeholder_label.place(relx=0.5, rely=0.5, anchor="center")



            # Columna Derecha - Panel de formulario
            right_frame = ctk.CTkFrame(main_frame, fg_color="#1A1A1A", corner_radius=10)
            right_frame.pack(side="right", expand=True, fill="both", pady=(10,10))
            right_frame.pack_propagate(False)

            # Contenedor del fromulario con padding
            form_ctn = ctk.CTkFrame(right_frame, fg_color="transparent")
            form_ctn.pack(fill="both", expand=True, pady=20, padx=40)

            # Texto de si se tiene una cuenta
            login_link_fm = ctk.CTkFrame(form_ctn, fg_color="transparent")
            login_link_fm.pack(fill="x", pady=(0,30))

            login_link_txt = ctk.CTkLabel(login_link_fm, text="¿Aun no tienes una cuenta?", font=("Arial", 13), text_color="#8B8B8B")
            login_link_txt.pack(side="left")

            # Botón "Log in" SIN hover_color transparent
            login_link_btn = ctk.CTkButton(login_link_fm, text="Crear.", font=("Arial", 13, "bold"), fg_color="transparent", text_color="#7C4DFF",text_color_disabled="#ffffff", width=50, height=20, hover_color="#272727", command=self._mode_login)
            login_link_btn.pack(padx=(5,0), side="left")

            # Titulo principal
            title_frame = ctk.CTkLabel(form_ctn, text="Ingresar ", font=("Arial", 28, "bold"), text_color="#FFFFFF")
            title_frame.pack(anchor="w", pady=(0,10))

            # Frame para campos de nombre
            name_fm = ctk.CTkFrame(form_ctn, fg_color="transparent")
            name_fm.pack(fill=x,  pady=(0, 20))

            # Campos de nombres 
            self.first_name = ctk.CTkEntry(name_fm, placeholder_text="Usuario: ",corner_radius=8, height=40, font=("Arial", 14, "bold"), fg_color="#2A2A2A", border_color="#3A3A3A", placeholder_text_color="#6B6B6B")
            self.first_name.pack(side=left, fill=x, expand=True, padx=(0, 10))

            # Campo del email
            self.email = ctk.CTkEntry(form_ctn, placeholder_text="Email",corner_radius=8, height=40, font=("Arial", 14, "bold"), fg_color="#2A2A2A", border_color="#3A3A3A", placeholder_text_color="#6B6B6B")
            self.email.pack(fill=x, pady=(0,15))

            # Frame para el campo de contraseña mas icono
            password_fm = ctk.CTkFrame(form_ctn, fg_color="transparent")
            password_fm.pack(fill=x, pady=(0, 20))

            self.password = ctk.CTkEntry(password_fm, placeholder_text="Contraseña:", show="*", corner_radius=8, height=40, font=("Arial", 14, "bold"), fg_color="#2A2A2A", border_color="#3A3A3A", placeholder_text_color="#6B6B6B")
            self.password.pack(side=left, fill=x, expand=True, padx=(0,10))

            # Seccion para el boton de ver u ocultar
            uri_patch = self._get_patch("gui/img/icons/cil-lock-unlocked.png")
            uri_patch2 = self._get_patch("gui/img/icons/cil-lock-locked.png")
            self.view_unable = ctk.CTkImage(Image.open(uri_patch2), size=(20, 20))
            self.view_enable = ctk.CTkImage(Image.open(uri_patch), size=(20, 20))
            self.eye_btn = ctk.CTkButton(password_fm,image=self.view_enable, text="", width=40, height=40, fg_color="transparent", hover_color="#3A3A3A", corner_radius=10, command=self._toggle_password_visibility)
            self.eye_btn.pack(side=right)

            # Boton de crear cuenta
            self.send_btn = ctk.CTkButton(form_ctn, text="Ingresar",fg_color="#7C4DFF", hover_color="#6B3FE6", corner_radius=8, height=40, font=("Arial", 16, "bold") )
            self.send_btn.pack(fill=x, pady=(0, 25))
            self.send_btn.configure(command=self._on_login)

            # Separador "Or register Width "
            separate_fm = ctk.CTkFrame(form_ctn, fg_color="transparent")
            separate_fm.pack(fill=x, pady=(0,25))

            # Linea Izquierda 
            ln_left = ctk.CTkFrame(separate_fm, height=2, fg_color="#3A3A3A")
            ln_left.pack(side=left, fill=x, expand=True, pady=10)

            # Texto separador
            sep_label = ctk.CTkLabel(separate_fm, text="Continua con.", font=("Arial", 16), text_color="#8B8B8B")
            sep_label.pack(side="left", padx=10)

            ln_right = ctk.CTkFrame(separate_fm, height=2, fg_color="#3A3A3A")
            ln_right.pack(side=right, fill=x, expand=True, pady=10)

            # Frame para botones de redes sociales
            social_fm = ctk.CTkFrame(form_ctn, fg_color="transparent")
            social_fm.pack(fill=x)

            # Imagenes de facebook e Google
            uri_patch = self._get_patch("gui/img/png/google.png")
            uri_patch2 = self._get_patch("gui/img/png/facebook.png")
            self.google_img = ctk.CTkImage(Image.open(uri_patch), size=(40, 40))
            self.facebook_img = ctk.CTkImage(Image.open(uri_patch2), size=(40, 40))

            # Boton de Google
            self.google_btn = ctk.CTkButton(social_fm, image=self.google_img, text="Google", fg_color="#FFFFFF", text_color="#000000", hover_color="#D3CFFB", corner_radius=8, height=40, font=("Arial", 14, "bold"), border_width=1, border_color="#3A3A3A")
            self.google_btn.pack(side=left, fill=x, expand=True, padx=(0, 10))
            self.google_btn.configure(command=lambda: sign_in_with_provider("google"))


            # Boton de Facebook
            self.facebook_btn = ctk.CTkButton(social_fm, image=self.facebook_img, text="Facebook", fg_color="#FFFFFF", text_color="#000000", hover_color="#D3CFFB", corner_radius=8, height=40, font=("Arial", 14, "bold"),  border_width=1, border_color="#3A3A3A")
            self.facebook_btn.pack(side=left, fill=x, expand=True)
            self.facebook_btn.configure(command=lambda: sign_in_with_provider("facebook"))


    # ---------------- Funciones de interacción ---------------- #

    #Funcion de creacion de la cuenta
    def _on_create_account(self):
        email = self.email.get()
        email2 = self.email_verify.get()
        password = self.password.get()
        password2 = self.password_confirm.get()

        # Validar que los correos sean iguales
        if email != email2:
            print("Error: los correos no son iguales")
            return
        if password != password2:
            print("Error: Las contraseñas no son iguales")
            return
        

        succes, msg = sign_up(email, password)
        if succes:
            print(f"Exito: {msg} ")
            if self.on_login_sucess:
                self.on_login_sucess()
        else:
            print(f"Error: {msg} ")

    # Funcion del login
    def _on_login(self):
        """Metodo para el ingreso """
        email = self.email.get()
        password = self.password.get()

        succes, msg = sign_in(email, password)
        if succes:
            print(f"Login exitoso: {msg}")
            if self.on_login_sucess:
                self.on_login_sucess()

        else:
            print(f"Error de login: {msg}")

    # Funcion para mostrar la password en el CtkEntry
    def _toggle_password_visibility(self):
        if self.password_visible:
            self.password.configure(show="*")
            self.password_confirm.configure(show="*")
            self.password_visible = False
            self.eye_btn.configure(image=self.view_enable)
        else:
            self.password.configure(show="")
            self.password_confirm.configure(show="")
            self.password_visible = True
            self.eye_btn.configure(image=self.view_unable)


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

    def _mode_login(self):
        self.login = not self.login
            # Encontrar el main_frame actual
        for widget in self.winfo_children():
            if widget != self.title_bar and isinstance(widget, ctk.CTkFrame):
                main_frame = widget
                break
        else:
            main_frame = None
    
        if main_frame:
            main_frame.destroy()
    
        # Recrear solo el contenido principal
        self._create_ui()
        print(f"Cambiando el estado a: {self.login}")

    def _on_destroy(self, event):
        if self.tray_icon:
            self.tray_icon.stop()

    def run(self):
        self.mainloop()