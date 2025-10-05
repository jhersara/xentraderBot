# Corredor principal main.py
# Importamos modulos y librerias
import tkinter as tk
from gui.main_app import MainApp
from gui.login_view import LoginView
from utils.loggers import get_logger

# Inicializamos el loger para reportes
logger = get_logger(__name__)

class AppController:
     def __init__(self):
          self.login_view = None
          self.main_app = None

     def start_login(self):
          """Inicia la ventana de login"""
          self.login_view = LoginView(on_login_sucess=self.on_login_sucess)
          self.login_view.run()

     def on_login_sucess(self):
          """Callback ejecutado cuando el login es exitosos"""
          if self.login_view:
               self.login_view.destroy()

          # LLama a la ventada principal
          self.main_app = MainApp()
          self.main_app.run()

if __name__ == "__main__":
     controller = AppController()
     controller.start_login()