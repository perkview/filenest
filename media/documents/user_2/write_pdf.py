# First, install reportlab if you haven't already:
# pip install reportlab

from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

# Path to save the PDF
pdf_file_path = "my_sample.pdf"

# Sample data to store in the PDF
data = """Hello! This is a sample PDF file created with Python.
You can store multiple lines of text here.
Each line will appear on a new line in the PDF.
Python makes generating PDFs easy and efficient."""

# Create a PDF canvas
c = canvas.Canvas(pdf_file_path, pagesize=letter)

# Set starting coordinates
x, y = 50, 750

# Write each line of data to the PDF
for line in data.split("\n"):
    c.drawString(x, y, line)
    y -= 20  # Move down for the next line

# Save the PDF
c.save()

print(f"PDF created successfully at '{pdf_file_path}'")
