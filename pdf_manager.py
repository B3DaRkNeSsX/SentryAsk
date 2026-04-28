import io
from fpdf import FPDF

class SentryReport(FPDF):
    def header(self):
        self.set_font("helvetica", "B", 15)
        # Colore primario (es. simile all'azzurro tech)
        self.set_text_color(88, 166, 255)
        self.cell(0, 10, "SentryTask AI - Report", border=0, align="C")
        self.ln(15)

    def footer(self):
        self.set_y(-15)
        self.set_font("helvetica", "I", 8)
        self.set_text_color(128, 128, 128)
        self.cell(0, 10, f"Pagina {self.page_no()}", align="C")

def genera_pdf(elenco_task: list) -> bytes:
    """
    Riceve la lista dei task decriptati e restituisce i byte di un file PDF
    pronti per essere scaricati tramite st.download_button.
    """
    pdf = SentryReport()
    pdf.add_page()
    pdf.set_font("helvetica", size=10)

    # Intestazione Tabella
    col_widths = [80, 45, 30, 35] # Titolo, Categoria, Priorita, Valore
    headers = ["Titolo", "Categoria", "Priorita", "Valore (EUR)"]

    pdf.set_fill_color(33, 38, 45) # Sfondo scuro per header tabella
    pdf.set_text_color(255, 255, 255)
    pdf.set_font(style="B")

    for w, h in zip(col_widths, headers):
        pdf.cell(w, 10, h, border=1, align="C", fill=True)
    pdf.ln()

    # Righe dati
    pdf.set_fill_color(240, 240, 240)
    pdf.set_text_color(0, 0, 0)
    pdf.set_font(style="")

    totale = 0.0
    fill = False
    for task in elenco_task:
        titolo = task.get("titolo", task.get("task", "N/D"))
        categoria = task.get("categoria", "N/D")
        priorita = task.get("priorità", "Media")
        valore = float(task.get("valore", task.get("spesa", 0.0)))
        totale += valore

        # Assicuriamoci che il testo non ecceda le celle, per semplicità qui facciamo un trim se troppo lungo,
        # oppure potremmo usare multi_cell, ma cell è più lineare per tabelle semplici
        titolo_trunc = (titolo[:42] + '...') if len(titolo) > 45 else titolo
        cat_trunc = (categoria[:20] + '...') if len(categoria) > 23 else categoria

        pdf.cell(col_widths[0], 10, titolo_trunc, border=1, fill=fill)
        pdf.cell(col_widths[1], 10, cat_trunc, border=1, align="C", fill=fill)
        pdf.cell(col_widths[2], 10, priorita, border=1, align="C", fill=fill)
        pdf.cell(col_widths[3], 10, f"{valore:.2f}", border=1, align="R", fill=fill)
        pdf.ln()
        fill = not fill # Righe alterne

    # Riga del totale
    pdf.set_font(style="B")
    pdf.set_fill_color(255, 255, 255)
    # Raggruppa le prime tre celle per il layout
    pdf.cell(sum(col_widths[:3]), 10, "TOTALE MONITORATO:", border=1, align="R")
    # Colore verde per il totale
    pdf.set_text_color(63, 185, 80)
    pdf.cell(col_widths[3], 10, f"{totale:.2f} EUR", border=1, align="R")
    pdf.ln()

    # Invece di salvare su file, esportiamo i bytes (perfetto per streamlit)
    pdf_bytes = bytes(pdf.output())
    return pdf_bytes
