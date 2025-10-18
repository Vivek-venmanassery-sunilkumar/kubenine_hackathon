from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from rest_framework_simplejwt.tokens import AccessToken


class CookieJWTAuthentication(JWTAuthentication):
    """
    Custom JWT authentication that works with HTTP-only cookies.
    """
    
    def authenticate(self, request):
        # First try to get token from Authorization header (default behavior)
        header = self.get_header(request)
        if header is not None:
            raw_token = self.get_raw_token(header)
            if raw_token is not None:
                try:
                    validated_token = self.get_validated_token(raw_token)
                    return self.get_user(validated_token), validated_token
                except TokenError:
                    pass
        
        # If no token in header, try to get from cookies
        raw_token = request.COOKIES.get('access_token')
        if raw_token is None:
            return None
            
        try:
            validated_token = self.get_validated_token(raw_token)
            return self.get_user(validated_token), validated_token
        except TokenError:
            return None
