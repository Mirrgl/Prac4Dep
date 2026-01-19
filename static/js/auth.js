function performLogout() {
    const xhr = new XMLHttpRequest();
    xhr.open('GET', '/logout', true, 'logout', 'logout');
    xhr.onreadystatechange = function() {
        if (xhr.readyState === 4) {
            window.location.href = '/login';
        }
    };
    xhr.send();
}
