from flask import request, jsonify
from . import app, db
from .models import User, UserBalance, ReportOrder # Importa i nuovi modelli
from werkzeug.security import generate_password_hash, check_password_hash
import re
import threading
from datetime import datetime
from .ai_utils import genera_testo
from .pdf_utils import salva_pdf
from .stripe_utils import create_checkout_session, verify_webhook
import json, glob

VIN_RE = re.compile(r"^[A-HJ-NPR-Z0-9]{17}$", re.IGNORECASE)
VALID_TOKENS = {"reportauto.it": "tok_reportauto_123"}

def is_vin(s: str) -> bool:
    return bool(VIN_RE.match(s))

# --- Funzioni di utilità per il saldo report ---
def get_user_balance(user_id):
    user_balance = UserBalance.query.filter_by(user_id=user_id).first()
    return user_balance.balance if user_balance else 0

def update_user_balance(user_id, new_balance):
    user_balance = UserBalance.query.filter_by(user_id=user_id).first()
    if user_balance:
        user_balance.balance = new_balance
    else:
        # Crea un nuovo record se l'utente non ha ancora un saldo
        user_balance = UserBalance(user_id=user_id, balance=new_balance)
        db.session.add(user_balance)
    db.session.commit()

def decrementa_saldo(user_id, n=1):
    saldo_attuale = get_user_balance(user_id)
    if saldo_attuale >= n:
        update_user_balance(user_id, saldo_attuale - n)
        return True
    else:
        # Non sollevare un ValueError, ma restituisci False per gestire l'errore nell'endpoint
        return False

# --- Endpoint di Test ---
@app.route("/api/test", methods=["GET"])
def test():
    return jsonify({"status": "ok"})

# --- Endpoint di Registrazione ---
@app.route("/api/register", methods=["POST"])
def register():
    data = request.get_json(silent=True) or {}
    email = data.get("email")
    password = data.get("password")

    if not email or not password:
        return jsonify({"error": "Email e password sono obbligatori"}), 400

    if User.query.filter_by(email=email).first():
        return jsonify({"error": "Utente con questa email già esistente"}), 409

    new_user = User(email=email, password_hash=generate_password_hash(password))
    db.session.add(new_user)
    db.session.commit()

    # Inizializza il saldo a 0 per il nuovo utente
    update_user_balance(new_user.id, 0)

    return jsonify({"message": "Utente registrato con successo", "user_id": new_user.id}), 201

# --- Endpoint di Login ---
@app.route("/api/login", methods=["POST"])
def login():
    data = request.get_json(silent=True) or {}
    email = data.get("email")
    password = data.get("password")

    if not email or not password:
        return jsonify({"error": "Email e password sono obbligatori"}), 400

    user = User.query.filter_by(email=email).first()

    if user and check_password_hash(user.password_hash, password):
        # Per ora, restituiamo solo un messaggio di successo e l'ID utente
        # In un'app reale, qui genereresti un token JWT e lo imposteresti in un cookie HttpOnly
        response = jsonify({"message": "Login effettuato con successo", "user_id": user.id})
        # Imposta l'ID utente in un cookie (per check-login)
        response.set_cookie("user_id", str(user.id), httponly=True, secure=True, samesite='Lax') # Aggiunto secure=True per HTTPS
        return response, 200
    else:
        return jsonify({"error": "Credenziali non valide"}), 401

# --- NUOVO Endpoint: Verifica Login ---
@app.route('/api/check-login', methods=['GET'])
def check_login():
    user_id = request.cookies.get("user_id") # Recupera user_id dal cookie
    if user_id:
        user = User.query.get(user_id)
        if user:
            return jsonify({"logged_in": True, "user_id": user.id})
    return jsonify({"logged_in": False})

# --- NUOVO Endpoint: Ottieni Saldo Report ---
@app.route('/api/get-report-balance', methods=['GET'])
def get_report_balance():
    user_id = request.cookies.get("user_id") # O da un header di autenticazione
    if not user_id:
        return jsonify({"error": "Utente non autenticato"}), 401
    
    saldo = get_user_balance(user_id)
    return jsonify({"user_id": user_id, "balance": saldo}), 200

# --- Endpoint per Generazione Report (Modificato per Saldo) ---
@app.route("/api/genera-report", methods=["POST"])
def genera_report():
    data = request.get_json(silent=True) or {}
    query = (data.get("query") or "").strip().upper()
    token = data.get("token") # Questo token è per l'API key, non l'autenticazione utente
    user_id = request.cookies.get("user_id") # Recupera user_id dal cookie

    if not query:
        return jsonify({"error": "query mancante"}), 400
    
    # Se l'utente è loggato, verifica il saldo
    if user_id:
        if not decrementa_saldo(user_id):
            return jsonify({"error": "Saldo report insufficiente"}), 403
    # Altrimenti, se non loggato, richiede un token API valido
    elif token not in VALID_TOKENS.values():
        return jsonify({"error": "token non valido o utente non autenticato"}), 403

    # Generazione del report
    testo = genera_testo(f"{'VIN' if is_vin(query) else 'targa'} {query}")
    pdf_path = salva_pdf(testo)
    base = request.host_url.rstrip('/')
    return jsonify({"pdf_url": f"{base}/{pdf_path}"})


# --- Endpoint per Avviare Report (Webhook Stripe - Modificato) ---
def genera_e_salva_report(query, order_id, user_id=None): # Aggiunto user_id
    try:
        tipo = "VIN" if is_vin(query) else "targa"
        testo = genera_testo(f"{tipo} {query}")
        filename = f"{order_id}_{query}.pdf"
        filepath = salva_pdf(testo, filename)
        log_entry = f"{datetime.now().isoformat()},{order_id},{query},OK,{filepath}\n"
        
        # Se c'è un user_id, non decrementiamo qui, perché l'acquisto ha aggiunto il saldo
        # Il decremento avviene quando l'utente effettivamente genera un report tramite /api/genera-report
        
    except Exception as e:
        log_entry = f"{datetime.now().isoformat()},{order_id},{query},ERRORE,{e}\n"

    with open("logs/report_log.csv", "a") as f:
        f.write(log_entry)

@app.route("/api/avvia-report", methods=["POST"])
def avvia_report():
    data = request.get_json(silent=True) or {}
    query = (data.get("query") or "").strip().upper()
    order_id = (data.get("order_id") or "").strip()
    user_id = data.get("user_id") # Recupera user_id se inviato dal webhook o da altro

    if not query or not order_id:
        return jsonify({"status": "error", "message": "query o order_id mancanti"}), 400

    # Passa user_id al thread per log o future associazioni se necessario
    thread = threading.Thread(target=genera_e_salva_report, args=(query, order_id, user_id))
    thread.start()

    return jsonify({"status": "received", "message": "Generazione in corso"})


# --- NUOVO Endpoint: Gestione Acquisto Report (per frontend) ---
@app.route("/api/acquisto-report", methods=["POST"])
def acquisto_report():
    data = request.get_json(silent=True) or {}
    queries = data.get("queries", [])
    quantity = int(data.get("quantity", len(queries) or 1))
    user_id = data.get("user_id") # L'ID utente loggato dal frontend
    site = data.get("site", "b2c") # "b2c" default, "b2b" per reportscar.it

    if not queries or not user_id:
        return jsonify({"error": "queries o user_id mancante"}), 400
    
    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "Utente non trovato"}), 404

    try:
        # Crea la sessione Stripe
        session_id = create_checkout_session(queries, quantity, user_id=user_id) # Passa user_id a Stripe
        
        # Registra l'ordine nel database (lo stato iniziale potrebbe essere "pending")
        new_order = ReportOrder(
            order_id=session_id, # Usiamo session_id come order_id temporaneo
            user_id=user_id,
            quantity=quantity,
            date=datetime.utcnow()
        )
        db.session.add(new_order)
        db.session.commit()

        return jsonify({"session_id": session_id})
    except Exception as e:
        db.session.rollback() # In caso di errore, annulla la transazione
        return jsonify({"error": str(e)}), 400


# --- Stripe Checkout session (Modificato) ---
@app.route("/stripe/create-session", methods=["POST"])
def stripe_create_session():
    # Questo endpoint è ora destinato principalmente a chi non è loggato o per casi specifici.
    # Per acquisti con utente loggato, useremo /api/acquisto-report.
    data = request.get_json()
    queries = data.get("queries") or []
    quantity = int(data.get("quantity", len(queries) or 1))
    site = data.get("site", "b2c")
    user_id = data.get("user_id") # Potrebbe essere passato se l'utente è loggato ma usa ancora questo endpoint

    if not queries:
        return jsonify({"error": "missing queries"}), 400

    try:
        session_id = create_checkout_session(queries, quantity, user_id=user_id) # Passa user_id a Stripe
        return jsonify({"session_id": session_id})
    except Exception as e:
        return jsonify({"error": str(e)}), 400


# --- Stripe Webhook (Modificato per Saldo Report) ---
@app.route("/stripe/webhook", methods=["POST"])
def stripe_webhook():
    payload = request.data
    sig = request.headers.get("Stripe-Signature", "")
    try:
        event = verify_webhook(payload, sig)
    except Exception as e:
        return "Invalid signature", 400

    if event["type"] == "checkout.session.completed":
        sess = event["data"]["object"]
        queries = json.loads(sess["metadata"]["queries"])
        order_id = sess["id"]
        user_id = sess["metadata"].get("user_id") # Recupera user_id dai metadata di Stripe

        if user_id: # Se l'acquisto è associato a un utente loggato
            quantity_purchased = int(sess["metadata"].get("quantity", len(queries)))
            current_balance = get_user_balance(user_id)
            update_user_balance(user_id, current_balance + quantity_purchased)
            
            # Aggiorna l'order_id nel DB ReportOrder con l'ID di Stripe definitivo
            # Se l'ordine è stato creato in /api/acquisto-report con session_id come order_id temporaneo
            report_order = ReportOrder.query.filter_by(order_id=sess["id"]).first()
            if report_order:
                # Se l'ordine è già stato registrato, aggiorna lo stato o l'ID se necessario
                pass # L'ordine è già associato, il saldo è stato aggiornato
            else:
                # Questo caso si verifica se l'acquisto è avvenuto tramite stripe_create_session
                # senza passare per /api/acquisto-report (es. utente non loggato)
                # In questo caso, non associamo i crediti a un utente, ma generiamo i report
                # e li rendiamo scaricabili una tantum.
                # Per ora, non registriamo l'ordine in ReportOrder se user_id non c'era all'inizio
                pass # Non facciamo nulla qui, il saldo è gestito solo per utenti loggati

        # Genera i report per tutti, indipendentemente dal login
        for q in queries:
            threading.Thread(
                target=genera_e_salva_report,
                args=(q, order_id, user_id) # Passa user_id al thread
            ).start()

    return "OK", 200


# --- endpoint che restituisce il primo PDF di una sessione ---
@app.route("/stripe/session-file/<session_id>")
def get_session_file(session_id):
    pattern = f"static/reports/{session_id}_*.pdf"
    matches = glob.glob(pattern)
    if matches:
        return jsonify({"file": "/" + matches[0]})
    return jsonify({"file": None})