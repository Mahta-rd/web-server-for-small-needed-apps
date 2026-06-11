import numpy as np
import re
import openpyxl
import os

BASE_DIR = os.path.dirname(__file__)
IRAN_PLATE_NUMBER_FILE = os.path.join(BASE_DIR, 'data', 'plate_number.xlsx')

def _get_city_name(plate_number: str) -> dict:
    """
    Get city and town name from 2 digits and the letter of plate number

    Args:
        plate_number: plate number string

    Returns:
        city and town name or empty string if not found
    """
    num = int(plate_number[len(plate_number) - 2:])
    letter = plate_number[2]
    try:
        wb = openpyxl.load_workbook(IRAN_PLATE_NUMBER_FILE, read_only=True, data_only=True)
        ws = wb.active

        for row in ws.iter_rows(min_row=2, values_only=True):
            if row[2] and int(row[2]) == num and letter == 'ت':
                wb.close()
                return {
                    'city': re.sub(r'\xa0', '', row[0]),
                    'region': row[1],
                    'type': 'taxi'
                }
            if row[2] and int(row[2]) == num and letter == 'ع':
                wb.close()
                return {
                    'city': re.sub(r'\xa0', '', row[0]),
                    'region': row[1],
                    'type': 'public transportation'
                }
            if row[2] and int(row[2]) == num and letter == 'ک':
                wb.close()
                return {
                    'city': re.sub(r'\xa0', '', row[0]),
                    'region': row[1],
                    'type': 'farming'
                }
            if row[2] and int(row[2]) == num and letter == 'الف':
                wb.close()
                return {
                    'city': re.sub(r'\xa0', '', row[0]),
                    'region': row[1],
                    'type': 'goverment'
                }
            if row[2] and int(row[2]) == num and letter == 'گ':
                wb.close()
                return {
                    'city': re.sub(r'\xa0', '', row[0]),
                    'region': row[1],
                    'type': 'temporary passage'
                }
            if row[2] and int(row[2]) == num and letter in ['پ', 'ش', 'ث', 'ف', 'ز']:
                wb.close()
                return {
                    'city': re.sub(r'\xa0', '', row[0]),
                    'region': row[1],
                    'type': 'police and military'
                }
            if row[2] and int(row[2]) == num and letter in ['S', 'D']:
                wb.close()
                return {
                    'city': re.sub(r'\xa0', '', row[0]),
                    'region': row[1],
                    'type': 'Diplomat and politician'
                }
            if row[2] and row[3] and int(row[2]) == num and row[3] == '*':
                wb.close()
                return {
                    'city': re.sub(r'\xa0', '', row[0]),
                    'region': row[1],
                    'type': 'personal'
                }
            if row[2] and row[3] and int(row[2]) == num and row[3] == letter:
                wb.close()
                return {
                    'city': re.sub(r'\xa0', '', row[0]),
                    'region': row[1],
                    'type': 'personal'
                }
        wb.close()
    except Exception as e:
        raise ValueError(f"Error reading plate number data file: {str(e)}")

    return ""

def plate_filter(plate_number: str) -> dict:
    """
    Validate Iranian plate number and return city information

    Args:
        plate_number: plate number string (can contain spaces, dashes, etc.)

    Returns:
        Dictionary with plate number with city and town name

    Raises:
        ValueError: If code number is invalid
    """
    cleaned = ''.join(re.findall(r"[آابپتثجچحخدذرزژسشصضطظعغفقکگلمنوهیئSD|0-9]+", plate_number))
    if len(cleaned) != 8:
        raise ValueError("plate number length is incorrect!")
    if not bool(re.search(r"[0-9]{2}[SDآابپتثجچحخدذرزژسشصضطظعغفقکگلمنوهیئ]{1}[0-9]{5}", cleaned)):
        raise ValueError("The plate number format is incorrect!")
    name = _get_city_name(cleaned)
    if not name:
        raise ValueError("City not found for this plate number")
    return {
        'plate_number': cleaned,
        'city': name['city'],
        'region': name['region'],
        'type': name['type']
    }

