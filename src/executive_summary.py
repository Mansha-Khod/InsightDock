from config.config import PROCESSED_DIR
from src.vector_store import load_all_chunks
from google import genai
from config.config import GEMINI_API_KEY

client=genai.Client(api_key=GEMINI_API_KEY)

def generate_executive_summary(chunk_json_path):
    chunks=load_all_chunks(chunk_json_path)
    final_summary=[]
    for a in range(0,len(chunks),20):
        chunk_20_summary=[]
        for b in range (a,min(a + 20, len(chunks)),1):
            chunk_20_summary.append(chunks[b]['text'])
        prompt=f"""You are an expert document analyst.

                    Write a professional executive summary based ONLY on the provided document excerpts.

                    Requirements:
                    - Explain the overall purpose of the document.
                    - Summarize the major topics discussed.
                    - Highlight the most important findings.
                    - Mention important numbers, dates, organizations, or decisions when relevant.
                    - State the overall conclusion or significance.

                    Rules:
                    - Do NOT invent information.
                    - Do NOT use outside knowledge.
                    - If something is not present, do not mention it.
                    - Write in professional business English.
                    - Keep the summary between 200 and 300 words.
                    - Avoid repeating information across sections.

                    Document excerpts :{"\n\n-----------------------------\n\n".join(chunk_20_summary)}"""
        response=client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt
        )
        final_summary.append(response.text)
        

    final_prompt=f"""You are an expert document analyst.

                    Write a professional executive summary based ONLY on the provided document excerpts.

                    Requirements:
                    - Explain the overall purpose of the document.
                    - Summarize the major topics discussed.
                    - Highlight the most important findings.
                    - Mention important numbers, dates, organizations, or decisions when relevant.
                    - State the overall conclusion or significance.

                    Rules:
                    - Do NOT invent information.
                    - Do NOT use outside knowledge.
                    - If something is not present, do not mention it.
                    - Write in professional business English.
                    - Keep the summary between 200 and 300 words.
                    - Avoid repeating information across sections.

                    Document excerpts:{"\n\n-----------------------------------------\n\n".join(final_summary)}"""
    final_response=client.models.generate_content(
        model="gemini-2.5-flash",
        contents=final_prompt
    )
    return final_response.text
            



