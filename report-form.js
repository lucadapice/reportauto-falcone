document.addEventListener('DOMContentLoaded', function() {
    const waitForForm = setInterval(function() {
        const reportForm = document.getElementById('reportForm');
        if (reportForm) {
            clearInterval(waitForForm);
            const qtySelect = document.getElementById('qty');
            const queryContainers = reportForm.querySelectorAll('.query-container');
            const msgParagraph = document.getElementById('msg');

            function updateFormForQuantity(quantity) {
                queryContainers.forEach((container, index) => {
                    if (index + 1 <= quantity) {
                        container.style.display = 'block';
                        container.querySelector('input[type="text"]').setAttribute('required', true);
                    } else {
                        container.style.display = 'none';
                        container.querySelector('input[type="text"]').removeAttribute('required');
                    }
                });
            }

            function toggleSaveForLaterVisibility(quantity) {
                const saveForLaterContainer1 = document.querySelector('#query-container-1 .save-for-later');
                const saveForLaterLabel1 = document.querySelector('#query-container-1 label[for^="save-for-later"]');

                if (quantity === 1) {
                    if (saveForLaterContainer1) {
                        saveForLaterContainer1.style.display = 'none';
                    }
                    if (saveForLaterLabel1) {
                        saveForLaterLabel1.style.display = 'none';
                    }
                } else {
                    if (saveForLaterContainer1) {
                        saveForLaterContainer1.style.display = 'inline-block';
                    }
                    if (saveForLaterLabel1) {
                        saveForLaterLabel1.style.display = 'inline';
                    }
                }
            }

            updateFormForQuantity(parseInt(qtySelect.value));
            toggleSaveForLaterVisibility(parseInt(qtySelect.value));

            qtySelect.addEventListener('change', function() {
                updateFormForQuantity(parseInt(this.value));
                toggleSaveForLaterVisibility(parseInt(this.value));
            });

            reportForm.addEventListener('submit', function(event) {
                event.preventDefault();

                const quantity = parseInt(qtySelect.value);
                console.log('Quantità selezionata:', quantity);

                const query1Input = reportForm.querySelector('#query1');
                console.log('Elemento #query1 al momento dell\'invio:', query1Input);

                const saveLaterCheckbox = reportForm.querySelector('.save-for-later[data-index="1"]');
                console.log('Elemento .save-for-later[data-index="1"] al momento dell\'invio:', saveLaterCheckbox);

                const data = {
                    queries: query1Input ? [query1Input.value.trim().toUpperCase()] : [],
                    quantity: quantity,
                    save_for_later: saveLaterCheckbox ? saveLaterCheckbox.checked : false
                };
                const isLoggedIn = localStorage.getItem('reportauto_user_id');
                if (isLoggedIn) {
                    data.user_id = isLoggedIn;
                }
                console.log('Dati inviati per 1 report:', data);

                fetch('/api/acquisto-report', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify(data),
                })
                .then(response => response.json())
                .then(result => {
                    console.log('Risultato API per 1 report:', result);
                    if (result.session_id) {
                        window.location.href = `https://checkout.stripe.com/pay/${result.session_id}`;
                    } else if (result.error) {
                        msgParagraph.textContent = result.error;
                        msgParagraph.style.color = 'red';
                    }
                })
                .catch(error => {
                    console.error('Errore durante la chiamata API (1 report):', error);
                    msgParagraph.textContent = 'Si è verificato un errore.';
                    msgParagraph.style.color = 'red';
                });
            } else if (quantity === 3 || quantity === 5) {
                const redirectUrl = `/regisrazione-2/?from=acquista&quantity=${quantity}`;
                window.location.href = redirectUrl;
            }
        });
    }, 100);
});