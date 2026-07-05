# app.py
from flask import Flask, request, jsonify
from core.events import get_full_info
from core.bank_validator import check_card_number, check_iban, detect_and_validate
from core.nationalCode_validator import check, filter, filter_company, get_national_code
from core.number_plate_validator import plate_filter, get_plate
from core.postal_code_validator import postal_filter, get_postal
from core.phone_number_validator import landline_phone_number_filter, mobile_phone_number_filter, phone_number_filter, get_phone_number, get_mobie_phone_number
from core.iran_city import get_information
import json
import re

app = Flask(__name__)
app.config['JSON_AS_ASCII'] = False


def custom_jsonify(data, status=200):
    """Custom jsonify that properly handles Persian/Arabic characters"""
    return app.response_class(
        response=json.dumps(data, ensure_ascii=False, indent=2),
        status=status,
        mimetype='application/json'
    )


# ============================================================
# Home Page
# ============================================================

@app.route('/')
def home():
    return custom_jsonify({
        "service": "Integrated API",
        "version": "2.0",
        "description": "Date Converter + Bank Card/IBAN Validator",
        "endpoints": {
            "/": "This help page",
            "/convert-date": "Convert dates between Jalali, Gregorian, and Hijri calendars",
            "/validate-card": "Validate bank card number and get bank name",
            "/validate-iban": "Validate Iranian IBAN and get bank name",
            "/validate": "Auto-detect and validate (card or IBAN)",
            "/validate-personal-code": "Validate Iranian Personal national code and get city and town name",
            "/validate-company-code": "Validate Iranian Companies national code",
            "/validate-national-code": "Auto-detect and validate national code (personal or company)",
            "/validate-postal-code": "Validate Iranian Postal code and get city and town name",
            "/validate-plate-number": "Validate Iranian Plate numbers and get city and town name",
            "/validate-landline-phone": "Validate Iranian landline phone numbers and get city and region name",
            "/validate-mobile-phone": "Validate Iranian mobile phone nummber and get city and operator name",
            "/validate-phone-number": "Auto-detect and validate phone number (mobile or landline)", 
            "/get-city": "get next part of a given region",
            "/get-city-information": "get cities information (postal code/plate number/etc) by city vode"
        },
        "usage": {
            "date_converter": {
                "method": "GET or POST",
                "parameter": "date",
                "examples": [
                    "/convert-date?date=1402/10/11",
                    "/convert-date?date=2024-01-01",
                    "/convert-date?date=1445/06/19"
                ]
            },
            "card_validator": {
                "method": "GET or POST",
                "parameter": "card",
                "example": "/validate-card?card=6037991234567890"
            },
            "iban_validator": {
                "method": "GET or POST",
                "parameter": "iban",
                "example": "/validate-iban?iban=IR130170000000104594407003"
            },
            "auto_validator": {
                "method": "GET or POST",
                "parameter": "input",
                "example": "/validate?input=6037991234567890"
            },
            "personal_national_code_validator": {
                "method": "GET or POST",
                "parameter": "personal",
                "example": "/validate-personal-code?personal=236 521-52"
            },
            "company_national_code_validator": {
                "method": "GET or POST",
                "parameter": "company",
                "example": "/validate-company-code?company=125-632-548-06"
            },
            "auto_national_code_validator": {
                "method": "GET or POST",
                "parameter": "input",
                "example": "/validate-national-code?input=125-632-548-06"
            },
            "postal_code_validator": {
                "method": "GET or POST",
                "parameter": "postal",
                "example": "/validate-postal-code?postal=13456 78092"
            },
            "plate_number_validator": {
                "method": "GET or POST",
                "parameter": "plate",
                "example": "/validate-plate-number?plate=88-ق-155-15"
            },
            "landline_phone_validator": {
                "method": "GET or POST",
                "parameter": "landlinephone",
                "example": "/validate-landline-phone?landlinephone=+98 021-66 05 12 34"
            },
            "mobile_phone_validator": {
                "method": "GET or POST",
                "parameter": "mobilephone",
                "example": "/validate-mobile-phone?mobilephone=+98 910 0123456"
            },
            "phone_number_validator": {
                "method": "GET or POST",
                "parameter": "phone",
                "example": "/validate-phone-number?phone=+98 910 069 5977"
            },
            "get_city": {
                "method": "GET or POST",
                "parameter": "code",
                "example": "/get-city?code=1"
            },
            "get_city_information": {
                "method": "GET or POST",
                "parameter": "code",
                "example": "/get-city-information?code=1"
            }
        }
    })


# ============================================================
# Date Converter Endpoint
# ============================================================

@app.route('/convert-date', methods=['GET', 'POST'])
def convert_date():
    if request.method == 'GET':
        date_string = request.args.get('date')
    else:
        data = request.get_json()
        date_string = data.get('date') if data else None

    if not date_string:
        return custom_jsonify({
            "error": "Missing 'date' parameter",
            "usage": "/convert-date?date=YYYY/MM/DD or YYYY-MM-DD"
        }, 400)

    try:
        result = get_full_info(date_string)
        return custom_jsonify(result)
    except ValueError as e:
        return custom_jsonify({"error": str(e)}, 400)
    except Exception as e:
        app.logger.error(f"Unexpected error: {str(e)}")
        return custom_jsonify({"error": "Internal Error"}, 500)


# ============================================================
# Bank Card Validator Endpoint
# ============================================================

@app.route('/validate-card', methods=['GET', 'POST'])
def validate_card():
    if request.method == 'GET':
        card_number = request.args.get('card')
    else:
        data = request.get_json()
        card_number = data.get('card') if data else None

    if not card_number:
        return custom_jsonify({
            "error": "Missing 'card' parameter",
            "usage": "/validate-card?card=6037991234567890"
        }, 400)

    try:
        result = check_card_number(card_number)
        return custom_jsonify(result)
    except ValueError as e:
        return custom_jsonify({"error": str(e)}, 400)
    except Exception as e:
        app.logger.error(f"Unexpected error: {str(e)}")
        return custom_jsonify({"error": "Internal Error"}, 500)


# ============================================================
# IBAN Validator Endpoint
# ============================================================

@app.route('/validate-iban', methods=['GET', 'POST'])
def validate_iban():
    if request.method == 'GET':
        iban = request.args.get('iban')
    else:
        data = request.get_json()
        iban = data.get('iban') if data else None

    if not iban:
        return custom_jsonify({
            "error": "Missing 'iban' parameter",
            "usage": "/validate-iban?iban=IR130170000000104594407003"
        }, 400)

    try:
        result = check_iban(iban)
        return custom_jsonify(result)
    except ValueError as e:
        return custom_jsonify({"error": str(e)}, 400)
    except Exception as e:
        app.logger.error(f"Unexpected error: {str(e)}")
        return custom_jsonify({"error": "Internal Error"}, 500)


# ============================================================
# Auto-detect Validator Endpoint
# ============================================================

@app.route('/validate', methods=['GET', 'POST'])
def validate_auto():
    if request.method == 'GET':
        input_str = request.args.get('input')
    else:
        data = request.get_json()
        input_str = data.get('input') if data else None

    if not input_str:
        return custom_jsonify({
            "error": "Missing 'input' parameter",
            "usage": "/validate?input=6037991234567890 or /validate?input=IR130170000000104594407003"
        }, 400)

    try:
        result = detect_and_validate(input_str)
        return custom_jsonify(result)
    except ValueError as e:
        return custom_jsonify({"error": str(e)}, 400)
    except Exception as e:
        app.logger.error(f"Unexpected error: {str(e)}")
        return custom_jsonify({"error": "Internal Error"}, 500)


# ============================================================
# Personal National Code Validator Endpoint
# ============================================================

@app.route('/validate-personal-code', methods=['GET', 'POST'])
def validate_personal_code():
    if request.method == 'GET':
        personal_code = request.args.get('personal')
    else:
        data = request.get_json()
        personal_code = data.get('personal') if data else None

    if not personal_code:
        return custom_jsonify({
            "error": "Missing 'personal' parameter",
            "usage": "/validate-personal-code?personal=236 521-52"
        }, 400)

    try:
        result = filter(personal_code)
        return custom_jsonify(result)
    except ValueError as e:
        return custom_jsonify({"error": str(e)}, 400)
    except Exception as e:
        app.logger.error(f"Unexpected error: {str(e)}")
        return custom_jsonify({"error": "Internal Error"}, 500)


# ============================================================
# Company National Code Validator Endpoint
# ============================================================

@app.route('/validate-company-code', methods=['GET', 'POST'])
def validate_company_code():
    if request.method == 'GET':
        company_code = request.args.get('company')
    else:
        data = request.get_json()
        company_code = data.get('company') if data else None

    if not company_code:
        return custom_jsonify({
            "error": "Missing 'company' parameter",
            "usage": "/validate-company-code?company=125-632-548-06"
        }, 400)

    try:
        result = filter_company(company_code)
        return custom_jsonify(result)
    except ValueError as e:
        return custom_jsonify({"error": str(e)}, 400)
    except Exception as e:
        app.logger.error(f"Unexpected error: {str(e)}")
        return custom_jsonify({"error": "Internal Error"}, 500)


# ============================================================
# Auto-detect National code Validator Endpoint
# ============================================================

@app.route('/validate-national-code', methods=['GET', 'POST'])
def validate_auto_national_code():
    if request.method == 'GET':
        input_str = request.args.get('input')
    else:
        data = request.get_json()
        input_str = data.get('input') if data else None

    if not input_str:
        return custom_jsonify({
            "error": "Missing 'input' parameter",
            "usage": "/validate-national-code?input=236 521-52 or /validate-national-code?input=125-632-548-06"
        }, 400)

    try:
        result = check(input_str)
        return custom_jsonify(result)
    except ValueError as e:
        return custom_jsonify({"error": str(e)}, 400)
    except Exception as e:
        app.logger.error(f"Unexpected error: {str(e)}")
        return custom_jsonify({"error": "Internal Error"}, 500)

# ============================================================
# Postal Code Validator Endpoint
# ============================================================

@app.route('/validate-postal-code', methods=['GET', 'POST'])
def validate_postal_code():
    if request.method == 'GET':
        postal_code = request.args.get('postal')
    else:
        data = request.get_json()
        postal_code = data.get('postal') if data else None

    if not postal_code:
        return custom_jsonify({
            "error": "Missing 'postal' parameter",
            "usage": "/validate-postal-code?postal=13456 78092"
        }, 400)

    try:
        result = postal_filter(postal_code)
        return custom_jsonify(result)
    except ValueError as e:
        return custom_jsonify({"error": str(e)}, 400)
    except Exception as e:
        app.logger.error(f"Unexpected error: {str(e)}")
        return custom_jsonify({"error": "Internal Error"}, 500)


# ============================================================
# Plate Number Validator Endpoint
# ============================================================

@app.route('/validate-plate-number', methods=['GET', 'POST'])
def validate_plate_number():
    if request.method == 'GET':
        plate_number = request.args.get('plate')
    else:
        data = request.get_json()
        plate_number = data.get('plate') if data else None

    if not plate_number:
        return custom_jsonify({
            "error": "Missing 'plate' parameter",
            "usage": "/validate-plate-number?plate=88-ق-155-15"
        }, 400)

    try:
        result = plate_filter(plate_number)
        return custom_jsonify(result)
    except ValueError as e:
        return custom_jsonify({"error": str(e)}, 400)
    except Exception as e:
        app.logger.error(f"Unexpected error: {str(e)}")
        return custom_jsonify({"error": "Internal Error"}, 500)


# ============================================================
# landline phone number Validator Endpoint
# ============================================================

@app.route('/validate-landline-phone', methods=['GET', 'POST'])
def validate_landline_phone():
    if request.method == 'GET':
        landlinephone = request.args.get('landlinephone')
    else:
        data = request.get_json()
        landlinephone = data.get('landlinephone') if data else None

    if not landlinephone:
        return custom_jsonify({
            "error": "Missing 'landlinephone' parameter",
            "usage": "/validate-landline-phone?landlinephone=+98 021-66 05 12 34"
        }, 400)

    try:
        result = landline_phone_number_filter(landlinephone)
        return custom_jsonify(result)
    except ValueError as e:
        return custom_jsonify({"error": str(e)}, 400)
    except Exception as e:
        app.logger.error(f"Unexpected error: {str(e)}")
        return custom_jsonify({"error": "Internal Error"}, 500)

# ============================================================
# Mobile phone Validator Endpoint
# ============================================================

@app.route('/validate-mobile-phone', methods=['GET', 'POST'])
def validate_mobile_phone():
    if request.method == 'GET':
        mobilephone = request.args.get('mobilephone')
    else:
        data = request.get_json()
        mobilephone = data.get('mobilephone') if data else None

    if not mobilephone:
        return custom_jsonify({
            "error": "Missing 'mobilephone' parameter",
            "usage": "/validate-mobile-phone?mobilephone=+98 910 0123456"
        }, 400)

    try:
        result = mobile_phone_number_filter(mobilephone)
        return custom_jsonify(result)
    except ValueError as e:
        return custom_jsonify({"error": str(e)}, 400)
    except Exception as e:
        app.logger.error(f"Unexpected error: {str(e)}")
        return custom_jsonify({"error": "Internal Error"}, 500)


# ============================================================
# Auto-detect Phone Number Validator Endpoint
# ============================================================

@app.route('/validate-phone-number', methods=['GET', 'POST'])
def validate_phone_number():
    if request.method == 'GET':
        phone_number = request.args.get('phone')
    else:
        data = request.get_json()
        phone_number = data.get('phone') if data else None

    if not phone_number:
        return custom_jsonify({
            "error": "Missing 'phone' parameter",
            "usage": "/validate-phone-number?phone=+98 910 069 5977 or /validate-phone-number?phone=+98 021-66 05 12 34"
        }, 400)

    try:
        result = phone_number_filter(phone_number)
        return custom_jsonify(result)
    except ValueError as e:
        return custom_jsonify({"error": str(e)}, 400)
    except Exception as e:
        app.logger.error(f"Unexpected error: {str(e)}")
        return custom_jsonify({"error": "Internal Error"}, 500)

# ============================================================
# Get city for a given region
# ============================================================

@app.route('/get-city', methods=['GET', 'POST'])
def vget_city():
    if request.method == 'GET':
        code = request.args.get('code')
    else:
        data = request.get_json()
        code = data.get('code') if data else None

    if not code:
        return custom_jsonify({
            "error": "Missing 'code' parameter",
            "usage": "/get-city?code=1"
        }, 400)

    try:
        result = get_information(code)
        return custom_jsonify(result)
    except ValueError as e:
        return custom_jsonify({"error": str(e)}, 400)
    except Exception as e:
        app.logger.error(f"Unexpected error: {str(e)}")
        return custom_jsonify({"error": "Internal Error"}, 500)


# ============================================================
# Get information in a given city
# ============================================================

@app.route('/get-city-information', methods=['GET', 'POST'])
def get_city_information():
    if request.method == 'GET':
        code = request.args.get('code')
    else:
        data = request.get_json()
        code = data.get('code') if data else None

    if not code:
        return custom_jsonify({
            "error": "Missing 'code' parameter",
            "usage": "/get-city-information?code=1"
        }, 400)

    try:
        cleaned = ''.join(re.findall(r"[0-9]+", code))
        plate = get_plate(cleaned)
        postal = get_postal(cleaned)
        phone = get_phone_number(cleaned)
        mobile = get_mobie_phone_number(cleaned)
        national = get_national_code(cleaned)
        parents = get_information(cleaned)
        result = {
            'city_code': cleaned,
            'plate': plate,
            'postal': postal,
            'phone': phone,
            'mobile_phone': mobile,
            'national_code': national
        }
        result.update(parents)
        return custom_jsonify(result)
    except ValueError as e:
        return custom_jsonify({"error": str(e)}, 400)
    except Exception as e:
        app.logger.error(f"Unexpected error: {str(e)}")
        return custom_jsonify({"error": "Internal Error"}, 500)

# ============================================================
# Run Server
# ============================================================

if __name__ == '__main__':
    print("=" * 60)
    print("Integrated API Server is running!")
    print("=" * 60)
    print("\nEndpoints:")
    print("  GET  /")
    print("  GET/POST  /convert-date?date=...")
    print("  GET/POST  /validate-card?card=...")
    print("  GET/POST  /validate-iban?iban=...")
    print("  GET/POST  /validate?input=...")
    print("  GET/POST  /validate-personal-code?pesonal=...")
    print("  GET/POST  /validate-company-code?company=...")
    print("  GET/POST  /validate-national-code?input=...")
    print("  GET/POST  /validate-postal-code?postal=...")
    print("  GET/POST  /validate-plate-number?plate=...")
    print("  GET/POST  /validate-landline-phone?landlinephone=...")
    print("  GET/POST  /validate-mobile-phone?mobilephone=...")
    print("  GET/POST  /validate-phone-number?phone=...")
    print("  GET/POST  /get-city?code=...")
    print("  GET/POST  /get-city-information?code=...")
    print("\nExamples:")
    print("  http://127.0.0.1:5000/convert-date?date=1402/10/11")
    print("  http://127.0.0.1:5000/validate-card?card=6037991234567890")
    print("  http://127.0.0.1:5000/validate-iban?iban=IR130170000000104594407003")
    print("  http://127.0.0.1:5000/validate?input=6037991234567890")
    print("  http://127.0.0.1:5000/validate-personal-code?personal=236 521-52")
    print("  http://127.0.0.1:5000/validate-company-code?company=125-632-548-06")
    print("  http://127.0.0.1:5000/validate-national-code?input=125-632-548-06")
    print("  http://127.0.0.1:5000/validate-postal-code?postal=13456 78092")
    print("  http://127.0.0.1:5000/validate-plate-number?plate=88-ق-155-15")
    print("  http://127.0.0.1:5000/validate-landline-phone?landlinephone=+98 021-66 05 12 34")
    print("  http://127.0.0.1:5000/validate-mobile-phone?mobilephone=+98 910 0123456")
    print("  http://127.0.0.1:5000/validate-phone-number?phone=+98 910 069 5977")
    print("  http://127.0.0.1:5000/get-city?code=1")
    print("  http://127.0.0.1:5000/get-city-information?code=1")
    print("\nPress Ctrl+C to stop\n")

    app.run(debug=True, host='0.0.0.0', port=5000)