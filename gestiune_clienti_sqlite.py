import sys
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import requests
import webbrowser
from tkcalendar import DateEntry
from datetime import datetime, date
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import csv
from tkinter import filedialog, messagebox
import os
from dotenv import load_dotenv
from tkinter import Toplevel, Label, Entry, Button
import sqlite3
from decimal import Decimal
from tkinter import filedialog
import shutil
import threading
import smtplib
from email.message import EmailMessage
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.styles import getSampleStyleSheet
from PIL import Image, ImageTk

"""
load_dotenv()  # încarcă variabilele din .env
API_KEY = os.getenv("API_KEY")
if not API_KEY:
    raise RuntimeError("API KEY lipsă! Verifică fișierul .env")
"""

API_KEY = "api aici"
ADMIN_PASSWORD = "cipri"  # parolă pentru ștergere client din baza de date

DB_NAME = "baza_date.db"


def creeaza_db_si_tabele(db_path):
    """Creează baza de date și tabelele dacă nu există"""
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Tabela clienti
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS tabela_date_clienti (
            Nr_Crt INTEGER PRIMARY KEY AUTOINCREMENT,
            Nume_Firma TEXT,
            Cui TEXT UNIQUE,
            Sediu_Social TEXT,
            Nr_Telefon TEXT,
            Mail TEXT,
            Reg_Comert TEXT,
            Tva TEXT,
            Administrator TEXT,
            Status_Firma TEXT
        )
        """)

        # Tabela sedii secundare
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS tabela_sedii_secundare (
            Nr_Crt INTEGER PRIMARY KEY AUTOINCREMENT,
            Id_Client INTEGER,
            Punct_Lucru TEXT,
            Model_Amef TEXT,
            Serie_Amef TEXT,
            Nui TEXT,
            Tip_Abonament TEXT,
            Data_Conect_Anaf TEXT,
            Tehnician TEXT,
            Data_Exp_Abon TEXT,
            Val_Ctr REAL,
            Data_Exp_Gprs TEXT,
            FOREIGN KEY(Id_Client) REFERENCES tabela_date_clienti(Nr_Crt)
        )
        """)

        # Tabela istoric abonamente
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS istoric_abonamente (
            Nr_Crt INTEGER PRIMARY KEY AUTOINCREMENT,
            id_client INTEGER,
            id_sediu INTEGER,
            serie_amef TEXT,
            tip_abonament TEXT,
            data_start TEXT,
            data_expirare TEXT,
            data_prelungire TEXT,
            observatii TEXT
        )
        """)

        conn.commit()
        conn.close()
        print("Baza de date și tabelele au fost create cu succes.")
    except Exception as e:
        print("!!! Eroare la crearea bazei sau a tabelelor:", e)
        messagebox.showerror("Eroare DB", f"Nu am putut crea baza de date: \n{e}")


def conectare_db():
    """Conectează aplicația la baza de date, creează DB dacă nu există"""
    try:
        if getattr(sys, 'frozen', False):
            base_path = os.path.dirname(sys.executable)
        else:
            base_path = os.path.dirname(__file__)

        db_path = os.path.join(base_path, DB_NAME)
        print("Calea bazei de date:", db_path)

        # Dacă baza de date nu există, o creăm
        if not os.path.exists(db_path):
            print("Baza de date nu există, o creez...")
            creeaza_db_si_tabele(db_path)

        # Conectăm la baza existentă
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        print("Conectare DB realizată cu succes.")
        return conn

    except Exception as e:
        print("!!! Eroare DB:", e)
        messagebox.showerror("Eroare DB", f"Nu ma pot conecta la baza de date: \n{e}")
        return None


# Exemplu de utilizare
if __name__ == "__main__":
    conn = conectare_db()
    if conn:
        conn.close()


# Functii pentru export/import baza date
def export_db():
    filedialog.asksaveasfilename(
        initialfile="baza_date.db",
        defaultextension=".db"
    )


def import_db():
    filedialog.askopenfilename(filetypes=[("SQLite DB", "*.db")])


"""
Functie pentru a uni 2 baze de date sqlite3 cu verificare si actualizare clienti
si cu creare fisier log cu actualizari
"""


def merge_sqlite_with_file_log(db_source_path, db_target_path, log_file_path="merge_log.txt"):
    # funcție simplă de log în fișier
    def log(msg):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(log_file_path, "a", encoding="utf-8") as f:
            f.write(f"[{timestamp}] {msg}\n")
        print(msg)  # păstrează și print-ul pe consolă

    # conectare baze
    src_conn = sqlite3.connect(db_source_path)
    src_conn.row_factory = sqlite3.Row
    src_cursor = src_conn.cursor()

    tgt_conn = sqlite3.connect(db_target_path)
    tgt_conn.row_factory = sqlite3.Row
    tgt_cursor = tgt_conn.cursor()

    # ================== CREAȚI TABELLELE DACA NU EXISTĂ ==================
    tgt_cursor.execute("""
    CREATE TABLE IF NOT EXISTS tabela_date_clienti (
        Nr_Crt INTEGER PRIMARY KEY AUTOINCREMENT,
        Nume_Firma TEXT,
        Sediu_Social TEXT,
        Cui TEXT UNIQUE,
        Nr_Telefon TEXT,
        Mail TEXT,
        Reg_Comert TEXT,
        Tva TEXT,
        Administrator TEXT,
        Status_Firma TEXT
    )
    """)

    tgt_cursor.execute("""
    CREATE TABLE IF NOT EXISTS tabela_sedii_secundare (
        Nr_Crt INTEGER PRIMARY KEY AUTOINCREMENT,
        Id_Client INTEGER,
        Punct_Lucru TEXT,
        Model_Amef TEXT,
        Serie_Amef TEXT,
        Nui TEXT,
        Tip_Abonament TEXT,
        Data_Conect_Anaf TEXT,
        Tehnician TEXT,
        Data_Exp_Abon TEXT,
        Val_Ctr REAL,
        Data_Exp_Gprs TEXT,
        FOREIGN KEY(Id_Client) REFERENCES tabela_date_clienti(Nr_Crt)
    )
    """)

    tgt_cursor.execute("""
    CREATE TABLE IF NOT EXISTS istoric_abonamente (
        Nr_Crt INTEGER PRIMARY KEY AUTOINCREMENT,
        id_client INTEGER,
        id_sediu INTEGER,
        serie_amef TEXT,
        tip_abonament TEXT,
        data_start TEXT,
        data_expirare TEXT,
        data_prelungire TEXT,
        observatii TEXT,
        FOREIGN KEY(id_client) REFERENCES tabela_date_clienti(Nr_Crt),
        FOREIGN KEY(id_sediu) REFERENCES tabela_sedii_secundare(Nr_Crt)
    )
    """)
    tgt_conn.commit()

    log("=== START MERGE BAZE DE DATE ===")

    # ================== MERGE CLIENTI ==================
    src_cursor.execute("SELECT * FROM tabela_date_clienti")
    clienti = src_cursor.fetchall()

    for client in clienti:
        tgt_cursor.execute("SELECT * FROM tabela_date_clienti WHERE Cui=?", (client["Cui"],))
        existing_client = tgt_cursor.fetchone()

        if existing_client:
            updated_fields = []
            updated_values = []
            for field in ["Nume_Firma", "Sediu_Social", "Nr_Telefon", "Mail", "Reg_Comert", "Tva", "Administrator",
                          "Status_Firma"]:
                if client[field] != existing_client[field]:
                    updated_fields.append(f"{field}=?")
                    updated_values.append(client[field])
            if updated_fields:
                updated_values.append(existing_client["Nr_Crt"])
                tgt_cursor.execute(f"UPDATE tabela_date_clienti SET {', '.join(updated_fields)} WHERE Nr_Crt=?",
                                   updated_values)
                log(f"Actualizat client CUI={client['Cui']}: {', '.join(updated_fields)}")
            else:
                log(f"Client CUI={client['Cui']} deja existent, fără modificări")
        else:
            fields = ["Nume_Firma", "Sediu_Social", "Cui", "Nr_Telefon", "Mail", "Reg_Comert", "Tva", "Administrator",
                      "Status_Firma"]
            placeholders = ",".join("?" * len(fields))
            values = [client[f] for f in fields]
            tgt_cursor.execute(f"INSERT INTO tabela_date_clienti ({','.join(fields)}) VALUES ({placeholders})", values)
            log(f"Adăugat client nou: CUI={client['Cui']}")

    tgt_conn.commit()

    # ================== MERGE SEDII SECUNDARE ==================
    src_cursor.execute("SELECT * FROM tabela_sedii_secundare")
    sedii = src_cursor.fetchall()

    for sediu in sedii:
        src_cursor.execute("SELECT Cui FROM tabela_date_clienti WHERE Nr_Crt=?", (sediu["Id_Client"],))
        cui = src_cursor.fetchone()["Cui"]

        tgt_cursor.execute("SELECT Nr_Crt FROM tabela_date_clienti WHERE Cui=?", (cui,))
        target_client = tgt_cursor.fetchone()
        if not target_client:
            log(f"Client CUI={cui} nu există în baza țintă, se sare sediul Serie_Amef={sediu['Serie_Amef']}")
            continue
        id_client_target = target_client["Nr_Crt"]

        tgt_cursor.execute("""
            SELECT * FROM tabela_sedii_secundare
            WHERE Id_Client=? AND Serie_Amef=? AND Nui=?
        """, (id_client_target, sediu["Serie_Amef"], sediu["Nui"]))
        existing_sediu = tgt_cursor.fetchone()

        if existing_sediu:
            updated_fields = []
            updated_values = []
            for field in ["Punct_Lucru", "Model_Amef", "Tip_Abonament", "Data_Conect_Anaf", "Tehnician",
                          "Data_Exp_Abon", "Val_Ctr", "Data_Exp_Gprs"]:
                val = sediu[field]
                if isinstance(val, Decimal):
                    val = float(val)
                if val != existing_sediu[field]:
                    updated_fields.append(f"{field}=?")
                    updated_values.append(val)
            if updated_fields:
                updated_values.append(existing_sediu["Nr_Crt"])
                tgt_cursor.execute(f"UPDATE tabela_sedii_secundare SET {', '.join(updated_fields)} WHERE Nr_Crt=?",
                                   updated_values)
                log(f"Actualizat sediu Serie_Amef={sediu['Serie_Amef']} client CUI={cui}: {', '.join(updated_fields)}")
            else:
                log(f"Sediu Serie_Amef={sediu['Serie_Amef']} client CUI={cui} deja existent, fără modificări")
        else:
            fields = ["Id_Client", "Punct_Lucru", "Model_Amef", "Serie_Amef", "Nui", "Tip_Abonament",
                      "Data_Conect_Anaf", "Tehnician", "Data_Exp_Abon", "Val_Ctr", "Data_Exp_Gprs"]
            values = [id_client_target] + [float(sediu[f]) if isinstance(sediu[f], Decimal) else sediu[f] for f in
                                           fields[1:]]
            placeholders = ",".join("?" * len(fields))
            tgt_cursor.execute(f"INSERT INTO tabela_sedii_secundare ({','.join(fields)}) VALUES ({placeholders})",
                               values)
            log(f"Adăugat sediu nou Serie_Amef={sediu['Serie_Amef']} client CUI={cui}")

    tgt_conn.commit()

    # ================== MERGE ISTORIC_ABONAMENTE ==================
    src_cursor.execute("SELECT * FROM istoric_abonamente")
    istoric = src_cursor.fetchall()

    for entry in istoric:
        src_cursor.execute("SELECT Cui FROM tabela_date_clienti WHERE Nr_Crt=?", (entry["id_client"],))
        cui = src_cursor.fetchone()["Cui"]

        tgt_cursor.execute("SELECT Nr_Crt FROM tabela_date_clienti WHERE Cui=?", (cui,))
        target_client = tgt_cursor.fetchone()
        if not target_client:
            log(f"Client CUI={cui} nu există în baza țintă, se sare istoricul Serie_Amef={entry['serie_amef']}")
            continue
        id_client_target = target_client["Nr_Crt"]

        tgt_cursor.execute("""
            SELECT Nr_Crt FROM tabela_sedii_secundare 
            WHERE Id_Client=? AND Serie_Amef=?
        """, (id_client_target, entry["serie_amef"]))

        target_sediu = tgt_cursor.fetchone()
        id_sediu_target = target_sediu["Nr_Crt"] if target_sediu else None

        if not id_sediu_target:
            log(f"Sediu lipsă în target pentru Serie_Amef={entry['serie_amef']}")
            continue

        tgt_cursor.execute("""
            SELECT * FROM istoric_abonamente 
            WHERE id_sediu=? AND tip_abonament=? AND data_start=?
        """, (id_sediu_target, entry["tip_abonament"], entry["data_start"]))
        existing_entry = tgt_cursor.fetchone()

        if existing_entry:
            updated_fields = []
            updated_values = []
            for field in ["data_expirare", "observatii"]:
                if entry[field] != existing_entry[field]:
                    updated_fields.append(f"{field}=?")
                    updated_values.append(entry[field])
            if updated_fields:
                updated_values.append(existing_entry["Nr_Crt"])
                tgt_cursor.execute(f"UPDATE istoric_abonamente SET {', '.join(updated_fields)} WHERE Nr_Crt=?",
                                   updated_values)
                log(f"Actualizat istoric abonament Serie_Amef={entry['serie_amef']} client CUI={cui}: {', '.join(updated_fields)}")
            else:
                log(f"Istoric abonament Serie_Amef={entry['serie_amef']} client CUI={cui} deja existent, fără modificări")
        else:
            fields = ["id_client", "id_sediu", "serie_amef", "tip_abonament", "data_start", "data_expirare",
                      "observatii"]
            values = [id_client_target, id_sediu_target] + [entry[f] for f in fields[2:]]
            placeholders = ",".join("?" * len(fields))
            tgt_cursor.execute(f"INSERT INTO istoric_abonamente ({','.join(fields)}) VALUES ({placeholders})", values)
            log(f"Adăugat istoric abonament Serie_Amef={entry['serie_amef']} client CUI={cui}")

    tgt_conn.commit()
    src_conn.close()
    tgt_conn.close()
    log("=== MERGE COMPLET FINALIZAT ===")

    def buton_update_baza(db_source_path, db_target_path):
        # cerere parola
        parola = simpledialog.askstring("Parola Admin", "Introduceți parola pentru update:", show="*")
        if parola != ADMIN_PASSWORD:
            messagebox.showerror("Eroare", "Parola incorectă!")
            return

        # confirmare
        if not messagebox.askyesno("Confirmare", "Sigur doriți să faceți update și merge la baza de date?"):
            return

        try:
            merge_sqlite_with_file_log(db_source_path, db_target_path)
            messagebox.showinfo("Succes", f"Update și merge complet realizat!\nVezi detalii în 'merge_log.txt'")
        except Exception as e:
            messagebox.showerror("Eroare", f"A apărut o eroare la merge: {e}")


# Final functie merge baze date

def update_baza_protejat():
    parola = simpledialog.askstring("Parola Admin", "Introduceți parola pentru update:", show="*")
    if parola != ADMIN_PASSWORD:
        messagebox.showerror("Eroare", "Parola incorectă!")
        return

    # Alegem baza de date sursa
    source = filedialog.askopenfilename(
        title="Selecteaza baza sursa (din care importi datele)",
        filetypes=[("SQLite DB", "*.db")]
    )
    if not source:
        return

    # Alegem baza de date tinta
    target = filedialog.askopenfilename(
        title="Selecteaza baza tinta (baza date master)",
        filetypes=[("SQLite DB", "*.db")]
    )
    if not source:
        return

    if source == target:
        messagebox.showerror("Eroare", "Nu poti selecta aceeasi baza")
        return

    # === BACKUP ===
    try:
        backup_file = backup_database(target)
    except Exception as e:
        messagebox.showerror("Eroare Backup", str(e))
        return

    # === Fereastră progres ===
    progress_win = Toplevel()
    progress_win.title("Merge în curs...")
    progress = ttk.Progressbar(progress_win, mode="indeterminate", length=400)
    progress.pack(padx=20, pady=20)
    progress["value"] = 0

    def run_merge():
        try:
            merge_sqlite_with_file_log(source, target)

            def finish_merge():
                progress.stop()
                progress_win.destroy()
                messagebox.showinfo("Succes", f"Merge finalizat!\nBackup salvat:\n{backup_file}")

                # ---------------- Întrebare trimitere email ----------------
                if messagebox.askyesno("Email", "Doriți să trimiteți backup-ul pe email?"):
                    destinatar = simpledialog.askstring("Email destinatar", "Introduceți adresa de email:")
                    if destinatar:
                        trimite_backup_email(backup_file, destinatar)
                        messagebox.showinfo("Email trimis", f"Backup-ul a fost trimis către {destinatar}")

            progress_win.after(0, finish_merge)

        except Exception as e:
            progress.stop()
            progress_win.destroy()
            messagebox.showerror("Eroare", str(e))

    threading.Thread(target=run_merge, daemon=True).start()


# Functie pentru backup baza date inainte de merge
def backup_database(db_path):
    if not os.path.exists(db_path):
        raise FileNotFoundError("Baza de date nu exista !")

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_name = f"{os.path.splitext(db_path)[0]}_backup_{timestamp}.db"
    shutil.copy2(db_path, backup_name)
    return backup_name


# Final functie backup baz adate

# Functie trimitere backup pe mail
def trimite_backup_email(backup_path, destinatar):
    msg = EmailMessage()
    msg["Subject"] = "Backup baza de date clienti SQLite3"
    msg["From"] = "instalari.secretdata@gmail.com"
    msg["To"] = destinatar
    msg.set_content("Atasat gasiti backup-ul bazei de date.")

    with open(backup_path, "rb") as f:
        file_data = f.read()
        file_name = os.path.basename(backup_path)
    msg.add_attachment(file_data, maintype="application", subtype="octet-stream", filename=file_name)

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
        smtp.login("instalari.secretdata@gmail.com", "ipns zunb qyxe bqbl")
        smtp.send_message(msg)


# =========================
# Functie de cautare firma in api dupa cod fiscal client
# =========================
def cauta_firma_firmeapi(cui):
    cui = cui.strip().replace("RO", "").replace("ro", "")
    url = f"https://www.firmeapi.ro/api/v1/firma/{cui}"
    headers = {"X-API-KEY": API_KEY, "Accept": "application/json"}
    try:
        r = requests.get(url, headers=headers, timeout=10)
        r.raise_for_status()
    except requests.RequestException:
        return None
    firma = r.json().get("data")
    if not firma:
        return None
    adresa_completa = ""
    sediu = firma.get("adresa_sediu_social", {})
    if isinstance(sediu, dict):
        strada = sediu.get("strada", "")
        numar = sediu.get("numar", "")
        localitate = ""
        judet = ""
        if isinstance(sediu.get("localitate"), dict):
            local = sediu["localitate"]
            localitate = local.get("nume", "")
            judet = local.get("judet", {}).get("nume", "")
        elif isinstance(sediu.get("localitate"), str):
            localitate = sediu.get("localitate")
        adresa_completa = f"{strada} {numar}, {localitate}, {judet}".strip(" ,")
    return {
        "cui": firma.get("cui", cui),
        "nume": firma.get("denumire", ""),
        "adresa": adresa_completa,
        "reg_comert": firma.get("nr_reg_com", "")
    }


"""
 Zona de FUNCȚII CRUD
 functie de conectare la baza de date sqlite date_clienti care are 3 tabele:
 tabela_date_clienti, tabela_sedii_secundare si tabela istoric_abonamente

"""


# Functia asta nu mai e utilizata in cod
def incarca_dropdown_puncte():
    for i in tree.get_children():
        tree.delete(i)
    conn = conectare_db()
    cursor = conn.cursor()
    cursor.execute("""SELECT d.Nr_Crt, d.Nume_Firma, d.Cui, d.Sediu_Social,
                      s.Punct_Lucru, s.Model_Amef, s.Serie_Amef
                      FROM tabela_date_clienti d
                      LEFT JOIN tabela_sedii_secundare s ON d.Nr_Crt = s.Id_Client""")
    for row in cursor.fetchall():
        tree.insert("", "end", values=row)
    conn.close()


# Functie pentru golirea tuturor campurilor din interfata
def resetare_toate_campurile():
    for e in entries.values():
        e.delete(0, tk.END)


# functie de resetare a campului de cautare client
def resetare_camp_cautare():
    search_entry.delete(0, tk.END)
    for item in tree.get_children():
        tree.delete(item)


# Funtie pentru modificarea datelor introduse gresit
"""Populează câmpurile cu datele clientului după CUI și punct de lucru pentru editare
Nu o mai folosesc in cod pentru ca si salvare client face acelasi lucru,
o pastrez, am dezactivat butonul atasat functiei
"""


def modifica_date_client():
    cui = entry_cui.get().strip()
    serie_amef = entry_serie_amef.get().strip()

    if not cui:
        messagebox.showwarning("Eroare", "Introduceți CUI-ul clientului")
        return

    conn = conectare_db()
    cursor = conn.cursor()

    cursor.execute("""
            SELECT d.Nume_Firma, d.Cui, d.Reg_Comert, d.Tva, d.Sediu_Social,
                   s.Punct_Lucru, s.Model_Amef, s.Serie_Amef, s.Nui,
                   s.Tehnician, s.Data_Conect_Anaf, s.Data_Exp_Abon, s.Val_Ctr, s.Data_Exp_Gprs
            FROM tabela_date_clienti d
            LEFT JOIN tabela_sedii_secundare s ON d.Nr_Crt = s.Id_Client
            WHERE d.Cui=? AND s.Serie_Amef=?
        """, (cui, serie_amef))
    result = cursor.fetchone()
    conn.close()

    if not result:
        messagebox.showinfo("Info", "Nu s-a găsit clientul sau punctul de lucru")
        return

    # Populare câmpuri
    mapping = {
        "Nume firmă": result["Nume_Firma"],
        "CUI Client": result["Cui"],
        "Nr. Registrul Comertului": result["Reg_Comert"],
        "Plătitor TVA": result["Tva"],
        "Adresă sediu": result["Sediu_Social"],
        "Punct de lucru": result["Punct_Lucru"],
        "Model Amef": result["Model_Amef"],
        "Serie Amef": result["Serie_Amef"],
        "Nui Amef": result["Nui"],
        "Tehnician Service": result["Tehnician"],
        "Data conectare Anaf": result["Data_Conect_Anaf"],
        "Data expirare abonament": result["Data_Exp_Abon"],
        "Valoare contract - RON": result["Val_Ctr"],
        "Data expirare gprs": result["Data_Exp_Gprs"]
    }

    for label, value in mapping.items():
        entries[label].delete(0, tk.END)
        entries[label].insert(0, value)


def cauta_firma():
    cui = entry_cui.get().strip()
    if not cui:
        messagebox.showwarning("Eroare", "Introduceți un CUI")
        return
    info = cauta_firma_firmeapi(cui)
    if not info:
        messagebox.showinfo("Info", "Firma nu a fost găsită")
        return
    entry_nume.delete(0, tk.END)
    entry_nume.insert(0, info["nume"])
    entry_adresa.delete(0, tk.END)
    entry_adresa.insert(0, info["adresa"])
    entry_reg_comert.delete(0, tk.END)
    entry_reg_comert.insert(0, info["reg_comert"])


"""
# Functie pentru introducerea clientilor in baza de date dar se si poate modifica datele cliewntului, 
La salvarea data expirare service si data expirare gprs , cu aceasta functie nu se salveaza in istoric abonamente 
decat cu butonul de prelungire abonament
"""


def salveaza_client():
    data = {
        "cui": entry_cui.get().strip(),
        "nume": entry_nume.get().strip(),
        "adresa": entry_adresa.get().strip(),
        "reg_comert": entry_reg_comert.get().strip(),
        "tva": entry_tva.get().strip(),
        "administrator": entry_administrator.get().strip(),
        "status_firma": entry_status_firma.get().strip(),
        "telefon": entry_telefon.get().strip(),
        "mail": entry_mail.get().strip(),
        "punct_lucru": entry_punct_lucru.get().strip(),
        "model_amef": entry_model_amef.get().strip(),
        "serie_amef": entry_serie_amef.get().strip(),
        "nui": entry_nui.get().strip(),
        "tip_abonament": entry_tip_abonament.get().strip(),
        "data_conect": entry_conectare_anaf.get().strip(),
        "tehnician": entry_tehnician.get().strip(),
        "data_exp": entry_data_exp.get().strip(),
        "val_ctr": entry_val_ctr.get().strip(),
        "data_exp_gprs": entry_data_exp_gprs.get().strip()
    }

    if not data["cui"] or not data["nume"]:
        messagebox.showwarning("Eroare", "CUI și Nume Firmă sunt obligatorii!")
        return

    if not data["serie_amef"]:
        messagebox.showwarning("Eroare", "Seria AMEF este obligatorie!")
        return
    conn = conectare_db()
    if not conn:
        return
    cursor = conn.cursor()

    # verific client existent
    try:
        cursor.execute("SELECT Nr_Crt FROM tabela_date_clienti WHERE Cui=? OR Reg_Comert=?",
                       (data["cui"], data["reg_comert"]))
        result = cursor.fetchone()

        if result:
            id_client = result["Nr_Crt"]
            cursor.execute("""
                UPDATE tabela_date_clienti
                SET Nume_Firma=?, Sediu_Social=?, Tva=?, Administrator=?,
                    Status_Firma=?, Nr_Telefon=?, Mail=?
                WHERE Nr_Crt=?
            """, (
                data["nume"], data["adresa"], data["tva"], data["administrator"],
                data["status_firma"], data["telefon"], data["mail"], id_client
            ))
            messagebox.showinfo("Info", f"Client existent. Datele au fost actualizate (Nr_Crt={id_client})")
        else:
            cursor.execute("""
                INSERT INTO tabela_date_clienti
                (Nume_Firma, Sediu_Social, Cui, Nr_Telefon, Mail, Reg_Comert, Tva, Administrator, Status_Firma)
                VALUES (?,?,?,?,?,?,?,?,?)
            """, (
                data["nume"], data["adresa"], data["cui"], data["telefon"], data["mail"],
                data["reg_comert"], data["tva"], data["administrator"], data["status_firma"]
            ))
            id_client = cursor.lastrowid
            messagebox.showinfo("Succes", f"Client nou adăugat (Nr_Crt={id_client})")

        # punct de lucru
        cursor.execute("SELECT 1 FROM tabela_sedii_secundare WHERE Id_Client=? AND Serie_Amef=?",
                       (id_client, data["serie_amef"]))
        if cursor.fetchone():
            cursor.execute("""
                UPDATE tabela_sedii_secundare
                SET Punct_Lucru=?, Model_Amef=?, Nui=?, Tip_Abonament=?,
                    Data_Conect_Anaf=?, Tehnician=?, Data_Exp_Abon=?,
                    Val_Ctr=?, Data_Exp_Gprs=?
                WHERE Id_Client=? AND Serie_Amef=?
            """, (
                data["punct_lucru"], data["model_amef"], data["nui"], data["tip_abonament"],
                data["data_conect"], data["tehnician"], data["data_exp"],
                data["val_ctr"], data["data_exp_gprs"], id_client, data["serie_amef"]
            ))
            messagebox.showinfo("Succes", f"Punct de lucru {data['serie_amef']} actualizat")
        else:
            cursor.execute("""
                INSERT INTO tabela_sedii_secundare
                (Id_Client, Punct_Lucru, Model_Amef, Serie_Amef, Nui,
                 Tip_Abonament, Data_Conect_Anaf, Tehnician, Data_Exp_Abon, Val_Ctr, Data_Exp_Gprs)
                VALUES (?,?,?,?,?,?,?,?,?,?,?)
            """, (
                id_client, data["punct_lucru"], data["model_amef"], data["serie_amef"], data["nui"],
                data["tip_abonament"], data["data_conect"], data["tehnician"],
                data["data_exp"], data["val_ctr"], data["data_exp_gprs"]
            ))
            messagebox.showinfo("Succes", f"Punct de lucru {data['serie_amef']} adăugat")

        conn.commit()
    except Exception as e:
        conn.rollback()
        messagebox.showerror("Eroare DB", str(e))
    finally:
        conn.close()


"""
Functie penntru calcularea automata a contractului in functie de situatia clientului
platitor/neplatitor tva sau deplasare/anual
"""


def calculeaza_valoare_contract(tip_abonament, platitor_tva):
    TVA = 0.21  # Aici modifici cand se schimba tva-ul
    tip_abonament = tip_abonament.strip().upper()
    platitor_tva = platitor_tva.strip().upper()
    valori_baza = {
        "DEPLASARE-INTERN": 120,
        "DEPLASARE-EXTERN": 135,
        "ANUAL": 300
    }
    if tip_abonament not in valori_baza:
        return ""
    valoare = valori_baza[tip_abonament]
    if platitor_tva == "DA":
        valoare *= (1 + TVA)
    return f"{valoare:.2f}"


# Functie pentru actualizare automata a campului UI
def actualizeaza_valoare_contract(event=None):
    tip = entry_tip_abonament.get()
    tva = entry_tva.get()
    valoare = calculeaza_valoare_contract(tip, tva)
    entry_val_ctr.delete(0, tk.END)
    entry_val_ctr.insert(0, valoare)


"""
Functie pentru a sterge un client din baza de date 
ATENTIE: La stergerea unui client se va sterge toate punctele de lucru si casele de marcat ale clientului
"""


def sterge_client():
    parola = simpledialog.askstring("Parola Admin", "Introduceți parola pentru ștergere:", show="*")
    if parola != ADMIN_PASSWORD:
        messagebox.showerror("Eroare", "Parola incorectă!")
        return
    cui = entry_cui.get().strip()
    if not cui:
        messagebox.showwarning("Eroare", "Introduceți CUI-ul clientului")
        return
    if not messagebox.askyesno("Confirmare", f"Sigur doriți să ștergeți clientul {cui} și toate punctele sale?"):
        return

    conn = conectare_db()
    if not conn:
        return
    cursor = conn.cursor()

    try:
        cursor.execute("SELECT Nr_Crt FROM tabela_date_clienti WHERE Cui=?", (cui,))
        result = cursor.fetchone()
        if not result:
            messagebox.showinfo("Info", "Clientul nu există")
            conn.close()
            return
        id_client = result["Nr_Crt"]
        cursor.execute("DELETE FROM tabela_sedii_secundare WHERE Id_Client=?", (id_client,))
        cursor.execute("DELETE FROM tabela_date_clienti WHERE Nr_Crt=?", (id_client,))
        conn.commit()
        conn.close()
        messagebox.showinfo("Succes", f"Client {cui} și punctele sale au fost șterse")
        resetare_toate_campurile()
        incarca_dropdown_puncte()
    except Exception as e:
        conn.rollback()
        messagebox.showerror("Eroare DB", str(e))

    finally:
        conn.close()


"""
Functie pentru a sterge doar punctul de lucru al clientuluiu, daca se inchide punctul de lucru
Nu se sterge si clientul din baza de date
"""


def sterge_punct():
    parola = simpledialog.askstring("Parola Admin", "Introduceți parola pentru ștergere:", show="*")
    if parola != ADMIN_PASSWORD:
        messagebox.showerror("Eroare", "Parola incorectă!")
        return
    serie_amef = entry_serie_amef.get().strip()
    if not serie_amef:
        messagebox.showwarning("Eroare", "Introduceți seria AMEF a punctului")
        return
    if not messagebox.askyesno("Confirmare", f"Sigur doriți să ștergeți punctul {serie_amef}?"):
        return
    conn = conectare_db()
    if not conn:
        return
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM tabela_sedii_secundare WHERE Serie_Amef=?", (serie_amef,))
        conn.commit()
        conn.close()
        messagebox.showinfo("Succes", f"Punct {serie_amef} a fost șters")
        resetare_toate_campurile()
        incarca_dropdown_puncte()
    except Exception as e:
        conn.rollback()
        messagebox.showerror("Eroare DB", str(e))

    finally:
        conn.close()


"""
Zona de cautare a unui client in baza de date
Functie pentru cautare client in baza de date, dupa cui, nume, serie casa sau nui
"""


def cauta_in_treeview():
    query = search_entry.get().strip().lower()

    # Curățare Treeview
    for item in tree.get_children():
        tree.delete(item)
    found = False  # Flag pentru a vedea daca am gasit la cautare ceva

    conn = conectare_db()
    if not conn:
        return
    cursor = conn.cursor()
    try:
        cursor.execute("""
            SELECT 
                d.Nr_Crt,
                d.Nume_Firma,
                d.Cui,
                d.Sediu_Social,
                d.Nr_Telefon,
                d.Mail,
                d.Reg_Comert,
                d.Tva,
                d.Administrator,
                d.Status_Firma,
                s.Punct_Lucru,
                s.Model_Amef,
                s.Serie_Amef,
                s.Nui,
                s.Tehnician,
                s.Data_Conect_Anaf,
                s.Data_Exp_Abon,
                s.Val_Ctr,
                s.Tip_Abonament,
                s.Data_Exp_Gprs

            FROM tabela_date_clienti d
            LEFT JOIN tabela_sedii_secundare s ON d.Nr_Crt = s.Id_Client
        """)

        rows = cursor.fetchall()
    except Exception as e:
        messagebox.showerror("Eroare DB", str(e))
        return
    finally:
        conn.close()

    for row in rows:
        # protecție la None
        nume = (row["Nume_Firma"] or "").lower()
        cui = (row["Cui"] or "").lower()
        serie = (row["Serie_Amef"] or "").lower()
        nui = (row["Nui"] or "").lower()

        if (
                query in str(row["Nume_Firma"]).lower()
                or query in str(row["Cui"]).lower()
                or query in str(row["Serie_Amef"]).lower()
                or query in str(row["Nui"]).lower()
        ):

            # Tag special pentru status firma non-activ
            status = (row["Status_Firma"] or "").strip().lower()
            if status in ["inchis", "suspendat", "inactiv"]:
                tag_final = "status_inactiv"  # Culoarea in tree a firmei inactiva
            else:
                tag_amef = calculeaza_tag_abonament(row["Data_Exp_Abon"])
                tag_gprs = calculeaza_tag_abonament_gprs(row["Data_Exp_Gprs"])
                tag_final = combina_taguri(tag_amef, tag_gprs)
            # inserare rând în Treeview cu tagurile corecte
            tree.insert("", "end", values=(
                row["Nr_Crt"],
                row["Nume_Firma"],
                row["Cui"],
                row["Sediu_Social"],
                row["Nr_Telefon"],
                row["Mail"],
                row["Reg_Comert"],
                row["Tva"],
                row["Administrator"],
                row["Status_Firma"],
                row["Punct_Lucru"],
                row["Model_Amef"],
                row["Serie_Amef"],
                row["Nui"],
                row["Tehnician"],
                row["Data_Conect_Anaf"],
                row["Data_Exp_Abon"],
                row["Val_Ctr"],
                row["Tip_Abonament"],
                row["Data_Exp_Gprs"]

            ),
                        tags=(tag_final,)
                        )
            print("STATUS DIN DB =", repr(row["Status_Firma"]))
            found = True  # Am gasit la cautare ceva
    # Daca nu am gasit nimic la cautare afiseaza nu am gait nimic in baza de date
    if not found:
        messagebox.showinfo("Rezultat cautare", f"Nici o inregistrare nu a fost gasita pentru: {query}")


"""
Functie in care combinam cele 2 taguri de amef si gprs
pentru colorarea coloanelor din tree cautare 
culoare rosie daca oricare din abonamente este expirat 
culoare galbena daca oricare din abonamnete urmeaza a expira in urmatoarele 30 de zile
culoare verde pentru ambele abonamente valabile
"""


def combina_taguri(tag_amef, tag_gprs):
    taguri = {tag_amef, tag_gprs}
    if "expirat" in taguri:
        return "expirat"
    if "avertizare" in taguri:
        return "avertizare"
    return "valid"


"""
Functie pentru a calcula cat timp mai este pana la expirare
"""


def calculeaza_tag_abonament(data_exp):
    if not data_exp:
        return "expirat"

    if isinstance(data_exp, str):

        try:
            data_exp = datetime.fromisoformat(data_exp).date()
        except ValueError:
            return "expirat"

    azi = date.today()
    zile = (data_exp - azi).days

    if zile < 0:
        return "expirat"
    elif zile <= 30:
        return "avertizare"
    else:
        return "valid"


def calculeaza_tag_abonament_gprs(data_exp):
    return calculeaza_tag_abonament(data_exp)


"""
Functie de combinare a abonamentelor pentru un singur pop-up
"""


def afiseaza_lista_abonamente(parent, rows, tip):
    azi = date.today()
    luna_curenta = azi.month
    anul_curent = azi.year

    canvas = tk.Canvas(parent)
    scrollbar = tk.Scrollbar(parent, orient="vertical", command=canvas.yview)
    scroll_frame = tk.Frame(canvas)

    scroll_frame.bind(
        "<Configure>",
        lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
    )

    canvas.create_window((0, 0), window=scroll_frame, anchor="nw")
    canvas.configure(yscrollcommand=scrollbar.set)

    canvas.pack(side="left", fill="both", expand=True)

    def on_mousewheel(event):
        canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    canvas.bind("<Enter>", lambda e: canvas.bind_all("<MouseWheel>", on_mousewheel))
    canvas.bind("<Leave>", lambda e: canvas.unbind_all("<MouseWheel>"))
    scrollbar.pack(side="right", fill="y")

    selected_label = {"widget": None, "bg": None}

    for r in rows:
        data_exp = r["data_exp"]
        if not data_exp:
            continue

        if isinstance(data_exp, str):
            try:
                data_exp = datetime.fromisoformat(data_exp).date()
            except ValueError:
                continue

        zile_ramase = (data_exp - azi).days

        if zile_ramase < 0:
            text_status = "EXPIRAT"
            culoare = "#f28c8c"
        elif 0 <= zile_ramase <= 30:
            text_status = f"expiră în {zile_ramase} zile"
            culoare = "#fff3b0"
        else:
            continue

        descriere = "abonament service" if tip == "amef" else "comunicație GPRS"

        text = (
            f"{r['Nume_Firma']} (CUI: {r['Cui']}) | "
            f"Seria: {r['Serie_Amef']} | "
            f"{descriere} | {data_exp} → {text_status}"
        )

        lbl = tk.Label(
            scroll_frame,
            text=text,
            bg=culoare,
            anchor="w",
            justify="left",
            font=("Arial", 10),
            pady=5
        )
        lbl.pack(fill="x", pady=2)

        # =============================
        # SELECTARE LA CLICK
        # =============================
        def on_click(event, label=lbl, bg=culoare, row=r):
            # reset selecție veche
            if selected_label["widget"]:
                selected_label["widget"].configure(bg=selected_label["bg"])

            # setează selecție nouă
            label.configure(bg="#9ecbff")
            selected_label["widget"] = label
            selected_label["bg"] = bg

            # DEBUG / FOLOSIRE MAI DEPARTE
            print("Selectat:", row)

        lbl.bind("<Button-1>", on_click)
    img = Image.open(resource_path("icons/pdf.png"))
    img = img.resize((20, 20))  # dimensiune modernă
    icon_pdf = ImageTk.PhotoImage(img)
    # Butonul de export clienti in pdf
    btn_export = tk.Button(
        parent,
        text="Exportă PDF",
        image=icon_pdf,
        compound="left",
        font=("Segoe UI", 10),
        bg="#f8f9fa",
        fg="#0d6efd",
        activebackground="#e9ecef",
        activeforeground="#212529",
        bd=1,  # activeaza conttur buton
        # relief="solid", stil solid la contur buton
        relief="raised",  # stil contur buton
        highlightthickness=0,
        padx=10,
        pady=6,
        cursor="hand2",
        command=lambda: exporta_clienti_pdf(rows, tip))
    btn_export.image = icon_pdf
    btn_export.pack(pady=5)

    def on_enter(e):
        btn_export["bg"] = "#e9f2ff"

    def on_leave(e):
        btn_export["bg"] = "#ffffff"

    btn_export.bind("<Enter>", on_enter)
    btn_export.bind("<Leave>", on_leave)


def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)


"""
Functie pentru a aparea in pop-ul cu abonamentele ce expira sau au expirat
"""


def alerta_abonamente_combinate():
    conn = conectare_db()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT 
            d.Nume_Firma,
            d.Cui,
            d.Status_Firma,
            s.Serie_Amef,
            s.Data_Exp_Abon,
            s.Data_Exp_Gprs
        FROM tabela_date_clienti d
        LEFT JOIN tabela_sedii_secundare s ON d.Nr_Crt = s.Id_Client
    """)

    rows = cursor.fetchall()
    conn.close()

    # pregătim datele separat
    amef_rows = []
    gprs_rows = []

    for r in rows:
        # filtram doar clientii activi
        if r["Status_Firma"] in ["Inchis", "Suspendat", "Inactiv"]:
            continue

        if r["Data_Exp_Abon"]:
            amef_rows.append({
                "Nume_Firma": r["Nume_Firma"],
                "Cui": r["Cui"],
                "Serie_Amef": r["Serie_Amef"],
                "data_exp": r["Data_Exp_Abon"]
            })
        if r["Data_Exp_Gprs"]:
            gprs_rows.append({
                "Nume_Firma": r["Nume_Firma"],
                "Cui": r["Cui"],
                "Serie_Amef": r["Serie_Amef"],
                "data_exp": r["Data_Exp_Gprs"]
            })

    # fereastra popup
    popup = tk.Toplevel()
    popup.title("Alerte Abonamente")
    popup.geometry("900x600")

    # ---------------- AMEF (sus) ----------------
    frame_amef = tk.LabelFrame(
        popup,
        text="Abonamente AMEF / Service",
        font=("Arial", 11, "bold"),
        padx=5,
        pady=5
    )
    frame_amef.pack(fill="both", expand=True, padx=10, pady=5)

    afiseaza_lista_abonamente(frame_amef, amef_rows, "amef")

    # ---------------- GPRS (jos) ----------------
    frame_gprs = tk.LabelFrame(
        popup,
        text="Abonamente Comunicație GPRS",
        font=("Arial", 11, "bold"),
        padx=5,
        pady=5
    )
    frame_gprs.pack(fill="both", expand=True, padx=10, pady=5)

    afiseaza_lista_abonamente(frame_gprs, gprs_rows, "gprs")


# Functie de export in pdf a clientilor cu abonamente pt luna curenta

pdfmetrics.registerFont(TTFont('ArialUnicode', 'arial.ttf'))  # asigură-te că ai arial.ttf în folder sau calea completă


def exporta_clienti_pdf(rows, tip):
    # Filtrăm doar ce expiră sau a expirat
    azi = date.today()
    rows_filtrate = []
    for r in rows:
        data_exp = r.get("data_exp")
        if not data_exp:
            continue

        if isinstance(data_exp, str):
            try:
                data_exp = datetime.fromisoformat(data_exp).date()
            except:
                continue

        zile_ramase = (data_exp - azi).days
        if zile_ramase < 0 or zile_ramase <= 30:  # doar expirat sau expira in 30 zile
            rows_filtrate.append(r)

    if not rows_filtrate:
        messagebox.showinfo("Export PDF", "Nu există date de exportat în intervalul de 30 zile!")
        return

    from tkinter import filedialog  # sus în fișier (o singură dată)

    file_path = filedialog.asksaveasfilename(
        defaultextension=".pdf",
        filetypes=[("PDF files", "*.pdf")],
        title="Salvează raportul PDF",
        initialfile=f"export_abonamente_{tip}.pdf"
    )

    if not file_path:
        return  # utilizatorul a apăsat Cancel

    doc = SimpleDocTemplate(
        file_path,
        pagesize=A4,
        rightMargin=15, leftMargin=15, topMargin=20, bottomMargin=20
    )

    styles = getSampleStyleSheet()
    styleN = styles["Normal"]
    styleN.fontName = "ArialUnicode"
    styleN.fontSize = 8
    styleN.leading = 10

    header = ["Nr", "Nume Firmă", "CUI", "Seria AMEF", "Tip Abonament", "Data Expirare", "Status"]
    data = [[Paragraph(col, styleN) for col in header]]

    for idx, r in enumerate(rows_filtrate, start=1):
        data_exp = r.get("data_exp")
        if isinstance(data_exp, str):
            data_exp = datetime.fromisoformat(data_exp).date()
        zile_ramase = (data_exp - azi).days
        text_status = "EXPIRAT" if zile_ramase < 0 else f"expiră în {zile_ramase} zile"
        tip_descriere = "abonament service" if tip == "amef" else "comunicație GPRS"

        row_data = [
            str(idx),
            r.get("Nume_Firma", ""),
            r.get("Cui", ""),
            r.get("Serie_Amef", ""),
            tip_descriere,
            str(data_exp),
            text_status
        ]
        data.append([Paragraph(str(cell), styleN) for cell in row_data])

    # Calcul lățimi coloane
    page_width, _ = A4
    total_margin = doc.leftMargin + doc.rightMargin
    max_width = page_width - total_margin
    col_widths = [25, 160, 70, 60, 100, 60, 60]
    sum_widths = sum(col_widths)
    if sum_widths > max_width:
        scale = max_width / sum_widths
        col_widths = [w * scale for w in col_widths]

    table = Table(data, colWidths=col_widths, repeatRows=1)
    table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), 'ArialUnicode'),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.whitesmoke]),
    ]))

    try:
        doc.build([table])
        messagebox.showinfo("Export PDF", f"PDF-ul a fost generat cu succes: {file_path}")
    except Exception as e:
        messagebox.showerror("Eroare Export PDF", f"A apărut o eroare la generarea PDF: {e}")


# =========================
# Functia care populeaza campurile de date din cele 2 coloane date client si sediu/amef
# =========================
def populare_campuri_treeview(event):
    selected = tree.focus()
    if not selected:
        return

    values = tree.item(selected, "values")

    mapping = {
        # date client
        "CUI Client": values[2],  # Cod Fiscal
        "Nume firmă": values[1],  # Nume Firma
        "Adresă sediu": values[3],  # Sediu Social
        "Numar Telefon": values[4],  # Nr Telefon
        "Adresa mail": values[5],  # Mail
        "Registrul Comertului": values[6],  # Reg Comert
        "Plătitor TVA": values[7],  # Tva
        "Administrator Firma": values[8],  # Administrator
        "Status Firma": values[9],  # Statusul Firmei Activ/Inchis

        # sediu secundar
        "Punct de lucru": values[10],  # Punct Lucru
        "Model Amef": values[11],  # Model AMEF
        "Serie Amef": values[12],  # Serie AMEF
        "Nui Amef": values[13],  # NUI
        "Tehnician Service": values[14],  # Tehnician srv
        "Data conectare Anaf": values[15],  # Data Conectare Anaf
        "Data expirare abonament": values[16],  # Data Exp. Abonament
        "Valoare contract - RON": values[17],  # Val_Ctr
        "Tip Abonament": values[18],  # Tip Abonament
        "Data expirare Gprs": values[19],  # Data expirarii comunicatie GPRS
    }

    for label, val in mapping.items():
        if label in entries:
            entries[label].delete(0, tk.END)
            entries[label].insert(0, val)


"""
Functie pentru a modifica tehnicianul de service
daca clientul trece la alt tehnician
"""


def modifica_tehnician():
    serie_amef = entry_serie_amef.get().strip()
    tehnician_nou = entry_tehnician.get().strip()

    if not serie_amef:
        messagebox.showwarning("Eroare", "Trebuie să introduci seria AMEF pentru a identifica punctul de lucru")
        return

    if not tehnician_nou:
        messagebox.showwarning("Eroare", "Trebuie să introduci numele tehnicianului")
        return

    # conectare la baza de date
    conn = conectare_db()
    cursor = conn.cursor()

    try:
        # verificam daca exista punctul de lucru cu seria AMEF introdusa
        cursor.execute("""
        SELECT Id_Client, Punct_Lucru FROM tabela_sedii_secundare WHERE Serie_Amef=%s
        """, (serie_amef,))
        result = cursor.fetchone()

        if not result:
            messagebox.showinfo("Info", "Nu există niciun punct de lucru cu această serie AMEF")
            return

        id_client, punct_lucru = result

        # actualizare doar a tehnicianului pentru punctul de lucru respectiv
        cursor.execute("""
        UPDATE tabela_sedii_secundare
        SET Tehnician=%s
        WHERE Id_Client=%s AND Serie_Amef=%s
        """, (tehnician_nou, id_client, serie_amef))

        conn.commit()
        messagebox.showinfo("Succes", f"Numele tehnicianului a fost modificat pentru seria AMEF {serie_amef}!")


    except Exception as e:
        messagebox.showerror("Eroare", f"Nu s-a putut modifica tehnicianul: {e}")
    finally:
        conn.close()


#############################################################################
"""
Functie pentru export baza date in format CSV
La exportare vor aparea 3 campuri de export pentru cele 3 tabele din baza de date
"""


def export_csv():
    conn = conectare_db()
    cursor = conn.cursor()

    # export tabela_date_clienti
    cursor.execute("SELECT * FROM tabela_date_clienti")
    clienti = cursor.fetchall()
    clienti_headers = [i[0] for i in cursor.description]

    # export tabela_sedii_secundare
    cursor.execute("SELECT * FROM tabela_sedii_secundare")
    sedii = cursor.fetchall()
    sedii_headers = [i[0] for i in cursor.description]

    # export tabela istoric_abonamente
    cursor.execute("SELECT * FROM istoric_abonamente")
    istoric = cursor.fetchall()
    istoric_headers = [i[0] for i in cursor.description]

    conn.close()

    # alegem folder și nume fișier
    file_path = filedialog.asksaveasfilename(defaultextension=".csv",
                                             filetypes=[("CSV files", "*.csv")],
                                             title="Export Bază de Date")
    if not file_path:
        return

    # salvăm tabela_date_clienti
    with open(file_path.replace(".csv", "_clienti.csv"), "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(clienti_headers)
        writer.writerows(clienti)

    # salvăm tabela_sedii_secundare
    with open(file_path.replace(".csv", "_sedii.csv"), "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(sedii_headers)
        writer.writerows(sedii)

    # salvam istoric_abonamente
    with open(file_path.replace("csv", "_istoric.csv"), "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(istoric_headers)
        writer.writerows(istoric)

    messagebox.showinfo("Succes",
                        f"Baza de date a fost exportată:\n{file_path}_clienti.csv,  {file_path}_sedii.csv, {file_path}_istoric.csv")


"""
Functie pentru import baza date in format CSV
La import vor aparea 3 campuri de importare pentru cele 3 tabele din baza de date
"""


def import_csv():
    # alegem fișierele CSV
    file_clienti = filedialog.askopenfilename(title="Selectează CSV tabela_date_clienti",
                                              filetypes=[("CSV files", "*.csv")])
    if not file_clienti:
        return

    file_sedii = filedialog.askopenfilename(title="Selectează CSV tabela_sedii_secundare",
                                            filetypes=[("CSV files", "*.csv")])
    if not file_sedii:
        return

    file_istoric = filedialog.askopenfilename(title="Selecteaza CSV istoric_abonamente",
                                              filetypes=[("CSV files", "*.csv")])
    if not file_istoric:
        return

    conn = conectare_db()
    cursor = conn.cursor()

    # import tabela_date_clienti
    with open(file_clienti, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            # verificăm dacă clientul există după CUI sau Reg_Comert
            cursor.execute("SELECT Nr_Crt FROM tabela_date_clienti WHERE Cui=%s OR Reg_Comert=%s",
                           (row['Cui'], row.get('Reg_Comert')))
            result = cursor.fetchone()
            if result:
                # update
                id_client = result[0]
                placeholders = ", ".join(f"{k}=%s" for k in row.keys() if k != "Nr_Crt")
                values = [row[k] for k in row.keys() if k != "Nr_Crt"]
                values.append(id_client)
                cursor.execute(f"UPDATE tabela_date_clienti SET {placeholders} WHERE Nr_Crt=%s", values)
            else:
                # insert
                columns = ", ".join(row.keys())
                placeholders = ", ".join(["%s"] * len(row))
                values = list(row.values())
                cursor.execute(f"INSERT INTO tabela_date_clienti ({columns}) VALUES ({placeholders})", values)

    # import tabela_sedii_secundare
    with open(file_sedii, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            # verificăm dacă punctul de lucru există după Id_Client și Serie_Amef
            cursor.execute("SELECT 1 FROM tabela_sedii_secundare WHERE Id_Client=%s AND Serie_Amef=%s",
                           (row['Id_Client'], row['Serie_Amef']))
            if cursor.fetchone():
                # update
                placeholders = ", ".join(f"{k}=%s" for k in row.keys() if k not in ["Id_Client", "Serie_Amef"])
                values = [row[k] for k in row.keys() if k not in ["Id_Client", "Serie_Amef"]]
                values.extend([row['Id_Client'], row['Serie_Amef']])
                cursor.execute(f"UPDATE tabela_sedii_secundare SET {placeholders} WHERE Id_Client=%s AND Serie_Amef=%s",
                               values)
            else:
                # insert
                columns = ", ".join(row.keys())
                placeholders = ", ".join(["%s"] * len(row))
                values = list(row.values())
                cursor.execute(f"INSERT INTO tabela_sedii_secundare ({columns}) VALUES ({placeholders})", values)

    # import tabela istoric abonamente
    with open(file_istoric, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            cursor.execute("SELECT 1 FROM istoric_abonamente WHERE id_sediu=%s AND tip_abonament=%s AND data_start=%s",
                           (row["id_sediu"], row["tip_abonament"], row["data_start"]))
            if cursor.fetchone():
                # update
                placeholders = ", ".join(
                    f"{k}=%s" for k in row.keys() if k not in ["id_sediu", "tip_abonament", "data_start"])
                values = [row[k] for k in row.keys() if k not in ["id_sediu", "tip_abonament", "data_start"]]
                values.extend([row["id_sediu"], row["tip_abonament"], row["data_start"]])
                cursor.execute(
                    f"UPDATE istoric_abonamente SET {placeholders} WHERE id_sediu=%s AND tip_abonament=%s AND data_start=%s",
                    values)
            else:
                # insert
                columns = ", ".join(row.keys())
                placeholders = ", ".join(["%s"] * len(row))
                values = list(row.values())
                cursor.execute(f"INSERT INTO istoric_abonamente ({columns}) VALUES ({placeholders})", values)

    conn.commit()
    conn.close()
    messagebox.showinfo("Succes", "Baza de date a fost importată cu succes!")


"""
Zona functiilor pentru istoricul abonamentelor service si gprs
Istoricul abonamentelor se va prelungi numai la buton prelungire abonamente
"""


def salveaza_istoric_abonament(id_client, id_sediu, serie_amef, tip_abonament, data_start, data_expirare,
                               observatii=""):
    conn = conectare_db()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO istoric_abonamente
        (id_client, id_sediu, serie_amef, tip_abonament, data_start, data_expirare, observatii)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (id_client, id_sediu, serie_amef, tip_abonament, data_start, data_expirare, observatii))
    conn.commit()
    conn.close()


def actualizeaza_sediu_secundar(id_sediu, tip_abonament, data_expirare):
    conn = conectare_db()
    cursor = conn.cursor()
    if tip_abonament == "SERVICE":
        cursor.execute("UPDATE tabela_sedii_secundare SET data_expirare_abonament=? WHERE Id=?",
                       (data_expirare, id_sediu))
    elif tip_abonament == "GPRS":
        cursor.execute("UPDATE tabela_sedii_secundare SET data_expirare_gprs=? WHERE Id=?",
                       (data_expirare, id_sediu))
    conn.commit()
    conn.close()


# --- Popup pentru prelungire abonament cu deplasare la 3 luni
def popup_prelungire_abonament_trimestrial(id_client, id_sediu, serie_amef, data_exp_service):
    popup = tk.Toplevel()
    popup.title("Prelungire abonament cu deplasare")
    popup.geometry("420x380")
    popup.grab_set()

    tk.Label(popup, text=f"Client: {id_client}", font=("Arial", 10, "bold")).pack(anchor="w", padx=10)
    tk.Label(popup, text=f"Serie AMEF: {serie_amef}", font=("Arial", 10, "bold")).pack(anchor="w", padx=10)

    # TIpul abonamentului adica cu deplasare la 3 luni buton creat numai pt a memora in istoric data deplasarii si incasarii
    tk.Label(popup, text="Abonament deplasare trimestrial")
    tip_var = tk.StringVar(value="SERVICE")

    # --- Data start ---
    tk.Label(popup, text="Data start prelungire").pack(pady=(10, 0))
    cal = DateEntry(popup, date_pattern="yyyy-mm-dd")
    cal.pack()

    def seteaza_data_initiala(*args):
        if tip_var.get() == "SERVICE" and data_exp_service:
            cal.set_date(data_exp_service)

    tip_var.trace_add("write", seteaza_data_initiala)
    seteaza_data_initiala()

    # --- CONFIRMA ---
    def confirma():
        tip = tip_var.get()
        data_start = cal.get_date()
        data_exp_noua = adauga_trei_luni(data_start)

        conn = conectare_db()
        cursor = conn.cursor()

        # Salvează ISTORIC
        cursor.execute("""
                INSERT INTO istoric_abonamente
                (id_client, id_sediu, serie_amef, tip_abonament,
                 data_start, data_expirare, observatii)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
            id_client, id_sediu, serie_amef,
            tip, data_start, data_exp_noua,
            "Prelungire manuală"
        ))

        # update sediu secundar
        if tip == "SERVICE":
            cursor.execute("""
                    UPDATE tabela_sedii_secundare
                    SET Data_Exp_Abon=?
                    WHERE Id_Client=? AND Serie_Amef=?
                """, (data_exp_noua, id_client, serie_amef))
        else:
            return

        conn.commit()
        conn.close()

        messagebox.showinfo("Succes", f"{tip} prelungit până la {data_exp_noua}")
        popup.destroy()
        cauta_in_treeview()  # refresh tabel

    tk.Button(
        popup,
        text="Prelungește cu 3 luni",
        bg="#cfe2f3",
        font=("Arial", 10, "bold"),
        command=confirma
    ).pack(pady=15)


# Final popup prelungire 3 luni

# Functie pentru prelungire 3 luni de abonament pentru clientii cu deplasare
def adauga_trei_luni(data):
    """
    Primește un obiect datetime.date și returnează data cu 3 luni adăugat
    """
    from dateutil.relativedelta import relativedelta
    # dacă e string, îl convertim la date
    if isinstance(data, str):
        try:
            data = datetime.fromisoformat(data).date()
        except ValueError:
            return None  # data invalidă
    return data + relativedelta(months=3)


# Final functie prelungire 3 luni

# Inceput functie buton prelungire 3  luni
def buton_prelungire_3_luni():
    selected = tree.selection()
    if not selected:
        messagebox.showwarning("Atenție", "Selectează un rând din tabel !")
        return
    row = tree.item(selected[0], "values")

    id_client = row[0]
    serie_amef = row[12]
    data_exp_service = row[16]
    # luăm id_sediu real
    conn = conectare_db()
    cursor = conn.cursor()
    cursor.execute("""
            SELECT Nr_Crt
            FROM tabela_sedii_secundare
            WHERE Id_Client=? AND Serie_Amef=?
        """, (id_client, serie_amef))
    result = cursor.fetchone()
    conn.close()

    if not result:
        messagebox.showerror("Eroare", "Sediu secundar negăsit!")
        return

    id_sediu = result["Nr_Crt"]

    popup_prelungire_abonament_trimestrial(
        id_client,
        id_sediu,
        serie_amef,
        data_exp_service
    )


# final functie buton prelungire 3 luni


# --- Popup pentru prelungire abonament anual ---
def popup_prelungire_abonament(id_client, id_sediu, serie_amef, data_exp_service, data_exp_gprs):
    popup = tk.Toplevel()
    popup.title("Prelungire abonament anual")
    popup.geometry("420x380")
    popup.grab_set()

    tk.Label(popup, text=f"Client: {id_client}", font=("Arial", 10, "bold")).pack(anchor="w", padx=10)
    tk.Label(popup, text=f"Serie AMEF: {serie_amef}", font=("Arial", 10)).pack(anchor="w", padx=10)

    # --- Tip abonament ---
    tk.Label(popup, text="Tip abonament anual").pack(pady=(10, 0))
    tip_var = tk.StringVar(value="SERVICE")
    cmb = ttk.Combobox(
        popup,
        textvariable=tip_var,
        values=["SERVICE", "GPRS"],
        state="readonly",
        width=20
    )
    cmb.pack()

    # --- Data start ---
    tk.Label(popup, text="Data start prelungire").pack(pady=(10, 0))
    cal = DateEntry(popup, date_pattern="yyyy-mm-dd")
    cal.pack()

    def seteaza_data_initiala(*args):
        if tip_var.get() == "SERVICE" and data_exp_service:
            cal.set_date(data_exp_service)
        elif tip_var.get() == "GPRS" and data_exp_gprs:
            cal.set_date(data_exp_gprs)

    tip_var.trace_add("write", seteaza_data_initiala)
    seteaza_data_initiala()

    # --- CONFIRMA ---
    def confirma():
        tip = tip_var.get()
        data_start = cal.get_date()
        data_exp_noua = adauga_un_an(data_start)

        conn = conectare_db()
        cursor = conn.cursor()

        # Salvează ISTORIC
        cursor.execute("""
            INSERT INTO istoric_abonamente
            (id_client, id_sediu, serie_amef, tip_abonament,
             data_start, data_expirare, observatii)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            id_client, id_sediu, serie_amef,
            tip, data_start, data_exp_noua,
            "Prelungire manuală"
        ))

        # update sediu secundar
        if tip == "SERVICE":
            cursor.execute("""
                UPDATE tabela_sedii_secundare
                SET Data_Exp_Abon=?
                WHERE Id_Client=? AND Serie_Amef=?
            """, (data_exp_noua, id_client, serie_amef))
        else:
            cursor.execute("""
                UPDATE tabela_sedii_secundare
                SET Data_Exp_Gprs=?
                WHERE Id_Client=? AND Serie_Amef=?
            """, (data_exp_noua, id_client, serie_amef))

        conn.commit()
        conn.close()

        messagebox.showinfo("Succes", f"{tip} prelungit până la {data_exp_noua}")
        popup.destroy()
        cauta_in_treeview()  # refresh tabel

    tk.Button(
        popup,
        text="Prelungește abonament anual",
        bg="#cfe2f3",
        font=("Arial", 10, "bold"),
        command=confirma
    ).pack(pady=15)


"""
Functie click dublu pe un client din campul de conectare
Si de aici la dublu click se deschide popup-ul de prelungire al abonamentului de service sau gprs
"""


def la_double_click(event):
    selected = tree.selection()
    if not selected:
        return

    row = tree.item(selected[0], "values")

    id_client = row[0]  # Nr_Crt client
    serie_amef = row[12]  # Serie AMEF
    data_exp_abon = row[16]  # Data expirare service
    data_exp_gprs = row[19]  # Data expirare gprs

    # luăm id_sediu real
    conn = conectare_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT Nr_Crt
        FROM tabela_sedii_secundare
        WHERE Id_Client=? AND Serie_Amef=?
    """, (id_client, serie_amef))
    result = cursor.fetchone()
    conn.close()

    if not result:
        messagebox.showerror("Eroare", "Sediu secundar negăsit!")
        return

    id_sediu = result["Nr_Crt"]

    popup_prelungire_abonament(
        id_client,
        id_sediu,
        serie_amef,
        data_exp_abon,
        data_exp_gprs
    )


# --- Functia apelata la buton ---
def buton_prelungire():
    selected = tree.selection()
    if not selected:
        messagebox.showwarning("Atenție", "Selectează un rând din tabel !")
        return

    la_double_click(None)


# Functie adaugare un an de abonament din data selectata in pupu-pul de prelungire
def adauga_un_an(data):
    """
    Primește un obiect datetime.date și returnează data cu 1 an adăugat
    """
    from dateutil.relativedelta import relativedelta
    # dacă e string, îl convertim la date
    if isinstance(data, str):
        try:
            data = datetime.fromisoformat(data).date()
        except ValueError:
            return None  # data invalidă
    return data + relativedelta(years=1)


# Functie pentru copierea datelor cu click dreapta
right_click_event = None  # Variabila globala pentru click dreapta


def copy_selection(mode="cell", event=None):
    """Copiaza in clipboard celula sau randul selectat"""
    selected_items = tree.selection()
    if not selected_items:
        return

    clipboard_text = ""
    if mode == "row":
        # Copiere randuri complete
        for item in selected_items:
            values = tree.item(item)["values"]
            clipboard_text += "\t".join(str(v) for v in values) + "\n"
    elif mode == "cell":
        # Copiere celula cu click dreapta
        if event is None:
            return
        col = tree.identify_column(event.x)
        col_index = int(col.replace("#", "")) - 1
        for item in selected_items:
            value = tree.item(item)["values"][col_index]
            clipboard_text += str(value) + "\n"

    root.clipboard_clear()
    root.clipboard_append(clipboard_text.strip())
    print(f"Copied:\n{clipboard_text.strip()}")


# Funtie pentru afisare si cautare live istoric abonamente
def popup_istoric_abonamente():
    popup = tk.Toplevel(root)
    popup.title("Istoric abonamente")
    popup.geometry("950x500")
    popup.grab_set()

    # ---------------- CAUTARE ----------------
    frame_cautare = tk.Frame(popup)
    frame_cautare.pack(fill="x", padx=10, pady=5)

    tk.Label(frame_cautare, text="Caută (Client / Serie AMEF / NUI):").pack(side="left")

    search_var = tk.StringVar()
    entry_search = tk.Entry(frame_cautare, textvariable=search_var, width=40)
    entry_search.pack(side="left", padx=5)

    # ---------------- TABEL ----------------
    frame_table = tk.Frame(popup)
    frame_table.pack(fill="both", expand=True, padx=10, pady=5)

    columns = (
        "client",
        "serie_amef",
        "nui",
        "tip",
        "data_start",
        "data_exp",
        "observatii"
    )

    tree = ttk.Treeview(frame_table, columns=columns, show="headings", selectmode="extended")
    tree.pack(fill="both", expand=True)

    headings = {
        "client": "Client",
        "serie_amef": "Serie AMEF",
        "nui": "NUI",
        "tip": "Tip Abonament",
        "data_start": "Data Start",
        "data_exp": "Data Expirare",
        "observatii": "Observații"
    }

    for col, txt in headings.items():
        tree.heading(col, text=txt)
        tree.column(col, width=120, anchor="w")

    # Scrollbar
    scrollbar = ttk.Scrollbar(frame_table, orient="vertical", command=tree.yview)
    scrollbar.pack(side="right", fill="y")
    tree.configure(yscrollcommand=scrollbar.set)

    # ---------------- DATE ----------------
    def incarca_date():
        tree.delete(*tree.get_children())

        conn = conectare_db()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT 
                d.Nume_Firma AS client,
                i.serie_amef,
                s.nui,
                i.tip_abonament,
                i.data_start,
                i.data_expirare,
                i.observatii
            FROM istoric_abonamente i
            JOIN tabela_date_clienti d
                ON d.Nr_Crt = i.id_client
            LEFT JOIN tabela_sedii_secundare s
                ON s.Id_Client = d.Nr_Crt
                AND s.Serie_Amef = i.serie_amef
            ORDER BY i.data_start DESC;
        """)
        rows = cursor.fetchall()
        conn.close()

        for row in rows:
            tree.insert("", "end", values=(
                row["client"],
                row["serie_amef"],
                row["nui"],
                row["tip_abonament"],
                row["data_start"],
                row["data_expirare"],
                row["observatii"]
            ))

    # ---------------- FILTRARE ----------------
    def filtreaza(*args):
        query = search_var.get().lower()
        tree.delete(*tree.get_children())

        conn = conectare_db()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT 
                d.Nume_Firma AS client,
                i.serie_amef,
                s.nui,
                i.tip_abonament,
                i.data_start,
                i.data_expirare,
                i.observatii
            FROM istoric_abonamente i
            JOIN tabela_date_clienti d
                ON d.Nr_Crt = i.id_client
            LEFT JOIN tabela_sedii_secundare s 
                ON s.Id_Client = d.Nr_Crt
                AND s.Serie_Amef = i.serie_amef
            WHERE 
                LOWER(d.Nume_Firma) LIKE ? OR
                LOWER(i.serie_amef) LIKE ? OR
                LOWER(s.nui) LIKE ?

            ORDER BY i.data_start DESC;
        """, (f"%{query}%", f"%{query}%", f"%{query}%"))

        rows = cursor.fetchall()
        conn.close()

        for row in rows:
            tree.insert("", "end", values=(
                row["client"],
                row["serie_amef"],
                row["nui"],
                row["tip_abonament"],
                row["data_start"],
                row["data_expirare"],
                row["observatii"]
            ))

    search_var.trace_add("write", filtreaza)

    incarca_date()

    # ----------------Buton pentru stergere istoric abonament------------
    # Butonul de ștergere
    tk.Button(
        popup,
        text="Șterge selecția",
        bg="#f28c8c",
        font=("Arial", 10, "bold"),
        command=lambda: sterge_selectie_istoric(tree)
    ).pack(pady=5)

    # ---------------- Buton inchidere pop-up istoric  ----------------
    tk.Button(
        popup,
        text="Închide",
        bg="#f28c8e",
        font=("Arial", 10, "bold"),
        command=popup.destroy
    ).pack(pady=8)


# Functie pentru stergerea istoricului
def sterge_selectie_istoric(tree):
    selected_items = tree.selection()
    if not selected_items:
        messagebox.showwarning("Atenție", "Nu ai selectat niciun rând!")
        return

    if not messagebox.askyesno("Confirmare", f"Sigur vrei să ștergi {len(selected_items)} rânduri?"):
        return

    try:
        conn = conectare_db()
        cursor = conn.cursor()

        for item in selected_items:
            values = tree.item(item, "values")
            print("Stergem:", values)
            client = values[0]
            serie_amef = values[1]
            tip_abonament = values[3]
            data_start = values[4]

            # ștergere după combinația unică
            cursor.execute("""
                DELETE FROM istoric_abonamente
                WHERE tip_abonament = ? AND serie_amef=? AND data_start=?              
            """, (tip_abonament, serie_amef, data_start))

            tree.delete(item)  # șterge și din Treeview
        conn.commit()
        messagebox.showinfo("Succes", f"{len(selected_items)} rânduri au fost șterse!")

    except Exception as e:
        messagebox.showerror("Eroare", f"A apărut o eroare la ștergere:\n{e}")
    finally:
        conn.close()


# =========================
# User Interface setup
# =========================
root = tk.Tk()
root.title("Gestionare Client și Sediu")
root.geometry("1400x700")

color_client = "#d0e1f9"
color_sediu = "#f9f1d0"

# -------------------------
# FRAME CLIENT (stânga)
# -------------------------
frame_client = tk.LabelFrame(root, text="Date Client", bg=color_client, padx=10, pady=10, font=("Arial", 12, "bold"))
frame_client.grid(row=0, column=0, sticky="nsew", padx=10, pady=5)

client_labels = ["CUI Client", "Nume firmă", "Adresă sediu", "Registrul Comertului",
                 "Plătitor TVA", "Administrator Firma", "Status Firma", "Numar Telefon", "Adresa mail"]
entries = {}

for i, label in enumerate(client_labels):
    tk.Label(frame_client, text=label, bg=color_client, font=("Arial", 10)).grid(row=i, column=0, sticky="w", padx=5,
                                                                                 pady=2)
    e = tk.Entry(frame_client, width=40)
    e.grid(row=i, column=1, sticky="w", padx=5, pady=2)
    entries[label] = e

(entry_cui, entry_nume, entry_adresa, entry_reg_comert,
 entry_tva, entry_administrator, entry_status_firma,
 entry_telefon, entry_mail) = [entries[label] for label in client_labels]

# -------------------------
# FRAME SEDIU/AMEF (dreapta)
# -------------------------
frame_sediu = tk.LabelFrame(root, text="Sediu Secundar / AMEF", bg=color_sediu, padx=10, pady=10,
                            font=("Arial", 12, "bold"))
frame_sediu.grid(row=0, column=1, sticky="nsew", padx=10, pady=5)

sediu_labels = ["Punct de lucru", "Model Amef", "Serie Amef", "Nui Amef",
                "Data conectare Anaf", "Tehnician Service", "Data expirare abonament",
                "Valoare contract - RON", "Tip Abonament", "Data expirare Gprs"]

for i, label in enumerate(sediu_labels):
    tk.Label(
        frame_sediu,
        text=label,
        bg=color_sediu,
        font=("Arial", 10)
    ).grid(row=i, column=0, sticky="w", padx=5, pady=2)

    if label in ("Data conectare Anaf", "Data expirare abonament", "Data expirare Gprs"):
        e = DateEntry(
            frame_sediu,
            width=37,
            date_pattern="yyyy-mm-dd"  # compatibil MySQL
        )
    else:
        e = tk.Entry(frame_sediu, width=40)

    e.grid(row=i, column=1, sticky="w", padx=5, pady=2)
    entries[label] = e

(entry_punct_lucru, entry_model_amef, entry_serie_amef, entry_nui,
 entry_conectare_anaf, entry_tehnician, entry_data_exp, entry_val_ctr,
 entry_tip_abonament, entry_data_exp_gprs) = [entries[label] for label in sediu_labels]

"""
Pentru populare automata in functie de tip client platitor tva sau nu 
cu deplasare sau anual
"""
entry_tip_abonament.bind("<KeyRelease>", actualizeaza_valoare_contract)
entry_tva.bind("<KeyRelease>", actualizeaza_valoare_contract)

# -------------------------
# FRAME BUTOANE
# -------------------------
frame_butoane = tk.Frame(root)
frame_butoane.grid(row=1, column=0, columnspan=3, pady=10)

btn_params = [
    ("Caută cu API", lambda: cauta_firma(), "#d4f0d0"),
    ("Salvează client", lambda: salveaza_client(), "#cfe2f3"),
    # ("Modifică date client", lambda: modifica_date_client(), "#cfe2f3"),
    # ("Modifica Tenhician", lambda: modifica_tehnician(), "#cfe2f3"),
    ("Prelungeste 1 AN", lambda: buton_prelungire(), "#cfe2f3"),
    ("Prelungeste 3 luni", lambda: buton_prelungire_3_luni(), "#cfe2f3"),
    ("Verifică TVA (ANAF)", lambda: webbrowser.open_new("https://www.anaf.ro/RegistruTVA/"), "#0000FF"),
    ("Afiseaza Abonam.", lambda: alerta_abonamente_combinate(), "#ffd966"),  # galben
    ("Istoric Abonament", lambda: popup_istoric_abonamente(), "#008080"),  # verde
    ("Resetare câmpuri", lambda: resetare_toate_campurile(), "#cfe2f3"),
    ("Merge DB (admin)", lambda: update_baza_protejat(), "#f4b183")  # Combinarea a 2 baze de date sqlite3

]
for i, (text, cmd, color) in enumerate(btn_params):
    tk.Button(frame_butoane, text=text, command=cmd, width=16, bg=color, font=("Arial", 10, "bold")).grid(row=i // 4,
                                                                                                          column=i % 4,
                                                                                                          pady=5,
                                                                                                          padx=10)

"""
Clasa care creaza hover cu mesajele deasupra butoanelor cand trecem cu mouseul peste ele
"""


class ToolTip:
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tip_window = None
        widget.bind("<Enter>", self.show_tip)
        widget.bind("<Leave>", self.hide_tip)

    def show_tip(self, event=None):
        if self.tip_window or not self.text:
            return
        x = self.widget.winfo_rootx() + 20
        y = self.widget.winfo_rooty() + self.widget.winfo_height() + 5
        self.tip_window = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)
        tw.wm_geometry(f"+{x}+{y}")
        label = tk.Label(tw, text=self.text, justify="left",
                         background="#ffffe0", relief="solid", borderwidth=1,
                         font=("Arial", 9))
        label.pack(ipadx=4, ipady=2)

    def hide_tip(self, event=None):
        if self.tip_window:
            self.tip_window.destroy()
            self.tip_window = None


# =========================
# Butoane + Tooltip
# =========================
btn_descriptions = [
    "Caută firma folosind API-ul ANAF",
    "Salvează clientul în baza de date locală",
    "Prelungește abonamentul curent cu 1 AN",
    "Prelungește abonamentul curent cu 3 luni",
    "Deschide site-ul ANAF pentru verificare TVA",
    "Afișează alerta cu expirarea abonamentelor",
    "Afișează istoricul abonamentelor Service si Gprs",
    "Resetează toate câmpurile din formular",
    "Combina si actualizeaza 2 baze de date"
]

# Creăm butoanele și atașăm tooltip
for i, (text, cmd, color) in enumerate(btn_params):
    btn = tk.Button(frame_butoane, text=text, command=cmd, width=16, bg=color, font=("Arial", 10, "bold"))
    btn.grid(row=i // 4, column=i % 4, pady=5)
    ToolTip(btn, btn_descriptions[i])

# -------------------------
# FRAME TREE + SEARCH (sub butoane)
# -------------------------
frame_tree = tk.Frame(root)
frame_tree.grid(row=3, column=0, columnspan=2, sticky="nsew", padx=10, pady=5)

# Mutăm câmpul de căutare aici și facem entry-ul mai mare
search_frame = tk.Frame(frame_tree)
search_frame.pack(fill="x", pady=5)

tk.Label(search_frame, text="Caută dupa Nume, Cui, Serie sau Nui:", font=("Arial", 10, "bold")).pack(side="left",
                                                                                                     padx=5)
search_entry = tk.Entry(search_frame, width=50)  # mai mare
search_entry.pack(side="left", padx=5)
tk.Button(search_frame, text="Caută", command=cauta_in_treeview, bg="#d4f0d0", width=12).pack(side="left", padx=5)
# tk.Button(search_frame, text="Resetează", command=incarca_dropdown_puncte, bg="#f0d0d0", width=12).pack(side="left", padx=5)

# Buton resetare camp cautare
tk.Button(search_frame, text="Resetează", command=resetare_camp_cautare, bg="#f0d0d0", width=12).pack(side="left",
                                                                                                      padx=5)

# =========================
# TREEVIEW REZULTATE (SUB CAUTARE)
# =========================

frame_tabel = tk.Frame(frame_tree)
frame_tabel.pack(fill="both", expand=True)

# search_frame.grid(row=3, column=0, columnspan=2, padx=10, pady=10, sticky="nsew")
scroll_y = tk.Scrollbar(frame_tabel, orient="vertical")
scroll_x = tk.Scrollbar(frame_tabel, orient="horizontal")

columns = (
    "Nr_Crt", "Nume Firma", "Cod Fiscal", "Sediu Social",
    "Nr Telefon", "Mail", "Reg Comert", "Tva", "Administrator", "Status Firma",
    "Punct Lucru", "Model AMEF", "Serie AMEF", "NUI",
    "Tehnician srv", "Data Conectare Anaf", "Data Exp. Abonament", "Val_Ctr", "Tip Abonament", "Data Exp. Gprs",

)
tree = ttk.Treeview(
    frame_tabel,
    columns=columns,
    show="headings",
    yscrollcommand=scroll_y.set,
    xscrollcommand=scroll_x.set
)
tree.tag_configure("expirat", background="#f28c8c")  # roșu
tree.tag_configure("avertizare", background="#fff3b0")  # galben
tree.tag_configure("valid", background="#d4f7d4")  # verde
tree.tag_configure("status_inactiv", background="#808080")  # gri pentru firme inactive

scroll_y.config(command=tree.yview)
scroll_x.config(command=tree.xview)

scroll_y.pack(side="right", fill="y")
scroll_x.pack(side="bottom", fill="x")
tree.pack(fill="both", expand=True)
tree.bind("<<TreeviewSelect>>",
          populare_campuri_treeview)  # cu linia asta activam functia de populare campuri cand selectam din cautare
tree.bind("<Double-1>", la_double_click)
search_entry.bind("<KeyRelease>", lambda e: cauta_in_treeview())  # cautare live in treeview

for col in columns:
    tree.heading(col, text=col)
    tree.column(col, width=130, anchor="w")

# Meniu
meniu = tk.Menu(root)
root.config(menu=meniu)

# Meniul de import export a bazei de date cu cele 3 tabele in format csv
import_export_menu = tk.Menu(meniu, tearoff=0)
export_menu = tk.Menu(meniu, tearoff=0)
meniu.add_cascade(label="Importa/Exporta DB", background="lightblue", menu=import_export_menu)
import_export_menu.add_command(label="Importa baza date", background="lightblue", command=import_csv)
import_export_menu.add_command(label="Exporta baza date", background="lightblue", command=export_csv)

# Meniul de stergere client sau punct lucru
sterge_menu = tk.Menu(meniu, tearoff=0)
meniu.add_cascade(label="Sterge Client/Punct Lucru", background="lightblue", menu=sterge_menu)
sterge_menu.add_command(label="Sterge Client", background="lightblue", foreground="red", command=sterge_client)
sterge_menu.add_command(label="Sterge Punct Lucru", background="lightblue", foreground="red", command=sterge_punct)

menu = tk.Menu(root, tearoff=0)
menu.add_command(label="Copiaza celula", command=lambda: copy_selection("cell", right_click_event))
menu.add_command(label="Copiaza tot randul", command=lambda: copy_selection("row", right_click_event))


def show_menu(event):
    global right_click_event
    right_click_event = event
    menu.tk_popup(event.x_root, event.y_root)


tree.bind("<Button-3>", show_menu)  # Button-3 = click dreapta pentru copiere

# CONFIGURARE GRID ROOT
root.grid_rowconfigure(3, weight=1)
root.grid_columnconfigure(0, weight=1)
root.grid_columnconfigure(1, weight=1)

# --- POP-UP ALERTĂ ABONAMENTE ---
# root.after(100, alerta_abonamente_color)  # rulează pop-up-ul automat după ce UI-ul principal e gata

footer = tk.Label(root, text="Designed by Pop Ciprian, © 2026 - Copywrite Edition",
                  font=("Arial", 8, "italic"), fg="gray")
footer.grid(row=4, column=0, columnspan=2, sticky="e", padx=10, pady=5)

root.mainloop()


