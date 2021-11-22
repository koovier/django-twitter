from django.conf import settings

FANOUT_BATCH_SIZE = 1000 if not settings.TESTING else 3
