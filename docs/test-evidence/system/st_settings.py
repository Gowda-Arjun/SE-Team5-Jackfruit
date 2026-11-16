"""Settings for the system test run: a throw-away SQLite DB, media and mail folder.

The work folder comes from HMS_ST_WORK so the real db.sqlite3 and media/ are never touched.
Emails are written to files so the runner can read the password-reset OTP and the
complaint notifications, as a tester would read them from MailHog.
"""
import os
from pathlib import Path

from config.settings import *  # noqa: F401,F403

_WORK = Path(os.environ["HMS_ST_WORK"])
DATABASES = {"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": _WORK / "st.sqlite3"}}
MEDIA_ROOT = _WORK / "media"
EMAIL_BACKEND = "django.core.mail.backends.filebased.EmailBackend"
EMAIL_FILE_PATH = str(_WORK / "mail")
PAYMENT_GATEWAY = "mock"
