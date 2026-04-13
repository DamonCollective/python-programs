#!/usr/bin/env python3
"""
Forward last month's foreign supplier invoices to accountant.
Searches both damoncollective@gmail.com and wigscoop@gmail.com.
Sends the bundled result from damoncollective@gmail.com.
"""

import os
import base64
import calendar
import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
from email import encoders

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# ── CONFIG ──────────────────────────────────────────────────────────────────

# Accounts to SEARCH. Each needs its own credentials file (from Google Cloud).
# Token files are created automatically on first login.
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

# The account that SENDS the final email (index into ACCOUNTS above)
SENDING_ACCOUNT_INDEX = 0

# From field — works only if info@damoncoop.eu is a "Send As" alias in
# damoncollective@gmail.com (Gmail Settings → Accounts → Send mail as).
# Otherwise Gmail sends from damoncollective@gmail.com regardless.
SENDER  = "info@damoncoop.eu"
CC      = "info@damoncoop.eu"
SUBJECT = "Τιμολογια εξωτερικου"
SCOPES  = ["https://www.googleapis.com/auth/gmail.modify"]

# Invoice detection keywords
INVOICE_KEYWORDS = [
    "invoice", "factura", "fattura", "bill", "receipt",
    "payment due", "pro forma", "proforma", "statement of account",
]

# Exclude emails from your own domains
EXCLUDE_SENDERS = [
    "alegro.gr", "damoncoop.eu", "claireswigs.com",
    "damoncollective@gmail.com", "wigscoop@gmail.com",
    "paypal.com",
]

# Subjects containing these words indicate outgoing payments or non-invoices — skip
EXCLUDE_SUBJECT_KEYWORDS = [
    "saldo", "bonifico", "your invoice to", "paid for your invoice",
    "we sent your invoice", "reminder from",
]

# Only keep emails that have at least one real file attachment (PDF, doc, etc.)
REQUIRE_ATTACHMENT = True

# Attachment MIME types to skip (promo images, etc.)
EXCLUDE_ATTACHMENT_MIMES = {"image/jpeg", "image/png", "image/gif", "image/webp", "image/bmp", "image/tiff"}
# Attachment extensions to skip
EXCLUDE_ATTACHMENT_EXTS  = {".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp", ".tiff", ".tif"}

# Senders exempt from the attachment requirement (body will be included as text)
ATTACHMENT_EXEMPT_SENDERS = [
    "payments-noreply@google.com",
]
# ────────────────────────────────────────────────────────────────────────────


def get_service(account: dict):
    """Authenticate and return Gmail API service for a given account."""
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


def _first_of_month_plus(d, n):
    """Return the 1st day of the month that is n months after d."""
    m = d.month - 1 + n
    return datetime.date(d.year + m // 12, m % 12 + 1, 1)


def _add_months(d, n):
    """Add n months to date d (same day clamped to month end if needed)."""
    m = d.month - 1 + n
    year  = d.year + m // 12
    month = m % 12 + 1
    day   = min(d.day, calendar.monthrange(year, month)[1])
    return datetime.date(year, month, day)


def ask_month_range():
    today = datetime.date.today()
    print(f"\nΓια ποιον μήνα θέλετε τιμολόγια;")
    print(f"  Πατήστε Enter για τον προηγούμενο μήνα, ή πληκτρολογήστε MM/YYYY (π.χ. 02/2026):")
    val = input("  Μήνας: ").strip()
    if not val:
        first_this_month = today.replace(day=1)
        last_month_end   = first_this_month - datetime.timedelta(days=1)
        month_start      = last_month_end.replace(day=1)
    else:
        try:
            parts       = val.split("/")
            month_start = datetime.date(int(parts[1]), int(parts[0]), 1)
        except (ValueError, IndexError):
            print("Μη έγκυρη μορφή. Χρησιμοποιώ τον προηγούμενο μήνα.")
            first_this_month = today.replace(day=1)
            last_month_end   = first_this_month - datetime.timedelta(days=1)
            month_start      = last_month_end.replace(day=1)

    # Last day of the asked month
    end_of_asked_month = _first_of_month_plus(month_start, 1) - datetime.timedelta(days=1)

    # If today is within 2 months of the end of the asked month, search up to today.
    # Otherwise cap at the end of the month following the asked month.
    if today <= _add_months(end_of_asked_month, 2):
        search_before = today + datetime.timedelta(days=1)   # inclusive of today
    else:
        search_before = _first_of_month_plus(month_start, 2) # exclusive = end of month+1

    return (
        month_start.strftime("%Y/%m/%d"),
        search_before.strftime("%Y/%m/%d"),
    )


def build_query(after, before):
    keyword_part = " OR ".join(f'"{kw}"' for kw in INVOICE_KEYWORDS)
    exclude_part = " ".join(f"-from:{d}" for d in EXCLUDE_SENDERS)
    return f"after:{after} before:{before} ({keyword_part}) {exclude_part}"


def extract_header(headers, name):
    for h in headers:
        if h["name"].lower() == name.lower():
            return h["value"]
    return ""


def decode_part(part):
    data = part["body"].get("data", "")
    return base64.urlsafe_b64decode(data) if data else b""


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
                if mime in EXCLUDE_ATTACHMENT_MIMES or ext in EXCLUDE_ATTACHMENT_EXTS:
                    pass  # skip promo images
                else:
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


def has_real_attachment(msg):
    """Return True if the message has at least one document attachment (not an image)."""
    payload = msg.get("payload", {})
    def walk(parts):
        for part in parts:
            filename = part.get("filename", "")
            mime     = part.get("mimeType", "")
            if filename and not mime.startswith("text/"):
                ext = os.path.splitext(filename.lower())[1]
                if mime not in EXCLUDE_ATTACHMENT_MIMES and ext not in EXCLUDE_ATTACHMENT_EXTS:
                    return True
            if "parts" in part and walk(part["parts"]):
                return True
        return False
    return walk(payload.get("parts", []))


def is_invoice_email(msg):
    headers  = msg["payload"].get("headers", [])
    subject  = extract_header(headers, "subject").lower()
    snippet  = msg.get("snippet", "").lower()
    combined = subject + " " + snippet

    if any(kw in subject for kw in EXCLUDE_SUBJECT_KEYWORDS):
        return False
    if REQUIRE_ATTACHMENT and not has_real_attachment(msg):
        sender = extract_header(headers, "from").lower()
        if not any(ex in sender for ex in ATTACHMENT_EXEMPT_SENDERS):
            return False
    return any(kw in combined for kw in INVOICE_KEYWORDS)


def search_account(account: dict, query: str):
    """Return list of invoice dicts found in this account."""
    print(f"\n  📬 {account['email']}")
    service = get_service(account)

    results  = service.users().messages().list(
        userId="me", q=query, maxResults=100
    ).execute()
    messages = results.get("messages", [])
    print(f"     {len(messages)} μηνύματα βρέθηκαν — φιλτράρισμα...", flush=True)

    invoices = []
    for m in messages:
        msg = service.users().messages().get(
            userId="me", id=m["id"], format="full"
        ).execute()
        if not is_invoice_email(msg):
            continue
        headers      = msg["payload"].get("headers", [])
        orig_from    = extract_header(headers, "from")
        orig_subject = extract_header(headers, "subject")
        attachments, body_text = get_attachments_and_body(service, msg)
        invoices.append({
            "account":     account["email"],
            "from":        orig_from,
            "subject":     orig_subject,
            "attachments": attachments,
            "body":        body_text,
        })

    print(f"     ✓ {len(invoices)} τιμολόγια αναγνωρίστηκαν")
    return invoices


def main():
    print("=" * 55)
    print("  Αυτόματη αποστολή τιμολογίων εξωτερικού")
    print("=" * 55)

    to_email = input("\nΑποστολή προς (email): ").strip()
    if not to_email:
        print("Δεν δόθηκε email. Έξοδος.")
        return

    after, before = ask_month_range()
    query         = build_query(after, before)
    print(f"\nΑναζήτηση ({after} → {before})...")

    all_invoices = []
    for account in ACCOUNTS:
        try:
            found = search_account(account, query)
            all_invoices.extend(found)
        except FileNotFoundError as e:
            print(f"\n⚠️  {e}\n   Παράλειψη αυτού του λογαριασμού.\n")

    if not all_invoices:
        print("\nΚανένα τιμολόγιο δεν βρέθηκε.")
        return

    # Build the outgoing email
    outer_msg = MIMEMultipart()
    outer_msg["From"]    = SENDER
    outer_msg["To"]      = to_email
    outer_msg["Cc"]      = CC
    outer_msg["Subject"] = SUBJECT

    summary_lines = [
        f"Τιμολόγια εξωτερικού — {after} έως {before}",
        "",
    ]

    attachment_count = 0
    for i, inv in enumerate(all_invoices, 1):
        summary_lines.append(f"{i}. Από: {inv['from']}")
        summary_lines.append(f"   Θέμα: {inv['subject']}")
        summary_lines.append(f"   Γραμματοκιβώτιο: {inv['account']}")

        if inv["attachments"]:
            names = []
            for filename, data in inv["attachments"]:
                part = MIMEBase("application", "octet-stream")
                part.set_payload(data)
                encoders.encode_base64(part)
                safe_name = f"{i:02d}_{filename}"
                part.add_header("Content-Disposition", "attachment", filename=safe_name)
                outer_msg.attach(part)
                names.append(safe_name)
                attachment_count += 1
            summary_lines.append(f"   Αρχεία: {', '.join(names)}")
        else:
            # No attachment — embed body as text file
            text_part = MIMEBase("text", "plain")
            content   = f"From: {inv['from']}\nSubject: {inv['subject']}\n\n{inv['body']}"
            text_part.set_payload(content.encode("utf-8"))
            encoders.encode_base64(text_part)
            safe_name = f"{i:02d}_invoice_body.txt"
            text_part.add_header("Content-Disposition", "attachment", filename=safe_name)
            outer_msg.attach(text_part)
            attachment_count += 1
            summary_lines.append("   (χωρίς συνημμένο — επισυνάπτεται το κείμενο)")

        summary_lines.append("")

    outer_msg.attach(MIMEText("\n".join(summary_lines), "plain", "utf-8"))

    print(f"\n{'─'*55}")
    print(f"  {len(all_invoices)} τιμολόγια | {attachment_count} αρχεία")
    print(f"  Προς:  {to_email}")
    print(f"  CC:    {CC}")
    print(f"  Θέμα:  {SUBJECT}")
    print(f"{'─'*55}")

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
