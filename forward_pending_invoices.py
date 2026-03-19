#!/usr/bin/env python3
"""
Forward invoices listed in ΔΑΜΩΝ ΕΚΚΡΕΜΟΤΗΤΕΣ ΠΑΡΑΣΤΑΤΙΚΩΝ.xlsx.
Searches both Gmail accounts from 1/1/2026 till today.
For each pending invoice, tries to locate the matching email by invoice number (AA).
"""

import os
import base64
import calendar
import datetime
import openpyxl
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
from email import encoders

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# ── CONFIG ──────────────────────────────────────────────────────────────────

ACCOUNTS = [
    {
        "email":      "damoncollective@gmail.com",
        "creds_file": "credentials_damoncollective.json",
        "token_file": "token_damoncollective.json",
    },
    {
        "email":      "wigscoop@gmail.com",
        "creds_file": "credentials_damoncollective.json",
        "token_file": "token_wigscoop.json",
    },
]

SENDING_ACCOUNT_INDEX = 0

SENDER  = "info@damoncoop.eu"
CC      = "info@damoncoop.eu"
SUBJECT = "Εκκρεμότητες Παραστατικών"
SCOPES  = ["https://www.googleapis.com/auth/gmail.modify"]

EXCEL_FILE  = "ΔΑΜΩΝ ΕΚΚΡΕΜΟΤΗΤΕΣ ΠΑΡΑΣΤΑΤΙΚΩΝ.xlsx"
SEARCH_FROM = "2026/01/01"   # fixed start date
# SEARCH_TO = today (computed at runtime)

# ────────────────────────────────────────────────────────────────────────────


def get_service(account: dict):
    creds = None
    token_file = account["token_file"]
    creds_file = account["creds_file"]

    if os.path.exists(token_file):
        creds = Credentials.from_authorized_user_file(token_file, SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not os.path.exists(creds_file):
                raise FileNotFoundError(
                    f"Credentials file not found: {creds_file}\n"
                    f"Download it from Google Cloud Console for {account['email']}"
                )
            flow = InstalledAppFlow.from_client_secrets_file(creds_file, SCOPES)
            creds = flow.run_local_server(port=0)
        with open(token_file, "w") as f:
            f.write(creds.to_json())

    return build("gmail", "v1", credentials=creds)


def extract_header(headers, name):
    for h in headers:
        if h["name"].lower() == name.lower():
            return h["value"]
    return ""


def decode_part(part):
    data = part["body"].get("data", "")
    return base64.urlsafe_b64decode(data) if data else b""


EXCLUDE_ATTACHMENT_MIMES = {"image/jpeg", "image/png", "image/gif", "image/webp", "image/bmp", "image/tiff"}
EXCLUDE_ATTACHMENT_EXTS  = {".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp", ".tiff", ".tif"}


def get_attachments_and_body(service, msg):
    attachments = []
    body_text   = ""
    payload     = msg.get("payload", {})

    def walk(parts):
        nonlocal body_text
        for part in parts:
            mime     = part.get("mimeType", "")
            filename = part.get("filename", "")
            if filename:
                ext = os.path.splitext(filename.lower())[1]
                if mime not in EXCLUDE_ATTACHMENT_MIMES and ext not in EXCLUDE_ATTACHMENT_EXTS:
                    att_id = part["body"].get("attachmentId")
                    if att_id:
                        att  = service.users().messages().attachments().get(
                            userId="me", messageId=msg["id"], id=att_id
                        ).execute()
                        data = base64.urlsafe_b64decode(att["data"])
                    else:
                        data = decode_part(part)
                    attachments.append((filename, data))
            elif mime == "text/plain" and not body_text:
                body_text = decode_part(part).decode("utf-8", errors="ignore")
            if "parts" in part:
                walk(part["parts"])

    if "parts" in payload:
        walk(payload["parts"])
    elif payload.get("mimeType") == "text/plain":
        body_text = decode_part(payload).decode("utf-8", errors="ignore")

    return attachments, body_text


def load_pending_invoices(excel_path: str) -> list[dict]:
    """Read the Excel and return list of pending invoice dicts."""
    wb = openpyxl.load_workbook(excel_path)
    ws = wb.active
    invoices = []
    headers = None
    for row in ws.iter_rows(values_only=True):
        if headers is None:
            headers = row  # first row = headers
            continue
        cancelled, afm, name, date, branch, series, aa, value = row[:8]
        if cancelled:          # skip cancelled rows
            continue
        if not aa:             # must have invoice number
            continue
        invoices.append({
            "afm":    str(afm).strip() if afm else "",
            "name":   str(name).strip() if name else "",
            "date":   str(date).strip() if date else "",
            "series": str(series).strip() if series else "",
            "aa":     str(aa).strip() if aa else "",
            "value":  value,
        })
    return invoices


def search_for_invoice(service, account_email: str, inv: dict, search_before: str) -> list[dict]:
    """Search for a single invoice by its AA number across the date range."""
    aa = inv["aa"]
    query = f'after:{SEARCH_FROM} before:{search_before} "{aa}"'
    results  = service.users().messages().list(
        userId="me", q=query, maxResults=20
    ).execute()
    messages = results.get("messages", [])

    found = []
    for m in messages:
        msg = service.users().messages().get(
            userId="me", id=m["id"], format="full"
        ).execute()
        headers      = msg["payload"].get("headers", [])
        orig_from    = extract_header(headers, "from")
        orig_subject = extract_header(headers, "subject")
        attachments, body_text = get_attachments_and_body(service, msg)
        found.append({
            "account":     account_email,
            "from":        orig_from,
            "subject":     orig_subject,
            "attachments": attachments,
            "body":        body_text,
            "invoice":     inv,
        })
    return found


def main():
    print("=" * 60)
    print("  Εκκρεμότητες Παραστατικών — Αναζήτηση & Αποστολή")
    print("=" * 60)

    # Locate the Excel file
    excel_path = EXCEL_FILE
    if not os.path.exists(excel_path):
        # Try Downloads folder
        home = os.path.expanduser("~")
        excel_path = os.path.join(home, "Downloads", EXCEL_FILE)
    if not os.path.exists(excel_path):
        excel_path = input(f"\nΔεν βρέθηκε το αρχείο '{EXCEL_FILE}'.\nΔώστε πλήρη διαδρομή: ").strip()
    if not os.path.exists(excel_path):
        print("Αρχείο δεν βρέθηκε. Έξοδος.")
        return

    pending = load_pending_invoices(excel_path)
    print(f"\nΒρέθηκαν {len(pending)} εκκρεμή παραστατικά στο Excel.")
    for p in pending:
        print(f"  • {p['date']}  {p['name'][:40]:<40}  {p['series']} {p['aa']}  {p['value']}€")

    to_email = input("\nΑποστολή προς (email): ").strip()
    if not to_email:
        print("Δεν δόθηκε email. Έξοδος.")
        return

    today        = datetime.date.today()
    search_before = (today + datetime.timedelta(days=1)).strftime("%Y/%m/%d")
    print(f"\nΑναζήτηση από {SEARCH_FROM} έως {today.strftime('%Y/%m/%d')}...")

    # For each pending invoice, search both accounts
    results = []   # list of (inv, [email_matches])
    for inv in pending:
        matches = []
        for account in ACCOUNTS:
            try:
                service = get_service(account)
                found = search_for_invoice(service, account["email"], inv, search_before)
                matches.extend(found)
            except FileNotFoundError as e:
                print(f"\n⚠️  {e}\n   Παράλειψη αυτού του λογαριασμού.\n")

        label = "✓" if matches else "✗"
        print(f"  {label}  {inv['series']} {inv['aa']} ({inv['name'][:35]}) → {len(matches)} email(s)")
        results.append((inv, matches))

    found_total   = sum(1 for _, m in results if m)
    missing_total = sum(1 for _, m in results if not m)

    print(f"\n{'─'*60}")
    print(f"  Βρέθηκαν: {found_total} | Δεν βρέθηκαν: {missing_total}")
    print(f"{'─'*60}")

    if found_total == 0:
        print("\nΚανένα παραστατικό δεν βρέθηκε στα email.")
        return

    # Build the outgoing email
    outer_msg = MIMEMultipart()
    outer_msg["From"]    = SENDER
    outer_msg["To"]      = to_email
    outer_msg["Cc"]      = CC
    outer_msg["Subject"] = SUBJECT

    summary_lines = [
        f"Εκκρεμότητες Παραστατικών — αναζήτηση από {SEARCH_FROM} έως {today.strftime('%d/%m/%Y')}",
        f"Σύνολο εκκρεμών: {len(pending)} | Βρέθηκαν: {found_total} | Δεν βρέθηκαν: {missing_total}",
        "",
    ]

    if missing_total:
        summary_lines.append("ΔΕΝ ΒΡΕΘΗΚΑΝ:")
        for inv, matches in results:
            if not matches:
                summary_lines.append(f"  • {inv['date']}  {inv['name']}  {inv['series']} {inv['aa']}  {inv['value']}€")
        summary_lines.append("")

    summary_lines.append("ΒΡΕΘΗΚΑΝ:")
    attachment_count = 0
    entry_num = 0

    for inv, matches in results:
        if not matches:
            continue
        entry_num += 1
        summary_lines.append(
            f"\n{entry_num}. {inv['date']}  {inv['name']}  {inv['series']} {inv['aa']}  {inv['value']}€"
        )
        for email_match in matches:
            summary_lines.append(f"   Email από: {email_match['from']}")
            summary_lines.append(f"   Θέμα: {email_match['subject']}")
            summary_lines.append(f"   Γραμματοκιβώτιο: {email_match['account']}")

            if email_match["attachments"]:
                names = []
                for filename, data in email_match["attachments"]:
                    part = MIMEBase("application", "octet-stream")
                    part.set_payload(data)
                    encoders.encode_base64(part)
                    safe_name = f"{entry_num:02d}_{inv['aa']}_{filename}"
                    part.add_header("Content-Disposition", "attachment", filename=safe_name)
                    outer_msg.attach(part)
                    names.append(safe_name)
                    attachment_count += 1
                summary_lines.append(f"   Αρχεία: {', '.join(names)}")
            else:
                text_part = MIMEBase("text", "plain")
                content   = f"From: {email_match['from']}\nSubject: {email_match['subject']}\n\n{email_match['body']}"
                text_part.set_payload(content.encode("utf-8"))
                encoders.encode_base64(text_part)
                safe_name = f"{entry_num:02d}_{inv['aa']}_body.txt"
                text_part.add_header("Content-Disposition", "attachment", filename=safe_name)
                outer_msg.attach(text_part)
                attachment_count += 1
                summary_lines.append("   (χωρίς συνημμένο — επισυνάπτεται το κείμενο)")

    outer_msg.attach(MIMEText("\n".join(summary_lines), "plain", "utf-8"))

    print(f"\n  {found_total} παραστατικά | {attachment_count} αρχεία")
    print(f"  Προς:  {to_email}")
    print(f"  CC:    {CC}")
    print(f"  Θέμα:  {SUBJECT}")

    confirm = input("\nΑποστολή; (yes/no): ").strip().lower()
    if confirm not in ("yes", "y", "ναι", "ν"):
        print("Ακυρώθηκε.")
        return

    sending_service = get_service(ACCOUNTS[SENDING_ACCOUNT_INDEX])
    raw = base64.urlsafe_b64encode(outer_msg.as_bytes()).decode("utf-8")
    sending_service.users().messages().send(
        userId="me", body={"raw": raw}
    ).execute()

    print("\n✅ Εστάλη επιτυχώς!")


if __name__ == "__main__":
    main()
