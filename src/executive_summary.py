from config.config import PROCESSED_DIR
from src.pdf_loader import load_document
from google import genai
from config.config import GEMINI_API_KEY

client=genai.Client(api_key=GEMINI_API_KEY)

client = genai.Client(api_key=GEMINI_API_KEY)

def generate_executive_summary(txt_path):

    document = load_document(txt_path)

    prompt = f"""
You are an expert document analyst.

Write a professional executive summary based ONLY on the supplied document.

Requirements

• Explain the purpose of the document.

• Summarize the major topics.

• Highlight the most important findings.

• Mention important numbers, dates, organizations or decisions when relevant.

• State the overall conclusion.

Rules

- Use ONLY the supplied document.
- Do NOT invent information.
- Do NOT use outside knowledge.
- Write in professional business English.
- Keep the summary between 250 and 350 words.

Document:

{document}
"""

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt
    )

    return response.text
            



