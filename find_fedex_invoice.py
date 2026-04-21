"""
Search FedEx PDF invoices for a specific AWB number.
Drop your FedEx invoice PDFs in a folder and run this script.
"""

import os
import sys
import pdfplumber

AWB = "870043907857"

# Default search folders — edit or pass a folder as argument
DEFAULT_FOLDERS = [
    os.path.join(os.path.expanduser("~"), "Downloads"),
    os.path.join(os.path.expanduser("~"), "Desktop"),
    r"C:\Users\Damon\Desktop\prestashop",
]


def search_pdf(path, awb):
    """Return list of (page_num, context_lines) if awb found."""
    hits = []
    try:
        with pdfplumber.open(path) as pdf:
            for i, page in enumerate(pdf.pages, 1):
                text = page.extract_text() or ""
                if awb in text:
                    # Grab the surrounding lines for context
                    lines = text.splitlines()
                    context = [
                        line.strip()
                        for j, line in enumerate(lines)
                        if awb in line or (
                            any(awb in lines[k] for k in range(max(0, j-1), min(len(lines), j+2)))
                            and line.strip()
                        )
                    ]
                    hits.append((i, context))
    except Exception as e:
        print(f"  [!] Could not read {os.path.basename(path)}: {e}")
    return hits


def search_folder(folder, awb):
    if not os.path.isdir(folder):
        return
    pdfs = [f for f in os.listdir(folder) if f.lower().endswith(".pdf")]
    if not pdfs:
        return
    print(f"\nSearching {len(pdfs)} PDF(s) in: {folder}")
    for fname in pdfs:
        fpath = os.path.join(folder, fname)
        hits = search_pdf(fpath, awb)
        if hits:
            print(f"\n  ✔ FOUND in: {fname}")
            for page_num, lines in hits:
                print(f"    Page {page_num}:")
                for line in lines:
                    if line:
                        print(f"      {line}")


def main():
    awb = AWB
    folders = sys.argv[1:] if len(sys.argv) > 1 else DEFAULT_FOLDERS

    print(f"Looking for AWB: {awb}")
    print("=" * 60)

    found_any = False
    for folder in folders:
        search_folder(folder, awb)

    print("\n" + "=" * 60)
    print("Done. If not found, make sure the FedEx invoice PDFs are")
    print("saved in one of the folders above, then re-run.")


if __name__ == "__main__":
    main()
