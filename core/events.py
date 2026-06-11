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
import openpyxl

from core.converters import convert, gregorian_to_jalali, gregorian_to_hijri
from core.detector import detect_calendar_type

logger = logging.getLogger(__name__)

NAMES_FILE_PATH = os.path.join(os.path.dirname(__file__), 'data', 'weekday_name.json')
EVENTS_FILE_PATH = os.path.join(os.path.dirname(__file__), 'data', 'events.xlsx')

def _load_name_data() -> Dict:
    """
    Load events data from JSON file

    Returns:
        Dictionary containing months, weekdays data
    """
    try:
        with open(NAMES_FILE_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        logger.error(f"Weekday name file not found at {NAMES_FILE_PATH}")
        raise FileNotFoundError(f"Weekday name data file not found: {NAMES_FILE_PATH}")
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in events file: {e}")
        raise ValueError(f"Invalid JSON format in events file: {e}")


_NAME_DATA = _load_name_data()


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
    months = _NAME_DATA.get('months', {}).get(calendar_type, {})
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
    weekdays = _NAME_DATA.get('weekdays', {}).get(calendar_type, {})

    if calendar_type == 'gregorian':
        weekday_index = date_obj.weekday()
    elif calendar_type == 'jalali':
        from jdatetime import date as jdate
        jalali_date = jdate.fromgregorian(date=date_obj)
        weekday_index = jalali_date.weekday()
    elif calendar_type == 'hijri':
        weekday_index = date_obj.weekday()
    else:
        raise ValueError(f"Invalid calendar type: {calendar_type}")

    day_name = weekdays.get(str(weekday_index))

    if not day_name:
        logger.warning(f"Day name not found for {calendar_type}/{weekday_index}")
        return f"Unknown Day {weekday_index}"

    return day_name

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
    conversion_result = convert(date_str, calendar_type)

    events_result = {
        "jalali": [],
        "gregorian": [],
        "hijri": []
    }

    jalali_str = conversion_result["jalali"]
    jy, jm, jd = map(int, jalali_str.split('/'))

    gregorian_str = conversion_result["gregorian"]
    gy, gm, gd = map(int, gregorian_str.split('-'))

    hijri_str = conversion_result["hijri"]
    hy, hm, hd = map(int, hijri_str.split('/'))
    try:
        wb = openpyxl.load_workbook(EVENTS_FILE_PATH, read_only=True, data_only=True)
        ws = wb.active

        for row in ws.iter_rows(min_row=2, values_only=True):
            if row[0] and row[0] == 'M':
                if int(row[1]) == int(gm) and int(row[2]) == int(gd):
                    events_result["gregorian"] = row[3].split("|")
            elif row[0] and row[0] == 'S':
                if int(row[1]) == int(jm) and int(row[2]) == int(jd):
                    events_result["jalali"] = row[3].split("|")
            else:
                if int(row[1]) == int(hm) and int(row[2]) == int(hd):
                    events_result["hijri"] = row[3].split("|")
        wb.close()
    except Exception as e:
        raise ValueError(f"Error reading events data file: {str(e)}")

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
    conversion_result = convert(date_str, calendar_type)

    gregorian_date = datetime_date.fromisoformat(conversion_result["gregorian"])

    jalali_parts = list(map(int, conversion_result["jalali"].split('/')))
    gregorian_parts = list(map(int, conversion_result["gregorian"].split('-')))
    hijri_parts = list(map(int, conversion_result["hijri"].split('/')))

    month_names = {
        "jalali": get_month_name(jalali_parts[0], jalali_parts[1], "jalali"),
        "gregorian": get_month_name(gregorian_parts[0], gregorian_parts[1], "gregorian"),
        "hijri": get_month_name(hijri_parts[0], hijri_parts[1], "hijri")
    }

    day_names = {
        "jalali": get_day_name(gregorian_date, "jalali"),
        "gregorian": get_day_name(gregorian_date, "gregorian"),
        "hijri": get_day_name(gregorian_date, "hijri")
    }

    events = get_events_for_date(date_str, calendar_type)

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
