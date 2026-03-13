import datetime
import os
from pathlib import Path

import django
import environ

env = environ.Env()

# Take environment variables from .env file
env.read_env(env.str("DOTENV_PATH", ".envs/local/django"))

BASE_DIR = Path(__file__).resolve().parent.parent

DEBUG = env.str("DEBUG", False)
TEST = False

ENVIRONMENT = env.str("ENVIRONMENT", "local")

INCLUDE_API_URLS = env.bool("INCLUDE_API_URLS", False)
API_URLS_PATH = env.str("API_URLS_PATH", "")

INCLUDE_ADMIN_URLS = env.bool("INCLUDE_ADMIN_URLS", False)
ADMIN_URLS_PATH = env.str("ADMIN_URLS_PATH", "")

ADMINS_EMAILS = env.list("ADMINS_EMAILS", default="")

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = env("SECRET_KEY")

# Application definition
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django_celery_beat",
    "django_extensions",
    "django_filters",
    "corsheaders",
    "drf_yasg",
    "rest_framework",
    "app.core",
    "app.tracker",
    "app.algorithm",
    "app.expert",
    "app.game",
]

SERIALIZATION_MODULES = {"json": "app.core.pydantic_serialization"}

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [os.path.join(BASE_DIR, "templates")],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

ALLOWED_HOSTS = ["*"]

CORS_ALLOWED_ORIGINS = env.list("CORS_ALLOWED_ORIGINS", [])
CSRF_TRUSTED_ORIGINS = env.list("CSRF_TRUSTED_ORIGINS", [])

ROOT_URLCONF = "app.urls"

WSGI_APPLICATION = "app.wsgi.application"

# Database
# https://docs.djangoproject.com/en/3.1/ref/settings/#databases
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql_psycopg2",
        "NAME": env("DATABASE_NAME"),
        "USER": env("DATABASE_USER"),
        "PASSWORD": env("DATABASE_PASS"),
        "HOST": env("DATABASE_HOST"),
        "PORT": env("DATABASE_PORT"),
    }
}

AUTH_USER_MODEL = "core.User"

# Password validation
# https://docs.djangoproject.com/en/3.1/ref/settings/#auth-password-validators
AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"
    },
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]


# Internationalization
# https://docs.djangoproject.com/en/3.1/topics/i18n/
LANGUAGE_CODE = "en-us"

TIME_ZONE = "UTC"

USE_I18N = True

USE_L10N = True

USE_TZ = True

# Logging
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "console": {"class": "logging.StreamHandler", "level": "INFO"},
    },
    "root": {
        "handlers": ["console"],
        "level": "INFO",
    },
}

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/3.1/howto/static-files/
STATIC_URL = env.str("STATIC_URL", "static/")
STATIC_ROOT = os.path.join(BASE_DIR, "build/static/")

# File storage
DEFAULT_FILE_STORAGE = "storages.backends.s3boto3.S3Boto3Storage"
# TODO: should this even be optional
AWS_STORAGE_BUCKET_NAME = env.str("AWS_STORAGE_BUCKET_NAME")

# These settings / env variables are only relevant when working with localstack
AWS_S3_ENDPOINT_URL = env.str("AWS_S3_ENDPOINT_URL", None)
AWS_S3_CUSTOM_DOMAIN = env.str("AWS_S3_CUSTOM_DOMAIN", None)
AWS_S3_URL_PROTOCOL = env.str("AWS_S3_URL_PROTOCOL", None)
AWS_S3_SECURE_URLS = env.bool("AWS_S3_SECURE_URLS", True)

# DRF Settings
REST_FRAMEWORK = {
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
    "DEFAULT_FILTER_BACKENDS": ("django_filters.rest_framework.DjangoFilterBackend",),
    "TEST_REQUEST_RENDERER_CLASSES": (
        "rest_framework.renderers.MultiPartRenderer",
        "rest_framework.renderers.JSONRenderer",
        "rest_framework.renderers.TemplateHTMLRenderer",
    ),
    "DEFAULT_PARSER_CLASSES": (
        "rest_framework.parsers.JSONParser",
        "rest_framework.parsers.MultiPartParser",
        "rest_framework.parsers.FormParser",
    ),
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.LimitOffsetPagination",
    "PAGE_SIZE": 50,
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "app.core.authentication.Auth0TokenAuthentication"
    ],
}

AUTH0_DOMAIN = os.getenv("AUTH0_DOMAIN")
AUTH0_ALGORITHMS = ["RS256"]
AUTH0_API_AUDIENCE = os.getenv("AUTH0_API_AUDIENCE")
AUTH0_ISSUER = f"https://{AUTH0_DOMAIN}/"
AUTH0_USER_INFO = f"https://{AUTH0_DOMAIN}/userinfo"
AUTH0_JWKS_URL = f"https://{AUTH0_DOMAIN}/.well-known/jwks.json"

OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")

LANGUAGE_MODELS: dict = {}

# Swagger settings
SWAGGER_SETTINGS = {
    "SECURITY_DEFINITIONS": {
        "Token": {"type": "apiKey", "name": "Authorization", "in": "header"}
    }
}

REDIS_URL = env.str("REDIS_URL")

# Celery settings
CELERY_BROKER_URL = REDIS_URL
CELERY_RESULT_BACKEND = REDIS_URL

CELERY_BEAT_SCHEDULER = "django_celery_beat.schedulers:DatabaseScheduler"

STRIPE_API_KEY = os.getenv("STRIPE_API_KEY")
STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET")

STRIPE_SECONDARY_API_KEY = os.getenv("STRIPE_SECONDARY_API_KEY")
STRIPE_SECONDARY_WEBHOOK_SECRET = os.getenv("STRIPE_SECONDARY_WEBHOOK_SECRET")

SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY", "")

HUBSPOT_ACCESS_TOKEN = os.getenv("HUBSPOT_ACCESS_TOKEN", "")


# Email settings
BCC_RECIPIENTS_EXPERT_REVIEW = env.list("BCC_RECIPIENTS_EXPERT_REVIEW", default=[])

django.setup()

# Game settings
MAX_ATTEMPTS_TO_GENERATE_GAME = env.int("MAX_ATTEMPTS_TO_GENERATE_GAME", default=3)
OPTION_LAST_USED_IN_GAME_DAYS_THRESHOLD = env.int(
    "OPTION_LAST_USED_IN_GAME_DAYS_THRESHOLD", default=30
)
LAST_USED_IN_GAME_DATE_INCREMENT_DAYS = env.int(
    "LAST_USED_IN_GAME_DATE_INCREMENT_DAYS", default=7
)
