from config.config import PROCESSED_DIR
from src.vector_store import load_all_chunks
from google import genai
from config.config import GEMINI_API_KEY

client=genai.Client(api_key=GEMINI_API_KEY)

def generate_key_points(chunk_json_path):
    chunks=load_all_chunks(chunk_json_path)
    batch_key_points = []
    for a in range(0,len(chunks),20):
        chunk_20_summary=[]
        for b in range (a,min(a + 20, len(chunks)),1):
            chunk_20_summary.append(chunks[b]['text'])
        prompt=f"""You are an expert document analyst.

                    Extract the most important points from the provided document excerpts.

                    Requirements:
                    - Return between 10 and 15 bullet points.
                    - Each bullet should contain one important fact.
                    - Preserve important names, dates, monetary values, percentages and statistics.
                    - Keep each bullet under two sentences.
                    - Do not repeat information.
                    - Order the bullets by importance.

                    Rules:
                    - Use ONLY the supplied document.
                    - Do NOT infer missing information.
                    - Do NOT add explanations beyond what is stated.
                    - Avoid repeating information across sections.

                    Document excerpts :{"\n\n-----------------------------\n\n".join(chunk_20_summary)}"""
        response=client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt
        )
        batch_key_points.append(response.text)
        

    final_prompt=f"""You are an expert document analyst.

                    Extract the most important points from the provided document excerpts.

                    Requirements:
                    - Return between 10 and 15 bullet points.
                    - Each bullet should contain one important fact.
                    - Preserve important names, dates, monetary values, percentages and statistics.
                    - Keep each bullet under two sentences.
                    - Do not repeat information.
                    - Order the bullets by importance.

                    Rules:
                    - Use ONLY the supplied document.
                    - Do NOT infer missing information.
                    - Do NOT add explanations beyond what is stated.
                    - Avoid repeating information across sections.

                    Document excerpts :{"\n\n-----------------------------------------\n\n".join(batch_key_points)}"""
    final_response=client.models.generate_content(
        model="gemini-2.5-flash",
        contents=final_prompt
    )
    return final_response.text
            



