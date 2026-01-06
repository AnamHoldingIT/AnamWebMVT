# worklog/dates.py
import jdatetime
from datetime import date


def parse_jalali_date(value: str) -> date:
    value = value.strip().replace("/", "-")
    try:
        y, m, d = map(int, value.split("-"))
        return jdatetime.date(y, m, d).togregorian()
    except Exception:
        raise ValueError("Invalid jalali date")

def format_jalali_date(g_date: date) -> str:
    """
    datetime.date -> '1404-09-26'
    """
    if not g_date:
        return ""
    j = jdatetime.date.fromgregorian(date=g_date)
    return f"{j.year}-{j.month:02d}-{j.day:02d}"
