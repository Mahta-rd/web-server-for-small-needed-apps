// Forbidden characters for passwords
const FORBIDDEN_CHARS = /[ ]/g;

// Password strength requirements
const PASSWORD_REQUIREMENTS = {
    minLength: 8,
    hasUpperCase: /[A-Z]/,
    hasLowerCase: /[a-z]/,
    hasNumber: /[0-9]/,
    hasSpecialChar: /[@$!%*?&]/
};

let token = null;
let locationData = {
    states: [],
    counties: {},
    sections: {},
    cities: {}
};

// Check if user is logged in
document.addEventListener('DOMContentLoaded', function() {
    token = sessionStorage.getItem('token');

    if (!token) {
        window.location.href = 'index.html';
        return;
    }

    // Verify session with server
    verifySession()
        .then(isValid => {
            if (!isValid) {
                sessionStorage.clear();
                window.location.href = 'index.html';
            } else {
                setupChangePasswordListeners();
                setupLocationSelectors();
                updateLastPage('company.html');
            }
        })
        .catch(() => {
            sessionStorage.clear();
            window.location.href = 'index.html';
        });
});

function verifySession() {
    return fetch('http://localhost:5000/api/auth/verify', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'Authorization': 'Bearer ' + token
        }
    })
    .then(response => response.json())
    .then(data => {
        return data.success === true;
    })
    .catch(() => false);
}

function updateLastPage(page) {
    return fetch('http://localhost:5000/api/auth/update-last-page', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'Authorization': 'Bearer ' + token
        },
        body: JSON.stringify({ lastPage: page })
    })
    .catch(() => {});
}

// ============================================================
// Password Change Functions
// ============================================================

function setupChangePasswordListeners() {
    const newPasswordInput = document.getElementById('newPassword');

    if (newPasswordInput) {
        newPasswordInput.addEventListener('focus', function() {
            document.getElementById('passwordRules').classList.add('show');
        });

        newPasswordInput.addEventListener('blur', function() {
            if (this.value.length === 0) {
                document.getElementById('passwordRules').classList.remove('show');
            }
        });

        newPasswordInput.addEventListener('input', function() {
            validatePasswordRules(this.value);
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

function validateNewPassword(password) {
    if (!password.trim()) {
        return { valid: false, message: 'رمز عبور جدید نمی‌تواند خالی باشد.' };
    }

    if (FORBIDDEN_CHARS.test(password)) {
        return {
            valid: false,
            message: 'رمز عبور نباید شامل کاراکترهای $ ،# ،@ و دیگر کاراکترهای خاص باشد.'
        };
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

function logout(event) {
    event.preventDefault();

    fetch('http://localhost:5000/api/auth/logout', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'Authorization': 'Bearer ' + token
        }
    })
    .finally(() => {
        sessionStorage.clear();
        window.location.href = 'index.html';
    });
}

function changePassword(event) {
    event.preventDefault();
    document.getElementById('changePasswordModal').classList.remove('hidden');
    clearChangePasswordErrors();
}

function closeChangePasswordModal() {
    document.getElementById('changePasswordModal').classList.add('hidden');
    document.getElementById('changePasswordForm').reset();
    clearChangePasswordErrors();
    document.getElementById('passwordRules').classList.remove('show');
}

function clearChangePasswordErrors() {
    document.getElementById('currentPasswordError').textContent = '';
    document.getElementById('newPasswordError').textContent = '';
    document.getElementById('confirmPasswordError').textContent = '';
    document.getElementById('changePasswordGeneralError').textContent = '';
    document.getElementById('changePasswordGeneralError').classList.remove('show');
}

function validatePasswordChange(currentPassword, newPassword, confirmPassword) {
    const errors = {};

    if (!currentPassword.trim()) {
        errors.currentPassword = 'رمز عبور فعلی نمی‌تواند خالی باشد';
    }

    const newPwdValidation = validateNewPassword(newPassword);
    if (!newPwdValidation.valid) {
        errors.newPassword = newPwdValidation.message;
    }

    if (!confirmPassword.trim()) {
        errors.confirmPassword = 'تایید رمز عبور نمی‌تواند خالی باشد';
    } else if (newPassword && confirmPassword && newPassword !== confirmPassword) {
        errors.confirmPassword = 'رمز عبور جدید و تایید آن باید یکسان باشند';
    }

    return errors;
}

function handleChangePassword(event) {
    event.preventDefault();
    clearChangePasswordErrors();

    const currentPassword = document.getElementById('currentPassword').value;
    const newPassword = document.getElementById('newPassword').value;
    const confirmPassword = document.getElementById('confirmPassword').value;

    const errors = validatePasswordChange(currentPassword, newPassword, confirmPassword);

    if (Object.keys(errors).length > 0) {
        if (errors.currentPassword) {
            document.getElementById('currentPasswordError').textContent = errors.currentPassword;
        }
        if (errors.newPassword) {
            document.getElementById('newPasswordError').textContent = errors.newPassword;
        }
        if (errors.confirmPassword) {
            document.getElementById('confirmPasswordError').textContent = errors.confirmPassword;
        }
        return;
    }

    fetch('http://localhost:5000/api/auth/change-password', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'Authorization': 'Bearer ' + token
        },
        body: JSON.stringify({
            currentPassword: currentPassword,
            newPassword: newPassword
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            closeChangePasswordModal();
            alert('رمز عبور با موفقیت تغییر یافت');
        } else {
            document.getElementById('changePasswordGeneralError').textContent = data.message;
            document.getElementById('changePasswordGeneralError').classList.add('show');
        }
    })
    .catch(error => {
        document.getElementById('changePasswordGeneralError').textContent = 'خطا در اتصال به سرور. لطفاً دوباره تلاش کنید.';
        document.getElementById('changePasswordGeneralError').classList.add('show');
    });
}

// Close modal when clicking outside of it
window.onclick = function(event) {
    const modal = document.getElementById('changePasswordModal');
    if (event.target === modal) {
        closeChangePasswordModal();
    }
};

// ============================================================
// Location Selectors - FIXED VERSION
// ============================================================

function setupLocationSelectors() {
    const stateSelect = document.getElementById('state');
    const countySelect = document.getElementById('county');
    const sectionSelect = document.getElementById('section');
    const citySelect = document.getElementById('city');

    // Load states
    loadStates();

    // State change - load counties
    stateSelect.addEventListener('change', function() {
        const stateCode = this.value;
        if (stateCode) {
            loadCounties(stateCode);
        } else {
            resetSelect(countySelect, 'ابتدا استان را انتخاب کنید');
            resetSelect(sectionSelect, 'ابتدا شهرستان را انتخاب کنید');
            resetSelect(citySelect, 'ابتدا بخش را انتخاب کنید');
        }
    });

    // County change - load sections
    countySelect.addEventListener('change', function() {
        const countyCode = this.value;
        if (countyCode) {
            loadSections(countyCode);
        } else {
            resetSelect(sectionSelect, 'ابتدا شهرستان را انتخاب کنید');
            resetSelect(citySelect, 'ابتدا بخش را انتخاب کنید');
        }
    });

    // Section change - load cities
    sectionSelect.addEventListener('change', function() {
        const sectionCode = this.value;
        if (sectionCode) {
            loadCities(sectionCode);
        } else {
            resetSelect(citySelect, 'ابتدا بخش را انتخاب کنید');
        }
    });
}

function resetSelect(select, placeholder) {
    select.innerHTML = `<option value="">${placeholder}</option>`;
    select.disabled = true;
}

function loadStates() {
    const stateSelect = document.getElementById('state');
    stateSelect.innerHTML = '<option value="">در حال بارگذاری...</option>';

    fetch('http://localhost:5000/get-city?code=1')
        .then(response => response.json())
        .then(data => {
            stateSelect.innerHTML = '<option value="">انتخاب کنید</option>';

            // The API returns a dictionary with state names as keys and codes as values
            // Example: { "تهران": "33", "اصفهان": "12", ... }
            if (typeof data === 'object' && !data.success) {
                // Convert object to array of {code, name}
                const states = Object.keys(data).map(name => ({
                    code: data[name],
                    name: name
                }));

                // Sort by name
                states.sort((a, b) => a.name.localeCompare(b.name));

                states.forEach(state => {
                    const option = document.createElement('option');
                    option.value = state.code;
                    option.textContent = state.name;
                    stateSelect.appendChild(option);
                });
                locationData.states = states;
            } else if (data.success && data.result) {
                // Fallback for other API format
                const states = data.result;
                states.forEach(state => {
                    const option = document.createElement('option');
                    option.value = state.code;
                    option.textContent = state.name;
                    stateSelect.appendChild(option);
                });
                locationData.states = states;
            } else {
                stateSelect.innerHTML = '<option value="">خطا در بارگذاری استان‌ها</option>';
                console.error('Unexpected API response:', data);
            }
        })
        .catch(error => {
            console.error('Error loading states:', error);
            stateSelect.innerHTML = '<option value="">خطا در بارگذاری استان‌ها</option>';
        });
}

function loadCounties(stateCode) {
    const countySelect = document.getElementById('county');
    const sectionSelect = document.getElementById('section');
    const citySelect = document.getElementById('city');

    countySelect.innerHTML = '<option value="">در حال بارگذاری...</option>';
    countySelect.disabled = true;
    resetSelect(sectionSelect, 'ابتدا شهرستان را انتخاب کنید');
    resetSelect(citySelect, 'ابتدا بخش را انتخاب کنید');

    fetch(`http://localhost:5000/get-city?code=${stateCode}`)
        .then(response => response.json())
        .then(data => {
            countySelect.innerHTML = '<option value="">انتخاب کنید</option>';

            // The API returns a dictionary with county names as keys and codes as values
            if (typeof data === 'object' && !data.success) {
                const counties = Object.keys(data).map(name => ({
                    code: data[name],
                    name: name
                }));
                counties.sort((a, b) => a.name.localeCompare(b.name));

                counties.forEach(county => {
                    const option = document.createElement('option');
                    option.value = county.code;
                    option.textContent = county.name;
                    countySelect.appendChild(option);
                });
                locationData.counties[stateCode] = counties;
                countySelect.disabled = false;
            } else if (data.success && data.result) {
                const counties = data.result;
                counties.forEach(county => {
                    const option = document.createElement('option');
                    option.value = county.code;
                    option.textContent = county.name;
                    countySelect.appendChild(option);
                });
                locationData.counties[stateCode] = counties;
                countySelect.disabled = false;
            } else {
                countySelect.innerHTML = '<option value="">خطا در بارگذاری شهرستان‌ها</option>';
                console.error('Unexpected API response:', data);
            }
        })
        .catch(error => {
            console.error('Error loading counties:', error);
            countySelect.innerHTML = '<option value="">خطا در بارگذاری شهرستان‌ها</option>';
        });
}

function loadSections(countyCode) {
    const sectionSelect = document.getElementById('section');
    const citySelect = document.getElementById('city');

    sectionSelect.innerHTML = '<option value="">در حال بارگذاری...</option>';
    sectionSelect.disabled = true;
    resetSelect(citySelect, 'ابتدا بخش را انتخاب کنید');

    fetch(`http://localhost:5000/get-city?code=${countyCode}`)
        .then(response => response.json())
        .then(data => {
            sectionSelect.innerHTML = '<option value="">انتخاب کنید</option>';

            // The API returns a dictionary with section names as keys and codes as values
            if (typeof data === 'object' && !data.success) {
                const sections = Object.keys(data).map(name => ({
                    code: data[name],
                    name: name
                }));
                sections.sort((a, b) => a.name.localeCompare(b.name));

                sections.forEach(section => {
                    const option = document.createElement('option');
                    option.value = section.code;
                    option.textContent = section.name;
                    sectionSelect.appendChild(option);
                });
                locationData.sections[countyCode] = sections;
                sectionSelect.disabled = false;
            } else if (data.success && data.result) {
                const sections = data.result;
                sections.forEach(section => {
                    const option = document.createElement('option');
                    option.value = section.code;
                    option.textContent = section.name;
                    sectionSelect.appendChild(option);
                });
                locationData.sections[countyCode] = sections;
                sectionSelect.disabled = false;
            } else {
                sectionSelect.innerHTML = '<option value="">خطا در بارگذاری بخش‌ها</option>';
                console.error('Unexpected API response:', data);
            }
        })
        .catch(error => {
            console.error('Error loading sections:', error);
            sectionSelect.innerHTML = '<option value="">خطا در بارگذاری بخش‌ها</option>';
        });
}

function loadCities(sectionCode) {
    const citySelect = document.getElementById('city');

    citySelect.innerHTML = '<option value="">در حال بارگذاری...</option>';
    citySelect.disabled = true;

    fetch(`http://localhost:5000/get-city?code=${sectionCode}`)
        .then(response => response.json())
        .then(data => {
            citySelect.innerHTML = '<option value="">انتخاب کنید</option>';

            // The API returns a dictionary with city names as keys and codes as values
            if (typeof data === 'object' && !data.success) {
                const cities = Object.keys(data).map(name => ({
                    code: data[name],
                    name: name
                }));
                cities.sort((a, b) => a.name.localeCompare(b.name));

                cities.forEach(city => {
                    const option = document.createElement('option');
                    option.value = city.code;
                    option.textContent = city.name;
                    citySelect.appendChild(option);
                });
                locationData.cities[sectionCode] = cities;
                citySelect.disabled = false;
            } else if (data.success && data.result) {
                const cities = data.result;
                cities.forEach(city => {
                    const option = document.createElement('option');
                    option.value = city.code;
                    option.textContent = city.name;
                    citySelect.appendChild(option);
                });
                locationData.cities[sectionCode] = cities;
                citySelect.disabled = false;
            } else {
                citySelect.innerHTML = '<option value="">خطا در بارگذاری شهرها</option>';
                console.error('Unexpected API response:', data);
            }
        })
        .catch(error => {
            console.error('Error loading cities:', error);
            citySelect.innerHTML = '<option value="">خطا در بارگذاری شهرها</option>';
        });
}

// ============================================================
// Company Form Validation
// ============================================================

function validateCompanyNationalCode(nationalCode) {
    // Remove non-digit characters
    const cleaned = nationalCode.replace(/\D/g, '');

    if (cleaned.length !== 11) {
        return { valid: false, message: 'شناسه ملی باید ۱۱ رقم باشد' };
    }

    // Check if all digits are the same (invalid)
    if (/^(\d)\1{10}$/.test(cleaned)) {
        return { valid: false, message: 'شناسه ملی معتبر نیست' };
    }

    // Company national code validation algorithm
    const coefficient = [29, 27, 23, 19, 17, 29, 27, 23, 19, 247];
    let sum = 0;
    for (let i = 0; i < 10; i++) {
        sum += parseInt(cleaned[i]) * coefficient[i];
    }
    sum += 460;
    const remain = sum % 11;
    const controlDigit = remain === 10 ? 0 : remain;

    if (controlDigit !== parseInt(cleaned[10])) {
        return { valid: false, message: 'شناسه ملی معتبر نیست' };
    }

    return { valid: true, message: '' };
}

function validateCompanyForm() {
    const errors = {};

    const companyName = document.getElementById('companyName').value.trim();
    const nationalCode = document.getElementById('nationalCode').value.trim();
    const registrationNumber = document.getElementById('registrationNumber').value.trim();
    const year = document.getElementById('registrationDateYear').value.trim();
    const month = document.getElementById('registrationDateMonth').value;
    const day = document.getElementById('registrationDateDay').value;
    const state = document.getElementById('state').value;
    const county = document.getElementById('county').value;
    const section = document.getElementById('section').value;
    const city = document.getElementById('city').value;

    // Clear previous errors
    clearErrors();

    // Validate company name
    if (!companyName) {
        errors.companyName = 'نام شرکت نمی‌تواند خالی باشد';
    } else if (companyName.length < 3) {
        errors.companyName = 'نام شرکت باید حداقل ۳ کاراکتر باشد';
    }

    // Validate national code
    if (!nationalCode) {
        errors.nationalCode = 'شناسه ملی نمی‌تواند خالی باشد';
    } else {
        const validation = validateCompanyNationalCode(nationalCode);
        if (!validation.valid) {
            errors.nationalCode = validation.message;
        }
    }

    // Validate registration number
    if (!registrationNumber) {
        errors.registrationNumber = 'شماره ثبت نمی‌تواند خالی باشد';
    }

    // Validate date
    if (!year) {
        errors.registrationDateYear = 'سال ثبت را وارد کنید';
    } else if (isNaN(year) || year < 1300 || year > 1410) {
        errors.registrationDateYear = 'سال ثبت باید بین ۱۳۰۰ تا ۱۴۱۰ باشد';
    }

    if (!month) {
        errors.registrationDateMonth = 'ماه ثبت را انتخاب کنید';
    }

    if (!day) {
        errors.registrationDateDay = 'روز ثبت را انتخاب کنید';
    }

    // Validate location
    if (!state) {
        errors.state = 'استان را انتخاب کنید';
    }
    if (!county) {
        errors.county = 'شهرستان را انتخاب کنید';
    }
    if (!section) {
        errors.section = 'بخش را انتخاب کنید';
    }
    if (!city) {
        errors.city = 'شهر را انتخاب کنید';
    }

    return errors;
}

function clearErrors() {
    const errorFields = [
        'companyName', 'nationalCode', 'registrationNumber',
        'registrationDateYear', 'registrationDateMonth', 'registrationDateDay',
        'state', 'county', 'section', 'city'
    ];

    errorFields.forEach(field => {
        const errorEl = document.getElementById(field + 'Error');
        if (errorEl) {
            errorEl.textContent = '';
            errorEl.classList.remove('show');
        }
        const inputEl = document.getElementById(field);
        if (inputEl) {
            inputEl.classList.remove('error', 'success');
        }
    });

    const generalError = document.getElementById('generalError');
    generalError.textContent = '';
    generalError.classList.remove('show');
    generalError.style.display = 'none';
}

function showFieldError(fieldName, message) {
    const errorEl = document.getElementById(fieldName + 'Error');
    if (errorEl) {
        errorEl.textContent = message;
        errorEl.classList.add('show');
    }
    const inputEl = document.getElementById(fieldName);
    if (inputEl) {
        inputEl.classList.add('error');
    }
}

function handleCompanySubmit(event) {
    event.preventDefault();

    const errors = validateCompanyForm();

    if (Object.keys(errors).length > 0) {
        // Show errors
        for (const [field, message] of Object.entries(errors)) {
            showFieldError(field, message);
        }
        // Scroll to first error
        const firstErrorField = Object.keys(errors)[0];
        const firstElement = document.getElementById(firstErrorField);
        if (firstElement) {
            firstElement.focus();
            firstElement.scrollIntoView({ behavior: 'smooth', block: 'center' });
        }
        return;
    }

    // Prepare form data
    const formData = {
        companyName: document.getElementById('companyName').value.trim(),
        nationalCode: document.getElementById('nationalCode').value.trim().replace(/\D/g, ''),
        registrationNumber: document.getElementById('registrationNumber').value.trim(),
        registrationDate: {
            year: parseInt(document.getElementById('registrationDateYear').value),
            month: parseInt(document.getElementById('registrationDateMonth').value),
            day: parseInt(document.getElementById('registrationDateDay').value)
        },
        location: {
            state: document.getElementById('state').value,
            county: document.getElementById('county').value,
            section: document.getElementById('section').value,
            city: document.getElementById('city').value
        }
    };

    const submitBtn = document.querySelector('.submit-btn');
    submitBtn.disabled = true;
    submitBtn.textContent = 'در حال ثبت...';

    // Send to server
    fetch('http://localhost:5000/api/company/register', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'Authorization': 'Bearer ' + token
        },
        body: JSON.stringify(formData)
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Show success message
            const generalError = document.getElementById('generalError');
            generalError.textContent = 'شرکت با موفقیت ثبت شد!';
            generalError.style.display = 'block';
            generalError.style.backgroundColor = '#d4edda';
            generalError.style.borderLeftColor = '#28a745';
            generalError.style.color = '#155724';
            generalError.classList.add('show');

            // Reset form
            document.getElementById('companyForm').reset();
            // Reset location selectors
            resetSelect(document.getElementById('county'), 'ابتدا استان را انتخاب کنید');
            resetSelect(document.getElementById('section'), 'ابتدا شهرستان را انتخاب کنید');
            resetSelect(document.getElementById('city'), 'ابتدا بخش را انتخاب کنید');
            // Reset day selector
            document.getElementById('registrationDateDay').innerHTML = '<option value="">انتخاب کنید</option>';

            // Clear success indicators
            document.querySelectorAll('.form-group input, .form-group select').forEach(el => {
                el.classList.remove('success');
            });

            // Update last page
            updateLastPage('company.html');
        } else {
            const generalError = document.getElementById('generalError');
            generalError.textContent = data.message || 'خطا در ثبت شرکت';
            generalError.style.display = 'block';
            generalError.classList.add('show');
        }
    })
    .catch(error => {
        const generalError = document.getElementById('generalError');
        generalError.textContent = 'خطا در اتصال به سرور. لطفاً دوباره تلاش کنید.';
        generalError.style.display = 'block';
        generalError.classList.add('show');
        console.error('Company registration error:', error);
    })
    .finally(() => {
        submitBtn.disabled = false;
        submitBtn.textContent = 'ثبت شرکت';
    });
}

// ============================================================
// Date Helpers - Populate days based on month
// ============================================================

document.addEventListener('DOMContentLoaded', function() {
    const monthSelect = document.getElementById('registrationDateMonth');
    const daySelect = document.getElementById('registrationDateDay');

    if (monthSelect) {
        monthSelect.addEventListener('change', function() {
            const month = parseInt(this.value);
            populateDays(daySelect, month);
        });
    }
});

function populateDays(daySelect, month) {
    // Clear previous options
    daySelect.innerHTML = '<option value="">انتخاب کنید</option>';

    if (!month) {
        return;
    }

    // Persian months days
    const monthDays = {
        1: 31, 2: 31, 3: 31, 4: 31, 5: 31, 6: 31,
        7: 30, 8: 30, 9: 30, 10: 30, 11: 30, 12: 30
    };

    const days = monthDays[month] || 31;

    for (let i = 1; i <= days; i++) {
        const option = document.createElement('option');
        option.value = i;
        option.textContent = i;
        daySelect.appendChild(option);
    }
}