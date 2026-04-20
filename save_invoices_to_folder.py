#!/usr/bin/env python3
"""
For each pending invoice, find the email from the actual supplier
(not from us, not from the accountant), take the most recent one,
and save its attachments to ~/Documents/invoices/.
"""

import os
import datetime

os.chdir(os.path.dirname(os.path.abspath(__file__)))

import forward_pending_invoices as fpi

OUTPUT_DIR = os.path.expanduser("~/Documents/invoices")

# Emails we sent ourselves or from the accountant — skip these
OUR_ADDRESSES = {
    "damoncollective@gmail.com",
    "wigscoop@gmail.com",
    "info@damoncoop.eu",
    "plistakas@yahoo.gr",
}

# For suppliers whose AA number is only inside the PDF (not in email body),
# we fall back to searching by sender + invoice date window (±10 days).
SENDER_FALLBACK = {
    "ΑΝΤΩΝΙΟΥ":       "andreas.andoniou@gmail.com",
    "ΤΡΑΠΕΖΑ ΠΕΙΡΑΙΩΣ": "ibankv2email@piraeusbank.gr",
    "NOVA":           "nova",
}


def sender_is_ours(from_header):
    from_lower = from_header.lower()
    return any(addr in from_lower for addr in OUR_ADDRESSES)


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    excel_path = os.path.expanduser("~/Downloads/ΔΑΜΩΝ ΕΚΚΡΕΜΟΤΗΤΕΣ ΠΑΡΑΣΤΑΤΙΚΩΝ.xlsx")
    pending = fpi.load_pending_invoices(excel_path)
    print(f"Pending invoices: {len(pending)}")

    today = datetime.date.today()
    search_before = (today + datetime.timedelta(days=1)).strftime("%Y/%m/%d")

    saved_total = 0

    for inv in pending:
        aa     = inv["aa"]
        series = inv["series"]
        name   = inv["name"][:35]

        # Collect matches from both accounts
        matches = []
        for account in fpi.ACCOUNTS:
            try:
                service = fpi.get_service(account)
                found = fpi.search_for_invoice(service, account["email"], inv, search_before)
                matches.extend(found)
            except Exception as e:
                print(f"  ⚠ {account['email']}: {e}")

        # Show ALL matches before filtering (for debugging)
        if matches:
            print(f"  [{series} {aa}] {len(matches)} total match(es):")
            for m in matches:
                print(f"     from: {m.get('from','')}  |  subj: {m.get('subject','')[:60]}")

        # Keep only emails from external suppliers (not from us, not the accountant)
        external = [m for m in matches if not sender_is_ours(m.get("from", ""))]

        if not external:
            # Fallback: search by known sender + date window if AA not in email body
            fallback_sender = next(
                (addr for key, addr in SENDER_FALLBACK.items() if key in inv["name"]),
                None
            )
            if fallback_sender:
                # Parse invoice date (DD/MM/YYYY) and search ±10 days around it
                try:
                    inv_date = datetime.datetime.strptime(inv["date"], "%d/%m/%Y").date()
                    date_from = (inv_date - datetime.timedelta(days=10)).strftime("%Y/%m/%d")
                    date_to   = (inv_date + datetime.timedelta(days=10)).strftime("%Y/%m/%d")
                    fb_query  = f"from:{fallback_sender} after:{date_from} before:{date_to}"
                    print(f"  ↺  fallback search: {fb_query}")
                    for account in fpi.ACCOUNTS:
                        try:
                            service  = fpi.get_service(account)
                            results  = service.users().messages().list(
                                userId="me", q=fb_query, maxResults=5
                            ).execute()
                            for m in results.get("messages", []):
                                msg = service.users().messages().get(
                                    userId="me", id=m["id"], format="full"
                                ).execute()
                                headers      = msg["payload"].get("headers", [])
                                orig_from    = fpi.extract_header(headers, "from")
                                orig_subject = fpi.extract_header(headers, "subject")
                                atts, body   = fpi.get_attachments_and_body(service, msg)
                                external.append({
                                    "from":          orig_from,
                                    "subject":       orig_subject,
                                    "attachments":   atts,
                                    "body":          body,
                                    "internal_date": int(msg.get("internalDate", 0)),
                                })
                        except Exception as e:
                            print(f"    ⚠ fallback {account['email']}: {e}")
                except ValueError:
                    pass

            if not external:
                print(f"  ✗  {series} {aa} ({name}) — not found")
                continue

        # Prefer emails WITH attachments; among those take the most recent
        with_atts    = [m for m in external if m.get("attachments")]
        without_atts = [m for m in external if not m.get("attachments")]
        pool = with_atts if with_atts else without_atts
        pool.sort(key=lambda m: m.get("internal_date", 0), reverse=True)
        latest = pool[0]

        print(f"  → {series} {aa} | from: {latest['from']} | {len(latest['attachments'])} attachment(s)")

        # Save attachments
        saved = 0
        for filename, data in latest["attachments"]:
            safe_name = f"{aa}_{filename}"
            dest = os.path.join(OUTPUT_DIR, safe_name)
            base, ext = os.path.splitext(dest)
            counter = 1
            while os.path.exists(dest):
                dest = f"{base}_{counter}{ext}"
                counter += 1
            with open(dest, "wb") as f:
                f.write(data)
            print(f"     ✓  {os.path.basename(dest)}")
            saved += 1
            saved_total += 1

        if saved == 0:
            print(f"     (no attachments in that email — body-only)")

    print(f"\n{saved_total} file(s) saved to {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
