# Mejores Prácticas de Seguridad OAuth

## ⚠️ IMPORTANTE: Protección de Credenciales

### 1. NO HARDCODEAR CREDENCIALES

❌ **INCORRECTO** (actual en el código):
```python
SUPABASE_URL = "https://rlnltxkgvpkfztkzotyj.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

✅ **CORRECTO** (usar variables de entorno):
```python
import os
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
```

### 2. Usar archivo .env

Crea un archivo `.env` en la raíz del proyecto:

```env
# .env
SUPABASE_URL=https://rlnltxkgvpkfztkzotyj.supabase.co
SUPABASE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
GOOGLE_CLIENT_ID=tu_client_id
GOOGLE_CLIENT_SECRET=tu_client_secret
FACEBOOK_APP_ID=tu_app_id
FACEBOOK_APP_SECRET=tu_app_secret
```

### 3. Agregar .env al .gitignore

```gitignore
# .gitignore
.env
*.pyc
__pycache__/
.vscode/
.idea/
*.log
```

### 4. Crear .env.example

```env
# .env.example
SUPABASE_URL=your_supabase_url_here
SUPABASE_KEY=your_supabase_anon_key_here
GOOGLE_CLIENT_ID=your_google_client_id
GOOGLE_CLIENT_SECRET=your_google_client_secret
FACEBOOK_APP_ID=your_facebook_app_id
FACEBOOK_APP_SECRET=your_facebook_app_secret
```

## 🔐 Implementación de Variables de Entorno

### Paso 1: Instalar python-dotenv

```bash
pip install python-dotenv
```

### Paso 2: Modificar utils/auth.py

```python
# utils/auth.py
from supabase import create_client, Client
import os
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Usar variables de entorno
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError("Las credenciales de Supabase no están configuradas. Verifica tu archivo .env")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
```

### Paso 3: Verificar en el código

Agrega validaciones:

```python
def validate_credentials():
    """Valida que las credenciales estén configuradas"""
    required_vars = {
        "SUPABASE_URL": os.getenv("SUPABASE_URL"),
        "SUPABASE_KEY": os.getenv("SUPABASE_KEY"),
    }
    
    missing = [key for key, value in required_vars.items() if not value]
    
    if missing:
        raise ValueError(
            f"Variables de entorno faltantes: {', '.join(missing)}\n"
            f"Crea un archivo .env basado en .env.example"
        )
    
    return True

# Validar al inicio
validate_credentials()
```

## 🛡️ Seguridad del Token de Acceso

### 1. Almacenamiento Seguro

❌ **NO HACER**:
```python
# Guardar en archivo de texto plano
with open("token.txt", "w") as f:
    f.write(access_token)
```

✅ **MEJOR OPCIÓN** (usando keyring):
```python
import keyring

# Guardar token
keyring.set_password("xentraders", "access_token", access_token)

# Recuperar token
token = keyring.get_password("xentraders", "access_token")
```

### 2. Instalación de keyring

```bash
pip install keyring
```

### 3. Implementación en el código

```python
# utils/token_manager.py
import keyring
from typing import Optional

SERVICE_NAME = "xentraders"

def save_token(token: str, user_id: str) -> bool:
    """Guarda el token de forma segura"""
    try:
        keyring.set_password(SERVICE_NAME, f"token_{user_id}", token)
        return True
    except Exception as e:
        print(f"Error guardando token: {e}")
        return False

def get_token(user_id: str) -> Optional[str]:
    """Recupera el token guardado"""
    try:
        return keyring.get_password(SERVICE_NAME, f"token_{user_id}")
    except Exception as e:
        print(f"Error recuperando token: {e}")
        return None

def delete_token(user_id: str) -> bool:
    """Elimina el token guardado"""
    try:
        keyring.delete_password(SERVICE_NAME, f"token_{user_id}")
        return True
    except Exception as e:
        print(f"Error eliminando token: {e}")
        return False
```

## 🔄 Renovación de Tokens

### Implementar Refresh Token

```python
# utils/auth.py
def refresh_session():
    """Renueva la sesión usando el refresh token"""
    try:
        session = supabase.auth.refresh_session()
        if session:
            # Guardar nuevo token
            save_token(session.access_token, session.user.id)
            return True
        return False
    except Exception as e:
        print(f"Error renovando sesión: {e}")
        return False

def get_current_session():
    """Obtiene la sesión actual o la renueva si es necesario"""
    try:
        session = supabase.auth.get_session()
        if not session:
            # Intentar renovar
            if refresh_session():
                return supabase.auth.get_session()
        return session
    except Exception as e:
        print(f"Error obteniendo sesión: {e}")
        return None
```

## 🌐 Seguridad de Red

### 1. Verificar HTTPS

Asegúrate de que todas las comunicaciones usen HTTPS:

```python
def validate_url(url: str) -> bool:
    """Valida que la URL use HTTPS"""
    if not url.startswith("https://"):
        raise ValueError(f"URL insegura detectada: {url}. Usa HTTPS.")
    return True

# Validar URL de Supabase
validate_url(SUPABASE_URL)
```

### 2. Timeout en Requests

```python
# Configurar timeout para evitar bloqueos
supabase = create_client(
    SUPABASE_URL, 
    SUPABASE_KEY,
    options={
        "timeout": 10  # 10 segundos de timeout
    }
)
```

## 📝 Logging Seguro

### NO registrar información sensible

❌ **INCORRECTO**:
```python
logger.info(f"Token recibido: {access_token}")
logger.info(f"Password: {password}")
```

✅ **CORRECTO**:
```python
logger.info(f"Token recibido: {access_token[:10]}...")
logger.info("Autenticación exitosa para usuario")
```

### Implementar logging seguro:

```python
import logging
import re

class SecureFormatter(logging.Formatter):
    """Formatter que oculta información sensible"""
    
    SENSITIVE_PATTERNS = [
        (r'token["\']?\s*:\s*["\']?([^"\']+)', r'token: ****'),
        (r'password["\']?\s*:\s*["\']?([^"\']+)', r'password: ****'),
        (r'secret["\']?\s*:\s*["\']?([^"\']+)', r'secret: ****'),
    ]
    
    def format(self, record):
        message = super().format(record)
        for pattern, replacement in self.SENSITIVE_PATTERNS:
            message = re.sub(pattern, replacement, message, flags=re.IGNORECASE)
        return message
```

## 🚨 Manejo de Errores

### Implementar manejo seguro de errores:

```python
def safe_login(email: str, password: str):
    """Login con manejo seguro de errores"""
    try:
        result = supabase.auth.sign_in_with_password({
            "email": email,
            "password": password
        })
        
        if result.user:
            logger.info(f"Login exitoso para: {email}")
            return True, "Login exitoso"
        
        return False, "Credenciales incorrectas"
        
    except Exception as e:
        # NO revelar detalles del error al usuario
        logger.error(f"Error en login: {str(e)}")
        return False, "Error al iniciar sesión. Intenta nuevamente."
```

## 🔒 Validación de Entrada

### Validar datos del usuario:

```python
import re

def validate_email(email: str) -> bool:
    """Valida formato de email"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_password(password: str) -> tuple[bool, str]:
    """Valida fortaleza de contraseña"""
    if len(password) < 8:
        return False, "La contraseña debe tener al menos 8 caracteres"
    
    if not re.search(r'[A-Z]', password):
        return False, "La contraseña debe tener al menos una mayúscula"
    
    if not re.search(r'[a-z]', password):
        return False, "La contraseña debe tener al menos una minúscula"
    
    if not re.search(r'[0-9]', password):
        return False, "La contraseña debe tener al menos un número"
    
    return True, "Contraseña válida"
```

## 🎯 Resumen de Mejores Prácticas

✅ **SIEMPRE**:
- Usar variables de entorno para credenciales
- Implementar .gitignore para proteger .env
- Usar HTTPS para todas las comunicaciones
- Almacenar tokens de forma segura (keyring)
- Validar entrada del usuario
- Manejar errores sin revelar información sensible
- Implementar refresh de tokens
- Registrar eventos sin información sensible

❌ **NUNCA**:
- Hardcodear credenciales en el código
- Guardar tokens en archivos de texto plano
- Commitear archivos .env al repositorio
- Registrar contraseñas o tokens completos
- Revelar detalles de errores al usuario
- Usar HTTP en lugar de HTTPS

## 📚 Recursos Adicionales

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [Supabase Security Best Practices](https://supabase.com/docs/guides/auth/security)
- [OAuth 2.0 Security](https://oauth.net/2/oauth-best-practice/)

---

**Nota**: Implementa estas prácticas gradualmente. Comienza con las variables de entorno y .gitignore, y luego agrega las demás según sea necesario.
