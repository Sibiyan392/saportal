# app.py - UPDATED WITH ALL ROUTES
from flask import Flask, render_template, jsonify, request, redirect, url_for, send_from_directory
from flask_cors import CORS
import requests
from datetime import datetime, timedelta
import hashlib
import os
from dotenv import load_dotenv
import pytz
import logging
import time
import os

# Disable SSL warnings
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)



logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'sa-portal-2026')
CORS(app, resources={r"/*": {"origins": "*"}}, supports_credentials=True)

# SA Timezone
sa_timezone = pytz.timezone('Africa/Johannesburg')

# =========== API KEYS ===========
API_KEYS = {
    'weather': '343239f3cf54b54415a375bf3211fe5e',
    'google_maps': 'AIzaSyB6cDIaPyXSEM05JiFsMolqAb2NhJIUoW4',
    'football_data': '601057ac05684f6fa4af02642d49555f',
}

# =========== CACHE SYSTEM ===========
class CacheSystem:
    def __init__(self):
        self.cache = {}
    
    def get(self, key, max_age=300):
        if key in self.cache:
            data, timestamp = self.cache[key]
            if time.time() - timestamp < max_age:
                return data
        return None
    
    def set(self, key, data):
        self.cache[key] = (data, time.time())
    
    def clear(self):
        self.cache.clear()

cache = CacheSystem()

# =========== FOOTBALL DATA SERVICE ===========
class FootballDataService:
    """Get 2026 European football data"""
    
    @staticmethod
    def get_headers():
        return {
            'X-Auth-Token': API_KEYS['football_data'],
            'Accept': 'application/json'
        }
    
    @staticmethod
    def make_api_request(url, params=None, retries=2):
        headers = FootballDataService.get_headers()
        
        for attempt in range(retries + 1):
            try:
                timeout = 8 if attempt == 0 else 15
                response = requests.get(url, headers=headers, params=params, timeout=timeout, verify=False)
                
                if response.status_code == 200:
                    return response.json()
                elif response.status_code == 429:
                    time.sleep(1)
                else:
                    logger.error(f"API error {response.status_code}")
                    
            except requests.exceptions.Timeout:
                if attempt < retries:
                    time.sleep(0.5)
                    continue
                else:
                    raise
            except requests.exceptions.RequestException as e:
                if attempt < retries:
                    time.sleep(0.5)
                    continue
                else:
                    raise
        
        return None
    
    @staticmethod
    def get_live_matches():
        cache_key = "football_live_matches"
        cached = cache.get(cache_key, 60)
        if cached:
            cached['cached'] = True
            return cached
        
        try:
            url = "https://api.football-data.org/v4/matches"
            params = {'status': 'LIVE'}
            
            data = FootballDataService.make_api_request(url, params)
            
            if data:
                matches = FootballDataService._process_matches_data(data)
                
                result = {
                    'success': True,
                    'matches': matches,
                    'total': len(matches),
                    'last_updated': datetime.now().isoformat(),
                    'source': 'Football-Data.org'
                }
                
                cache.set(cache_key, result)
                return result
            
        except Exception as e:
            logger.error(f"Live matches error: {str(e)}")
        
        return {
            'success': True,
            'matches': [],
            'total': 0,
            'last_updated': datetime.now().isoformat(),
        }
    
    @staticmethod
    def get_todays_matches():
        cache_key = "football_todays_matches"
        cached = cache.get(cache_key, 300)
        if cached:
            cached['cached'] = True
            return cached
        
        try:
            url = "https://api.football-data.org/v4/matches"
            today = datetime.now().strftime('%Y-%m-%d')
            params = {'dateFrom': today, 'dateTo': today}
            
            data = FootballDataService.make_api_request(url, params)
            
            if data:
                matches = FootballDataService._process_matches_data(data)
                
                result = {
                    'success': True,
                    'matches': matches,
                    'total': len(matches),
                    'date': today,
                    'last_updated': datetime.now().isoformat(),
                }
                
                cache.set(cache_key, result)
                return result
            
        except Exception as e:
            logger.error(f"Today matches error: {str(e)}")
        
        return {
            'success': True,
            'matches': [],
            'total': 0,
            'date': datetime.now().strftime('%Y-%m-%d'),
            'last_updated': datetime.now().isoformat(),
        }
    
    @staticmethod
    def get_standings():
        cache_key = "football_standings"
        cached = cache.get(cache_key, 3600)
        if cached:
            cached['cached'] = True
            return cached
        
        try:
            url = "https://api.football-data.org/v4/competitions/PL/standings"
            
            data = FootballDataService.make_api_request(url)
            
            if data:
                standings = FootballDataService._process_standings_data(data)
                
                result = {
                    'success': True,
                    'standings': standings,
                    'last_updated': datetime.now().isoformat(),
                    'competition': 'Premier League',
                    'season': data.get('season', {}).get('currentMatchday', 1),
                }
                
                cache.set(cache_key, result)
                return result
            
        except Exception as e:
            logger.error(f"Standings error: {str(e)}")
        
        return {
            'success': True,
            'standings': [],
            'last_updated': datetime.now().isoformat(),
            'competition': 'Premier League',
        }
    
    @staticmethod
    def get_upcoming_fixtures():
        cache_key = "football_upcoming_fixtures"
        cached = cache.get(cache_key, 600)
        if cached:
            cached['cached'] = True
            return cached
        
        try:
            url = "https://api.football-data.org/v4/matches"
            
            today = datetime.now()
            next_week = today + timedelta(days=7)
            
            params = {
                'dateFrom': today.strftime('%Y-%m-%d'),
                'dateTo': next_week.strftime('%Y-%m-%d'),
                'status': 'SCHEDULED'
            }
            
            data = FootballDataService.make_api_request(url, params)
            
            if data:
                matches = FootballDataService._process_matches_data(data, upcoming=True)
                
                result = {
                    'success': True,
                    'matches': matches,
                    'total': len(matches),
                    'date_range': f"{today.strftime('%Y-%m-%d')} to {next_week.strftime('%Y-%m-%d')}",
                    'last_updated': datetime.now().isoformat(),
                }
                
                cache.set(cache_key, result)
                return result
            
        except Exception as e:
            logger.error(f"Fixtures error: {str(e)}")
        
        return {
            'success': True,
            'matches': [],
            'total': 0,
            'date_range': f"{datetime.now().strftime('%Y-%m-%d')} to {(datetime.now() + timedelta(days=7)).strftime('%Y-%m-%d')}",
            'last_updated': datetime.now().isoformat(),
        }
    
    @staticmethod
    def _process_matches_data(data, upcoming=False):
        matches = []
        
        if 'matches' in data:
            for match in data['matches']:
                status = match.get('status', 'SCHEDULED')
                
                if status == 'LIVE':
                    match_status = 'LIVE'
                    is_live = True
                elif status == 'FINISHED':
                    match_status = 'COMPLETED'
                    is_live = False
                elif status in ['SCHEDULED', 'TIMED']:
                    match_status = 'UPCOMING'
                    is_live = False
                else:
                    match_status = 'UPCOMING'
                    is_live = False
                
                score = match.get('score', {})
                full_time = score.get('fullTime', {})
                home_score = full_time.get('home')
                away_score = full_time.get('away')
                
                if home_score is not None and away_score is not None:
                    score_display = f"{home_score}-{away_score}"
                elif match_status == 'UPCOMING' or upcoming:
                    score_display = 'vs'
                else:
                    score_display = '0-0'
                
                minute = None
                if is_live:
                    minute = match.get('minute', 'LIVE')
                
                competition = match.get('competition', {})
                
                utc_date = match.get('utcDate')
                match_time = ''
                match_date = ''
                
                if utc_date:
                    try:
                        dt = datetime.fromisoformat(utc_date.replace('Z', '+00:00'))
                        sa_dt = dt.astimezone(sa_timezone)
                        match_date = sa_dt.strftime('%Y-%m-%d')
                        match_time = sa_dt.strftime('%H:%M')
                    except Exception:
                        match_date = datetime.now().strftime('%Y-%m-%d')
                        match_time = 'TBC'
                
                match_data = {
                    'id': match.get('id'),
                    'home_team': match.get('homeTeam', {}).get('name', 'Home Team'),
                    'away_team': match.get('awayTeam', {}).get('name', 'Away Team'),
                    'score': score_display,
                    'status': match_status,
                    'is_live': is_live,
                    'date': match_date,
                    'time': match_time,
                    'venue': match.get('venue', 'Football Stadium'),
                    'competition': competition.get('name', 'Football Match'),
                    'competition_code': competition.get('code'),
                    'matchday': match.get('matchday', 1)
                }
                
                if minute:
                    match_data['minute'] = minute
                
                matches.append(match_data)
        
        return matches
    
    @staticmethod
    def _process_standings_data(data):
        standings = []
        
        if 'standings' in data and len(data['standings']) > 0:
            table = data['standings'][0].get('table', [])
            
            for i, team_data in enumerate(table):
                team = team_data.get('team', {})
                stats = team_data
                
                standings.append({
                    'position': stats.get('position', i + 1),
                    'team': team.get('name', f'Team {i + 1}'),
                    'played': stats.get('playedGames', 0),
                    'won': stats.get('won', 0),
                    'drawn': stats.get('draw', 0),
                    'lost': stats.get('lost', 0),
                    'goals_for': stats.get('goalsFor', 0),
                    'goals_against': stats.get('goalsAgainst', 0),
                    'goal_difference': stats.get('goalDifference', 0),
                    'points': stats.get('points', 0),
                    'form': stats.get('form', '-----')
                })
        
        return standings

# =========== LOCATION SERVICE ===========
class LocationService:
    
    @staticmethod
    def reverse_geocode(lat: float, lon: float):
        cache_key = f"reverse_{lat:.6f}_{lon:.6f}"
        cached = cache.get(cache_key, 86400)
        if cached:
            return cached
        
        try:
            url = "https://maps.googleapis.com/maps/api/geocode/json"
            params = {
                'latlng': f"{lat},{lon}",
                'key': API_KEYS['google_maps'],
                'region': 'za',
                'language': 'en',
                'result_type': ['street_address', 'route', 'locality', 'sublocality', 'neighborhood']
            }
            
            response = requests.get(url, params=params, timeout=5, verify=False)
            
            if response.status_code == 200:
                data = response.json()
                if data['status'] == 'OK' and data['results']:
                    # Try to get the best possible location name
                    location_name = LocationService._extract_best_location_name(data['results'], lat, lon)
                    
                    location_data = {
                        'name': location_name,
                        'formatted_address': data['results'][0]['formatted_address'],
                        'latitude': lat,
                        'longitude': lon,
                        'success': True,
                        'accuracy': LocationService._determine_accuracy(data['results'])
                    }
                    
                    cache.set(cache_key, location_data)
                    return location_data
        
        except Exception as e:
            logger.error(f"Reverse geocoding error: {str(e)}")
        
        # Fallback to coordinates if geocoding fails
        return {
            'name': f"Location ({lat:.4f}, {lon:.4f})",
            'formatted_address': f"Latitude: {lat:.4f}, Longitude: {lon:.4f}",
            'latitude': lat,
            'longitude': lon,
            'success': False,
            'accuracy': 'coordinates'
        }
    
    @staticmethod
    def _extract_best_location_name(results, lat, lon):
        """
        Extract the best possible location name from geocoding results.
        Priority order:
        1. Street name with number
        2. Street/Route name
        3. Neighborhood
        4. Sublocality (suburb)
        5. Locality (town/city)
        6. Administrative area level 2 (municipality)
        7. Fallback to coordinates
        """
        
        # First, try to find street address
        for result in results:
            address_components = result.get('address_components', [])
            types = result.get('types', [])
            
            # Check for street address or route
            if 'street_address' in types or 'route' in types:
                for component in address_components:
                    if 'route' in component.get('types', []):
                        street_name = component.get('long_name', '')
                        # Try to get street number
                        street_number = ''
                        for comp in address_components:
                            if 'street_number' in comp.get('types', []):
                                street_number = comp.get('long_name', '')
                                break
                        
                        if street_number:
                            return f"{street_number} {street_name}"
                        return street_name
            
            # Check for neighborhood
            if 'neighborhood' in types:
                for component in address_components:
                    if 'neighborhood' in component.get('types', []):
                        return component.get('long_name', '')
            
            # Check for sublocality (suburb)
            if 'sublocality' in types or 'sublocality_level_1' in types:
                for component in address_components:
                    if 'sublocality' in component.get('types', []) or 'sublocality_level_1' in component.get('types', []):
                        return component.get('long_name', '')
            
            # Check for locality (town/city)
            if 'locality' in types:
                for component in address_components:
                    if 'locality' in component.get('types', []):
                        return component.get('long_name', '')
            
            # Check for administrative area level 2 (municipality)
            if 'administrative_area_level_2' in types:
                for component in address_components:
                    if 'administrative_area_level_2' in component.get('types', []):
                        return component.get('long_name', '')
        
        # If no good name found in address components, use the first formatted address
        # but extract just the first part (before first comma)
        first_result = results[0]
        formatted_address = first_result.get('formatted_address', '')
        
        # Try to get a meaningful part of the address
        parts = formatted_address.split(',')
        if len(parts) > 0:
            # Return first part (usually the most specific)
            return parts[0].strip()
        
        # Ultimate fallback
        return f"Location ({lat:.4f}, {lon:.4f})"
    
    @staticmethod
    def _determine_accuracy(results):
        """
        Determine the accuracy level of the geocoding result.
        """
        if not results:
            return 'coordinates'
        
        first_result = results[0]
        types = first_result.get('types', [])
        
        if 'street_address' in types:
            return 'street_address'
        elif 'route' in types:
            return 'route'
        elif 'neighborhood' in types:
            return 'neighborhood'
        elif 'sublocality' in types:
            return 'sublocality'
        elif 'locality' in types:
            return 'locality'
        elif 'administrative_area_level_2' in types:
            return 'municipality'
        else:
            return 'general'

# =========== WEATHER SERVICE WITH HOURLY FORECAST ===========
class WeatherService:
    """Get weather data from OpenWeatherMap with hourly forecast"""
    
    @staticmethod
    def get_weather_with_forecast(lat: float, lon: float):
        """Get current weather AND 5-day forecast WITH HOURLY DATA"""
        cache_key = f"weather_forecast_{lat}_{lon}"
        cached = cache.get(cache_key, 300)
        if cached:
            cached['cached'] = True
            return cached
        
        try:
            current_url = "https://api.openweathermap.org/data/2.5/weather"
            current_params = {
                'lat': lat,
                'lon': lon,
                'appid': API_KEYS['weather'],
                'units': 'metric',
                'lang': 'en'
            }
            
            forecast_url = "https://api.openweathermap.org/data/2.5/forecast"
            forecast_params = {
                'lat': lat,
                'lon': lon,
                'appid': API_KEYS['weather'],
                'units': 'metric',
                'lang': 'en',
                'cnt': 40
            }
            
            current_response = requests.get(current_url, params=current_params, timeout=10)
            forecast_response = requests.get(forecast_url, params=forecast_params, timeout=10)
            
            if current_response.status_code == 200 and forecast_response.status_code == 200:
                current_data = current_response.json()
                forecast_data = forecast_response.json()
                
                # Process current weather
                current_weather = {
                    'temp': round(current_data['main']['temp']),
                    'feels_like': round(current_data['main']['feels_like']),
                    'humidity': current_data['main']['humidity'],
                    'pressure': current_data['main']['pressure'],
                    'wind_speed': round(current_data['wind']['speed'] * 3.6, 1),
                    'wind_deg': current_data['wind'].get('deg', 0),
                    'description': current_data['weather'][0]['description'].title(),
                    'icon': current_data['weather'][0]['icon'],
                    'visibility': current_data.get('visibility', 10000) / 1000,
                    'clouds': current_data.get('clouds', {}).get('all', 0),
                    'sunrise': datetime.fromtimestamp(current_data['sys']['sunrise']).astimezone(sa_timezone).strftime('%H:%M'),
                    'sunset': datetime.fromtimestamp(current_data['sys']['sunset']).astimezone(sa_timezone).strftime('%H:%M'),
                    'timestamp': datetime.now().isoformat(),
                }
                
                # Process hourly forecast
                hourly_forecast = []
                
                for item in forecast_data['list'][:12]:
                    dt = datetime.fromtimestamp(item['dt'])
                    time_str = dt.strftime('%I %p').lstrip('0')
                    
                    hourly_forecast.append({
                        'time': time_str,
                        'temp': round(item['main']['temp']),
                        'feels_like': round(item['main']['feels_like']),
                        'description': item['weather'][0]['description'].title(),
                        'icon': item['weather'][0]['icon'],
                        'humidity': item['main']['humidity'],
                        'wind_speed': round(item['wind']['speed'] * 3.6, 1),
                        'pop': round(item.get('pop', 0) * 100),
                        'clouds': item.get('clouds', {}).get('all', 0)
                    })
                
                # Process 5-day forecast
                forecast_list = []
                daily_forecast = {}
                
                for item in forecast_data['list']:
                    dt = datetime.fromtimestamp(item['dt'])
                    date_key = dt.strftime('%Y-%m-%d')
                    
                    if date_key not in daily_forecast:
                        daily_forecast[date_key] = {
                            'date': dt,
                            'temps': [],
                            'icons': [],
                            'descriptions': []
                        }
                    
                    daily_forecast[date_key]['temps'].append(item['main']['temp'])
                    daily_forecast[date_key]['icons'].append(item['weather'][0]['icon'])
                    daily_forecast[date_key]['descriptions'].append(item['weather'][0]['description'])
                
                forecast_days = []
                today_date = datetime.now().date()
                
                for i, (date_key, day_data) in enumerate(sorted(daily_forecast.items())[:6]):
                    if datetime.strptime(date_key, '%Y-%m-%d').date() <= today_date:
                        continue
                    
                    temps = day_data['temps']
                    day_name = day_data['date'].strftime('%a')
                    month_day = day_data['date'].strftime('%b %d')
                    
                    icon_counts = {}
                    for icon in day_data['icons']:
                        icon_counts[icon] = icon_counts.get(icon, 0) + 1
                    most_common_icon = max(icon_counts, key=icon_counts.get)
                    
                    desc_counts = {}
                    for desc in day_data['descriptions']:
                        desc_counts[desc] = desc_counts.get(desc, 0) + 1
                    most_common_desc = max(desc_counts, key=desc_counts.get)
                    
                    forecast_days.append({
                        'date': date_key,
                        'day': day_name,
                        'month_day': month_day,
                        'temp': round(sum(temps) / len(temps)),
                        'temp_min': round(min(temps)),
                        'temp_max': round(max(temps)),
                        'icon': most_common_icon,
                        'description': most_common_desc.title()
                    })
                
                weather_data = {
                    'success': True,
                    'current': current_weather,
                    'hourly': hourly_forecast[:8],
                    'forecast': forecast_days[:5],
                    'cached': False
                }
                
                cache.set(cache_key, weather_data)
                return weather_data
                
        except Exception as e:
            logger.error(f"Weather API error: {str(e)}")
        
        return None

# =========== ROUTES ===========

@app.route('/')
def index():
    """Homepage"""
    try:
        football_service = FootballDataService()
        live_data = football_service.get_live_matches()
        standings_data = football_service.get_standings()
        
        return render_template('index.html',
                             sports_data=live_data,
                             standings_data=standings_data,
                             current_year=datetime.now().year,
                             page_title='SA Daily Portal 2026',
                             current_date=datetime.now().strftime('%d %B %Y'))
        
    except Exception as e:
        logger.error(f"Homepage error: {str(e)}")
        return render_template('index.html',
                             current_year=datetime.now().year)

@app.route('/weather')
def weather():
    """Weather page"""
    return render_template('weather.html',
                         current_year=datetime.now().year,
                         page_title='South African Weather 2026')

@app.route('/sassa')
def sassa():
    """SASSA page"""
    return render_template('sassa.html',
                         current_year=datetime.now().year,
                         page_title='SASSA 2026')

@app.route('/sports')
def sports():
    """Sports page"""
    try:
        football_service = FootballDataService()
        live_data = football_service.get_live_matches()
        standings_data = football_service.get_standings()
        fixtures_data = football_service.get_upcoming_fixtures()
        
        return render_template('sports.html',
                             live_data=live_data,
                             standings_data=standings_data,
                             fixtures_data=fixtures_data,
                             current_year=datetime.now().year,
                             page_title='European Football 2026',
                             current_date=datetime.now().strftime('%d %B %Y'))
        
    except Exception as e:
        logger.error(f"Sports page error: {str(e)}")
        return render_template('sports.html',
                             current_year=datetime.now().year)

@app.route('/howto')
def howto():
    """How-to guides"""
    return render_template('howto.html',
                         current_year=datetime.now().year,
                         page_title='How-To Guides 2026')

@app.route('/contact')
def contact():
    """Contact page"""
    return render_template('contact.html',
                         current_year=datetime.now().year,
                         page_title='Contact Developer - SA Daily Portal 2026')

@app.route('/disclaimer')
def disclaimer():
    """Disclaimer page"""
    return render_template('disclaimer.html',
                         current_year=datetime.now().year,
                         page_title='Disclaimer - SA Daily Portal 2026')

@app.route('/faq')
def faq():
    """FAQ page"""
    return render_template('faq.html',
                         current_year=datetime.now().year,
                         page_title='Frequently Asked Questions - SA Daily Portal 2026')

@app.route('/privacy')
def privacy():
    """Privacy policy page"""
    return render_template('privacy.html',
                         current_year=datetime.now().year,
                         page_title='Privacy Policy - SA Daily Portal 2026')

@app.route('/terms')
def terms():
    """Terms of service page"""
    return render_template('terms.html',
                         current_year=datetime.now().year,
                         page_title='Terms of Service - SA Daily Portal 2026')

@app.route('/about')
def about():
    """About page - redirected from /about"""
    return redirect(url_for('contact'))

# =========== API ENDPOINTS ===========

@app.route('/api/weather', methods=['GET'])
def api_weather():
    """Weather API endpoint WITH HOURLY FORECAST"""
    location = request.args.get('location', '').strip()
    lat = request.args.get('lat')
    lon = request.args.get('lon')
    
    try:
        weather_service = WeatherService()
        location_service = LocationService()
        
        coordinates = None
        location_name = 'Your Location'
        
        if lat and lon:
            try:
                lat_float = float(lat)
                lon_float = float(lon)
                coordinates = (lat_float, lon_float)
                
                reverse_data = location_service.reverse_geocode(lat_float, lon_float)
                if reverse_data:
                    location_name = reverse_data.get('name', f"Lat: {lat_float}, Lon: {lon_float}")
                else:
                    location_name = f"Lat: {lat_float:.2f}, Lon: {lon_float:.2f}"
            except ValueError:
                return jsonify({'success': False, 'error': 'Invalid coordinates'}), 400
        elif location:
            # Location search functionality (simplified)
            location_name = location
            coordinates = (-26.2041, 28.0473)  # Default to Johannesburg
        else:
            return jsonify({'success': False, 'error': 'Location required'}), 400
        
        lat, lon = coordinates
        weather_data = weather_service.get_weather_with_forecast(lat, lon)
        
        if weather_data:
            response_data = {
                'success': weather_data.get('success', False),
                'location': location_name,
                'coordinates': {'lat': lat, 'lon': lon},
                'current': weather_data.get('current', {}),
                'hourly': weather_data.get('hourly', []),
                'forecast': weather_data.get('forecast', []),
                'timestamp': datetime.now().isoformat(),
                'cached': weather_data.get('cached', False)
            }
            return jsonify(response_data)
        else:
            return jsonify({
                'success': False,
                'error': 'Weather service temporarily unavailable',
                'timestamp': datetime.now().isoformat()
            }), 503
        
    except Exception as e:
        logger.error(f"Weather API error: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Weather service temporarily unavailable',
            'timestamp': datetime.now().isoformat()
        }), 503

@app.route('/api/sports/matches', methods=['GET'])
def api_sports_matches():
    """Today's matches"""
    try:
        football_service = FootballDataService()
        matches_data = football_service.get_todays_matches()
        return jsonify(matches_data)
    except Exception as e:
        logger.error(f"Matches API error: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Matches service updating',
            'timestamp': datetime.now().isoformat()
        }), 503

@app.route('/api/sports/standings', methods=['GET'])
def api_sports_standings():
    """Standings"""
    try:
        football_service = FootballDataService()
        standings_data = football_service.get_standings()
        return jsonify(standings_data)
    except Exception as e:
        logger.error(f"Standings API error: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Standings service updating',
            'timestamp': datetime.now().isoformat()
        }), 503

@app.route('/api/sports/live', methods=['GET'])
def api_sports_live():
    """Live scores"""
    try:
        football_service = FootballDataService()
        live_data = football_service.get_live_matches()
        return jsonify(live_data)
    except Exception as e:
        logger.error(f"Live scores API error: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Live scores updating',
            'timestamp': datetime.now().isoformat()
        }), 503

@app.route('/api/sports/fixtures', methods=['GET'])
def api_sports_fixtures():
    """Fixtures"""
    try:
        football_service = FootballDataService()
        fixtures_data = football_service.get_upcoming_fixtures()
        return jsonify(fixtures_data)
    except Exception as e:
        logger.error(f"Fixtures API error: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Fixtures service updating',
            'timestamp': datetime.now().isoformat()
        }), 503

@app.route('/api/sports/upcoming', methods=['GET'])
def api_sports_upcoming():
    """Upcoming matches"""
    try:
        football_service = FootballDataService()
        fixtures_data = football_service.get_upcoming_fixtures()
        return jsonify(fixtures_data)
    except Exception as e:
        logger.error(f"Upcoming matches API error: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Upcoming matches service updating',
            'timestamp': datetime.now().isoformat()
        }), 503@app.route('/api/weather', methods=['GET'])
def api_weather():
    """Weather API endpoint WITH HOURLY FORECAST"""
    location = request.args.get('location', '').strip()
    lat = request.args.get('lat')
    lon = request.args.get('lon')
    
    try:
        weather_service = WeatherService()
        location_service = LocationService()
        
        coordinates = None
        location_name = 'Your Location'
        location_accuracy = 'unknown'
        
        if lat and lon:
            try:
                lat_float = float(lat)
                lon_float = float(lon)
                coordinates = (lat_float, lon_float)
                
                # Get location data with improved reverse geocoding
                location_data = location_service.reverse_geocode(lat_float, lon_float)
                
                if location_data and location_data.get('success', False):
                    location_name = location_data.get('name', f"Location ({lat_float:.4f}, {lon_float:.4f})")
                    location_accuracy = location_data.get('accuracy', 'coordinates')
                else:
                    # Fallback if reverse geocoding fails
                    location_name = f"Location ({lat_float:.4f}, {lon_float:.4f})"
                    location_accuracy = 'coordinates'
                    
            except ValueError:
                return jsonify({'success': False, 'error': 'Invalid coordinates'}), 400
        elif location:
            # Location search by name (simplified - could be enhanced)
            location_name = location
            coordinates = (-26.2041, 28.0473)  # Default to Johannesburg
            location_accuracy = 'search'
        else:
            return jsonify({'success': False, 'error': 'Location required'}), 400
        
        lat, lon = coordinates
        weather_data = weather_service.get_weather_with_forecast(lat, lon)
        
        if weather_data:
            response_data = {
                'success': weather_data.get('success', False),
                'location': location_name,
                'location_accuracy': location_accuracy,
                'coordinates': {'lat': lat, 'lon': lon},
                'current': weather_data.get('current', {}),
                'hourly': weather_data.get('hourly', []),
                'forecast': weather_data.get('forecast', []),
                'timestamp': datetime.now().isoformat(),
                'cached': weather_data.get('cached', False)
            }
            return jsonify(response_data)
        else:
            return jsonify({
                'success': False,
                'error': 'Weather service temporarily unavailable',
                'timestamp': datetime.now().isoformat()
            }), 503
        
    except Exception as e:
        logger.error(f"Weather API error: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Weather service temporarily unavailable',
            'timestamp': datetime.now().isoformat()
        }), 503

@app.route('/api/sassa/payment-dates', methods=['GET'])
def api_sassa_payment_dates():
    """SASSA 2026 payment dates"""
    now = datetime.now()
    
    payment_dates_2026 = [
        '5 January 2026',
        '2 February 2026',
        '2 March 2026',
        '1 April 2026',
        '5 May 2026',
        '2 June 2026',
        '1 July 2026',
        '4 August 2026',
        '1 September 2026',
        '6 October 2026',
        '3 November 2026',
        '1 December 2026'
    ]
    
    next_payment = None
    for payment_date in payment_dates_2026:
        payment_datetime = datetime.strptime(payment_date, '%d %B %Y')
        if payment_datetime >= now:
            next_payment = payment_date
            break
    
    if not next_payment:
        next_payment = payment_dates_2026[0]
    
    return jsonify({
        'success': True,
        'next_payment_date': next_payment,
        'payment_window': '1st - 5th of each month',
        'current_year': '2026',
        'official_contacts': {
            'helpline': '0800 60 10 11',
            'whatsapp': '082 046 8553',
            'website': 'https://www.sassa.gov.za',
            'email': 'GrantEnquiries@sassa.gov.za'
        }
    })

@app.route('/api/contact/submit', methods=['POST'])
def api_contact_submit():
    """Contact form submission"""
    try:
        data = request.form
        
        # Validate required fields
        required_fields = ['name', 'email', 'subject', 'message']
        for field in required_fields:
            if not data.get(field):
                return jsonify({
                    'success': False,
                    'error': f'Missing required field: {field}'
                }), 400
        
        # In a production environment, you would:
        # 1. Save to database
        # 2. Send email notification
        # 3. Validate email format
        # 4. Implement spam protection
        
        # For now, simulate successful submission
        return jsonify({
            'success': True,
            'message': 'Message received successfully',
            'response_time': '24-48 hours',
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Contact form error: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to process contact form',
            'timestamp': datetime.now().isoformat()
        }), 500

@app.route('/api/guides/list', methods=['GET'])
def api_guides_list():
    """List of available guides"""
    guides = [
        {
            'id': 'sassa-srd-application',
            'title': 'SRD R350 Grant Application',
            'description': 'Complete step-by-step guide to applying for the Social Relief of Distress R350 grant',
            'category': 'sassa',
            'difficulty': 'easy',
            'estimated_time': '15 minutes',
            'steps': 7
        },
        {
            'id': 'id-application',
            'title': 'Smart ID Card Application',
            'description': 'How to apply for a South African Smart ID Card',
            'category': 'id',
            'difficulty': 'medium',
            'estimated_time': '30 minutes',
            'steps': 8
        },
        {
            'id': 'tax-return',
            'title': 'SARS Tax Return Filing',
            'description': 'Guide to filing your annual tax return with SARS',
            'category': 'tax',
            'difficulty': 'medium',
            'estimated_time': '25 minutes',
            'steps': 6
        },
        {
            'id': 'drivers-license',
            'title': 'Drivers License Renewal',
            'description': 'Complete process for renewing your South African drivers license',
            'category': 'license',
            'difficulty': 'medium',
            'estimated_time': '20 minutes',
            'steps': 5
        }
    ]
    
    return jsonify({
        'success': True,
        'guides': guides,
        'total': len(guides),
        'timestamp': datetime.now().isoformat()
    })

@app.route('/api/status', methods=['GET'])
def api_status():
    """API status"""
    return jsonify({
        'status': 'online',
        'timestamp': datetime.now().isoformat(),
        'year': '2026',
        'services': {
            'weather': 'active',
            'football': 'active',
            'sassa_2026': 'active',
            'guides': 'active',
            'contact': 'active',
            'faq': 'active'
        },
        'version': '2026.2.0',
        'uptime': '100%',
        'last_updated': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    })

# =========== ERROR HANDLERS ===========

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html',
                         current_year=datetime.now().year,
                         page_title='Page Not Found - SA Daily Portal 2026'), 404

@app.errorhandler(500)
def internal_server_error(e):
    logger.error(f"500 Error: {str(e)}")
    return render_template('500.html',
                         current_year=datetime.now().year,
                         page_title='Server Error - SA Daily Portal 2026'), 500

# =========== STATIC FILES ===========

@app.route('/static/<path:filename>')
def static_files(filename):
    return send_from_directory('static', filename)

# =========== REDIRECTS ===========

@app.route('/home')
def redirect_home():
    return redirect(url_for('index'))

@app.route('/index.html')
def redirect_index():
    return redirect(url_for('index'))

@app.route('/soccer')
def redirect_soccer():
    return redirect(url_for('sports'))

@app.route('/football')
def redirect_football():
    return redirect(url_for('sports'))

@app.route('/guide')
def redirect_guide():
    return redirect(url_for('howto'))

@app.route('/guides')
def redirect_guides():
    return redirect(url_for('howto'))

@app.route('/help')
def redirect_help():
    return redirect(url_for('faq'))

@app.route('/questions')
def redirect_questions():
    return redirect(url_for('faq'))

# =========== APPLICATION START ===========

if __name__ == '__main__':
    # Create necessary directories
    required_dirs = ['templates', 'static/css', 'static/js', 'static/images']
    for dir_name in required_dirs:
        os.makedirs(dir_name, exist_ok=True)
    
    # Create basic templates if they don't exist
    basic_templates = {
        'contact.html': '''<!DOCTYPE html>
<html lang="en" data-theme="light">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Contact Developer - SA Daily Portal 2026</title>
    <style>
        :root {
            --primary: #2563eb;
            --primary-dark: #1d4ed8;
            --secondary: #10b981;
            --accent: #f59e0b;
            --danger: #ef4444;
            --background: #f8fafc;
            --card-bg: #ffffff;
            --text: #1f2937;
            --text-light: #6b7280;
            --border: #e5e7eb;
        }
        body { font-family: 'Inter', sans-serif; margin: 0; padding: 20px; background: var(--background); color: var(--text); min-height: 100vh; }
        .container { max-width: 800px; margin: 0 auto; }
        .contact-hero { background: linear-gradient(135deg, var(--primary), var(--primary-dark)); color: white; padding: 3rem 2rem; border-radius: 16px; margin-bottom: 2rem; text-align: center; }
        .contact-hero h1 { margin: 0 0 1rem 0; font-size: 2.5rem; }
        .contact-hero p { font-size: 1.1rem; opacity: 0.9; max-width: 600px; margin: 0 auto; }
        .contact-form { background: var(--card-bg); padding: 2rem; border-radius: 16px; box-shadow: 0 4px 20px rgba(0,0,0,0.08); margin: 2rem 0; }
        .form-group { margin-bottom: 1.5rem; }
        .form-group label { display: block; margin-bottom: 0.5rem; font-weight: 600; color: var(--text); }
        .form-control { width: 100%; padding: 0.85rem; border: 1px solid var(--border); border-radius: 8px; font-size: 1rem; transition: border-color 0.3s; }
        .form-control:focus { outline: none; border-color: var(--primary); box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.1); }
        .btn-primary { background: linear-gradient(135deg, var(--primary), var(--primary-dark)); color: white; padding: 0.85rem 1.75rem; border: none; border-radius: 10px; font-weight: 600; cursor: pointer; transition: all 0.3s; display: inline-flex; align-items: center; gap: 0.5rem; }
        .btn-primary:hover { background: linear-gradient(135deg, var(--primary-dark), #1e40af); transform: translateY(-3px); box-shadow: 0 6px 12px rgba(37, 99, 235, 0.25); }
        .contact-info { display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 1.5rem; margin: 2rem 0; }
        .info-card { background: var(--card-bg); padding: 1.5rem; border-radius: 12px; border: 1px solid var(--border); }
        .info-card h3 { margin: 0 0 1rem 0; color: var(--primary); display: flex; align-items: center; gap: 0.5rem; }
        a { color: var(--primary); text-decoration: none; }
        a:hover { text-decoration: underline; }
    </style>
</head>
<body>
    <div class="container">
        <div class="contact-hero">
            <h1>Contact Developer</h1>
            <p>Have questions, suggestions, or feedback? Get in touch with the developer of SA Daily Portal 2026.</p>
        </div>
        
        <div class="contact-info">
            <div class="info-card">
                <h3><i class="fas fa-user"></i> Developer Info</h3>
                <p><strong>Name:</strong> Nompumelelo</p>
                <p><strong>Location:</strong> Ermelo, South Africa</p>
                <p><strong>Email:</strong> sibiyan4444@gmail.com</p>
                <p><strong>Phone:</strong> 072 472 8166</p>
                <p><strong>Hours:</strong> 9am-5pm Weekdays</p>
            </div>
            
            <div class="info-card">
                <h3><i class="fas fa-question-circle"></i> Support</h3>
                <p>For technical issues or website feedback, please use the contact form or email directly.</p>
                <p>For SASSA-related questions, always contact official SASSA channels first.</p>
                <p>Response time: 24-48 hours</p>
            </div>
        </div>
        
        <div class="contact-form">
            <h2 style="margin: 0 0 1.5rem 0; color: var(--primary);">Send Message</h2>
            <form id="contactForm">
                <div class="form-group">
                    <label for="name">Full Name</label>
                    <input type="text" id="name" class="form-control" required>
                </div>
                
                <div class="form-group">
                    <label for="email">Email Address</label>
                    <input type="email" id="email" class="form-control" required>
                </div>
                
                <div class="form-group">
                    <label for="subject">Subject</label>
                    <input type="text" id="subject" class="form-control" required>
                </div>
                
                <div class="form-group">
                    <label for="message">Message</label>
                    <textarea id="message" class="form-control" rows="6" required></textarea>
                </div>
                
                <button type="submit" class="btn-primary">
                    <i class="fas fa-paper-plane"></i> Send Message
                </button>
            </form>
        </div>
        
        <p style="text-align: center; margin-top: 2rem;">
            <a href="/">← Return to Home</a>
        </p>
    </div>
    
    <script>
        document.getElementById('contactForm').addEventListener('submit', async function(e) {
            e.preventDefault();
            
            const formData = {
                name: document.getElementById('name').value,
                email: document.getElementById('email').value,
                subject: document.getElementById('subject').value,
                message: document.getElementById('message').value
            };
            
            try {
                const response = await fetch('/api/contact/submit', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/x-www-form-urlencoded',
                    },
                    body: new URLSearchParams(formData)
                });
                
                const data = await response.json();
                
                if (data.success) {
                    alert('Message sent successfully! We\'ll respond within 24-48 hours.');
                    document.getElementById('contactForm').reset();
                } else {
                    alert('Failed to send message: ' + data.error);
                }
            } catch (error) {
                alert('Network error. Please try again or email directly.');
            }
        });
    </script>
</body>
</html>''',
        'disclaimer.html': '''<!DOCTYPE html>
<html lang="en" data-theme="light">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Disclaimer - SA Daily Portal 2026</title>
    <style>
        :root {
            --primary: #2563eb;
            --primary-dark: #1d4ed8;
            --secondary: #10b981;
            --accent: #f59e0b;
            --danger: #ef4444;
            --background: #f8fafc;
            --card-bg: #ffffff;
            --text: #1f2937;
            --text-light: #6b7280;
            --border: #e5e7eb;
        }
        body { font-family: 'Inter', sans-serif; margin: 0; padding: 20px; background: var(--background); color: var(--text); min-height: 100vh; }
        .container { max-width: 800px; margin: 0 auto; }
        .disclaimer-hero { background: linear-gradient(135deg, var(--danger), #dc2626); color: white; padding: 3rem 2rem; border-radius: 16px; margin-bottom: 2rem; text-align: center; }
        .disclaimer-hero h1 { margin: 0 0 1rem 0; font-size: 2.5rem; }
        .disclaimer-hero p { font-size: 1.1rem; opacity: 0.9; max-width: 600px; margin: 0 auto; }
        .disclaimer-content { background: var(--card-bg); padding: 2rem; border-radius: 16px; box-shadow: 0 4px 20px rgba(0,0,0,0.08); margin: 2rem 0; }
        .warning-box { background: #fef3c7; border: 2px solid var(--accent); border-radius: 12px; padding: 1.5rem; margin: 1.5rem 0; }
        .warning-box h3 { color: #d97706; margin: 0 0 1rem 0; display: flex; align-items: center; gap: 0.5rem; }
        h2 { color: var(--primary); margin: 2rem 0 1rem 0; }
        p { line-height: 1.7; margin-bottom: 1rem; }
        ul { padding-left: 1.5rem; margin-bottom: 1rem; }
        li { margin-bottom: 0.5rem; line-height: 1.6; }
        a { color: var(--primary); text-decoration: none; }
        a:hover { text-decoration: underline; }
    </style>
</head>
<body>
    <div class="container">
        <div class="disclaimer-hero">
            <h1>⚠️ Important Disclaimer</h1>
            <p>Please read this disclaimer carefully before using SA Daily Portal 2026</p>
        </div>
        
        <div class="disclaimer-content">
            <div class="warning-box">
                <h3><i class="fas fa-exclamation-triangle"></i> CRITICAL NOTICE</h3>
                <p><strong>SA Daily Portal is an UNOFFICIAL information website. We are NOT affiliated with any government department, SASSA, SARS, or official weather services.</strong></p>
            </div>
            
            <h2>1. Nature of Information</h2>
            <p>All information provided on this website is for general informational purposes only. We strive to provide accurate and up-to-date information, but we make no representations or warranties of any kind, express or implied, about the completeness, accuracy, reliability, suitability, or availability of the information.</p>
            
            <h2>2. Government Services Information</h2>
            <p>Information regarding SASSA grants, payment dates, application processes, and other government services is based on:</p>
            <ul>
                <li>Publicly available information</li>
                <li>Historical patterns and trends</li>
                <li>User experiences and reports</li>
                <li>Official announcements (when available)</li>
            </ul>
            <p><strong>Always verify with official sources before making decisions based on this information.</strong></p>
            
            <h2>3. Weather Information</h2>
            <p>Weather data is sourced from third-party providers. While we strive for accuracy, weather predictions are inherently uncertain. Never make safety-critical decisions based solely on our weather information.</p>
            
            <h2>4. Sports Data</h2>
            <p>European football data is provided by third-party APIs. Match schedules, scores, and standings are subject to change. Always check official league websites for confirmed information.</p>
            
            <h2>5. No Professional Advice</h2>
            <p>The information on this website does not constitute professional advice of any kind. For specific advice regarding grants, taxes, legal matters, or other issues, consult qualified professionals or official government channels.</p>
            
            <h2>6. Limitation of Liability</h2>
            <p>We shall not be liable for any loss or damage including without limitation, indirect or consequential loss or damage, or any loss or damage whatsoever arising from loss of data or profits arising out of, or in connection with, the use of this website.</p>
            
            <h2>7. External Links</h2>
            <p>Our website may contain links to external websites. We have no control over the nature, content, and availability of those sites. The inclusion of any links does not necessarily imply a recommendation or endorse the views expressed within them.</p>
            
            <h2>8. User Responsibility</h2>
            <p>By using this website, you acknowledge that:</p>
            <ul>
                <li>You understand the informational nature of this site</li>
                <li>You will verify critical information with official sources</li>
                <li>You use the information at your own risk</li>
                <li>You will not hold us liable for decisions made based on our information</li>
            </ul>
            
            <div class="warning-box">
                <h3><i class="fas fa-shield-alt"></i> Official Channels</h3>
                <p><strong>For official information always use:</strong></p>
                <ul>
                    <li>SASSA: 0800 60 10 11 or www.sassa.gov.za</li>
                    <li>SARS: 0800 00 7277 or www.sars.gov.za</li>
                    <li>Home Affairs: Visit your local office</li>
                    <li>Weather: www.weathersa.co.za</li>
                </ul>
            </div>
            
            <p style="text-align: center; margin-top: 2rem; font-weight: 600;">
                Last updated: February 2026
            </p>
        </div>
        
        <p style="text-align: center; margin-top: 2rem;">
            <a href="/">← Return to Home</a> | 
            <a href="/contact">Contact Developer</a>
        </p>
    </div>
</body>
</html>'''
    }
    
    # Add missing templates from previous list
    basic_templates.update({
        'privacy.html': '''<!DOCTYPE html>
<html lang="en" data-theme="light">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Privacy Policy - SA Daily Portal 2026</title>
    <style>
        :root {
            --primary: #2563eb;
            --primary-dark: #1d4ed8;
            --secondary: #10b981;
            --accent: #f59e0b;
            --danger: #ef4444;
            --background: #f8fafc;
            --card-bg: #ffffff;
            --text: #1f2937;
            --text-light: #6b7280;
            --border: #e5e7eb;
        }
        body { font-family: 'Inter', sans-serif; margin: 0; padding: 20px; background: var(--background); color: var(--text); }
        .container { max-width: 800px; margin: 0 auto; background: var(--card-bg); padding: 2rem; border-radius: 16px; box-shadow: 0 4px 20px rgba(0,0,0,0.08); }
        h1 { color: var(--primary); margin-top: 0; }
        a { color: var(--primary); text-decoration: none; }
        a:hover { text-decoration: underline; }
    </style>
</head>
<body>
    <div class="container">
        <h1>Privacy Policy</h1>
        <p>SA Daily Portal 2026 respects your privacy. We use cookies for analytics and advertising through Google AdSense. We don't collect personal information unless you voluntarily provide it through our contact form.</p>
        <p>For full privacy policy details, please contact the developer.</p>
        <p><a href="/">Return to Home</a></p>
    </div>
</body>
</html>''',
        'terms.html': '''<!DOCTYPE html>
<html lang="en" data-theme="light">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Terms of Service - SA Daily Portal 2026</title>
    <style>
        :root {
            --primary: #2563eb;
            --primary-dark: #1d4ed8;
            --secondary: #10b981;
            --accent: #f59e0b;
            --danger: #ef4444;
            --background: #f8fafc;
            --card-bg: #ffffff;
            --text: #1f2937;
            --text-light: #6b7280;
            --border: #e5e7eb;
        }
        body { font-family: 'Inter', sans-serif; margin: 0; padding: 20px; background: var(--background); color: var(--text); }
        .container { max-width: 800px; margin: 0 auto; background: var(--card-bg); padding: 2rem; border-radius: 16px; box-shadow: 0 4px 20px rgba(0,0,0,0.08); }
        h1 { color: var(--primary); margin-top: 0; }
        a { color: var(--primary); text-decoration: none; }
        a:hover { text-decoration: underline; }
    </style>
</head>
<body>
    <div class="container">
        <h1>Terms of Service</h1>
        <p>By using SA Daily Portal 2026, you agree to our terms. This is an unofficial information portal. Always verify information with official sources. We are not liable for decisions made based on information from this site.</p>
        <p>For full terms, please see our <a href="/disclaimer">Disclaimer</a> page.</p>
        <p><a href="/">Return to Home</a></p>
    </div>
</body>
</html>''',
        '404.html': '''<!DOCTYPE html>
<html lang="en" data-theme="light">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Page Not Found - SA Daily Portal 2026</title>
    <style>
        :root {
            --primary: #2563eb;
            --primary-dark: #1d4ed8;
            --secondary: #10b981;
            --accent: #f59e0b;
            --danger: #ef4444;
            --background: #f8fafc;
            --card-bg: #ffffff;
            --text: #1f2937;
            --text-light: #6b7280;
            --border: #e5e7eb;
        }
        body { font-family: 'Inter', sans-serif; margin: 0; padding: 20px; background: var(--background); color: var(--text); display: flex; align-items: center; justify-content: center; min-height: 100vh; }
        .container { max-width: 600px; margin: 0 auto; background: var(--card-bg); padding: 3rem; border-radius: 16px; box-shadow: 0 4px 20px rgba(0,0,0,0.08); text-align: center; }
        h1 { color: var(--primary); margin-top: 0; font-size: 3rem; }
        p { font-size: 1.1rem; color: var(--text-light); }
        a { color: var(--primary); text-decoration: none; font-weight: 600; display: inline-block; margin-top: 1rem; padding: 0.75rem 1.5rem; background: var(--primary); color: white; border-radius: 8px; }
        a:hover { background: var(--primary-dark); }
    </style>
</head>
<body>
    <div class="container">
        <h1>404</h1>
        <p>Page not found. The page you're looking for doesn't exist or has been moved.</p>
        <a href="/">Return to Home</a>
    </div>
</body>
</html>''',
        '500.html': '''<!DOCTYPE html>
<html lang="en" data-theme="light">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Server Error - SA Daily Portal 2026</title>
    <style>
        :root {
            --primary: #2563eb;
            --primary-dark: #1d4ed8;
            --secondary: #10b981;
            --accent: #f59e0b;
            --danger: #ef4444;
            --background: #f8fafc;
            --card-bg: #ffffff;
            --text: #1f2937;
            --text-light: #6b7280;
            --border: #e5e7eb;
        }
        body { font-family: 'Inter', sans-serif; margin: 0; padding: 20px; background: var(--background); color: var(--text); display: flex; align-items: center; justify-content: center; min-height: 100vh; }
        .container { max-width: 600px; margin: 0 auto; background: var(--card-bg); padding: 3rem; border-radius: 16px; box-shadow: 0 4px 20px rgba(0,0,0,0.08); text-align: center; }
        h1 { color: var(--danger); margin-top: 0; font-size: 3rem; }
        p { font-size: 1.1rem; color: var(--text-light); }
        a { color: var(--primary); text-decoration: none; font-weight: 600; display: inline-block; margin-top: 1rem; padding: 0.75rem 1.5rem; background: var(--primary); color: white; border-radius: 8px; }
        a:hover { background: var(--primary-dark); }
    </style>
</head>
<body>
    <div class="container">
        <h1>500</h1>
        <p>Server error. Something went wrong on our end. Please try again later.</p>
        <a href="/">Return to Home</a>
    </div>
</body>
</html>'''
    })
    
    for template, content in basic_templates.items():
        template_path = f'templates/{template}'
        if not os.path.exists(template_path):
            with open(template_path, 'w') as f:
                f.write(content)
    
   # =========== PRODUCTION SERVER CONFIG ===========
if __name__ == '__main__':
    # Get port from environment variable
    port = int(os.environ.get('PORT', 10000))
    
    # Production vs Development
    if os.environ.get('FLASK_ENV') == 'production':
        # For production (Render), use 0.0.0.0
        app.run(host='0.0.0.0', port=port, debug=False)
    else:
        # For local development
        app.run(host='127.0.0.1', port=port, debug=True)