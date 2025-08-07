# utils/rag_engine.py
import os
import fitz  # PyMuPDF
import pytesseract
from PIL import Image
import io
from sentence_transformers import SentenceTransformer
import faiss
import numpy as np
import pickle
import json
from pymongo import MongoClient

pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"


# ---- CONFIG ----
DOCS_DIR = "static/docs"
INDEX_DIR = "embeddings/faiss_index"
CHUNK_SIZE = 500
CHUNK_OVERLAP = 100
MODEL_NAME = "all-MiniLM-L6-v2"

# ---- INITIALIZE ----
model = SentenceTransformer(MODEL_NAME)

EMBEDDING_DIM = model.get_sentence_embedding_dimension()
INDEX_TRACK_FILE = os.path.join(INDEX_DIR, "index_log.json")

index = faiss.IndexFlatL2(EMBEDDING_DIM)
corpus_chunks = []  

def load_index_log():
    try:
        if os.path.exists(INDEX_TRACK_FILE):
            with open(INDEX_TRACK_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        return {"indexed": [], "unindexed": []}
    except Exception as e:
        return {"indexed": [], "unindexed": []}


def save_index_log(log):
    with open(INDEX_TRACK_FILE, "w", encoding="utf-8") as f:
        json.dump(log, f, indent=4)


def detect_new_files(index_log):
    all_files = [f for f in os.listdir(DOCS_DIR) if f.endswith(".txt") or f.endswith(".pdf")]
    known_files = set(index_log["indexed"]) | set(index_log["unindexed"])
    new_files = [f for f in all_files if f not in known_files]
    index_log["unindexed"].extend(new_files)


def extract_text_from_pdf(path):
    text = ""
    doc = fitz.open(path)
    for page in doc:
        page_text = page.get_text()
        if len(page_text.strip()) > 50:
            text += page_text
        else:
            # Fallback to OCR ( non-text content )
            pix = page.get_pixmap(dpi=300)
            img = Image.open(io.BytesIO(pix.tobytes("png")))
            text += pytesseract.image_to_string(img)
    return text

def chunk_text(text, size=CHUNK_SIZE, overlap=CHUNK_OVERLAP):
    words = text.split()
    chunks = []
    for i in range(0, len(words), size - overlap):
        chunk = " ".join(words[i:i + size])
        chunks.append(chunk)
    return chunks

def embed_chunks(chunks):
    result = model.encode(chunks, convert_to_numpy=True)
    return result

def build_index(index_log):
    global corpus_chunks, index
    all_embeddings = []
    corpus_chunks = []


    for filename in index_log["unindexed"]:
        path = os.path.join(DOCS_DIR, filename)
        if filename.endswith(".txt"):
            with open(path, 'r', encoding='utf-8') as f:
                text = f.read()
        else:
            text = extract_text_from_pdf(path)

        chunks = chunk_text(text)
        corpus_chunks.extend(chunks)
        chunk_embeddings = embed_chunks(chunks) 
        all_embeddings.append(chunk_embeddings)
        index_log["indexed"].append(filename)

    index_log["unindexed"] = []  # clear after processing
    if all_embeddings:
        full_embeddings = np.vstack(all_embeddings).astype(np.float32)
        index.add(full_embeddings)
        save_index_log(index_log)
        save_index()
    return index_log



def save_index():
    if not os.path.exists(INDEX_DIR):
        os.makedirs(INDEX_DIR)
    faiss.write_index(index, os.path.join(INDEX_DIR, "legal_index.faiss"))
    with open(os.path.join(INDEX_DIR, "chunks.pkl"), "wb") as f:
        pickle.dump(corpus_chunks, f)

def load_index():
    global corpus_chunks, index
    index_path = os.path.join(INDEX_DIR, "legal_index.faiss")
    chunks_path = os.path.join(INDEX_DIR, "chunks.pkl")

    index_log = load_index_log()
    
    detect_new_files(index_log)

    if index_log["unindexed"]:
        index_log = build_index(index_log)
    else:
        index = faiss.read_index(index_path)
            
        with open(chunks_path, "rb") as f:
            corpus_chunks = pickle.load(f)



def get_relevant_chunks(query, top_k=5):
    load_index()
    query_embedding = model.encode([query], convert_to_numpy=True)
    print(index.ntotal)
    D, I = index.search(query_embedding, top_k)
    return [corpus_chunks[i] for i in I[0]]

def get_relevant_history_chunks(query, chat):
    chunks = chat["history_chunks"]
    embeddings = np.array(chat["history_embeddings"]).astype(np.float32)

    temp_index = faiss.IndexFlatL2(embeddings.shape[1])
    temp_index.add(embeddings)

    query_vec = model.encode([query], convert_to_numpy=True)

    D, I = temp_index.search(query_vec, 3)
    return [chunks[i] for i in I[0]]


def update_indexing(chatID, chats, update):
    chat = chats.find_one({"_id": chatID})
    
    chunks = chat.get("history_chunks", [])
    embeddings = chat.get("history_embeddings", [])

    new_chunks = chunk_text(update, size=CHUNK_SIZE, overlap=CHUNK_OVERLAP)
    chunks += new_chunks

    new_embeddings = embed_chunks(new_chunks)
    embeddings += new_embeddings.tolist()  # convert numpy to regular list

    result = chats.update_one(
        {"_id": chatID},
        {
            "$set": {
                "history_chunks": chunks,
                "history_embeddings": embeddings
            }
        }
    )

    return result.modified_count > 0


    