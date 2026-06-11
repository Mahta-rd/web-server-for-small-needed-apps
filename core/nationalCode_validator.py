import numpy as np
import re
import openpyxl
import os

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
    nums = [int(national_code[i]) * (len(national_code) - i) for i in range(len(national_code))]
    number = np.array(nums[:len(national_code) - 1])
    sum = number.sum()
    remain = sum % 11
    if remain >= 2:
        control_num = 11 - remain
    else:
        control_num = remain
    return control_num == int(national_code[len(national_code) - 1])

def _get_city_name(national_code: str) -> str:
    """
    Get city and town name from first 3 digits of national code number

    Args:
        national_code: 10-digit code number

    Returns:
        city and town name or empty string if not found
    """
    code = national_code[:3]

    try:
        wb = openpyxl.load_workbook(IRAN_NATIONAL_CODE_FILE, read_only=True, data_only=True)
        ws = wb.active

        for row in ws.iter_rows(min_row=2, values_only=True):
            if row[0] and int(row[0]) == int(code):
                wb.close()
                return {
                    'city': row[2],
                    'town': row[1]
                }

        wb.close()
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
    cleaned = ''.join(re.findall(r"[0-9]+", national_code))
    if not 8 <= len(cleaned) < 11:
        raise ValueError("national code number length is incorrect!")
    if len(cleaned) < 10:
        cleaned = ("0"*(10 - len(cleaned))) + cleaned
    if not _validate_nationalCode(cleaned):
        raise ValueError("written national code number is incorrect!")
    name = _get_city_name(cleaned)
    if not name:
        raise ValueError("City not found for this national code number")
    return {
        'national_code': cleaned,
        'city': name['city'],
        'town': name['town'],
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
    number = np.array([int(national_code[i]) * coefficient[i] for i in range(10)])
    sum = number.sum() + 460
    remain = sum % 11
    if remain == 10:
        control_num = 0
    else:
        control_num = remain
    return control_num == int(national_code[len(national_code) - 1])

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
    cleaned = ''.join(re.findall(r"[0-9]+", national_code))
    if len(cleaned) != 11:
        raise ValueError("national code number length is incorrect!")
    if not _validate_nationalCode_company(cleaned):
        raise ValueError("written national code number is incorrect!")
    return {
        'national_code': cleaned,
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
    cleaned = ''.join(re.findall(r"[0-9]+", input_str))

    if len(cleaned) > 10:
        try:
            return filter_company(cleaned)
        except ValueError as e:
            pass

    try:
        return filter(cleaned)
    except ValueError as e:
        pass

    raise ValueError("Input is neither a valid bank card number nor a valid IBAN")

