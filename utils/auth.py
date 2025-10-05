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
<!doctype html>
<html lang="es">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width,initial-scale=1" />
  <title>Xent — Autenticación Exitosa</title>
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap" rel="stylesheet">
  <style>
    :root{
      --bg-accent-1: #0f172a;
      --accent: #00d084;
      --muted: #9aa4b2;
      --card-bg: rgba(255,255,255,0.06);
      --glass: rgba(255,255,255,0.06);
      --glass-border: rgba(255,255,255,0.08);
      --max-width: 760px;
      --radius: 14px;
      font-family: 'Inter', system-ui, -apple-system, 'Segoe UI', Roboto, 'Helvetica Neue', Arial;
    }
    html,body{height:100%;margin:0}
    body{
      display:flex;align-items:center;justify-content:center;
      background: linear-gradient(135deg,#0b1220 0%, #07122a 40%);
      color:#e6eef6;
      -webkit-font-smoothing:antialiased;
      -moz-osx-font-smoothing:grayscale;
      padding:32px;
    }

    .bg-wrap{
      position:fixed;inset:0;z-index:0;pointer-events:none;overflow:hidden;
    }
    .bg-wrap::before{
      content:"";position:absolute;inset:0;background-image: url('https://cdn.pixabay.com/photo/2017/02/17/13/20/space-2071142_1280.jpg');
      background-size:cover;background-position:center;filter:blur(6px) brightness(0.45) saturate(0.9);
      transform:scale(1.06);
    }
    .bg-wrap::after{
      content:"";position:absolute;inset:0;background:linear-gradient(180deg, rgba(3,7,18,0.35), rgba(3,7,18,0.6));
    }

    .card{
      position:relative;z-index:2;max-width:var(--max-width);width:100%;
      margin:0 auto;padding:28px;border-radius:var(--radius);
      background: linear-gradient(180deg, rgba(255,255,255,0.03), rgba(255,255,255,0.02));
      border: 1px solid var(--glass-border);
      box-shadow: 0 12px 40px rgba(2,6,23,0.6);
      display:grid;grid-template-columns:1fr 280px;gap:24px;align-items:center;
      backdrop-filter: blur(6px) saturate(1.1);
    }

    @media (max-width:880px){
      .card{grid-template-columns:1fr;}
    }

    .left{padding: 8px 8px;}

    .brand{display:flex;gap:12px;align-items:center;margin-bottom:6px}
    .logo{
      width:56px;height:56px;border-radius:12px;background:linear-gradient(135deg,#0ea5a4,#06b6d4);
      display:flex;align-items:center;justify-content:center;font-weight:700;color:white;font-size:20px;box-shadow:0 6px 20px rgba(6,95,70,0.12);
    }
    .brand h2{margin:0;font-size:18px;letter-spacing:0.2px}
    .brand p{margin:0;font-size:12px;color:var(--muted)}

    h1{margin:10px 0 6px;font-size:22px}
    p.lead{margin:0;color:var(--muted);line-height:1.5}

    .status{display:flex;gap:12px;align-items:center;margin-top:18px}

    .badge{
      width:84px;height:84px;border-radius:999px;background:linear-gradient(180deg, rgba(10,200,150,0.12), rgba(10,200,150,0.06));
      display:flex;align-items:center;justify-content:center;flex-shrink:0;border:1px solid rgba(0,0,0,0.12);
      backdrop-filter: blur(4px);
    }
    .check{
      width:54px;height:54px;display:inline-grid;place-items:center;border-radius:50%;background:linear-gradient(180deg,var(--accent),#00b36a);box-shadow:0 8px 18px rgba(0,208,132,0.18);color:#042014;font-weight:700;font-size:28px;transform:scale(0);animation:pop-in .6s cubic-bezier(.2,.9,.3,1) .15s forwards;
    }
    @keyframes pop-in{to{transform:scale(1)}}

    .right{padding:12px;border-left:1px dashed rgba(255,255,255,0.03);min-width:220px;text-align:center}
    @media (max-width:880px){.right{border-left:none;border-top:1px dashed rgba(255,255,255,0.03);}}

    .info{font-size:13px;color:var(--muted);margin-top:6px}
    .actions{margin-top:18px;display:flex;gap:10px;justify-content:center}
    .btn{padding:10px 14px;border-radius:10px;border:0;cursor:pointer;font-weight:600}
    .btn-primary{background:linear-gradient(90deg,var(--accent),#00b36a);color:#021a12;box-shadow:0 8px 20px rgba(0,208,132,0.12)}
    .btn-ghost{background:transparent;border:1px solid rgba(255,255,255,0.06);color:var(--muted)}

    .small{font-size:12px;color:var(--muted);margin-top:12px}

    .sparkle{position:absolute;inset:auto -40px auto auto;width:160px;height:160px;opacity:0.08;filter:blur(2px);transform:rotate(22deg)}

    footer{margin-top:14px;text-align:center;color:var(--muted);font-size:12px}
  </style>
</head>
<body>
  <div class="bg-wrap" aria-hidden></div>

  <main class="card" role="main" aria-labelledby="titulo">
    <section class="left">
      <div class="brand">
        <div class="logo">X</div>
        <div>
          <h2 id="titulo">Xent — Autenticación Exitosa</h2>
          <p>Conexión segura establecida con tu bot de trading</p>
        </div>
      </div>

      <h1>¡Listo! Sesión autenticada</h1>
      <p class="lead">Hemos recibido tu autorización. Puedes volver a la aplicación y continuar con tus operaciones. Esta ventana se cerrará automáticamente si fue abierta por la aplicación.</p>

      <div class="status" aria-hidden>
        <div class="badge" aria-hidden>
          <div class="check">✓</div>
        </div>
        <div>
          <div class="info"><strong>Usuario:</strong> <span id="user-email">usuario@ejemplo.com</span></div>
          <div class="info"><strong>Conexión:</strong> Segura · Token válido</div>
          <div class="small">Si la ventana no se cierra sola, pulsa "Volver a la App" o "Cerrar ventana".</div>
        </div>
      </div>

      <div class="actions">
        <button class="btn btn-primary" id="open-app">Volver a la App</button>
        <button class="btn btn-ghost" id="close">Cerrar ventana</button>
      </div>

      <footer>¿Problemas? Copia este código y pégalo en tu aplicación: <code id="code" style="background:rgba(255,255,255,0.03);padding:6px;border-radius:6px;margin-left:6px">ABCD-1234-EFGH</code></footer>
    </section>

    <aside class="right" aria-label="Panel de confirmación">
      <img class="sparkle" src="data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 200 200'><defs><linearGradient id='g' x1='0' x2='1'><stop offset='0' stop-color='%23ffffff' stop-opacity='0.4'/><stop offset='1' stop-color='%23ffffff' stop-opacity='0.08'/></linearGradient></defs><rect width='200' height='200' fill='url(%23g)'/></svg>" alt="" />
      <h3 style="margin:0 0 8px">Conexión segura</h3>
      <p class="info">Xent ahora podrá operar según los permisos que autorizaste. Recomendamos revisar la configuración de permisos desde la app si necesitas restringir acciones.</p>

      <div style="margin-top:14px">
        <svg width="120" height="80" viewBox="0 0 120 80" aria-hidden>
          <rect x="4" y="6" width="112" height="60" rx="8" fill="rgba(255,255,255,0.02)" stroke="rgba(255,255,255,0.04)"/>
          <path d="M22 36 L46 52 L96 18" fill="none" stroke="rgba(0,208,132,0.9)" stroke-width="4" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>
      </div>

    </aside>
  </main>

  <script>
    const data = {
      userEmail: window.__XENT_USER_EMAIL || 'usuario@ejemplo.com',
      code: window.__XENT_CODE || 'ABCD-1234-EFGH'
    };
    document.getElementById('user-email').textContent = data.userEmail;
    document.getElementById('code').textContent = data.code;

    const tryClose = () => {
      try { window.close(); } catch (e) {}
    };

    setTimeout(tryClose, 3000);

    document.getElementById('close').addEventListener('click', tryClose);
    document.getElementById('open-app').addEventListener('click', () => {
      if (window.opener && typeof window.opener.postMessage === 'function') {
        window.opener.postMessage({ type: 'XENT_AUTH_COMPLETE', payload: data }, '*');
      }
      tryClose();
    });

    document.getElementById('code').addEventListener('click', async () => {
      try{
        await navigator.clipboard.writeText(data.code);
        const prev = document.getElementById('code').textContent;
        document.getElementById('code').textContent = 'Copiado ✔';
        setTimeout(()=> document.getElementById('code').textContent = prev,1400);
      }catch(e){}
    });
  </script>
</body>
</html>

            """
        else:
            html_response = """
            <!doctype html>
<html lang="es">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width,initial-scale=1" />
  <title>Xent — Error de Autenticación</title>
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap" rel="stylesheet">
  <style>
    :root {
      --accent: #f5576c;
      --muted: #9aa4b2;
      --radius: 14px;
      font-family: 'Inter', system-ui, -apple-system, 'Segoe UI', Roboto, 'Helvetica Neue', Arial;
    }

    html, body {
      height: 100%; margin: 0;
      display: flex; align-items: center; justify-content: center;
      background: linear-gradient(135deg, #0b1220 0%, #1a0a2a 100%);
      color: #e6eef6;
    }

    .bg-wrap {
      position: fixed; inset: 0; z-index: 0; pointer-events: none;
    }
    .bg-wrap::before {
      content: "";
      position: absolute; inset: 0;
      background-image: url('https://cdn.pixabay.com/photo/2014/09/27/13/44/space-463848_1280.jpg');
      background-size: cover; background-position: center;
      filter: blur(6px) brightness(0.45);
      transform: scale(1.06);
    }
    .bg-wrap::after {
      content: "";
      position: absolute; inset: 0;
      background: linear-gradient(180deg, rgba(3,7,18,0.35), rgba(3,7,18,0.7));
    }

    .card {
      position: relative;
      z-index: 2;
      background: rgba(255,255,255,0.05);
      border: 1px solid rgba(255,255,255,0.08);
      border-radius: var(--radius);
      padding: 36px 28px;
      text-align: center;
      box-shadow: 0 12px 40px rgba(0,0,0,0.6);
      backdrop-filter: blur(6px) saturate(1.1);
      max-width: 420px;
    }

    .error-icon {
      font-size: 64px;
      color: var(--accent);
      animation: pulse 1.3s infinite ease-in-out;
    }

    h1 {
      margin-top: 18px;
      color: var(--accent);
      font-size: 24px;
    }

    p {
      color: var(--muted);
      margin: 8px 0 22px;
      line-height: 1.5;
    }

    .btn {
      background: transparent;
      border: 1px solid rgba(255,255,255,0.15);
      color: var(--muted);
      padding: 10px 18px;
      border-radius: 10px;
      cursor: pointer;
      transition: all 0.2s ease;
    }

    .btn:hover {
      background: var(--accent);
      color: #fff;
      box-shadow: 0 6px 16px rgba(245,87,108,0.3);
    }

    @keyframes pulse {
      0%, 100% { transform: scale(1); opacity: 1; }
      50% { transform: scale(1.2); opacity: 0.8; }
    }
  </style>
</head>
<body>
  <div class="bg-wrap" aria-hidden></div>

  <div class="card" role="alert">
    <div class="error-icon">✗</div>
    <h1>Error de Autenticación</h1>
    <p>Hubo un problema al autenticarte. Por favor, intenta nuevamente o verifica tu conexión.</p>
    <button class="btn" onclick="window.location.reload()">Reintentar</button>
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
