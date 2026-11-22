"""Django settings for the Deltablock API (demonstration data only; no real market data)."""
import os
import sys
from datetime import date
from pathlib import Path

import dj_database_url
from django.core.exceptions import ImproperlyConfigured

BASE_DIR = Path(__file__).resolve().parent.parent


def _load_dotenv():
    """Tiny .env reader (no extra dependency). Real environment variables always win."""
    path = BASE_DIR / '.env'
    if not path.exists():
        return
    for line in path.read_text(encoding='utf-8').splitlines():
        line = line.strip()
        if not line or line.startswith('#') or '=' not in line:
            continue
        key, value = line.split('=', 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


_load_dotenv()


def env(name, default=None):
    return os.environ.get(name, default)


def env_bool(name, default=False):
    value = os.environ.get(name)
    if value is None:
        return default
    return value.strip().lower() in ('1', 'true', 'yes', 'on')


def env_list(name, default):
    value = os.environ.get(name)
    if value is None:
        return list(default)
    return [item.strip() for item in value.split(',') if item.strip()]


TESTING = len(sys.argv) > 1 and sys.argv[1] == 'test'
DEBUG = env_bool('DEBUG', True)

SECRET_KEY = env('SECRET_KEY')

if not SECRET_KEY:
    if DEBUG or TESTING:
        SECRET_KEY = 'insecure-development-key-do-not-use-in-production'
    else:
        raise ImproperlyConfigured('Set the SECRET_KEY environment variable (or DEBUG=True for local development).')

ALLOWED_HOSTS = env_list('ALLOWED_HOSTS', ['localhost', '127.0.0.1', 'testserver'] if (DEBUG or TESTING) else [])

# Demonstration switches ------------------------------------------------------------------------------------------
DEMO_MODE = env_bool('DEMO_MODE', DEBUG)
DEMO_TODAY = env('DEMO_TODAY', '2026-10-23')  # fixed reference date used by the prototype for renewal countdowns
DEMO_PERSONA_EMAILS = ['khan@gmail.com', 'aisha.khan@gmail.com', 'diego@acme.co', 'jordan@example.com']
FRONTEND_URL = env('FRONTEND_URL', 'http://localhost:3000')

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.contenttypes',
    'django.contrib.auth',
    'django.contrib.messages',
    'django.contrib.sessions',
    'django.contrib.staticfiles',
    'rest_framework',
    'drf_spectacular',
    'corsheaders',
    'common',
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
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'
WSGI_APPLICATION = 'config.wsgi.application'
ASGI_APPLICATION = 'config.asgi.application'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {'context_processors': [
            'django.template.context_processors.request',
            'django.contrib.messages.context_processors.messages',
            'django.contrib.auth.context_processors.auth',
        ]},
    },
]

DATABASES = {
    'default': dj_database_url.config(default='sqlite:///' + str(BASE_DIR / 'db.sqlite3'), conn_max_age=600),
}

AUTH_USER_MODEL = 'accounts.User'
AUTHENTICATION_BACKENDS = ['accounts.backends.EmailBackend']
DEMO_PASSWORD = env('DEMO_PASSWORD', 'prototype-password')
DELTABLOCK_DEMO_MODE = env_bool('DELTABLOCK_DEMO_MODE', DEBUG)
DELTABLOCK_REFERENCE_DATE = date.fromisoformat(env('DELTABLOCK_REFERENCE_DATE', '2026-10-23'))
PORTAL_REFERENCE_DATE = env('PORTAL_REFERENCE_DATE', '2026-10-23')
LOGIN_REVEAL_ACCOUNT_STATE = env_bool('LOGIN_REVEAL_ACCOUNT_STATE', DELTABLOCK_DEMO_MODE)
REMEMBER_ME_AGE = int(env('REMEMBER_ME_AGE', str(14 * 24 * 60 * 60)))
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator', 'OPTIONS': {'min_length': 12}},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]
PASSWORD_RESET_TIMEOUT = 60 * 60 * 24

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = False
USE_TZ = True

STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STORAGES = {
    'default': {'BACKEND': 'django.core.files.storage.FileSystemStorage'},
    'staticfiles': {'BACKEND': 'whitenoise.storage.CompressedStaticFilesStorage'},
}
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Sessions / cookies -------------------------------------------------------------------------------------------------
SESSION_ENGINE = 'django.contrib.sessions.backends.db'
SESSION_COOKIE_AGE = int(env('SESSION_COOKIE_AGE', str(8 * 60 * 60)))
SESSION_SAVE_EVERY_REQUEST = True
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Lax'
CSRF_COOKIE_HTTPONLY = False  # the SPA reads the token cookie and echoes it in X-CSRFToken
CSRF_COOKIE_SAMESITE = 'Lax'
CSRF_TRUSTED_ORIGINS = env_list('CSRF_TRUSTED_ORIGINS', ['http://localhost:3000', 'http://127.0.0.1:3000'])
CORS_ALLOWED_ORIGINS = env_list('CORS_ALLOWED_ORIGINS', ['http://localhost:3000', 'http://127.0.0.1:3000'])
CORS_ALLOW_CREDENTIALS = True

if not DEBUG and not TESTING:
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_SSL_REDIRECT = env_bool('SECURE_SSL_REDIRECT', True)
    SECURE_HSTS_SECONDS = int(env('SECURE_HSTS_SECONDS', str(31536000)))
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    if env_bool('TRUST_PROXY_SSL_HEADER', False):
        SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
X_FRAME_OPTIONS = 'DENY'

EMAIL_BACKEND = env('EMAIL_BACKEND', 'django.core.mail.backends.console.EmailBackend')
DEFAULT_FROM_EMAIL = env('DEFAULT_FROM_EMAIL', 'no-reply@deltablock.example')

# REST framework --------------------------------------------------------------------------------------------------
_login_rate = '100000/min' if TESTING else env('THROTTLE_LOGIN', '20/min')
_public_rate = '100000/min' if TESTING else env('THROTTLE_PUBLIC', '30/min')
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': ['rest_framework.authentication.SessionAuthentication'],
    'DEFAULT_PERMISSION_CLASSES': ['rest_framework.permissions.IsAuthenticated'],
    'DEFAULT_RENDERER_CLASSES': ['rest_framework.renderers.JSONRenderer'],
    'DEFAULT_PARSER_CLASSES': ['rest_framework.parsers.JSONParser'],
    'EXCEPTION_HANDLER': 'core.exceptions.api_exception_handler',
    'DEFAULT_THROTTLE_RATES': {'login': _login_rate, 'public': _public_rate},
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
}
SPECTACULAR_SETTINGS = {
    'TITLE': 'Deltablock API',
    'DESCRIPTION': 'REST API for the Deltablock liquidity portal. All data is demonstration data.',
    'VERSION': '1.0.0',
    'SERVE_INCLUDE_SCHEMA': False,
}
API_DOCS_PUBLIC = env_bool('API_DOCS_PUBLIC', DEBUG)

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {'console': {'class': 'logging.StreamHandler'}},
    'root': {'handlers': ['console'], 'level': env('LOG_LEVEL', 'INFO')},
}
