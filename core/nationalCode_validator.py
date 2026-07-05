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
IRAN_NATIONAL_CODE_FILE = os.path.join(BASE_DIR, 'data', 'national_code_city.xlsx')

def _validate_nationalCode(national_code: str) -> bool:
    """
    Validate personal national code number

    Args:
        national_code: 10 digit code number as string

    Returns:
        True if valid, False otherwise
    """
    nums = [int(str(national_code)[i]) * (len(str(national_code)) - i) for i in range(len(str(national_code)))]
    number = np.array(nums[:len(str(national_code)) - 1])
    sum = number.sum()
    remain = sum % 11
    if remain >= 2:
        control_num = 11 - remain
    else:
        control_num = remain
    return control_num == int(str(national_code)[len(str(national_code)) - 1])

def _get_city_name(national_code: str) -> dict:
    """
    Get city and town name from first 3 digits of national code number

    Args:
        national_code: 10-digit code number

    Returns:
        city and town name or empty string if not found
    """
    code = str(national_code)[:3]

    try:
        # wb = openpyxl.load_workbook(IRAN_NATIONAL_CODE_FILE, read_only=True, data_only=True)
        # ws = wb.active

        rows = execute_query('SELECT * FROM tNational')
        for row in rows:
            if row[0] and int(row[0]) == int(code):
                # wb.close()
                city = get_name_from_code(str(row[3]))
                if not row[3]:
                    return {
                        'city': str(row[2]),
                        'town': str(row[1])
                }
                return {
                    'city': str(city['city']),
                    'section': str(city['section']),
                    'county': str(city['county']),
                    'state': str(city['state']),
                    'city_code': str(row[3])
                }
                
        # wb.close()
    except Exception as e:
        raise ValueError(f"Error reading code city data file: {str(e)}")

    return ""

def filter(national_code: str) -> dict:
    """
    Validate Iranian personal national code and return city information

    Args:
        national_code: national code number string (can contain spaces, dashes, etc.)

    Returns:
        Dictionary with national code number with city and town name

    Raises:
        ValueError: If code number is invalid
    """
    cleaned = ''.join(re.findall(r"[0-9]+", str(national_code)))
    if not 8 <= len(cleaned) < 11:
        raise ValueError("national code number length is incorrect!")
    if len(cleaned) < 10:
        cleaned = ("0"*(10 - len(cleaned))) + cleaned
    if not _validate_nationalCode(cleaned):
        raise ValueError("written national code number is incorrect!")
    name = _get_city_name(str(cleaned))
    if not name:
        raise ValueError("City not found for this national code number")
    if not name['county']:
        return {
        'national_code': str(cleaned),
        'city': name['city'],
        'town': name['town'],
        'type': 'Personal'
        }
    return {
        'national_code': str(cleaned),
        'city': name['city'],
        'section': name['section'],
        'county': name['county'],
        'state': name['state'],
        'city_code': name['city_code'],
        'type': 'Personal'
    }

def _validate_nationalCode_company(national_code: str) -> bool:
    """
    Validate company national code number

    Args:
        national_code: 11 digit code number as string

    Returns:
        True if valid, False otherwise
    """
    coefficient = np.array([29, 27, 23, 19, 17, 29, 27, 23, 19, 247]) 
    number = np.array([int(str(national_code)[i]) * coefficient[i] for i in range(10)])
    sum = number.sum() + 460
    remain = sum % 11
    if remain == 10:
        control_num = 0
    else:
        control_num = remain
    return control_num == int(str(national_code)[len(str(national_code)) - 1])

def filter_company(national_code: str) -> dict:
    """
    Validate Iranian company's national code and return city information

    Args:
        national_code: national code number string (can contain spaces, dashes, etc.)

    Returns:
        Dictionary with national code number with city and town name

    Raises:
        ValueError: If code number is invalid
    """
    cleaned = ''.join(re.findall(r"[0-9]+", str(national_code)))
    if len(cleaned) != 11:
        raise ValueError("national code number length is incorrect!")
    if not _validate_nationalCode_company(str(cleaned)):
        raise ValueError("written national code number is incorrect!")
    return {
        'national_code': str(cleaned),
        'type': 'Company'
    }

def check(input_str: str) -> dict:
    """
    Automatically detect whether input is Personal or Company national code
    and validate it

    Args:
        input_str: String containing national code

    Returns:
        Dictionary with validation results

    Raises:
        ValueError: If input is neither valid card nor valid IBAN
    """
    cleaned = ''.join(re.findall(r"[0-9]+", str(input_str)))

    if len(cleaned) > 10:
        try:
            return filter_company(str(cleaned))
        except ValueError as e:
            pass

    try:
        return filter(str(cleaned))
    except ValueError as e:
        pass

    raise ValueError("Input is neither a valid bank card number nor a valid IBAN")

def get_national_code(code: str) -> list:
    """
    Get national code for a city with city code

    Args:
        code: 8-digit

    Returns:
        national code in that region
    """
    
    try:
        # wb = openpyxl.load_workbook(IRAN_NATIONAL_CODE_FILE, read_only=True, data_only=True)
        # ws = wb.active
        national = []
        rows = execute_query('SELECT * FROM tNational')
        for row in rows:
            if row[3] and int(row[3]) == int(str(code)):
                    national.append(str(row[0]))

        # wb.close()
    except Exception as e:
        raise ValueError(f"Error reading code city data file: {str(e)}")

    return national