from __future__ import absolute_import, unicode_literals

import os

from celery import Celery

# Вказуємо Django, який файл settings використовувати
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mentorship_platform.settings')

app = Celery('mentorship_platform')

# Налаштування з settings.py (ті, що починаються з "CELERY_")
app.config_from_object('django.conf:settings', namespace='CELERY')

# Автоматично шукати задачі у всіх додатках
app.autodiscover_tasks()


@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')
