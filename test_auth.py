#!/usr/bin/env python3
# test_auth.py - Script de prueba del sistema de autenticación

import sys
from pathlib import Path

# Agregar el directorio raíz al path
sys.path.insert(0, str(Path(__file__).parent))

from utils.auth import (
    sign_up, 
    sign_in, 
    sign_out, 
    get_current_user, 
    is_logged_in,
    is_online
)

def print_separator():
    print("\n" + "="*60 + "\n")

def test_authentication():
    """Prueba el sistema de autenticación completo"""
    
    print("🔐 PRUEBA DEL SISTEMA DE AUTENTICACIÓN HÍBRIDO")
    print_separator()
    
    # 1. Verificar conexión
    print("1️⃣  Verificando conexión a internet...")
    online = is_online()
    print(f"   Estado: {'🟢 ONLINE' if online else '🔴 OFFLINE'}")
    print_separator()
    
    # 2. Crear usuario de prueba
    print("2️⃣  Registrando usuario de prueba...")
    test_email = "test@local.com"
    test_password = "Test123456"
    test_username = "TestUser"
    
    success, msg = sign_up(test_email, test_password, test_username)
    if success:
        print(f"   ✅ {msg}")
    else:
        print(f"   ℹ️  {msg}")
    print_separator()
    
    # 3. Iniciar sesión
    print("3️⃣  Iniciando sesión con el usuario de prueba...")
    success, msg = sign_in(test_email, test_password)
    if success:
        print(f"   ✅ {msg}")
    else:
        print(f"   ❌ {msg}")
        return
    print_separator()
    
    # 4. Verificar sesión activa
    print("4️⃣  Verificando sesión activa...")
    if is_logged_in():
        print("   ✅ Hay una sesión activa")
        user = get_current_user()
        if user:
            print(f"   👤 Usuario: {user['username']}")
            print(f"   📧 Email: {user['email']}")
            print(f"   🔗 Proveedor: {user.get('provider', 'local')}")
    else:
        print("   ❌ No hay sesión activa")
    print_separator()
    
    # 5. Cerrar sesión
    print("5️⃣  Cerrando sesión...")
    success, msg = sign_out()
    if success:
        print(f"   ✅ {msg}")
    else:
        print(f"   ❌ {msg}")
    print_separator()
    
    # 6. Verificar que la sesión se cerró
    print("6️⃣  Verificando que la sesión se cerró...")
    if not is_logged_in():
        print("   ✅ Sesión cerrada correctamente")
    else:
        print("   ❌ La sesión sigue activa")
    print_separator()
    
    # 7. Intentar login con credenciales incorrectas
    print("7️⃣  Probando login con contraseña incorrecta...")
    success, msg = sign_in(test_email, "wrong_password")
    if not success:
        print(f"   ✅ Error detectado correctamente: {msg}")
    else:
        print(f"   ❌ No se detectó el error de contraseña")
    print_separator()
    
    # 8. Login exitoso nuevamente
    print("8️⃣  Login exitoso con credenciales correctas...")
    success, msg = sign_in(test_email, test_password)
    if success:
        print(f"   ✅ {msg}")
    else:
        print(f"   ❌ {msg}")
    print_separator()
    
    print("🎉 PRUEBA COMPLETADA")
    print("\n📋 RESUMEN:")
    print(f"   • Modo: {'Online' if online else 'Offline'}")
    print(f"   • Usuario de prueba: {test_email}")
    print(f"   • Sesión activa: {'Sí' if is_logged_in() else 'No'}")
    print("\n💡 NOTA: Los archivos de datos locales están en storage/")
    print("   - storage/users.json (usuarios registrados)")
    print("   - storage/session.json (sesión actual)")
    print_separator()


def test_offline_mode():
    """Prueba específica del modo offline"""
    print("🔴 PRUEBA DEL MODO OFFLINE")
    print_separator()
    
    print("Para probar el modo offline:")
    print("1. Desconecta tu internet")
    print("2. Ejecuta este script nuevamente")
    print("3. El sistema debería funcionar sin conexión")
    print_separator()


def interactive_menu():
    """Menú interactivo para probar las funciones"""
    while True:
        print("\n" + "="*60)
        print("🔐 MENÚ DE PRUEBA DE AUTENTICACIÓN")
        print("="*60)
        print("1. Registrar nuevo usuario")
        print("2. Iniciar sesión")
        print("3. Ver usuario actual")
        print("4. Cerrar sesión")
        print("5. Ejecutar prueba automática")
        print("6. Verificar estado de conexión")
        print("0. Salir")
        print("="*60)
        
        choice = input("\nSelecciona una opción: ").strip()
        
        if choice == "1":
            print("\n📝 REGISTRO DE NUEVO USUARIO")
            email = input("Email: ").strip()
            password = input("Contraseña: ").strip()
            username = input("Nombre de usuario (opcional): ").strip() or None
            
            success, msg = sign_up(email, password, username)
            print(f"\n{'✅' if success else '❌'} {msg}")
            input("\nPresiona Enter para continuar...")
            
        elif choice == "2":
            print("\n🔑 INICIO DE SESIÓN")
            email = input("Email: ").strip()
            password = input("Contraseña: ").strip()
            
            success, msg = sign_in(email, password)
            print(f"\n{'✅' if success else '❌'} {msg}")
            input("\nPresiona Enter para continuar...")
            
        elif choice == "3":
            print("\n👤 USUARIO ACTUAL")
            if is_logged_in():
                user = get_current_user()
                print(f"Email: {user['email']}")
                print(f"Usuario: {user['username']}")
                print(f"Proveedor: {user.get('provider', 'local')}")
            else:
                print("❌ No hay sesión activa")
            input("\nPresiona Enter para continuar...")
            
        elif choice == "4":
            print("\n🚪 CERRAR SESIÓN")
            success, msg = sign_out()
            print(f"{'✅' if success else '❌'} {msg}")
            input("\nPresiona Enter para continuar...")
            
        elif choice == "5":
            test_authentication()
            input("\nPresiona Enter para continuar...")
            
        elif choice == "6":
            print("\n🌐 ESTADO DE CONEXIÓN")
            online = is_online()
            print(f"Estado: {'🟢 ONLINE' if online else '🔴 OFFLINE'}")
            input("\nPresiona Enter para continuar...")
            
        elif choice == "0":
            print("\n👋 ¡Hasta luego!")
            break
        else:
            print("\n❌ Opción inválida")
            input("\nPresiona Enter para continuar...")


if __name__ == "__main__":
    print("\n" + "="*60)
    print("🚀 SISTEMA DE AUTENTICACIÓN HÍBRIDO - XENTRADER BOT")
    print("="*60)
    print("\nElige el modo de prueba:")
    print("1. Prueba automática")
    print("2. Menú interactivo")
    print("="*60)
    
    mode = input("\nSelecciona una opción (1 o 2): ").strip()
    
    if mode == "1":
        test_authentication()
    elif mode == "2":
        interactive_menu()
    else:
        print("\n❌ Opción inválida. Ejecutando prueba automática...")
        test_authentication()
