# app.py
from flask import Flask, request, jsonify
from core.events import get_full_info

app = Flask(__name__)

app.json.ensure_ascii = False
@app.route('/')
def home():
    """صفحه اصلی با راهنمای استفاده"""
    return jsonify({
        "service": "Date Converter API",
        "version": "1.0",
        "description": "Convert dates between Jalali (Shamsi), Gregorian, and Hijri calendars",
        "endpoints": {
            "/": "This help page",
            "/convert-date": "Main conversion endpoint"
        },
        "usage": {
            "method": "GET",
            "parameter": "date",
            "examples": [
                "/convert-date?date=1402/10/11",
                "/convert-date?date=2024-01-01",
                "/convert-date?date=1445/06/19"
            ]
        },
        "output": {
            "original_calendar_type": "Detected calendar type",
            "dates": {"jalali": "...", "gregorian": "...", "hijri": "..."},
            "month_names": {"jalali": "...", "gregorian": "...", "hijri": "..."},
            "day_names": {"jalali": "...", "gregorian": "...", "hijri": "..."},
            "events": {"jalali": [], "gregorian": [], "hijri": []}
        }
    })


@app.route('/convert-date', methods=['GET', 'POST'])
def convert_date():
    """
    Convert a date to all three calendar formats with events

    GET: /convert-date?date=1402/10/11
    POST: {"date": "1402/10/11"}
    """
    if request.method == 'GET':
        date_string = request.args.get('date')
    else:
        data = request.get_json()
        date_string = data.get('date') if data else None

    if not date_string:
        return jsonify({
            "error": "Missing 'date' parameter",
            "usage": "/convert-date?date=YYYY/MM/DD or YYYY-MM-DD"
        }), 400

    try:
        result = get_full_info(date_string)
        return jsonify(result)
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": f"Internal error: {str(e)}"}), 500


if __name__ == '__main__':
    print("=" * 50)
    print("Date Converter API is running!")
    print("=" * 50)
    print("\nTry these URLs:")
    print("  http://127.0.0.1:5000/")
    print("  http://127.0.0.1:5000/convert-date?date=1402/10/11")
    print("  http://127.0.0.1:5000/convert-date?date=2024-01-01")
    print("  http://127.0.0.1:5000/convert-date?date=1445/06/19")
    print("\nPress Ctrl+C to stop\n")

    app.run(debug=True, host='0.0.0.0', port=5000)