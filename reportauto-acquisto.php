<?php
/**
 * Plugin Name: ReportAuto Acquisto Form
 * Description: Mostra un form per l'acquisto di report.
 * Version: 1.0.0
 * Author: Simone Falcone
 */

// Impedisce l'accesso diretto al file del plugin
if (!defined('ABSPATH')) {
    exit;
}
require_once plugin_dir_path(__FILE__) . 'includes/class-reportauto-acquisto-api.php';

// Funzione per generare l'HTML del form
function reportauto_acquisto_form_shortcode() {
    ob_start(); // Inizia l'output buffering
    ?>
    <form id="reportForm">
        <div class="query-container" id="query-container-1">
            <label for="query1">Targa o VIN #1</label><br />
          	<input name="query1" id="query1" required="" type="text" placeholder="Es. ZAR940..." />
            <input type="checkbox" class="save-for-later" data-index="1" style="margin-left: 10px;"> <label style="margin-left: 5px;">Salva per dopo</label>
        </div>
        <div class="query-container extra-query-container" id="query-container-2" style="display: none;">
            <label for="query2">Targa o VIN #2</label><br />
            <input name="query2" type="text" placeholder="Es. ZAR940..." />
            <input type="checkbox" class="save-for-later" data-index="2" style="margin-left: 10px;"> <label style="margin-left: 5px;">Salva per dopo</label>
        </div>
        <div class="query-container extra-query-container" id="query-container-3" style="display: none;">
            <label for="query3">Targa o VIN #3</label><br />
            <input name="query3" type="text" placeholder="Es. ZAR940..." />
            <input type="checkbox" class="save-for-later" data-index="3" style="margin-left: 10px;"> <label style="margin-left: 5px;">Salva per dopo</label>
        </div>
        <div class="query-container extra-query-container" id="query-container-4" style="display: none;">
            <label for="query4">Targa o VIN #4</label><br />
            <input name="query4" type="text" placeholder="Es. ZAR940..." />
            <input type="checkbox" class="save-for-later" data-index="4" style="margin-left: 10px;"> <label style="margin-left: 5px;">Salva per dopo</label>
        </div>
        <div class="query-container extra-query-container" id="query-container-5" style="display: none;">
            <label for="query5">Targa o VIN #5</label><br />
            <input name="query5" type="text" placeholder="Es. ZAR940..." />
            <input type="checkbox" class="save-for-later" data-index="5" style="margin-left: 10px;"> <label style="margin-left: 5px;">Salva per dopo</label>
        </div>
        <p><label>Seleziona pacchetto</label><br /><select id="qty" style="max-width: 200px;">
            <option value="1">1 report – 23 €</option>
            <option value="3">3 report – 58 €</option>
            <option value="5">5 report – 80 €</option>
        </select></p>
        <p><button type="submit">Ottieni report</button></p>
        <p id="msg" style="margin-top: 10px;"> </p>
    </form>
    <?php
    $output = ob_get_clean(); // Ottieni il contenuto del buffer e lo pulisci
    return $output;
}
add_shortcode('reportauto_acquisto', 'reportauto_acquisto_form_shortcode');

// Funzione per includere il JavaScript
function reportauto_acquisto_enqueue_scripts_registrazione() {
    wp_enqueue_script('report-form-script', plugin_dir_url(__FILE__) . 'js/report-form.js', array(), '1.0', true);
}
add_action('wp_enqueue_scripts', 'reportauto_acquisto_enqueue_scripts_registrazione');