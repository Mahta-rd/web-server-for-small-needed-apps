# core/events.py
"""
Module for retrieving events, month names, and day names for dates
Data is loaded from events.json file
"""

import json
import os
from datetime import date as datetime_date
from typing import Dict, List, Tuple, Optional
import logging

from core.converters import convert, gregorian_to_jalali, gregorian_to_hijri
from core.detector import detect_calendar_type

logger = logging.getLogger(__name__)

# Path to events.json file
EVENTS_FILE_PATH = os.path.join(os.path.dirname(__file__), 'data', 'events.json')


def _load_events_data() -> Dict:
    """
    Load events data from JSON file

    Returns:
        Dictionary containing months, weekdays, and events data
    """
    try:
        with open(EVENTS_FILE_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        logger.error(f"Events file not found at {EVENTS_FILE_PATH}")
        raise FileNotFoundError(f"Events data file not found: {EVENTS_FILE_PATH}")
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in events file: {e}")
        raise ValueError(f"Invalid JSON format in events file: {e}")


# Load data once at module level
_EVENTS_DATA = _load_events_data()


def get_month_name(year: int, month: int, calendar_type: str) -> str:
    """
    Get month name for a given date

    Args:
        year: Year in the specified calendar
        month: Month number (1-12)
        calendar_type: 'jalali', 'gregorian', or 'hijri'

    Returns:
        Month name as string
    """
    months = _EVENTS_DATA.get('months', {}).get(calendar_type, {})
    month_name = months.get(str(month))

    if not month_name:
        logger.warning(f"Month name not found for {calendar_type}/{month}")
        return f"Unknown Month {month}"

    return month_name


def get_day_name(date_obj: datetime_date, calendar_type: str) -> str:
    """
    Get day of week name for a given date

    Args:
        date_obj: datetime.date object in Gregorian calendar
        calendar_type: 'jalali', 'gregorian', or 'hijri' (for output)

    Returns:
        Day name as string
    """
    weekdays = _EVENTS_DATA.get('weekdays', {}).get(calendar_type, {})

    if calendar_type == 'gregorian':
        # Gregorian: Monday = 0, Sunday = 6
        weekday_index = date_obj.weekday()
    elif calendar_type == 'jalali':
        # Jalali: Saturday = 0, Friday = 6
        # Convert Gregorian weekday to Jalali weekday
        # Gregorian Monday (0) = Jalali Tuesday? Let's compute properly
        from jdatetime import date as jdate
        jalali_date = jdate.fromgregorian(date=date_obj)
        # In jdatetime, Monday = 0, Sunday = 6 (same as Gregorian)
        weekday_index = jalali_date.weekday()
    elif calendar_type == 'hijri':
        # Hijri: Use Gregorian weekday as approximation
        # Islamic calendar starts on Friday, but weekday names follow Gregorian
        weekday_index = date_obj.weekday()
    else:
        raise ValueError(f"Invalid calendar type: {calendar_type}")

    day_name = weekdays.get(str(weekday_index))

    if not day_name:
        logger.warning(f"Day name not found for {calendar_type}/{weekday_index}")
        return f"Unknown Day {weekday_index}"

    return day_name


def get_fixed_events(year: int, month: int, day: int, calendar_type: str) -> List[str]:
    """
    Get fixed events for a specific date in a calendar

    Fixed events are those that occur on the same date every year
    (e.g., Nowruz on 1/1 in Jalali, Christmas on 12/25 in Gregorian)

    Args:
        year: Year in the specified calendar
        month: Month number (1-12)
        day: Day number (1-31)
        calendar_type: 'jalali', 'gregorian', or 'hijri'

    Returns:
        List of event names
    """
    fixed_events = _EVENTS_DATA.get('fixed_events', {}).get(calendar_type, {})
    key = f"{month}-{day}"

    return fixed_events.get(key, [])


def get_events_for_date(date_str: str, calendar_type: str = None) -> Dict[str, List[str]]:
    """
    Get all events for a given date in all three calendars

    Args:
        date_str: Date string (e.g., "1402/10/11" or "2024-01-01")
        calendar_type: Optional, if provided uses this calendar type

    Returns:
        Dictionary with events for each calendar
        {
            "jalali": ["event1", "event2"],
            "gregorian": ["event1"],
            "hijri": []
        }
    """
    # First convert the date to get all three calendar representations
    conversion_result = convert(date_str, calendar_type)

    events_result = {
        "jalali": [],
        "gregorian": [],
        "hijri": []
    }

    # Parse Jalali date from conversion result
    jalali_str = conversion_result["jalali"]
    jy, jm, jd = map(int, jalali_str.split('/'))
    events_result["jalali"] = get_fixed_events(jy, jm, jd, "jalali")

    # Parse Gregorian date from conversion result
    gregorian_str = conversion_result["gregorian"]
    gy, gm, gd = map(int, gregorian_str.split('-'))
    events_result["gregorian"] = get_fixed_events(gy, gm, gd, "gregorian")

    # Parse Hijri date from conversion result
    hijri_str = conversion_result["hijri"]
    hy, hm, hd = map(int, hijri_str.split('/'))
    events_result["hijri"] = get_fixed_events(hy, hm, hd, "hijri")

    logger.debug(f"Events for {date_str}: {events_result}")

    return events_result


def get_full_info(date_str: str, calendar_type: str = None) -> Dict:
    """
    Get complete information for a date including:
    - Converted dates in all three calendars
    - Month names
    - Day names
    - Events

    Args:
        date_str: Date string (e.g., "1402/10/11" or "2024-01-01")
        calendar_type: Optional, if provided uses this calendar type

    Returns:
        Complete dictionary with all date information
    """
    # Get conversion results
    conversion_result = convert(date_str, calendar_type)

    # Get Gregorian date object for day name calculation
    gregorian_date = datetime_date.fromisoformat(conversion_result["gregorian"])

    # Parse dates for month name extraction
    jalali_parts = list(map(int, conversion_result["jalali"].split('/')))
    gregorian_parts = list(map(int, conversion_result["gregorian"].split('-')))
    hijri_parts = list(map(int, conversion_result["hijri"].split('/')))

    # Get month names
    month_names = {
        "jalali": get_month_name(jalali_parts[0], jalali_parts[1], "jalali"),
        "gregorian": get_month_name(gregorian_parts[0], gregorian_parts[1], "gregorian"),
        "hijri": get_month_name(hijri_parts[0], hijri_parts[1], "hijri")
    }

    # Get day names
    day_names = {
        "jalali": get_day_name(gregorian_date, "jalali"),
        "gregorian": get_day_name(gregorian_date, "gregorian"),
        "hijri": get_day_name(gregorian_date, "hijri")
    }

    # Get events
    events = get_events_for_date(date_str, calendar_type)

    # Build final result
    result = {
        "original_calendar_type": conversion_result["original_calendar_type"],
        "dates": {
            "jalali": conversion_result["jalali"],
            "gregorian": conversion_result["gregorian"],
            "hijri": conversion_result["hijri"]
        },
        "month_names": month_names,
        "day_names": day_names,
        "events": events
    }

    return result


# ============================================================
# Test section
# ============================================================

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    print("=" * 70)
    print("Testing Events Module")
    print("=" * 70)

    # Test 1: Get month names
    print("\n1. Testing Month Names:")
    print(f"   Jalali month 1: {get_month_name(1402, 1, 'jalali')}")
    print(f"   Gregorian month 1: {get_month_name(2024, 1, 'gregorian')}")
    print(f"   Hijri month 1: {get_month_name(1445, 1, 'hijri')}")

    # Test 2: Get day names
    print("\n2. Testing Day Names:")
    test_date = datetime_date(2024, 1, 1)
    print(f"   Gregorian 2024-01-01: {get_day_name(test_date, 'gregorian')}")
    print(f"   Jalali equivalent: {get_day_name(test_date, 'jalali')}")
    print(f"   Hijri equivalent: {get_day_name(test_date, 'hijri')}")

    # Test 3: Get fixed events
    print("\n3. Testing Fixed Events:")
    print(f"   Jalali 1/1 events: {get_fixed_events(1402, 1, 1, 'jalali')}")
    print(f"   Gregorian 12/25 events: {get_fixed_events(2024, 12, 25, 'gregorian')}")
    print(f"   Hijri 1/1 events: {get_fixed_events(1445, 1, 1, 'hijri')}")

    # Test 4: Get events for a specific date
    print("\n4. Testing Events for Date:")
    test_dates = [
        "1402/01/01",  # Nowruz
        "2024-12-25",  # Christmas
        "1445/01/01",  # Islamic New Year
        "1402/10/11",  # Normal day with no events
    ]

    for date_str in test_dates:
        print(f"\n   Date: {date_str}")
        events = get_events_for_date(date_str)
        print(f"     Jalali events: {events['jalali']}")
        print(f"     Gregorian events: {events['gregorian']}")
        print(f"     Hijri events: {events['hijri']}")

    # Test 5: Get full info
    print("\n" + "=" * 70)
    print("5. Testing Full Info")
    print("=" * 70)

    for date_str in test_dates:
        print(f"\nInput: {date_str}")
        try:
            info = get_full_info(date_str)
            print(f"  Original type: {info['original_calendar_type']}")
            print(f"  Dates: {info['dates']}")
            print(f"  Month names: {info['month_names']}")
            print(f"  Day names: {info['day_names']}")
            print(f"  Events: {info['events']}")
        except Exception as e:
            print(f"  ERROR: {e}")

    print("\n✓ All tests completed!")