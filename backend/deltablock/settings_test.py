"""Settings used by the automated tests: SQLite in memory, fast hashing, relaxed throttles, demo mode on."""
import os

os.environ.setdefault('DJANGO_SECRET_KEY', 'test-only-secret-key')
os.environ.setdefault('DJANGO_DEBUG', 'True')
from .settings import *  # noqa: E402,F401,F403

DEBUG = False
ALLOWED_HOSTS = ['testserver', 'localhost']
DATABASES = {'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}}
PASSWORD_HASHERS = ['django.contrib.auth.hashers.MD5PasswordHasher']
REST_FRAMEWORK = {**REST_FRAMEWORK, 'DEFAULT_THROTTLE_RATES': {'login': '1000/min', 'public': '1000/min', 'password-reset': '1000/min'}}  # noqa: F405
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False
SECURE_SSL_REDIRECT = False
DELTABLOCK_DEMO_MODE = True
LOGIN_REVEAL_ACCOUNT_STATE = True
EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'
CACHES = {'default': {'BACKEND': 'django.core.cache.backends.locmem.LocMemCache'}}
