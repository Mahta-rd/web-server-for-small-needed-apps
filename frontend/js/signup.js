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

// Initialize background with random image
document.addEventListener('DOMContentLoaded', function() {
    initializeBackground();
    setupBackgroundRotation();
    setupEventListeners();
});

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
    const confirmPasswordInput = document.getElementById('confirmPassword');

    // Password focus event - show rules
    if (passwordInput) {
        passwordInput.addEventListener('focus', function() {
            document.getElementById('passwordRules').classList.add('show');
        });

        // Password blur event - hide rules if empty
        passwordInput.addEventListener('blur', function() {
            if (this.value.length === 0) {
                document.getElementById('passwordRules').classList.remove('show');
            }
        });

        // Password input event - validate in real-time
        passwordInput.addEventListener('input', function() {
            validatePasswordRules(this.value);
            // Clear confirm password error when password changes
            const confirmError = document.getElementById('confirmPasswordError');
            if (confirmError.textContent) {
                const confirmInput = document.getElementById('confirmPassword');
                if (confirmInput.value) {
                    validateConfirmPassword(confirmInput.value, this.value);
                }
            }
        });
    }

    // Confirm password validation
    if (confirmPasswordInput) {
        confirmPasswordInput.addEventListener('input', function() {
            const password = document.getElementById('password').value;
            validateConfirmPassword(this.value, password);
        });
    }

    // Username input event - clear error on change
    if (usernameInput) {
        usernameInput.addEventListener('input', function() {
            if (this.classList.contains('error')) {
                clearError(this);
            }
            // Real-time username validation
            const result = validateUsername(this.value);
            if (!result.valid && this.value.length > 0) {
                showError(this, result.message);
            } else if (this.value.length > 0) {
                clearError(this);
            }
        });
    }
}

function validateConfirmPassword(confirmPassword, password) {
    const errorElement = document.getElementById('confirmPasswordError');
    const inputElement = document.getElementById('confirmPassword');

    if (!confirmPassword) {
        errorElement.textContent = '';
        errorElement.classList.remove('show');
        inputElement.classList.remove('error', 'success');
        return;
    }

    if (confirmPassword !== password) {
        errorElement.textContent = 'رمز عبور و تایید آن باید یکسان باشند';
        errorElement.classList.add('show');
        inputElement.classList.add('error');
        inputElement.classList.remove('success');
        return false;
    } else {
        errorElement.textContent = '';
        errorElement.classList.remove('show');
        inputElement.classList.remove('error');
        inputElement.classList.add('success');
        return true;
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
    // Check if empty
    if (!username.trim()) {
        return { valid: false, message: 'نام کاربری نمی‌تواند خالی باشد.' };
    }

    // Check minimum length
    if (username.length < 3) {
        return { valid: false, message: 'نام کاربری باید حداقل ۳ کاراکتر باشد.' };
    }

    // Check for forbidden characters
    if (FORBIDDEN_CHARS.test(username)) {
        return {
            valid: false,
            message: 'نام کاربری نباید شامل کاراکترهای $ ،# ،@ و دیگر کاراکترهای خاص باشد.'
        };
    }

    // Check for valid characters (only letters, numbers, underscore)
    if (!/^[a-zA-Z0-9_]+$/.test(username)) {
        return {
            valid: false,
            message: 'نام کاربری فقط می‌تواند شامل حروف، اعداد و زیرخط (_) باشد.'
        };
    }

    return { valid: true, message: '' };
}

function validatePassword(password) {
    // Check if empty
    if (!password.trim()) {
        return { valid: false, message: 'رمز عبور نمی‌تواند خالی باشد.' };
    }

    // Check password strength
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
    document.getElementById('usernameError').classList.remove('show');
    document.getElementById('passwordError').textContent = '';
    document.getElementById('passwordError').classList.remove('show');
    document.getElementById('confirmPasswordError').textContent = '';
    document.getElementById('confirmPasswordError').classList.remove('show');
    document.getElementById('generalError').textContent = '';
    document.getElementById('generalError').classList.remove('show');
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
        errorEl.textContent = '';
        errorEl.classList.remove('show');
    }
}

function markAsSuccess(input) {
    input.classList.add('success');
    input.classList.remove('error');
    const errorEl = input.parentElement.querySelector('.error-message');
    if (errorEl) {
        errorEl.textContent = '';
        errorEl.classList.remove('show');
    }
}

function handleSignup(event) {
    event.preventDefault();

    clearErrorMessages();

    const usernameInput = document.getElementById('username');
    const passwordInput = document.getElementById('password');
    const confirmPasswordInput = document.getElementById('confirmPassword');
    const username = usernameInput.value;
    const password = passwordInput.value;
    const confirmPassword = confirmPasswordInput.value;
    const signupBtn = document.querySelector('.signup-btn');

    // Validate username
    const usernameValidation = validateUsername(username);
    if (!usernameValidation.valid) {
        showError(usernameInput, usernameValidation.message);
        usernameInput.focus();
        return;
    }

    // Validate password
    const passwordValidation = validatePassword(password);
    if (!passwordValidation.valid) {
        showError(passwordInput, passwordValidation.message);
        passwordInput.focus();
        document.getElementById('passwordRules').classList.add('show');
        return;
    }

    // Validate confirm password
    if (!confirmPassword) {
        showError(confirmPasswordInput, 'تایید رمز عبور نمی‌تواند خالی باشد');
        confirmPasswordInput.focus();
        return;
    }

    if (password !== confirmPassword) {
        showError(confirmPasswordInput, 'رمز عبور و تایید آن باید یکسان باشند');
        confirmPasswordInput.focus();
        return;
    }

    // Mark inputs as success
    markAsSuccess(usernameInput);
    markAsSuccess(passwordInput);
    markAsSuccess(confirmPasswordInput);

    // Show loading overlay
    const loadingOverlay = document.getElementById('loading-overlay');
    loadingOverlay.classList.remove('hidden');
    signupBtn.disabled = true;

    // Send signup request to server
    fetch('http://localhost:5000/api/auth/signup', {
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
        signupBtn.disabled = false;

        if (data.success) {
            // Show success message
            const generalError = document.getElementById('generalError');
            generalError.textContent = 'ثبت نام با موفقیت انجام شد! در حال انتقال به صفحه ورود...';
            generalError.style.display = 'block';
            generalError.style.backgroundColor = '#d4edda';
            generalError.style.borderLeftColor = '#28a745';
            generalError.style.color = '#155724';

            // Redirect to login page after 2 seconds
            setTimeout(() => {
                window.location.href = 'index.html';
            }, 2000);
        } else {
            const generalError = document.getElementById('generalError');
            generalError.textContent = data.message || 'خطا در ثبت نام. لطفاً دوباره تلاش کنید.';
            generalError.style.display = 'block';
            generalError.style.backgroundColor = '#fadbd8';
            generalError.style.borderLeftColor = '#e74c3c';
            generalError.style.color = '#e74c3c';
        }
    })
    .catch(error => {
        loadingOverlay.classList.add('hidden');
        signupBtn.disabled = false;
        const generalError = document.getElementById('generalError');
        generalError.textContent = 'خطا در اتصال به سرور. لطفاً دوباره تلاش کنید.';
        generalError.style.display = 'block';
        generalError.style.backgroundColor = '#fadbd8';
        generalError.style.borderLeftColor = '#e74c3c';
        generalError.style.color = '#e74c3c';
        console.error('Signup error:', error);
    });
}