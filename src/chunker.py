import re
import json
from config.config import PROCESSED_DIR

def text_to_chunks(txt_path,chunk_json_path):
    try:
        chunk = []
        current_page = 0
        
        with open(PROCESSED_DIR /txt_path, "r", encoding="utf-8") as f:
            for line in f:
                if line.startswith("== PAGE"):
                    page = line.split()
                    current_page = int(page[2])
                    continue
                if line.strip():
                    sentences = re.split(r'(?<=[.!?])\s+', line.strip())
                    for sentence in sentences:
                        if sentence.strip():
                            chunk.append([current_page, sentence])

        final_chunks = []
        chunk_id = 0
        current_bucket = []
        current_word_count = 0
        chunk_start_page = None
        chunk_end_page = None

        for page_num, sentence_text in chunk:
            words = len(sentence_text.split())
            if current_word_count + words > 400:
                chunk_id += 1
                final_chunks.append({
                    "chunk_id": chunk_id,
                    "start_page": chunk_start_page,
                    "end_page": chunk_end_page,
                    "word_count": current_word_count,
                    "text": " ".join(current_bucket)
                })
                current_bucket = []
                current_word_count = 0
                chunk_start_page = None
                chunk_end_page = None

            if chunk_start_page is None:
                chunk_start_page = page_num

            current_bucket.append(sentence_text)
            current_word_count += words
            chunk_end_page = page_num

        if current_bucket:
            chunk_id += 1
            final_chunks.append({
                "chunk_id": chunk_id,
                "start_page": chunk_start_page,
                "end_page": chunk_end_page,
                "word_count": current_word_count,
                "text": " ".join(current_bucket)
            })

        with open(PROCESSED_DIR /chunk_json_path, "w", encoding="utf-8") as f:
            json.dump(final_chunks, f, indent=4)
            
        print(f"Successfully processed {len(final_chunks)} chunks")
        return final_chunks
        
    except FileNotFoundError as e:
        print(f"Error: File not found - {e}")
        raise
    except Exception as e:
        print(f"Error processing financial report: {e}")
        raise


