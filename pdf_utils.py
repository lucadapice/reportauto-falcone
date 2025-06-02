import os, uuid
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from textwrap import wrap

def salva_pdf(testo: str, filename: str = None) -> str:
    os.makedirs("static/reports", exist_ok=True)
    if not filename:
        filename = f"{uuid.uuid4().hex[:8]}.pdf"
    filepath = f"static/reports/{filename}"

    c = canvas.Canvas(filepath, pagesize=A4)
    W, H = A4

    c.setFont("Helvetica-Bold", 20)
    c.setFillColorRGB(0, 0.46, 0.81)
    c.drawString(40, H - 60, "Report Veicolo – ReportAuto.it")
    c.setStrokeColorRGB(1, 0.88, 0)
    c.setLineWidth(3)
    c.line(40, H - 65, W - 40, H - 65)

    y = H - 100
    c.setFont("Helvetica", 11)
    c.setFillColorRGB(.2, .2, .2)
    for line in wrap(testo, 100):
        c.drawString(40, y, line)
        y -= 14
        if y < 50:
            c.showPage()
            y = H - 60

    c.save()
    return filepath
