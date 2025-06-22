#!/usr/bin/env python3
"""
Simple Timezone Converter Web App
Converts current time between two cities
"""

from flask import Flask, render_template, request, jsonify
from datetime import datetime
import pytz
from timezonefinder import TimezoneFinder
import requests

app = Flask(__name__)

# Initialize timezone finder
tf = TimezoneFinder()

def get_city_coordinates(city_name):
    """Get latitude and longitude for a city using a geocoding service"""
    try:
        # Using OpenStreetMap Nominatim API (free, no API key required)
        url = f"https://nominatim.openstreetmap.org/search"
        params = {
            'q': city_name,
            'format': 'json',
            'limit': 1
        }
        headers = {
            'User-Agent': 'TimezoneConverter/1.0'
        }
        
        response = requests.get(url, params=params, headers=headers)
        response.raise_for_status()
        
        data = response.json()
        if data:
            return float(data[0]['lat']), float(data[0]['lon'])
        return None, None
    except Exception as e:
        print(f"Error getting coordinates for {city_name}: {e}")
        return None, None

def get_timezone_from_city(city_name):
    """Get timezone for a given city"""
    try:
        lat, lon = get_city_coordinates(city_name)
        if lat is None or lon is None:
            return None
        
        timezone_str = tf.timezone_at(lat=lat, lng=lon)
        if timezone_str:
            return pytz.timezone(timezone_str)
        return None
    except Exception as e:
        print(f"Error getting timezone for {city_name}: {e}")
        return None

def convert_time_between_cities(city_a, city_b, time_str=None):
    """Convert current time or specified time between two cities"""
    try:
        # Get timezones for both cities
        tz_a = get_timezone_from_city(city_a)
        tz_b = get_timezone_from_city(city_b)
        
        if not tz_a or not tz_b:
            return None
        
        # Use current time if no time specified
        if time_str:
            # Parse the time string (assuming format: HH:MM)
            try:
                hour, minute = map(int, time_str.split(':'))
                # Use today's date with specified time
                today = datetime.now().date()
                dt = datetime.combine(today, datetime.min.time().replace(hour=hour, minute=minute))
            except ValueError:
                dt = datetime.now()
        else:
            dt = datetime.now()
        
        # Localize to city A's timezone
        dt_a = tz_a.localize(dt)
        
        # Convert to city B's timezone
        dt_b = dt_a.astimezone(tz_b)
        
        return {
            'city_a': city_a,
            'city_b': city_b,
            'time_a': dt_a.strftime('%Y-%m-%d %H:%M:%S %Z'),
            'time_b': dt_b.strftime('%Y-%m-%d %H:%M:%S %Z'),
            'timezone_a': str(tz_a),
            'timezone_b': str(tz_b)
        }
        
    except Exception as e:
        print(f"Error converting time: {e}")
        return None

@app.route('/')
def index():
    """Main page"""
    return render_template('index.html')

@app.route('/convert', methods=['POST'])
def convert():
    """Convert timezone between cities"""
    try:
        data = request.get_json()
        city_a = data.get('city_a', '').strip()
        city_b = data.get('city_b', '').strip()
        time_str = data.get('time', '').strip()
        
        if not city_a or not city_b:
            return jsonify({'error': 'Both cities are required'}), 400
        
        # Convert empty time string to None
        if not time_str:
            time_str = None
            
        result = convert_time_between_cities(city_a, city_b, time_str)
        
        if result:
            return jsonify(result)
        else:
            return jsonify({'error': 'Could not find timezone information for one or both cities'}), 400
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, host='127.0.0.1', port=5000)