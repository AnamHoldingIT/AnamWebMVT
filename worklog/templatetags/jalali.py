import jdatetime
from django import template

register = template.Library()


@register.filter
def jalali_date(value):
    if not value:
        return ""
    # اگر datetime بود، date بگیر
    g_date = getattr(value, "date", lambda: value)()
    j = jdatetime.date.fromgregorian(date=g_date)
    return f"{j.year}/{j.month:02d}/{j.day:02d}"
