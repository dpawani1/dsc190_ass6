from datetime import date

import pytest

from nldate import parse


def test_today():
    assert parse("today", today=date(2026, 5, 13)) == date(2026, 5, 13)


def test_tonight_and_now():
    assert parse("tonight", today=date(2026, 5, 13)) == date(2026, 5, 13)
    assert parse("now", today=date(2026, 5, 13)) == date(2026, 5, 13)


def test_tomorrow():
    assert parse("tomorrow", today=date(2026, 5, 13)) == date(2026, 5, 14)


def test_yesterday():
    assert parse("yesterday", today=date(2026, 5, 13)) == date(2026, 5, 12)


def test_day_after_tomorrow():
    assert parse("the day after tomorrow", today=date(2026, 5, 13)) == date(2026, 5, 15)


def test_day_before_yesterday():
    assert parse("the day before yesterday", today=date(2026, 5, 13)) == date(
        2026, 5, 11
    )


def test_in_3_days():
    assert parse("in 3 days", today=date(2026, 5, 13)) == date(2026, 5, 16)


def test_after_3_days():
    assert parse("after 3 days", today=date(2026, 5, 13)) == date(2026, 5, 16)


def test_3_days_ago():
    assert parse("3 days ago", today=date(2026, 5, 13)) == date(2026, 5, 10)


def test_1_month_and_5_days_ago():
    assert parse("1 month and 5 days ago", today=date(2026, 5, 13)) == date(2026, 4, 8)


def test_next_tuesday():
    assert parse("next Tuesday", today=date(2026, 5, 13)) == date(2026, 5, 19)


def test_last_friday():
    assert parse("last Friday", today=date(2026, 5, 13)) == date(2026, 5, 8)


def test_this_monday():
    assert parse("this Monday", today=date(2026, 5, 13)) == date(2026, 5, 11)


def test_bare_weekday_including_today():
    assert parse("Wednesday", today=date(2026, 5, 13)) == date(2026, 5, 13)


def test_uppercase_weekday():
    assert parse("NEXT MONDAY", today=date(2026, 5, 13)) == date(2026, 5, 18)


def test_month_name_formats():
    assert parse("Dec. 1, 2025") == date(2025, 12, 1)
    assert parse("Dec 1, 2025") == date(2025, 12, 1)
    assert parse("December 1st, 2025") == date(2025, 12, 1)
    assert parse("1 December 2025") == date(2025, 12, 1)
    assert parse("January. 1, 2025") == date(2025, 1, 1)


def test_absolute_date_with_slashes():
    assert parse("2025/12/04") == date(2025, 12, 4)


def test_single_digit_day_year_first_with_slashes():
    assert parse("2025/12/3") == date(2025, 12, 3)


def test_absolute_date_with_dashes():
    assert parse("2025-12-04") == date(2025, 12, 4)


def test_single_digit_month_day_year_first_with_dashes():
    assert parse("2025-1-3") == date(2025, 1, 3)


def test_month_day_year_with_slashes():
    assert parse("12/04/2025") == date(2025, 12, 4)


def test_single_digit_month_day_year_with_slashes_requested_case():
    assert parse("1/3/2025") == date(2025, 1, 3)


def test_month_day_year_with_dashes():
    assert parse("12-04-2025") == date(2025, 12, 4)


def test_single_digit_month_day_year_with_dashes():
    assert parse("1-4-2025") == date(2025, 1, 4)


def test_days_before_date():
    assert parse("5 days before December 1st, 2025") == date(2025, 11, 26)


def test_days_before_abbreviated_date():
    assert parse("five days before Dec. 1, 2025") == date(2025, 11, 26)


def test_days_after_date():
    assert parse("2 days after December 1st, 2025") == date(2025, 12, 3)


def test_relative_offsets_from_base_dates():
    assert parse("2 weeks from tomorrow", today=date(2026, 5, 13)) == date(2026, 5, 28)
    assert parse("1 month before 2025/12/3") == date(2025, 11, 3)
    assert parse("ten days after yesterday", today=date(2026, 5, 13)) == date(
        2026, 5, 22
    )


def test_number_words_with_today():
    assert parse("one day from today", today=date(2026, 5, 13)) == date(2026, 5, 14)
    assert parse("three weeks ago", today=date(2026, 5, 13)) == date(2026, 4, 22)


def test_combined_offsets():
    assert parse(
        "1 year and 2 months after yesterday", today=date(2026, 5, 13)
    ) == date(2027, 7, 12)
    assert parse("2 weeks, 3 days from today", today=date(2026, 5, 13)) == date(
        2026, 5, 30
    )
    assert parse(
        "five days and two weeks after today", today=date(2026, 5, 13)
    ) == date(2026, 6, 1)


def test_month_and_year_clamping():
    assert parse("1 month after January 31, 2025") == date(2025, 2, 28)
    assert parse("1 year after February 29, 2024") == date(2025, 2, 28)


def test_next_month_phrase():
    assert parse("next month", today=date(2026, 1, 31)) == date(2026, 2, 28)


def test_last_year_phrase():
    assert parse("last year", today=date(2024, 2, 29)) == date(2023, 2, 28)


def test_invalid_inputs_raise_value_error():
    with pytest.raises(ValueError):
        parse("not a date")

    with pytest.raises(ValueError):
        parse("February 30, 2025")
