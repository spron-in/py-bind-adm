import logging
from django.conf import settings
from django.contrib.auth import login, authenticate
from django.core.exceptions import ImproperlyConfigured
from importlib import import_module
from django.contrib.auth.models import AnonymousUser

try:
    from django.contrib.auth import get_user_model

    User = get_user_model()
except ImportError:
    from django.contrib.auth.models import User

logging.basicConfig()
logger = logging.getLogger(__name__)

class SSLClientAuthBackend(object):
    @staticmethod
    def authenticate(request=None):
        _module_name, _function_name = settings.USER_DATA_DN.rsplit('.', 1)
        _module = import_module(_module_name)  # We need a non-empty fromlist
        USER_DATA_DN = getattr(_module, _function_name)
        logger.info("DN: {0}".format(request.META.get('HTTP_X_SSL_AUTHENTICATED')))

        authentication_status = request.META.get('HTTP_X_SSL_AUTHENTICATED',
                                                 None)
        if (authentication_status != "SUCCESS" and 'HTTP_SSL_CLIENT_S_DN' not in request.META):
            logger.warn(
                "HTTP_X_SSL_AUTHENTICATED marked failed or "
                "HTTP_SSL_CLIENT_S_DN "
                "header missing")
            return None
        dn = request.META.get('HTTP_SSL_CLIENT_S_DN')
        logger.info("DN: {0}".format(dn))
        user_data = USER_DATA_DN(dn)
        username = user_data['username']
        username = username.replace(" ", "_")
        logger.info("username: {0}".format(username))
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            logger.info("user {0} not found".format(username))
            if settings.AUTOCREATE_VALID_SSL_USERS:
                user = User(**user_data)
                user.save()
            else:
                return None
        if not user.is_active:
            logger.warning("user {0} inactive".format(username))
            return None
        logger.info("user {0} authenticated using a certificate issued to "
                    "{1}".format(username, dn))
        return user

    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None

class SSLClientAuthMiddleware(object):
    def process_request(self, request):
        if not hasattr(request, 'user'):
            raise ImproperlyConfigured()
        if request.user.is_authenticated():
            return
        user = authenticate(request=request)
        if user is None or not user.is_authenticated():
            request.user = AnonymousUser()
            return
        if int(request.META.get('HTTP_X_REST_API', 0)):
            request.user = user
            logger.debug("REST API call, not logging user in")
        else:
            logger.info("Logging user in")
            login(request, user)
