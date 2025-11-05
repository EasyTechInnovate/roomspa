from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed

ADMIN_TOKEN = "admin-simple-token-2024"

class SimpleAdminAuthentication(BaseAuthentication):
    """
    Simple token authentication for admin panel only.
    Bypasses JWT authentication completely.
    """

    def authenticate(self, request):
        auth_header = request.META.get('HTTP_AUTHORIZATION', '')

        if not auth_header.startswith('Bearer '):
            return None

        token = auth_header.split(' ')[1]

        if token == ADMIN_TOKEN:
            # Create a dummy user object
            class AdminUser:
                is_authenticated = True
                is_admin = True
                email = "admin@gmail.com"
                id = "admin-001"

            return (AdminUser(), token)

        return None

    def authenticate_header(self, request):
        return 'Bearer'