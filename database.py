import json
import base64
import os
import uuid
from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.backends import default_backend

# Contributo Membro A: Logica di crittografia AES e gestione persistenza sicura dei dati

DB_FILE = "database_criptato.json"
# Un salt statico per derivare la chiave in modo deterministico dalla master password.
# Per una vera app in produzione dovrebbe essere generato casualmente e salvato separatamente.
STATIC_SALT = b'sentry_task_university_project_salt'

def _derive_key(password: str) -> bytes:
    """
    Deriva una chiave compatibile con Fernet (32 byte, URL-safe base64) 
    utilizzando PBKDF2HMAC partendo da una password in chiaro.
    """
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=STATIC_SALT,
        iterations=100000,
        backend=default_backend()
    )
    key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
    return key

def setup_db_if_not_exists(password: str):
    """
    Crea un file di database criptato di default (lista vuota) se non esiste.
    """
    if not os.path.exists(DB_FILE):
        _save_db([], password)

def _save_db(tasks: list, password: str):
    """
    Cripta in formato JSON e sovrascrive il file locale.
    Solleva InvalidToken (tramite Fernet) se la chiave non è adatta, 
    ma noi criptiamo quindi andrà a buon fine.
    """
    key = _derive_key(password)
    f = Fernet(key)
    json_data = json.dumps(tasks).encode('utf-8')
    encrypted_data = f.encrypt(json_data)
    
    with open(DB_FILE, "wb") as file:
        file.write(encrypted_data)

def get_tasks(password: str) -> list:
    """
    Legge e decripta i task. Se la password è sbagliata solleva ValueError gestito in UI.
    Ritorna una lista di dizionari.
    """
    if not os.path.exists(DB_FILE):
        return []
        
    key = _derive_key(password)
    f = Fernet(key)
    
    with open(DB_FILE, "rb") as file:
        encrypted_data = file.read()
        
    try:
        decrypted_data = f.decrypt(encrypted_data)
        return json.loads(decrypted_data.decode('utf-8'))
    except InvalidToken:
        raise ValueError("Password errata. Impossibile decriptare il database.")
    except Exception as e:
        # File corrotto o JSON invalido
        return []

def add_task(task_data: dict, password: str):
    """
    Aggiunge un singolo task alla base dati salvando su file.
    Assicura che ci sia un UUID e un valore default per lo stato.
    """
    tasks = get_tasks(password)
    task_id = str(uuid.uuid4())
    task_data['id'] = task_id
    if 'completato' not in task_data:
        task_data['completato'] = False
        
    tasks.append(task_data)
    _save_db(tasks, password)

def remove_task(task_id: str, password: str):
    """
    Rimuove un task tramite il suo ID.
    """
    tasks = get_tasks(password)
    tasks = [t for t in tasks if t.get('id') != task_id]
    _save_db(tasks, password)

def update_task_status(task_id: str, completato: bool, password: str):
    """
    Aggiorna lo stato di un task (completato o meno).
    """
    tasks = get_tasks(password)
    for t in tasks:
        if t.get('id') == task_id:
            t['completato'] = completato
            break
    _save_db(tasks, password)

def update_item(task_id: str, new_titolo: str, new_valore: float, new_priorita: str, password: str):
    """
    Modifica 'titolo', 'valore' e 'priorità' di un elemento senza alterare id e categoria.
    """
    tasks = get_tasks(password)
    for t in tasks:
        if t.get('id') == task_id:
            t['titolo'] = new_titolo
            t['valore'] = new_valore
            t['priorità'] = new_priorita
            # Ripuliamo vecchie chiavi obsolete per evitare confusione
            if 'task' in t: del t['task']
            if 'spesa' in t: del t['spesa']
            break
    _save_db(tasks, password)


def test_credentials(password: str) -> bool:
    """
    Tenta di accedere al DB (o crearlo se non esiste) per testare la Master Password.
    Ritorna True se corretto, False altrimenti (senza crashare).
    """
    try:
        if not os.path.exists(DB_FILE):
            setup_db_if_not_exists(password)
            return True
        get_tasks(password)
        return True
    except ValueError:
        return False
    except Exception:
        return False
