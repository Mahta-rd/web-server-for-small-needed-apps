# core/detector.py
"""
Module for detecting calendar type of input date string
Detection based on: format, year range, and priority rules
"""

import re
from datetime import datetime
from jdatetime import date as jdate
import logging
logger = logging.getLogger(__name__)


def detect_calendar_type(date_str: str) -> str:
    """
    Detect calendar type of input date string

    Args:
        date_str: date string like "1402/10/11" or "2024-01-01"

    Returns:
        'jalali', 'gregorian', or 'hijri'

    Raises:
        ValueError: if date cannot be detected or has invalid format
    """

    # Remove leading/trailing whitespace
    date_str = date_str.strip()

    if not date_str:
        raise ValueError("Date string is empty")

    # ============================================================
    # Step 1: Detect based on format (separator)
    # ============================================================
    if '-' in date_str:
        # Standard Gregorian format: YYYY-MM-DD
        return _detect_by_format(date_str, separator='-')
    elif '/' in date_str:
        # Jalali or Hijri format: YYYY/MM/DD
        return _detect_by_format(date_str, separator='/')
    else:
        raise ValueError(f"Invalid date format. Use '/' or '-' separator. Input: {date_str}")


def _detect_by_format(date_str: str, separator: str) -> str:
    """
    Detect calendar type based on format and year range

    Args:
        date_str: date string
        separator: separator character ('/' or '-')

    Returns:
        Detected calendar type
    """
    # Parse date components
    parts = date_str.split(separator)
    if len(parts) != 3:
        raise ValueError(f"Invalid date format. Must be YYYY{separator}MM{separator}DD. Input: {date_str}")

    try:
        year = int(parts[0])
        month = int(parts[1])
        day = int(parts[2])
    except ValueError:
        raise ValueError(f"Year, month and day must be numbers. Input: {date_str}")

    # Basic validation of month and day (before type detection)
    if month < 1 or month > 12:
        raise ValueError(f"Month must be between 1 and 12. Input: {month}")
    if day < 1 or day > 31:
        raise ValueError(f"Day must be between 1 and 31. Input: {day}")
    if (month == 9 or month == 11) and day == 31:
        raise ValueError(f"this month, the day must be between 1 and 30. Input: {day}")
    this_year_g = datetime.today().year
    this_year_j = jdate.today().year
    this_year_h = this_year_j + 43
    leap_year_g = (year % 4) == 0
    leap_year_j = (year % 4) == 3
    leap_year_h = (year % 30) in [2, 5, 7, 10, 13, 16, 18, 21, 24, 26, 29]
    if month == 2 and day == 30:
        return 'jalali'
    if (month == 2 or month == 4 or month == 6) and day == 31:
        return 'jalali'
    if (month == 7 or month == 8 or month == 10 or month == 12) and day == 31:
        return 'gregorian'

    # ====================================
    # Step 2: Validation in every calendar
    # ====================================
    gregorian = True
    hijri = True
    jalali = _is_valid_jalali(year, month, day)

    if month == 2 and not(leap_year_g) and day > 28:
        gregorian = False

    if 1342 < year < 1501:
        hijri = _is_valid_hijri(year, month, day)
    else:
        if (month == 1 or month == 3 or month == 5) and day > 30:
            hijri = False
        if (month == 4 or month == 8 or month == 10 or month == 11) and day > 29:
            hijri = False
        if month == 12 and not(leap_year_h) and day > 29:
            hijri = False

    # =============================================================================
    # Step 3: Detect based on reasonable year ranges with priority of smaller range
    # =============================================================================
    if gregorian and not(hijri) and not(jalali):
        return 'gregorian'
    if not(gregorian) and hijri and not(jalali):
        return 'hijri'
    if not(gregorian) and not(hijri) and jalali:
        return 'jalali'
    if gregorian and hijri and jalali:
        if abs(this_year_g - year) <= abs(this_year_h - year):
            logger.debug("thus difference between input year with gregorian this year is smaller than others, it probably is gregorian")
            return 'gregorian'
        if abs(this_year_g - year) > abs(this_year_h - year) and abs(this_year_j - year) > abs(this_year_h - year):
            logger.debug("thus difference between input year with hijri this year is smaller than others, it probably is hijri")
            return 'hijri'
        if abs(this_year_j - year) <= abs(this_year_h - year):
            logger.debug("thus difference between input year with jalali this year is smaller than others, it probably is jalali")
            return 'jalali'
    if gregorian and hijri and not (jalali):
        if abs(this_year_g - year) <= abs(this_year_h - year):
            logger.debug("thus difference between input year with gregorian this year is smaller than others, it probably is gregorian")
            return 'gregorian'
        else:
            logger.debug("thus difference between input year with hijri this year is smaller than others, it probably is hijri")
            return 'hijri'
    if gregorian and not(hijri) and jalali:
        if abs(this_year_g - year) <= abs(this_year_j - year):
            logger.debug("thus difference between input year with gregorian this year is smaller than others, it probably is gregorian")
            return 'gregorian'
        else:
            logger.debug("thus difference between input year with jalali this year is smaller than others, it probably is jalali")
            return 'jalali'
    if not(gregorian) and hijri and jalali:
        if abs(this_year_j - year) <= abs(this_year_h - year):
            logger.debug("thus difference between input year with jalali this year is smaller than others, it probably is jalali")
            return 'jalali'
        else:
            return 'hijri'
    if not(gregorian) and not(hijri) and not(jalali):
        raise ValueError(f"you have given a date that does not exist. Input: {date_str}")

def _is_valid_jalali(year: int, month: int, day: int) -> bool:
    """
    Check if Jalali date is valid
    """
    try:
        jdate(year, month, day)
        return True
    except (ValueError, ImportError):
        return False


def _is_valid_hijri(year: int, month: int, day: int) -> bool:
    """
    Check if Hijri date is valid
    """
    try:
        from hijri_converter import Hijri
        Hijri(year, month, day)
        return True
    except (ValueError, OverflowError, ImportError):
        return False

def validate_and_normalize_date(date_str: str, calendar_type: str = None):
    """
    Helper function to validate and normalize date

    If calendar_type is specified, only validate that calendar
    If not specified, detect first
    """

    # If calendar type is specified, just validate
    if calendar_type:
        if calendar_type not in ['jalali', 'gregorian', 'hijri']:
            raise ValueError(f"Invalid calendar type: {calendar_type}")

        if calendar_type == 'gregorian':
            # Validate Gregorian
            try:
                from datetime import datetime
                datetime.strptime(date_str, '%Y-%m-%d')
                return calendar_type
            except ValueError:
                raise ValueError(f"Invalid Gregorian date: {date_str}")

        elif calendar_type == 'jalali':
            # Validate Jalali
            parts = date_str.split('/')
            if len(parts) != 3:
                raise ValueError(f"Jalali date format must be YYYY/MM/DD")
            y, m, d = int(parts[0]), int(parts[1]), int(parts[2])
            if not _is_valid_jalali(y, m, d):
                raise ValueError(f"Invalid Jalali date: {date_str}")
            return calendar_type

        elif calendar_type == 'hijri':
            # Validate Hijri
            parts = date_str.split('/')
            if len(parts) != 3:
                raise ValueError(f"Hijri date format must be YYYY/MM/DD")
            y, m, d = int(parts[0]), int(parts[1]), int(parts[2])
            if not _is_valid_hijri(y, m, d):
                raise ValueError(f"Invalid Hijri date: {date_str}")
            return calendar_type

    # If calendar type not specified, detect
    return detect_calendar_type(date_str)


# ============================================================
# Test section (run directly with python core/detector.py)
# ============================================================

if __name__ == "__main__":
    # Sample test cases
    test_cases = [
        ("1402/10/11", "jalali"),  # Normal Jalali
        ("1360/10/01", "jalali"),  # Jalali - priority to Jalali
        ("2024-01-01", "gregorian"),  # Gregorian
        ("1445/01/01", "hijri"),  # Hijri
        ("1406/10/01", "hijri"),  # According to rule: >1405 -> Hijri
        ("1405/10/01", "jalali"),  # 1405 -> priority to Jalali
        ("1950/10/01", None),  # '/' format but Gregorian year - will error
    ]

    print("=" * 50)
    print("Calendar Type Detection Tests")
    print("=" * 50)

    for date_str, expected in test_cases:
        try:
            result = detect_calendar_type(date_str)
            status = "✓" if result == expected or expected is None else "✗"
            print(f"{status} Input: {date_str:15} -> Detected: {result:10} (Expected: {expected})")
        except ValueError as e:
            print(f"✗ Input: {date_str:15} -> Error: {str(e)[:50]}...")

    print("\n" + "=" * 50)
    print("Ambiguous Cases Tests")
    print("=" * 50)

    # Ambiguous cases
    ambiguous_cases = [
        "1400/01/01",  # Year 1400 -> priority Jalali
        "1404/12/29",  # Year 1404 -> Jalali
        "1406/01/01",  # Year 1406 -> Hijri (by rule)
        "1410/05/15",  # Year 1410 -> Hijri
    ]

    for date_str in ambiguous_cases:
        try:
            result = detect_calendar_type(date_str)
            print(f"Input: {date_str:15} -> Detected: {result}")
        except ValueError as e:
            print(f"Input: {date_str:15} -> Error: {e}")