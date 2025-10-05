# Guía Rápida: Configuración OAuth

## 🚀 Inicio Rápido

### 1. Configurar Supabase (5 minutos)

1. Ve a: https://app.supabase.com
2. Abre tu proyecto
3. **Authentication** → **URL Configuration**
4. En "Redirect URLs" agrega:
   ```
   http://localhost:8000
   ```
5. Haz clic en "Save"

### 2. Configurar Google OAuth (10 minutos)

1. Ve a: https://console.cloud.google.com
2. Crea/selecciona un proyecto
3. **APIs & Services** → **Credentials** → **Create Credentials** → **OAuth client ID**
4. Application type: **Desktop app** (o Web application)
5. Authorized redirect URIs:
   ```
   http://localhost:8000
   https://rlnltxkgvpkfztkzotyj.supabase.co/auth/v1/callback
   ```
6. Copia el **Client ID** y **Client Secret**
7. En Supabase: **Authentication** → **Providers** → **Google**
8. Pega las credenciales y guarda

### 3. Configurar Facebook OAuth (10 minutos)

1. Ve a: https://developers.facebook.com
2. Crea una nueva app (tipo: Consumer)
3. **Settings** → **Basic** → copia **App ID** y **App Secret**
4. **Facebook Login** → **Settings**
5. En "Valid OAuth Redirect URIs":
   ```
   http://localhost:8000
   https://rlnltxkgvpkfztkzotyj.supabase.co/auth/v1/callback
   ```
6. En Supabase: **Authentication** → **Providers** → **Facebook**
7. Pega las credenciales y guarda

### 4. Probar la Aplicación

```bash
# Ejecutar el script de prueba
python test_oauth.py
```

O ejecutar la aplicación completa:
```bash
python main.py  # o como tengas configurado tu punto de entrada
```

## ✅ Verificación

Si todo está bien configurado, verás:

1. ✓ Botones de Google y Facebook funcionando
2. ✓ El navegador se abre automáticamente
3. ✓ Página de éxito después de seleccionar cuenta
4. ✓ La aplicación detecta el login exitoso
5. ✓ Entras al panel principal

## ❌ Errores Comunes

### "Redirect URL not allowed"
- Verifica que `http://localhost:8000` esté en Supabase
- Espera 30 segundos después de guardar cambios

### "OAuth provider not configured"
- Verifica que el proveedor esté habilitado en Supabase
- Revisa las credenciales de Google/Facebook

### "Timeout"
- El puerto 8000 puede estar ocupado
- Intenta reiniciar la aplicación

## 📚 Documentación Completa

Ver archivo: `OAUTH_SETUP.md` para detalles completos

## 🔧 Estructura de Archivos Modificados

```
xentraderBot/
├── utils/
│   └── auth.py              # ✨ Actualizado con servidor callback
├── gui/
│   └── login_view.py        # ✨ Actualizado con manejo OAuth
├── OAUTH_SETUP.md           # 📄 Documentación detallada
├── OAUTH_QUICKSTART.md      # 📄 Este archivo
└── test_oauth.py            # 🧪 Script de prueba
```

## 💡 Consejos

- Usa cuentas de prueba durante desarrollo
- Nunca compartas tus credenciales en Git
- Guarda tus credenciales en variables de entorno para producción

## 🆘 Soporte

Si tienes problemas:
1. Lee `OAUTH_SETUP.md` sección "Solución de Problemas"
2. Verifica los logs en la consola
3. Revisa que todas las URLs estén correctas (sin espacios extra)
4. Intenta con modo incógnito en el navegador

---

**¡Listo para usar! 🎉**
