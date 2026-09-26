"""Wall-clock countdowns and local reset times for the two UI surfaces."""
from datetime import datetime, timezone
import math
import re

MONTHS_TR = ("Oca", "Şub", "Mar", "Nis", "May", "Haz", "Tem", "Ağu", "Eyl", "Eki", "Kas", "Ara")


def local_now():
    return datetime.now().astimezone()


def format_remaining_time(reset_at, now, mode="five_hour", compact=False):
    if mode not in ("five_hour", "weekly"):
        raise ValueError("Unknown countdown mode")
    for value in (reset_at, now):
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("Countdown requires timezone-aware dates")
    # UTC subtraction also handles DST transitions with the same ZoneInfo object.
    seconds = (reset_at.astimezone(timezone.utc) - now.astimezone(timezone.utc)).total_seconds()
    if seconds <= 0:
        return "Resetting…"
    minutes = math.ceil(seconds / 60)
    days, remainder = divmod(minutes, 1440)
    hours, mins = divmod(remainder, 60)
    if mode == "weekly":
        if days:
            duration = f"{days}d {hours}h" if compact else f"{days}d {hours:02d}h {mins:02d}m"
        elif hours:
            duration = f"{hours}h {mins:02d}m"
        else:
            duration = f"{mins}m"
    else:
        total_hours = minutes // 60
        duration = f"{total_hours:02d}:{mins:02d}" if total_hours else f"{mins}m"
    return f"Resets: {duration}"


def format_reset_display(reset_at, now, mode="five_hour", display="in", clock_format=24,
                         compact=False, language="en"):
    """Present remaining time, or local clock time with a date for weekly resets."""
    if display == "in":
        value = format_remaining_time(reset_at, now, mode, compact)
        if language == "tr":
            if value == "Resetting…":
                return "Sıfırlanıyor…"
            duration = value.removeprefix("Resets: ")
            duration = re.sub(r"(\d+)d\b", r"\1g", duration)
            duration = re.sub(r"(\d+)h\b", r"\1sa", duration)
            duration = re.sub(r"(\d+)m\b", r"\1dk", duration)
            return "Reset: " + duration
        return value.replace("Resets: ", "Reset: ", 1)
    if display != "at" or clock_format not in (12, 24):
        raise ValueError("Unknown reset display setting")
    if reset_at.tzinfo is None or reset_at.utcoffset() is None or now.tzinfo is None or now.utcoffset() is None:
        raise ValueError("Reset time requires timezone-aware dates")
    if reset_at.astimezone(timezone.utc) <= now.astimezone(timezone.utc):
        return "Sıfırlanıyor…" if language == "tr" else "Resetting…"
    # Resolve the target instant against the system timezone, including a
    # possible daylight-saving transition between now and the reset.
    local_reset = reset_at.astimezone()
    if clock_format == 24:
        clock = f"{local_reset.hour:02d}:{local_reset.minute:02d}"
    else:
        clock = f"{local_reset.hour % 12 or 12}:{local_reset.minute:02d} {'AM' if local_reset.hour < 12 else 'PM'}"
    if mode == "five_hour":
        return ("Sıfırlanır " if language == "tr" else "Resets at ") + clock
    if compact:
        return f"{local_reset.day:02d}/{local_reset.month:02d} {clock}"
    month = MONTHS_TR[local_reset.month - 1] if language == "tr" else local_reset.strftime("%b")
    clock = f"{local_reset.day:02d} {month} {clock}"
    return ("Sıfırlanır " if language == "tr" else "Resets at ") + clock
