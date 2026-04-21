import os
from pathlib import Path
from tkinter import Tk, filedialog
from pypdf import PdfReader, PdfWriter


def get_downloads_folder() -> Path:
    return Path.home() / "Downloads"


def choose_pdfs():
    root = Tk()
    root.withdraw()
    root.attributes("-topmost", True)

    files = filedialog.askopenfilenames(
        title="Select PDF files",
        filetypes=[("PDF files", "*.pdf")]
    )
    return list(files)


def merge_pdfs(pdf_files, output_path):
    writer = PdfWriter()

    for pdf_file in pdf_files:
        reader = PdfReader(pdf_file)
        for page in reader.pages:
            writer.add_page(page)

    with open(output_path, "wb") as f:
        writer.write(f)


def split_pdfs(pdf_files, output_folder):
    for pdf_file in pdf_files:
        reader = PdfReader(pdf_file)
        base_name = Path(pdf_file).stem

        for i, page in enumerate(reader.pages, start=1):
            writer = PdfWriter()
            writer.add_page(page)

            output_file = output_folder / f"{base_name}_page_{i}.pdf"
            with open(output_file, "wb") as f:
                writer.write(f)


def main():
    print("PDF Merger / Divider")
    print("--------------------")

    pdf_files = choose_pdfs()

    if not pdf_files:
        print("No PDF files selected.")
        return

    print("\nSelected files:")
    for f in pdf_files:
        print(f" - {f}")

    print("\nWhat would you like to do?")
    print("1. attach   -> merge all selected PDFs into one")
    print("2. separate -> split each selected PDF into individual pages")

    choice = input("\nType attach or separate: ").strip().lower()

    downloads = get_downloads_folder()
    downloads.mkdir(parents=True, exist_ok=True)

    if choice == "attach":
        output_file = downloads / "merged_output.pdf"
        merge_pdfs(pdf_files, output_file)
        print(f"\nDone. Merged PDF saved to:\n{output_file}")

    elif choice == "separate":
        output_folder = downloads / "split_pdfs_output"
        output_folder.mkdir(parents=True, exist_ok=True)
        split_pdfs(pdf_files, output_folder)
        print(f"\nDone. Split PDFs saved to:\n{output_folder}")

    else:
        print("\nInvalid choice. Please run the program again and type attach or separate.")


if __name__ == "__main__":
    main()import os
from pathlib import Path
from tkinter import Tk, filedialog
from pypdf import PdfReader, PdfWriter


def get_downloads_folder() -> Path:
    return Path.home() / "Downloads"


def choose_pdfs():
    root = Tk()
    root.withdraw()
    root.attributes("-topmost", True)

    files = filedialog.askopenfilenames(
        title="Select PDF files",
        filetypes=[("PDF files", "*.pdf")]
    )
    return list(files)


def merge_pdfs(pdf_files, output_path):
    writer = PdfWriter()

    for pdf_file in pdf_files:
        reader = PdfReader(pdf_file)
        for page in reader.pages:
            writer.add_page(page)

    with open(output_path, "wb") as f:
        writer.write(f)


def split_pdfs(pdf_files, output_folder):
    for pdf_file in pdf_files:
        reader = PdfReader(pdf_file)
        base_name = Path(pdf_file).stem

        for i, page in enumerate(reader.pages, start=1):
            writer = PdfWriter()
            writer.add_page(page)

            output_file = output_folder / f"{base_name}_page_{i}.pdf"
            with open(output_file, "wb") as f:
                writer.write(f)


def main():
    print("PDF Merger / Divider")
    print("--------------------")

    pdf_files = choose_pdfs()

    if not pdf_files:
        print("No PDF files selected.")
        return

    print("\nSelected files:")
    for f in pdf_files:
        print(f" - {f}")

    print("\nWhat would you like to do?")
    print("1. attach   -> merge all selected PDFs into one")
    print("2. separate -> split each selected PDF into individual pages")

    choice = input("\nType attach or separate: ").strip().lower()

    downloads = get_downloads_folder()
    downloads.mkdir(parents=True, exist_ok=True)

    if choice == "attach":
        output_file = downloads / "merged_output.pdf"
        merge_pdfs(pdf_files, output_file)
        print(f"\nDone. Merged PDF saved to:\n{output_file}")

    elif choice == "separate":
        output_folder = downloads / "split_pdfs_output"
        output_folder.mkdir(parents=True, exist_ok=True)
        split_pdfs(pdf_files, output_folder)
        print(f"\nDone. Split PDFs saved to:\n{output_folder}")

    else:
        print("\nInvalid choice. Please run the program again and type attach or separate.")


if __name__ == "__main__":
    main()