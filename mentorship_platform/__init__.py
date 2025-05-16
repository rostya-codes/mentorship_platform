# mentorship_platform/__init__.py
from __future__ import absolute_import, unicode_literals

# Імпортуємо Celery, щоб він запускався разом з Django
from .celery import app as celery_app

__all__ = ('celery_app',)
