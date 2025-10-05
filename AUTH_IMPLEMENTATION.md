# 🔐 Sistema de Autenticación Local + Online

## ✨ Implementación Completada

Se ha implementado un **sistema de autenticación híbrido** que permite:

### ✅ Funcionalidades Implementadas

1. **Registro Local Offline**
   - Los usuarios pueden registrarse sin conexión a internet
   - Las contraseñas se hashean con PBKDF2 + salt (100,000 iteraciones)
   - Almacenamiento seguro en `storage/users.json`

2. **Login Local Offline**
   - Inicio de sesión sin requerir internet
   - Validación de credenciales contra base de datos local
   - Sesión persistente en `storage/session.json`

3. **Sincronización Automática**
   - Cuando hay internet, los datos se sincronizan con Supabase
   - Fallback automático a modo local si no hay conexión

4. **Indicador Visual de Conexión**
   - Muestra `● Online` (verde) o `● Offline` (rojo) en la barra superior
   - Se actualiza automáticamente cada 5 segundos

5. **OAuth Social (Google/Facebook)**
   - Funciona solo con conexión a internet
   - Guarda sesión localmente para uso posterior

---

## 📁 Archivos Creados/Modificados

### Nuevos Archivos:
```
storage/
├── __init__.py                 # Inicializador del módulo
├── local_auth.py              # Sistema de autenticación local
├── README.md                  # Documentación del sistema
└── .gitkeep                   # Mantiene carpeta en git

test_auth.py                   # Script de prueba completo
.gitignore                     # Protege archivos sensibles
```

### Archivos Modificados:
```
utils/auth.py                  # Autenticación híbrida (online + offline)
gui/login_view.py              # Indicador de conexión agregado
requirements.txt               # Dependencias actualizadas
```

---

## 🚀 Cómo Usar

### 1. Instalar Dependencias
```bash
pip install -r requirements.txt
```

### 2. Ejecutar Prueba
```bash
python test_auth.py
```

### 3. Usar en tu Aplicación
```python
from utils.auth import sign_up, sign_in, is_online

# Registro (funciona online y offline)
success, msg = sign_up("usuario@email.com", "password123", "Usuario")
print(msg)

# Login (funciona online y offline)
success, msg = sign_in("usuario@email.com", "password123")
if success:
    print("¡Bienvenido!")
```

---

## 🔒 Seguridad

### Almacenamiento de Contraseñas
- ✅ Hasheadas con PBKDF2-HMAC-SHA256
- ✅ 100,000 iteraciones (resistente a fuerza bruta)
- ✅ Salt único por contraseña
- ✅ NUNCA se guardan en texto plano

### Archivos Protegidos
Los siguientes archivos están en `.gitignore`:
- `storage/users.json` - Base de datos de usuarios
- `storage/session.json` - Sesión activa
- `config/secrets.json` - Configuración sensible

---

## 📊 Flujo de Autenticación

```
┌─────────────────────────────────────────────────┐
│          Usuario intenta registrarse            │
└────────────────┬────────────────────────────────┘
                 │
                 ▼
         ┌───────────────┐
         │ ¿Hay Internet? │
         └───────┬────────┘
                 │
        ┌────────┴────────┐
        │                 │
        ▼                 ▼
    [Online]          [Offline]
        │                 │
        ▼                 ▼
Registrar en         Registrar
  Supabase           localmente
        │                 │
        ▼                 ▼
Guardar sesión      Guardar sesión
  localmente          localmente
        │                 │
        └────────┬────────┘
                 │
                 ▼
        ┌────────────────┐
        │ Usuario logueado│
        └────────────────┘
```

---

## 🧪 Pruebas

### Modo Automático
```bash
python test_auth.py
# Selecciona opción 1
```

Prueba:
1. ✅ Verificación de conexión
2. ✅ Registro de usuario
3. ✅ Inicio de sesión
4. ✅ Verificación de sesión activa
5. ✅ Cierre de sesión
6. ✅ Validación de errores
7. ✅ Login con credenciales correctas

### Modo Interactivo
```bash
python test_auth.py
# Selecciona opción 2
```

Menú con opciones:
- Registrar nuevo usuario
- Iniciar sesión
- Ver usuario actual
- Cerrar sesión
- Ejecutar prueba automática
- Verificar estado de conexión

---

## 🌐 Escenarios de Uso

### Escenario 1: Usuario Nuevo (Online)
```python
# Usuario se registra con internet
sign_up("user@mail.com", "pass123")
# → Guardado en Supabase + local
# → Puede usar offline después
```

### Escenario 2: Usuario Nuevo (Offline)
```python
# Usuario se registra sin internet
sign_up("user@mail.com", "pass123")
# → Guardado solo localmente
# → Se sincronizará cuando haya internet
```

### Escenario 3: Login Existente (Online)
```python
# Usuario inicia sesión con internet
sign_in("user@mail.com", "pass123")
# → Valida contra Supabase
# → Guarda sesión localmente
```

### Escenario 4: Login Existente (Offline)
```python
# Usuario inicia sesión sin internet
sign_in("user@mail.com", "pass123")
# → Valida contra base de datos local
# → Funciona normalmente
```

---

## 💡 Características Técnicas

### LocalAuthStorage (storage/local_auth.py)
```python
class LocalAuthStorage:
    - register_user()        # Registrar usuario local
    - login_user()           # Login local
    - is_logged_in()         # Verificar sesión
    - get_current_user()     # Obtener usuario actual
    - logout_user()          # Cerrar sesión
    - save_oauth_session()   # Guardar sesión OAuth
    - get_unsynced_users()   # Usuarios no sincronizados
    - mark_user_synced()     # Marcar como sincronizado
```

### utils/auth.py (Funciones Híbridas)
```python
- sign_up()              # Registro híbrido
- sign_in()              # Login híbrido
- sign_in_with_provider() # OAuth (Google/Facebook)
- get_current_user()     # Usuario actual
- sign_out()             # Cerrar sesión
- is_online()            # Verificar conexión
- is_logged_in()         # Verificar sesión activa
- sync_pending_users()   # Sincronizar pendientes
```

---

## 📝 Notas Importantes

1. **Archivos JSON**: Los archivos `users.json` y `session.json` se crean automáticamente
2. **Git**: Los archivos de datos están protegidos con `.gitignore`
3. **OAuth**: Google/Facebook requieren configuración en Supabase
4. **Sincronización**: Automática al detectar conexión
5. **Seguridad**: Las contraseñas NUNCA se guardan en texto plano

---

## 🐛 Solución de Problemas

### Error: "ModuleNotFoundError: No module named 'supabase'"
```bash
pip install supabase
```

### Error: "No se puede conectar a Supabase"
- Verifica tu conexión a internet
- El sistema funcionará en modo offline automáticamente

### Los archivos JSON no se crean
- La carpeta `storage/` debe existir
- Se crean automáticamente al primer uso

---

## 🎯 Próximos Pasos Sugeridos

1. **Encriptación de Archivos**: Encriptar `users.json` y `session.json`
2. **Expiración de Sesiones**: Implementar timeout de sesión
3. **Recuperación de Contraseña**: Sistema de reset de password
4. **2FA**: Autenticación de dos factores
5. **Logs de Auditoría**: Registrar intentos de login

---

## ✅ Checklist de Implementación

- [x] Sistema de registro local
- [x] Sistema de login local
- [x] Hash de contraseñas con PBKDF2
- [x] Almacenamiento seguro
- [x] Sincronización con Supabase
- [x] Fallback automático offline
- [x] Indicador visual de conexión
- [x] Protección de archivos sensibles
- [x] Script de pruebas
- [x] Documentación completa

---

## 📞 Soporte

Para más información sobre el proyecto:
- Revisa el código en `storage/local_auth.py`
- Ejecuta `python test_auth.py` para probar
- Lee `storage/README.md` para detalles técnicos

¡Todo listo para usar! 🚀
