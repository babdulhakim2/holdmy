function validateForm() {
    const targetNumber = document.getElementsByName('target_number')[0].value;
    const callbackNumber = document.getElementsByName('callback_number')[0].value;
    const errorDiv = document.getElementById('error-message');
    
    const ukNumberRegex = /^(?:0|\+?44)?[0-9\s-]{10,}$/;
    
    if (!ukNumberRegex.test(targetNumber) || !ukNumberRegex.test(callbackNumber)) {
        errorDiv.textContent = 'Please enter valid UK phone numbers';
        return false;
    }
    
    return true;
} 