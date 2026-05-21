from celery import Celery

celery = Celery('workers')
celery.config_from_object('celery_app.config:CeleryConfig')
celery.autodiscover_tasks(['celery_app'])
