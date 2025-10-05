"""
Script de prueba para verificar la autenticación OAuth
Ejecuta este archivo para probar el login con Google/Facebook
"""

import sys
from pathlib import Path

# Agregar el directorio raíz al path
root_dir = Path(__file__).parent
sys.path.insert(0, str(root_dir))

from gui.login_view import LoginView
from utils.loggers import get_logger

logger = get_logger(__name__)

def on_login_success():
    """Callback que se ejecuta cuando el login es exitoso"""
    logger.info("="*50)
    logger.info("¡LOGIN EXITOSO!")
    logger.info("="*50)
    print("\n" + "="*50)
    print("✓ ¡Autenticación exitosa!")
    print("="*50)
    print("\nCerrando ventana de login...")
    
    # Aquí puedes abrir tu ventana principal
    # Por ahora solo cerramos el login
    import time
    time.sleep(2)
    app.destroy()

if __name__ == "__main__":
    print("="*50)
    print("XENTRADERS - Test de Autenticación OAuth")
    print("="*50)
    print("\nInstrucciones:")
    print("1. Haz clic en el botón 'Google' o 'Facebook'")
    print("2. Se abrirá tu navegador")
    print("3. Selecciona tu cuenta")
    print("4. Espera a que se complete la autenticación")
    print("\nNOTA: Asegúrate de haber configurado las Redirect URLs en Supabase")
    print("Ver archivo OAUTH_SETUP.md para más detalles")
    print("="*50 + "\n")
    
    # Crear y ejecutar la aplicación
    app = LoginView(on_login_sucess=on_login_success)
    app.run()
