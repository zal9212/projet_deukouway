"""
Django settings for dekouway project.

Security and configuration managed by django-environ.
Clean Architecture / DDD / Modular Monolith.
"""

import os
import sys
from pathlib import Path
from datetime import timedelta
import environ

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Détecte l'exécution sous `manage.py test` : sert à désactiver les caches applicatifs
# de longue durée (catégories/types, stats admin) qui, sinon, feraient fuiter des
# données périmées d'un test à l'autre (LocMemCache n'est pas réinitialisé entre les
# tests par Django). Les tests qui vérifient explicitement le comportement du cache
# (ex. RateLimitMiddleware) appellent cache.clear() eux-mêmes et ne sont pas affectés.
TESTING = 'test' in sys.argv

# Initialize environment variables.
# SECRET_KEY, DEBUG et ALLOWED_HOSTS n'ont VOLONTAIREMENT aucune valeur par défaut :
# un .env manquant ou mal configuré doit faire échouer le démarrage immédiatement
# (ImproperlyConfigured) plutôt que de basculer silencieusement sur DEBUG=True et une
# clé secrète publique et connue de tous (faille de sécurité critique en production).
env = environ.Env(
    DATABASE_URL=(str, f'sqlite:///{BASE_DIR}/db.sqlite3'),
    CSRF_TRUSTED_ORIGINS=(list, []),
)

# Read environment variables from .env file if it exists
if os.path.exists(BASE_DIR / '.env'):
    environ.Env.read_env(BASE_DIR / '.env')

SECRET_KEY = env('SECRET_KEY')
DEBUG = env.bool('DEBUG')
ALLOWED_HOSTS = env.list('ALLOWED_HOSTS')

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    
    # Third party apps
    'rest_framework',
    'rest_framework_simplejwt',
    'rest_framework_simplejwt.token_blacklist',
    'django_filters',
    'drf_spectacular',
    'django.contrib.sites',        # requis par allauth
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'allauth.socialaccount.providers.google',

    # Local apps (monolith modules)
    'apps.core',
    'apps.accounts',
    'apps.properties',
    'apps.reservations',
    'apps.payments',
    'apps.support',
    'apps.dashboard',
    'apps.notifications',
    'apps.documents',
    'apps.analytics',
    'apps.api',
    'apps.ai',
]

# Groq LLM Configuration
GROQ_API_KEY = env('GROQ_API_KEY', default='')
GROQ_MODEL = env('GROQ_MODEL', default='llama-3.3-70b-versatile')
GROQ_TIMEOUT = env.float('GROQ_TIMEOUT', default=10.0)

# Email : par défaut la console (visible dans les logs, aucune dépendance externe
# en dev). En production, définir EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
# et les identifiants SMTP dans .env pour que les emails (reset mot de passe,
# vérification de compte...) partent réellement.
EMAIL_BACKEND = env('EMAIL_BACKEND', default='django.core.mail.backends.console.EmailBackend')
EMAIL_HOST = env('EMAIL_HOST', default='')
EMAIL_PORT = env.int('EMAIL_PORT', default=587)
EMAIL_HOST_USER = env('EMAIL_HOST_USER', default='')
EMAIL_HOST_PASSWORD = env('EMAIL_HOST_PASSWORD', default='')
EMAIL_USE_TLS = env.bool('EMAIL_USE_TLS', default=True)
DEFAULT_FROM_EMAIL = env('DEFAULT_FROM_EMAIL', default='noreply@dekouway.sn')

# Jeton partagé exigé par /metrics/ (endpoint Prometheus) : vide par défaut, ce qui
# refuse l'accès par défaut tant qu'il n'est pas explicitement configuré.
METRICS_TOKEN = env('METRICS_TOKEN', default='')

# Sentry error monitoring (no-op if SENTRY_DSN is left blank)
SENTRY_DSN = env('SENTRY_DSN', default='')
if SENTRY_DSN:
    import sentry_sdk
    from sentry_sdk.integrations.django import DjangoIntegration

    sentry_sdk.init(
        dsn=SENTRY_DSN,
        integrations=[DjangoIntegration()],
        traces_sample_rate=env.float('SENTRY_TRACES_SAMPLE_RATE', default=0.2),
        send_default_pii=False,
        environment=env('SENTRY_ENVIRONMENT', default='production'),
    )

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'apps.core.middleware.SecurityHeadersMiddleware',
    'apps.core.middleware.RateLimitMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'allauth.account.middleware.AccountMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'dekouway.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'apps.accounts.context_processors.social_login',
                'apps.payments.context_processors.site_branding',
                'apps.notifications.context_processors.notifications',
            ],
        },
    },
]

WSGI_APPLICATION = 'dekouway.wsgi.application'

# Database configuration
DATABASES = {
    'default': env.db(),
}

# Password hashers using Argon2 by default for top-tier security
PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.Argon2PasswordHasher',
    'django.contrib.auth.hashers.PBKDF2PasswordHasher',
    'django.contrib.auth.hashers.PBKDF2SHA1PasswordHasher',
    'django.contrib.auth.hashers.BCryptSHA256PasswordHasher',
]

# Custom User Model
AUTH_USER_MODEL = 'accounts.User'

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        'OPTIONS': {
            'min_length': 8,
        }
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Authentication redirect configuration
LOGIN_URL = 'accounts:login'
LOGIN_REDIRECT_URL = 'dashboard:home'
LOGOUT_REDIRECT_URL = 'public:home'

# Authentication backends - support login via email (USERNAME_FIELD = 'email')
AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
    'allauth.account.auth_backends.AuthenticationBackend',
]

SITE_ID = 1

# --- django-allauth : connexion Google ---
# Notre modèle User n'a pas de champ `username` (email = USERNAME_FIELD) : on
# désactive tout ce qui concerne le username côté allauth, et on ne monte que
# le sous-système socialaccount (nos propres vues gèrent déjà login/inscription
# par email — voir apps/accounts/views/auth.py).
ACCOUNT_USER_MODEL_USERNAME_FIELD = None
ACCOUNT_LOGIN_METHODS = {'email'}
ACCOUNT_SIGNUP_FIELDS = ['email*', 'password1*', 'password2*']
ACCOUNT_ADAPTER = 'apps.accounts.adapters.AccountAdapter'
SOCIALACCOUNT_ADAPTER = 'apps.accounts.adapters.SocialAccountAdapter'

# Un compte Google authentifie l'email : si un compte DEKOUWAY existe déjà avec
# cet email (inscrit normalement), on connecte l'utilisateur à CE compte plutôt
# que d'en créer un doublon, et on relie durablement le compte Google dessus.
SOCIALACCOUNT_EMAIL_AUTHENTICATION = True
SOCIALACCOUNT_EMAIL_AUTHENTICATION_AUTO_CONNECT = True
# Autorise un simple lien <a href> (GET) au lieu d'exiger un formulaire POST.
SOCIALACCOUNT_LOGIN_ON_GET = True
SOCIALACCOUNT_STORE_TOKENS = False

SOCIALACCOUNT_PROVIDERS = {
    'google': {
        'APP': {
            'client_id': env('GOOGLE_CLIENT_ID', default=''),
            'secret': env('GOOGLE_CLIENT_SECRET', default=''),
            'key': '',
        },
        'SCOPE': ['profile', 'email'],
        'AUTH_PARAMS': {'access_type': 'online'},
    }
}

# Django REST Framework Configuration
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
    'DEFAULT_FILTER_BACKENDS': (
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ),
    'DEFAULT_PAGINATION_CLASS': 'apps.core.api.pagination.StandardResultsSetPagination',
    'EXCEPTION_HANDLER': 'apps.core.api.exceptions.custom_exception_handler',
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
}

# Simple JWT Configuration
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=60),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'UPDATE_LAST_LOGIN': True,
    'ALGORITHM': 'HS256',
    'SIGNING_KEY': SECRET_KEY,
    'AUTH_HEADER_TYPES': ('Bearer', 'JWT'),
    'AUTH_HEADER_NAME': 'HTTP_AUTHORIZATION',
    'USER_ID_FIELD': 'id',
    'USER_ID_CLAIM': 'user_id',
}

# OpenAPI 3.0 / Swagger Documentation (drf-spectacular)
SPECTACULAR_SETTINGS = {
    'TITLE': 'DEKOUWAY SaaS API',
    'DESCRIPTION': 'API REST complète de la plateforme SaaS immobilière DEKOUWAY (Clean Architecture / DDD).',
    'VERSION': '1.0.0',
    'SERVE_INCLUDE_SCHEMA': False,
    'COMPONENT_SPLIT_REQUEST': True,
}

# Cache configuration (Redis avec fallback LocMemCache pour dev)
CACHES = {
    'default': {
        'BACKEND': env('CACHE_BACKEND', default='django.core.cache.backends.locmem.LocMemCache'),
        'LOCATION': env('CACHE_LOCATION', default='dekouway-cache'),
    }
}

# Centralized Logging System
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '[{asctime}] {levelname} {name} ({module}:{lineno}): {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
        'apps': {
            'handlers': ['console'],
            'level': 'DEBUG' if DEBUG else 'INFO',
            'propagate': False,
        },
    },
}

# Internationalization
LANGUAGE_CODE = 'fr-fr'
TIME_ZONE = 'Africa/Dakar'
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [
    BASE_DIR / 'static',
]

# Whitenoise storage with compression and caching.
# En test, la storage manifeste (hashage des noms de fichiers) dépend d'un
# `collectstatic` déjà exécuté et à jour : ce n'est pas une préoccupation de
# correction fonctionnelle mais de build de production, donc les tests utilisent
# une storage simple, sans manifeste, pour ne jamais dépendre de cet état externe.
# MEDIA (photos de logements, logo, image hero) : Cloudinary si CLOUDINARY_URL est
# défini (ex. déploiement Render, dont le disque est éphémère), sinon disque local.
# Les documents d'identité (KYC) restent volontairement hors de ce mécanisme : ils
# utilisent toujours `apps.core.storage.private_storage` (local), jamais un CDN public.
CLOUDINARY_URL = env('CLOUDINARY_URL', default='')
STORAGES = {
    "default": {
        "BACKEND": (
            "cloudinary_storage.storage.MediaCloudinaryStorage"
            if CLOUDINARY_URL
            else "django.core.files.storage.FileSystemStorage"
        ),
    },
    "staticfiles": {
        "BACKEND": (
            "django.contrib.staticfiles.storage.StaticFilesStorage"
            if TESTING
            else "whitenoise.storage.CompressedManifestStaticFilesStorage"
        ),
    },
}
if CLOUDINARY_URL:
    INSTALLED_APPS += ['cloudinary_storage', 'cloudinary']

# Media files
MEDIA_URL = 'media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Security settings for production
if not DEBUG:
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    X_FRAME_OPTIONS = 'DENY'
    SECURE_SSL_REDIRECT = env.bool('SECURE_SSL_REDIRECT', default=True)
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    CSRF_TRUSTED_ORIGINS = env.list('CSRF_TRUSTED_ORIGINS')
    SECURE_HSTS_SECONDS = 31536000  # 1 year
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
else:
    # Development CSRF settings. Le domaine ngrok-free.dev change à chaque redémarrage
    # du tunnel (tier gratuit sans domaine réservé) : on autorise tout le sous-domaine
    # plutôt qu'une URL figée, pour ne pas avoir à éditer ce fichier à chaque relance.
    CSRF_TRUSTED_ORIGINS = [
        'http://localhost:8000', 'http://127.0.0.1:8000', 'http://192.168.0.106:8000',
        'https://*.ngrok-free.dev', 'https://*.ngrok-free.app', 'https://*.ngrok.app',
    ]
