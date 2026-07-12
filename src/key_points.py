from google import genai

from config.config import GEMINI_API_KEY
from src.pdf_loader import load_document

client = genai.Client(api_key=GEMINI_API_KEY)


def generate_key_points(txt_path):
    """
    Generate key insights from the complete document.
    Uses a single Gemini request instead of one request per chunk.
    """

    document = load_document(txt_path)

    prompt = f"""
You are an expert document analyst.

Extract the most important points from the document.

Requirements

• Return 10–15 bullet points.

• Each bullet should contain one important fact.

• Preserve important names, dates, percentages, monetary values and statistics.

• Order the bullets by importance.

• Keep each bullet concise.

Rules

- Use ONLY the supplied document.

- Do NOT invent information.

- Do NOT use outside knowledge.

Document:

{document}
"""

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt
    )

    return response.text
