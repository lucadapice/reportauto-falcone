import os, stripe, json
from dotenv import load_dotenv
load_dotenv()

stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET")

PRICE = {
    1: os.getenv("PRICE_ID_1"),
    3: os.getenv("PRICE_ID_3"),
    5: os.getenv("PRICE_ID_5"),
}

import stripe
import json
import os

# Assicurati che queste variabili siano definite (es. dal tuo .env o configurazione)
# Esempio:
# stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
# YOUR_DOMAIN = os.getenv("YOUR_DOMAIN") # Es. "https://reportauto.it"
# PRICE = {
#     1: os.getenv("STRIPE_PRICE_ID_1_REPORT"),
#     3: os.getenv("STRIPE_PRICE_ID_3_REPORTS"),
#     5: os.getenv("STRIPE_PRICE_ID_5_REPORTS"),
# }

# Assicurati che stripe.api_key e PRICE siano configurati correttamente altrove nel tuo codice
# o nel file .env e caricati.

def create_checkout_session(queries: list[str], quantity: int, user_id: int = None):
    """
    Crea una sessione di checkout Stripe per l'acquisto di pacchetti di report.

    Args:
        queries (list[str]): Lista di VIN/targhe per cui generare i report.
        quantity (int): Quantità di report acquistati (3 o 5).
        user_id (int, optional): ID dell'utente loggato, se presente. Verrà aggiunto ai metadata di Stripe.

    Returns:
        str: L'ID della sessione di checkout Stripe.

    Raises:
        ValueError: Se il Price ID per la quantità specificata non è configurato.
    """
    # Recupera l'ID del prezzo Stripe in base alla quantità del PACCHETTO
    price_id = PRICE.get(quantity)
    if not price_id:
        raise ValueError(f"[ERRORE STRIPE] Price ID mancante per il pacchetto da {quantity} report. Controlla il file .env.")

    # Prepara i metadata per la sessione Stripe
    metadata = {
        "queries": json.dumps(queries), # Le query vengono serializzate in JSON string
        "quantity": str(quantity),      # La quantità del pacchetto
        "site": "b2c"                   # Esempio di un altro metadata (potrebbe essere dinamico)
    }

    # Aggiungi l'user_id ai metadata solo se è stato fornito
    if user_id is not None:
        metadata["user_id"] = str(user_id) # Converti l'ID utente in stringa per i metadata di Stripe

    # Crea la sessione di checkout Stripe
    session = stripe.checkout.Session.create(
        payment_method_types=["card"],
        mode="payment",
        line_items=[{"price": price_id, "quantity": 1}], # Acquistiamo 1 unità del PACCHETTO
        success_url="https://reportauto.it/success?session_id={CHECKOUT_SESSION_ID}",
        cancel_url="https://reportauto.it/cancel",
        metadata=metadata, # Passa i metadata alla sessione Stripe
    )

    return session.id


def verify_webhook(payload, sig_header):
    return stripe.Webhook.construct_event(payload, sig_header, WEBHOOK_SECRET)
