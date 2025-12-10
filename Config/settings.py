# Config/settings.py
from pathlib import Path
import os

BASE_DIR = Path(__file__).resolve().parent.parent

# -------------------------
# SECURITY
# -------------------------
SECRET_KEY = 'django-@ana$RadyasIn%adfnj2$Sj3vj1!jndjrjbfha'
DEBUG = True  # ❗ سرور = False

ALLOWED_HOSTS = [
    '91.107.251.83',
    'anamholding.com',
    'www.anamholding.com',
    'localhost',
    '127.0.0.1',
]

CSRF_TRUSTED_ORIGINS = [
    'http://91.107.251.83',
    'http://anamholding.com',
    'http://www.anamholding.com',
    'https://anamholding.com',
    'https://www.anamholding.com',
]

# -------------------------
# INSTALLED APPS
# -------------------------
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    "django.contrib.sitemaps",
    'admin_panel.apps.AdminPanelConfig',
    'errors.apps.ErrorsConfig',
    'accounts.apps.AccountsConfig',
    'home.apps.HomeConfig',
    'zlink.apps.ZlinkConfig',
]

ROOT_URLCONF = 'Config.urls'

AUTH_USER_MODEL = 'accounts.User'

# -------------------------
# MIDDLEWARE
# -------------------------
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',

    # برای استاتیک nginx لازم میشه
    'django.middleware.gzip.GZipMiddleware',

    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',

    'accounts.middleware.CurrentUserMiddleware',

    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# -------------------------
# TEMPLATES
# -------------------------
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'Config.wsgi.application'

# -------------------------
# DATABASE (MySQL)
# -------------------------
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'AnamFirstStep',
        'USER': 'anamuser',
        'PASSWORD': 'raYasANaM$1',
        'HOST': '127.0.0.1',
        'PORT': '3306',

        # بهترین حالت برای سرور
        'OPTIONS': {
            'charset': 'utf8mb4',
            'init_command': "SET sql_mode='STRICT_ALL_TABLES'"
        }
    }
}

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.filebased.FileBasedCache",
        "LOCATION": BASE_DIR / "cache",
    }
}

# -------------------------
# PASSWORD VALIDATION
# -------------------------
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'fa-ir'
TIME_ZONE = 'Asia/Tehran'
USE_I18N = True
USE_TZ = True

# -------------------------
# STATIC FILES
# -------------------------
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [
    BASE_DIR / 'static',
]

# -------------------------
# MEDIA
# -------------------------
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
