from pathlib import Path
from dotenv import load_dotenv
from kombu import Exchange, Queue
import os


# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(os.path.join(BASE_DIR, '.env'))

TEMPLATE_DIR = os.path.join(BASE_DIR, 'templates')

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-q=x+*59yj&s@!6&0jaghn$f$&js&_#s#xhzyh!mfb$51j6%c49'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True


ALLOWED_HOSTS = ['*']


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Third party
    'phonenumber_field',
    
    # Local
    'authentication',
    'accounts',
    # 'sms',
    'product',
    'sales',
    'sales_return',
    'purchase',
    'purchase_return',
    'inventory',
    'commons',
]

INSTALLED_APPS += ['sequences.apps.SequencesConfig']

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    # 'silk.middleware.SilkyMiddleware',
]

ROOT_URLCONF = 'core.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [TEMPLATE_DIR],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'core.wsgi.application'


AUTH_USER_MODEL = 'authentication.User'


CSRF_TRUSTED_ORIGINS = [
    "https://shop.xinotrix.com",
    "http://shop.xinotrix.com",
]

# AUTHENTICATION_BACKENDS = [
#     # 'django.contrib.auth.backends.ModelBackend',
#     'authentication.backends.EmailorPhoneModelBackend',
#     ]


# Database
# https://docs.djangoproject.com/en/4.1/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# DATABASES = {
#     'default': {
#         'ENGINE': 'django.db.backends.postgresql_psycopg2',
#         'NAME': os.environ.get('DB_NAME'),
#         'USER': os.environ.get('DB_USER'),
#         'PASSWORD': os.environ.get('DB_PASS'),
#         'HOST': os.environ.get('DB_HOST'),
#     }
# }


CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'CONFIG': {
            "hosts": [('127.0.0.1', 6379)],
        },
    },
}

CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': 'redis://127.0.0.1:6379/0',
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        },
    }
}

# Password validation
# https://docs.djangoproject.com/en/4.1/ref/settings/#auth-password-validators

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


# Internationalization
# https://docs.djangoproject.com/en/4.1/topics/i18n/

LANGUAGE_CODE = 'en-bd'

TIME_ZONE = 'Asia/Dhaka'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.1/howto/static-files/

STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATIC_URL = '/static/'
STATIC_DIR = os.path.join(BASE_DIR, 'static')

# Extra places for collectstatic to find static files.
STATICFILES_DIRS = [
    STATIC_DIR,
]

MEDIA_ROOT = os.path.join(BASE_DIR, 'media')
MEDIA_URL = '/media/'

# Default primary key field type
# https://docs.djangoproject.com/en/4.1/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# custom mail configurations
# EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
# EMAIL_HOST = 'mail.bluebayit.com'
# EMAIL_PORT = 587
# EMAIL_HOST_USER = 'admin@bluebayit.com'
# EMAIL_HOST_PASSWORD = 'bluebayit7811'
# EMAIL_USE_TLS = True


# REST_FRAMEWORK = {
#   'DEFAULT_AUTHENTICATION_CLASSES': (
#     'rest_framework_simplejwt.authentication.JWTAuthentication',
#   ),
#   'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
#   'DEFAULT_PARSER_CLASSES': [
#         'rest_framework.parsers.MultiPartParser',
#         'rest_framework.parsers.JSONParser',
#         'rest_framework.parsers.FormParser',
#     ],
#     'DEFAULT_FILTER_BACKENDS': (
#         'django_filters.rest_framework.DjangoFilterBackend',
#     ),
# }

# SPECTACULAR_SETTINGS = {
#     'TITLE': 'SMS Server',
#     'DESCRIPTION': '',
#     'VERSION': '1.0.0',
#     # OTHER SETTINGS
# 		# available SwaggerUI configuration parameters
#     # https://swagger.io/docs/open-source-tools/swagger-ui/usage/configuration/
#     "SWAGGER_UI_SETTINGS": {
#         "deepLinking": True,
#         "persistAuthorization": True,
#         # "displayOperationId": True,
#     },
#     # available SwaggerUI versions: https://github.com/swagger-api/swagger-ui/releases
#     "SWAGGER_UI_DIST": "//unpkg.com/swagger-ui-dist@3.35.1", # default
#     # "SWAGGER_UI_FAVICON_HREF": STATIC_URL + "your_company_favicon.png", # default is swagger favicon
# 		# "APPEND_COMPONENTS": {
# 		# "securitySchemes": {
# 		# 		"ApiKeyAuth": {
# 		# 				"type": "apiKey",
# 		# 				"in": "header",
# 		# 				"name": "Authorization"
# 		# 		}
# 		# 	}
#     # },
#     # "SECURITY": [{"ApiKeyAuth": [], }],
# }

# SIMPLE_JWT = {
#     'ACCESS_TOKEN_LIFETIME': timedelta(days=30),
#     'REFRESH_TOKEN_LIFETIME': timedelta(days=1),
#     'ROTATE_REFRESH_TOKENS': False,
#     'BLACKLIST_AFTER_ROTATION': True,
#     'UPDATE_LAST_LOGIN': True,

#     'ALGORITHM': 'HS256',
#     # 'SIGNING_KEY': settings.SECRET_KEY,
#     'VERIFYING_KEY': None,
#     'AUDIENCE': None,
#     'ISSUER': None,
#     'AUTH_HEADER_TYPES': ('Bearer',),
#     'AUTH_HEADER_NAME': 'HTTP_AUTHORIZATION',
#     'USER_ID_FIELD': 'id',
#     'USER_ID_CLAIM': 'user_id',
#     'USER_AUTHENTICATION_RULE': 'rest_framework_simplejwt.authentication.default_user_authentication_rule',
#     'AUTH_TOKEN_CLASSES': ('rest_framework_simplejwt.tokens.AccessToken',),
#     'TOKEN_TYPE_CLAIM': 'token_type',
#     'JTI_CLAIM': 'jti',
#     'SLIDING_TOKEN_REFRESH_EXP_CLAIM': 'refresh_exp',
#     'SLIDING_TOKEN_LIFETIME': timedelta(minutes=5),
#     'SLIDING_TOKEN_REFRESH_LIFETIME': timedelta(days=1),
# }



# DJOSER = {
#     'LOGIN_FIELD': 'email',
#     'USER_CREATE_PASSWORD_RETYPE': True,
#     'USERNAME_CHANGED_EMAIL_CONFIRMATION': True,
#     'PASSWORD_CHANGED_EMAIL_CONFIRMATION': True,
#     'SEND_CONFIRMATION_EMAIL': True,
#     'SET_USERNAME_RETYPE': True,
#     'SET_PASSWORD_RETYPE': True,
#     'PASSWORD_RESET_CONFIRM_URL': 'password/reset/confirm/{uid}/{token}',
#     'USERNAME_RESET_CONFIRM_URL': 'email/reset/confirm/{uid}/{token}',
#     'ACTIVATION_URL': 'activate/{uid}/{token}',
#     'SEND_ACTIVATION_EMAIL': True,
#     'SERIALIZERS': {
#     'user_create': 'authentication.serializers.UserSerializer',
#     'user': 'authentication.serializers.UserSerializer',
#     'current_user': 'authentication.serializers.UserSerializer',
#     'user_delete': 'djoser.  .UserDeleteSerializer',
#     }
# }



#NEVER USER THIS IF YOU NEED LOCAL DATA ON HEROKU
# Simplified static file serving.
# https://warehouse.python.org/project/whitenoise/

# STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
# Activate Django-Heroku.
# django_heroku.settings(locals())


# Celery settings
# CELERY_BROKER_URL = "amqp://guest:guest@localhost:5672"
CELERY_BROKER_URL = 'redis://localhost:6379/0'
CELERY_RESULT_BACKEND = 'redis://localhost:6379/0'
CELERY_TIMEZONE = 'Asia/Dhaka'
CELERY_BROKER_CONNECTION_RETRY_ON_STARTUP = True

CELERY_TASK_QUEUES = [
    Queue('sms_server_queue', Exchange('sms_server'), routing_key='sms_server.#'),
]
CELERY_TASK_DEFAULT_QUEUE = 'sms_server_queue'
CELERY_TASK_DEFAULT_ROUTING_KEY = 'sms_server.default'



# URL settings for password reset
LOGIN_URL = 'login'
LOGOUT_URL = 'logout'
LOGIN_REDIRECT_URL = 'home'
LOGOUT_REDIRECT_URL = 'login'