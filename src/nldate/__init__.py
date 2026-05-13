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

_SMALL_NUMBER_WORDS: dict[str, int] = {
    "zero": 0,
    "a": 1,
    "an": 1,
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
    "eleven": 11,
    "twelve": 12,
    "thirteen": 13,
    "fourteen": 14,
    "fifteen": 15,
    "sixteen": 16,
    "seventeen": 17,
    "eighteen": 18,
    "nineteen": 19,
}

_TENS_NUMBER_WORDS: dict[str, int] = {
    "twenty": 20,
    "thirty": 30,
    "forty": 40,
    "fifty": 50,
    "sixty": 60,
    "seventy": 70,
    "eighty": 80,
    "ninety": 90,
}

_UNIT_PATTERN = r"(?:day|days|week|weeks|month|months|year|years)"
_YEAR_FIRST_DATE_RE = re.compile(
    r"^(?P<year>\d{4})[-/](?P<month>\d{1,2})[-/](?P<day>\d{1,2})$"
)
_YEAR_LAST_DATE_RE = re.compile(
    r"^(?P<month>\d{1,2})[-/](?P<day>\d{1,2})[-/](?P<year>\d{4})$"
)
_MONTH_DAY_YEAR_RE = re.compile(
    r"^(?P<month>[a-z]+)\s+(?P<day>\d{1,2})(?:\s*,\s*|\s+)(?P<year>\d{4})$"
)
_DAY_MONTH_YEAR_RE = re.compile(
    r"^(?P<day>\d{1,2})\s+(?P<month>[a-z]+)\s+(?P<year>\d{4})$"
)
_OFFSET_WITH_BASE_RE = re.compile(
    r"^(?P<offsets>.+?)\s+(?P<direction>before|after|from)\s+(?P<base>.+)$"
)
_PREFIX_DIRECTION_RE = re.compile(r"^(?P<direction>in|after|before)\s+(?P<offsets>.+)$")
_SUFFIX_DIRECTION_RE = re.compile(r"^(?P<offsets>.+)\s+(?P<direction>ago|later)$")
_QUALIFIED_WEEKDAY_RE = re.compile(
    r"^(?P<direction>next|last|this)\s+(?P<weekday>[a-z]+)$"
)
_OFFSET_PART_RE = re.compile(rf"^(?P<amount>.+?)\s+(?P<unit>{_UNIT_PATTERN})$")


def parse(s: str, today: date | None = None) -> date:
    base_today = date.today() if today is None else today
    normalized = _normalize(s)

    if not normalized:
        raise ValueError("Unsupported date expression: empty string")

    return _parse_normalized(normalized, base_today)


def _parse_normalized(s: str, today: date) -> date:
    if s in {"today", "tonight", "now"}:
        return today
    if s == "tomorrow":
        return today + timedelta(days=1)
    if s == "yesterday":
        return today - timedelta(days=1)

    qualified_weekday_match = _QUALIFIED_WEEKDAY_RE.fullmatch(s)
    if qualified_weekday_match is not None:
        return _parse_relative_weekday(
            today=today,
            direction=qualified_weekday_match.group("direction"),
            weekday_name=qualified_weekday_match.group("weekday"),
        )

    if s in _WEEKDAYS:
        return _parse_bare_weekday(today=today, weekday_name=s)

    offset_with_base_match = _OFFSET_WITH_BASE_RE.fullmatch(s)
    if offset_with_base_match is not None:
        offsets = _parse_offset_sequence(offset_with_base_match.group("offsets"))
        direction = offset_with_base_match.group("direction")
        base = _parse_normalized(offset_with_base_match.group("base"), today)
        sign = -1 if direction == "before" else 1
        return _apply_offset(base, offsets, sign)

    prefix_direction_match = _PREFIX_DIRECTION_RE.fullmatch(s)
    if prefix_direction_match is not None:
        offsets = _parse_offset_sequence(prefix_direction_match.group("offsets"))
        direction = prefix_direction_match.group("direction")
        sign = -1 if direction == "before" else 1
        return _apply_offset(today, offsets, sign)

    suffix_direction_match = _SUFFIX_DIRECTION_RE.fullmatch(s)
    if suffix_direction_match is not None:
        offsets = _parse_offset_sequence(suffix_direction_match.group("offsets"))
        direction = suffix_direction_match.group("direction")
        sign = -1 if direction == "ago" else 1
        return _apply_offset(today, offsets, sign)

    return _parse_absolute_date(s)


def _normalize(s: str) -> str:
    normalized = s.strip().lower()
    normalized = re.sub(r"\s+", " ", normalized)
    normalized = re.sub(r"\b(\d{1,2})(st|nd|rd|th)\b", r"\1", normalized)
    normalized = re.sub(r"\b([a-z]+)\.(?=\s|$)", r"\1", normalized)
    normalized = re.sub(r"\s*,\s*", ", ", normalized)
    normalized = re.sub(r"\s+", " ", normalized)
    return normalized.strip()


def _parse_relative_weekday(today: date, direction: str, weekday_name: str) -> date:
    target_weekday = _get_weekday(weekday_name)
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

    if direction == "this":
        return today + timedelta(days=target_weekday - current_weekday)

    raise ValueError(f"Unsupported weekday direction: {direction!r}")


def _parse_bare_weekday(today: date, weekday_name: str) -> date:
    target_weekday = _get_weekday(weekday_name)
    delta = (target_weekday - today.weekday()) % 7
    return today + timedelta(days=delta)


def _get_weekday(weekday_name: str) -> int:
    try:
        return _WEEKDAYS[weekday_name]
    except KeyError as exc:
        raise ValueError(f"Unsupported weekday: {weekday_name!r}") from exc


def _parse_absolute_date(s: str) -> date:
    year_first_match = _YEAR_FIRST_DATE_RE.fullmatch(s)
    if year_first_match is not None:
        return date(
            year=int(year_first_match.group("year")),
            month=int(year_first_match.group("month")),
            day=int(year_first_match.group("day")),
        )

    year_last_match = _YEAR_LAST_DATE_RE.fullmatch(s)
    if year_last_match is not None:
        return date(
            year=int(year_last_match.group("year")),
            month=int(year_last_match.group("month")),
            day=int(year_last_match.group("day")),
        )

    month_day_year_match = _MONTH_DAY_YEAR_RE.fullmatch(s)
    if month_day_year_match is not None:
        return date(
            year=int(month_day_year_match.group("year")),
            month=_parse_month_name(month_day_year_match.group("month")),
            day=int(month_day_year_match.group("day")),
        )

    day_month_year_match = _DAY_MONTH_YEAR_RE.fullmatch(s)
    if day_month_year_match is not None:
        return date(
            year=int(day_month_year_match.group("year")),
            month=_parse_month_name(day_month_year_match.group("month")),
            day=int(day_month_year_match.group("day")),
        )

    raise ValueError(f"Unsupported date expression: {s!r}")


def _parse_month_name(token: str) -> int:
    month = _MONTHS.get(token)
    if month is None:
        raise ValueError(f"Unsupported month name: {token!r}")
    return month


def _parse_offset_sequence(s: str) -> list[tuple[int, str]]:
    parts = [part.strip() for part in re.split(r"\s*(?:,|and)\s*", s) if part.strip()]
    if not parts:
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

    compact = token.replace("-", " ")
    words = [word for word in compact.split() if word]
    if not words:
        raise ValueError(f"Unsupported number word: {token!r}")

    if len(words) == 1:
        if words[0] in _SMALL_NUMBER_WORDS:
            return _SMALL_NUMBER_WORDS[words[0]]
        if words[0] in _TENS_NUMBER_WORDS:
            return _TENS_NUMBER_WORDS[words[0]]
        raise ValueError(f"Unsupported number word: {token!r}")

    if (
        len(words) == 2
        and words[0] in _TENS_NUMBER_WORDS
        and words[1] in _SMALL_NUMBER_WORDS
    ):
        ones = _SMALL_NUMBER_WORDS[words[1]]
        if ones >= 10:
            raise ValueError(f"Unsupported number word: {token!r}")
        return _TENS_NUMBER_WORDS[words[0]] + ones

    raise ValueError(f"Unsupported number word: {token!r}")


def _canonical_unit(unit: str) -> str:
    if unit.endswith("s"):
        return unit[:-1]
    return unit


def _apply_offset(base: date, offsets: list[tuple[int, str]], sign: int) -> date:
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
