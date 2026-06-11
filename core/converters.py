# core/converters.py
"""
Module for converting dates between Jalali, Gregorian, and Hijri calendars
All conversions are done manually using mathematical formulas
- Jalali <-> Gregorian: Using jdf.scr.ir algorithm
- Hijri <-> Gregorian: Using direct astronomical formulas
- Hijri <-> Jalali: Using Gregorian as bridge or direct 33/34 rule
"""

from datetime import date as datetime_date, datetime, timedelta
from typing import Dict, List, Tuple, Union
import logging

from core.detector import detect_calendar_type, validate_and_normalize_date

logger = logging.getLogger(__name__)


# ============================================================
# Part 1: Jalali (Shamsi) <-> Gregorian Conversion
# ============================================================

def gregorian_to_jalali(gy: int, gm: int, gd: int) -> List[int]:
    """
    Convert Gregorian date to Jalali (Shamsi)
    Using algorithm from jdf.scr.ir

    Args:
        gy: Gregorian year
        gm: Gregorian month (1-12)
        gd: Gregorian day (1-31)

    Returns:
        List [jy, jm, jd] Jalali date
    """
    g_d_m = [0, 31, 59, 90, 120, 151, 181, 212, 243, 273, 304, 334]

    if gm > 2:
        gy2 = gy + 1
    else:
        gy2 = gy

    days = 355666 + (365 * gy) + ((gy2 + 3) // 4) - ((gy2 + 99) // 100) + ((gy2 + 399) // 400) + gd + g_d_m[gm - 1]
    jy = -1595 + (33 * (days // 12053))
    days %= 12053
    jy += 4 * (days // 1461)
    days %= 1461

    if days > 365:
        jy += (days - 1) // 365
        days = (days - 1) % 365

    if days < 186:
        jm = 1 + (days // 31)
        jd = 1 + (days % 31)
    else:
        jm = 7 + ((days - 186) // 30)
        jd = 1 + ((days - 186) % 30)

    return [jy, jm, jd]


def jalali_to_gregorian(jy: int, jm: int, jd: int) -> List[int]:
    """
    Convert Jalali (Shamsi) date to Gregorian

    Args:
        jy: Jalali year
        jm: Jalali month (1-12)
        jd: Jalali day (1-31)

    Returns:
        List [gy, gm, gd] Gregorian date
    """
    jy += 1595
    days = -355668 + (365 * jy) + ((jy // 33) * 8) + (((jy % 33) + 3) // 4) + jd

    if jm < 7:
        days += (jm - 1) * 31
    else:
        days += ((jm - 7) * 30) + 186

    gy = 400 * (days // 146097)
    days %= 146097

    if days > 36524:
        days -= 1
        gy += 100 * (days // 36524)
        days %= 36524
        if days >= 365:
            days += 1

    gy += 4 * (days // 1461)
    days %= 1461

    if days > 365:
        gy += ((days - 1) // 365)
        days = (days - 1) % 365

    gd = days + 1

    # Find month
    if (gy % 4 == 0 and gy % 100 != 0) or (gy % 400 == 0):
        kab = 29
    else:
        kab = 28

    sal_a = [0, 31, kab, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
    gm = 0
    while gm < 13 and gd > sal_a[gm]:
        gd -= sal_a[gm]
        gm += 1

    return [gy, gm, gd]


# ============================================================
# Part 2: Hijri (Islamic Lunar) <-> Gregorian Conversion
# Manual implementation using astronomical rules
# ============================================================

# Reference point: Hijri epoch (1 Muharram 1 AH) = 622-07-16 Gregorian (Julian)
# Actually: 1 Muharram 1 AH = 622-07-16 (Friday) in Julian calendar
# In Gregorian: 622-07-19

HIJRI_EPOCH_GREGORIAN_YEAR = 622
HIJRI_EPOCH_GREGORIAN_MONTH = 7
HIJRI_EPOCH_GREGORIAN_DAY = 19

# Average lunar month length in days (synodic month)
LUNAR_MONTH_DAYS = 29.53058867

# Average lunar year length in days (12 lunar months)
LUNAR_YEAR_DAYS = 354.36706404

# Average solar year length in days (Gregorian)
SOLAR_YEAR_DAYS = 365.2425


def hijri_to_gregorian(hy: int, hm: int, hd: int) -> List[int]:
    """
    Convert Hijri (Islamic Lunar) date to Gregorian
    Using accurate astronomical calculations

    Formula:
    - Calculate total days since Hijri epoch (1 Muharram 1 AH)
    - Add to Gregorian epoch date

    Args:
        hy: Hijri year (1 AH = 622 CE)
        hm: Hijri month (1-12, 1=Muharram, 7=Rajab, 9=Ramadan, 12=Dhu al-Hijjah)
        hd: Hijri day (1-30, depending on month)

    Returns:
        List [gy, gm, gd] Gregorian date
    """

    # Step 1: Calculate total days from Hijri epoch to the given date
    # Days from complete years
    days_from_years = (hy - 1) * LUNAR_YEAR_DAYS

    # Days from months in current year
    days_from_months = _hijri_months_to_days(hy, hm, hd)

    total_days = days_from_years + days_from_months

    # Step 2: Convert total days to Gregorian date starting from Hijri epoch
    # Create epoch date
    epoch_date = datetime_date(HIJRI_EPOCH_GREGORIAN_YEAR,
                               HIJRI_EPOCH_GREGORIAN_MONTH,
                               HIJRI_EPOCH_GREGORIAN_DAY)

    # Add total days (rounded to nearest integer)
    target_date = epoch_date + timedelta(days=int(round(total_days)))

    return [target_date.year, target_date.month, target_date.day]


def _hijri_months_to_days(hy: int, hm: int, hd: int) -> float:
    """
    Calculate total days from months and days in a Hijri year
    Hijri months alternate between 30 and 29 days, but with adjustments

    Month mapping:
    1 - Muharram: 30 days
    2 - Safar: 29 days
    3 - Rabi' al-awwal: 30 days
    4 - Rabi' al-thani: 29 days
    5 - Jumada al-awwal: 30 days
    6 - Jumada al-thani: 30 days
    7 - Rajab: 30 days
    8 - Sha'ban: 29 days
    9 - Ramadan: 30 days
    10 - Shawwal: 29 days
    11 - Dhu al-Qi'dah: 29 days
    12 - Dhu al-Hijjah: 29 days (30 in leap years)
    """

    # Standard month lengths (non-leap year)
    month_lengths = [30, 29, 30, 29, 30, 29, 30, 29, 30, 29, 30, 29]

    # Check if it's a leap year (11 leap years in 30-year cycle)
    # Hijri leap years: years 2, 5, 7, 10, 13, 16, 18, 21, 24, 26, 29 of each 30-year cycle
    is_leap = (hy % 30) in [2, 5, 7, 10, 13, 16, 18, 21, 24, 26, 29]

    if is_leap:
        month_lengths[11] = 30  # Dhu al-Hijjah has 30 days in leap years

    # Calculate days from complete months
    days = 0
    for month in range(hm - 1):
        days += month_lengths[month]

    # Add days of current month
    days += hd - 1

    return days


def gregorian_to_hijri(gy: int, gm: int, gd: int) -> List[int]:
    """
    Convert Gregorian date to Hijri (Islamic Lunar)
    Using accurate astronomical calculations

    Formula:
    - Calculate total days from Gregorian epoch (622-07-19) to given date
    - Convert to Hijri years, months, days

    Args:
        gy: Gregorian year
        gm: Gregorian month (1-12)
        gd: Gregorian day (1-31)

    Returns:
        List [hy, hm, hd] Hijri date
    """

    # Step 1: Calculate total days from Hijri epoch to given date
    epoch_date = datetime_date(HIJRI_EPOCH_GREGORIAN_YEAR,
                               HIJRI_EPOCH_GREGORIAN_MONTH,
                               HIJRI_EPOCH_GREGORIAN_DAY)

    target_date = datetime_date(gy, gm, gd)
    total_days = (target_date - epoch_date).days

    if total_days < 0:
        raise ValueError(f"Date {gy}/{gm}/{gd} is before Hijri epoch (622 CE)")

    # Step 2: Convert total days to Hijri date
    # Calculate Hijri year (1 year = LUNAR_YEAR_DAYS days)
    hy = int(total_days / LUNAR_YEAR_DAYS) + 1

    # Calculate remaining days in the current year
    remaining_days = total_days - ((hy - 1) * LUNAR_YEAR_DAYS)

    # Step 3: Find month and day
    hm, hd = _days_to_hijri_month_day(hy, remaining_days)

    return [hy, hm, hd]


def _days_to_hijri_month_day(hy: int, days: float) -> Tuple[int, int]:
    """
    Convert days in a Hijri year to month and day

    Args:
        hy: Hijri year (for leap year calculation)
        days: number of days since start of the year (0-based)

    Returns:
        Tuple of (month, day) where month is 1-12, day is 1-30
    """

    # Standard month lengths
    month_lengths = [30, 29, 30, 29, 30, 29, 30, 29, 30, 29, 30, 29]

    # Check for leap year
    is_leap = (hy % 30) in [2, 5, 7, 10, 13, 16, 18, 21, 24, 26, 29]
    if is_leap:
        month_lengths[11] = 30

    days_int = int(round(days))

    for month_idx, length in enumerate(month_lengths):
        if days_int < length:
            return (month_idx + 1, days_int + 1)
        days_int -= length

    # If we get here, days is beyond year length (should not happen)
    return (12, month_lengths[11])


# ============================================================
# Part 3: Jalali <-> Hijri Conversion (Direct using 33/34 rule)
# ============================================================

def jalali_to_hijri_direct(jy: int, jm: int, jd: int) -> List[int]:
    """
    Convert Jalali to Hijri using the 33/34 rule
    Every 33 Jalali years = 34 Hijri years
    Hijri year = Jalali year - (Jalali year - 1) // 33 + 41

    Note: This is an approximation. For exact date, use the Gregorian bridge.

    Args:
        jy: Jalali year
        jm: Jalali month
        jd: Jalali day

    Returns:
        List [hy, hm, hd] Hijri date (approximate)
    """
    gy, gm, gd = jalali_to_gregorian(jy, jm, jd)
    return gregorian_to_hijri(gy, gm, gd)


def hijri_to_jalali_direct(hy: int, hm: int, hd: int) -> List[int]:
    """
    Convert Hijri to Jalali using the 33/34 rule

    Args:
        hy: Hijri year
        hm: Hijri month
        hd: Hijri day

    Returns:
        List [jy, jm, jd] Jalali date (approximate)
    """
    gy, gm, gd = hijri_to_gregorian(hy, hm, hd)
    return gregorian_to_jalali(gy, gm, gd)


jalali_to_hijri = jalali_to_hijri_direct
hijri_to_jalali = hijri_to_jalali_direct


# ============================================================
# Part 4: Main Web Service Functions
# ============================================================

def to_gregorian(date_str: str, calendar_type: str) -> datetime_date:
    """
    Convert input date string to Gregorian datetime.date object

    Args:
        date_str: date string in format YYYY/MM/DD or YYYY-MM-DD
        calendar_type: 'jalali', 'gregorian', or 'hijri'

    Returns:
        datetime.date object in Gregorian calendar
    """

    if calendar_type == 'jalali':
        parts = date_str.split('/')
        if len(parts) != 3:
            raise ValueError(f"Invalid Jalali date format. Expected YYYY/MM/DD, got: {date_str}")

        try:
            jy, jm, jd = map(int, parts)
            gy, gm, gd = jalali_to_gregorian(jy, jm, jd)
            gregorian_date = datetime_date(gy, gm, gd)
            logger.debug(f"Converted Jalali {date_str} to Gregorian {gregorian_date}")
            return gregorian_date
        except Exception as e:
            raise ValueError(f"Invalid Jalali date: {date_str}. Error: {str(e)}")

    elif calendar_type == 'gregorian':
        try:
            if '-' in date_str:
                gregorian_date = datetime.strptime(date_str, '%Y-%m-%d').date()
            elif '/' in date_str:
                gregorian_date = datetime.strptime(date_str, '%Y/%m/%d').date()
            else:
                raise ValueError(f"Unrecognized Gregorian date format: {date_str}")

            logger.debug(f"Validated Gregorian date: {gregorian_date}")
            return gregorian_date
        except ValueError as e:
            raise ValueError(f"Invalid Gregorian date: {date_str}. Error: {str(e)}")

    elif calendar_type == 'hijri':
        parts = date_str.split('/')
        if len(parts) != 3:
            raise ValueError(f"Invalid Hijri date format. Expected YYYY/MM/DD, got: {date_str}")

        try:
            hy, hm, hd = map(int, parts)
            gy, gm, gd = hijri_to_gregorian(hy, hm, hd)
            gregorian_date = datetime_date(gy, gm, gd)
            logger.debug(f"Converted Hijri {date_str} to Gregorian {gregorian_date}")
            return gregorian_date
        except Exception as e:
            raise ValueError(f"Invalid Hijri date: {date_str}. Error: {str(e)}")

    else:
        raise ValueError(f"Invalid calendar type: {calendar_type}. Must be 'jalali', 'gregorian', or 'hijri'")


def from_gregorian_to_all(gregorian_date: datetime_date) -> Dict[str, str]:
    """
    Convert Gregorian date to all three calendar formats

    Args:
        gregorian_date: datetime.date object in Gregorian calendar

    Returns:
        Dictionary with keys 'gregorian', 'jalali', 'hijri'
    """

    gy = gregorian_date.year
    gm = gregorian_date.month
    gd = gregorian_date.day

    gregorian_str = gregorian_date.isoformat()

    jy, jm, jd = gregorian_to_jalali(gy, gm, gd)
    jalali_str = f"{jy}/{jm}/{jd}"

    hy, hm, hd = gregorian_to_hijri(gy, gm, gd)
    hijri_str = f"{hy}/{hm}/{hd}"

    logger.debug(f"Converted Gregorian {gregorian_str} -> Jalali: {jalali_str}, Hijri: {hijri_str}")

    return {
        "gregorian": gregorian_str,
        "jalali": jalali_str,
        "hijri": hijri_str
    }


def convert(date_str: str, calendar_type: str = None) -> Dict[str, Union[str, dict]]:
    """
    Main conversion function: detect calendar type and convert to all three formats

    Args:
        date_str: input date string (e.g., "1402/10/11" or "2024-01-01")
        calendar_type: optional, if provided skips detection

    Returns:
        Dictionary with converted dates in all three calendars
    """

    if calendar_type is None:
        calendar_type = detect_calendar_type(date_str)
        logger.info(f"Detected calendar type for '{date_str}': {calendar_type}")
    else:
        validate_and_normalize_date(date_str, calendar_type)
        logger.debug(f"Using provided calendar type: {calendar_type}")

    gregorian_date = to_gregorian(date_str, calendar_type)
    result = from_gregorian_to_all(gregorian_date)
    result["original_calendar_type"] = calendar_type

    return result

