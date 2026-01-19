document.addEventListener('DOMContentLoaded', function() {
    const loginBtn = document.getElementById('loginBtn');
    
    if (!loginBtn) {
        console.warn('Login button not found');
        return;
    }
    
    loginBtn.addEventListener('click', function() {
        const xhr = new XMLHttpRequest();
        xhr.open('GET', '/dashboard', true);
        xhr.onreadystatechange = function() {
            if (xhr.readyState === 4) {
                if (xhr.status === 200) {
                    window.location.href = '/dashboard';
                }
            }
        };
        xhr.send();
    });
    
    const urlParams = new URLSearchParams(window.location.search);
    const error = urlParams.get('error');
    if (error) {
        console.log('Ошибка аутентификации:', error);
    }
});
