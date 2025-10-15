# Importacion de librerias
from utils.loggers import get_logger
from pathlib import Path
from PIL import Image
import customtkinter as ctk
import tkinter as tk
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
        self.geometry("1000x650")
        self.normal_geometry = "1000x650"
        self.is_maximized = False
        self.tray_icon = None
        self.tray_thread = None

        # Estado del menú lateral
        self.menu_expanded = False
        self.menu_width_collapsed = 70
        self.menu_width_expanded = 260

        # Datos simulados del dashboard
        self.balance = 10000.00
        self.profit_loss = 250.50
        self.open_positions = 3

        # Configurar protocolo de cierre
        self.protocol("WM_DELETE_WINDOW", self._minimized_to_dray)

        # Crear barra superior personalizada
        self._title_navbar()
        self._create_ui()

        # Configuracion del system tray cuando se cierra la ventana
        self.bind("<Destroy>", self._on_destroy)

    # ---------------- Barra de navegación superior ---------------- #
    def _title_navbar(self):
        self.title_bar = ctk.CTkFrame(self, height=32, fg_color="#1E1E2E", border_width=0, corner_radius=0)
        self.title_bar.pack(fill="x", side="top")

        # Logo de la app
        try:
            img_patch = self._get_patch("gui/img/img/logo1.png")
            self.logo = ctk.CTkImage(
                light_image=Image.open(img_patch),
                dark_image=Image.open(img_patch),
                size=(24, 24)
            )
            logo_label = ctk.CTkLabel(self.title_bar, image=self.logo, text="")
            logo_label.pack(side="left", padx=12, pady=4)
        except:
            pass

        # Nombre de la app
        app_name = ctk.CTkLabel(self.title_bar, text="Xentraders Bot", font=("Segoe UI", 13, "bold"), text_color="#CDD6F4")
        app_name.pack(side="left", padx=(0 if hasattr(self, 'logo') else 12, 0))

        # Botones ventana
        try:
            min_ico = self._get_patch("gui/img/icons/icon_minimize.png")
            max_ico = self._get_patch("gui/img/icons/icon_maximize.png")
            close_ico = self._get_patch("gui/img/icons/icon_close.png")

            self.close_icon = ctk.CTkImage(Image.open(close_ico), size=(12, 12))
            close_btn = ctk.CTkButton(self.title_bar, image=self.close_icon, text="",
                                      fg_color="transparent", hover_color="#F38BA8", width=45, height=32,
                                      command=self._close_wind, corner_radius=0)
            close_btn.pack(side="right")

            self.max_icon = ctk.CTkImage(Image.open(max_ico), size=(14, 14))
            max_btn = ctk.CTkButton(self.title_bar, image=self.max_icon, text="",
                                    fg_color="transparent", hover_color="#313244", width=45, height=32,
                                    command=self._toggle_maximized, corner_radius=0)
            max_btn.pack(side="right")

            self.min_icon = ctk.CTkImage(Image.open(min_ico), size=(14, 14))
            min_btn = ctk.CTkButton(self.title_bar, image=self.min_icon, text="",
                                    fg_color="transparent", hover_color="#313244", width=45, height=32,
                                    command=self._minimized_to_dray, corner_radius=0)
            min_btn.pack(side="right")
        except:
            close_btn = ctk.CTkButton(self.title_bar, text="✕", 
                                      fg_color="transparent", hover_color="#F38BA8", width=45, height=32,
                                      command=self._close_wind, corner_radius=0, font=("Arial", 12))
            close_btn.pack(side="right")

            max_btn = ctk.CTkButton(self.title_bar, text="□", 
                                    fg_color="transparent", hover_color="#313244", width=45, height=32,
                                    command=self._toggle_maximized, corner_radius=0, font=("Arial", 12))
            max_btn.pack(side="right")

            min_btn = ctk.CTkButton(self.title_bar, text="−", 
                                    fg_color="transparent", hover_color="#313244", width=45, height=32,
                                    command=self._minimized_to_dray, corner_radius=0, font=("Arial", 12))
            min_btn.pack(side="right")

        # Mover ventana
        self.title_bar.bind("<Button-1>", self._start_move)
        self.title_bar.bind("<B1-Motion>", self._do_move)


    # ---------------- Contenido principal ---------------- #
    def _create_ui(self):
        # Contenedor principal
        self.main_container = ctk.CTkFrame(self, fg_color="#11111B", border_width=0, corner_radius=0)
        self.main_container.pack(fill="both", expand=True)

        # Barra lateral (sidebar)
        self._create_sidebar()

        # Área de contenido principal
        self.content_area = ctk.CTkFrame(self.main_container, fg_color="#181825", corner_radius=0)
        self.content_area.pack(side="right", fill="both", expand=True)

        # Contenido por defecto
        self._show_dashboard()


    def _create_sidebar(self):
        """Crea la barra lateral expandible"""
        self.sidebar = ctk.CTkFrame(
            self.main_container, 
            width=self.menu_width_collapsed,
            fg_color="#1E1E2E",
            corner_radius=0
        )
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)

        # Botón hamburguesa en la parte superior
        hamburger_container = ctk.CTkFrame(self.sidebar, fg_color="transparent", height=60)
        hamburger_container.pack(fill="x", pady=0)
        hamburger_container.pack_propagate(False)

        self.hamburger_btn = ctk.CTkButton(
            hamburger_container,
            text="☰",
            width=50,
            height=50,
            fg_color="transparent",
            hover_color="#313244",
            font=("Segoe UI", 22),
            text_color="#CDD6F4",
            command=self._toggle_menu,
            corner_radius=10
        )
        self.hamburger_btn.pack(expand=True)

        # Separador
        sep1 = ctk.CTkFrame(self.sidebar, height=1, fg_color="#313244")
        sep1.pack(fill="x", padx=10, pady=5)

        # SECCIÓN PRINCIPAL
        self._create_section_label("PRINCIPAL")
        
        self.menu_items_main = [
            {"name": "Dashboard", "icon": "cil-home.png", "command": self._show_dashboard, "color": "#89B4FA"},
            {"name": "Trading Manual", "icon": "cil-cursor.png", "command": self._show_manual_trading, "color": "#F9E2AF"},
            {"name": "Trading Auto", "icon": "cil-av-timer.png", "command": self._show_auto_trading, "color": "#A6E3A1"},
        ]

        self.menu_buttons_main = []
        for item in self.menu_items_main:
            btn = self._create_menu_button(item)
            self.menu_buttons_main.append(btn)

        # Separador
        sep2 = ctk.CTkFrame(self.sidebar, height=1, fg_color="#313244")
        sep2.pack(fill="x", padx=10, pady=10)

        # SECCIÓN ANÁLISIS
        self._create_section_label("ANÁLISIS")
        
        self.menu_items_analysis = [
            {"name": "Gráficos", "icon": "cil-chart-line.png", "command": self._show_charts, "color": "#CBA6F7"},
            {"name": "Análisis", "icon": "cil-chart-pie.png", "command": self._show_analysis, "color": "#F5C2E7"},
        ]

        self.menu_buttons_analysis = []
        for item in self.menu_items_analysis:
            btn = self._create_menu_button(item)
            self.menu_buttons_analysis.append(btn)

        # Separador
        sep3 = ctk.CTkFrame(self.sidebar, height=1, fg_color="#313244")
        sep3.pack(fill="x", padx=10, pady=10)

        # SECCIÓN SISTEMA
        self._create_section_label("SISTEMA")
        
        self.menu_items_system = [
            {"name": "Logs", "icon": "cil-file.png", "command": self._show_logs, "color": "#94E2D5"},
            {"name": "Alertas", "icon": "cil-bell.png", "command": self._show_alerts, "color": "#FAB387"},
        ]

        self.menu_buttons_system = []
        for item in self.menu_items_system:
            btn = self._create_menu_button(item)
            self.menu_buttons_system.append(btn)

        # Espaciador flexible
        spacer = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        spacer.pack(fill="both", expand=True)

        # Separador antes de la parte inferior
        sep4 = ctk.CTkFrame(self.sidebar, height=1, fg_color="#313244")
        sep4.pack(fill="x", padx=10, pady=5)

        # SECCIÓN USUARIO (al final)
        self.menu_items_user = [
            {"name": "Configuración", "icon": "cil-settings.png", "command": self._show_settings, "color": "#B4BEFE"},
            {"name": "Perfil", "icon": "cil-user.png", "command": self._show_profile, "color": "#89DCEB"},
            {"name": "Cerrar Sesión", "icon": "cil-account-logout.png", "command": self._logout, "color": "#F38BA8"},
        ]

        self.menu_buttons_user = []
        for item in self.menu_items_user:
            btn = self._create_menu_button(item, bottom=True)
            self.menu_buttons_user.append(btn)

        # Combinar todas las listas de botones
        self.all_menu_buttons = (
            self.menu_buttons_main + 
            self.menu_buttons_analysis + 
            self.menu_buttons_system + 
            self.menu_buttons_user
        )

    def _create_section_label(self, text):
        """Crea una etiqueta de sección"""
        self.section_label = ctk.CTkLabel(
            self.sidebar,
            text="",
            font=("Segoe UI", 9, "bold"),
            text_color="#6C7086",
            anchor="w"
        )
        self.section_label.pack(fill="x", padx=15, pady=(5, 3))
        self.section_label.section_text = text


    def _create_menu_button(self, item, bottom=False):
        """Crea un botón del menú con icono y texto"""
        btn_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent", height=52)
        btn_frame.pack(fill="x", padx=8, pady=2)
        btn_frame.pack_propagate(False)

        # Intentar cargar el icono
        try:
            icon_path = self._get_patch(f"gui/img/icons/{item['icon']}")
            icon_image = ctk.CTkImage(
                light_image=Image.open(icon_path),
                dark_image=Image.open(icon_path),
                size=(22, 22)
            )
            
            btn = ctk.CTkButton(
                btn_frame,
                image=icon_image,
                text="",
                width=50,
                height=48,
                fg_color="transparent",
                hover_color="#313244",
                command=item["command"],
                corner_radius=10,
                anchor="center"
            )
            btn.icon_image = icon_image
        except Exception as e:
            logger.warning(f"No se pudo cargar icono {item['icon']}: {e}")
            btn = ctk.CTkButton(
                btn_frame,
                text="●",
                width=50,
                height=48,
                fg_color="transparent",
                hover_color="#313244",
                command=item["command"],
                corner_radius=10,
                font=("Segoe UI", 16),
                text_color=item.get("color", "#CDD6F4")
            )
        
        btn.pack(side="left")
        
        # Label del texto (inicialmente oculto pero clickeable)
        label = ctk.CTkLabel(
            btn_frame,
            text=item["name"],
            font=("Segoe UI", 12),
            text_color=item.get("color", "#CDD6F4"),
            anchor="w",
            cursor="hand2"
        )
        
        # Hacer el label clickeable
        label.bind("<Button-1>", lambda e: item["command"]())
        label.bind("<Enter>", lambda e: btn.configure(fg_color="#313244"))
        label.bind("<Leave>", lambda e: btn.configure(fg_color="transparent"))
        
        # Guardar referencia
        btn.text_label = label
        btn.item_name = item["name"]
        btn.item_color = item.get("color", "#CDD6F4")
        
        return btn


    def _toggle_menu(self):
        """Expande o colapsa el menú lateral"""
        if self.menu_expanded:
            # Colapsar
            self.sidebar.configure(width=self.menu_width_collapsed)
            
            # Ocultar etiquetas de sección
            for widget in self.sidebar.winfo_children():
                if isinstance(widget, ctk.CTkLabel) and hasattr(widget, 'section_text'):
                    widget.configure(text="")
            
            # Ocultar textos de botones
            for btn in self.all_menu_buttons:
                if hasattr(btn, 'text_label'):
                    btn.text_label.pack_forget()
            
            self.menu_expanded = False
        else:
            # Expandir
            self.sidebar.configure(width=self.menu_width_expanded)
            
            # Mostrar etiquetas de sección
            for widget in self.sidebar.winfo_children():
                if isinstance(widget, ctk.CTkLabel) and hasattr(widget, 'section_text'):
                    widget.configure(text=widget.section_text)
            
            # Mostrar textos de botones
            for btn in self.all_menu_buttons:
                if hasattr(btn, 'text_label'):
                    btn.text_label.pack(side="left", padx=12, fill="x", expand=True)
            
            self.menu_expanded = True


    # ---------------- Funciones de navegación ---------------- #
    def _clear_content(self):
        """Limpia el área de contenido"""
        for widget in self.content_area.winfo_children():
            widget.destroy()


    def _show_dashboard(self):
        """Muestra el dashboard con información financiera"""
        self._clear_content()
        
        # Configurar grid layout
        self.content_area.grid_columnconfigure((0, 1), weight=1)
        self.content_area.grid_rowconfigure((0, 1, 2), weight=1)

        # Resumen Financiero
        financial_frame = ctk.CTkFrame(self.content_area, fg_color="#1E1E2E", corner_radius=15)
        financial_frame.grid(row=0, column=0, padx=15, pady=15, sticky="nsew")
        
        ctk.CTkLabel(
            financial_frame,
            text="💰 Resumen Financiero",
            font=("Segoe UI", 18, "bold"),
            text_color="#89B4FA"
        ).pack(pady=15)
        
        self.balance_label = ctk.CTkLabel(
            financial_frame,
            text=f"Saldo Total: ${self.balance:,.2f}",
            font=("Segoe UI", 14),
            text_color="#CDD6F4"
        )
        self.balance_label.pack(pady=8, padx=20, anchor="w")
        
        self.profit_loss_label = ctk.CTkLabel(
            financial_frame,
            text=f"Ganancias/Pérdidas: ${self.profit_loss:,.2f}",
            font=("Segoe UI", 14),
            text_color="#A6E3A1" if self.profit_loss >= 0 else "#F38BA8"
        )
        self.profit_loss_label.pack(pady=8, padx=20, anchor="w")
        
        self.open_positions_label = ctk.CTkLabel(
            financial_frame,
            text=f"Posiciones Abiertas: {self.open_positions}",
            font=("Segoe UI", 14),
            text_color="#CDD6F4"
        )
        self.open_positions_label.pack(pady=8, padx=20, anchor="w")

        # Vista de Mercado
        market_frame = ctk.CTkFrame(self.content_area, fg_color="#1E1E2E", corner_radius=15)
        market_frame.grid(row=0, column=1, padx=15, pady=15, sticky="nsew")
        
        ctk.CTkLabel(
            market_frame,
            text="📈 Vista de Mercado",
            font=("Segoe UI", 18, "bold"),
            text_color="#CBA6F7"
        ).pack(pady=15)
        
        ctk.CTkLabel(
            market_frame,
            text="Precio EURUSD: 1.0850",
            font=("Segoe UI", 14),
            text_color="#CDD6F4"
        ).pack(pady=8, padx=20, anchor="w")
        
        ctk.CTkLabel(
            market_frame,
            text="Volumen: 125,000",
            font=("Segoe UI", 14),
            text_color="#CDD6F4"
        ).pack(pady=8, padx=20, anchor="w")
        
        ctk.CTkLabel(
            market_frame,
            text="[Gráfico de Velas Aquí]",
            font=("Segoe UI", 12),
            text_color="#6C7086"
        ).pack(pady=20, padx=20)

        # Operaciones Rápidas
        operations_frame = ctk.CTkFrame(self.content_area, fg_color="#1E1E2E", corner_radius=15)
        operations_frame.grid(row=1, column=0, columnspan=2, padx=15, pady=15, sticky="nsew")
        
        ctk.CTkLabel(
            operations_frame,
            text="⚡ Operaciones Rápidas",
            font=("Segoe UI", 18, "bold"),
            text_color="#F9E2AF"
        ).pack(pady=15)
        
        buttons_frame = ctk.CTkFrame(operations_frame, fg_color="transparent")
        buttons_frame.pack(expand=True, fill="both", padx=20, pady=10)
        
        ctk.CTkButton(
            buttons_frame,
            text="🟢 Comprar",
            font=("Segoe UI", 14, "bold"),
            fg_color="#A6E3A1",
            hover_color="#94E2D5",
            text_color="#11111B",
            height=45,
            corner_radius=10
        ).pack(side="left", expand=True, padx=5)
        
        ctk.CTkButton(
            buttons_frame,
            text="🔴 Vender",
            font=("Segoe UI", 14, "bold"),
            fg_color="#F38BA8",
            hover_color="#F5C2E7",
            text_color="#11111B",
            height=45,
            corner_radius=10
        ).pack(side="left", expand=True, padx=5)
        
        ctk.CTkButton(
            buttons_frame,
            text="❌ Cerrar Posiciones",
            font=("Segoe UI", 14, "bold"),
            fg_color="#FAB387",
            hover_color="#F9E2AF",
            text_color="#11111B",
            height=45,
            corner_radius=10
        ).pack(side="left", expand=True, padx=5)


    def update_financial_summary(self, balance, profit_loss, open_positions):
        """Actualiza los datos financieros del dashboard"""
        self.balance = balance
        self.profit_loss = profit_loss
        self.open_positions = open_positions
        
        if hasattr(self, 'balance_label'):
            self.balance_label.configure(text=f"Saldo Total: ${balance:,.2f}")
            self.profit_loss_label.configure(
                text=f"Ganancias/Pérdidas: ${profit_loss:,.2f}",
                text_color="#A6E3A1" if profit_loss >= 0 else "#F38BA8"
            )
            self.open_positions_label.configure(text=f"Posiciones Abiertas: {open_positions}")


    def _show_manual_trading(self):
        """Muestra trading manual"""
        self._clear_content()
        
        header = ctk.CTkFrame(self.content_area, fg_color="#1E1E2E", corner_radius=15)
        header.pack(fill="x", padx=20, pady=20)
        
        ctk.CTkLabel(
            header,
            text="🎯 Trading Manual",
            font=("Segoe UI", 32, "bold"),
            text_color="#F9E2AF"
        ).pack(padx=30, pady=25)


    def _show_auto_trading(self):
        """Muestra trading automático"""
        self._clear_content()
        
        header = ctk.CTkFrame(self.content_area, fg_color="#1E1E2E", corner_radius=15)
        header.pack(fill="x", padx=20, pady=20)
        
        ctk.CTkLabel(
            header,
            text="🤖 Trading Automático",
            font=("Segoe UI", 32, "bold"),
            text_color="#A6E3A1"
        ).pack(padx=30, pady=25)


    def _show_charts(self):
        """Muestra los gráficos"""
        self._clear_content()
        
        header = ctk.CTkFrame(self.content_area, fg_color="#1E1E2E", corner_radius=15)
        header.pack(fill="x", padx=20, pady=20)
        
        ctk.CTkLabel(
            header,
            text="📈 Gráficos",
            font=("Segoe UI", 32, "bold"),
            text_color="#CBA6F7"
        ).pack(padx=30, pady=25)


    def _show_analysis(self):
        """Muestra el análisis"""
        self._clear_content()
        
        header = ctk.CTkFrame(self.content_area, fg_color="#1E1E2E", corner_radius=15)
        header.pack(fill="x", padx=20, pady=20)
        
        ctk.CTkLabel(
            header,
            text="🔍 Análisis",
            font=("Segoe UI", 32, "bold"),
            text_color="#F5C2E7"
        ).pack(padx=30, pady=25)


    def _show_logs(self):
        """Muestra los logs"""
        self._clear_content()
        
        header = ctk.CTkFrame(self.content_area, fg_color="#1E1E2E", corner_radius=15)
        header.pack(fill="x", padx=20, pady=20)
        
        ctk.CTkLabel(
            header,
            text="📄 Logs del Sistema",
            font=("Segoe UI", 32, "bold"),
            text_color="#94E2D5"
        ).pack(padx=30, pady=25)


    def _show_alerts(self):
        """Muestra las alertas"""
        self._clear_content()
        
        header = ctk.CTkFrame(self.content_area, fg_color="#1E1E2E", corner_radius=15)
        header.pack(fill="x", padx=20, pady=20)
        
        ctk.CTkLabel(
            header,
            text="🔔 Alertas y Notificaciones",
            font=("Segoe UI", 32, "bold"),
            text_color="#FAB387"
        ).pack(padx=30, pady=25)


    def _show_settings(self):
        """Muestra la configuración"""
        self._clear_content()
        
        header = ctk.CTkFrame(self.content_area, fg_color="#1E1E2E", corner_radius=15)
        header.pack(fill="x", padx=20, pady=20)
        
        ctk.CTkLabel(
            header,
            text="⚙️ Configuración",
            font=("Segoe UI", 32, "bold"),
            text_color="#B4BEFE"
        ).pack(padx=30, pady=25)


    def _show_profile(self):
        """Muestra el perfil"""
        self._clear_content()
        
        header = ctk.CTkFrame(self.content_area, fg_color="#1E1E2E", corner_radius=15)
        header.pack(fill="x", padx=20, pady=20)
        
        ctk.CTkLabel(
            header,
            text="👤 Mi Perfil",
            font=("Segoe UI", 32, "bold"),
            text_color="#89DCEB"
        ).pack(padx=30, pady=25)


    def _logout(self):
        """Cierra sesión"""
        from utils.auth import sign_out
        sign_out()
        print("Cerrando sesión...")
        self.destroy()


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
                self.tray_icon = pystray.Icon("xentrader", tray_image, "Xentraders App", menu=menu)
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
        return str(full_patch)

    def _on_destroy(self, event):
        if self.tray_icon:
            self.tray_icon.stop()

    def run(self):
        self.mainloop()



# Codigo para descargar datos del backtesting
import MetaTrader5 as mt5
import pandas as pd
from datetime import datetime, timedelta

# === CONFIGURACIÓN ===
symbol = "EURUSD"               # Par a descargar
timeframe = mt5.TIMEFRAME_M1    # 1 minuto
start_date = datetime.now() - timedelta(days=365)  # Último año
end_date = datetime.now()
output_file = "eurusd_m1.csv"   # Nombre del archivo CSV final

# === INICIAR CONEXIÓN ===
print("🔌 Conectando a MetaTrader 5...")
if not mt5.initialize():
    print("❌ No se pudo conectar con MetaTrader 5")
    quit()

# === DESCARGAR DATOS ===
print(f"📊 Descargando datos de {symbol} desde {start_date.date()} hasta {end_date.date()} ...")
rates = mt5.copy_rates_range(symbol, timeframe, start_date, end_date)

# === CERRAR CONEXIÓN ===
mt5.shutdown()

# === VALIDAR DATOS ===
if rates is None or len(rates) == 0:
    print("⚠️ No se recibieron datos. Asegúrate de que MT5 esté abierto y conectado.")
    quit()

# === CONVERTIR A DATAFRAME ===
data = pd.DataFrame(rates)
data['time'] = pd.to_datetime(data['time'], unit='s')
data.set_index('time', inplace=True)

# === GUARDAR ARCHIVO ===
data.to_csv(output_file)
print(f"✅ {len(data)} velas M1 guardadas en '{output_file}' correctamente.")
