from datetime import date

from nldate import parse


def test_today():
    assert parse("today", today=date(2026, 5, 13)) == date(2026, 5, 13)


def test_tomorrow():
    assert parse("tomorrow", today=date(2026, 5, 13)) == date(2026, 5, 14)


def test_yesterday():
    assert parse("yesterday", today=date(2026, 5, 13)) == date(2026, 5, 12)


def test_in_3_days():
    assert parse("in 3 days", today=date(2026, 5, 13)) == date(2026, 5, 16)


def test_3_days_ago():
    assert parse("3 days ago", today=date(2026, 5, 13)) == date(2026, 5, 10)


def test_next_tuesday():
    assert parse("next Tuesday", today=date(2026, 5, 13)) == date(2026, 5, 19)


def test_last_friday():
    assert parse("last Friday", today=date(2026, 5, 13)) == date(2026, 5, 8)


def test_absolute_date():
    assert parse("December 1st, 2025") == date(2025, 12, 1)


def test_days_before_date():
    assert parse("5 days before December 1st, 2025") == date(2025, 11, 26)


def test_days_after_date():
    assert parse("2 days after December 1st, 2025") == date(2025, 12, 3)
