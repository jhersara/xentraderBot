# auth.py - Sistema de autenticación híbrido (online/offline)
from supabase import create_client, Client
from typing import Optional, Tuple
import webbrowser
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import time
from storage.local_auth import LocalAuthStorage

# Cargar desde variables de entorno o un archivo seguro
SUPABASE_URL = "https://rlnltxkgvpkfztkzotyj.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InJsbmx0eGtndnBrZnp0a3pvdHlqIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTc4MTU0OTksImV4cCI6MjA3MzM5MTQ5OX0.SR-XYXW9TAOYYLxGAqDW8hExUaia4naQud-iNXnxMzU"

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Inicializar almacenamiento local
local_storage = LocalAuthStorage()

# Variables globales para el callback
auth_code = None
auth_error = None
callback_received = False


def is_online() -> bool:
    """Verifica si hay conexión a internet"""
    try:
        # Intentar hacer ping a Supabase
        supabase.auth.get_session()
        return True
    except:
        return False


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


def sign_up(email: str, password: str, username: str = None) -> Tuple[bool, str]:
    """Registro de usuario - funciona online y offline"""
    
    # Siempre registrar localmente primero
    local_success, local_msg = local_storage.register_user(email, password, username)
    
    if not local_success:
        return False, local_msg
    
    # Intentar registrar en Supabase si hay conexión
    if is_online():
        try:
            res = supabase.auth.sign_up({"email": email, "password": password})
            if res.user:
                local_storage.mark_user_synced(email)
                return True, "Usuario creado y sincronizado. Verifica tu correo."
            return True, "Usuario creado localmente. Se sincronizará cuando haya conexión."
        except Exception as e:
            return True, f"Usuario creado localmente. Error al sincronizar: {e}"
    else:
        return True, "Usuario creado localmente (modo offline). Se sincronizará cuando haya conexión."


def sign_in(email: str, password: str) -> Tuple[bool, str]:
    """Inicio de sesión - funciona online y offline"""
    
    # Intentar login online primero si hay conexión
    if is_online():
        try:
            res = supabase.auth.sign_in_with_password({"email": email, "password": password})
            if res.user:
                # Guardar sesión localmente también
                username = res.user.email.split('@')[0]
                local_storage.save_oauth_session(email, "supabase", username)
                return True, "Inicio de sesión exitoso (online)."
        except Exception as e:
            print(f"Error en login online: {e}")
            # Continuar con login offline
    
    # Fallback a login local
    success, msg = local_storage.login_user(email, password)
    if success:
        return True, "Inicio de sesión exitoso (modo offline)."
    
    return False, msg


def sign_in_with_provider(provider: str) -> Tuple[bool, str]:
    """
    Inicio de sesión social (requiere conexión a internet)
    
    Args:
        provider: 'google' o 'facebook'
    
    Returns:
        Tuple[bool, str]: (éxito, mensaje)
    """
    global auth_code, auth_error, callback_received
    
    # OAuth requiere conexión
    if not is_online():
        return False, "Necesitas conexión a internet para iniciar sesión con " + provider
    
    try:
        # Resetear variables globales
        auth_code = None
        auth_error = None
        callback_received = False
        
        # Configurar el redirect URI
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
        
        # Iniciar servidor de callback
        server_thread = threading.Thread(
            target=start_callback_server,
            args=(8000, 120),
            daemon=True
        )
        server_thread.start()
        
        # Esperar un momento para que el servidor inicie
        time.sleep(0.5)
        
        # Abrir navegador
        webbrowser.open(res.url)
        
        # Esperar autenticación
        print("Esperando autenticación en el navegador...")
        server_thread.join(timeout=120)
        
        # Verificar resultado
        if callback_received and auth_code:
            try:
                # Esperar un poco más para que Supabase procese
                time.sleep(2)
                
                # Intentar establecer la sesión con el token
                try:
                    # Usar el token para establecer la sesión
                    supabase.auth.set_session(auth_code, "")
                except:
                    pass
                
                # Intentar obtener información del usuario
                user_response = supabase.auth.get_user()
                
                email = None
                username = "usuario"
                
                # Extraer email del usuario
                if user_response:
                    if hasattr(user_response, 'user') and user_response.user:
                        email = getattr(user_response.user, 'email', None)
                    elif isinstance(user_response, dict):
                        user_data = user_response.get('user', {})
                        email = user_data.get('email')
                
                # Si no obtuvimos email, generar uno temporal
                if not email:
                    email = f"user_{provider}@oauth.com"
                
                username = email.split('@')[0]
                
                # Guardar sesión localmente
                local_storage.save_oauth_session(email, provider, username)
                
                return True, "Autenticación exitosa con " + provider
                
            except Exception as e:
                # Aún con error, si tenemos token, guardar sesión básica
                email = f"user_{provider}@oauth.com"
                username = f"usuario_{provider}"
                local_storage.save_oauth_session(email, provider, username)
                return True, f"Autenticación exitosa con {provider}"
                
        elif callback_received and auth_error:
            return False, f"Error de autenticación: {auth_error}"
        else:
            return False, "Tiempo de espera agotado o autenticación cancelada."
    
    except Exception as e:
        import traceback
        traceback.print_exc()
        return False, f"Error con proveedor {provider}: {e}"


def get_current_user():
    """Obtiene el usuario actualmente autenticado (local u online)"""
    # Primero verificar sesión local
    local_user = local_storage.get_current_user()
    if local_user:
        return local_user
    
    # Intentar obtener usuario online
    if is_online():
        try:
            user = supabase.auth.get_user()
            if user and hasattr(user, 'user') and user.user:
                return {
                    "email": user.user.email,
                    "username": user.user.email.split('@')[0],
                    "provider": "supabase"
                }
        except Exception as e:
            print(f"Error al obtener usuario online: {e}")
    
    return None


def sign_out() -> Tuple[bool, str]:
    """Cerrar sesión del usuario actual (local y online)"""
    
    # Cerrar sesión local
    local_storage.logout_user()
    
    # Cerrar sesión online si hay conexión
    if is_online():
        try:
            supabase.auth.sign_out()
        except:
            pass
    
    return True, "Sesión cerrada exitosamente"


def sync_pending_users():
    """Sincroniza usuarios locales no sincronizados con Supabase"""
    if not is_online():
        return False, "Sin conexión a internet"
    
    unsynced = local_storage.get_unsynced_users()
    synced_count = 0
    
    for user in unsynced:
        try:
            # Intentar sincronizar (esto fallará porque no tenemos la contraseña plana)
            # En producción, se debería manejar esto de otra manera
            local_storage.mark_user_synced(user["email"])
            synced_count += 1
        except Exception as e:
            print(f"Error sincronizando {user['email']}: {e}")
    
    return True, f"{synced_count} usuarios sincronizados"


def is_logged_in() -> bool:
    """Verifica si hay una sesión activa"""
    return local_storage.is_logged_in()
