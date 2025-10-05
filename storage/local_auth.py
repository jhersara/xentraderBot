# storage/local_auth.py
# Sistema de autenticación local para modo offline

import os
import json
import hashlib
import secrets
from pathlib import Path
from typing import Tuple, Optional, Dict
from datetime import datetime
import base64

class LocalAuthStorage:
    """Gestiona la autenticación local y offline"""
    
    def __init__(self, storage_dir: str = "storage"):
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(exist_ok=True)
        self.users_file = self.storage_dir / "users.json"
        self.session_file = self.storage_dir / "session.json"
        self._ensure_storage_exists()
    
    def _ensure_storage_exists(self):
        """Crea los archivos de almacenamiento si no existen"""
        if not self.users_file.exists():
            self._save_users({})
        if not self.session_file.exists():
            self._save_session({})
    
    def _hash_password(self, password: str, salt: str = None) -> Tuple[str, str]:
        """Hashea una contraseña con salt"""
        if salt is None:
            salt = secrets.token_hex(32)
        
        # Usar PBKDF2 para hashear la contraseña
        pwd_hash = hashlib.pbkdf2_hmac(
            'sha256',
            password.encode('utf-8'),
            salt.encode('utf-8'),
            100000  # 100,000 iteraciones
        )
        return base64.b64encode(pwd_hash).decode('utf-8'), salt
    
    def _verify_password(self, password: str, hashed: str, salt: str) -> bool:
        """Verifica una contraseña contra su hash"""
        pwd_hash, _ = self._hash_password(password, salt)
        return pwd_hash == hashed
    
    def _load_users(self) -> Dict:
        """Carga los usuarios del archivo"""
        try:
            with open(self.users_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {}
    
    def _save_users(self, users: Dict):
        """Guarda los usuarios en el archivo"""
        with open(self.users_file, 'w', encoding='utf-8') as f:
            json.dump(users, f, indent=2, ensure_ascii=False)
    
    def _load_session(self) -> Dict:
        """Carga la sesión actual"""
        try:
            with open(self.session_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {}
    
    def _save_session(self, session: Dict):
        """Guarda la sesión actual"""
        with open(self.session_file, 'w', encoding='utf-8') as f:
            json.dump(session, f, indent=2, ensure_ascii=False)
    
    def register_user(self, email: str, password: str, username: str = None) -> Tuple[bool, str]:
        """Registra un nuevo usuario localmente"""
        users = self._load_users()
        
        # Verificar si el usuario ya existe
        if email in users:
            return False, "El usuario ya existe"
        
        # Hashear la contraseña
        pwd_hash, salt = self._hash_password(password)
        
        # Guardar usuario
        users[email] = {
            "username": username or email.split('@')[0],
            "email": email,
            "password_hash": pwd_hash,
            "salt": salt,
            "created_at": datetime.now().isoformat(),
            "provider": "local",
            "synced": False
        }
        
        self._save_users(users)
        return True, "Usuario registrado localmente"
    
    def login_user(self, email: str, password: str) -> Tuple[bool, str]:
        """Inicia sesión localmente"""
        users = self._load_users()
        
        # Verificar si el usuario existe
        if email not in users:
            return False, "Usuario no encontrado"
        
        user = users[email]
        
        # Verificar contraseña
        if not self._verify_password(password, user["password_hash"], user["salt"]):
            return False, "Contraseña incorrecta"
        
        # Crear sesión
        session = {
            "email": email,
            "username": user["username"],
            "logged_in_at": datetime.now().isoformat(),
            "provider": "local"
        }
        self._save_session(session)
        
        return True, "Inicio de sesión exitoso"
    
    def is_logged_in(self) -> bool:
        """Verifica si hay una sesión activa"""
        session = self._load_session()
        return "email" in session
    
    def get_current_user(self) -> Optional[Dict]:
        """Obtiene el usuario actual de la sesión"""
        session = self._load_session()
        if not self.is_logged_in():
            return None
        
        users = self._load_users()
        email = session.get("email")
        
        if email in users:
            user_data = users[email].copy()
            user_data.pop("password_hash", None)
            user_data.pop("salt", None)
            return user_data
        
        return None
    
    def logout_user(self) -> Tuple[bool, str]:
        """Cierra la sesión actual"""
        self._save_session({})
        return True, "Sesión cerrada"
    
    def save_oauth_session(self, email: str, provider: str, username: str = None) -> Tuple[bool, str]:
        """Guarda una sesión de OAuth (Google/Facebook) localmente"""
        users = self._load_users()
        
        # Si el usuario no existe, crearlo
        if email not in users:
            users[email] = {
                "username": username or email.split('@')[0],
                "email": email,
                "provider": provider,
                "created_at": datetime.now().isoformat(),
                "synced": True  # OAuth siempre está sincronizado
            }
            self._save_users(users)
        
        # Crear sesión
        session = {
            "email": email,
            "username": username or email.split('@')[0],
            "logged_in_at": datetime.now().isoformat(),
            "provider": provider
        }
        self._save_session(session)
        
        return True, "Sesión OAuth guardada"
    
    def get_unsynced_users(self) -> list:
        """Obtiene usuarios que no se han sincronizado con Supabase"""
        users = self._load_users()
        return [
            {
                "email": email,
                "username": data["username"],
                "created_at": data["created_at"]
            }
            for email, data in users.items()
            if not data.get("synced", False) and data.get("provider") == "local"
        ]
    
    def mark_user_synced(self, email: str):
        """Marca un usuario como sincronizado"""
        users = self._load_users()
        if email in users:
            users[email]["synced"] = True
            self._save_users(users)
