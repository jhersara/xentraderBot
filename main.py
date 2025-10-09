# Corredor principal main.py
# Importamos modulos y librerias
import tkinter as tk
from gui.main_app import MainApp
from gui.login_view import LoginView
from utils.loggers import get_logger

# Inicializamos el loger para reportes
logger = get_logger(__name__)


# Funciones principales
# Funcion inicial

# Ejecutador del codigo principal
# if __name__ == "__main__":
#      app = MainApp()
#      app.run()

if __name__ == "__main__":
     # app = LoginView()
     # app.run()
     app = MainApp()
     app.run()