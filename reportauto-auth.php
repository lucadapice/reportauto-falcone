<?php
/**
 * Plugin Name: ReportAuto Authentication
 * Description: Plugin per la gestione di registrazione e login personalizzati per ReportAuto.it.
 * Version: 1.0.0
 * Author: Simone Falcone
 */


// Funzione per generare il form di registrazione
function reportauto_registration_form() {
    ob_start();
    ?>
    <form id="registrationForm">
        <div>
            <label for="registerEmail">Email:</label>
            <input type="email" id="registerEmail" name="registerEmail" required>
        </div>
        <div>
            <label for="registerPassword">Password:</label>
            <input type="password" id="registerPassword" name="registerPassword" required>
        </div>
        <button type="submit">Registrati</button>
        <div id="registrationMessage"></div>
    </form>
    <?php
    return ob_get_clean();
}
add_shortcode('reportauto_register_form', 'reportauto_registration_form');

// Funzione per generare il form di login
function reportauto_login_form() {
    ob_start();
    ?>
    <form id="loginForm" method="post">
        <div>
            <label for="loginEmail">Email:</label>
            <input type="email" id="loginEmail" name="loginEmail" required>
        </div>
        <div>
            <label for="loginPassword">Password:</label>
            <input type="password" id="loginPassword" name="loginPassword" required>
        </div>
        <button type="submit">Accedi</button>
        <div id="loginMessage"></div>
    </form>
    <?php
    return ob_get_clean();
}
add_shortcode('reportauto_login_form', 'reportauto_login_form');

// Modificato: Rinominata la funzione e l'hook per evitare conflitti
function reportauto_auth_enqueue_scripts() {
    // Enqueue lo script solo se siamo sulla pagina di registrazione o iscriviti
    if (is_page('registrazione') || is_page('login')) {
        wp_enqueue_script('reportauto-auth-script', plugin_dir_url(__FILE__) . 'js/reportauto-auth.js', array('jquery'), '1.0', true);
        // Passa l'URL dell'API al tuo script JavaScript
        wp_localize_script('reportauto-auth-script', 'reportauto_api_settings', array(
            'api_url' => 'https://api.reportauto.it',
        ));
    }
}
add_action('wp_enqueue_scripts', 'reportauto_auth_enqueue_scripts');