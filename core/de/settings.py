"""
Django settings for de project.
"""

import environ
from pathlib import Path
import boto3
import logging

# ==================== 初始化 environ ====================
env = environ.Env(
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

DEV_APPS = ["django_extensions"]

INSTALLED_APPS = BASE_APPS + THIRD_PARTY_APPS + PROJECT_APPS

if DEBUG:
    INSTALLED_APPS += DEV_APPS

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
TIME_ZONE = "Asia/Taipei"
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


class PrettyFormatter(logging.Formatter):
    """簡單彩色 formatter，顯示 extra"""

    COLORS = {
        "DEBUG": "\033[36m",
        "INFO": "\033[32m",
        "WARNING": "\033[33m",
        "ERROR": "\033[31m",
        "CRITICAL": "\033[35m",
    }
    RESET = "\033[0m"
    BOLD = "\033[1m"

    SKIP = {
        "name",
        "msg",
        "args",
        "created",
        "filename",
        "funcName",
        "levelname",
        "levelno",
        "lineno",
        "module",
        "msecs",
        "pathname",
        "process",
        "processName",
        "relativeCreated",
        "stack_info",
        "exc_info",
        "exc_text",
        "thread",
        "threadName",
        "taskName",
        "message",
        "asctime",
    }

    def format(self, record):
        color = self.COLORS.get(record.levelname, self.RESET)
        time = self.formatTime(record, "%H:%M:%S")

        # 收集 extra
        extras = {k: v for k, v in record.__dict__.items() if k not in self.SKIP}
        extra_str = f" | {extras}" if extras else ""

        # 前後空行 + 醒目格式
        return (
            f"\n"
            f"{color}{self.BOLD}[{record.levelname}]{self.RESET} "
            f"[{time}] "
            f"[{record.name}] "
            f"{record.getMessage()}"
            f"{extra_str}"
            f"\n"
        )


boto3_logs_client = boto3.client(
    "logs",
    aws_access_key_id=env("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=env("AWS_SECRET_ACCESS_KEY"),
    region_name=env("AWS_DEFAULT_REGION", default="ap-northeast-1"),
)

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
            "json_ensure_ascii": False,  # Ensure chinese characters display
        },
        "pretty": {
            "()": PrettyFormatter,
        },
    },
    # ===== Handlers =====
    "handlers": {
        "watchtower": {
            "level": "INFO",
            "class": "watchtower.CloudWatchLogHandler",
            "boto3_client": boto3_logs_client,
            "log_group": env("CLOUDWATCH_LOG_GROUP", default="/docker/etl"),
            "stream_name": "console",
            "formatter": "json",
            # "use_queues": False,  # Set to True in production
        },
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "pretty",
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
            "handlers": ["console", "file", "watchtower"],
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
