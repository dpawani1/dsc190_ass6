from __future__ import annotations

import calendar
import re
from datetime import date, timedelta

__all__ = ["parse"]

_WEEKDAYS: dict[str, int] = {
    "monday": 0,
    "tuesday": 1,
    "wednesday": 2,
    "thursday": 3,
    "friday": 4,
    "saturday": 5,
    "sunday": 6,
}

_MONTHS: dict[str, int] = {
    "jan": 1,
    "january": 1,
    "feb": 2,
    "february": 2,
    "mar": 3,
    "march": 3,
    "apr": 4,
    "april": 4,
    "may": 5,
    "jun": 6,
    "june": 6,
    "jul": 7,
    "july": 7,
    "aug": 8,
    "august": 8,
    "sep": 9,
    "sept": 9,
    "september": 9,
    "oct": 10,
    "october": 10,
    "nov": 11,
    "november": 11,
    "dec": 12,
    "december": 12,
}

_NUMBER_WORDS: dict[str, int] = {
    "one": 1,
    "two": 2,
    "three": 3,
    "four": 4,
    "five": 5,
    "six": 6,
    "seven": 7,
    "eight": 8,
    "nine": 9,
    "ten": 10,
}

_UNIT_PATTERN = r"(?:day|days|week|weeks|month|months|year|years)"
_OFFSET_PART_RE = re.compile(
    rf"(?P<amount>\d+|[a-z]+)\s+(?P<unit>{_UNIT_PATTERN})"
)
_BEFORE_AFTER_RE = re.compile(
    rf"^(?P<offsets>.+?)\s+(?P<direction>before|after|from)\s+(?P<base>.+)$"
)
_IN_RE = re.compile(rf"^in\s+(?P<offsets>.+)$")
_AGO_RE = re.compile(rf"^(?P<offsets>.+)\s+ago$")
_WEEKDAY_RE = re.compile(r"^(?P<direction>next|last)\s+(?P<weekday>[a-z]+)$")
_ISO_DATE_RE = re.compile(r"^(?P<year>\d{4})-(?P<month>\d{2})-(?P<day>\d{2})$")
_MONTH_NAME_DATE_RE = re.compile(
    r"^(?P<month>[a-z]+)\s+(?P<day>\d{1,2}),\s*(?P<year>\d{4})$"
)


def parse(s: str, today: date | None = None) -> date:
    base_today = date.today() if today is None else today
    normalized = _normalize(s)

    if normalized == "today":
        return base_today
    if normalized == "tomorrow":
        return base_today + timedelta(days=1)
    if normalized == "yesterday":
        return base_today - timedelta(days=1)

    weekday_match = _WEEKDAY_RE.fullmatch(normalized)
    if weekday_match is not None:
        direction = weekday_match.group("direction")
        weekday_name = weekday_match.group("weekday")
        return _parse_relative_weekday(base_today, direction, weekday_name)

    in_match = _IN_RE.fullmatch(normalized)
    if in_match is not None:
        offsets = _parse_offset_sequence(in_match.group("offsets"))
        return _apply_offset(base_today, offsets, 1)

    ago_match = _AGO_RE.fullmatch(normalized)
    if ago_match is not None:
        offsets = _parse_offset_sequence(ago_match.group("offsets"))
        return _apply_offset(base_today, offsets, -1)

    before_after_match = _BEFORE_AFTER_RE.fullmatch(normalized)
    if before_after_match is not None:
        offsets = _parse_offset_sequence(before_after_match.group("offsets"))
        direction = before_after_match.group("direction")
        base = parse(before_after_match.group("base"), today=base_today)
        sign = -1 if direction == "before" else 1
        return _apply_offset(base, offsets, sign)

    try:
        return _parse_absolute_date(normalized)
    except ValueError:
        pass

    raise ValueError(f"Unsupported date expression: {s!r}")


def _normalize(s: str) -> str:
    normalized = s.strip().lower()
    normalized = re.sub(r"\s+", " ", normalized)
    normalized = re.sub(r"\b(\d{1,2})(st|nd|rd|th)\b", r"\1", normalized)
    return normalized


def _parse_relative_weekday(
    today: date, direction: str, weekday_name: str
) -> date:
    try:
        target_weekday = _WEEKDAYS[weekday_name]
    except KeyError as exc:
        raise ValueError(f"Unsupported weekday: {weekday_name!r}") from exc

    current_weekday = today.weekday()
    if direction == "next":
        delta = (target_weekday - current_weekday) % 7
        if delta == 0:
            delta = 7
        return today + timedelta(days=delta)

    if direction == "last":
        delta = (current_weekday - target_weekday) % 7
        if delta == 0:
            delta = 7
        return today - timedelta(days=delta)

    raise ValueError(f"Unsupported weekday direction: {direction!r}")


def _parse_absolute_date(s: str) -> date:
    iso_match = _ISO_DATE_RE.fullmatch(s)
    if iso_match is not None:
        return date(
            year=int(iso_match.group("year")),
            month=int(iso_match.group("month")),
            day=int(iso_match.group("day")),
        )

    month_name_match = _MONTH_NAME_DATE_RE.fullmatch(s)
    if month_name_match is None:
        raise ValueError(f"Unsupported absolute date: {s!r}")

    month_name = month_name_match.group("month")
    month = _MONTHS.get(month_name)
    if month is None:
        raise ValueError(f"Unsupported month name: {month_name!r}")

    return date(
        year=int(month_name_match.group("year")),
        month=month,
        day=int(month_name_match.group("day")),
    )


def _parse_offset_sequence(s: str) -> list[tuple[int, str]]:
    parts = [part.strip() for part in s.split(" and ")]
    if not parts or any(not part for part in parts):
        raise ValueError(f"Invalid offset expression: {s!r}")

    offsets: list[tuple[int, str]] = []
    for part in parts:
        match = _OFFSET_PART_RE.fullmatch(part)
        if match is None:
            raise ValueError(f"Invalid offset expression: {s!r}")
        amount = _parse_number_token(match.group("amount"))
        unit = _canonical_unit(match.group("unit"))
        offsets.append((amount, unit))
    return offsets


def _parse_number_token(token: str) -> int:
    if token.isdigit():
        return int(token)

    amount = _NUMBER_WORDS.get(token)
    if amount is None:
        raise ValueError(f"Unsupported number word: {token!r}")
    return amount


def _canonical_unit(unit: str) -> str:
    if unit.endswith("s"):
        return unit[:-1]
    return unit


def _apply_offset(
    base: date, offsets: list[tuple[int, str]], sign: int
) -> date:
    result = base
    for amount, unit in offsets:
        result = _apply_single_offset(result, amount * sign, unit)
    return result


def _apply_single_offset(base: date, amount: int, unit: str) -> date:
    if unit == "day":
        return base + timedelta(days=amount)
    if unit == "week":
        return base + timedelta(weeks=amount)
    if unit == "month":
        return _add_months(base, amount)
    if unit == "year":
        return _add_years(base, amount)
    raise ValueError(f"Unsupported unit: {unit!r}")


def _add_months(base: date, months: int) -> date:
    month_index = base.month - 1 + months
    year = base.year + month_index // 12
    month = month_index % 12 + 1
    day = min(base.day, calendar.monthrange(year, month)[1])
    return date(year, month, day)


def _add_years(base: date, years: int) -> date:
    year = base.year + years
    day = min(base.day, calendar.monthrange(year, base.month)[1])
    return date(year, base.month, day)
