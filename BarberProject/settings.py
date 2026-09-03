"""
Django settings for BarberProject project.
"""

import os
from pathlib import Path

# Carrega variáveis de ambiente de .env se existir
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.getenv('DJANGO_SECRET_KEY')
if not SECRET_KEY:
    if os.getenv('DJANGO_DEBUG', 'True').lower() in ('true', '1', 'yes'):
        SECRET_KEY = 'django-insecure-k8$x!q3v@mz#7f&w+r2^t9p=y6u0j4e1s5n8c_b(g)d%hloai'
    else:
        from django.core.exceptions import ImproperlyConfigured
        raise ImproperlyConfigured("DJANGO_SECRET_KEY é obrigatória em ambiente de produção (DEBUG=False).")

DEBUG = os.getenv('DJANGO_DEBUG', 'True').lower() in ('true', '1', 'yes')

ALLOWED_HOSTS = [
    host.strip()
    for host in os.getenv('DJANGO_ALLOWED_HOSTS', '*').split(',')
    if host.strip()
]

CSRF_TRUSTED_ORIGINS = [
    origin.strip()
    for origin in os.getenv('DJANGO_CSRF_TRUSTED_ORIGINS', 'http://localhost:8000,http://127.0.0.1:8000').split(',')
    if origin.strip()
]

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'website',
    'crispy_forms',
    'crispy_bootstrap5',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'BarberProject.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'website' / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'website.context_processors.user_roles',
                'website.context_processors.brand_context',
            ],
        },
    },
]

WSGI_APPLICATION = 'BarberProject.wsgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# Suporte a PostgreSQL em Produção via DATABASE_URL
DATABASE_URL = os.getenv('DATABASE_URL')
if DATABASE_URL:
    try:
        import dj_database_url
        DATABASES['default'] = dj_database_url.config(default=DATABASE_URL, conn_max_age=600)
    except ImportError:
        pass

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'pt-br'

TIME_ZONE = 'America/Sao_Paulo'

USE_I18N = True

USE_TZ = True

STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [
    BASE_DIR / 'website' / 'static',
]
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

CRISPY_ALLOWED_TEMPLATE_PACKS = 'bootstrap5'

CRISPY_TEMPLATE_PACK = 'bootstrap5'

LOGIN_URL = 'login'

LOGIN_REDIRECT_URL = 'dashboard'

LOGOUT_REDIRECT_URL = 'pagina_inicial'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# ==============================================================================
# CONFIGURAÇÃO CENTRAL DA MARCA — BARBER HEITOR
# ==============================================================================
BARBER_NAME = os.getenv('BARBER_NAME', 'Barber Heitor')
BARBER_SHORT_NAME = os.getenv('BARBER_SHORT_NAME', 'Barber Heitor')
BARBER_SLOGAN = os.getenv('BARBER_SLOGAN', 'Seu estilo. Sua assinatura.')
BARBER_PHONE = os.getenv('BARBER_PHONE', '(44) 9102-2176')
BARBER_PHONE_RAW = os.getenv('BARBER_PHONE_RAW', '554491022176')
BARBER_EMAIL = os.getenv('BARBER_EMAIL', 'contato@barberheitor.com.br')
BARBER_INSTAGRAM = os.getenv('BARBER_INSTAGRAM', 'barberheitor_oficial')
BARBER_ADDRESS = os.getenv('BARBER_ADDRESS', 'Rua Terezinha Fortes Martins, 136, Jardim Progresso, Paranavaí - PR')
BARBER_HOURS = os.getenv('BARBER_HOURS', 'Seg a Sáb: 08:00 às 21:00')

# ==============================================================================
# CONFIGURAÇÕES DE MÓDULOS, PAGAMENTOS E INTEGRAÇÕES
# ==============================================================================
PAYMENT_GATEWAY = os.getenv('PAYMENT_GATEWAY', 'mock')
PAYMENT_ACCESS_TOKEN = os.getenv('PAYMENT_ACCESS_TOKEN', '')
PAYMENT_WEBHOOK_SECRET = os.getenv('PAYMENT_WEBHOOK_SECRET', '')
PIX_CHAVE = os.getenv('PIX_CHAVE', '')
PIX_TITULAR = os.getenv('PIX_TITULAR', 'Barber Heitor')
PIX_CIDADE = os.getenv('PIX_CIDADE', 'Paranavai')

WHATSAPP_PROVIDER = os.getenv('WHATSAPP_PROVIDER', 'none')
WHATSAPP_API_TOKEN = os.getenv('WHATSAPP_API_TOKEN', '')
WHATSAPP_PHONE_NUMBER_ID = os.getenv('WHATSAPP_PHONE_NUMBER_ID', '')

AI_PROVIDER = os.getenv('AI_PROVIDER', 'mock')
AI_API_KEY = os.getenv('AI_API_KEY', '')

VAPID_PUBLIC_KEY = os.getenv('VAPID_PUBLIC_KEY', '')
VAPID_PRIVATE_KEY = os.getenv('VAPID_PRIVATE_KEY', '')
VAPID_ADMIN_EMAIL = os.getenv('VAPID_ADMIN_EMAIL', 'contato@barberheitor.com.br')

