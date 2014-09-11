import os

ADMINS = ()
DATABASES = {}


database_implementation = os.getenv('DATABASE', 'sqlite3')

DATABASES['default'] = {
    'sqlite3': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': 'django_atomic_signals.db',
    },
}[database_implementation]

SECRET_KEY = '_uobce43e5osp8xgzle*yag2_16%y$sf*5(12vfg25hpnxik_*'

INSTALLED_APPS = (
    'django_atomic_signals',
    'django_atomic_dispatch',
    'tests',
    'django_nose',
)

DEBUG = True

TEST_RUNNER = 'django_nose.NoseTestSuiteRunner'
NOSE_ARGS = ['--verbosity=2', '--detailed-errors', '--rednose']
