# Configuración de OAuth con Supabase para Aplicación de Escritorio

## Problema Identificado
La autenticación con Google/Facebook en aplicaciones de escritorio requiere configuración especial porque el flujo OAuth redirige al navegador web y luego debe volver a la aplicación.

## Solución Implementada

### 1. Servidor Local de Callback
Se implementó un servidor HTTP temporal en `utils/auth.py` que:
- Escucha en `http://localhost:8000`
- Recibe el callback de autenticación de Supabase
- Muestra una página de confirmación al usuario
- Captura el token de acceso
- Se cierra automáticamente después de la autenticación

### 2. Configuración Requerida en Supabase

Para que esto funcione, necesitas configurar lo siguiente en tu proyecto de Supabase:

#### Paso 1: Acceder a la configuración de autenticación
1. Ve a tu dashboard de Supabase: https://app.supabase.com
2. Selecciona tu proyecto
3. Ve a **Authentication** → **URL Configuration**

#### Paso 2: Agregar Redirect URLs
En el campo "Redirect URLs", agrega las siguientes URLs (una por línea):

```
http://localhost:8000
http://localhost:8000/
```

#### Paso 3: Configurar proveedores OAuth

##### Google OAuth
1. Ve a **Authentication** → **Providers** → **Google**
2. Habilita el proveedor de Google
3. Necesitas crear credenciales en Google Cloud Console:
   - Ve a: https://console.cloud.google.com
   - Crea un proyecto nuevo o selecciona uno existente
   - Ve a **APIs & Services** → **Credentials**
   - Crea un **OAuth 2.0 Client ID**
   - Tipo de aplicación: **Desktop app** (o Web application)
   - Authorized redirect URIs:
     ```
     http://localhost:8000
     https://rlnltxkgvpkfztkzotyj.supabase.co/auth/v1/callback
     ```
   - Copia el **Client ID** y **Client Secret**
4. Pega estas credenciales en Supabase (Google Provider)
5. Guarda los cambios

##### Facebook OAuth
1. Ve a **Authentication** → **Providers** → **Facebook**
2. Habilita el proveedor de Facebook
3. Necesitas crear una app en Facebook Developers:
   - Ve a: https://developers.facebook.com
   - Crea una nueva app (tipo: Consumer)
   - Ve a **Settings** → **Basic**
   - Copia el **App ID** y **App Secret**
   - Ve a **Facebook Login** → **Settings**
   - En "Valid OAuth Redirect URIs" agrega:
     ```
     http://localhost:8000
     https://rlnltxkgvpkfztkzotyj.supabase.co/auth/v1/callback
     ```
4. Pega el App ID y App Secret en Supabase (Facebook Provider)
5. Guarda los cambios

### 3. Flujo de Autenticación

```
Usuario hace clic en "Google" o "Facebook"
    ↓
Se inicia servidor local en puerto 8000
    ↓
Se abre navegador con URL de autenticación
    ↓
Usuario se autentica con Google/Facebook
    ↓
Google/Facebook redirige a Supabase
    ↓
Supabase redirige a http://localhost:8000
    ↓
Servidor local captura el token
    ↓
Muestra página de éxito
    ↓
Token se procesa en la aplicación
    ↓
Usuario entra al panel principal
```

### 4. Verificación del Funcionamiento

Para probar que todo funciona:

1. Ejecuta la aplicación
2. Haz clic en el botón "Google" o "Facebook"
3. Deberías ver en la consola:
   ```
   Abriendo navegador para login con google...
   URL de callback configurada: http://localhost:8000
   Esperando autenticación en el navegador...
   ```
4. Se abrirá tu navegador web
5. Selecciona tu cuenta de Google/Facebook
6. Deberías ver una página de éxito con el mensaje "¡Autenticación Exitosa!"
7. La aplicación debería mostrar: `✓ Autenticación exitosa con google`
8. Y deberías entrar al panel principal

### 5. Solución de Problemas

#### Error: "Redirect URL not allowed"
- Verifica que `http://localhost:8000` esté en las Redirect URLs de Supabase
- Asegúrate de no tener espacios extra o errores de tipeo
- Guarda los cambios en Supabase y espera unos segundos

#### Error: "OAuth provider not configured"
- Verifica que hayas habilitado y configurado correctamente el proveedor en Supabase
- Asegúrate de tener las credenciales correctas de Google Cloud Console o Facebook Developers
- Revisa que las redirect URIs en Google/Facebook coincidan con las configuradas

#### El navegador abre pero no redirige
- Verifica que el puerto 8000 no esté siendo usado por otra aplicación
- Intenta cerrar y volver a abrir la aplicación
- Revisa el firewall de Windows para asegurarte de que no bloquee el puerto 8000

#### Timeout: "Tiempo de espera agotado"
- El servidor espera 120 segundos (2 minutos) por la autenticación
- Si tardas más, tendrás que intentar de nuevo
- Puedes aumentar el timeout en `utils/auth.py`, línea donde dice `timeout=120`

### 6. Alternativas de Implementación

Si el servidor local no funciona en tu entorno, hay otras opciones:

#### Opción A: Deep Linking (Más complejo)
- Registrar un protocolo personalizado (xentraders://)
- Configurar el sistema operativo para que abra tu app con ese protocolo
- Usar ese protocolo como redirect URI

#### Opción B: Copiar Token Manualmente (Más simple pero menos UX)
- Mostrar un cuadro de texto donde el usuario pegue el token
- Dar instrucciones de cómo obtenerlo manualmente

#### Opción C: WebView Integrado (Más profesional)
- Usar un componente WebView dentro de la aplicación
- Capturar el redirect internamente sin servidor local
- Requiere librerías adicionales como `webview` o `PyQt5`

### 7. Mejoras Futuras

- Implementar manejo de refresh tokens para mantener la sesión
- Agregar almacenamiento seguro de tokens (encrypted)
- Implementar flujo de recuperación de contraseña
- Agregar verificación de email en el registro
- Mostrar mensajes de error más amigables en la UI
- Implementar logout completo

### 8. Código Relevante

Los archivos modificados son:
- `utils/auth.py`: Lógica de autenticación con servidor callback
- `gui/login_view.py`: Interfaz de usuario con botones OAuth mejorados

### 9. Seguridad

⚠️ **IMPORTANTE**: 
- Nunca compartas tus credenciales de Supabase en repositorios públicos
- Usa variables de entorno para almacenar:
  - `SUPABASE_URL`
  - `SUPABASE_KEY`
  - `GOOGLE_CLIENT_ID`
  - `GOOGLE_CLIENT_SECRET`
  - `FACEBOOK_APP_ID`
  - `FACEBOOK_APP_SECRET`

Ejemplo de uso con variables de entorno:

```python
import os
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
```

### 10. Testing

Para probar sin afectar usuarios reales:
1. Usa el modo de prueba de Google Cloud Console
2. Usa cuentas de prueba de Facebook Developer
3. Crea un proyecto de Supabase separado para desarrollo

## Conclusión

Con esta implementación, tu aplicación de escritorio puede autenticar usuarios mediante Google y Facebook de forma segura. El flujo es transparente para el usuario y maneja correctamente el redirect desde el navegador hacia la aplicación.

Si tienes problemas, revisa los logs en la consola y verifica cada paso de la configuración en Supabase, Google Cloud Console y Facebook Developers.
