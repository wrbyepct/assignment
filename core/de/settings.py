"""
Django settings for de project.
"""

import environ
from pathlib import Path

# ==================== 初始化 environ ====================
env = environ.Env(
    # 設定預設值與類型
    DEBUG=(bool, False),
    ALLOWED_HOSTS=(list, []),
    DB_PORT=(int, 5432),
    LOG_LEVEL=(str, "INFO"),
)

# Build paths
BASE_DIR = Path(__file__).resolve().parent.parent


# ==================== Django 基本設定 ====================
SECRET_KEY = env("SECRET_KEY")
DEBUG = env("DEBUG")
ALLOWED_HOSTS = env("ALLOWED_HOSTS")

# Application definition
BASE_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
]

PROJECT_APPS = ["core.tax_registration"]

INSTALLED_APPS = BASE_APPS + PROJECT_APPS

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "core.de.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "core.de.wsgi.application"

# ==================== Database ====================
DATABASES = {"default": env.db("DATABASE_URL")}

# ==================== Password validation ====================
AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

# ==================== Internationalization ====================
LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

# ==================== Static files ====================
STATIC_URL = "static/"

# ==================== ETL 設定（自訂）====================
CSV_URL = env("CSV_URL", default="https://eip.fia.gov.tw/data/BGMOPEN1.csv")
BATCH_SIZE = env.int("BATCH_SIZE", default=10000)
CHUNK_SIZE = env.int("CHUNK_SIZE", default=50000)

# ==================== Logging ====================
LOG_LEVEL = env("LOG_LEVEL", default="INFO")
