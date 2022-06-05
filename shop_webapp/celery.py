from __future__ import unicode_literals, absolute_import

import os

from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "shop_webapp.settings")

app = Celery("shop_webapp")

app.config_from_object("django.conf:settings", namespace="CELERY")

app.autodiscover_tasks()
