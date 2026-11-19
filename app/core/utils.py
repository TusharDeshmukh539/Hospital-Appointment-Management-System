from datetime import date, datetime, time, timezone

def utc_now() -> datetime:
    #Current time in UTC (timezone aware).
    return datetime.now(timezone.utc)


def utc_now_naive() -> datetime:
    return utc_now().replace(tzinfo=None)


def slot_start_datetime(slot_date: date, start_time: time) -> datetime:
    #Combine a slot's date and start time into one datetime.
    return datetime.combine(slot_date, start_time)