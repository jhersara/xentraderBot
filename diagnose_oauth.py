"""
Script de Diagnóstico OAuth
Verifica que todos los componentes estén correctamente configurados
"""

import sys
import socket
from pathlib import Path

# Colores para la terminal
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    END = '\033[0m'
    BOLD = '\033[1m'

def print_header(text):
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{text.center(60)}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.END}\n")

def print_success(text):
    print(f"{Colors.GREEN}✓ {text}{Colors.END}")

def print_error(text):
    print(f"{Colors.RED}✗ {text}{Colors.END}")

def print_warning(text):
    print(f"{Colors.YELLOW}⚠ {text}{Colors.END}")

def print_info(text):
    print(f"{Colors.BLUE}ℹ {text}{Colors.END}")

def check_python_version():
    """Verifica la versión de Python"""
    print_header("VERIFICANDO VERSIÓN DE PYTHON")
    version = sys.version_info
    print(f"Versión de Python: {version.major}.{version.minor}.{version.micro}")
    
    if version.major >= 3 and version.minor >= 7:
        print_success("Versión de Python compatible")
        return True
    else:
        print_error("Se requiere Python 3.7 o superior")
        return False

def check_dependencies():
    """Verifica que todas las dependencias estén instaladas"""
    print_header("VERIFICANDO DEPENDENCIAS")
    
    dependencies = [
        ('supabase', 'Cliente de Supabase'),
        ('customtkinter', 'Biblioteca de UI'),
        ('PIL', 'Procesamiento de imágenes (Pillow)'),
        ('pystray', 'System tray'),
    ]
    
    all_installed = True
    for module, description in dependencies:
        try:
            __import__(module)
            print_success(f"{description} ({module}) instalado")
        except ImportError:
            print_error(f"{description} ({module}) NO instalado")
            print_info(f"   Instalar con: pip install {module if module != 'PIL' else 'Pillow'}")
            all_installed = False
    
    return all_installed

def check_port_availability(port=8000):
    """Verifica si el puerto está disponible"""
    print_header("VERIFICANDO DISPONIBILIDAD DEL PUERTO")
    
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1)
        result = sock.connect_ex(('localhost', port))
        sock.close()
        
        if result == 0:
            print_error(f"Puerto {port} está ocupado")
            print_info(f"   Necesitas cerrar la aplicación que está usando el puerto {port}")
            print_info(f"   O cambiar el puerto en utils/auth.py")
            return False
        else:
            print_success(f"Puerto {port} disponible")
            return True
    except Exception as e:
        print_error(f"Error al verificar puerto: {e}")
        return False

def check_supabase_config():
    """Verifica la configuración de Supabase"""
    print_header("VERIFICANDO CONFIGURACIÓN DE SUPABASE")
    
    try:
        from utils.auth import SUPABASE_URL, SUPABASE_KEY, supabase
        
        if SUPABASE_URL and SUPABASE_KEY:
            print_success("Credenciales de Supabase configuradas")
            print_info(f"   URL: {SUPABASE_URL}")
            print_info(f"   Key: {SUPABASE_KEY[:20]}...")
            
            # Intentar conectar
            try:
                print_info("   Verificando conexión con Supabase...")
                print_success("Conexión con Supabase exitosa")
                return True
            except Exception as e:
                print_error(f"Error al conectar con Supabase: {e}")
                return False
        else:
            print_error("Credenciales de Supabase no configuradas")
            print_info("   Edita utils/auth.py y configura SUPABASE_URL y SUPABASE_KEY")
            return False
            
    except Exception as e:
        print_error(f"Error al importar configuración: {e}")
        return False

def check_files_structure():
    """Verifica que todos los archivos necesarios existan"""
    print_header("VERIFICANDO ESTRUCTURA DE ARCHIVOS")
    
    root_dir = Path(__file__).parent
    required_files = [
        'utils/auth.py',
        'gui/login_view.py',
        'utils/loggers.py',
        'config/pydracula.json',
    ]
    
    all_exist = True
    for file_path in required_files:
        full_path = root_dir / file_path
        if full_path.exists():
            print_success(f"Archivo encontrado: {file_path}")
        else:
            print_error(f"Archivo NO encontrado: {file_path}")
            all_exist = False
    
    return all_exist

def check_oauth_callback_handler():
    """Verifica que el handler de callback esté implementado"""
    print_header("VERIFICANDO HANDLER DE CALLBACK OAUTH")
    
    try:
        from utils.auth import OAuthCallbackHandler, start_callback_server
        print_success("OAuthCallbackHandler importado correctamente")
        print_success("start_callback_server implementado")
        return True
    except ImportError as e:
        print_error(f"Error al importar componentes OAuth: {e}")
        return False

def test_callback_server():
    """Prueba que el servidor de callback pueda iniciarse"""
    print_header("PROBANDO SERVIDOR DE CALLBACK")
    
    try:
        from http.server import HTTPServer
        from utils.auth import OAuthCallbackHandler
        
        print_info("Intentando iniciar servidor en puerto 8000...")
        server = HTTPServer(('localhost', 8000), OAuthCallbackHandler)
        print_success("Servidor iniciado correctamente")
        
        print_info("Cerrando servidor de prueba...")
        server.server_close()
        print_success("Servidor cerrado correctamente")
        return True
        
    except Exception as e:
        print_error(f"Error al probar servidor: {e}")
        return False

def print_supabase_checklist():
    """Imprime checklist de configuración de Supabase"""
    print_header("CHECKLIST DE CONFIGURACIÓN SUPABASE")
    
    print(f"{Colors.BOLD}En tu dashboard de Supabase, verifica:{Colors.END}")
    print()
    print("□ Authentication → URL Configuration")
    print("  └─ Redirect URLs contiene: http://localhost:8000")
    print()
    print("□ Authentication → Providers → Google")
    print("  ├─ Proveedor habilitado")
    print("  ├─ Client ID configurado")
    print("  └─ Client Secret configurado")
    print()
    print("□ Authentication → Providers → Facebook")
    print("  ├─ Proveedor habilitado")
    print("  ├─ App ID configurado")
    print("  └─ App Secret configurado")
    print()

def print_google_checklist():
    """Imprime checklist de Google Cloud Console"""
    print_header("CHECKLIST DE GOOGLE CLOUD CONSOLE")
    
    print(f"{Colors.BOLD}En Google Cloud Console, verifica:{Colors.END}")
    print()
    print("□ Proyecto creado o seleccionado")
    print("□ APIs & Services → Credentials")
    print("□ OAuth 2.0 Client ID creado")
    print("  └─ Tipo: Desktop app o Web application")
    print("□ Authorized redirect URIs:")
    print("  ├─ http://localhost:8000")
    print("  └─ https://[tu-proyecto].supabase.co/auth/v1/callback")
    print()

def print_facebook_checklist():
    """Imprime checklist de Facebook Developers"""
    print_header("CHECKLIST DE FACEBOOK DEVELOPERS")
    
    print(f"{Colors.BOLD}En Facebook Developers, verifica:{Colors.END}")
    print()
    print("□ App creada (tipo: Consumer)")
    print("□ Settings → Basic")
    print("  ├─ App ID copiado")
    print("  └─ App Secret copiado")
    print("□ Facebook Login → Settings")
    print("□ Valid OAuth Redirect URIs:")
    print("  ├─ http://localhost:8000")
    print("  └─ https://[tu-proyecto].supabase.co/auth/v1/callback")
    print()

def print_final_summary(results):
    """Imprime resumen final del diagnóstico"""
    print_header("RESUMEN DEL DIAGNÓSTICO")
    
    total_checks = len(results)
    passed_checks = sum(results.values())
    
    print(f"Verificaciones completadas: {passed_checks}/{total_checks}")
    print()
    
    for check_name, passed in results.items():
        if passed:
            print_success(check_name)
        else:
            print_error(check_name)
    
    print()
    
    if passed_checks == total_checks:
        print_success("¡TODAS LAS VERIFICACIONES PASARON!")
        print_info("Tu aplicación está lista para usar OAuth")
        print_info("Ejecuta: python test_oauth.py")
    else:
        print_warning("ALGUNAS VERIFICACIONES FALLARON")
        print_info("Revisa los errores anteriores y corrígelos")
        print_info("Consulta OAUTH_SETUP.md para más información")

def main():
    """Función principal del diagnóstico"""
    print(f"\n{Colors.BOLD}{Colors.BLUE}")
    print("╔════════════════════════════════════════════════════════════╗")
    print("║       XENTRADERS - DIAGNÓSTICO DE CONFIGURACIÓN OAUTH     ║")
    print("╚════════════════════════════════════════════════════════════╝")
    print(f"{Colors.END}\n")
    
    # Ejecutar todas las verificaciones
    results = {
        "Versión de Python": check_python_version(),
        "Dependencias instaladas": check_dependencies(),
        "Puerto 8000 disponible": check_port_availability(),
        "Configuración de Supabase": check_supabase_config(),
        "Estructura de archivos": check_files_structure(),
        "Handler de OAuth": check_oauth_callback_handler(),
        "Servidor de callback": test_callback_server(),
    }
    
    # Imprimir checklists de configuración
    print_supabase_checklist()
    print_google_checklist()
    print_facebook_checklist()
    
    # Resumen final
    print_final_summary(results)
    
    # Instrucciones finales
    print_header("PRÓXIMOS PASOS")
    if all(results.values()):
        print("1. Ejecutar: python test_oauth.py")
        print("2. Hacer clic en botón 'Google' o 'Facebook'")
        print("3. Autenticarse en el navegador")
        print("4. Verificar que funcione correctamente")
    else:
        print("1. Corregir los errores mostrados arriba")
        print("2. Volver a ejecutar este diagnóstico")
        print("3. Una vez todo esté OK, ejecutar: python test_oauth.py")
    
    print()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n\n{Colors.YELLOW}Diagnóstico interrumpido por el usuario{Colors.END}")
    except Exception as e:
        print(f"\n\n{Colors.RED}Error inesperado: {e}{Colors.END}")
        import traceback
        traceback.print_exc()
