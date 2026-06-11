# app.py
from flask import Flask, request, jsonify
from core.events import get_full_info
from core.bank_validator import check_card_number, check_iban, detect_and_validate
from core.nationalCode_validator import check, filter, filter_company
from core.number_plate_validator import plate_filter
from core.postal_code_validator import postal_filter
import json

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
            "/validate": "Auto-detect and validate (card or IBAN)"
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
    print("  GET/POST  /validate-postal-code?input=...")
    print("  GET/POST  /validate-plate-number?input=...")
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
    print("\nPress Ctrl+C to stop\n")

    app.run(debug=True, host='0.0.0.0', port=5000)