"""
Django settings for studio project.

Generated by 'django-admin startproject' using Django 3.2.11.

For more information on this file, see
https://docs.djangoproject.com/en/3.2/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/3.2/ref/settings/
"""

import logging
import os
import sys
from pathlib import Path

import colorlog
import structlog

from studio.utils import add_loggers

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/3.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = "django-insecure-t)9$8__a+vfsak+w30xf9ui9p8#rnyqb6p($!6ne8lin%&zf0h"

# SECURITY WARNING: don't run with debug turned on in production!

DEBUG = os.getenv("DEBUG", default="False").lower() in ("true", "1", "t")


# Since this file is only used for development, we can have this set to all hosts.
ALLOWED_HOSTS = ["*"]


# For django-wiki
SITE_ID = 1
# wiki: Sign up, login and logout views should be accessible.
WIKI_ACCOUNT_HANDLING = False
# wiki: No user signup, but superusers can create new users.
WIKI_ACCOUNT_SIGNUP_ALLOWED = False

DJANGO_WIKI_APPS = [
    "django.contrib.sites.apps.SitesConfig",
    "django.contrib.humanize.apps.HumanizeConfig",
    "django_nyt.apps.DjangoNytConfig",
    "mptt",
    "sekizai",
    "sorl.thumbnail",
    "wiki.apps.WikiConfig",
    "wiki.plugins.attachments.apps.AttachmentsConfig",
    "wiki.plugins.notifications.apps.NotificationsConfig",
    "wiki.plugins.images.apps.ImagesConfig",
    "wiki.plugins.macros.apps.MacrosConfig",
]

DJANGO_WIKI_MIDDLEWARE = [
    "django.contrib.sites.middleware.CurrentSiteMiddleware",
]

DJANGO_WIKI_CONTEXT_PROCESSOR = [
    "sekizai.context_processors.sekizai",
]

STRUCTLOG_MIDDLEWARE = ["django_structlog.middlewares.RequestMiddleware"]
DJANGO_STRUCTLOG_CELERY_ENABLED = not DEBUG

# Application definition


INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "rest_framework.authtoken",
    "rest_framework",
    "django.contrib.staticfiles",
    "corsheaders",
    "django_celery_beat",
    "django_extensions",  # for executing runscript among others
    "django_filters",
    "django_structlog",
    "tagulous",
    "guardian",
    "crispy_forms",
    "crispy_bootstrap5",
    "common",
    "portal",
    "projects",
    "models",
    "monitor",
    "apps",
    "api",
    "customtags",
    "news",
    "axes",  # django-axes for brute force login protection
    "django_password_validators",  # django-password-validators for password validation
    "collections_module",
] + DJANGO_WIKI_APPS

MIDDLEWARE = (
    [
        "django.middleware.security.SecurityMiddleware",
        "django.contrib.sessions.middleware.SessionMiddleware",
        "django.middleware.common.CommonMiddleware",
        "django.middleware.csrf.CsrfViewMiddleware",
        "django.contrib.auth.middleware.AuthenticationMiddleware",
        "django.contrib.messages.middleware.MessageMiddleware",
        "django.middleware.clickjacking.XFrameOptionsMiddleware",
        "corsheaders.middleware.CorsMiddleware",
        "axes.middleware.AxesMiddleware",
        "studio.middleware.ExceptionLoggingMiddleware",
    ]
    + DJANGO_WIKI_MIDDLEWARE
    + (STRUCTLOG_MIDDLEWARE if not DEBUG else [])
)

ROOT_URLCONF = "studio.urls"

CRISPY_ALLOWED_TEMPLATE_PACKS = "bootstrap5"
CRISPY_TEMPLATE_PACK = "bootstrap5"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "common.context_processors.maintenance_mode",
            ]
            + DJANGO_WIKI_CONTEXT_PROCESSOR,
            "libraries": {
                "custom_tags": "models.templatetags.custom_tags",
            },
        },
    },
]

TEMPLATE_LOADERS = (
    "django.template.loaders.filesystem.Loader",
    "django.template.loaders.app_directories.Loader",
    "django.template.loaders.eggs.Loader",
)


STATICFILES_FINDERS = (
    "django.contrib.staticfiles.finders.FileSystemFinder",
    "django.contrib.staticfiles.finders.AppDirectoriesFinder",
    # other finders
    "compressor.finders.CompressorFinder",
)

WSGI_APPLICATION = "studio.wsgi.application"

TESTING = len(sys.argv) > 1 and sys.argv[1] == "test"

# Database
# https://docs.djangoproject.com/en/3.2/ref/settings/#databases
if TESTING:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql_psycopg2",
            "NAME": "postgres",
            "USER": "postgres",
            "PASSWORD": "postgres",
            "HOST": "localhost",
            "PORT": "5432",
        }
    }
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql_psycopg2",
            "NAME": "postgres",
            "USER": "postgres",
            "PASSWORD": "postgres",
            "HOST": "db",
            "PORT": "5432",
        }
    }

AUTHENTICATION_BACKENDS = [
    "axes.backends.AxesStandaloneBackend",
    "django.contrib.auth.backends.ModelBackend",
    "guardian.backends.ObjectPermissionBackend",
]

# Related to user registration and authetication workflow
LOGIN_REDIRECT_URL = "/projects"
LOGIN_URL = "login"
LOGOUT_URL = "logout"

# Make new user inactive by default
INACTIVE_USERS = True

# Session settings for managing automatic login expiration.
# The age of session cookies, in seconds. Set to 1 day = 86400 seconds:
SESSION_COOKIE_AGE = 86400
# Whether to save the session data on every request. For sliding expiration:
SESSION_SAVE_EVERY_REQUEST = True
# Whether to expire the session when the user closes their browser:
SESSION_EXPIRE_AT_BROWSER_CLOSE = False

# The expiration duration in seconds for authentication tokens
AUTH_TOKEN_EXPIRATION = 60 * 20

# Settings for the Django Axes brute force login protection
# Number of allowed login failures before action is taken
AXES_FAILURE_LIMIT = 5
# Duration in hours after which old failed login attempts will be cleared
AXES_COOLOFF_TIME = 0.05
# Reset the number of failed attempts to 0 after a successful login
AXES_RESET_ON_SUCCESS = True
# Block failed attempts based on IP and username combination
AXES_LOCKOUT_PARAMETERS = [["ip_address", "username"]]
# Do not prolong the lock duration upon correct credentials entered during a lock period
AXES_RESET_COOL_OFF_ON_FAILURE_DURING_LOCKOUT = False
# Do not save all login and logout attempts to the database
AXES_DISABLE_ACCESS_LOG = True
# The custom view template to display on locked out event
AXES_LOCKOUT_TEMPLATE = "registration/locked_out.html"

# Django guardian 403 templates
GUARDIAN_RENDER_403 = True
GUARDIAN_TEMPLATE_403 = "403.html"

# Password validation
# https://docs.djangoproject.com/en/3.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",  # noqa: E501
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",  # noqa: E501
        "OPTIONS": {
            "min_length": 10,
        },
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",  # noqa: E501
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",  # noqa: E501
    },
    {
        "NAME": (
            "django_password_validators.password_character_requirements.password_validation.PasswordCharacterValidator"
        ),
        "OPTIONS": {
            "min_length_digit": 1,
            "min_length_alpha": 2,
            "min_length_special": 1,
            "min_length_lower": 1,
            "min_length_upper": 1,
            "special_characters": "~!@#$%^&*()_+{}\":;'[]",
        },
    },
]


# Internationalization
# https://docs.djangoproject.com/en/3.2/topics/i18n/

LANGUAGE_CODE = "en-us"

TIME_ZONE = "UTC"

USE_I18N = True


# Media Files for Studio apps
MEDIA_URL = "/media/"
MEDIA_ROOT = os.path.join(BASE_DIR, "media/")

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/3.2/howto/static-files/

STATIC_URL = "/static/"
STATIC_ROOT = ""
# SS-507
# Please keep "static" files first, because common/forms.py expects it
STATICFILES_DIRS = (os.path.join(BASE_DIR, "static"),)

# Default primary key field type
# https://docs.djangoproject.com/en/3.2/ref/settings/#default-auto-field

# Setting this will remove a warning about CorsModel primary keys filed,
# however a permission denied error is introduced
# when django tries to apply a new migration to corsheaders package.
# This is because the web server is started as stackn user but the
# migrations folder in corsheader is root
# DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
# solution for now: setting AutoField as default (below)
# then setting BigAutoField on app level (ex /projects/apps.py)
DEFAULT_AUTO_FIELD = "django.db.models.AutoField"

# Allow all clients to make requests to the OpenAPI
CORS_URLS_REGEX = r"^/openapi/.*$"
CORS_ALLOW_ALL_ORIGINS = True

# https://www.django-rest-framework.org/api-guide/authentication/#setting-the-authentication-scheme
# DEFAULT_VERSIONING_CLASS: NamespaceVersioning uses the URL path scheme, e.g. /v1/
# https://www.django-rest-framework.org/api-guide/versioning/
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": ["rest_framework.authentication.TokenAuthentication"],
    "DEFAULT_VERSIONING_CLASS": "rest_framework.versioning.NamespaceVersioning",
    "ALLOWED_VERSIONS": [None, "beta", "v1", "api", "api-v1"],
    "DEFAULT_VERSION": "v1",
    "DEFAULT_RENDERER_CLASSES": ("rest_framework.renderers.JSONRenderer",),
    "DEFAULT_PARSER_CLASSES": ("rest_framework.parsers.JSONParser",),
}

# Tagulous serialization settings
SERIALIZATION_MODULES = {
    "xml": "tagulous.serializers.xml_serializer",
    "json": "tagulous.serializers.json",
    "python": "tagulous.serializers.python",
    "yaml": "tagulous.serializers.pyyaml",
}

# Specific to Studio stack:
# Redis settings
REDIS_PORT = 6379
REDIS_DB = 0
REDIS_HOST = os.environ.get("REDIS_PORT_6379_TCP_ADDR", "redis")
# Celery settings
CELERY_BROKER_URL = "amqp://admin:LJqEG9RE4FdZbVWoJzZIOQEI@rabbit:5672//"
CELERY_RESULT_BACKEND = "redis://%s:%d/%d" % (REDIS_HOST, REDIS_PORT, REDIS_DB)
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TIMEZONE = "UTC"
CELERY_ENABLE_UTC = True
# For Model Objects creation (check models/models.py, pre_save_model() )
VERSION_BACKEND = "studio.version.Version"

# Other Helm/k8s deployment settings
CHART_FOLDER = "/app/charts/apps"
EXTERNAL_KUBECONF = True
KUBECONFIG = "/app/cluster.conf"
NAMESPACE = "default"
KUBE_API_REQUEST_TIMEOUT = 1
STORAGECLASS = "microk8s-hostpath"

# This can be simply "localhost", but it's better to test with a
# wildcard dns such as nip.io
IP = os.environ.get("IP", "127.0.0.1")

DOMAIN = f"studio.{IP}.nip.io"
AUTH_DOMAIN = IP
AUTH_PROTOCOL = "http"
STUDIO_URL = f"http://studio.{IP}.nip.io:8080"
# To enable sticky sessions for k8s ingress
SESSION_COOKIE_DOMAIN = f".{IP}.nip.io"

# App statuses
APPS_STATUS_SUCCESS = ["Running", "Succeeded", "Success"]
APPS_STATUS_WARNING = [
    "Pending",
    "Installed",
    "Waiting",
    "Installing",
    "Created",
]

# App dependencies

# Apps
APPS_MODEL = "apps.Apps"
APPINSTANCE_MODEL = "apps.AppInstance"
APPCATEGORIES_MODEL = "apps.AppCategories"

# Models
MODELS_MODEL = "models.Model"

# Projects
PROJECTS_MODEL = "projects.Project"
PROJECTLOG_MODEL = "projects.ProjectLog"
ENVIRONMENT_MODEL = "projects.Environment"
RELEASENAME_MODEL = "projects.ReleaseName"
# Portal
PUBLISHEDMODEL_MODEL = "portal.PublishedModel"
PUBLICMODELOBJECT_MODEL = "portal.PublicModelObject"

# Email
EMAIL_BACKEND = (
    "django.core.mail.backends.smtp.EmailBackend" if not DEBUG else "django.core.mail.backends.console.EmailBackend"
)
EMAIL_HOST = "smtp.gmail.com"
EMAIL_PORT = 465
EMAIL_USE_SSL = True
EMAIL_USE_TLS = False
EMAIL_HOST_USER = os.getenv("EMAIL_HOST_USER")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")
EMAIL_HOST_PASSWORD = os.getenv("EMAIL_PASSWORD")

# 2024-02-21: Removed because this is not used.
# VERSION = "dev"

MIGRATION_MODULES = {
    "apps": "studio.migrations.apps",
    "models": "studio.migrations.models",
    "monitor": "studio.migrations.monitor",
    "portal": "studio.migrations.portal",
    "projects": "studio.migrations.projects",
    "common": "common.migrations",
    "news": "news.migrations",
    "collections_module": "collections_module.migrations",
}

# Defines how many apps a user is allowed to create within one project
APPS_PER_PROJECT_LIMIT = {
    "dashapp": 10,
    "shinyapp": 10,
    "shinyproxyapp": 10,
    "customapp": 10,
    "pytorch-serve": 10,
    "tensorflow-serve": 10,
    "mlflow-serve": 10,
    "rstudio": 3,
    "vscode": 3,
    "jupyter-lab": 3,
    "mlflow": 1,
    "tissuumaps": 1,
    "volumeK8s": 0,
    "minio": 1,
    "mongo-express": 0,
    "reducer": 0,
    "combiner": 0,
    "mongodb": 0,
    "netpolicy": 0,
}

PROJECTS_PER_USER_LIMIT = 5

STUDIO_ACCESSMODE = os.environ.get("STUDIO_ACCESSMODE", "")
ENABLE_PROJECT_EXTRA_SETTINGS = False

DISABLED_APP_INSTANCE_FIELDS = []  # type: ignore

# This was added in SS-507.
# This setting is for django-guardian.
# We had to set it because AnonymousUser was not working properly.
# Specifically, apps.tests.test_user_has_no_access was failing.
# Also anonymous access to pages was not working.
ANONYMOUS_USER_NAME = None

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "json_formatter": {
            "()": structlog.stdlib.ProcessorFormatter,
            "processor": structlog.processors.JSONRenderer(),
        },
        "colored": {
            "()": colorlog.ColoredFormatter,
            "datefmt": "%Y-%m-%d %H:%M:%S",
            "log_colors": {
                "DEBUG": "blue",
                "INFO": "green",
                "WARNING": "yellow",
                "ERROR": "red",
                "CRITICAL": "bold_red",
            },
            "format": "%(log_color)s%(asctime)s - %(levelname)s - %(name)s: %(message)s%(reset)s",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "colored",
        },
        "json": {
            "class": "logging.StreamHandler",
            "formatter": "json_formatter",
        },
    },
    "loggers": {
        "": {
            "handlers": ["console" if DEBUG else "json"],
            "level": "DEBUG" if DEBUG else "INFO",
        },
        "django.server": {
            "handlers": ["console" if DEBUG else "json"],
            "level": "WARNING",
            "propagate": False,
        },
    },
}

LOGGING = add_loggers(LOGGING, INSTALLED_APPS)

if not DEBUG:
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.stdlib.filter_by_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )


