from croniter import croniter

import datetime
import random
import pytz


def utcnow():
    return datetime.datetime.utcnow().replace(tzinfo=datetime.timezone.utc)


def to_tz(dt, tz):
    tzobj = pytz.timezone(tz)

    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=datetime.timezone.utc)

    return dt.astimezone(tzobj)


def to_utc(dt):
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=datetime.timezone.utc)

    return dt.astimezone(datetime.timezone.utc)


def next_fire(schedule, base=None):
    now = base or utcnow()
    t = getattr(schedule, "schedule_type", None)

    if t and getattr(t, "value", None) == "ONEOFF":
        return None
    
    if t and getattr(t, "value", None) == "INTERVAL":
        n = now + datetime.timedelta(seconds=schedule.interval_seconds or 0)
        if getattr(schedule, "jitter_seconds", 0):
            n = n + datetime.timedelta(seconds=random.randint(0, schedule.jitter_seconds))
        return n
    
    if t and getattr(t, "value", None) == "CRON":
        zone_now = to_tz(now, schedule.timezone)
        it = croniter(schedule.cron_expr, zone_now)
        n = it.get_next(datetime.datetime)
        n_utc = to_utc(n)

        if getattr(schedule, "jitter_seconds", 0):
            n_utc = n_utc + datetime.timedelta(seconds=random.randint(0, schedule.jitter_seconds))

        return n_utc
    
    return None
