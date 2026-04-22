# app.py
from flask import Flask, request, jsonify
from core.events import get_full_info
import json

app = Flask(__name__)

# app.json.ensure_ascii = False

app.config['JSON_AS_ASCII'] = False

def custom_jsonify(data, status=200):
    """Custom jsonify that properly handles Persian/Arabic characters"""
    return app.response_class(
        response=json.dumps(data, ensure_ascii=False, indent=2),
        status=status,
        mimetype='application/json'
    )


@app.route('/')
def home():
    """صفحه اصلی با راهنمای استفاده"""
    return custom_jsonify({
        "service": "Date Converter API",
        "version": "1.0",
        "description": "Convert dates between Jalali (Shamsi), Gregorian, and Hijri calendars",
        "endpoints": {
            "/": "This help page",
            "/convert-date": "Main conversion endpoint"
        },
        "usage": {
            "method": "GET or POST",
            "parameter": "date",
            "examples": [
                "/convert-date?date=1402/10/11",
                "/convert-date?date=2024-01-01",
                "/convert-date?date=1445/06/19"
            ]
        },
        "output": {
            "original_calendar_type": "Detected calendar type",
            "dates": {"jalali": "تاریخ شمسی", "gregorian": "تاریخ میلادی", "hijri": "تاریخ قمری"},
            "month_names": {"jalali": "نام ماه شمسی", "gregorian": "نام ماه میلادی", "hijri": "نام ماه قمری"},
            "day_names": {"jalali": "نام روز شمسی", "gregorian": "نام روز میلادی", "hijri": "نام روز قمری"},
            "events": {"jalali": ["مناسبت‌های شمسی"], "gregorian": ["مناسبت‌های میلادی"], "hijri": ["مناسبت‌های قمری"]}
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


if __name__ == '__main__':
#    print("  http://127.0.0.1:5000/convert-date?date=1445/06/19")

    app.run(debug=True, host='0.0.0.0', port=5000)