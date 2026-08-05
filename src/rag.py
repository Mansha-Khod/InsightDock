from google import genai
from src.vector_store import search
from config.config import GEMINI_API_KEY

client=genai.Client(api_key=GEMINI_API_KEY)

def ask_gemini(query,index_path,chunk_json_path):
    result=search(query,index_path,chunk_json_path,k=3)
    chunks = [chunk["chunk"]["text"] for chunk in result]
    context="\n----\n".join(chunks)
    full_prompt=f"""
            You are an intelligent document assistant.

            You answer questions using ONLY the information contained in the provided document excerpts.

            Instructions:

            - Base every answer strictly on the supplied context.
            - Do not use outside knowledge.
            - If the answer is not present in the context, respond:
            "I couldn't find that information in the document."
            - Be concise and well structured.
            - Use bullet points whenever appropriate.
            - Do not speculate or make assumptions.
            - Preserve important numbers, dates, names, and terminology exactly as written.
            - If multiple retrieved passages provide relevant information, combine them into a single coherent answer.

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
    sources = []

    for item in result:
        sources.append(
            {
                "pages": f"{item['chunk']['start_page']}-{item['chunk']['end_page']}",
                "distance": round(item["distance"], 4),
                "preview": item["chunk"]["text"][:250] + "..."
            }
        )
    return response.text,sources

from src.vector_store import search_multi

def ask_gemini_multi(query, docs, k=3, mode="semantic"):
    result = search_multi(query, docs, k=k)

    chunks = [item["chunk"]["text"] for item in result]
    context = "\n----\n".join(chunks)

    full_prompt = f"""
            You are an intelligent document assistant.

            You answer questions using ONLY the information contained in the provided document excerpts.
            These excerpts may come from multiple different documents.

            Instructions:

            - Base every answer strictly on the supplied context.
            - Do not use outside knowledge.
            - If the answer is not present in the context, respond:
            "I couldn't find that information in the document."
            - Be concise and well structured.
            - Use bullet points whenever appropriate.
            - Do not speculate or make assumptions.
            - Preserve important numbers, dates, names, and terminology exactly as written.
            - If excerpts come from different documents, make clear which document each point relates to.

            Context:
            {context}

            Question:
            {query}

            Answer:
            """

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=full_prompt
    )

    sources = []
    for item in result:
        sources.append({
            "filename": item.get("source_filename"),
            "pages": f"{item['chunk']['start_page']}-{item['chunk']['end_page']}",
            "distance": round(item["distance"], 4),
            "preview": item["chunk"]["text"][:250] + "...",
        })

    return response.text, sources

    
