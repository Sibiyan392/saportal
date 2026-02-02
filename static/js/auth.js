// Authentication Modal Management
class AuthManager {
    constructor() {
        this.initAuthModal();
        this.initEventListeners();
        this.checkAuthState();
    }
    
    initAuthModal() {
        // Create auth modal HTML if it doesn't exist
        if (!document.getElementById('authModal')) {
            const modalHTML = `
            <div id="authModal" class="auth-modal" style="display: none;">
                <div class="auth-modal-content">
                    <div class="auth-modal-header">
                        <h2>Sign In / Sign Up</h2>
                        <button class="close-auth-modal">&times;</button>
                    </div>
                    <div class="auth-modal-body">
                        <div class="auth-tabs">
                            <button class="auth-tab active" data-tab="signin">Sign In</button>
                            <button class="auth-tab" data-tab="signup">Sign Up</button>
                        </div>
                        
                        <div class="auth-form" id="signinForm" style="display: block;">
                            <div class="form-group">
                                <label for="signinEmail">Email</label>
                                <input type="email" id="signinEmail" placeholder="your@email.com" required>
                            </div>
                            <div class="form-group">
                                <label for="signinPassword">Password</label>
                                <input type="password" id="signinPassword" placeholder="••••••••" required>
                            </div>
                            <button class="btn-primary btn-block" id="signinBtn">Sign In</button>
                            <div class="auth-links">
                                <a href="#" class="forgot-password">Forgot password?</a>
                            </div>
                        </div>
                        
                        <div class="auth-form" id="signupForm" style="display: none;">
                            <div class="form-group">
                                <label for="signupEmail">Email</label>
                                <input type="email" id="signupEmail" placeholder="your@email.com" required>
                            </div>
                            <div class="form-group">
                                <label for="signupPassword">Password</label>
                                <input type="password" id="signupPassword" placeholder="••••••••" minlength="6" required>
                            </div>
                            <div class="form-group">
                                <label for="confirmPassword">Confirm Password</label>
                                <input type="password" id="confirmPassword" placeholder="••••••••" minlength="6" required>
                            </div>
                            <div class="form-check">
                                <input type="checkbox" id="termsAgreement" required>
                                <label for="termsAgreement">
                                    I agree to the <a href="/terms" target="_blank">Terms of Service</a> and <a href="/privacy" target="_blank">Privacy Policy</a>
                                </label>
                            </div>
                            <button class="btn-primary btn-block" id="signupBtn">Create Account</button>
                        </div>
                        
                        <div class="auth-divider">
                            <span>Or continue as</span>
                        </div>
                        
                        <button class="btn-secondary btn-block" id="continueGuest">
                            <i class="fas fa-user-secret"></i> Guest User
                        </button>
                    </div>
                    <div class="auth-modal-footer">
                        <p>By continuing, you agree to our Terms and Privacy Policy</p>
                    </div>
                </div>
            </div>
            `;
            document.body.insertAdjacentHTML('beforeend', modalHTML);
        }
    }
    
    initEventListeners() {
        // Open auth modal
        document.addEventListener('click', (e) => {
            if (e.target.matches('[data-auth-action="open-modal"]')) {
                e.preventDefault();
                this.openAuthModal();
            }
        });
        
        // Close auth modal
        document.addEventListener('click', (e) => {
            if (e.target.closest('.close-auth-modal') || 
                (e.target.id === 'authModal' && e.target.classList.contains('auth-modal'))) {
                this.closeAuthModal();
            }
        });
        
        // Tab switching
        document.addEventListener('click', (e) => {
            if (e.target.classList.contains('auth-tab')) {
                this.switchAuthTab(e.target);
            }
        });
        
        // Sign in button
        document.getElementById('signinBtn')?.addEventListener('click', () => this.signIn());
        
        // Sign up button
        document.getElementById('signupBtn')?.addEventListener('click', () => this.signUp());
        
        // Continue as guest
        document.getElementById('continueGuest')?.addEventListener('click', () => this.continueAsGuest());
        
        // Sign out
        document.addEventListener('click', (e) => {
            if (e.target.matches('[data-auth-action="signout"]')) {
                e.preventDefault();
                this.signOut();
            }
        });
        
        // Close on escape
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && document.getElementById('authModal').style.display === 'block') {
                this.closeAuthModal();
            }
        });
    }
    
    openAuthModal() {
        const modal = document.getElementById('authModal');
        modal.style.display = 'block';
        document.body.style.overflow = 'hidden';
        
        // Reset forms
        this.resetAuthForms();
        
        // Focus on first input
        setTimeout(() => {
            document.getElementById('signinEmail')?.focus();
        }, 100);
    }
    
    closeAuthModal() {
        const modal = document.getElementById('authModal');
        modal.style.display = 'none';
        document.body.style.overflow = '';
        this.resetAuthForms();
    }
    
    switchAuthTab(clickedTab) {
        const tabs = document.querySelectorAll('.auth-tab');
        const forms = document.querySelectorAll('.auth-form');
        
        // Update active tab
        tabs.forEach(tab => tab.classList.remove('active'));
        clickedTab.classList.add('active');
        
        // Show corresponding form
        const tabType = clickedTab.getAttribute('data-tab');
        forms.forEach(form => {
            form.style.display = form.id === `${tabType}Form` ? 'block' : 'none';
        });
    }
    
    resetAuthForms() {
        // Reset all form inputs
        const inputs = document.querySelectorAll('#authModal input');
        inputs.forEach(input => {
            input.value = '';
            input.classList.remove('error');
        });
        
        // Clear error messages
        const errorElements = document.querySelectorAll('.auth-error');
        errorElements.forEach(el => el.remove());
        
        // Reset to sign in tab
        const signinTab = document.querySelector('[data-tab="signin"]');
        if (signinTab) this.switchAuthTab(signinTab);
    }
    
    showAuthError(formId, message) {
        // Remove existing errors
        const existingErrors = document.querySelectorAll(`#${formId} .auth-error`);
        existingErrors.forEach(el => el.remove());
        
        // Add new error
        const errorDiv = document.createElement('div');
        errorDiv.className = 'auth-error';
        errorDiv.innerHTML = `
            <div class="error-message">
                <i class="fas fa-exclamation-circle"></i>
                <span>${message}</span>
            </div>
        `;
        
        const form = document.getElementById(formId);
        form.insertBefore(errorDiv, form.firstChild);
        
        // Scroll to error
        errorDiv.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }
    
    async signIn() {
        const email = document.getElementById('signinEmail').value.trim();
        const password = document.getElementById('signinPassword').value;
        
        if (!email || !password) {
            this.showAuthError('signinForm', 'Please enter both email and password');
            return;
        }
        
        const signinBtn = document.getElementById('signinBtn');
        const originalText = signinBtn.textContent;
        signinBtn.textContent = 'Signing in...';
        signinBtn.disabled = true;
        
        try {
            const result = await window.firebaseAuth.signInWithEmail(email, password);
            
            if (result.success) {
                this.closeAuthModal();
                this.showNotification('Signed in successfully!', 'success');
                // Update UI
                window.firebaseAuth.updateUIForUser(result.user);
            } else {
                this.showAuthError('signinForm', result.error || 'Sign in failed');
            }
        } catch (error) {
            this.showAuthError('signinForm', error.message);
        } finally {
            signinBtn.textContent = originalText;
            signinBtn.disabled = false;
        }
    }
    
    async signUp() {
        const email = document.getElementById('signupEmail').value.trim();
        const password = document.getElementById('signupPassword').value;
        const confirmPassword = document.getElementById('confirmPassword').value;
        const termsAgreed = document.getElementById('termsAgreement').checked;
        
        // Validation
        if (!email || !password || !confirmPassword) {
            this.showAuthError('signupForm', 'Please fill in all fields');
            return;
        }
        
        if (password !== confirmPassword) {
            this.showAuthError('signupForm', 'Passwords do not match');
            return;
        }
        
        if (password.length < 6) {
            this.showAuthError('signupForm', 'Password must be at least 6 characters');
            return;
        }
        
        if (!termsAgreed) {
            this.showAuthError('signupForm', 'You must agree to the Terms and Privacy Policy');
            return;
        }
        
        const signupBtn = document.getElementById('signupBtn');
        const originalText = signupBtn.textContent;
        signupBtn.textContent = 'Creating Account...';
        signupBtn.disabled = true;
        
        try {
            const result = await window.firebaseAuth.signUpWithEmail(email, password);
            
            if (result.success) {
                this.closeAuthModal();
                this.showNotification('Account created successfully!', 'success');
                // Update UI
                window.firebaseAuth.updateUIForUser(result.user);
            } else {
                this.showAuthError('signupForm', result.error || 'Sign up failed');
            }
        } catch (error) {
            this.showAuthError('signupForm', error.message);
        } finally {
            signupBtn.textContent = originalText;
            signupBtn.disabled = false;
        }
    }
    
    async continueAsGuest() {
        try {
            await window.firebaseAuth.signInAnonymously();
            this.closeAuthModal();
            this.showNotification('Continuing as guest user', 'info');
        } catch (error) {
            this.showAuthError('signinForm', 'Failed to continue as guest');
        }
    }
    
    async signOut() {
        if (confirm('Are you sure you want to sign out?')) {
            const success = await window.firebaseAuth.signOutUser();
            if (success) {
                this.showNotification('Signed out successfully', 'info');
                // Refresh page to update state
                setTimeout(() => location.reload(), 1000);
            }
        }
    }
    
    showNotification(message, type = 'info') {
        // Remove existing notification
        const existingNotification = document.querySelector('.auth-notification');
        if (existingNotification) existingNotification.remove();
        
        // Create notification
        const notification = document.createElement('div');
        notification.className = `auth-notification auth-notification-${type}`;
        notification.innerHTML = `
            <div class="notification-content">
                <i class="fas fa-${type === 'success' ? 'check-circle' : 'info-circle'}"></i>
                <span>${message}</span>
            </div>
            <button class="close-notification">&times;</button>
        `;
        
        document.body.appendChild(notification);
        
        // Show notification
        setTimeout(() => notification.classList.add('show'), 10);
        
        // Auto remove after 5 seconds
        setTimeout(() => {
            notification.classList.remove('show');
            setTimeout(() => notification.remove(), 300);
        }, 5000);
        
        // Close button
        notification.querySelector('.close-notification').addEventListener('click', () => {
            notification.classList.remove('show');
            setTimeout(() => notification.remove(), 300);
        });
    }
    
    checkAuthState() {
        // Check if user needs to sign in for certain actions
        document.addEventListener('click', (e) => {
            const authRequiredElement = e.target.closest('[data-auth-required]');
            
            if (authRequiredElement && !window.firebaseAuth.auth.currentUser) {
                e.preventDefault();
                e.stopPropagation();
                
                const action = authRequiredElement.getAttribute('data-auth-required');
                const message = authRequiredElement.getAttribute('data-auth-message') || 
                              'Please sign in to access this feature';
                
                this.showNotification(message, 'warning');
                this.openAuthModal();
                
                // Log event
                if (window.gtag) {
                    window.gtag('event', 'auth_required_click', {
                        'action': action,
                        'page_location': window.location.pathname
                    });
                }
            }
        });
    }
}

// Initialize auth manager when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.authManager = new AuthManager();
});