import os
from pathlib import Path

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

SECRET_KEY = '!$p@0nhnw%fkql36xg46^5z9sz7=02y1w)@4nxghl5qf_#b(5$'

DEBUG = True

ALLOWED_HOSTS = ['127.0.0.1', '.herokuapp.com']

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'userapp',
    'accounts', # カスタムユーザー
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',  # 追加
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'


ROOT_URLCONF = 'nagoyameshi.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'userapp.context_processors.common',
            ],
        },
    },
]

WSGI_APPLICATION = 'nagoyameshi.wsgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

LANGUAGE_CODE = 'ja'

TIME_ZONE = 'Asia/Tokyo'

USE_I18N = True

USE_L10N = True

USE_TZ = True

STATIC_URL = '/static/'

STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'userapp/static'),
]

# STATIC_ROOT の設定
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

LOGIN_URL = 'userapp:login'
LOGOUT_REDIRECT_URL = 'userapp:index'
LOGIN_REDIRECT_URL = 'userapp:index'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Stripe settings
STRIPE_SECRET_KEY = 'sk_test_51PegsNHgh7sLH8myPovEAkC4vKrXmAMecdKrBbaW7tS4tKWH0ATCpAjz0HS5Qdbc5lnH1Zu5WHI4quuQCYTsx4fF0033T7zJoP'
STRIPE_PUBLISHABLE_KEY = 'pk_test_51PegsNHgh7sLH8myw7KsXeXiADJWvP4d7hfco1kOfb1hTxeEZw8f4PdgXNxhri368KMNGeu3AehTuWBP6reIdH0i00JjXSkETX'
STRIPE_PRICE_ID = 'price_1PehRdHgh7sLH8myyNDfnci9'


# Custom authentication backend
AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',  # 既存の認証バックエンド
    'userapp.backends.EmailBackend',  # 新しいメールアドレス認証バックエンド
    'accounts.backends.CustomUserBackend', # カスタム認証バックエンドを使用
]


AUTH_USER_MODEL = 'accounts.CustomUser'


EMAIL_BACKEND   = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'userhanako@gmail.com'  # アプリ管理者のメールアドレス
EMAIL_HOST_PASSWORD = 'hanakohanako'  # アプリ管理者のGmailのパスワード
DEFAULT_FROM_EMAIL = 'userhanako@gmail.com'  # メールの送信元アドレス

EMAIL_HOST_USER = os.getenv('userhanako@gmail.com')
EMAIL_HOST_PASSWORD = os.getenv('hanakohanako')



