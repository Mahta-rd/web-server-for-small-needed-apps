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
                setupReportListeners();
                updateLastPage('report.html');
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

function setupReportListeners() {
    // Real-time validation for number fields
    const numberFields = [
        'fromPersonnelNum', 'toPersonnelNum', 'fromPnd', 'toPnd', 'fromYear', 'toYear'
    ];

    numberFields.forEach(fieldId => {
        const field = document.getElementById(fieldId);
        if (field) {
            field.addEventListener('input', function(e) {
                this.value = this.value.replace(/[^\d]/g, '');
            });

            field.addEventListener('blur', function() {
                validateReportForm();
            });
        }
    });

    const selects = ['fromMonth', 'toMonth', 'fromYear', 'toYear'];
    selects.forEach(selectId => {
        const select = document.getElementById(selectId);
        if (select) {
            select.addEventListener('change', function() {
                validateReportForm();
            });
        }
    });
}

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

    // Send logout request to server
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

    // Send change password request with token
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

// Report form validation
function validateReportForm() {
    const errors = {};

    const fromMonth = document.getElementById('fromMonth').value;
    const fromYear = document.getElementById('fromYear').value;
    const toMonth = document.getElementById('toMonth').value;
    const toYear = document.getElementById('toYear').value;

    const fromPersonnelNum = document.getElementById('fromPersonnelNum').value;
    const toPersonnelNum = document.getElementById('toPersonnelNum').value;

    const fromPnd = document.getElementById('fromPnd').value;
    const toPnd = document.getElementById('toPnd').value;

    clearReportErrors();

    if (!fromMonth) {
        errors.fromMonth = 'ماه "از" را انتخاب کنید';
    }
    if (!fromYear) {
        errors.fromYear = 'سال "از" را وارد کنید';
    }
    if (!toMonth) {
        errors.toMonth = 'ماه "تا" را انتخاب کنید';
    }
    if (!toYear) {
        errors.toYear = 'سال "تا" را وارد کنید';
    }

    if (fromYear && toYear && fromMonth && toMonth) {
        const fromDate = parseInt(fromYear) * 12 + parseInt(fromMonth);
        const toDate = parseInt(toYear) * 12 + parseInt(toMonth);

        if (toDate < fromDate) {
            errors.toYear = 'بازه زمانی "تا" باید بزرگتر یا مساوی "از" باشد';
        }
    }

    if (!fromPersonnelNum) {
        errors.fromPersonnelNum = 'شماره پرسنلی "از" نمی‌تواند خالی باشد';
    } else if (!/^\d{6}$/.test(fromPersonnelNum)) {
        errors.fromPersonnelNum = 'شماره پرسنلی باید 6 رقم باشد';
    }

    if (!toPersonnelNum) {
        errors.toPersonnelNum = 'شماره پرسنلی "تا" نمی‌تواند خالی باشد';
    } else if (!/^\d{6}$/.test(toPersonnelNum)) {
        errors.toPersonnelNum = 'شماره پرسنلی باید 6 رقم باشد';
    }

    if (fromPersonnelNum && toPersonnelNum && /^\d{6}$/.test(fromPersonnelNum) && /^\d{6}$/.test(toPersonnelNum)) {
        if (parseInt(toPersonnelNum) < parseInt(fromPersonnelNum)) {
            errors.toPersonnelNum = 'شماره پرسنلی "تا" باید بزرگتر یا مساوی "از" باشد';
        }
    }

    if (!fromPnd) {
        errors.fromPnd = 'PND "از" نمی‌تواند خالی باشد';
    } else if (!/^\d{3}$/.test(fromPnd)) {
        errors.fromPnd = 'PND باید 3 رقم باشد';
    }

    if (!toPnd) {
        errors.toPnd = 'PND "تا" نمی‌تواند خالی باشد';
    } else if (!/^\d{3}$/.test(toPnd)) {
        errors.toPnd = 'PND باید 3 رقم باشد';
    }

    if (fromPnd && toPnd && /^\d{3}$/.test(fromPnd) && /^\d{3}$/.test(toPnd)) {
        if (parseInt(toPnd) < parseInt(fromPnd)) {
            errors.toPnd = 'PND "تا" باید بزرگتر یا مساوی "از" باشد';
        }
    }

    return errors;
}

function clearReportErrors() {
    const errorElements = document.querySelectorAll('.error-message:not(.general-error)');
    errorElements.forEach(el => {
        el.textContent = '';
    });

    const generalError = document.getElementById('generalError');
    generalError.textContent = '';
    generalError.classList.remove('show');
}

function showReportErrors(errors) {
    if (Object.keys(errors).length > 0) {
        Object.keys(errors).forEach(fieldName => {
            const errorElement = document.getElementById(fieldName + 'Error');
            if (errorElement) {
                errorElement.textContent = errors[fieldName];
            }
        });
        return false;
    }
    return true;
}

function handleReportSubmit(event) {
    event.preventDefault();

    const errors = validateReportForm();

    if (!showReportErrors(errors)) {
        return;
    }

    const formData = {
        fromMonth: document.getElementById('fromMonth').value,
        fromYear: document.getElementById('fromYear').value,
        toMonth: document.getElementById('toMonth').value,
        toYear: document.getElementById('toYear').value,
        fromPersonnelNum: document.getElementById('fromPersonnelNum').value,
        toPersonnelNum: document.getElementById('toPersonnelNum').value,
        fromPnd: document.getElementById('fromPnd').value,
        toPnd: document.getElementById('toPnd').value,
        aggregation: document.getElementById('aggregation').checked,
        difference: document.getElementById('difference').checked
    };

    console.log('Form Data:', formData);

    const submitBtn = document.querySelector('.submit-btn');
    submitBtn.disabled = true;
    submitBtn.textContent = 'در حال تولید...';

    simulateReportGeneration(formData)
        .then(() => {
            alert('گزارش با موفقیت تولید شد');
            // Update session with last page (already done on load)
            updateLastPage('report.html');
        })
        .catch(error => {
            const generalError = document.getElementById('generalError');
            generalError.textContent = error.message || 'خطا در تولید گزارش';
            generalError.classList.add('show');
        })
        .finally(() => {
            submitBtn.disabled = false;
            submitBtn.textContent = 'تهیه گزارش';
        });
}

function simulateReportGeneration(formData) {
    return new Promise((resolve, reject) => {
        // Check session before making report
        verifySession()
            .then(isValid => {
                if (!isValid) {
                    sessionStorage.clear();
                    window.location.href = 'index.html';
                    reject({ message: 'نشست منقضی شده است' });
                    return;
                }

                // Simulate report generation
                const delay = Math.random() * 3000 + 1000;
                setTimeout(() => {
                    resolve();
                }, delay);
            })
            .catch(() => {
                reject({ message: 'خطا در بررسی نشست' });
            });
    });
}