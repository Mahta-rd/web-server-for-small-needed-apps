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
                // اعمال جستجوی زنده به comboboxها
                setupSearchableSelects();

                setupChangePasswordListeners();
                setupLocationSelectors();
                loadRegistrationCenters();
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
// Live Search for Combobox - NEW SECTION
// ============================================================

/**
 * تبدیل یک select معمولی به select با قابلیت جستجوی زنده
 * @param {string} selectId - ID المنت select
 * @param {string} placeholder - متن placeholder
 */
function makeSelectSearchable(selectId, placeholder = 'جستجو کنید...') {
    const select = document.getElementById(selectId);
    if (!select) return null;

    // ایجاد container برای wrapper
    const wrapper = document.createElement('div');
    wrapper.className = 'searchable-select-wrapper';
    wrapper.style.position = 'relative';
    wrapper.style.width = '100%';

    // ایجاد input جستجو
    const searchInput = document.createElement('input');
    searchInput.type = 'text';
    searchInput.className = 'searchable-select-input';
    searchInput.placeholder = placeholder;
    searchInput.autocomplete = 'off';
    searchInput.style.width = '100%';
    searchInput.style.padding = '12px 15px';
    searchInput.style.border = '2px solid #ddd';
    searchInput.style.borderRadius = '6px';
    searchInput.style.fontSize = '14px';
    searchInput.style.fontFamily = "'B Yekan', 'Tahoma', sans-serif";
    searchInput.style.background = '#f9f9f9';
    searchInput.style.boxSizing = 'border-box';
    searchInput.style.cursor = 'text';
    searchInput.style.transition = 'all 0.3s ease';

    // ایجاد dropdown برای گزینه‌ها
    const dropdown = document.createElement('div');
    dropdown.className = 'searchable-select-dropdown';
    dropdown.style.position = 'absolute';
    dropdown.style.top = '100%';
    dropdown.style.left = '0';
    dropdown.style.right = '0';
    dropdown.style.background = 'white';
    dropdown.style.border = '2px solid #ddd';
    dropdown.style.borderTop = 'none';
    dropdown.style.borderRadius = '0 0 6px 6px';
    dropdown.style.maxHeight = '200px';
    dropdown.style.overflowY = 'auto';
    dropdown.style.zIndex = '1000';
    dropdown.style.display = 'none';
    dropdown.style.boxShadow = '0 4px 12px rgba(0,0,0,0.15)';
    dropdown.style.marginTop = '-1px';

    // مخفی کردن select اصلی
    select.style.display = 'none';

    // ذخیره گزینه‌های اصلی
    const originalOptions = [];
    for (let i = 0; i < select.options.length; i++) {
        const opt = select.options[i];
        originalOptions.push({
            value: opt.value,
            text: opt.text,
            disabled: opt.disabled,
            selected: opt.selected
        });
    }

    // تعیین مقدار پیش‌فرض
    let currentValue = select.value;
    let currentText = '';
    for (const opt of originalOptions) {
        if (opt.value === currentValue) {
            currentText = opt.text;
            break;
        }
    }
    if (currentText) {
        searchInput.value = currentText;
    }

    // تابع ساخت dropdown
    function buildDropdown(filterText = '') {
        dropdown.innerHTML = '';
        const filterLower = filterText.trim().toLowerCase();

        let hasResults = false;
        for (const opt of originalOptions) {
            const textMatch = filterLower === '' ||
                              opt.text.toLowerCase().includes(filterLower) ||
                              opt.value.toLowerCase().includes(filterLower);

            if (textMatch && !opt.disabled) {
                const optionDiv = document.createElement('div');
                optionDiv.className = 'searchable-option';
                optionDiv.style.padding = '10px 15px';
                optionDiv.style.cursor = 'pointer';
                optionDiv.style.borderBottom = '1px solid #f0f0f0';
                optionDiv.style.fontSize = '14px';
                optionDiv.style.fontFamily = "'B Yekan', 'Tahoma', sans-serif";
                optionDiv.style.transition = 'background 0.15s ease';
                optionDiv.textContent = opt.text;

                if (opt.value === currentValue) {
                    optionDiv.style.background = '#e8f4fd';
                    optionDiv.style.fontWeight = '600';
                }

                optionDiv.addEventListener('mouseenter', function() {
                    this.style.background = '#f0f7ff';
                });
                optionDiv.addEventListener('mouseleave', function() {
                    if (this.dataset.value === currentValue) {
                        this.style.background = '#e8f4fd';
                    } else {
                        this.style.background = '';
                    }
                });

                optionDiv.dataset.value = opt.value;
                optionDiv.dataset.text = opt.text;

                optionDiv.addEventListener('click', function() {
                    selectOption(this.dataset.value, this.dataset.text);
                });

                dropdown.appendChild(optionDiv);
                hasResults = true;
            }
        }

        if (!hasResults) {
            const noResult = document.createElement('div');
            noResult.className = 'searchable-option no-result';
            noResult.style.padding = '12px 15px';
            noResult.style.color = '#999';
            noResult.style.fontSize = '14px';
            noResult.style.textAlign = 'center';
            noResult.textContent = 'نتیجه‌ای یافت نشد';
            dropdown.appendChild(noResult);
        }
    }

    // تابع انتخاب گزینه
    function selectOption(value, text) {
        currentValue = value;
        currentText = text;
        searchInput.value = text;
        select.value = value;

        // به‌روزرسانی استایل گزینه انتخاب شده
        const options = dropdown.querySelectorAll('.searchable-option');
        options.forEach(opt => {
            opt.style.background = '';
            opt.style.fontWeight = '';
            if (opt.dataset.value === value) {
                opt.style.background = '#e8f4fd';
                opt.style.fontWeight = '600';
            }
        });

        dropdown.style.display = 'none';
        searchInput.classList.remove('open');
        searchInput.style.borderColor = '#2ecc71';
        searchInput.style.background = '#f0fff4';

        const changeEvent = new Event('change', { bubbles: true });
        select.dispatchEvent(changeEvent);
    }

    // رویدادهای input جستجو
    searchInput.addEventListener('focus', function() {
        dropdown.style.display = 'block';
        this.classList.add('open');
        this.style.borderColor = '#3498db';
        this.style.background = '#fff';
        buildDropdown(this.value);
    });

    searchInput.addEventListener('input', function() {
        dropdown.style.display = 'block';
        this.classList.add('open');
        this.style.borderColor = '#3498db';
        buildDropdown(this.value);
    });

    // بستن dropdown با کلیک خارج از آن
    document.addEventListener('click', function(e) {
        if (!wrapper.contains(e.target)) {
            dropdown.style.display = 'none';
            searchInput.classList.remove('open');
            searchInput.style.borderColor = '#ddd';
            searchInput.style.background = '#f9f9f9';
        }
    });

    dropdown.addEventListener('click', function(e) {
        e.stopPropagation();
    });

    // کلیدهای صفحه‌کلید
    searchInput.addEventListener('keydown', function(e) {
        const options = dropdown.querySelectorAll('.searchable-option:not(.no-result)');
        if (options.length === 0) return;

        let currentIndex = -1;
        for (let i = 0; i < options.length; i++) {
            if (options[i].style.background === 'rgb(240, 247, 255)' ||
                options[i].style.background === '#f0f7ff') {
                currentIndex = i;
                break;
            }
        }

        if (e.key === 'ArrowDown') {
            e.preventDefault();
            const nextIndex = (currentIndex + 1) % options.length;
            options.forEach(opt => {
                opt.style.background = '';
                opt.style.fontWeight = '';
            });
            options[nextIndex].style.background = '#f0f7ff';
            options[nextIndex].scrollIntoView({ block: 'nearest' });
        } else if (e.key === 'ArrowUp') {
            e.preventDefault();
            const prevIndex = (currentIndex - 1 + options.length) % options.length;
            options.forEach(opt => {
                opt.style.background = '';
                opt.style.fontWeight = '';
            });
            options[prevIndex].style.background = '#f0f7ff';
            options[prevIndex].scrollIntoView({ block: 'nearest' });
        } else if (e.key === 'Enter') {
            e.preventDefault();
            if (currentIndex >= 0 && currentIndex < options.length) {
                const selected = options[currentIndex];
                selectOption(selected.dataset.value, selected.dataset.text);
            } else if (options.length === 1) {
                const selected = options[0];
                selectOption(selected.dataset.value, selected.dataset.text);
            }
        } else if (e.key === 'Escape') {
            dropdown.style.display = 'none';
            searchInput.classList.remove('open');
            searchInput.blur();
        }
    });

    select.parentNode.insertBefore(wrapper, select);
    wrapper.appendChild(searchInput);
    wrapper.appendChild(dropdown);
    wrapper.appendChild(select);

    // تابع بازسازی dropdown از روی select
    wrapper.rebuildDropdown = function() {
        // به‌روزرسانی originalOptions
        originalOptions.length = 0;
        for (let i = 0; i < select.options.length; i++) {
            const opt = select.options[i];
            originalOptions.push({
                value: opt.value,
                text: opt.text,
                disabled: opt.disabled,
                selected: opt.selected
            });
        }
        // اگر dropdown باز است، بازسازی کن
        if (dropdown.style.display === 'block') {
            buildDropdown(searchInput.value);
        }
    };

    // تابع تنظیم مقدار از بیرون
    wrapper.setValue = function(value) {
        for (const opt of originalOptions) {
            if (opt.value === value) {
                selectOption(value, opt.text);
                return true;
            }
        }
        return false;
    };

    wrapper.getValue = function() {
        return currentValue;
    };

    wrapper.getSelect = function() {
        return select;
    };

    return wrapper;
}

/**
 * اعمال قابلیت جستجوی زنده به همه comboboxهای فرم ثبت شرکت
 */
function setupSearchableSelects() {
    const companySelects = [
        { id: 'state', placeholder: 'جستجوی استان...' },
        { id: 'county', placeholder: 'جستجوی شهرستان...' },
        { id: 'section', placeholder: 'جستجوی بخش...' },
        { id: 'city', placeholder: 'جستجوی شهر...' },
        { id: 'registrationCenter', placeholder: 'جستجوی مرکز ثبت...' }
    ];

    const wrappers = {};

    companySelects.forEach(({ id, placeholder }) => {
        const select = document.getElementById(id);
        if (select) {
            wrappers[id] = makeSelectSearchable(id, placeholder);
        }
    });

    return wrappers;
}

// ============================================================
// Location Selectors
// ============================================================

function setupLocationSelectors() {
    const stateSelect = document.getElementById('state');
    const countySelect = document.getElementById('county');
    const sectionSelect = document.getElementById('section');
    const citySelect = document.getElementById('city');

    loadStates();

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

    countySelect.addEventListener('change', function() {
        const countyCode = this.value;
        if (countyCode) {
            loadSections(countyCode);
        } else {
            resetSelect(sectionSelect, 'ابتدا شهرستان را انتخاب کنید');
            resetSelect(citySelect, 'ابتدا بخش را انتخاب کنید');
        }
    });

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
    if (!select) return;

    // اگر select از نوع wrapper باشد
    const wrapper = select.closest ? select.closest('.searchable-select-wrapper') : null;
    if (wrapper) {
        const input = wrapper.querySelector('input');
        const dropdown = wrapper.querySelector('.searchable-select-dropdown');
        const originalSelect = wrapper.querySelector('select');

        if (input) {
            input.value = '';
            input.placeholder = placeholder;
        }
        if (originalSelect) {
            originalSelect.innerHTML = `<option value="">${placeholder}</option>`;
            originalSelect.disabled = true;
            originalSelect.value = '';
        }
        if (dropdown) {
            dropdown.innerHTML = '';
            const optionDiv = document.createElement('div');
            optionDiv.className = 'searchable-option no-result';
            optionDiv.style.padding = '10px 15px';
            optionDiv.style.color = '#999';
            optionDiv.style.fontSize = '14px';
            optionDiv.style.textAlign = 'center';
            optionDiv.textContent = placeholder;
            dropdown.appendChild(optionDiv);
        }
        return;
    }

    // روش معمول
    select.innerHTML = `<option value="">${placeholder}</option>`;
    select.disabled = true;
}

function getSelectElement(selectId) {
    const el = document.getElementById(selectId);
    if (!el) return null;

    const wrapper = el.closest ? el.closest('.searchable-select-wrapper') : null;
    if (wrapper) {
        return wrapper.querySelector('select') || el;
    }
    return el;
}

function loadStates() {
    const stateSelect = document.getElementById('state');
    if (!stateSelect) return;

    const wrapper = stateSelect.closest ? stateSelect.closest('.searchable-select-wrapper') : null;
    const input = wrapper ? wrapper.querySelector('input') : null;
    const originalSelect = wrapper ? wrapper.querySelector('select') : stateSelect;
    const targetSelect = originalSelect || stateSelect;

    targetSelect.innerHTML = '<option value="">در حال بارگذاری...</option>';
    targetSelect.disabled = true;
    if (input) input.value = 'در حال بارگذاری...';

    fetch('http://localhost:5000/get-city?code=1')
        .then(response => response.json())
        .then(data => {
            targetSelect.innerHTML = '<option value="">انتخاب کنید</option>';
            targetSelect.disabled = false;
            if (input) {
                input.value = '';
                input.placeholder = 'جستجوی استان...';
            }

            if (typeof data === 'object' && !data.success) {
                const states = Object.keys(data).map(name => ({
                    code: data[name],
                    name: name
                }));
                states.sort((a, b) => a.name.localeCompare(b.name));

                states.forEach(state => {
                    const option = document.createElement('option');
                    option.value = state.code;
                    option.textContent = state.name;
                    targetSelect.appendChild(option);
                });
                locationData.states = states;

                if (wrapper && wrapper.rebuildDropdown) {
                    wrapper.rebuildDropdown();
                }
            } else if (data.success && data.result) {
                const states = data.result;
                states.forEach(state => {
                    const option = document.createElement('option');
                    option.value = state.code;
                    option.textContent = state.name;
                    targetSelect.appendChild(option);
                });
                locationData.states = states;

                if (wrapper && wrapper.rebuildDropdown) {
                    wrapper.rebuildDropdown();
                }
            } else {
                targetSelect.innerHTML = '<option value="">خطا در بارگذاری استان‌ها</option>';
                console.error('Unexpected API response:', data);
                if (input) input.value = 'خطا';
            }
        })
        .catch(error => {
            console.error('Error loading states:', error);
            targetSelect.innerHTML = '<option value="">خطا در بارگذاری استان‌ها</option>';
            if (input) input.value = 'خطا';
        });
}

function loadCounties(stateCode) {
    const countySelect = document.getElementById('county');
    if (!countySelect) return;

    const wrapper = countySelect.closest ? countySelect.closest('.searchable-select-wrapper') : null;
    const input = wrapper ? wrapper.querySelector('input') : null;
    const originalSelect = wrapper ? wrapper.querySelector('select') : countySelect;
    const targetSelect = originalSelect || countySelect;

    const sectionSelect = document.getElementById('section');
    const citySelect = document.getElementById('city');

    targetSelect.innerHTML = '<option value="">در حال بارگذاری...</option>';
    targetSelect.disabled = true;
    if (input) input.value = 'در حال بارگذاری...';

    resetSelect(sectionSelect, 'ابتدا شهرستان را انتخاب کنید');
    resetSelect(citySelect, 'ابتدا بخش را انتخاب کنید');

    fetch(`http://localhost:5000/get-city?code=${stateCode}`)
        .then(response => response.json())
        .then(data => {
            targetSelect.innerHTML = '<option value="">انتخاب کنید</option>';
            targetSelect.disabled = false;
            if (input) {
                input.value = '';
                input.placeholder = 'جستجوی شهرستان...';
            }

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
                    targetSelect.appendChild(option);
                });
                locationData.counties[stateCode] = counties;
                targetSelect.disabled = false;

                if (wrapper && wrapper.rebuildDropdown) {
                    wrapper.rebuildDropdown();
                }
            } else if (data.success && data.result) {
                const counties = data.result;
                counties.forEach(county => {
                    const option = document.createElement('option');
                    option.value = county.code;
                    option.textContent = county.name;
                    targetSelect.appendChild(option);
                });
                locationData.counties[stateCode] = counties;
                targetSelect.disabled = false;

                if (wrapper && wrapper.rebuildDropdown) {
                    wrapper.rebuildDropdown();
                }
            } else {
                targetSelect.innerHTML = '<option value="">خطا در بارگذاری شهرستان‌ها</option>';
                console.error('Unexpected API response:', data);
                if (input) input.value = 'خطا';
            }
        })
        .catch(error => {
            console.error('Error loading counties:', error);
            targetSelect.innerHTML = '<option value="">خطا در بارگذاری شهرستان‌ها</option>';
            if (input) input.value = 'خطا';
        });
}

function loadSections(countyCode) {
    const sectionSelect = document.getElementById('section');
    if (!sectionSelect) return;

    const wrapper = sectionSelect.closest ? sectionSelect.closest('.searchable-select-wrapper') : null;
    const input = wrapper ? wrapper.querySelector('input') : null;
    const originalSelect = wrapper ? wrapper.querySelector('select') : sectionSelect;
    const targetSelect = originalSelect || sectionSelect;

    const citySelect = document.getElementById('city');

    targetSelect.innerHTML = '<option value="">در حال بارگذاری...</option>';
    targetSelect.disabled = true;
    if (input) input.value = 'در حال بارگذاری...';

    resetSelect(citySelect, 'ابتدا بخش را انتخاب کنید');

    fetch(`http://localhost:5000/get-city?code=${countyCode}`)
        .then(response => response.json())
        .then(data => {
            targetSelect.innerHTML = '<option value="">انتخاب کنید</option>';
            targetSelect.disabled = false;
            if (input) {
                input.value = '';
                input.placeholder = 'جستجوی بخش...';
            }

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
                    targetSelect.appendChild(option);
                });
                locationData.sections[countyCode] = sections;
                targetSelect.disabled = false;

                if (wrapper && wrapper.rebuildDropdown) {
                    wrapper.rebuildDropdown();
                }
            } else if (data.success && data.result) {
                const sections = data.result;
                sections.forEach(section => {
                    const option = document.createElement('option');
                    option.value = section.code;
                    option.textContent = section.name;
                    targetSelect.appendChild(option);
                });
                locationData.sections[countyCode] = sections;
                targetSelect.disabled = false;

                if (wrapper && wrapper.rebuildDropdown) {
                    wrapper.rebuildDropdown();
                }
            } else {
                targetSelect.innerHTML = '<option value="">خطا در بارگذاری بخش‌ها</option>';
                console.error('Unexpected API response:', data);
                if (input) input.value = 'خطا';
            }
        })
        .catch(error => {
            console.error('Error loading sections:', error);
            targetSelect.innerHTML = '<option value="">خطا در بارگذاری بخش‌ها</option>';
            if (input) input.value = 'خطا';
        });
}

function loadCities(sectionCode) {
    const citySelect = document.getElementById('city');
    if (!citySelect) return;

    const wrapper = citySelect.closest ? citySelect.closest('.searchable-select-wrapper') : null;
    const input = wrapper ? wrapper.querySelector('input') : null;
    const originalSelect = wrapper ? wrapper.querySelector('select') : citySelect;
    const targetSelect = originalSelect || citySelect;

    targetSelect.innerHTML = '<option value="">در حال بارگذاری...</option>';
    targetSelect.disabled = true;
    if (input) input.value = 'در حال بارگذاری...';

    fetch(`http://localhost:5000/get-city?code=${sectionCode}`)
        .then(response => response.json())
        .then(data => {
            targetSelect.innerHTML = '<option value="">انتخاب کنید</option>';
            targetSelect.disabled = false;
            if (input) {
                input.value = '';
                input.placeholder = 'جستجوی شهر...';
            }

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
                    targetSelect.appendChild(option);
                });
                locationData.cities[sectionCode] = cities;
                targetSelect.disabled = false;

                if (wrapper && wrapper.rebuildDropdown) {
                    wrapper.rebuildDropdown();
                }
            } else if (data.success && data.result) {
                const cities = data.result;
                cities.forEach(city => {
                    const option = document.createElement('option');
                    option.value = city.code;
                    option.textContent = city.name;
                    targetSelect.appendChild(option);
                });
                locationData.cities[sectionCode] = cities;
                targetSelect.disabled = false;

                if (wrapper && wrapper.rebuildDropdown) {
                    wrapper.rebuildDropdown();
                }
            } else {
                targetSelect.innerHTML = '<option value="">خطا در بارگذاری شهرها</option>';
                console.error('Unexpected API response:', data);
                if (input) input.value = 'خطا';
            }
        })
        .catch(error => {
            console.error('Error loading cities:', error);
            targetSelect.innerHTML = '<option value="">خطا در بارگذاری شهرها</option>';
            if (input) input.value = 'خطا';
        });
}

// ============================================================
// Company Form Validation
// ============================================================

function validateCompanyNationalCode(nationalCode) {
    const cleaned = nationalCode.replace(/\D/g, '');

    if (cleaned.length !== 11) {
        return { valid: false, message: 'شناسه ملی باید ۱۱ رقم باشد' };
    }

    if (/^(\d)\1{10}$/.test(cleaned)) {
        return { valid: false, message: 'شناسه ملی معتبر نیست' };
    }

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
    const state = document.getElementById('state').value;
    const county = document.getElementById('county').value;
    const section = document.getElementById('section').value;
    const city = document.getElementById('city').value;
    const selectedDate = document.getElementById('selectedDate').value;

    if (!selectedDate) {
        errors.registrationDate = 'تاریخ ثبت را انتخاب کنید';
    } else {
        const parts = selectedDate.split('/');
        if (parts.length !== 3) {
            errors.registrationDate = 'تاریخ ثبت نامعتبر است';
        } else {
            const year = parseInt(parts[0]);
            const month = parseInt(parts[1]);
            const day = parseInt(parts[2]);
            if (isNaN(year) || isNaN(month) || isNaN(day) || year < 1300 || year > 1410 || month < 1 || month > 12 || day < 1 || day > 31) {
                errors.registrationDate = 'تاریخ ثبت نامعتبر است';
            }
        }
    }

    clearErrors();

    if (!companyName) {
        errors.companyName = 'نام شرکت نمی‌تواند خالی باشد';
    } else if (companyName.length < 3) {
        errors.companyName = 'نام شرکت باید حداقل ۳ کاراکتر باشد';
    }

    if (!nationalCode) {
        errors.nationalCode = 'شناسه ملی نمی‌تواند خالی باشد';
    } else {
        const validation = validateCompanyNationalCode(nationalCode);
        if (!validation.valid) {
            errors.nationalCode = validation.message;
        }
    }

    if (!registrationNumber) {
        errors.registrationNumber = 'شماره ثبت نمی‌تواند خالی باشد';
    } else if (!/^\d{3,6}$/.test(registrationNumber)) {
        errors.registrationNumber = 'شماره ثبت باید عددی بین ۳ تا ۶ رقم باشد';
    }

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

    const registrationCenter = document.getElementById('registrationCenter').value;
    if (!registrationCenter) {
        errors.registrationCenter = 'مرکز ثبت را انتخاب کنید';
    }

    return errors;
}

function clearErrors() {
    const errorFields = [
        'companyName', 'nationalCode', 'registrationNumber',
        'registrationDateYear', 'registrationDateMonth', 'registrationDateDay',
        'state', 'county', 'section', 'city',
        'registrationCenter'
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
        for (const [field, message] of Object.entries(errors)) {
            showFieldError(field, message);
        }
        const firstErrorField = Object.keys(errors)[0];
        const firstElement = document.getElementById(firstErrorField);
        if (firstElement) {
            firstElement.focus();
            firstElement.scrollIntoView({ behavior: 'smooth', block: 'center' });
        }
        return;
    }

    const selectedDateVal = document.getElementById('selectedDate').value;
    const parts = selectedDateVal.split('/');

    const formData = {
        companyName: document.getElementById('companyName').value.trim(),
        nationalCode: document.getElementById('nationalCode').value.trim().replace(/\D/g, ''),
        registrationNumber: document.getElementById('registrationNumber').value.trim(),
        registrationDate: {
            year: parseInt(parts[0]),
            month: parseInt(parts[1]),
            day: parseInt(parts[2])
        },
        location: {
            state: document.getElementById('state').value,
            county: document.getElementById('county').value,
            section: document.getElementById('section').value,
            city: document.getElementById('city').value
        },
        registrationCenter: document.getElementById('registrationCenter').value
    };

    const submitBtn = document.querySelector('.submit-btn');
    submitBtn.disabled = true;
    submitBtn.textContent = 'در حال ثبت...';

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
            const generalError = document.getElementById('generalError');
            generalError.textContent = 'شرکت با موفقیت ثبت شد!';
            generalError.style.display = 'block';
            generalError.style.backgroundColor = '#d4edda';
            generalError.style.borderLeftColor = '#28a745';
            generalError.style.color = '#155724';
            generalError.classList.add('show');

            document.getElementById('companyForm').reset();
            resetSelect(document.getElementById('county'), 'ابتدا استان را انتخاب کنید');
            resetSelect(document.getElementById('section'), 'ابتدا شهرستان را انتخاب کنید');
            resetSelect(document.getElementById('city'), 'ابتدا بخش را انتخاب کنید');
            document.getElementById('registrationDateDay').innerHTML = '<option value="">انتخاب کنید</option>';

            document.querySelectorAll('.form-group input, .form-group select').forEach(el => {
                el.classList.remove('success');
            });

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
// Date Helpers
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
    daySelect.innerHTML = '<option value="">انتخاب کنید</option>';

    if (!month) {
        return;
    }

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

function loadRegistrationCenters() {
    const centerSelect = document.getElementById('registrationCenter');
    if (!centerSelect) return;

    const wrapper = centerSelect.closest ? centerSelect.closest('.searchable-select-wrapper') : null;
    const input = wrapper ? wrapper.querySelector('input') : null;
    const originalSelect = wrapper ? wrapper.querySelector('select') : centerSelect;
    const targetSelect = originalSelect || centerSelect;

    const token = sessionStorage.getItem('token');

    if (!token) {
        console.error('No token found');
        targetSelect.innerHTML = '<option value="">خطا در احراز هویت</option>';
        if (input) input.value = 'خطا';
        return;
    }

    targetSelect.innerHTML = '<option value="">در حال بارگذاری...</option>';
    targetSelect.disabled = true;
    if (input) input.value = 'در حال بارگذاری...';

    fetch('http://localhost:5000/api/registration-centers', {
        method: 'GET',
        headers: {
            'Content-Type': 'application/json',
            'Authorization': 'Bearer ' + token
        }
    })
    .then(response => {
        if (response.status === 401) {
            sessionStorage.clear();
            window.location.href = 'index.html';
            throw new Error('Session expired');
        }
        return response.json();
    })
    .then(data => {
        targetSelect.innerHTML = '<option value="">انتخاب کنید</option>';
        targetSelect.disabled = false;
        if (input) {
            input.value = '';
            input.placeholder = 'جستجوی مرکز ثبت...';
        }

        if (data.success && data.centers) {
            data.centers.forEach(center => {
                const option = document.createElement('option');
                option.value = center.id;
                option.textContent = center.name;
                targetSelect.appendChild(option);
            });

            if (wrapper && wrapper.rebuildDropdown) {
                wrapper.rebuildDropdown();
            }
        } else {
            targetSelect.innerHTML = '<option value="">خطا در بارگذاری مراکز ثبت</option>';
            console.error('Error loading centers:', data.message);
            if (input) input.value = 'خطا';
        }
    })
    .catch(error => {
        console.error('Error loading registration centers:', error);
        targetSelect.innerHTML = '<option value="">خطا در بارگذاری مراکز ثبت</option>';
        if (input) input.value = 'خطا';
    });
}