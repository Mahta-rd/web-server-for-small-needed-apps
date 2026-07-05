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
IRAN_PLATE_NUMBER_FILE = os.path.join(BASE_DIR, 'data', 'plate_number.xlsx')

def _get_city_name(plate_number: str) -> dict:
    """
    Get city and town name from 2 digits and the letter of plate number

    Args:
        plate_number: plate number string

    Returns:
        city and town name or empty string if not found
    """
    num = int(str(plate_number)[len(str(plate_number)) - 2:])
    letter = str(plate_number)[2]
    try:
        # wb = openpyxl.load_workbook(IRAN_PLATE_NUMBER_FILE, read_only=True, data_only=True)
        # ws = wb.active

        rows = execute_query('SELECT * FROM tPlate')
        for row in rows:
            if row[4] and row[2] and int(row[2]) == num and letter == 'ت':
                city = get_name_from_code(str(row[4]))
                # wb.close()
                return {
                    'city': city['city'],
                    'section': city['section'],
                    'county': city['county'],
                    'state': city['state'],
                    'city_code': str(row[4]),
                    'type': 'taxi'
                }
            if row[4] and row[2] and int(row[2]) == num and letter == 'ع':
                city = get_name_from_code(str(row[4]))
                # wb.close()
                return {
                    'city': city['city'],
                    'section': city['section'],
                    'county': city['county'],
                    'state': city['state'],
                    'city_code': str(row[4]),
                    'type': 'public transportation'
                }
            if row[4] and row[2] and int(row[2]) == num and letter == 'ک':
                city = get_name_from_code(str(row[4]))
                # wb.close()
                return {
                    'city': city['city'],
                    'section': city['section'],
                    'county': city['county'],
                    'state': city['state'],
                    'city_code': str(row[4]),
                    'type': 'farming'
                }
            if row[4] and row[2] and int(row[2]) == num and letter == 'الف':
                city = get_name_from_code(str(row[4]))
                # wb.close()
                return {
                    'city': city['city'],
                    'section': city['section'],
                    'county': city['county'],
                    'state': city['state'],
                    'city_code': str(row[4]),
                    'type': 'goverment'
                }
            if row[4] and row[2] and int(row[2]) == num and letter == 'گ':
                city = get_name_from_code(str(row[4]))
                # wb.close()
                return {
                    'city': city['city'],
                    'section': city['section'],
                    'county': city['county'],
                    'state': city['state'],
                    'city_code': str(row[4]),
                    'type': 'temporary passage'
                }
            if row[4] and row[2] and int(row[2]) == num and letter in ['پ', 'ش', 'ث', 'ف', 'ز']:
                city = get_name_from_code(str(row[4]))
                # wb.close()
                return {
                    'city': city['city'],
                    'section': city['section'],
                    'county': city['county'],
                    'state': city['state'],
                    'city_code': str(row[4]),
                    'type': 'police and military'
                }
            if row[4] and row[2] and int(row[2]) == num and letter in ['S', 'D']:
                city = get_name_from_code(str(row[4]))
                # wb.close()
                return {
                    'city': city['city'],
                    'section': city['section'],
                    'county': city['county'],
                    'state': city['state'],
                    'city_code': str(row[4]),
                    'type': 'Diplomat and politician'
                }
            if row[4] and row[2] and row[3] and int(row[2]) == num and row[3] == '*':
                city = get_name_from_code(str(row[4]))
                # wb.close()
                return {
                    'city': city['city'],
                    'section': city['section'],
                    'county': city['county'],
                    'state': city['state'],
                    'city_code': str(row[4]),
                    'type': 'personal'
                }
            if row[4] and row[2] and row[3] and int(row[2]) == num and row[3] == letter:
                city = get_name_from_code(str(row[4]))
                # wb.close()
                return {
                    'city': city['city'],
                    'section': city['section'],
                    'county': city['county'],
                    'state': city['state'],
                    'city_code': str(row[4]),
                    'type': 'personal'
                }
        # wb.close()
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
    cleaned = ''.join(re.findall(r"[آابپتثجچحخدذرزژسشصضطظعغفقکگلمنوهیئSD|0-9]+", str(plate_number)))
    if len(cleaned) != 8:
        raise ValueError("plate number length is incorrect!")
    if not bool(re.search(r"[0-9]{2}[SDآابپتثجچحخدذرزژسشصضطظعغفقکگلمنوهیئ]{1}[0-9]{5}", cleaned)):
        raise ValueError("The plate number format is incorrect!")
    name = _get_city_name(str(cleaned))
    if not name:
        raise ValueError("City not found for this plate number")
    return {
        'plate_number': str(cleaned),
        'city': name['city'],
        'section': name['section'],
        'county': name['county'],
        'state': name['state'],
        'city_code': name['city_code'],
        'type': name['type']
    }

def get_plate(code: str) -> list:
    """
    Get plate number for a city with city code

    Args:
        code: 8-digit

    Returns:
        plate number in that region
    """
    
    try:
        # wb = openpyxl.load_workbook(IRAN_PLATE_NUMBER_FILE, read_only=True, data_only=True)
        # ws = wb.active
        plate = []
        rows = execute_query('SELECT * FROM tPlate')
        for row in rows:
            if row[4] and int(row[4]) == int(str(code)):
                    plate.append((str(row[2]), str(row[3])))

        # wb.close()
    except Exception as e:
        raise ValueError(f"Error reading code city data file: {str(e)}")

    return plate