// Forbidden characters for username and password
const FORBIDDEN_CHARS = /[\@\#\$\\\\/\%\^\&\*\(\)\-\+\=]/g;

// Password strength requirements
const PASSWORD_REQUIREMENTS = {
    minLength: 8,
    hasUpperCase: /[A-Z]/,
    hasLowerCase: /[a-z]/,
    hasNumber: /[0-9]/,
    hasSpecialChar: /[@$!%*?&]/
};

let backgroundChangeInterval;
let token = null;

// Initialize background with random image
document.addEventListener('DOMContentLoaded', function() {
    initializeBackground();
    setupBackgroundRotation();
    setupEventListeners();

    // Check if already logged in
    checkExistingSession();
});

function checkExistingSession() {
    const savedToken = sessionStorage.getItem('token');
    if (savedToken) {
        // Verify token with server
        fetch('http://localhost:5000/api/auth/verify', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': 'Bearer ' + savedToken
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // Session is valid, redirect to report page
                window.location.href = 'report.html';
            } else {
                // Session invalid, clear storage
                sessionStorage.removeItem('token');
                sessionStorage.removeItem('username');
                sessionStorage.removeItem('isLoggedIn');
            }
        })
        .catch(() => {
            // Error checking session, clear storage
            sessionStorage.removeItem('token');
            sessionStorage.removeItem('username');
            sessionStorage.removeItem('isLoggedIn');
        });
    }
}

function initializeBackground() {
    const background = document.getElementById('background');
    const randomImageNum = Math.floor(Math.random() * 50) + 1;
    const imageUrl = `background/image${randomImageNum}.jpg`;
    background.style.backgroundImage = `url('${imageUrl}')`;
}

function getRandomBackgroundImage() {
    const randomImageNum = Math.floor(Math.random() * 50) + 1;
    return `background/image${randomImageNum}.jpg`;
}

function changeBackgroundImage() {
    const background = document.getElementById('background');
    const newImageUrl = getRandomBackgroundImage();
    background.style.backgroundImage = `url('${newImageUrl}')`;
}

function setupBackgroundRotation() {
    backgroundChangeInterval = setInterval(() => {
        changeBackgroundImage();
    }, 3000);
}

function setupEventListeners() {
    const passwordInput = document.getElementById('password');
    const usernameInput = document.getElementById('username');

    if (passwordInput) {
        passwordInput.addEventListener('focus', function() {
            document.getElementById('passwordRules').classList.add('show');
        });

        passwordInput.addEventListener('blur', function() {
            if (this.value.length === 0) {
                document.getElementById('passwordRules').classList.remove('show');
            }
        });

        passwordInput.addEventListener('input', function() {
            validatePasswordRules(this.value);
        });
    }

    if (usernameInput) {
        usernameInput.addEventListener('input', function() {
            if (this.classList.contains('error')) {
                clearError(this);
            }
        });
    }
}

function validatePasswordRules(password) {
    const rules = {
        length: { regex: /.{8,}/, element: document.getElementById('ruleLength') },
        uppercase: { regex: /[A-Z]/, element: document.getElementById('ruleUppercase') },
        lowercase: { regex: /[a-z]/, element: document.getElementById('ruleLowercase') },
        number: { regex: /[0-9]/, element: document.getElementById('ruleNumber') },
        special: { regex: /[@$!%*?&]/, element: document.getElementById('ruleSpecial') }
    };

    let allValid = true;
    for (const [key, rule] of Object.entries(rules)) {
        const isValid = rule.regex.test(password);
        rule.element.className = isValid ? 'valid' : 'invalid';
        if (!isValid) allValid = false;
    }
    return allValid;
}

function validateUsername(username) {
    if (!username.trim()) {
        return { valid: false, message: 'نام کاربری نمی‌تواند خالی باشد.' };
    }

    if (FORBIDDEN_CHARS.test(username)) {
        return {
            valid: false,
            message: 'نام کاربری نباید شامل کاراکترهای $ ،# ،@ و دیگر کاراکترهای خاص باشد.'
        };
    }

    return { valid: true, message: '' };
}

function validatePassword(password) {
    if (!password.trim()) {
        return { valid: false, message: 'رمز عبور نمی‌تواند خالی باشد.' };
    }

    const isValidLength = PASSWORD_REQUIREMENTS.minLength && password.length >= PASSWORD_REQUIREMENTS.minLength;
    const hasUpperCase = PASSWORD_REQUIREMENTS.hasUpperCase.test(password);
    const hasLowerCase = PASSWORD_REQUIREMENTS.hasLowerCase.test(password);
    const hasNumber = PASSWORD_REQUIREMENTS.hasNumber.test(password);
    const hasSpecialChar = PASSWORD_REQUIREMENTS.hasSpecialChar.test(password);

    if (!isValidLength || !hasUpperCase || !hasLowerCase || !hasNumber || !hasSpecialChar) {
        return { valid: false, message: 'رمز عبور قوانین را رعایت نمی‌کند.' };
    }

    return { valid: true, message: '' };
}

function clearErrorMessages() {
    document.getElementById('usernameError').textContent = '';
    document.getElementById('passwordError').textContent = '';
    document.getElementById('generalError').textContent = '';
    document.getElementById('generalError').style.display = 'none';
}

function showError(input, message) {
    input.classList.add('error');
    input.classList.remove('success');
    const errorEl = input.parentElement.querySelector('.error-message');
    if (errorEl) {
        errorEl.textContent = message;
        errorEl.classList.add('show');
    }
}

function clearError(input) {
    input.classList.remove('error');
    input.classList.remove('success');
    const errorEl = input.parentElement.querySelector('.error-message');
    if (errorEl) {
        errorEl.classList.remove('show');
    }
}

function markAsSuccess(input) {
    input.classList.add('success');
    input.classList.remove('error');
    const errorEl = input.parentElement.querySelector('.error-message');
    if (errorEl) {
        errorEl.classList.remove('show');
    }
}

function handleLogin(event) {
    event.preventDefault();

    clearErrorMessages();

    const usernameInput = document.getElementById('username');
    const passwordInput = document.getElementById('password');
    const username = usernameInput.value;
    const password = passwordInput.value;
    const loginBtn = document.querySelector('.login-btn');

    const usernameValidation = validateUsername(username);
    if (!usernameValidation.valid) {
        showError(usernameInput, usernameValidation.message);
        usernameInput.focus();
        return;
    }

    const passwordValidation = validatePassword(password);
    if (!passwordValidation.valid) {
        showError(passwordInput, passwordValidation.message);
        passwordInput.focus();
        document.getElementById('passwordRules').classList.add('show');
        return;
    }

    markAsSuccess(usernameInput);
    markAsSuccess(passwordInput);

    const loadingOverlay = document.getElementById('loading-overlay');
    loadingOverlay.classList.remove('hidden');
    loginBtn.disabled = true;

    // Send login request to server
    fetch('http://localhost:5000/api/auth/login', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            username: username,
            password: password
        })
    })
    .then(response => response.json())
    .then(data => {
        loadingOverlay.classList.add('hidden');
        loginBtn.disabled = false;

        if (data.success) {
            // Store token and session data
            sessionStorage.setItem('token', data.token);
            sessionStorage.setItem('username', data.username);
            sessionStorage.setItem('isLoggedIn', 'true');

            document.querySelector('.login-box').style.border = '3px solid #2ecc71';

            clearInterval(backgroundChangeInterval);

            setTimeout(() => {
                window.location.href = 'report.html';
            }, 1000);
        } else {
            const generalError = document.getElementById('generalError');
            generalError.textContent = data.message || 'نام کاربری یا رمز عبور اشتباه است';
            generalError.style.display = 'block';
        }
    })
    .catch(error => {
        loadingOverlay.classList.add('hidden');
        loginBtn.disabled = false;
        const generalError = document.getElementById('generalError');
        generalError.textContent = 'خطا در اتصال به سرور. لطفاً دوباره تلاش کنید.';
        generalError.style.display = 'block';
        console.error('Login error:', error);
    });
}
