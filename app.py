import os
from dotenv import load_dotenv

# ================================================
# AUTO-CREAZIONE .ENV + CARICAMENTO CHIAVE
# Strategia a tre livelli:
#   1. Legge da variabile d'ambiente di sistema
#   2. Legge dal file .env (creato se mancante)
#   3. Fallback hardcoded in ai_engine.py
# ================================================
ENV_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
if not os.path.exists(ENV_FILE):
    with open(ENV_FILE, "w") as _f:
        _f.write("GROQ_API_KEY=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\n")

load_dotenv(ENV_FILE, override=False)

# Iniezione diretta in os.environ come ulteriore garanzia
if not os.environ.get("GROQ_API_KEY"):
    os.environ["GROQ_API_KEY"] = "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"

import streamlit as st
import pandas as pd
import plotly.express as px
from ai_engine import parse_natural_language, chat_with_context, smart_reorder
import database
import pdf_manager

# Contributo Membro B: Interfaccia Streamlit e Data Visualization

st.set_page_config(page_title="SentryTask AI", page_icon="[S]", layout="wide")

# ================================================
# CSS — TEMA TECH/CYBER
# Tutti i blocchi HTML del CSS sono self-contained.
# Nel loop di rendering NON vengono mai aperti div
# in chiamate separate per evitare tag orfani visibili.
# ================================================
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&family=JetBrains+Mono:wght@400;600&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
    background-color: #0d1117;
    color: #c9d1d9;
}
.block-container { padding-top: 1.8rem !important; }
hr { border-color: #21262d !important; }

.badge {
    display: inline-block;
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.65rem;
    font-weight: 700;
    padding: 2px 7px;
    border-radius: 3px;
    letter-spacing: 0.8px;
}
.badge-alta  { background:rgba(248,81,73,0.12);  color:#f85149; border:1px solid rgba(248,81,73,0.35); }
.badge-media { background:rgba(227,179,65,0.12); color:#e3b341; border:1px solid rgba(227,179,65,0.35); }
.badge-bassa { background:rgba(63,185,80,0.12);  color:#3fb950; border:1px solid rgba(63,185,80,0.35); }

.chip {
    display: inline-block;
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.62rem;
    padding: 2px 7px;
    border-radius: 3px;
    background: #21262d;
    color: #8b949e;
    border: 1px solid #30363d;
    letter-spacing: 0.5px;
}

.section-label {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.68rem;
    color: #8b949e;
    text-transform: uppercase;
    letter-spacing: 1.5px;
    margin-bottom: 0.75rem;
}
.field-label {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.68rem;
    color: #8b949e;
    text-transform: uppercase;
    letter-spacing: 1.2px;
}

.app-header {
    border-bottom: 1px solid #21262d;
    padding-bottom: 1rem;
    margin-bottom: 1.5rem;
}
.app-header h1 {
    font-family: 'JetBrains Mono', monospace;
    font-size: 1.8rem;
    color: #58a6ff;
    letter-spacing: -0.5px;
    margin: 0;
}
.app-header p {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.78rem;
    color: #8b949e;
    margin: 4px 0 0 0;
}

.recap-label {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.68rem;
    color: #8b949e;
    text-transform: uppercase;
    letter-spacing: 1px;
    margin-bottom: 0.3rem;
}
.recap-total {
    font-family: 'JetBrains Mono', monospace;
    font-size: 2rem;
    font-weight: 700;
    color: #3fb950;
    line-height: 1.2;
}

section[data-testid="stSidebar"] {
    background: #0d1117;
    border-right: 1px solid #21262d;
}

.stButton > button {
    background: #21262d !important;
    color: #c9d1d9 !important;
    border: 1px solid #30363d !important;
    border-radius: 6px !important;
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 0.76rem !important;
    transition: all 0.18s ease !important;
}
.stButton > button:hover {
    background: #388bfd !important;
    color: #ffffff !important;
    border-color: #388bfd !important;
}

.stTextInput input, .stNumberInput input {
    background-color: #161b22 !important;
    border: 1px solid #30363d !important;
    color: #e6edf3 !important;
    font-family: 'JetBrains Mono', monospace !important;
    border-radius: 6px !important;
}
[data-baseweb="select"] > div {
    background-color: #161b22 !important;
    border: 1px solid #30363d !important;
    border-radius: 6px !important;
}
[data-baseweb="select"] span {
    color: #e6edf3 !important;
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 0.82rem !important;
}
[data-baseweb="popover"] li {
    background-color: #161b22 !important;
    color: #c9d1d9 !important;
    font-family: 'JetBrains Mono', monospace !important;
}
[data-baseweb="popover"] li:hover { background-color: #21262d !important; }

[data-testid="stChatMessage"] {
    background: #161b22 !important;
    border: 1px solid #21262d !important;
    border-radius: 8px !important;
    padding: 0.6rem 0.8rem !important;
    margin-bottom: 0.4rem !important;
    font-size: 0.82rem !important;
}

[data-testid="stVerticalBlockBorderWrapper"] {
    background: #161b22 !important;
    border: 1px solid #21262d !important;
    border-radius: 8px !important;
    margin-bottom: 0.4rem !important;
}
</style>
""", unsafe_allow_html=True)


# ================================================
# SESSION STATE
# ================================================
defaults = {
    "logged_in":    False,
    "password":     "",
    "editing_item": None,
    "chat_history": [],
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v


# ================================================
# SIDEBAR
# ================================================
with st.sidebar:
    st.markdown(
        "<span style='font-family:\"JetBrains Mono\",monospace;color:#58a6ff;"
        "font-size:1.05rem;font-weight:700;'>SentryTask AI</span><br>"
        "<span style='font-family:\"JetBrains Mono\",monospace;color:#8b949e;"
        "font-size:0.68rem;'>v3.1 // GROQ POWERED // LOCAL VAULT</span>",
        unsafe_allow_html=True
    )
    st.markdown("---")

    # ── NON LOGGATO ────────────────────────────
    if not st.session_state["logged_in"]:
        st.markdown("<span class='field-label'>MASTER PASSWORD</span>",
                    unsafe_allow_html=True)
        pwd_input = st.text_input("pw", type="password",
                                  label_visibility="collapsed",
                                  placeholder="Inserisci password...")
        if st.button("Accedi al Vault", use_container_width=True):
            if database.test_credentials(pwd_input):
                st.session_state["logged_in"] = True
                st.session_state["password"]  = pwd_input
                st.rerun()
            else:
                st.error("Accesso negato. Password errata.")
        st.markdown("---")
        st.markdown(
            "<span style='font-family:\"JetBrains Mono\",monospace;font-size:0.7rem;"
            "color:#8b949e;'>STATO: <span style='color:#f85149;font-weight:700;'>"
            "LOCKED</span></span>",
            unsafe_allow_html=True
        )

    # ── LOGGATO ────────────────────────────────
    else:
        st.markdown(
            "<span style='font-family:\"JetBrains Mono\",monospace;font-size:0.7rem;"
            "color:#8b949e;'>STATO: <span style='color:#3fb950;font-weight:700;'>"
            "UNLOCKED</span></span>",
            unsafe_allow_html=True
        )
        st.markdown("<br>", unsafe_allow_html=True)

        if st.button("Blocca e Esci", use_container_width=True):
            for k in defaults:
                st.session_state[k] = defaults[k]
            st.rerun()

        # ── SENTRY ASSISTANT ───────────────────
        st.markdown("---")
        # Header sezione
        st.markdown(
            "<span style='font-family:\"JetBrains Mono\",monospace;font-size:0.72rem;"
            "color:#58a6ff;text-transform:uppercase;letter-spacing:1.2px;"
            "font-weight:700;'>🤖 Sentry Assistant</span><br>"
            "<span style='font-family:\"JetBrains Mono\",monospace;font-size:0.65rem;"
            "color:#8b949e;'>RAG contestuale sul tuo archivio.</span>",
            unsafe_allow_html=True
        )
        # Banner ONLINE — self-contained, nessun div orfano
        st.markdown(
            "<span style='display:block;background:rgba(63,185,80,0.1);"
            "border:1px solid rgba(63,185,80,0.35);border-radius:5px;"
            "padding:4px 10px;margin-top:6px;"
            "font-family:\"JetBrains Mono\",monospace;"
            "font-size:0.68rem;color:#3fb950;letter-spacing:0.8px;'>"
            "● SENTRY ASSISTANT ONLINE</span>",
            unsafe_allow_html=True
        )
        st.markdown("<br>", unsafe_allow_html=True)

        # Bottone Smart Reorder
        if st.button("Ottimizza Ordine", use_container_width=True,
                     help="L'AI analizza e ri-ordina i task per priorita logica"):
            try:
                tasks_ctx = database.get_tasks(st.session_state["password"])
            except Exception:
                tasks_ctx = []
            with st.spinner("[ AI ] Analisi ordine..."):
                reply = smart_reorder(tasks_ctx)
            st.session_state["chat_history"].append(
                {"role": "assistant", "content": f"[SMART REORDER]\n\n{reply}"}
            )
            st.rerun()

        st.markdown("<br>", unsafe_allow_html=True)

        # Area messaggi — st.chat_message nativo, zero HTML strutturale
        chat_area = st.container(height=280)
        with chat_area:
            if not st.session_state["chat_history"]:
                st.markdown(
                    "<span style='font-family:\"JetBrains Mono\",monospace;"
                    "font-size:0.72rem;color:#8b949e;'>"
                    "// Invia un messaggio per iniziare...</span>",
                    unsafe_allow_html=True
                )
            else:
                for msg in st.session_state["chat_history"]:
                    with st.chat_message(msg["role"]):
                        st.markdown(msg["content"])

        # Form chat — st.text_input garantisce digitazione fluida
        with st.form(key="chat_form", clear_on_submit=True):
            user_msg = st.text_input(
                "msg",
                placeholder="Chiedi a Sentry Assistant...",
                label_visibility="collapsed"
            )
            invia = st.form_submit_button("Invia", use_container_width=True)

        if invia and user_msg.strip():
            st.session_state["chat_history"].append(
                {"role": "user", "content": user_msg.strip()}
            )
            try:
                tasks_ctx = database.get_tasks(st.session_state["password"])
            except Exception:
                tasks_ctx = []
            with st.spinner("[ AI ] Elaborazione..."):
                reply = chat_with_context(user_msg.strip(), tasks_ctx)
            st.session_state["chat_history"].append(
                {"role": "assistant", "content": reply}
            )
            st.rerun()

        st.caption(
            "🔒 [ SYSTEM NOTICE: Privacy garantita. "
            "Dati locali, elaborazione volatile. ]"
        )


# ================================================
# SCHERMATA DI BLOCCO
# ================================================
if not st.session_state["logged_in"]:
    st.markdown(
        "<span style='display:block;text-align:center;padding:5rem 2rem;"
        "font-family:\"JetBrains Mono\",monospace;'>"
        "<span style='font-size:1.5rem;color:#58a6ff;font-weight:700;'>"
        "VAULT LOCKED</span><br><br>"
        "<span style='font-size:0.8rem;color:#8b949e;'>"
        "Autenticati dal pannello laterale per accedere ai tuoi dati."
        "</span></span>",
        unsafe_allow_html=True
    )
    st.stop()


# ================================================
# MAIN — HEADER
# ================================================
pwd = st.session_state["password"]

st.markdown("""
<div class='app-header'>
    <h1>SentryTask AI</h1>
    <p>// Archivio Intelligente Locale &nbsp;&middot;&nbsp; Groq AI &nbsp;&middot;&nbsp; Crittografia Locale</p>
</div>
""", unsafe_allow_html=True)


# ================================================
# PANNELLO INSERIMENTO
# ================================================
st.markdown("<span class='field-label'>INPUT &gt; Linguaggio Naturale</span>",
            unsafe_allow_html=True)

ci, cp, cb = st.columns([3.5, 1.2, 0.9])
with ci:
    user_input = st.text_input(
        "inp", label_visibility="collapsed",
        placeholder="Comprare manga per 18 euro / Visita medica domani / WiFi fattura 48 euro...",
        key="main_input"
    )
with cp:
    st.markdown("<span class='field-label'>PRIORITA</span>", unsafe_allow_html=True)
    priorita_sel = st.selectbox("prio", ["Bassa", "Media", "Alta"],
                                index=1, label_visibility="collapsed")
with cb:
    st.markdown("<br>", unsafe_allow_html=True)
    execute = st.button("+ Aggiungi", use_container_width=True)

st.markdown("<hr style='margin:0.8rem 0 1.4rem 0;'>", unsafe_allow_html=True)

if execute:
    if user_input.strip():
        with st.spinner("[ AI ] Classificazione..."):
            res = parse_natural_language(user_input)
            res["priorità"] = priorita_sel
            try:
                database.add_task(res, pwd)
                st.success("Elemento aggiunto all'archivio.")
            except Exception:
                st.error("Errore durante il salvataggio.")
    else:
        st.warning("Campo vuoto. Inserisci un elemento da archiviare.")





# ================================================
# CARICA DATI
# ================================================
try:
    lista_info = database.get_tasks(pwd)
except Exception:
    st.error("Impossibile leggere l'archivio.")
    lista_info = []


# ================================================
# HELPER — solo inline HTML (span/code), zero div
# ================================================
PRIORITA_LIST = ["Bassa", "Media", "Alta"]

def badge_html(p: str) -> str:
    if "alta"  in p.lower(): return "<span class='badge badge-alta'>[ ALTA ]</span>"
    if "media" in p.lower(): return "<span class='badge badge-media'>[ MEDIA ]</span>"
    return "<span class='badge badge-bassa'>[ BASSA ]</span>"

def border_color(p: str) -> str:
    if "alta"  in p.lower(): return "#f85149"
    if "media" in p.lower(): return "#e3b341"
    return "#3fb950"

def cat_label(c: str) -> str:
    return {"Task": "TASK", "Prezzo/Spesa": "SPESA"}.get(c, "NOTA")

def prio_idx(p: str) -> int:
    if "alta"  in p.lower(): return 2
    if "media" in p.lower(): return 1
    return 0


# ================================================
# LAYOUT PRINCIPALE
# ================================================
col_lista, col_recap = st.columns([2.2, 1])

# ── LISTA ─────────────────────────────────────
with col_lista:
    st.markdown(
        f"<span class='section-label'>ARCHIVIO // {len(lista_info)} elementi</span>",
        unsafe_allow_html=True
    )

    if not lista_info:
        st.markdown(
            "<span style='display:block;text-align:center;padding:2rem;"
            "background:#161b22;border:1px dashed #30363d;border-radius:8px;"
            "font-family:\"JetBrains Mono\",monospace;color:#8b949e;font-size:0.82rem;'>"
            "// ARCHIVIO VUOTO</span>",
            unsafe_allow_html=True
        )
    else:
        for item in lista_info:
            prio      = item.get("priorità", "Media")
            cat       = item.get("categoria", "Nota/Info Generale")
            titolo    = item.get("titolo", item.get("task", "Elemento"))
            valore    = float(item.get("valore", item.get("spesa", 0.0)))
            done      = item.get("completato", False)
            iid       = item["id"]

            # ── EDIT MODE ─────────────────────
            if st.session_state["editing_item"] == iid:
                with st.container(border=True):
                    st.markdown(
                        f"<span style='font-family:\"JetBrains Mono\",monospace;"
                        f"font-size:0.7rem;color:#388bfd;'>[ EDIT MODE ] — {cat_label(cat)}</span>",
                        unsafe_allow_html=True
                    )
                    e1, e2, e3 = st.columns([2.5, 1, 1.2])
                    with e1:
                        nt = st.text_input("Testo", value=titolo,
                                           key=f"et_{iid}")
                    with e2:
                        nv = st.number_input("EUR", value=valore,
                                             step=0.5, min_value=0.0,
                                             key=f"ev_{iid}")
                    with e3:
                        np_ = st.selectbox("Prio", PRIORITA_LIST,
                                           index=prio_idx(prio),
                                           key=f"ep_{iid}")
                    b1, b2, _ = st.columns([0.25, 0.28, 0.47])
                    with b1:
                        if st.button("Salva", key=f"sv_{iid}"):
                            database.update_item(iid, nt, nv, np_, pwd)
                            st.session_state["editing_item"] = None
                            st.rerun()
                    with b2:
                        if st.button("Annulla", key=f"ca_{iid}"):
                            st.session_state["editing_item"] = None
                            st.rerun()

            # ── VIEW MODE ─────────────────────
            else:
                def _aggiorna(tid=iid, val=done):
                    database.update_task_status(tid, not val, pwd)

                def _modifica(tid=iid):
                    st.session_state["editing_item"] = tid

                def _elimina(tid=iid):
                    database.remove_task(tid, pwd)

                t_style = ("text-decoration:line-through;color:#8b949e;"
                           if (done and cat == "Task")
                           else "color:#e6edf3;font-weight:600;")

                v_html = (
                    f"&nbsp;&nbsp;<code style='color:#3fb950;"
                    f"font-family:\"JetBrains Mono\",monospace;font-size:0.75rem;'>"
                    f"EUR {valore:.2f}</code>"
                    if valore > 0 else ""
                )

                # Card: singola stringa self-contained, zero tag orfani
                card = (
                    f"<span style='display:block;background:#161b22;"
                    f"border:1px solid #21262d;"
                    f"border-left:3px solid {border_color(prio)};"
                    f"border-radius:8px;padding:0.75rem 1rem;'>"
                    f"<span style='{t_style}font-size:0.92rem;'>{titolo}</span><br>"
                    f"<span style='font-size:0.7rem;font-family:\"JetBrains Mono\",monospace;"
                    f"color:#8b949e;display:inline-block;margin-top:4px;'>"
                    f"<span class='chip'>{cat_label(cat)}</span>"
                    f"&nbsp;{badge_html(prio)}{v_html}"
                    f"</span></span>"
                )

                cc, bc = st.columns([0.83, 0.17])
                with cc:
                    st.markdown(card, unsafe_allow_html=True)
                with bc:
                    if cat == "Task":
                        st.checkbox("", value=done, key=f"chk_{iid}",
                                    on_change=_aggiorna,
                                    label_visibility="collapsed")
                    st.button("📝 Edit",   key=f"mod_{iid}",
                              help="Modifica elemento", on_click=_modifica)
                    st.button("🗑️ Delete", key=f"del_{iid}",
                              help="Elimina elemento", on_click=_elimina)


# ── RIEPILOGO ─────────────────────────────────
with col_recap:
    spese = [i for i in lista_info
             if i.get("categoria") == "Prezzo/Spesa"
             or float(i.get("valore", i.get("spesa", 0.0))) > 0]
    totale = sum(float(i.get("valore", i.get("spesa", 0.0))) for i in spese)

    st.markdown("<span class='section-label'>RIEPILOGO ECONOMICO</span>",
                unsafe_allow_html=True)

    # Pannello totale — span self-contained
    st.markdown(
        f"<span style='display:block;background:#161b22;border:1px solid #21262d;"
        f"border-radius:10px;padding:1.4rem 1.6rem;'>"
        f"<span class='recap-label'>TOTALE MONITORATO</span><br>"
        f"<span class='recap-total'>EUR {totale:.2f}</span><br>"
        f"<span style='font-family:\"JetBrains Mono\",monospace;font-size:0.68rem;"
        f"color:#8b949e;'>{len(spese)} voci con importo</span>"
        f"</span>",
        unsafe_allow_html=True
    )

    if spese:
        st.markdown("<br>", unsafe_allow_html=True)
        df = pd.DataFrame([{
            "Nome":  i.get("titolo", i.get("task", "N/D")),
            "Costo": float(i.get("valore", i.get("spesa", 0.0)))
        } for i in spese])

        fig = px.bar(df, x="Nome", y="Costo",
                     color_discrete_sequence=["#388bfd"],
                     labels={"Costo": "EUR", "Nome": ""})
        fig.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font=dict(family="JetBrains Mono", color="#8b949e", size=10),
            margin=dict(t=10, b=0, l=0, r=0),
            xaxis=dict(showgrid=False, tickangle=-30, tickfont=dict(size=9)),
            yaxis=dict(showgrid=True, gridcolor="#21262d"),
            bargap=0.4
        )
        fig.update_traces(marker_line_width=0)
        st.plotly_chart(fig, use_container_width=True,
                        config={"displayModeBar": False})
    else:
        st.markdown(
            "<span style='display:block;font-family:\"JetBrains Mono\",monospace;"
            "font-size:0.75rem;color:#8b949e;margin-top:1.2rem;text-align:center;'>"
            "// nessuna voce economica</span>",
            unsafe_allow_html=True
        )

    # ── EXPORT PDF ────────────────────────────────
    st.markdown("<br><hr style='margin:1rem 0;'>", unsafe_allow_html=True)
    st.markdown("<span class='section-label'>ESPORTAZIONE DATI</span>", unsafe_allow_html=True)
    
    if lista_info:
        pdf_bytes = pdf_manager.genera_pdf(lista_info)
        st.download_button(
            label="📄 Scarica Resoconto PDF",
            data=pdf_bytes,
            file_name="SentryTask_Report.pdf",
            mime="application/pdf",
            use_container_width=True
        )
    else:
        st.button("📄 Scarica Resoconto PDF", disabled=True, use_container_width=True)
