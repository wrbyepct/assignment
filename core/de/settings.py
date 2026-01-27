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

THIRD_PARTY_APPS = [
    "django_q",
]

PROJECT_APPS = ["core.tax_registration"]

INSTALLED_APPS = BASE_APPS + THIRD_PARTY_APPS + PROJECT_APPS

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


# 2. 配置 Django-Q2
Q_CLUSTER = {
    "name": "ETL_Cluster",
    "workers": 1,
    "queue_limit": 50,
    "recycle": 5,  # 執行 5 次任務後重啟 worker，防止記憶體洩漏
    "timeout": 7200,  # 2 小時（ETL 可能跑很久）
    "retry": 7300,  # 重試時間要略長於 timeout
    "orm": "default",  # 直接使用 DB，不需 Redis
    "compress": True,  # 任務資料壓縮後存，省 DB 空間
    "cpu_affinity": 1,  # 最佳化 CPU 使用
    "catch_up": False,  # ETL 是 full refresh（truncate + 重新匯入），補跑沒意義，反而可能造成重複執行
}

# ==================== Logging ====================
LOG_LEVEL = env("LOG_LEVEL", default="INFO")

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    # ===== Formatters =====
    "formatters": {
        "json": {
            "()": "pythonjsonlogger.jsonlogger.JsonFormatter",
            "format": "%(asctime)s %(levelname)s %(name)s %(message)s",
            "rename_fields": {
                "levelname": "level",
                "asctime": "timestamp",
            },
            "datefmt": "%Y-%m-%dT%H:%M:%S%z",
            "json_indent": 2 if DEBUG else None,
            "json_ensure_ascii": False,  # Ensure chinese characters display
        },
    },
    # ===== Handlers =====
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "json",
            "stream": "ext://sys.stdout",
        },
        "file": {
            "class": "logging.handlers.RotatingFileHandler",
            "formatter": "json",
            "filename": "/var/log/django/etl.log",
            # 輪替門檻：當檔案達到 10MB (10 * 1024 * 1024 bytes) 時，就切換新檔
            "maxBytes": 10 * 1024 * 1024,  # 10 MB
            # 備份數量：最多保留 5 個舊檔（etl.log.1, etl.log.2...）
            #  當產生第 6 個時，最舊的會被刪除。這叫「循環覆蓋」。
            "backupCount": 5,
            "encoding": "utf-8",
        },
    },
    # ===== Loggers =====
    "loggers": {
        "tax_registration": {
            "handlers": ["console", "file"],
            "level": LOG_LEVEL,
            "propagate": False,  # Don't send to root to duplicate logs
        },
    },
    # ===== Root Logger =====
    "root": {
        "handlers": ["console"],
        "level": "WARNING",  # Handle only third party WARNING log
    },
}
