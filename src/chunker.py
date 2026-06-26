import re
import json

chunk=[]
current_page=0
with open("C:/Users/hp/Desktop/Projects/financial-report-analyzer/data/processed/apple_2024.txt","r", encoding="utf-8") as f:
    for line in f:
        if line.startswith("== PAGE"):
            page=line.split()
            current_page=int(page[2])
            continue
        if line.strip():
            sentances=re.split(r'(?<=[.!?])\s+',line.strip())
            for sentance in sentances:
                if sentance.strip():
                 chunk.append([current_page,sentance])


final_chunks=[]
chunk_id=0
current_bucket=[]
current_word_count=0
chunk_start_page=None
chunk_end_page = None

for page_num,sentance_text in chunk:
    words=len(sentance_text.split())
    if current_word_count+words>250:
        chunk_id+=1
        final_chunks.append({
                    "chunk_id": chunk_id,
                    "start_page": chunk_start_page,
                    "end_page": chunk_end_page,
                    "word_count": current_word_count,
                    "text": " ".join(current_bucket)
                })
        current_bucket=[]
        current_word_count=0
        chunk_start_page=None
        chunk_end_page = None

    if chunk_start_page is None:
        chunk_start_page = page_num
    
    current_bucket.append(sentance_text)
    current_word_count+=words
    chunk_end_page = page_num
    

if current_bucket:
    chunk_id+=1
    final_chunks.append({
    "chunk_id": chunk_id,
    "start_page": chunk_start_page,
    "end_page": chunk_end_page,
    "word_count": current_word_count,
    "text": " ".join(current_bucket)
})
    

with open("C:/Users/hp/Desktop/Projects/financial-report-analyzer/data/processed/apple_2024_chunks.json","w", encoding="utf-8") as f:
    json.dump(final_chunks,f,indent=4)
