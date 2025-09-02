# auth/auth.py

# Usuarios de ejemplo (hardcodeado por ahpora)
USERS= {
    "admin": "1234",
    "trader": "abcd",
    "liners": "117-liners"
}

# Funcion de autentificacion
def authenticate(username: str, password: str) -> bool:
    return USERS.get(username) == password