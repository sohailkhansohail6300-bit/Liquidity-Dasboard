"""Django settings for the Deltablock backend. Everything environment-specific comes from environment variables
(optionally loaded from backend/.env)."""
import os
from datetime import date
from pathlib import Path

from django.core.exceptions import ImproperlyConfigured

BASE_DIR = Path(__file__).resolve().parent.parent

try:  # optional convenience: load backend/.env when python-dotenv is installed
    from dotenv import load_dotenv
    load_dotenv(BASE_DIR / '.env')
except ImportError:  # pragma: no cover
    pass


def env(name, default=None):
    return os.environ.get(name, default)


def env_bool(name, default=False):
    v = os.environ.get(name)
    return default if v is None else v.strip().lower() in ('1', 'true', 'yes', 'on')


def env_list(name, default=''):
    return [x.strip() for x in os.environ.get(name, default).split(',') if x.strip()]


DEBUG = env_bool('DJANGO_DEBUG', False)

SECRET_KEY = env('DJANGO_SECRET_KEY')
if not SECRET_KEY:
    if DEBUG:
        SECRET_KEY = 'insecure-development-only-key'  # never used when DJANGO_DEBUG is false
    else:
        raise ImproperlyConfigured('Set DJANGO_SECRET_KEY (or DJANGO_DEBUG=True for local development).')

ALLOWED_HOSTS = env_list('DJANGO_ALLOWED_HOSTS', 'localhost,127.0.0.1' if DEBUG else '')

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'corsheaders',
    'rest_framework',
    'drf_spectacular',
    'core',
    'accounts',
    'companies',
    'market',
    'subscriptions',
    'support',
    'administration',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'deltablock.urls'
WSGI_APPLICATION = 'deltablock.wsgi.application'

TEMPLATES = [{
    'BACKEND': 'django.template.backends.django.DjangoTemplates',
    'DIRS': [],
    'APP_DIRS': True,
    'OPTIONS': {'context_processors': [
        'django.template.context_processors.request',
        'django.contrib.auth.context_processors.auth',
        'django.contrib.messages.context_processors.messages',
    ]},
}]

# ------------------------------------------------------------------------------------------------ database
DB_ENGINE = env('DB_ENGINE', 'sqlite3')
if DB_ENGINE == 'postgresql':
    DATABASES = {'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': env('DB_NAME', 'deltablock'),
        'USER': env('DB_USER', 'deltablock'),
        'PASSWORD': env('DB_PASSWORD', ''),
        'HOST': env('DB_HOST', 'localhost'),
        'PORT': env('DB_PORT', '5432'),
        'CONN_MAX_AGE': int(env('DB_CONN_MAX_AGE', '60')),
    }}
elif DB_ENGINE == 'sqlite3':
    DATABASES = {'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': BASE_DIR / 'db.sqlite3'}}
else:
    raise ImproperlyConfigured('DB_ENGINE must be "sqlite3" or "postgresql".')
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ------------------------------------------------------------------------------------------------ auth
AUTH_USER_MODEL = 'accounts.User'
AUTH_PASSWORD_VALIDATORS = [
    # The prototype's only password rule is "at least 12 characters"; the API enforces exactly that message itself.
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator', 'OPTIONS': {'min_length': 12}},
]
PASSWORD_RESET_TIMEOUT = int(env('PASSWORD_RESET_TIMEOUT', '3600'))

SESSION_COOKIE_AGE = int(env('SESSION_COOKIE_AGE', str(12 * 3600)))
REMEMBER_ME_AGE = int(env('REMEMBER_ME_AGE', str(14 * 24 * 3600)))
SESSION_SAVE_EVERY_REQUEST = True          # sliding idle timeout
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Lax'
CSRF_COOKIE_HTTPONLY = False                # the Next.js client reads the token and sends X-CSRFToken
CSRF_COOKIE_SAMESITE = 'Lax'
CSRF_TRUSTED_ORIGINS = env_list('CSRF_TRUSTED_ORIGINS', 'http://localhost:3000' if DEBUG else '')

CORS_ALLOWED_ORIGINS = env_list('CORS_ALLOWED_ORIGINS')
CORS_ALLOW_CREDENTIALS = True

if not DEBUG:
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_SSL_REDIRECT = env_bool('SECURE_SSL_REDIRECT', True)
    SECURE_HSTS_SECONDS = int(env('SECURE_HSTS_SECONDS', '31536000'))
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    X_FRAME_OPTIONS = 'DENY'
    _proxy = env('SECURE_PROXY_SSL_HEADER', '')
    if _proxy:
        SECURE_PROXY_SSL_HEADER = tuple(_proxy.split(',', 1))

# ------------------------------------------------------------------------------------------------ REST framework
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': ['core.authentication.SessionAuth'],
    'DEFAULT_PERMISSION_CLASSES': ['rest_framework.permissions.IsAuthenticated'],
    'DEFAULT_RENDERER_CLASSES': ['rest_framework.renderers.JSONRenderer'],
    'DEFAULT_PARSER_CLASSES': ['rest_framework.parsers.JSONParser'],
    'EXCEPTION_HANDLER': 'core.exceptions.api_exception_handler',
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
    'DEFAULT_THROTTLE_CLASSES': ['rest_framework.throttling.ScopedRateThrottle'],
    'DEFAULT_THROTTLE_RATES': {
        'login': env('THROTTLE_LOGIN', '10/min'),
        'public': env('THROTTLE_PUBLIC', '30/hour'),
        'password-reset': env('THROTTLE_PASSWORD_RESET', '5/hour'),
    },
}
SPECTACULAR_SETTINGS = {
    'TITLE': 'Deltablock API',
    'DESCRIPTION': 'REST API for the Deltablock liquidity portal. Sample data is for demonstration only.',
    'VERSION': '1.0.0',
    'SERVE_INCLUDE_SCHEMA': False,
}

# ------------------------------------------------------------------------------------------------ Deltablock
DELTABLOCK_DEMO_MODE = env_bool('DELTABLOCK_DEMO_MODE', DEBUG)
DELTABLOCK_REFERENCE_DATE = date.fromisoformat(env('DELTABLOCK_REFERENCE_DATE', '2026-10-23'))
LOGIN_REVEAL_ACCOUNT_STATE = env_bool('LOGIN_REVEAL_ACCOUNT_STATE', DELTABLOCK_DEMO_MODE)
FRONTEND_URL = env('FRONTEND_URL', 'http://localhost:3000')
DEMO_PASSWORD = 'prototype-password'   # only used by the demo seed and the demo persona login hint

EMAIL_BACKEND = env('EMAIL_BACKEND', 'django.core.mail.backends.console.EmailBackend')
DEFAULT_FROM_EMAIL = env('DEFAULT_FROM_EMAIL', 'Deltablock <no-reply@deltablock.example>')

# ------------------------------------------------------------------------------------------------ misc
LANGUAGE_CODE = 'en-gb'
TIME_ZONE = 'UTC'
USE_I18N = False
USE_TZ = True
STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'

LOGGING = {
    'version': 1, 'disable_existing_loggers': False,
    'handlers': {'console': {'class': 'logging.StreamHandler'}},
    'root': {'handlers': ['console'], 'level': env('LOG_LEVEL', 'INFO')},
}
