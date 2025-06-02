import os, openai
from dotenv import load_dotenv
load_dotenv()

openai.api_key = os.getenv("OPENAI_KEY")
openai.api_base = os.getenv("OPENAI_ENDPOINT", "https://api.openai.com/v1")
MODEL = os.getenv("MODEL", "gpt-3.5-turbo")

def genera_testo(query: str) -> str:
    res = openai.ChatCompletion.create(
        model=MODEL,
        messages=[
            {"role":"system",
             "content":"Sei un sistema esperto di auto che scrive report professionali."},
            {"role":"user","content":f"Genera un report estremamente dettagliato in italiano con le informazioni che ti fornisco. non devi assolutamente fare riferimento alla fonte dei dati che non è altro che motorizzazzione e database pubblici ma non devi dirlo ne questo ne nomi di altre aziende. è importante che fai tutto con molta attenzione eche non lasci neanche un dettaglio a riguardo del veicolo. puoi fornire idee e spunti professionali ma é molto importante che siano di valore per il cliente che acquista il report. il testo che mi darai in risposta sar° poi convertito in pdf e mandato direttamente al cliente quindi non aggiungere nient'altro che non sia un report, anche messaggi affermativi a questo prompt non ci devo essere, deve essere lo testo che poi verrà dato al cliente. è molto importate che rielabori ttte le informazioni che ti do in input e che non le manipoli o alteri in nessun modo, tutte le informaizoni che ricevi in input devi usarle, non trascurarne neanche una. : {query}."}
        ],
        temperature=0.2
    )
    return res.choices[0].message["content"].strip()
