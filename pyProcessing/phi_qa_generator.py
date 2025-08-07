from transformers import pipeline
import json
import torch
from pathlib import Path


device = 0 if torch.cuda.is_available() else -1  # Use GPU if available, else CPU

qa_generator = pipeline("text2text-generation", model="microsoft/phi-2", device=device)

source_dir = Path("../static/docs/text")
dest_dir = Path("../static/docs/qa_sets")

def get_file_objects_in_directory(path):
    return [file for file in path.iterdir() if file.is_file()]

for file in get_file_objects_in_directory(source_dir):
    with open(file, "r", encoding="utf-8") as f:
        text = f.read()


    chunks = [text[i:i+500] for i in range(0, len(text), 500)]
    qa_pairs = []

    for chunk in chunks:
        prompt = f"""Given the following legal text, generate 1-2 question-answer pairs.

    Legal Text:
    \"\"\"{chunk}\"\"\"

    Output format:
    Q: ...
    A: ..."""

        response = qa_generator(prompt, max_new_tokens=256)[0]["generated_text"]
        
        i = 0
        for line in response.split("\n"):
            i += 1
            print("line: ", i)        
            if line.strip().startswith("Q:") or line.strip().startswith("A:"):
                if "Q:" in line: 
                    question = line[2:].strip()
                elif "A:" in line:
                    answer = line[2:].strip()
                    if question and answer:
                        qa_pairs.append({"question": question, "answer": answer})

    try:
        dest_file = dest_dir / file.with_suffix("_qa.json").name
        with open(dest_file, "w", encoding="utf-8") as f:
            json.dump(qa_pairs, f)
            print(f"{dest_file.name} JSON ready")
    except Exception as e:
        print("No file: ", e)
