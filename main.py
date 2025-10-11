# Corredor principal main.py
# Importamos modulos y librerias
import tkinter as tk
from gui.main_app import MainApp
from gui.login_view import LoginView
from utils.loggers import get_logger

# Inicializamos el loger para reportes
logger = get_logger(__name__)


def show_main_app():
    """Muestra la aplicación principal después del login exitoso"""
    # Cerrar ventana de login
    #login_window.destroy()
    
    # Abrir aplicación principal
    main_app = MainApp()
    main_app.run()


if __name__ == "__main__":
    # Crear ventana de login con callback
    #login_window = LoginView(on_login_sucess=show_main_app)
    #login_window.run()
    main_app = MainApp()
    main_app.run()

