# app.py - UPDATED WITH GUIDE SERVING ROUTE
from flask import Flask, render_template, jsonify, request, redirect, url_for, send_from_directory, abort
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
load_dotenv()

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
        
        # Get list of guides for homepage
        guides = [
            {
                'title': 'How to Check SASSA Status Online',
                'description': 'Step-by-step guide for South Africans to check their SASSA grant status online.',
                'url': '/article/sassa-status-check',
                'image': 'sassa-status.jpg',
                'category': 'SASSA'
            },
            {
                'title': 'How to Make Money Online in South Africa',
                'description': 'Legitimate ways to earn money online from South Africa in 2026.',
                'url': '/article/make-money-online-sa',
                'image': 'make-money.jpg',
                'category': 'Finance'
            },
            {
                'title': 'How to Write a CV in South Africa',
                'description': 'Create a professional CV that stands out to South African employers.',
                'url': '/article/how-to-write-cv-sa',
                'image': 'cv-writing.jpg',
                'category': 'Career'
            },
            {
                'title': 'Best Job Websites in South Africa',
                'description': 'Top platforms to find employment opportunities in South Africa.',
                'url': '/article/best-job-websites-sa',
                'image': 'job-websites.jpg',
                'category': 'Career'
            },
            {
                'title': 'How Students Can Make Money Online',
                'description': 'Practical online income opportunities for South African students.',
                'url': '/article/students-make-money-online',
                'image': 'students-money.jpg',
                'category': 'Finance'
            },
            {
                'title': 'How to Start an Online Business in South Africa',
                'description': 'Complete guide to launching your online business in South Africa.',
                'url': '/article/start-online-business-sa',
                'image': 'online-business.jpg',
                'category': 'Business'
            }
        ]
        
        return render_template('index.html',
                             sports_data=live_data,
                             standings_data=standings_data,
                             guides=guides,
                             current_year=datetime.now().year,
                             page_title='SA Daily Portal 2026 - South African Information Hub',
                             page_description='Your complete guide to South African weather, SASSA grants, European football, and helpful how-to guides.',
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
                         page_title='South African Weather 2026 - Live Forecasts',
                         page_description='Real-time weather forecasts for South African cities. Hourly updates, 5-day forecast, and weather alerts.')

@app.route('/sassa')
def sassa():
    """SASSA page"""
    return render_template('sassa.html',
                         current_year=datetime.now().year,
                         page_title='SASSA 2026 - Grants and Payment Information',
                         page_description='Unofficial guide to SASSA grants, payment dates, application processes, and status checks for 2026.')

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
                             page_title='European Football 2026 - Live Scores and Standings',
                             page_description='Live European football scores, Premier League standings, upcoming fixtures, and match predictions.',
                             current_date=datetime.now().strftime('%d %B %Y'))
        
    except Exception as e:
        logger.error(f"Sports page error: {str(e)}")
        return render_template('sports.html',
                             current_year=datetime.now().year)

@app.route('/howto')
def howto():
    """How-to guides listing page"""
    guides = [
        {
            'title': 'How to Check SASSA Status Online',
            'description': 'Complete guide to checking your SASSA grant application status online.',
            'url': '/article/sassa-status-check',
            'category': 'SASSA',
            'read_time': '5 min'
        },
        {
            'title': 'How to Apply for SASSA SRD Grant',
            'description': 'Step-by-step application process for the SASSA R350 grant.',
            'url': '/article/sassa-srd-application',
            'category': 'SASSA',
            'read_time': '8 min'
        },
        {
            'title': 'How to Make Money Online in South Africa',
            'description': 'Legitimate ways to earn income online from South Africa.',
            'url': '/article/make-money-online-sa',
            'category': 'Finance',
            'read_time': '10 min'
        },
        {
            'title': 'How to Write a CV in South Africa',
            'description': 'Create a professional CV that gets you hired in South Africa.',
            'url': '/article/how-to-write-cv-sa',
            'category': 'Career',
            'read_time': '7 min'
        },
        {
            'title': 'Best Job Websites in South Africa',
            'description': 'Top platforms to find jobs in South Africa.',
            'url': '/article/best-job-websites-sa',
            'category': 'Career',
            'read_time': '6 min'
        },
        {
            'title': 'How Students Can Make Money Online',
            'description': 'Practical online income opportunities for students.',
            'url': '/article/students-make-money-online',
            'category': 'Finance',
            'read_time': '8 min'
        },
        {
            'title': 'How to Start an Online Business in South Africa',
            'description': 'Complete guide to launching your online business.',
            'url': '/article/start-online-business-sa',
            'category': 'Business',
            'read_time': '12 min'
        },
        {
            'title': 'Freelancing Guide for Beginners',
            'description': 'Start your freelancing career in South Africa.',
            'url': '/article/freelancing-guide-beginners',
            'category': 'Career',
            'read_time': '9 min'
        },
        {
            'title': 'NSFAS Application Guide',
            'description': 'How to apply for NSFAS funding in 2026.',
            'url': '/article/nsfas-application-guide',
            'category': 'Education',
            'read_time': '7 min'
        },
        {
            'title': 'Best Skills to Learn in 2026',
            'description': 'High-demand skills for South Africans.',
            'url': '/article/best-skills-learn-2026',
            'category': 'Career',
            'read_time': '8 min'
        }
    ]
    
    return render_template('howto.html',
                         guides=guides,
                         current_year=datetime.now().year,
                         page_title='How-To Guides for South Africans 2026',
                         page_description='Practical step-by-step guides for SASSA, careers, online income, and more.')

@app.route('/article/<article_name>')
def article(article_name):
    """Dynamic article rendering"""
    try:
        # List of valid articles for security
        valid_articles = [
            'sassa-status-check',
            'sassa-srd-application',
            'make-money-online-sa',
            'how-to-write-cv-sa',
            'best-job-websites-sa',
            'students-make-money-online',
            'start-online-business-sa',
            'freelancing-guide-beginners',
            'nsfas-application-guide',
            'best-skills-learn-2026',
            'become-freelancer-sa',
            'find-jobs-without-experience',
            'earn-money-student-sa'
        ]
        
        if article_name not in valid_articles:
            abort(404)
        
        # Get related articles for sidebar
        related_articles = []
        if article_name == 'sassa-status-check':
            related_articles = [
                {'title': 'How to Apply for SASSA SRD Grant', 'url': '/article/sassa-srd-application'},
                {'title': 'NSFAS Application Guide', 'url': '/article/nsfas-application-guide'}
            ]
        elif article_name == 'make-money-online-sa':
            related_articles = [
                {'title': 'How Students Can Make Money Online', 'url': '/article/students-make-money-online'},
                {'title': 'Freelancing Guide for Beginners', 'url': '/article/freelancing-guide-beginners'}
            ]
        elif article_name == 'how-to-write-cv-sa':
            related_articles = [
                {'title': 'Best Job Websites in South Africa', 'url': '/article/best-job-websites-sa'},
                {'title': 'Best Skills to Learn in 2026', 'url': '/article/best-skills-learn-2026'}
            ]
        
        return render_template(f'guides/{article_name}.html',
                             current_year=datetime.now().year,
                             related_articles=related_articles)
    except Exception as e:
        logger.error(f"Article error: {str(e)}")
        abort(404)

# =========== NEW ROUTE TO SERVE GUIDES DIRECTLY ===========
@app.route('/guides/<path:filename>')
def serve_guide(filename):
    """Serve guide HTML files from templates/guides folder"""
    try:
        # Ensure the filename ends with .html
        if not filename.endswith('.html'):
            filename += '.html'
        
        # Send the file from the templates/guides directory
        return send_from_directory('templates/guides', filename)
    except Exception as e:
        logger.error(f"Guide not found: {filename} - Error: {str(e)}")
        abort(404)

@app.route('/contact')
def contact():
    """Contact page"""
    return render_template('contact.html',
                         current_year=datetime.now().year,
                         page_title='Contact Developer - SA Daily Portal 2026',
                         page_description='Get in touch with the developer of SA Daily Portal for questions, suggestions, or feedback.')

@app.route('/about')
def about():
    """About page"""
    return render_template('about.html',
                         current_year=datetime.now().year,
                         page_title='About SA Daily Portal 2026',
                         page_description='Learn about SA Daily Portal, your source for South African information, weather, and guides.')

@app.route('/privacy-policy')
def privacy_policy():
    """Privacy policy page"""
    return render_template('privacy-policy.html',
                         current_year=datetime.now().year,
                         page_title='Privacy Policy - SA Daily Portal 2026',
                         page_description='Privacy policy for SA Daily Portal. Learn how we handle your data.')

@app.route('/terms')
def terms():
    """Terms of service page"""
    return render_template('terms.html',
                         current_year=datetime.now().year,
                         page_title='Terms of Service - SA Daily Portal 2026',
                         page_description='Terms and conditions for using SA Daily Portal.')

@app.route('/disclaimer')
def disclaimer():
    """Disclaimer page"""
    return render_template('disclaimer.html',
                         current_year=datetime.now().year,
                         page_title='Disclaimer - SA Daily Portal 2026',
                         page_description='Important disclaimer about the unofficial nature of information on SA Daily Portal.')

@app.route('/faq')
def faq():
    """FAQ page"""
    return render_template('faq.html',
                         current_year=datetime.now().year,
                         page_title='Frequently Asked Questions - SA Daily Portal 2026',
                         page_description='Answers to common questions about SA Daily Portal.')

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

@app.route('/privacy')
def redirect_privacy():
    return redirect(url_for('privacy_policy'))

# =========== APPLICATION START ===========

if __name__ == '__main__':
    # Create necessary directories
    required_dirs = ['templates', 'templates/guides', 'static/css', 'static/js', 'static/images']
    for dir_name in required_dirs:
        os.makedirs(dir_name, exist_ok=True)
    
    # Get port from environment variable
    port = int(os.environ.get('PORT', 10000))
    
    # Production vs Development
    if os.environ.get('FLASK_ENV') == 'production':
        # For production (Render), use 0.0.0.0
        app.run(host='0.0.0.0', port=port, debug=False)
    else:
        # For local development
        app.run(host='127.0.0.1', port=port, debug=True)