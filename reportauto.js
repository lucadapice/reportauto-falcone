jQuery(document).ready(function($) {
    $('#reportauto-form').on('submit', function(e) {
        e.preventDefault();
        const vin = $('#vin').val();
        $('#reportauto-output').html('⏳ Generazione in corso...');

        $.ajax({
            url: 'http://213.165.77.149:5000/api/genera-report',
            method: 'POST',
            contentType: 'application/json',
            data: JSON.stringify({
                vin: vin,
                token: 'tok_reportauto_123'
            }),
            success: function(response) {
                if (response.pdf_url) {
                    $('#reportauto-output').html(`<p>✅ Report pronto: <a href="${response.pdf_url}" target="_blank">Scarica PDF</a></p>`);
                } else {
                    $('#reportauto-output').html('<p>⚠️ Nessun link ricevuto.</p>');
                }
            },
            error: function(xhr) {
                $('#reportauto-output').html('<p>❌ Errore nella generazione del report.</p>');
            }
        });
    });
});