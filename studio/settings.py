"""
Django settings for studio project.

Generated by 'django-admin startproject' using Django 3.2.11.

For more information on this file, see
https://docs.djangoproject.com/en/3.2/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/3.2/ref/settings/
"""

import os
import sys
from pathlib import Path

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/3.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = (
    "django-insecure-t)9$8__a+vfsak+w30xf9ui9p8#rnyqb6p($!6ne8lin%&zf0h"
)

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

if DEBUG:
    ALLOWED_HOSTS = ["*"]
else:
    ALLOWED_HOSTS = ["localhost"]


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
    "tagulous",
    "guardian",
    "crispy_forms",
    "common",
    "portal",
    "projects",
    "models",
    "monitor",
    "apps",
    "api",
    "customtags",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "corsheaders.middleware.CorsMiddleware",
]

ROOT_URLCONF = "studio.urls"
CRISPY_TEMPLATE_PACK = "bootstrap"

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
            ],
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


# Database
# https://docs.djangoproject.com/en/3.2/ref/settings/#databases
if sys.argv[1] == "test":
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
    "django.contrib.auth.backends.ModelBackend",
    "guardian.backends.ObjectPermissionBackend",
]

# Related to user registration and authetication workflow
LOGIN_REDIRECT_URL = "/projects"
LOGIN_URL = "login"
LOGOUT_URL = "logout"

# Make new user inactive by default
INACTIVE_USERS = False

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
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",  # noqa: E501
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",  # noqa: E501
    },
]


# Internationalization
# https://docs.djangoproject.com/en/3.2/topics/i18n/

LANGUAGE_CODE = "en-us"

TIME_ZONE = "UTC"

USE_I18N = True

USE_L10N = True

USE_TZ = True

# Media Files for Studio apps
MEDIA_URL = "/media/"
MEDIA_ROOT = os.path.join(BASE_DIR, "media/")

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/3.2/howto/static-files/

STATIC_URL = "/static/"
STATIC_ROOT = ""
STATICFILES_DIRS = (os.path.join("static"),)

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

# https://www.django-rest-framework.org/api-guide/authentication/#setting-the-authentication-scheme
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework.authentication.TokenAuthentication"
    ],
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
STORAGECLASS = "microk8s-hostpath"

# This can be simply "localhost", but it's better to test with a
# wildcard dns such as nip.io
DOMAIN = "studio.127.0.0.1.nip.io"
AUTH_DOMAIN = "10.0.144.239"
AUTH_PROTOCOL = "http"
STUDIO_URL = "http://studio.127.0.0.1.nip.io:8080"
# To enable sticky sessions for k8s ingress
SESSION_COOKIE_DOMAIN = ".127.0.0.1.nip.io"

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
EMAIL_BACKEND = "django.core.mail.backends.filebased.EmailBackend"
EMAIL_FILE_PATH = BASE_DIR / "sent_emails"

VERSION = "dev"
