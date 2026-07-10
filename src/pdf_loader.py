import pymupdf
from config.config import REPORTS_DIR
from config.config import PROCESSED_DIR

def extract_text(pdf_path,txt_path):
    doc=pymupdf.open(pdf_path)

    with open(txt_path,"w",encoding="utf-8") as f:
        for page_num,page in enumerate(doc,start=1):
            f.write(f"== PAGE {page_num} ==\n\n")

            blocks=page.get_text("blocks")

            blocks.sort(key=lambda b: (b[1],b[0]))
            for block in blocks:
                text=block[4].strip()

                if text:
                    f.write(text+"\n\n")
            f.write("\n")
    doc.close()
    return txt_path

def load_document(txt_path):
    with open(
        PROCESSED_DIR / txt_path,
        "r",
        encoding="utf-8"
    ) as f:
        return f.read()

    
