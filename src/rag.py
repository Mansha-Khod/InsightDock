from google import genai
from src.vector_store import search
from config.config import GEMINI_API_KEY

client=genai.Client(api_key=GEMINI_API_KEY)

def ask_gemini(query):
    result=search(query,k=3)
    chunks = [chunk["chunk"]["text"] for chunk in result]
    context="\n----\n".join(chunks)
    full_prompt=f"""
            You are a financial analyst.

            Answer  using ONLY the supplied context.

            If the answer is not present in the context, say:
            "I couldn't find that information in the report."

            Be concise.

            Use bullet points where appropriate.

            Do not make assumptions.

            Context:
            {context}

            Question:
            {query}

            Answer:
            """
    response=client.models.generate_content(
        model="gemini-2.5-flash",
        contents=full_prompt
    )
    sources=[
        f"Pages {item["chunk"]['start_page']}-{item['chunk']['end_page'] }"for item in result
    ]
    return response.text,sources


    
