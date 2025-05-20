''' service related to google social login'''
from django.conf import settings
from rest_framework_simplejwt.tokens import RefreshToken
from urllib.parse import urlencode
from .models import User
from .serializers import UserSerializer
import secrets
import requests
from jose import jwt

class GoogleOAuth2Service():
    ''' google service class for social login'''
    client_id = settings.SOCIAL_AUTH_GOOGLE_OAUTH2_KEY
    client_secret = settings.SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET
    scope = settings.SOCIAL_AUTH_GOOGLE_OAUTH2_SCOPE
    redirect_uri = settings.SOCIAL_AUTH_GOOGLE_OAUTH2_REDIRECT_URI
    google_auth_endpoint = settings.SOCIAL_AUTH_GOOGLE_OAUTH2_AUTHORIZATION_ENDPOINT
    google_token_obtain_uri = settings.GOOGLE_ACCESS_TOKEN_OBTAIN_URI
    google_jwks_url = "https://www.googleapis.com/oauth2/v3/certs"  # URL for Google's public keys

    def getAuthorizationUri(self):
        ''' Get the Google authorization uri'''
        # state = secrets.token_hex(32)
        options = {
            'client_id': self.client_id,
            'scope': " ".join(self.scope),
            'response_type': 'code',
            'access_type': 'offline',
            'redirect_uri': self.redirect_uri,
            'prompt': 'consent',
            # 'state': state
        }

        query = urlencode(options)

        authorization_uri = f"{self.google_auth_endpoint}?{query}"

        return authorization_uri
    
    def getTokens(self, code):
        ''' exchange for access token with code from google OAUTH2 api'''
        options = {
            'code': code,
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'redirect_uri': self.redirect_uri,
            'grant_type': 'authorization_code',
        }

        response = requests.post(self.google_token_obtain_uri, data=options)

        tokens = response.json()
        return tokens


    def decodeIdToken(self, token):
        '''Validate and decode the id_token from Google'''
        id_token = token.get('id_token')

        # Decode the ID Token
        try:
            # First, fetch Google's public keys
            response = requests.get(self.google_jwks_url)
            jwks = response.json()
            
            # Decode JWT token and get the header
            unverified_header = jwt.get_unverified_header(id_token)
            
            if unverified_header is None:
                raise ValueError("Unable to decode token header")

            # Get the public key that corresponds to the token's key ID
            rsa_key = {}
            for key in jwks['keys']:
                if key['kid'] == unverified_header['kid']:
                    rsa_key = {
                        'kty': key['kty'],
                        'kid': key['kid'],
                        'use': key['use'],
                        'n': key['n'],
                        'e': key['e']
                    }
                    break

            if not rsa_key:
                raise ValueError("Unable to find appropriate key")

            # Now, use the RSA key to validate and decode the ID token
            payload = jwt.decode(id_token, rsa_key, algorithms=['RS256'], audience=self.client_id)

            # Ensure that the token is valid (check for 'iss' and 'aud' claims)
            if payload.get('iss') != 'https://accounts.google.com':
                raise ValueError("Invalid issuer")
            if payload.get('aud') != self.client_id:
                raise ValueError("Invalid audience")

            return payload  # This will contain user info from the ID token
        
        except jwt.ExpiredSignatureError:
            raise ValueError("Token is expired")
        except jwt.JWTClaimsError:
            raise ValueError("Invalid claims, please check the audience and issuer")
        except Exception as e:
            raise ValueError(f"Unable to parse token: {str(e)}")
    
    def getTokenForUser(self, user_info):
        '''creating access and refresh token for the user'''
        user = User.objects.filter(email=user_info.get('email')).first()

        if not user_info.get('email_verified'):
            raise ValueError('email must be verified')

        if not user:
            user_data = {
                'email': user_info['email'],
                'first_name': user_info['name'].split()[0],
                'last_name': user_info['name'].split()[1],
                'provider': "google",
                'password': secrets.token_urlsafe(16)
            }

            serilizer = UserSerializer(data=user_data)
            serilizer.is_valid(raise_exception=True)
            user = serilizer.save()
        
        tokens = RefreshToken.for_user(user)

        return tokens
