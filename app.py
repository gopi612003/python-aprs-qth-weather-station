# coding: utf-8
from flask import Flask, request, jsonify
import json
import time
import re

app = Flask(__name__)
DATA_PATH = "/config/meteo.json"
start_time = time.time()

def safe_float_conversion(value_str):
    """Convert string to float supporting both comma and dot as decimal separator"""
    if not isinstance(value_str, str):
        return float(value_str)  # If already a number, convert directly
    
    # Remove spaces
    value_str = value_str.strip()
    
    # Replace comma with dot to support European format
    # Ex: "22,5" becomes "22.5"
    value_str = value_str.replace(',', '.')
    
    try:
        return float(value_str)
    except ValueError as e:
        print(f"Conversion error '{value_str}': {e}")
        raise

def validate_weather_data(data):
    """Validate received weather data with realistic limits and decimal comma support"""
    limits = {
        'temperature': (-50, 70),     # °C - extreme but realistic range
        'humidity': (0, 100),         # % - standard range
        'pressure': (800, 1200),      # hPa - valid barometric range
        'wind_speed': (0, 100),       # m/s - up to 360 km/h
        'wind_direction': (0, 360),   # degrees - wind direction
        'wind_gust': (0, 150),        # m/s - more intense gusts
        'rain_1h': (0, 200),          # mm - maximum hourly rain
        'rain_24h': (0, 1000),        # mm - maximum daily rain
        'dewpoint': (-60, 50)         # °C - dew point
    }
    
    validated = {}
    rejected = {}
    
    for key, value in data.items():
        try:
            # Conversion with decimal comma support
            numeric_value = safe_float_conversion(value)
            
            if key in limits:
                min_val, max_val = limits[key]
                if min_val <= numeric_value <= max_val:
                    validated[key] = numeric_value
                    print(f"VALID {key}: {value} -> {numeric_value}")
                else:
                    rejected[key] = value
                    print(f"REJECTED {key}: {value} -> {numeric_value} - valid range [{min_val}, {max_val}]")
            else:
                # Unmapped parameters - accept anyway if numeric
                validated[key] = numeric_value
                print(f"UNMAPPED {key}: {value} -> {numeric_value} (unmapped parameter, accepted)")
                
        except (ValueError, TypeError):
            rejected[key] = value
            print(f"REJECTED {key}: {value} - numeric conversion failed")
    
    if rejected:
        print(f"WARNING: {len(rejected)} parameters rejected: {list(rejected.keys())}")
    
    return validated, rejected

@app.route('/meteo', methods=['GET', 'POST'])
def meteo():
    data = None
    client_ip = request.remote_addr
    print(f"Weather request from IP: {client_ip}")

    # Try to read JSON from body if POST
    if request.method == 'POST':
        try:
            data = request.get_json(force=True)
        except Exception as e:
            print(f"JSON parsing error: {e}")
            data = None

    # If no JSON body, try to read parameters from query string
    if not data:
        # List of all possible parameters
        param_names = [
            'temperature', 'humidity', 'pressure', 'wind_speed', 
            'wind_direction', 'wind_gust', 'rain_1h', 'rain_24h', 'dewpoint'
        ]
        
        data = {}
        for param_name in param_names:
            param_value = request.args.get(param_name)
            if param_value is not None:
                data[param_name] = param_value  # Keep as string for validation

    if not data:
        return jsonify({
            "error": "No valid weather data received",
            "help": "Send data via POST JSON or GET parameters",
            "decimal_format": "Both dot (22.5) and comma (22,5) supported"
        }), 400

    print(f"Received data: {data}")
    
    # DATA VALIDATION with decimal comma support
    validated_data, rejected_data = validate_weather_data(data)
    
    if not validated_data:
        return jsonify({
            "error": "All weather data rejected due to validation",
            "rejected": rejected_data,
            "limits_info": "Check parameter ranges in logs"
        }), 400

    # Save only validated data
    try:
        with open(DATA_PATH, 'w') as f:
            json.dump(validated_data, f, indent=2)
        
        response_data = {
            "status": "ok",
            "accepted": len(validated_data),
            "accepted_params": list(validated_data.keys()),
            "timestamp": time.time(),
            "decimal_support": "comma and dot supported"
        }
        
        if rejected_data:
            response_data["rejected"] = len(rejected_data)
            response_data["rejected_params"] = list(rejected_data.keys())
        
        print(f"Weather data saved: {validated_data}")
        return jsonify(response_data)
        
    except Exception as e:
        print(f"File save error: {e}")
        return jsonify({"error": f"File save error: {str(e)}"}), 500

@app.route('/health', methods=['GET'])
def health():
    """Endpoint for healthcheck"""
    return jsonify({
        "status": "healthy",
        "uptime": time.time() - start_time,
        "decimal_support": "Both comma and dot decimal separators supported"
    })

@app.route('/status', methods=['GET'])
def status():
    """Endpoint for complete system monitoring"""
    try:
        import os
        # Read last transmission
        if os.path.exists(DATA_PATH):
            with open(DATA_PATH, 'r') as f:
                last_data = json.load(f)
            data_timestamp = os.path.getmtime(DATA_PATH)
        else:
            last_data = None
            data_timestamp = None
            
        return jsonify({
            "status": "running",
            "last_weather_data": last_data,
            "last_update": data_timestamp,
            "uptime": time.time() - start_time,
            "features": {
                "decimal_support": "comma and dot (22,5 or 22.5)",
                "validation": "enabled with realistic ranges",
                "parameters": ["temperature", "humidity", "pressure", "wind_speed", "wind_direction", "wind_gust", "rain_1h", "rain_24h", "dewpoint"]
            }
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
