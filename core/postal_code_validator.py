import sqlite3
import numpy as np
import re
import openpyxl
import os

from core.connect import execute_query, get_db_connection
from core.iran_city import get_name_from_code

con = sqlite3.connect('database.db')
cursorObj = con.cursor()
BASE_DIR = os.path.dirname(__file__)
IRAN_POSTAL_CODE_FILE = os.path.join(BASE_DIR, 'data', 'postal_code.xlsx')

def _get_city_name(postal_code: str) -> dict:
    """
    Get city and region name from first 5 digits of postal code number

    Args:
        postal_code: 10-digit code number

    Returns:
        city and region name or empty string if not found
    """
    code = str(postal_code)[:5]

    try:
        # wb = openpyxl.load_workbook(IRAN_POSTAL_CODE_FILE, read_only=True, data_only=True)
        # ws = wb.active

        rows = execute_query('SELECT * FROM tPostal')
        for row in rows:
            if row[2] and row[3] and min(int(row[2]), int(row[3])) <= int(code) <= max(int(row[2]), int(row[3])):
                # wb.close()
                city = get_name_from_code(str(row[4]))
                return {
                    'city': city['city'],
                    'section': city['section'],
                    'county': city['county'],
                    'state': city['state'],
                    'city_code': str(row[4])
                }

        # wb.close()
    except Exception as e:
        raise ValueError(f"Error reading code city data file: {str(e)}")

    return ""

def postal_filter(postal_code: str) -> dict:
    """
    Validate Iranian postal code and return city information

    Args:
        postal_code: postal code number string (can contain spaces, dashes, etc.)

    Returns:
        Dictionary with postal code number with city and region name

    Raises:
        ValueError: If code number is invalid
    """
    cleaned = ''.join(re.findall(r"[0-9]+", str(postal_code)))
    if len(cleaned) != 10:
        raise ValueError("postal code number length is incorrect!")
    if bool(re.search(r"[2|0]+", cleaned[:5])):
        raise ValueError("There should not be 0 or 2 in 5 first numbers!")
    name = _get_city_name(str(cleaned))
    if not name:
        raise ValueError("City not found for this postal code number")
    return {
        'postal_code': str(cleaned),
        'city': name['city'],
        'section': name['section'],
        'county': name['county'],
        'state': name['state'],
        'city_code': name['city_code']
    }

def get_postal(code: str) -> list:
    """
    Get postal code for a city with city code

    Args:
        code: 8-digit

    Returns:
        postal code in that region
    """
    
    try:
        # wb = openpyxl.load_workbook(IRAN_POSTAL_CODE_FILE, read_only=True, data_only=True)
        # ws = wb.active
        postal = []
        rows = execute_query('SELECT * FROM tPostal')
        for row in rows:
            if row[4] and int(row[4]) == int(str(code)):
                    postal.append((str(row[2]), str(row[3])))

        # wb.close()
    except Exception as e:
        raise ValueError(f"Error reading code city data file: {str(e)}")

    return postal