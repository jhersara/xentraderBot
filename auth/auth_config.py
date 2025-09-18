# auth_config.py
# Codigo que se va a encargar de las autentificaciones

class Authenticate:
    def __init__(self):
        super().__init__(self)

    
    def AuthLogin(self, user, password):
        self.user = user
        self.pasword = password
    
    def AuthLoginFacebook(self, token):
        self.token = token

    def AuthLoginGoogle(self, token):
        self.token = token

    def redirectPage(self, action):
        pass

    def isLogin(self, state: bool) -> bool:
        self.state = state
        self.isAuth = True
    
