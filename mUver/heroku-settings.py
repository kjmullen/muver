import dj_database_url
from .settings import *


DEBUG = False
SECRET_KEY = os.environ['SECRET_KEY']

DATABASES['default'] = dj_database_url.config()
DATABASES['default']['ENGINE'] = 'django.contrib.gis.db.backends.postgis'

SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

ALLOWED_HOSTS = ['*']

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

STATIC_URL = '/static/'
STATIC_ROOT = 'staticfiles'

STATICFILES_STORAGE = 'whitenoise.django.GzipManifestStaticFilesStorage'
