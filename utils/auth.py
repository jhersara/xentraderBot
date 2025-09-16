# auth.py
from supabase import create_client, Client
from typing import Optional, Tuple
import webbrowser

# Cargar desde variables de entorno o un archivo seguro
SUPABASE_URL = "https://rlnltxkgvpkfztkzotyj.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InJsbmx0eGtndnBrZnp0a3pvdHlqIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTc4MTU0OTksImV4cCI6MjA3MzM5MTQ5OX0.SR-XYXW9TAOYYLxGAqDW8hExUaia4naQud-iNXnxMzU"  # ⚠️ mejor usar variables de entorno en producción

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

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

def sign_in_with_provider(provider: str) -> None:
    """Inicio de sesión social (abre navegador)"""
    try:
        res = supabase.auth.sign_in_with_oauth({"provider": provider})
        if hasattr(res, "url") and res.url:
            print(f"Abriendo navegador para login con: {provider}...")
            webbrowser.open(res.url)  # Abre la URL de login en navegador
        else:
            print(f"No se recibió URL de autenticación. Respuesta: {res}")
    except Exception as e:
        print(f"Error con proveedor {provider}: {e}")
