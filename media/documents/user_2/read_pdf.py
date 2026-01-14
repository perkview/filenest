# First, install PyPDF2 if you haven't already:
# pip install PyPDF2

import PyPDF2

# Path to your PDF file
pdf_file_path = "sample.pdf"

# Open the PDF file in read-binary mode
with open(pdf_file_path, "rb") as file:
    # Create a PDF reader object
    reader = PyPDF2.PdfReader(file)
    
    # Loop through all pages and extract text
    for page_num, page in enumerate(reader.pages, start=1):
        text = page.extract_text()
        print(f"--- Page {page_num} ---")
        print(text)
        print("\n")
