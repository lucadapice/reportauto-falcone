<?php
if (!defined('ABSPATH')) {
    exit; // Exit if accessed directly.
}

class ReportAuto_Acquisto_API {

    public function __construct() {
        add_action('rest_api_init', [$this, 'register_routes']);
    }

    public function register_routes() {
        register_rest_route('reportauto/v1', '/registra-acquista', [
            'methods' => 'POST',
            'callback' => [$this, 'handle_registra_acquista'],
            'permission_callback' => '__return_true',
        ]);

        register_rest_route('reportauto/v1', '/registra-acquista-semplice', [ // NUOVA ROUTE
            'methods' => 'POST',
            'callback' => [$this, 'handle_registra_acquista_semplice'],
            'permission_callback' => '__return_true',
        ]);

        register_rest_route('reportauto/v1', '/genera-report-multipli', [ // NUOVA ROUTE
            'methods' => 'POST',
            'callback' => [$this, 'handle_genera_report_multipli'],
            'permission_callback' => '__return_logged_in', // Richiedi che l'utente sia loggato
        ]);

        // **NUOVA ROUTE PER L'ACQUISTO SINGOLO REPORT**
        register_rest_route('reportauto/v1', '/acquisto-report', [
            'methods' => 'POST',
            'callback' => [$this, 'handle_acquisto_report'],
            'permission_callback' => '__return_true',
        ]);
    }

    public function handle_registra_acquista($request) {
        $params = $request->get_params();

        if (empty($params['username']) || empty($params['email']) || empty($params['quantity']) || !isset($params['targhe_vin']) || !is_array($params['targhe_vin'])) {
            return new WP_Error('invalid_data', 'Dati mancanti o non validi.', ['status' => 400]);
        }

        $username = sanitize_user($params['username']);
        $email = sanitize_email($params['email']);
        $quantity = intval($params['quantity']);
        $targhe_vin = array_map('sanitize_text_field', $params['targhe_vin']);
        $save_for_later_global = isset($params['save_for_later']) && $params['save_for_later'] === true;
        $save_for_later_targhe = isset($params['save_for_later_targhe']) && is_array($params['save_for_later_targhe']) ? $params['save_for_later_targhe'] : [];

        // 1. Verifica se l'utente esiste già
        $user_id = username_exists($username);
        if (!$user_id && email_exists($email)) {
            $user = get_user_by('email', $email);
            $user_id = $user->ID;
        }

        if ($user_id) {
            // Utente esistente: effettua il login
            wp_set_current_user($user_id);
            wp_set_auth_cookie($user_id);
            do_action('wp_login', $username, get_user_by('id', $user_id));
            $user = get_user_by('id', $user_id);
        } else {
            // 2. Registra un nuovo utente
            $random_password = wp_generate_password();
            $user_id = wp_create_user($username, $random_password, $email);
            if (is_wp_error($user_id)) {
                return new WP_Error('registration_failed', 'Errore durante la registrazione: ' . $user_id->get_error_message(), ['status' => 500]);
            }

            // Effettua il login del nuovo utente
            wp_set_current_user($user_id);
            wp_set_auth_cookie($user_id);
            do_action('wp_login', $username, get_user_by('id', $user_id));
            $user = get_user_by('id', $user_id);

            // Invia email di benvenuto (opzionale)
            wp_new_user_notification($user_id, $random_password);
        }

        // 3. Salva le targhe/VIN associate all'utente
        $saved_targhe = [];
        foreach ($targhe_vin as $index => $targa) {
            if (!empty($targa)) {
                $save = $save_for_later_global || isset($save_for_later_targhe[$index + 1]); // L'indice in JS parte da 1
                if ($save) {
                    update_user_meta($user_id, 'reportauto_targa_' . ($index + 1), $targa);
                    $saved_targhe[$index + 1] = $targa;
                }
            }
        }

        // 4. Crea una sessione di pagamento Stripe
        try {
            require_once WP_PLUGIN_DIR . '/reportauto-acquisto-plugin/includes/stripe-php/init.php'; // Assicurati del percorso corretto
            \Stripe\Stripe::setApiKey('ppppp'); // *** RICONTROLLA LA TUA CHIAVE SEGRETA DI STRIPE ***

            $line_items = [
                [
                    'price_data' => [
                        'currency' => 'eur',
                        'unit_amount' => $this->get_report_price($quantity) * 100, // Prezzo in centesimi
                        'product_data' => [
                            'name' => $quantity . ' Report Auto',
                        ],
                    ],
                    'quantity' => 1,
                ],
            ];

            $checkout_session = \Stripe\Checkout\Session::create([
                'customer_email' => $user->user_email,
                'line_items' => $line_items,
                'mode' => 'payment',
                'success_url' => home_url('/acquisto-successo'), // Assicurati che queste pagine esistano
                'cancel_url' => home_url('/acquisto-annullato'),
                'metadata' => [
                    'user_id' => $user_id,
                    'quantity' => $quantity,
                    'targhe_vin' => json_encode($targhe_vin),
                    'save_for_later' => $save_for_later_global,
                    'saved_targhe' => json_encode($saved_targhe),
                ],
            ]);

            return rest_ensure_response(['redirect_url' => $checkout_session->url]);

        } catch (\Stripe\Exception\ApiErrorException $e) {
            return new WP_Error('stripe_error', 'Errore nella creazione della sessione di pagamento: ' . $e->getMessage(), ['status' => 500]);
        }
    }

    public function handle_registra_acquista_semplice($request) {
        $params = $request->get_params();

        if (empty($params['username']) || empty($params['email']) || empty($params['quantity'])) {
            return new WP_Error('invalid_data', 'Dati mancanti o non validi.', ['status' => 400]);
        }

        $username = sanitize_user($params['username']);
        $email = sanitize_email($params['email']);
        $quantity = intval($params['quantity']);

        // 1. Verifica e registra/logga l'utente (stessa logica di prima)
        $user_id = username_exists($username);
        if (!$user_id && email_exists($email)) {
            $user = get_user_by('email', $email);
            $user_id = $user->ID;
        }

        if ($user_id) {
            wp_set_current_user($user_id);
            wp_set_auth_cookie($user_id);
            do_action('wp_login', $username, get_user_by('id', $user_id));
            $user = get_user_by('id', $user_id);
        } else {
            $random_password = wp_generate_password();
            $user_id = wp_create_user($username, $random_password, $email);
            if (is_wp_error($user_id)) {
                return new WP_Error('registration_failed', 'Errore durante la registrazione: ' . $user_id->get_error_message(), ['status' => 500]);
            }
            wp_set_current_user($user_id);
            wp_set_auth_cookie($user_id);
            do_action('wp_login', $username, get_user_by('id', $user_id));
            $user = get_user_by('id', $user_id);
            wp_new_user_notification($user_id, $random_password);
        }

        // 2. Crea direttamente la sessione di pagamento Stripe
        try {
            require_once WP_PLUGIN_DIR . '/reportauto-acquisto-plugin/includes/stripe-php/init.php';
            \Stripe\Stripe::setApiKey('YOUR_STRIPE_SECRET_KEY');

            $line_items = [
                [
                    'price_data' => [
                        'currency' => 'eur',
                        'unit_amount' => $this->get_report_price($quantity) * 100,
                        'product_data' => [
                            'name' => $quantity . ' Report Auto',
                        ],
                    ],
                    'quantity' => 1,
                ],
            ];

            $checkout_session = \Stripe\Checkout\Session::create([
                'customer_email' => $user->user_email,
                'line_items' => $line_items,
                'mode' => 'payment',
                'success_url' => home_url('/inserimento-targhe?quantity=' . $quantity), // Nuova pagina per inserire le targhe dopo il pagamento
                'cancel_url' => home_url('/acquisto-annullato'),
                'metadata' => [
                    'user_id' => $user_id,
                    'quantity' => $quantity,
                ],
            ]);

            return rest_ensure_response(['redirect_url' => $checkout_session->url]);

        } catch (\Stripe\Exception\ApiErrorException $e) {
            return new WP_Error('stripe_error', 'Errore nella creazione della sessione di pagamento: ' . $e->getMessage(), ['status' => 500]);
        }
    }

    // **NUOVA FUNZIONE PER GESTIRE L'ACQUISTO SINGOLO**
    public function handle_acquisto_report($request) {
        $params = $request->get_params();

        if (empty($params['queries']) || !is_array($params['queries']) || empty($params['quantity'])) {
            return new WP_Error('invalid_data', 'Dati mancanti o non validi.', ['status' => 400]);
        }

        $quantity = intval($params['quantity']);
        $targa = sanitize_text_field($params['queries'][0]); // Dovrebbe esserci solo una targa
        $save_for_later = isset($params['save_for_later']) ? filter_var($params['save_for_later'], FILTER_VALIDATE_BOOLEAN) : false;
        $user_id = get_current_user_id(); // Potrebbe essere 0 se l'utente non è loggato

        // Se l'utente è loggato e ha scelto "Salva per dopo", salviamo la targa
        if ($user_id && $save_for_later) {
            $existing_targhe = get_user_meta($user_id, 'reportauto_targhe_salvate', true);
            if (!is_array($existing_targhe)) {
                $existing_targhe = [];
            }
            $existing_targhe[] = $targa;
            update_user_meta($user_id, 'reportauto_targhe_salvate', array_unique($existing_targhe));
        }

        // Crea una sessione di pagamento Stripe per 1 report
        try {
            require_once WP_PLUGIN_DIR . '/reportauto-acquisto-plugin/includes/stripe-php/init.php';
            \Stripe\Stripe::setApiKey('pppp'); // *** RICONTROLLA LA TUA CHIAVE SEGRETA DI STRIPE ***

            $line_items = [
                [
                    'price_data' => [
                        'currency' => 'eur',
                        'unit_amount' => $this->get_report_price($quantity) * 100,
                        'product_data' => [
                            'name' => $quantity . ' Report Auto',
                        ],
                    ],
                    'quantity' => 1,
                ],
            ];

            $checkout_session = \Stripe\Checkout\Session::create([
                'line_items' => $line_items,
                'mode' => 'payment',
                'success_url' => home_url('/acquisto-successo'), // Modifica se necessario
                'cancel_url' => home_url('/acquisto-annullato'), // Modifica se necessario
                'metadata' => [
                    'quantity' => $quantity,
                    'targa' => $targa,
                    'user_id' => $user_id,
                ],
            ]);

            return rest_ensure_response(['session_id' => $checkout_session->id]);

        } catch (\Stripe\Exception\ApiErrorException $e) {
            return new WP_Error('stripe_error', 'Errore nella creazione della sessione di pagamento: ' . $e->getMessage(), ['status' => 500]);
        }
    }

    public function handle_genera_report_multipli($request) {
        $params = $request->get_params();
        $user_id = get_current_user_id();

        if (!$user_id) {
            return new WP_Error('not_logged_in', 'Utente non loggato.', ['status' => 401]);
        }

        if (empty($params['quantity']) || !isset($params['targhe_vin']) || !is_array($params['targhe_vin'])) {
            return new WP_Error('invalid_data', 'Dati mancanti o non validi per la generazione dei report.', ['status' => 400]);
        }

        $quantity = intval($params['quantity']);
        $targhe_vin = array_map('sanitize_text_field', $params['targhe_vin']);

        if (count($targhe_vin) !== $quantity) {
            return new WP_Error('invalid_data', 'Il numero di targhe fornite non corrisponde alla quantità acquistata.', ['status' => 400]);
        }

        $report_urls = [];
        foreach ($targhe_vin as $index => $targa) {
            // Qui simuleremo la generazione del report e creeremo un URL fittizio
            $report_urls[] = home_url('/report-generato?targa=' . urlencode($targa) . '&id=' . uniqid());
            // Nella realtà, qui dovresti chiamare la tua logica di generazione dei report
        }

        return rest_ensure_response(['report_urls' => $report_urls]);
    }

    private function get_report_price($quantity) {
        if ($quantity === 1) return 23;
        if ($quantity === 3) return 58;
        if ($quantity === 5) return 80;
        return 0; // Prezzo predefinito o gestione errore
    }
}

new ReportAuto_Acquisto_API();
