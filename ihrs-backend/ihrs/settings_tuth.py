
"""
TUTH's settings -- same Django app code as Bir, but pointed at a
different database ENGINE entirely (MariaDB via XAMPP, MySQL-compatible).
This file is never used by default -- only when a server process is
explicitly started with DJANGO_SETTINGS_MODULE=ihrs.settings_tuth,
so Bir's normal `python manage.py runserver` is completely unaffected.
"""

# $env:DJANGO_SETTINGS_MODULE="ihrs.settings_tuth"
import pymysql
pymysql.install_as_MySQLdb()  # MUST run before Django touches the DB backend



from .settings import *  # noqa -- inherit everything else (apps, RSA, DRF, etc.)

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.mysql",
        "NAME": "tuth_db",
        "USER": "root",
        "PASSWORD": "ihrs123",  # whatever you set for the 3307 instance
        "HOST": "127.0.0.1",   # use 127.0.0.1, not localhost -- avoids the socket/TCP ambiguity we just hit
        "PORT": "3307",
    }
}

# See settings.py for why this exists -- MUST differ from Bir's "BIR",
# otherwise both hospitals generate identical NHIDs (e.g. NH-00001-KTM
# on both sides) because their Patient.id sequences are independent.
HOSPITAL_CODE = "TUTH"