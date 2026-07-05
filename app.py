from flask import Flask, request, jsonify
from flask_cors import CORS
import json
import re
from functools import wraps

# ============================================================
# Import Site Modules (Backend)
# ============================================================
from backend.auth import Auth
from backend.database import Database

# ============================================================
# Import Web Service Modules (Core)
# ============================================================
from core.events import get_full_info
from core.bank_validator import check_card_number, check_iban, detect_and_validate
from core.nationalCode_validator import check, filter, filter_company, get_national_code
from core.number_plate_validator import plate_filter, get_plate
from core.postal_code_validator import postal_filter, get_postal
from core.phone_number_validator import (
    landline_phone_number_filter,
    mobile_phone_number_filter,
    phone_number_filter,
    get_phone_number,
    get_mobie_phone_number
)
from core.iran_city import get_information

app = Flask(__name__)
app.secret_key = 'your-secret-key-here-change-in-production'
app.config['JSON_AS_ASCII'] = False

# ============================================================
# CORS Configuration
# ============================================================
CORS(app, resources={
    r"/api/*": {
        "methods": ["POST", "GET", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"]
    },
    r"/*": {
        "methods": ["GET", "POST", "OPTIONS"],
        "allow_headers": ["Content-Type"]
    }
})

# ============================================================
# Initialize Database
# ============================================================
db = Database()


# ============================================================
# Utility Functions
# ============================================================

def custom_jsonify(data, status=200):
    """Custom jsonify that properly handles Persian/Arabic characters"""
    return app.response_class(
        response=json.dumps(data, ensure_ascii=False, indent=2),
        status=status,
        mimetype='application/json'
    )


# ============================================================
# Auth Decorators
# ============================================================

def require_auth(f):
    """Decorator to require authentication for routes"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = None

        # Get token from Authorization header
        auth_header = request.headers.get('Authorization')
        if auth_header and auth_header.startswith('Bearer '):
            token = auth_header[7:]

        # If no token in header, try to get from JSON body
        if not token and request.is_json:
            data = request.get_json(silent=True)
            if data and data.get('token'):
                token = data.get('token')

        if not token:
            return jsonify({
                'success': False,
                'message': 'Authentication required',
                'code': 'AUTH_REQUIRED'
            }), 401

        # Validate session
        is_valid, message, session_data = Auth.validate_session(token)

        if not is_valid:
            return jsonify({
                'success': False,
                'message': message,
                'code': 'SESSION_INVALID'
            }), 401

        # Store session data in request context
        request.session_data = session_data
        request.token = token

        return f(*args, **kwargs)
    return decorated_function


# ============================================================
# Site Authentication Routes
# ============================================================

@app.route('/api/auth/login', methods=['POST'])
def login():
    """User login route"""
    try:
        data = request.get_json()

        if not data or not data.get('username') or not data.get('password'):
            return jsonify({
                'success': False,
                'message': 'Username and password are required'
            }), 400

        username = data.get('username', '').strip()
        password = data.get('password', '')

        success, message, token = Auth.login(username, password)

        if success:
            return jsonify({
                'success': True,
                'message': message,
                'username': username,
                'token': token
            }), 200
        else:
            return jsonify({
                'success': False,
                'message': message
            }), 401

    except Exception as e:
        print(f"[ERROR] Error in login route: {e}")
        return jsonify({
            'success': False,
            'message': 'Internal server error'
        }), 500


@app.route('/api/auth/signup', methods=['POST'])
def signup():
    """User signup route"""
    try:
        data = request.get_json()

        if not data or not data.get('username') or not data.get('password'):
            return jsonify({
                'success': False,
                'message': 'Username and password are required'
            }), 400

        username = data.get('username', '').strip()
        password = data.get('password', '')

        success, message = Auth.signup(username, password)

        if success:
            return jsonify({
                'success': True,
                'message': message
            }), 200
        else:
            return jsonify({
                'success': False,
                'message': message
            }), 400

    except Exception as e:
        print(f"[ERROR] Error in signup route: {e}")
        return jsonify({
            'success': False,
            'message': 'Internal server error'
        }), 500


@app.route('/api/auth/verify', methods=['POST', 'GET'])
@require_auth
def verify_session():
    """Verify session validity"""
    return jsonify({
        'success': True,
        'message': 'Session is valid',
        'username': request.session_data.get('userName'),
        'lastPage': request.session_data.get('lastPage')
    }), 200


@app.route('/api/auth/logout', methods=['POST'])
@require_auth
def logout():
    """Logout route"""
    try:
        token = request.token
        success, message = Auth.logout(token)

        if success:
            return jsonify({
                'success': True,
                'message': message
            }), 200
        else:
            return jsonify({
                'success': False,
                'message': message
            }), 400

    except Exception as e:
        print(f"[ERROR] Error in logout route: {e}")
        return jsonify({
            'success': False,
            'message': 'Internal server error'
        }), 500


@app.route('/api/auth/change-password', methods=['POST'])
@require_auth
def change_password():
    """Change password route"""
    try:
        data = request.get_json()

        if not data or not data.get('currentPassword') or not data.get('newPassword'):
            return jsonify({
                'success': False,
                'message': 'All parameters are required'
            }), 400

        username = request.session_data.get('userName')
        current_password = data.get('currentPassword', '')
        new_password = data.get('newPassword', '')

        success, message = Auth.change_password(username, current_password, new_password)

        if success:
            return jsonify({
                'success': True,
                'message': message
            }), 200
        else:
            return jsonify({
                'success': False,
                'message': message
            }), 401

    except Exception as e:
        print(f"[ERROR] Error in change password route: {e}")
        return jsonify({
            'success': False,
            'message': 'Internal server error'
        }), 500


@app.route('/api/auth/update-last-page', methods=['POST'])
@require_auth
def update_last_page():
    """Update last page in session"""
    try:
        data = request.get_json()
        if not data or not data.get('lastPage'):
            return jsonify({
                'success': False,
                'message': 'lastPage is required'
            }), 400

        token = request.token
        last_page = data.get('lastPage')

        success = Auth.update_last_page(token, last_page)
        if success:
            return jsonify({
                'success': True,
                'message': 'Last page updated'
            }), 200
        else:
            return jsonify({
                'success': False,
                'message': 'Error updating last page'
            }), 400

    except Exception as e:
        print(f"[ERROR] Error in update last page route: {e}")
        return jsonify({
            'success': False,
            'message': 'Internal server error'
        }), 500


@app.route('/api/auth/validate-username', methods=['POST'])
def validate_username():
    """Username validation route"""
    try:
        data = request.get_json()

        if not data or not data.get('username'):
            return jsonify({
                'valid': False,
                'message': 'Username is required'
            }), 400

        username = data.get('username', '').strip()
        is_valid, message = Auth.validate_username(username)

        return jsonify({
            'valid': is_valid,
            'message': message
        }), 200

    except Exception as e:
        print(f"[ERROR] Error in username validation route: {e}")
        return jsonify({
            'valid': False,
            'message': 'Internal server error'
        }), 500


@app.route('/api/auth/validate-password', methods=['POST'])
def validate_password():
    """Password validation route"""
    try:
        data = request.get_json()

        if not data or not data.get('password'):
            return jsonify({
                'valid': False,
                'errors': ['Password is required']
            }), 400

        password = data.get('password', '')
        is_valid, errors = Auth.validate_password(password)

        return jsonify({
            'valid': is_valid,
            'errors': errors
        }), 200

    except Exception as e:
        print(f"[ERROR] Error in password validation route: {e}")
        return jsonify({
            'valid': False,
            'errors': ['Internal server error']
        }), 500

# ============================================================
# Company Routes
# ============================================================

@app.route('/api/company/register', methods=['POST'])
@require_auth
def register_company():
    """Register a new company"""
    try:
        data = request.get_json()
        username = request.session_data.get('userName')

        # Validate required fields
        required_fields = ['companyName', 'nationalCode', 'registrationNumber', 'registrationDate', 'location']
        for field in required_fields:
            if not data.get(field):
                return jsonify({
                    'success': False,
                    'message': f'فیلد {field} الزامی است'
                }), 400

        # Validate company name
        company_name = data.get('companyName', '').strip()
        if len(company_name) < 3:
            return jsonify({
                'success': False,
                'message': 'نام شرکت باید حداقل ۳ کاراکتر باشد'
            }), 400

        # Validate national code
        national_code = data.get('nationalCode', '').strip()
        if not re.match(r'^\d{11}$', national_code):
            return jsonify({
                'success': False,
                'message': 'شناسه ملی باید ۱۱ رقم باشد'
            }), 400

        # Validate national code using algorithm
        if not Auth.validate_company_national_code(national_code):
            return jsonify({
                'success': False,
                'message': 'شناسه ملی معتبر نیست'
            }), 400

        # Check if company already exists
        if db.company_exists(national_code):
            return jsonify({
                'success': False,
                'message': 'شرکتی با این شناسه ملی قبلاً ثبت شده است'
            }), 400

        # Validate registration number
        registration_number = data.get('registrationNumber', '').strip()
        if not registration_number:
            return jsonify({
                'success': False,
                'message': 'شماره ثبت نمی‌تواند خالی باشد'
            }), 400

        # Validate registration date
        reg_date = data.get('registrationDate', {})
        year = reg_date.get('year')
        month = reg_date.get('month')
        day = reg_date.get('day')

        if not year or not month or not day:
            return jsonify({
                'success': False,
                'message': 'تاریخ ثبت کامل نیست'
            }), 400

        if year < 1300 or year > 1410:
            return jsonify({
                'success': False,
                'message': 'سال ثبت باید بین ۱۳۰۰ تا ۱۴۱۰ باشد'
            }), 400

        if month < 1 or month > 12:
            return jsonify({
                'success': False,
                'message': 'ماه ثبت معتبر نیست'
            }), 400

        # Validate location
        location = data.get('location', {})
        required_location = ['state', 'county', 'section', 'city']
        for loc in required_location:
            if not location.get(loc):
                return jsonify({
                    'success': False,
                    'message': f'فیلد {loc} الزامی است'
                }), 400

        # Create company
        success = db.create_company(username, data)

        if success:
            return jsonify({
                'success': True,
                'message': 'شرکت با موفقیت ثبت شد'
            }), 200
        else:
            return jsonify({
                'success': False,
                'message': 'خطا در ثبت شرکت'
            }), 500

    except Exception as e:
        print(f"[ERROR] Error in register company route: {e}")
        return jsonify({
            'success': False,
            'message': 'Internal server error'
        }), 500


@app.route('/api/company/list', methods=['GET'])
@require_auth
def list_companies():
    """Get list of companies for the current user"""
    try:
        username = request.session_data.get('userName')
        companies = db.get_companies_by_user(username)

        return jsonify({
            'success': True,
            'companies': companies
        }), 200

    except Exception as e:
        print(f"[ERROR] Error in list companies route: {e}")
        return jsonify({
            'success': False,
            'message': 'Internal server error'
        }), 500

# ============================================================
# Web Service Routes (Home Page)
# ============================================================

@app.route('/')
def home():
    return custom_jsonify({
        "service": "Integrated API",
        "version": "2.0",
        "description": "Date Converter + Bank Card/IBAN Validator + National Code Validator + More",
        "endpoints": {
            "/": "This help page",
            # Authentication endpoints
            "/api/auth/login": "User login",
            "/api/auth/signup": "User registration",
            "/api/auth/verify": "Verify session",
            "/api/auth/logout": "User logout",
            "/api/auth/change-password": "Change password",
            "/api/auth/update-last-page": "Update last page",
            "/api/auth/validate-username": "Validate username",
            "/api/auth/validate-password": "Validate password",
            # Web service endpoints
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
            "/validate-mobile-phone": "Validate Iranian mobile phone number and get city and operator name",
            "/validate-phone-number": "Auto-detect and validate phone number (mobile or landline)",
            "/get-city": "get next part of a given region",
            "/get-city-information": "get cities information (postal code/plate number/etc) by city code"
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
# Web Service Routes (Validators)
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


@app.route('/get-city', methods=['GET', 'POST'])
def get_city():
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
# Error Handlers
# ============================================================

@app.errorhandler(404)
def not_found(error):
    """Route not found"""
    return jsonify({
        'success': False,
        'message': 'Route not found'
    }), 404


@app.errorhandler(500)
def internal_error(error):
    """Internal server error"""
    return jsonify({
        'success': False,
        'message': 'Internal server error'
    }), 500


# ============================================================
# Run Server
# ============================================================

if __name__ == '__main__':
    print("=" * 60)
    print("Integrated Server (Site + Web Service) is running!")
    print("=" * 60)
    print("\n=== Site Authentication Endpoints ===")
    print("  POST /api/auth/login")
    print("  POST /api/auth/signup")
    print("  POST /api/auth/verify")
    print("  POST /api/auth/logout")
    print("  POST /api/auth/change-password")
    print("  POST /api/auth/update-last-page")
    print("  POST /api/auth/validate-username")
    print("  POST /api/auth/validate-password")
    print("\n=== Web Service Endpoints ===")
    print("  GET  /")
    print("  GET/POST  /convert-date?date=...")
    print("  GET/POST  /validate-card?card=...")
    print("  GET/POST  /validate-iban?iban=...")
    print("  GET/POST  /validate?input=...")
    print("  GET/POST  /validate-personal-code?personal=...")
    print("  GET/POST  /validate-company-code?company=...")
    print("  GET/POST  /validate-national-code?input=...")
    print("  GET/POST  /validate-postal-code?postal=...")
    print("  GET/POST  /validate-plate-number?plate=...")
    print("  GET/POST  /validate-landline-phone?landlinephone=...")
    print("  GET/POST  /validate-mobile-phone?mobilephone=...")
    print("  GET/POST  /validate-phone-number?phone=...")
    print("  GET/POST  /get-city?code=...")
    print("  GET/POST  /get-city-information?code=...")
    print("\n=== Examples ===")
    print("  Site: http://127.0.0.1:5000/frontend/index.html")
    print("  Web Service: http://127.0.0.1:5000/")
    print("\nPress Ctrl+C to stop\n")

    app.run(debug=True, host='0.0.0.0', port=5000)