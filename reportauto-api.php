<?php
/**
 * Plugin Name: ReportAuto – Generatore Report Auto
 * Description: Plugin per inviare VIN al server API e ottenere un PDF del report.
 * Version: 1.0
 * Author: Simone Falcone
 */

function reportauto_enqueue_scripts() {
    wp_enqueue_script(
        'reportauto-script',
        plugin_dir_url(__FILE__) . 'reportauto.js',
        array('jquery'),
        null,
        true
    );

    // Iniettiamo endpoint e token nel JS
    wp_add_inline_script('reportauto-script', '
        const reportauto_api = {
            endpoint: "http://213.165.77.149:5000/api/genera-report",
            token: "tok_reportauto_123"
        };
    ');
}
add_action('wp_enqueue_scripts', 'reportauto_enqueue_scripts');

function reportauto_form_shortcode() {
    ob_start(); ?>
    <form id="reportauto-form">
        <label for="vin">Inserisci VIN:</label><br>
        <input type="text" id="vin" name="vin" required style="width: 300px; padding: 8px;">
        <button type="submit" style="margin-top: 10px;">Genera Report</button>
    </form>
    <div id="reportauto-output" style="margin-top: 20px;"></div>
    <?php return ob_get_clean();
}
add_shortcode('reportauto_form', 'reportauto_form_shortcode');