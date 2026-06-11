import numpy as np
import re
import openpyxl
import os

BASE_DIR = os.path.dirname(__file__)
IRAN_POSTAL_CODE_FILE = os.path.join(BASE_DIR, 'data', 'postal_code.xlsx')

def _get_city_name(postal_code: str) -> str:
    """
    Get city and region name from first 5 digits of postal code number

    Args:
        postal_code: 10-digit code number

    Returns:
        city and region name or empty string if not found
    """
    code = postal_code[:5]

    try:
        wb = openpyxl.load_workbook(IRAN_POSTAL_CODE_FILE, read_only=True, data_only=True)
        ws = wb.active

        for row in ws.iter_rows(min_row=2, values_only=True):
            if row[2] and row[3] and min(int(row[2]), int(row[3])) <= int(code) <= max(int(row[2]), int(row[3])):
                wb.close()
                return {
                    'city': re.sub(r'\xa0', '', row[0]),
                    'region': row[1]
                }

        wb.close()
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
    cleaned = ''.join(re.findall(r"[0-9]+", postal_code))
    if len(cleaned) != 10:
        raise ValueError("postal code number length is incorrect!")
    if bool(re.search(r"[2|0]+", cleaned[:5])):
        raise ValueError("There should not be 0 or 2 in 5 first numbers!")
    name = _get_city_name(cleaned)
    if not name:
        raise ValueError("City not found for this postal code number")
    return {
        'postal_code': cleaned,
        'city': name['city'],
        'region': name['region']
    }

print(postal_filter("13456-78902"))