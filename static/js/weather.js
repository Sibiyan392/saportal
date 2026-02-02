// Modern Weather Page with Automatic Location Detection
class WeatherManager {
    constructor() {
        this.currentLocation = null;
        this.weatherData = null;
        this.savedLocations = [];
        this.geocoder = null;
        this.autocomplete = null;
        this.isLoading = false;
        
        this.initWeatherPage();
        this.initEventListeners();
        this.initAutocomplete();
        this.attemptAutoLocation();
    }
    
    initWeatherPage() {
        // Create loading overlay
        this.createLoadingOverlay();
        
        // Create weather UI elements if they don't exist
        this.createWeatherUI();
        
        // Check for saved locations
        this.loadSavedLocations();
    }
    
    createLoadingOverlay() {
        const overlay = document.createElement('div');
        overlay.id = 'weatherLoading';
        overlay.className = 'weather-loading-overlay';
        overlay.innerHTML = `
            <div class="weather-loading-content">
                <div class="weather-spinner">
                    <div class="weather-spinner-circle"></div>
                </div>
                <p>Detecting your location...</p>
                <button class="btn-secondary skip-location">Enter location manually</button>
            </div>
        `;
        document.body.appendChild(overlay);
    }
    
    createWeatherUI() {
        // Create main weather container if it doesn't exist
        if (!document.getElementById('weatherContainer')) {
            const weatherHTML = `
            <div class="weather-container" id="weatherContainer">
                <div class="weather-header">
                    <h1><i class="fas fa-sun"></i> South African Weather</h1>
                    <p class="weather-subtitle">Real-time weather for your exact location</p>
                </div>
                
                <div class="weather-search-section">
                    <div class="location-input-group">
                        <div class="input-with-icon">
                            <i class="fas fa-map-marker-alt"></i>
                            <input type="text" 
                                   id="locationInput" 
                                   placeholder="Enter your exact location in South Africa..."
                                   autocomplete="off">
                        </div>
                        <button class="btn-primary" id="searchWeather">
                            <i class="fas fa-search"></i> Get Weather
                        </button>
                        <button class="btn-secondary" id="useMyLocation">
                            <i class="fas fa-location-crosshairs"></i> Use My Location
                        </button>
                    </div>
                    <div class="location-hint">
                        <i class="fas fa-info-circle"></i>
                        <span>We need your exact location for accurate weather. No preset cities allowed.</span>
                    </div>
                </div>
                
                <div class="weather-display" id="weatherDisplay" style="display: none;">
                    <div class="current-weather-card">
                        <div class="current-weather-header">
                            <div class="location-info">
                                <h2 id="currentLocation">--</h2>
                                <div class="location-actions">
                                    <button class="btn-icon save-location-btn" title="Save location">
                                        <i class="far fa-bookmark"></i>
                                    </button>
                                    <button class="btn-icon share-weather-btn" title="Share weather">
                                        <i class="fas fa-share-alt"></i>
                                    </button>
                                </div>
                            </div>
                            <div class="current-temp" id="currentTemp">--°C</div>
                        </div>
                        
                        <div class="current-weather-details">
                            <div class="weather-condition">
                                <img id="weatherIcon" src="" alt="Weather icon">
                                <span id="weatherDescription">--</span>
                            </div>
                            
                            <div class="weather-stats-grid">
                                <div class="weather-stat">
                                    <i class="fas fa-thermometer-half"></i>
                                    <div>
                                        <span class="stat-label">Feels Like</span>
                                        <span class="stat-value" id="feelsLike">--°C</span>
                                    </div>
                                </div>
                                <div class="weather-stat">
                                    <i class="fas fa-tint"></i>
                                    <div>
                                        <span class="stat-label">Humidity</span>
                                        <span class="stat-value" id="humidity">--%</span>
                                    </div>
                                </div>
                                <div class="weather-stat">
                                    <i class="fas fa-wind"></i>
                                    <div>
                                        <span class="stat-label">Wind Speed</span>
                                        <span class="stat-value" id="windSpeed">-- km/h</span>
                                    </div>
                                </div>
                                <div class="weather-stat">
                                    <i class="fas fa-compress-alt"></i>
                                    <div>
                                        <span class="stat-label">Pressure</span>
                                        <span class="stat-value" id="pressure">-- hPa</span>
                                    </div>
                                </div>
                                <div class="weather-stat">
                                    <i class="fas fa-eye"></i>
                                    <div>
                                        <span class="stat-label">Visibility</span>
                                        <span class="stat-value" id="visibility">-- km</span>
                                    </div>
                                </div>
                                <div class="weather-stat">
                                    <i class="fas fa-sun"></i>
                                    <div>
                                        <span class="stat-label">Sunrise</span>
                                        <span class="stat-value" id="sunrise">--:--</span>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                    
                    <div class="forecast-section">
                        <h3>7-Day Forecast</h3>
                        <div class="forecast-grid" id="forecastGrid">
                            <!-- Forecast cards will be inserted here -->
                        </div>
                    </div>
                    
                    <div class="weather-extra-section">
                        <div class="weather-actions">
                            <button class="btn-action" id="loadsheddingBtn">
                                <i class="fas fa-bolt"></i>
                                <span>Check Loadshedding</span>
                            </button>
                            <button class="btn-action" id="uvIndexBtn">
                                <i class="fas fa-sun"></i>
                                <span>UV Index</span>
                            </button>
                            <button class="btn-action" id="airQualityBtn">
                                <i class="fas fa-wind"></i>
                                <span>Air Quality</span>
                            </button>
                            <button class="btn-action" onclick="window.print()">
                                <i class="fas fa-print"></i>
                                <span>Print Report</span>
                            </button>
                        </div>
                    </div>
                </div>
                
                <div class="weather-error" id="weatherError" style="display: none;">
                    <div class="error-card">
                        <i class="fas fa-exclamation-triangle"></i>
                        <h3>Unable to get weather</h3>
                        <p id="errorMessage">Please enter a valid South African location</p>
                        <button class="btn-primary" id="retryWeather">Try Again</button>
                    </div>
                </div>
            </div>
            `;
            
            const mainContent = document.querySelector('main') || document.body;
            mainContent.innerHTML = weatherHTML;
        }
    }
    
    initAutocomplete() {
        if (typeof google === 'undefined' || !google.maps) {
            console.warn('Google Maps API not loaded yet');
            setTimeout(() => this.initAutocomplete(), 1000);
            return;
        }
        
        const input = document.getElementById('locationInput');
        if (!input) return;
        
        // Restrict to South Africa
        const options = {
            types: ['(cities)'],
            componentRestrictions: { country: 'za' }
        };
        
        this.autocomplete = new google.maps.places.Autocomplete(input, options);
        
        this.autocomplete.addListener('place_changed', () => {
            const place = this.autocomplete.getPlace();
            if (place.geometry) {
                this.currentLocation = {
                    name: place.name,
                    lat: place.geometry.location.lat(),
                    lng: place.geometry.location.lng(),
                    address: place.formatted_address
                };
                this.fetchWeatherData();
            }
        });
    }
    
    initEventListeners() {
        // Search button
        document.getElementById('searchWeather')?.addEventListener('click', () => {
            const location = document.getElementById('locationInput').value.trim();
            if (location) {
                this.searchByLocationName(location);
            }
        });
        
        // Use my location button
        document.getElementById('useMyLocation')?.addEventListener('click', () => {
            this.getUserLocation();
        });
        
        // Enter key in location input
        document.getElementById('locationInput')?.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                const location = e.target.value.trim();
                if (location) {
                    this.searchByLocationName(location);
                }
            }
        });
        
        // Save location button
        document.addEventListener('click', (e) => {
            if (e.target.closest('.save-location-btn')) {
                this.saveCurrentLocation();
            }
            
            if (e.target.closest('.share-weather-btn')) {
                this.shareWeather();
            }
            
            if (e.target.closest('.skip-location')) {
                this.hideLoadingOverlay();
            }
            
            if (e.target.closest('#retryWeather')) {
                this.retryWeather();
            }
        });
        
        // Extra weather actions
        document.getElementById('loadsheddingBtn')?.addEventListener('click', () => {
            this.showLoadsheddingInfo();
        });
    }
    
    attemptAutoLocation() {
        if (navigator.geolocation) {
            this.showLoadingOverlay();
            
            navigator.geolocation.getCurrentPosition(
                (position) => {
                    this.handleGeolocationSuccess(position);
                },
                (error) => {
                    console.log('Geolocation error:', error);
                    this.handleGeolocationError(error);
                },
                {
                    enableHighAccuracy: true,
                    timeout: 10000,
                    maximumAge: 0
                }
            );
        } else {
            this.hideLoadingOverlay();
            this.showGeolocationError('Geolocation not supported by your browser');
        }
    }
    
    async handleGeolocationSuccess(position) {
        const lat = position.coords.latitude;
        const lng = position.coords.longitude;
        
        // Reverse geocode to get address
        try {
            const address = await this.reverseGeocode(lat, lng);
            
            this.currentLocation = {
                name: address.city || address.town || address.village || 'Your Location',
                lat: lat,
                lng: lng,
                address: address.display_name
            };
            
            // Update input field
            document.getElementById('locationInput').value = address.display_name;
            
            // Fetch weather data
            await this.fetchWeatherData();
            
            this.hideLoadingOverlay();
            
        } catch (error) {
            console.error('Reverse geocode error:', error);
            this.handleGeolocationError(error);
        }
    }
    
    async reverseGeocode(lat, lng) {
        // Using OpenStreetMap Nominatim for reverse geocoding (no API key needed)
        const url = `https://nominatim.openstreetmap.org/reverse?format=json&lat=${lat}&lon=${lng}&zoom=18&addressdetails=1`;
        
        const response = await fetch(url);
        const data = await response.json();
        
        return data;
    }
    
    handleGeolocationError(error) {
        this.hideLoadingOverlay();
        
        let errorMessage = 'Could not detect your location. ';
        
        switch(error.code) {
            case error.PERMISSION_DENIED:
                errorMessage += 'Please enable location permissions or enter your location manually.';
                break;
            case error.POSITION_UNAVAILABLE:
                errorMessage += 'Location information is unavailable.';
                break;
            case error.TIMEOUT:
                errorMessage += 'Location request timed out.';
                break;
            default:
                errorMessage += 'An unknown error occurred.';
        }
        
        this.showGeolocationError(errorMessage);
    }
    
    showGeolocationError(message) {
        const errorDiv = document.createElement('div');
        errorDiv.className = 'geolocation-error';
        errorDiv.innerHTML = `
            <div class="error-alert">
                <i class="fas fa-exclamation-circle"></i>
                <div>
                    <strong>Location Access Required</strong>
                    <p>${message}</p>
                    <p>Please enter your location manually for accurate weather information.</p>
                </div>
            </div>
        `;
        
        const searchSection = document.querySelector('.weather-search-section');
        if (searchSection) {
            searchSection.appendChild(errorDiv);
        }
    }
    
    showLoadingOverlay() {
        const overlay = document.getElementById('weatherLoading');
        if (overlay) {
            overlay.style.display = 'flex';
            document.body.style.overflow = 'hidden';
        }
    }
    
    hideLoadingOverlay() {
        const overlay = document.getElementById('weatherLoading');
        if (overlay) {
            overlay.style.display = 'none';
            document.body.style.overflow = '';
        }
    }
    
    async searchByLocationName(locationName) {
        if (!locationName) return;
        
        this.showLoadingOverlay();
        
        try {
            // First try to geocode the location
            const geocodeUrl = `https://nominatim.openstreetmap.org/search?format=json&q=${encodeURIComponent(locationName + ', South Africa')}&limit=1`;
            
            const response = await fetch(geocodeUrl);
            const data = await response.json();
            
            if (data && data.length > 0) {
                const result = data[0];
                this.currentLocation = {
                    name: locationName,
                    lat: parseFloat(result.lat),
                    lng: parseFloat(result.lon),
                    address: result.display_name
                };
                
                await this.fetchWeatherData();
            } else {
                throw new Error('Location not found in South Africa');
            }
            
        } catch (error) {
            this.showWeatherError(error.message);
        } finally {
            this.hideLoadingOverlay();
        }
    }
    
    async fetchWeatherData() {
        if (!this.currentLocation) return;
        
        this.isLoading = true;
        this.showLoadingOverlay();
        
        try {
            const response = await fetch(`/api/weather?lat=${this.currentLocation.lat}&lon=${this.currentLocation.lng}`);
            
            if (!response.ok) {
                throw new Error('Weather data not available');
            }
            
            const data = await response.json();
            
            if (data.error) {
                throw new Error(data.error);
            }
            
            this.weatherData = data;
            this.displayWeatherData();
            this.hideWeatherError();
            
            // Track weather search
            if (window.gtag) {
                window.gtag('event', 'weather_search', {
                    'location': this.currentLocation.name,
                    'latitude': this.currentLocation.lat,
                    'longitude': this.currentLocation.lng
                });
            }
            
        } catch (error) {
            console.error('Weather fetch error:', error);
            this.showWeatherError('Unable to fetch weather data. Please try another location.');
        } finally {
            this.isLoading = false;
            this.hideLoadingOverlay();
        }
    }
    
    displayWeatherData() {
        if (!this.weatherData) return;
        
        const display = document.getElementById('weatherDisplay');
        display.style.display = 'block';
        
        // Update current location
        document.getElementById('currentLocation').textContent = this.currentLocation.address;
        
        // Update current weather
        const current = this.weatherData.current;
        document.getElementById('currentTemp').textContent = `${Math.round(current.temp)}°C`;
        document.getElementById('feelsLike').textContent = `${Math.round(current.feels_like)}°C`;
        document.getElementById('humidity').textContent = `${current.humidity}%`;
        document.getElementById('windSpeed').textContent = `${Math.round(current.wind_speed * 3.6)} km/h`;
        document.getElementById('pressure').textContent = `${current.pressure} hPa`;
        document.getElementById('visibility').textContent = `${current.visibility.toFixed(1)} km`;
        document.getElementById('sunrise').textContent = current.sunrise;
        
        // Update weather description and icon
        document.getElementById('weatherDescription').textContent = 
            current.description.charAt(0).toUpperCase() + current.description.slice(1);
        
        const weatherIcon = document.getElementById('weatherIcon');
        weatherIcon.src = `https://openweathermap.org/img/wn/${current.icon}@2x.png`;
        weatherIcon.alt = current.description;
        
        // Update forecast
        this.displayForecast();
    }
    
    displayForecast() {
        const forecastGrid = document.getElementById('forecastGrid');
        if (!forecastGrid || !this.weatherData.forecast) return;
        
        forecastGrid.innerHTML = '';
        
        this.weatherData.forecast.forEach((day, index) => {
            const date = new Date(day.date);
            const dayName = date.toLocaleDateString('en-ZA', { weekday: 'short' });
            const dayNumber = date.getDate();
            const month = date.toLocaleDateString('en-ZA', { month: 'short' });
            
            const forecastCard = document.createElement('div');
            forecastCard.className = 'forecast-card';
            forecastCard.innerHTML = `
                <div class="forecast-date">
                    <div class="forecast-day">${dayName}</div>
                    <div class="forecast-date-num">${dayNumber} ${month}</div>
                </div>
                <div class="forecast-icon">
                    <img src="https://openweathermap.org/img/wn/${day.icon}.png" alt="${day.description}">
                </div>
                <div class="forecast-temp">${Math.round(day.temp)}°C</div>
                <div class="forecast-desc">${day.description}</div>
                <div class="forecast-details">
                    <div class="forecast-detail">
                        <i class="fas fa-tint"></i>
                        <span>${day.humidity}%</span>
                    </div>
                    <div class="forecast-detail">
                        <i class="fas fa-wind"></i>
                        <span>${Math.round(day.wind_speed * 3.6)} km/h</span>
                    </div>
                </div>
            `;
            
            forecastGrid.appendChild(forecastCard);
        });
    }
    
    showWeatherError(message) {
        const errorDiv = document.getElementById('weatherError');
        const errorMessage = document.getElementById('errorMessage');
        
        if (errorDiv && errorMessage) {
            errorMessage.textContent = message;
            errorDiv.style.display = 'block';
            
            // Hide weather display
            document.getElementById('weatherDisplay').style.display = 'none';
        }
    }
    
    hideWeatherError() {
        const errorDiv = document.getElementById('weatherError');
        if (errorDiv) {
            errorDiv.style.display = 'none';
        }
    }
    
    retryWeather() {
        if (this.currentLocation) {
            this.fetchWeatherData();
        } else {
            this.hideWeatherError();
        }
    }
    
    async saveCurrentLocation() {
        if (!this.currentLocation || !window.firebaseAuth?.auth.currentUser) {
            this.showNotification('Please sign in to save locations', 'warning');
            return;
        }
        
        try {
            const user = window.firebaseAuth.auth.currentUser;
            const userRef = window.firebaseAuth.db.collection('users').doc(user.uid);
            
            await userRef.update({
                'savedLocations': firebase.firestore.FieldValue.arrayUnion({
                    name: this.currentLocation.name,
                    address: this.currentLocation.address,
                    coordinates: {
                        lat: this.currentLocation.lat,
                        lng: this.currentLocation.lng
                    },
                    savedAt: firebase.firestore.FieldValue.serverTimestamp()
                })
            });
            
            this.showNotification('Location saved to your profile!', 'success');
            
        } catch (error) {
            console.error('Error saving location:', error);
            this.showNotification('Failed to save location', 'error');
        }
    }
    
    async loadSavedLocations() {
        if (!window.firebaseAuth?.auth.currentUser || !window.firebaseAuth.db) return;
        
        try {
            const user = window.firebaseAuth.auth.currentUser;
            const userRef = window.firebaseAuth.db.collection('users').doc(user.uid);
            const doc = await userRef.get();
            
            if (doc.exists) {
                const data = doc.data();
                this.savedLocations = data.savedLocations || [];
                
                // Display saved locations if any
                if (this.savedLocations.length > 0) {
                    this.displaySavedLocations();
                }
            }
        } catch (error) {
            console.error('Error loading saved locations:', error);
        }
    }
    
    displaySavedLocations() {
        // Create saved locations dropdown or section
        // Implementation depends on UI design
    }
    
    async shareWeather() {
        if (!this.weatherData || !this.currentLocation) return;
        
        const current = this.weatherData.current;
        const message = `🌤️ Weather in ${this.currentLocation.name}: ${current.temp}°C, ${current.description}. Check more details at ${window.location.origin}`;
        
        if (navigator.share) {
            try {
                await navigator.share({
                    title: 'Current Weather',
                    text: message,
                    url: window.location.href
                });
            } catch (error) {
                console.log('Share cancelled:', error);
            }
        } else {
            // Fallback: Copy to clipboard
            navigator.clipboard.writeText(message)
                .then(() => this.showNotification('Weather copied to clipboard!', 'success'))
                .catch(() => this.showNotification('Failed to copy weather', 'error'));
        }
    }
    
    showLoadsheddingInfo() {
        if (!this.currentLocation) {
            this.showNotification('Please select a location first', 'warning');
            return;
        }
        
        // Implement loadshedding schedule integration
        // This would typically use EskomSePush API or similar
        // For now, show a placeholder
        const loadsheddingInfo = `
            <div class="loadshedding-modal">
                <h3>Loadshedding Schedule</h3>
                <p>Loadshedding information for ${this.currentLocation.name}</p>
                <div class="loadshedding-status">
                    <div class="status-indicator status-none"></div>
                    <p>No loadshedding currently</p>
                </div>
                <p class="loadshedding-note">
                    <i class="fas fa-info-circle"></i>
                    Loadshedding schedules change frequently. Check with your local municipality for the most accurate information.
                </p>
            </div>
        `;
        
        this.showModal('Loadshedding Info', loadsheddingInfo);
    }
    
    showModal(title, content) {
        // Create and show modal
        const modal = document.createElement('div');
        modal.className = 'weather-modal';
        modal.innerHTML = `
            <div class="weather-modal-content">
                <div class="weather-modal-header">
                    <h3>${title}</h3>
                    <button class="close-modal">&times;</button>
                </div>
                <div class="weather-modal-body">
                    ${content}
                </div>
            </div>
        `;
        
        document.body.appendChild(modal);
        
        // Show modal
        setTimeout(() => modal.classList.add('show'), 10);
        
        // Close button
        modal.querySelector('.close-modal').addEventListener('click', () => {
            modal.classList.remove('show');
            setTimeout(() => modal.remove(), 300);
        });
        
        // Close on background click
        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                modal.classList.remove('show');
                setTimeout(() => modal.remove(), 300);
            }
        });
    }
    
    showNotification(message, type = 'info') {
        // Similar to auth notification
        const notification = document.createElement('div');
        notification.className = `weather-notification notification-${type}`;
        notification.innerHTML = `
            <div class="notification-content">
                <i class="fas fa-${type === 'success' ? 'check-circle' : 'info-circle'}"></i>
                <span>${message}</span>
            </div>
            <button class="close-notification">&times;</button>
        `;
        
        document.body.appendChild(notification);
        
        setTimeout(() => notification.classList.add('show'), 10);
        
        setTimeout(() => {
            notification.classList.remove('show');
            setTimeout(() => notification.remove(), 300);
        }, 5000);
        
        notification.querySelector('.close-notification').addEventListener('click', () => {
            notification.classList.remove('show');
            setTimeout(() => notification.remove(), 300);
        });
    }
    
    getUserLocation() {
        if (navigator.geolocation) {
            this.showLoadingOverlay();
            
            navigator.geolocation.getCurrentPosition(
                (position) => {
                    this.handleGeolocationSuccess(position);
                },
                (error) => {
                    this.handleGeolocationError(error);
                },
                {
                    enableHighAccuracy: true,
                    timeout: 10000
                }
            );
        } else {
            this.showNotification('Geolocation not supported', 'error');
        }
    }
}

// Initialize weather manager when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    // Load Google Maps API for autocomplete
    const script = document.createElement('script');
    script.src = `https://maps.googleapis.com/maps/api/js?key=AIzaSyB6cDIaPyXSEM05JiFsMolqAb2NhJIUoW4&libraries=places&callback=initWeather`;
    script.async = true;
    script.defer = true;
    document.head.appendChild(script);
    
    window.initWeather = function() {
        window.weatherManager = new WeatherManager();
    };
});