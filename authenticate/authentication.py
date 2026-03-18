from django.contrib.auth.models import User

# when call authenticate it will eterate over this after check with username
class EmailAuthBackend:
    def authenticate(self, request, username=None, password=None):
        try:
            user = User.objects.get(email=username)
            if user.check_password(password):
                return user
            return None
        except (User.DoesNotExist, User.MultipleObjectsReturned):    
            return None
        
    def get_user(self, user_id):
        try:
            user = User.objects.get(pk=user_id)
            return user
        except User.DoesNotExist:
            return None



def associate_by_email(backend, details, user=None, *args, **kwargs):
    """
    Associate current social auth with existing user by email address.
    
    If a user with the social auth email already exists, return that user
    instead of creating a new one. This allows users who registered normally
    to login with social auth using the same email.
    """
    email = details.get('email')
    try:
        existing_user = User.objects.get(email__iexact=email)
        return {
            'user': existing_user,
            'is_new': False
        }
    except User.DoesNotExist:
        return None  # No user found, continue to create new user
