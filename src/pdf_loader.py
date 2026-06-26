import pymupdf

def extract_text(pdf_path,txt_path):
    doc=pymupdf.open(pdf_path)

    with open(txt_path,"w",encoding="utf-8") as f:
        for page_num,page in enumerate(doc,start=0):
            f.write(f"== PAGE {page_num} ==\n\n")

            blocks=page.get_text("blocks")

            blocks.sort(key=lambda b: (b[1],b[0]))
            for block in blocks:
                text=block[4].strip()

                if text:
                    f.write(text+"\n\n")
            f.write("\n")

extract_text("C:/Users/hp/Desktop/Projects/financial-report-analyzer/data/reports/apple_2024.pdf","C:/Users/hp/Desktop/Projects/financial-report-analyzer/data/processed/apple_2024.txt")
    
