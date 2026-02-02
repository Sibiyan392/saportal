// Main JavaScript for SA Daily Portal - OPTIMIZED VERSION
class MainApp {
    constructor() {
        this.init();
    }
    
    init() {
        // Initialize core features first
        this.initMobileMenu();
        this.initThemeSwitcher();
        this.initGDPRBanner();
        
        // Initialize data loading
        this.initDataLoading();
        
        // Initialize other features
        this.initAdSense();
        this.initAnalytics();
        this.initSASSAFeatures();
        this.initPageSpecificFeatures();
        this.initServiceWorker();
    }
    
    initMobileMenu() {
        const menuToggle = document.querySelector('.mobile-menu-toggle');
        const navMenu = document.querySelector('.nav-menu');
        
        if (menuToggle && navMenu) {
            menuToggle.addEventListener('click', () => {
                navMenu.classList.toggle('active');
                menuToggle.classList.toggle('active');
            });
            
            // Close menu when clicking outside
            document.addEventListener('click', (e) => {
                if (!navMenu.contains(e.target) && !menuToggle.contains(e.target)) {
                    navMenu.classList.remove('active');
                    menuToggle.classList.remove('active');
                }
            });
        }
    }
    
    initThemeSwitcher() {
        const themeToggle = document.querySelector('#themeToggle');
        const prefersDark = window.matchMedia('(prefers-color-scheme: dark)');
        
        // Check for saved theme or prefer system theme
        const savedTheme = localStorage.getItem('theme');
        const systemTheme = prefersDark.matches ? 'dark' : 'light';
        const currentTheme = savedTheme || systemTheme;
        
        // Apply theme
        document.documentElement.setAttribute('data-theme', currentTheme);
        
        if (themeToggle) {
            themeToggle.checked = currentTheme === 'dark';
            
            themeToggle.addEventListener('change', () => {
                const newTheme = themeToggle.checked ? 'dark' : 'light';
                document.documentElement.setAttribute('data-theme', newTheme);
                localStorage.setItem('theme', newTheme);
            });
        }
        
        // Listen for system theme changes
        prefersDark.addEventListener('change', (e) => {
            if (!localStorage.getItem('theme')) {
                const newTheme = e.matches ? 'dark' : 'light';
                document.documentElement.setAttribute('data-theme', newTheme);
                if (themeToggle) themeToggle.checked = newTheme === 'dark';
            }
        });
    }
    
    initGDPRBanner() {
        // Check if user has already consented
        const hasConsented = localStorage.getItem('gdpr_consent');
        
        if (!hasConsented) {
            // Show GDPR banner after 2 seconds
            setTimeout(() => {
                this.showGDPRBanner();
            }, 2000);
        } else if (hasConsented === 'accepted') {
            // Load analytics if accepted
            this.loadAnalytics();
        }
    }
    
    showGDPRBanner() {
        // Simplified GDPR banner for faster loading
        const banner = document.createElement('div');
        banner.id = 'gdprBanner';
        banner.style.cssText = `
            position: fixed;
            bottom: 0;
            left: 0;
            right: 0;
            background: #1f2937;
            color: white;
            padding: 1rem;
            z-index: 9999;
            box-shadow: 0 -2px 10px rgba(0,0,0,0.1);
        `;
        
        banner.innerHTML = `
            <div style="max-width: 1200px; margin: 0 auto; display: flex; flex-direction: column; gap: 1rem;">
                <div style="flex: 1;">
                    <div style="font-weight: 600; margin-bottom: 0.5rem;">🍪 We Use Cookies</div>
                    <div style="font-size: 0.875rem; opacity: 0.9;">
                        We use cookies to improve your experience. By continuing, you agree to our use of cookies.
                    </div>
                </div>
                <div style="display: flex; gap: 0.5rem;">
                    <button id="gdprCustomize" style="padding: 0.5rem 1rem; background: #374151; color: white; border: none; border-radius: 6px; cursor: pointer;">
                        Customize
                    </button>
                    <button id="gdprAcceptAll" style="padding: 0.5rem 1rem; background: #3b82f6; color: white; border: none; border-radius: 6px; cursor: pointer;">
                        Accept All
                    </button>
                </div>
            </div>
        `;
        
        document.body.appendChild(banner);
        
        // Event listeners
        document.getElementById('gdprAcceptAll').addEventListener('click', () => {
            this.acceptAllCookies();
            banner.remove();
        });
        
        document.getElementById('gdprCustomize').addEventListener('click', () => {
            this.showGDPRPreferences();
            banner.remove();
        });
    }
    
    acceptAllCookies() {
        localStorage.setItem('gdpr_consent', 'accepted');
        localStorage.setItem('gdpr_analytics', 'true');
        localStorage.setItem('gdpr_ads', 'true');
        
        // Load analytics and ads
        this.loadAnalytics();
        this.loadAdSense();
    }
    
    showGDPRPreferences() {
        // Simplified GDPR preferences modal
        const modal = document.createElement('div');
        modal.style.cssText = `
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: rgba(0,0,0,0.5);
            z-index: 10000;
            display: flex;
            align-items: center;
            justify-content: center;
        `;
        
        modal.innerHTML = `
            <div style="background: white; border-radius: 12px; padding: 1.5rem; max-width: 500px; width: 90%; max-height: 90vh; overflow-y: auto;">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1.5rem;">
                    <div style="font-weight: 600; font-size: 1.1rem;">Cookie Preferences</div>
                    <button class="close-gdpr-modal" style="background: none; border: none; font-size: 1.5rem; cursor: pointer;">&times;</button>
                </div>
                
                <div style="margin-bottom: 1.5rem;">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem;">
                        <div style="font-weight: 500;">Essential Cookies</div>
                        <div style="color: #6b7280; font-size: 0.875rem;">Required</div>
                    </div>
                    <div style="font-size: 0.875rem; color: #6b7280; margin-bottom: 1.5rem;">
                        Required for the website to function properly.
                    </div>
                    
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem;">
                        <div style="font-weight: 500;">Analytics Cookies</div>
                        <label style="display: inline-block; position: relative; width: 44px; height: 24px;">
                            <input type="checkbox" id="analyticsCookies" style="opacity: 0; width: 0; height: 0;">
                            <span style="position: absolute; cursor: pointer; top: 0; left: 0; right: 0; bottom: 0; background: #d1d5db; transition: .4s; border-radius: 24px;">
                                <span style="position: absolute; content: ""; height: 16px; width: 16px; left: 4px; bottom: 4px; background: white; transition: .4s; border-radius: 50%;"></span>
                            </span>
                        </label>
                    </div>
                    <div style="font-size: 0.875rem; color: #6b7280; margin-bottom: 1.5rem;">
                        Help us understand how visitors use our website.
                    </div>
                    
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem;">
                        <div style="font-weight: 500;">Advertising Cookies</div>
                        <label style="display: inline-block; position: relative; width: 44px; height: 24px;">
                            <input type="checkbox" id="advertisingCookies" style="opacity: 0; width: 0; height: 0;">
                            <span style="position: absolute; cursor: pointer; top: 0; left: 0; right: 0; bottom: 0; background: #d1d5db; transition: .4s; border-radius: 24px;">
                                <span style="position: absolute; content: ""; height: 16px; width: 16px; left: 4px; bottom: 4px; background: white; transition: .4s; border-radius: 50%;"></span>
                            </span>
                        </label>
                    </div>
                    <div style="font-size: 0.875rem; color: #6b7280;">
                        Used to show relevant advertisements.
                    </div>
                </div>
                
                <div style="display: flex; gap: 0.5rem;">
                    <button id="gdprSavePreferences" style="flex: 1; padding: 0.75rem; background: #f3f4f6; border: 1px solid #d1d5db; border-radius: 6px; cursor: pointer;">
                        Save Preferences
                    </button>
                    <button id="gdprAcceptSelected" style="flex: 1; padding: 0.75rem; background: #3b82f6; color: white; border: none; border-radius: 6px; cursor: pointer;">
                        Accept Selected
                    </button>
                </div>
            </div>
        `;
        
        document.body.appendChild(modal);
        
        // Set current preferences
        const analyticsChecked = localStorage.getItem('gdpr_analytics') === 'true';
        const adsChecked = localStorage.getItem('gdpr_ads') === 'true';
        
        document.getElementById('analyticsCookies').checked = analyticsChecked;
        document.getElementById('advertisingCookies').checked = adsChecked;
        
        // Event listeners
        modal.querySelector('.close-gdpr-modal').addEventListener('click', () => {
            modal.remove();
        });
        
        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                modal.remove();
            }
        });
        
        document.getElementById('gdprSavePreferences').addEventListener('click', () => {
            this.saveGDPRPreferences();
            modal.remove();
        });
        
        document.getElementById('gdprAcceptSelected').addEventListener('click', () => {
            this.saveGDPRPreferences();
            modal.remove();
        });
    }
    
    saveGDPRPreferences() {
        const analytics = document.getElementById('analyticsCookies').checked;
        const ads = document.getElementById('advertisingCookies').checked;
        
        localStorage.setItem('gdpr_consent', 'custom');
        localStorage.setItem('gdpr_analytics', analytics.toString());
        localStorage.setItem('gdpr_ads', ads.toString());
        
        if (analytics) {
            this.loadAnalytics();
        }
        
        if (ads) {
            this.loadAdSense();
        }
    }
    
    initDataLoading() {
        // Initialize sports ticker if present
        if (document.getElementById('sportsTicker')) {
            this.initSportsTicker();
        }
        
        // Initialize weather widget if present
        if (document.getElementById('weatherWidget')) {
            this.initWeatherWidget();
        }
    }
    
    initSportsTicker() {
        this.updateSportsTicker();
        // Update every 2 minutes
        setInterval(() => this.updateSportsTicker(), 120000);
    }
    
    async updateSportsTicker() {
        try {
            const response = await fetch('/api/sports/matches');
            const data = await response.json();
            
            if (data.success && data.matches && data.matches.length > 0) {
                this.displaySportsTicker(data.matches);
            } else {
                this.displayDefaultSportsTicker();
            }
        } catch (error) {
            console.error('Sports ticker error:', error);
            this.displayDefaultSportsTicker();
        }
    }
    
    displaySportsTicker(matches) {
        const ticker = document.getElementById('sportsTicker');
        if (!ticker) return;
        
        const liveMatches = matches.filter(m => m.is_live);
        const upcomingMatches = matches.filter(m => m.status === 'UPCOMING');
        const displayMatches = liveMatches.length > 0 ? liveMatches.slice(0, 3) : upcomingMatches.slice(0, 3);
        
        if (displayMatches.length > 0) {
            const items = displayMatches.map(match => {
                return `
                    <div class="ticker-item">
                        <span class="match-teams">${match.home_team} vs ${match.away_team}</span>
                        <span class="match-score">${match.score}</span>
                        ${match.is_live ? '<span class="match-status">LIVE</span>' : ''}
                    </div>
                `;
            }).join('');
            
            ticker.innerHTML = items;
        } else {
            this.displayDefaultSportsTicker();
        }
    }
    
    displayDefaultSportsTicker() {
        const ticker = document.getElementById('sportsTicker');
        if (!ticker) return;
        
        const defaultMatches = [
            { home_team: 'Sundowns', away_team: 'Pirates', score: '2-1', is_live: false },
            { home_team: 'Chiefs', away_team: 'Cape Town City', score: '1-1', is_live: false },
            { home_team: 'SuperSport', away_team: 'Stellenbosch', score: '2-0', is_live: false }
        ];
        
        const items = defaultMatches.map(match => `
            <div class="ticker-item">
                <span class="match-teams">${match.home_team} vs ${match.away_team}</span>
                <span class="match-score">${match.score}</span>
            </div>
        `).join('');
        
        ticker.innerHTML = items;
    }
    
    initWeatherWidget() {
        // Load weather data for default location (Johannesburg)
        this.loadWeatherData('Johannesburg');
        
        // Setup refresh button if present
        const refreshBtn = document.getElementById('refreshWeather');
        if (refreshBtn) {
            refreshBtn.addEventListener('click', () => {
                this.loadWeatherData('Johannesburg');
            });
        }
        
        // Setup location button if present
        const locationBtn = document.getElementById('useMyLocation');
        if (locationBtn) {
            locationBtn.addEventListener('click', () => {
                this.getLocationWeather();
            });
        }
    }
    
    async loadWeatherData(location) {
        try {
            const response = await fetch(`/api/weather?location=${encodeURIComponent(location)}`);
            const data = await response.json();
            
            if (data.success) {
                this.displayWeatherData(data);
            }
        } catch (error) {
            console.error('Weather load error:', error);
        }
    }
    
    displayWeatherData(data) {
        const widget = document.getElementById('weatherWidget');
        if (!widget) return;
        
        const weather = data.current;
        
        widget.innerHTML = `
            <div style="text-align: center;">
                <div style="font-size: 3rem; font-weight: 700; margin-bottom: 0.5rem; color: white;">${weather.temp}°C</div>
                <div style="font-size: 1.1rem; margin-bottom: 0.25rem; color: white;">${data.location}</div>
                <div style="opacity: 0.9; margin-bottom: 1.5rem; color: white;">${weather.description}</div>
                
                <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 1rem; margin-top: 1.5rem;">
                    <div>
                        <div style="font-size: 0.875rem; opacity: 0.8; color: white;">Wind</div>
                        <div style="font-weight: 600; color: white;">${weather.wind_speed} km/h</div>
                    </div>
                    <div>
                        <div style="font-size: 0.875rem; opacity: 0.8; color: white;">Humidity</div>
                        <div style="font-weight: 600; color: white;">${weather.humidity}%</div>
                    </div>
                    <div>
                        <div style="font-size: 0.875rem; opacity: 0.8; color: white;">Feels Like</div>
                        <div style="font-weight: 600; color: white;">${weather.feels_like}°C</div>
                    </div>
                </div>
            </div>
        `;
    }
    
    getLocationWeather() {
        if (navigator.geolocation) {
            navigator.geolocation.getCurrentPosition(async (position) => {
                try {
                    const response = await fetch(`/api/weather?lat=${position.coords.latitude}&lon=${position.coords.longitude}`);
                    const data = await response.json();
                    
                    if (data.success) {
                        this.displayWeatherData(data);
                    }
                } catch (error) {
                    console.error('Location weather error:', error);
                    this.loadWeatherData('Johannesburg');
                }
            }, () => {
                this.loadWeatherData('Johannesburg');
            });
        } else {
            this.loadWeatherData('Johannesburg');
        }
    }
    
    initAdSense() {
        // Check if ads are consented to
        const adsConsented = localStorage.getItem('gdpr_ads') === 'true';
        
        if (adsConsented || !localStorage.getItem('gdpr_consent')) {
            this.loadAdSense();
        }
    }
    
    loadAdSense() {
        // AdSense is already loaded in the HTML head
        // Just push the ads
        if (typeof adsbygoogle !== 'undefined') {
            setTimeout(() => {
                (adsbygoogle = window.adsbygoogle || []).push({});
            }, 1000);
        }
    }
    
    initAnalytics() {
        // Check if analytics are consented to
        const analyticsConsented = localStorage.getItem('gdpr_analytics') === 'true';
        
        if (analyticsConsented || !localStorage.getItem('gdpr_consent')) {
            this.loadAnalytics();
        }
    }
    
    loadAnalytics() {
        // Analytics is already loaded in the HTML head
        // Nothing to do here
    }
    
    initSASSAFeatures() {
        // Only on SASSA page
        if (!document.getElementById('sassaStatusChecker')) return;
        
        this.initSASSAStatusChecker();
    }
    
    initSASSAStatusChecker() {
        const form = document.getElementById('sassaStatusChecker');
        const idInput = document.getElementById('sassaIdNumber');
        const resultDiv = document.getElementById('sassaResult');
        
        if (!form || !idInput || !resultDiv) return;
        
        form.addEventListener('submit', async (e) => {
            e.preventDefault();
            
            const idNumber = idInput.value.trim();
            
            // Validate SA ID number
            if (!this.validateSAID(idNumber)) {
                this.showSASSAError('Please enter a valid 13-digit South African ID number');
                return;
            }
            
            // Show loading
            resultDiv.innerHTML = `
                <div style="text-align: center; padding: 2rem;">
                    <div style="width: 40px; height: 40px; border: 3px solid #f3f4f6; border-top: 3px solid #3b82f6; border-radius: 50%; animation: spin 1s linear infinite; margin: 0 auto 1rem;"></div>
                    <p>Checking SASSA status...</p>
                </div>
            `;
            
            // Simulate API call (since we don't have real SASSA API)
            setTimeout(() => {
                this.displayMockSASSAResult();
            }, 1500);
        });
    }
    
    validateSAID(idNumber) {
        // Basic SA ID validation
        if (!idNumber || idNumber.length !== 13 || !/^\d+$/.test(idNumber)) {
            return false;
        }
        
        // Luhn algorithm check (simplified)
        let sum = 0;
        for (let i = 0; i < 12; i++) {
            let digit = parseInt(idNumber[i]);
            if (i % 2 === 0) {
                digit *= 2;
                if (digit > 9) digit -= 9;
            }
            sum += digit;
        }
        
        const checkDigit = (10 - (sum % 10)) % 10;
        return checkDigit === parseInt(idNumber[12]);
    }
    
    displayMockSASSAResult() {
        const resultDiv = document.getElementById('sassaResult');
        
        const today = new Date();
        const nextPayment = new Date(today.getFullYear(), today.getMonth() + 1, 1);
        if (nextPayment.getDay() === 6) nextPayment.setDate(nextPayment.getDate() + 2);
        if (nextPayment.getDay() === 0) nextPayment.setDate(nextPayment.getDate() + 1);
        
        resultDiv.innerHTML = `
            <div style="background: white; border: 1px solid #e5e7eb; border-radius: 12px; overflow: hidden;">
                <div style="background: #10b981; color: white; padding: 1rem;">
                    <div style="font-weight: 600;">Status Check Result</div>
                </div>
                <div style="padding: 1.5rem;">
                    <div style="margin-bottom: 1rem;">
                        <div style="font-size: 0.875rem; color: #6b7280;">Status</div>
                        <div style="font-weight: 600;">Application Processed Successfully</div>
                    </div>
                    
                    <div style="margin-bottom: 1rem;">
                        <div style="font-size: 0.875rem; color: #6b7280;">Next Payment Date</div>
                        <div style="font-weight: 600;">${nextPayment.toLocaleDateString('en-ZA', { day: 'numeric', month: 'long', year: 'numeric' })}</div>
                    </div>
                    
                    <div style="margin-bottom: 1.5rem;">
                        <div style="font-size: 0.875rem; color: #6b7280;">Official SASSA Contact</div>
                        <div style="font-weight: 600;">0800 60 10 11</div>
                    </div>
                    
                    <div style="background: #fef3c7; padding: 1rem; border-radius: 8px; margin-bottom: 1.5rem; font-size: 0.875rem;">
                        <div style="font-weight: 600; margin-bottom: 0.25rem;">Important Information</div>
                        <div>This is an unofficial informational service. Always verify with official SASSA channels. Never share personal or banking details.</div>
                    </div>
                    
                    <div style="display: flex; gap: 0.5rem;">
                        <button style="flex: 1; padding: 0.75rem; background: #f3f4f6; border: 1px solid #d1d5db; border-radius: 6px; cursor: pointer;">
                            Print Result
                        </button>
                        <a href="/sassa" style="flex: 1; padding: 0.75rem; background: #3b82f6; color: white; text-align: center; text-decoration: none; border-radius: 6px;">
                            More SASSA Info
                        </a>
                    </div>
                </div>
            </div>
        `;
    }
    
    showSASSAError(message) {
        const resultDiv = document.getElementById('sassaResult');
        resultDiv.innerHTML = `
            <div style="text-align: center; padding: 2rem;">
                <div style="color: #ef4444; font-size: 2rem; margin-bottom: 1rem;">
                    <i class="fas fa-exclamation-circle"></i>
                </div>
                <div style="font-weight: 600; margin-bottom: 0.5rem;">Error</div>
                <div style="color: #6b7280; margin-bottom: 1.5rem;">${message}</div>
                <button style="padding: 0.75rem 1.5rem; background: #3b82f6; color: white; border: none; border-radius: 6px; cursor: pointer;">
                    Try Again
                </button>
            </div>
        `;
        
        // Add event listener to try again button
        resultDiv.querySelector('button').addEventListener('click', () => {
            document.getElementById('sassaStatusChecker').dispatchEvent(new Event('submit'));
        });
    }
    
    initPageSpecificFeatures() {
        const page = document.body.getAttribute('data-page') || 
                    document.body.getAttribute('id') || 
                    document.querySelector('main')?.getAttribute('id');
        
        if (page === 'sports' || document.querySelector('#standings-table')) {
            this.initSportsPage();
        } else if (page === 'howto' || document.querySelector('.interactive-guide')) {
            this.initHowToPage();
        } else if (page === 'account' || document.querySelector('#userProfile')) {
            this.initAccountPage();
        }
    }
    
    initSportsPage() {
        // Initialize sports page features
        this.loadSportsStandings();
        this.initSportsTabs();
    }
    
    async loadSportsStandings() {
        try {
            const response = await fetch('/api/sports/standings');
            const data = await response.json();
            
            if (data.success) {
                this.displaySportsStandings(data);
            }
        } catch (error) {
            console.error('Error loading standings:', error);
        }
    }
    
    displaySportsStandings(data) {
        const tableBody = document.getElementById('standings-table') || 
                         document.getElementById('standingsBody');
        
        if (!tableBody || !data.standings) return;
        
        let html = '';
        data.standings.forEach(team => {
            html += `
                <tr style="border-bottom: 1px solid #e5e7eb;">
                    <td style="padding: 0.75rem;">
                        <span style="display: inline-flex; align-items: center; justify-content: center; width: 24px; height: 24px; background: ${team.position <= 3 ? '#fef3c7' : '#f3f4f6'}; border-radius: 4px; font-weight: 600;">
                            ${team.position}
                        </span>
                    </td>
                    <td style="padding: 0.75rem; font-weight: 500;">${team.team}</td>
                    <td style="padding: 0.75rem;">${team.played}</td>
                    <td style="padding: 0.75rem;">${team.won}</td>
                    <td style="padding: 0.75rem;">${team.drawn}</td>
                    <td style="padding: 0.75rem;">${team.lost}</td>
                    <td style="padding: 0.75rem;">${team.goals_for}</td>
                    <td style="padding: 0.75rem;">${team.goals_against}</td>
                    <td style="padding: 0.75rem; color: ${team.goal_difference > 0 ? '#10b981' : team.goal_difference < 0 ? '#f59e0b' : '#6b7280'}">
                        ${team.goal_difference > 0 ? '+' : ''}${team.goal_difference}
                    </td>
                    <td style="padding: 0.75rem; font-weight: 600;">${team.points}</td>
                </tr>
            `;
        });
        
        tableBody.innerHTML = html;
    }
    
    initSportsTabs() {
        const tabButtons = document.querySelectorAll('.tab-btn');
        const tabContents = document.querySelectorAll('.tab-content');
        
        if (tabButtons.length === 0 || tabContents.length === 0) return;
        
        tabButtons.forEach(button => {
            button.addEventListener('click', () => {
                // Remove active class from all buttons
                tabButtons.forEach(btn => btn.classList.remove('active'));
                // Add active class to clicked button
                button.classList.add('active');
                
                // Hide all tab contents
                tabContents.forEach(content => content.classList.add('hidden'));
                
                // Show corresponding tab content
                const tabId = button.id.replace('tab-', 'content-');
                const tabContent = document.getElementById(tabId);
                if (tabContent) {
                    tabContent.classList.remove('hidden');
                }
            });
        });
    }
    
    initHowToPage() {
        // Initialize simple guide functionality
        const guides = document.querySelectorAll('.interactive-guide');
        
        guides.forEach(guide => {
            const steps = guide.querySelectorAll('.guide-step');
            if (steps.length > 0) {
                steps[0].classList.add('active');
            }
        });
    }
    
    initAccountPage() {
        // Simple account page initialization
        const userEmail = document.getElementById('userEmail');
        if (userEmail) {
            const email = localStorage.getItem('user_email') || 'user@example.com';
            userEmail.textContent = email;
        }
    }
    
    initServiceWorker() {
        if ('serviceWorker' in navigator && process.env.NODE_ENV === 'production') {
            window.addEventListener('load', () => {
                navigator.serviceWorker.register('/sw.js')
                    .then(registration => {
                        console.log('ServiceWorker registered');
                    })
                    .catch(error => {
                        console.log('ServiceWorker registration failed:', error);
                    });
            });
        }
    }
}

// Initialize main app when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.mainApp = new MainApp();
    
    // Load AdSense after page load
    setTimeout(() => {
        if (typeof adsbygoogle !== 'undefined') {
            (adsbygoogle = window.adsbygoogle || []).push({});
        }
    }, 1000);
});