import pdfplumber

with pdfplumber.open("test.pdf") as pdf:
    with open("output.txt", "a", encoding="utf-8") as f:
        for page in pdf.pages:
            text = page.extract_text()
            if text:  # avoid writing None
                f.write(text + "\n")
