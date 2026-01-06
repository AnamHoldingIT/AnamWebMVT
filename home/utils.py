from django.core.cache import cache
from django.db.models import F
from .models import SiteStat


def increase_views_cached(step=1, flush_threshold=100):
    key = "site_views_buffer"
    try:
        buffer = cache.incr(key, step)
    except ValueError:
        cache.set(key, step, 600)
        buffer = step

    if buffer >= flush_threshold:
        SiteStat.objects.get_or_create(pk=1, defaults={"total_views": 0})
        SiteStat.objects.filter(pk=1).update(total_views=F("total_views") + buffer)
        cache.set(key, 0, 600)
