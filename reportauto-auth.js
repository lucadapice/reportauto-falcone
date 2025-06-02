jQuery(document).ready(function($) {
    $('#registrationForm').submit(function(event) {
        event.preventDefault();
        const email = $('#registerEmail').val();
        const password = $('#registerPassword').val();
        const registrationMessage = $('#registrationMessage');

        $.ajax({
            url: reportauto_api_settings.api_url + '/api/register',
            type: 'POST',
            contentType: 'application/json',
            data: JSON.stringify({ email: email, password: password }),
            dataType: 'json',
            success: function(response) {
                registrationMessage.html('<p style="color: green;">' + response.message + '</p>');
                // Potresti reindirizzare alla pagina di login qui: window.location.href = '/login';
            },
            error: function(error) {
                registrationMessage.html('<p style="color: red;">' + error.responseJSON.error + '</p>');
            }
        });
    });

    $('#loginForm').submit(function(event) {
        event.preventDefault();
        const email = $('#loginEmail').val();
        const password = $('#loginPassword').val();
        const loginMessage = $('#loginMessage');

        $.ajax({
            url: reportauto_api_settings.api_url + '/api/login',
            type: 'POST',
            contentType: 'application/json',
            data: JSON.stringify({ email: email, password: password }),
            dataType: 'json',
            success: function(response) {
                loginMessage.html('<p style="color: green;">' + response.message + ' - User ID: ' + response.user_id + '</p>');
                localStorage.setItem('reportauto_user_id', response.user_id); // Esempio di memorizzazione
                // Potresti reindirizzare alla pagina dell'account qui: window.location.href = '/account';
            },
            error: function(error) {
                loginMessage.html('<p style="color: red;">' + error.responseJSON.error + '</p>');
            }
        });
    });
});