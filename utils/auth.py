# auth.py
from supabase import create_client, Client
from typing import Optional, Tuple
import webbrowser
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import time

# Cargar desde variables de entorno o un archivo seguro
SUPABASE_URL = "https://rlnltxkgvpkfztkzotyj.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InJsbmx0eGtndnBrZnp0a3pvdHlqIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTc4MTU0OTksImV4cCI6MjA3MzM5MTQ5OX0.SR-XYXW9TAOYYLxGAqDW8hExUaia4naQud-iNXnxMzU"  # ⚠️ mejor usar variables de entorno en producción

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Variables globales para el callback
auth_code = None
auth_error = None
callback_received = False

class OAuthCallbackHandler(BaseHTTPRequestHandler):
    """Manejador HTTP para recibir el callback de OAuth"""
    
    def do_GET(self):
        global auth_code, auth_error, callback_received
        
        # Parsear la URL para obtener los parámetros
        parsed_url = urlparse(self.path)
        params = parse_qs(parsed_url.query)
        
        # Extraer el access_token del fragmento (#) si está presente
        if parsed_url.fragment:
            fragment_params = parse_qs(parsed_url.fragment)
            if 'access_token' in fragment_params:
                auth_code = fragment_params['access_token'][0]
                callback_received = True
        
        # O extraer del query string
        if 'code' in params:
            auth_code = params['code'][0]
            callback_received = True
        elif 'error' in params:
            auth_error = params['error'][0]
            callback_received = True
        
        # Enviar respuesta HTML al navegador
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        
        if auth_code:
            html_response = """
            <html>
            <head>
                <title>Autenticación Exitosa</title>
                <style>
                    body { 
                        font-family: Arial, sans-serif; 
                        display: flex; 
                        justify-content: center; 
                        align-items: center; 
                        height: 100vh; 
                        margin: 0;
                        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    }
                    .container {
                        background: white;
                        padding: 40px;
                        border-radius: 10px;
                        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
                        text-align: center;
                    }
                    h1 { color: #667eea; margin-bottom: 20px; }
                    p { color: #666; }
                    .success-icon { font-size: 60px; color: #4CAF50; }
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="success-icon">✓</div>
                    <h1>¡Autenticación Exitosa!</h1>
                    <p>Ya puedes cerrar esta ventana y volver a la aplicación.</p>
                </div>
                <script>
                    // Intentar cerrar la ventana automáticamente
                    setTimeout(() => { window.close(); }, 2000);
                </script>
            </body>
            </html>
            """
        else:
            html_response = """
            <html>
            <head>
                <title>Error de Autenticación</title>
                <style>
                    body { 
                        font-family: Arial, sans-serif; 
                        display: flex; 
                        justify-content: center; 
                        align-items: center; 
                        height: 100vh; 
                        margin: 0;
                        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
                    }
                    .container {
                        background: white;
                        padding: 40px;
                        border-radius: 10px;
                        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
                        text-align: center;
                    }
                    h1 { color: #f5576c; margin-bottom: 20px; }
                    p { color: #666; }
                    .error-icon { font-size: 60px; color: #f44336; }
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="error-icon">✗</div>
                    <h1>Error de Autenticación</h1>
                    <p>Hubo un problema al autenticarte. Por favor intenta nuevamente.</p>
                </div>
            </body>
            </html>
            """
        
        self.wfile.write(html_response.encode())
    
    def log_message(self, format, *args):
        # Suprimir los logs del servidor HTTP
        pass


def start_callback_server(port=8000, timeout=60):
    """Inicia un servidor HTTP temporal para recibir el callback de OAuth"""
    global auth_code, auth_error, callback_received
    
    # Resetear variables
    auth_code = None
    auth_error = None
    callback_received = False
    
    server = HTTPServer(('localhost', port), OAuthCallbackHandler)
    
    # Ejecutar servidor con timeout
    start_time = time.time()
    while not callback_received and (time.time() - start_time) < timeout:
        server.handle_request()
    
    server.server_close()


def sign_up(email: str, password: str) -> Tuple[bool, str]:
    """Registro de usuario con email y contraseña"""
    try:
        res = supabase.auth.sign_up({"email": email, "password": password})
        if res.user:
            return True, "Usuario creado. Verifica tu correo para confirmar la cuenta."
        return False, str(res)
    except Exception as e:
        return False, f"Error: {e}"


def sign_in(email: str, password: str) -> Tuple[bool, str]:
    """Inicio de sesión con email y contraseña"""
    try:
        res = supabase.auth.sign_in_with_password({"email": email, "password": password})
        if res.user:
            return True, "Inicio de sesión exitoso."
        return False, "Credenciales incorrectas."
    except Exception as e:
        return False, f"Error: {e}"


def sign_in_with_provider(provider: str, callback_func=None) -> Tuple[bool, str]:
    """
    Inicio de sesión social (abre navegador y espera callback)
    
    Args:
        provider: 'google' o 'facebook'
        callback_func: Función opcional que se llamará cuando se complete la autenticación
    
    Returns:
        Tuple[bool, str]: (éxito, mensaje)
    """
    global auth_code, auth_error, callback_received
    
    try:
        # Configurar el redirect URI (debe coincidir con el configurado en Supabase)
        redirect_to = "http://localhost:8000"
        
        # Obtener la URL de autenticación
        res = supabase.auth.sign_in_with_oauth({
            "provider": provider,
            "options": {
                "redirect_to": redirect_to
            }
        })
        
        if not hasattr(res, "url") or not res.url:
            return False, f"No se recibió URL de autenticación de {provider}"
        
        print(f"Abriendo navegador para login con {provider}...")
        print(f"URL de callback configurada: {redirect_to}")
        
        # Iniciar servidor de callback en segundo plano
        server_thread = threading.Thread(
            target=start_callback_server,
            args=(8000, 120),  # Puerto 8000, timeout 120 segundos
            daemon=True
        )
        server_thread.start()
        
        # Abrir navegador
        webbrowser.open(res.url)
        
        # Esperar a que se complete la autenticación
        print("Esperando autenticación en el navegador...")
        server_thread.join(timeout=120)
        
        # Verificar resultado
        if callback_received and auth_code:
            # Establecer la sesión con el token recibido
            try:
                # Aquí puedes guardar el token para usarlo después
                if callback_func:
                    callback_func(True, "Autenticación exitosa")
                return True, "Autenticación exitosa con " + provider
            except Exception as e:
                return False, f"Error al procesar el token: {e}"
        elif auth_error:
            return False, f"Error de autenticación: {auth_error}"
        else:
            return False, "Tiempo de espera agotado. No se recibió respuesta del navegador."
    
    except Exception as e:
        return False, f"Error con proveedor {provider}: {e}"


def get_current_user():
    """Obtiene el usuario actualmente autenticado"""
    try:
        user = supabase.auth.get_user()
        return user
    except Exception as e:
        print(f"Error al obtener usuario: {e}")
        return None


def sign_out() -> Tuple[bool, str]:
    """Cerrar sesión del usuario actual"""
    try:
        supabase.auth.sign_out()
        return True, "Sesión cerrada exitosamente"
    except Exception as e:
        return False, f"Error al cerrar sesión: {e}"
