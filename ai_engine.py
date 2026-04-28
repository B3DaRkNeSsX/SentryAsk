import os
import json
import re
from dotenv import load_dotenv
from openai import OpenAI

# Contributo Membro C: Gestione API IA (Groq) e Sentry Assistant RAG

load_dotenv()

# ================================================
# CLIENT GROQ
# La chiave viene letta esclusivamente da variabile d'ambiente (.env).
# ================================================
GROQ_BASE_URL  = "https://api.groq.com/openai/v1"
GROQ_MODEL     = "llama-3.1-8b-instant"   # aggiornato: llama3-8b-8192 è stato dismesso

def _get_client() -> OpenAI:
    """
    Restituisce un client Groq valido.
    Se la variabile d'ambiente manca, solleva un'eccezione.
    """
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        raise ValueError("GROQ_API_KEY non trovata nelle variabili d'ambiente.")
    return OpenAI(api_key=api_key, base_url=GROQ_BASE_URL)


# ================================================
# PARSING LINGUAGGIO NATURALE
# ================================================

def _fallback_parse(text: str) -> dict:
    """
    Parsing locale con euristiche regex.
    Usato solo se la chiamata API fallisce per motivi imprevisti.
    """
    spesa_mat = re.search(r'(\d+(?:[.,]\d+)?)\s*(?:€|euro)', text, re.IGNORECASE)
    valore    = float(spesa_mat.group(1).replace(',', '.')) if spesa_mat else 0.0
    lower     = text.lower()

    if valore > 0 or any(w in lower for w in ["comprare", "pagare", "acquistare", "costo"]):
        categoria = "Prezzo/Spesa"
    elif any(w in lower for w in ["fare", "completare", "ricorda", "chiama", "invia"]):
        categoria = "Task"
    else:
        categoria = "Nota/Info Generale"

    return {"titolo": text.capitalize(), "valore": valore, "categoria": categoria}


def parse_natural_language(text: str) -> dict:
    """
    Classifica l'input in categoria / titolo / valore tramite Groq llama3.
    """
    system_prompt = (
        "Sei un assistente per un Archivio Intelligente. Analizza l'input e rispondi "
        "SOLO con un oggetto JSON con le chiavi esatte: "
        "'titolo' (stringa breve descrittiva), "
        "'valore' (float: importo in euro se presente, altrimenti 0.0), "
        "'categoria' (scegli ESATTAMENTE tra: 'Task', 'Prezzo/Spesa', 'Nota/Info Generale'). "
        "Nessun testo aggiuntivo, solo il JSON."
    )
    try:
        client   = _get_client()
        response = client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user",   "content": text}
            ],
            response_format={"type": "json_object"},
            temperature=0.1,
            max_tokens=150
        )
        result = json.loads(response.choices[0].message.content)
        # Normalizza le chiavi obbligatorie
        result.setdefault("titolo",    text.capitalize())
        result.setdefault("valore",    0.0)
        result.setdefault("categoria", "Nota/Info Generale")
        return result
    except Exception:
        return _fallback_parse(text)


# ================================================
# SENTRY ASSISTANT — RAG CHAT
# ================================================

def _build_task_context(task_list: list) -> tuple[str, float]:
    """
    Costruisce il testo di contesto con tutti i task decriptati e
    calcola il totale spese. I dati sono solo in memoria (RAG volatile).
    Ritorna (testo_contesto, totale_spese).
    """
    if not task_list:
        return "Archivio vuoto.", 0.0

    totale = 0.0
    lines  = []
    for i, t in enumerate(task_list, 1):
        titolo  = t.get("titolo", t.get("task", "N/D"))
        cat     = t.get("categoria", "N/D")
        prio    = t.get("priorità", "Media")
        valore  = float(t.get("valore", t.get("spesa", 0.0)))
        stato   = "COMPLETATO" if t.get("completato") else "IN CORSO"
        totale += valore
        val_str = f" | EUR {valore:.2f}" if valore > 0 else ""
        lines.append(
            f"{i}. [{cat.upper()}] {titolo} | Priorita: {prio} | {stato}{val_str}"
        )

    return "\n".join(lines), totale


def chat_with_context(user_query: str, task_list: list) -> str:
    """
    RAG principale: inietta la lista dei task nel System Prompt e interroga Groq.
    Ogni chiamata è indipendente — i dati non vengono conservati sui server esterni.
    """
    context, totale = _build_task_context(task_list)

    system_prompt = (
        "Sei Sentry Assistant, un esperto di produttivita, risparmio e sicurezza digitale. "
        "Hai visione completa dell'archivio personale dell'utente (fornito sotto). "
        "Cita sempre i dati reali presenti: nomi dei task, importi specifici, priorita. "
        "Sii concreto, sintetico, tecnico. Niente emoji. Rispondi in italiano.\n\n"
        f"=== ARCHIVIO UTENTE (SESSIONE VOLATILE) ===\n"
        f"{context}\n"
        f"TOTALE SPESE MONITORATE: EUR {totale:.2f}\n"
        f"============================================"
    )

    try:
        client   = _get_client()
        response = client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user",   "content": user_query}
            ],
            temperature=0.6,
            max_tokens=500
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"[ERRORE CONNESSIONE] Impossibile raggiungere l'assistente: {e}"


def smart_reorder(task_list: list) -> str:
    """
    Analizza tutti i task e propone un ordine logico ottimale con spiegazione.
    Ordina per: urgenza implicita, importo, categoria, stato.
    """
    if not task_list:
        return "Nessun elemento da analizzare. Aggiungi dei task all'archivio prima."

    context, totale = _build_task_context(task_list)

    system_prompt = (
        "Sei Sentry Assistant, esperto di produttivita. "
        "Analizza la seguente lista di task e spese e proponi un ordine ottimale. "
        "Basa la priorita logica su: urgenza implicita nel testo, importo economico "
        "(spese elevate = priorita alta), tipo di attivita, stato (IN CORSO prima dei completati). "
        "Per ogni gruppo, spiega brevemente il motivo del riordino. "
        "Sii concreto e cita i nomi reali degli elementi. Niente emoji. Rispondi in italiano.\n\n"
        f"=== ARCHIVIO CORRENTE ===\n{context}\n"
        f"TOTALE: EUR {totale:.2f}\n========================="
    )

    try:
        client   = _get_client()
        response = client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user",   "content": "Proponi il riordine ottimale della lista con spiegazione."}
            ],
            temperature=0.5,
            max_tokens=700
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"[ERRORE CONNESSIONE] Impossibile completare l'analisi: {e}"

