import os
from pathlib import Path
import subprocess
from langchain_ollama import OllamaLLM
from langchain_core.prompts import ChatPromptTemplate
import PyPDF2


# Function to get the list of files in a directory
def get_file_objects_in_directory(directory_path):
    path = Path(directory_path)
    return [file for file in path.iterdir() if file.is_file()]

# Function to extract text from PDF using PyPDF2
def pdf_to_text(pdf_path):
    print("\nExtracting text...")
    try:
        with open(pdf_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            text = ''
            for page_num in range(len(pdf_reader.pages)):
                page = pdf_reader.pages[page_num]
                text += page.extract_text()
            return text
    except Exception as e:
        return f"An error occurred: {e}"

# Function to process text via LLaMA model using Ollama
def enhance_text_with_llama(text):
    print("\nEnhancing text...")
    print("Text len: ", len(text))
    end = min(len(text), 6000)
    start = 0
    history = "*NO HISTORY*"
    output = ""
    while start != end:
        chunk = text[start:end:]
        print(f"Processing {end-start}x2 characters")
        try:
            
            template = """        
            Please correct the following text by fixing any spelling, grammar, punctuation, or missing words. Do not change the meaning or structure of the sentences. Ensure that the text is accurate and properly written.
            
            DO NOT hallucinate facts or cite laws unless they are explicitly present in the context.

            IGNORE any text enclosed in *
            
            Here is the previous chunk of the text for context: {context}
            
            This is the text to be corrected: {text}
            
            Return only the corrected version of the text. Do not include any explanations, just the text with all errors corrected.
            
            Answer: 
            """
            
            model = OllamaLLM(model="llama3")

            prompt = ChatPromptTemplate.from_template(template)
            
            chain = prompt | model
            
            result = chain.invoke({"context":history, "text":chunk})

            output += result.strip()
            
            history = chunk
            start = end
            end = min(len(text), end+6000)
            
        except Exception as e:
            return f"An error occurred while processing with Ollama: {e}"
    
    return output


# Main processing function
def process_pdf_and_save_text(source_dir, dest_dir):
    try:
        dest_dir = Path(dest_dir)
        source_dir = Path(source_dir)
        dest_dir.mkdir(parents=True, exist_ok=True)

        for file in get_file_objects_in_directory(source_dir):
            # Get the full path of the PDF file
            pdf_path = os.path.abspath(file)
            
            # Extract text from PDF
            extracted_text = pdf_to_text(pdf_path)
            if not extracted_text:
                print(f"Skipping {file.name} due to empty content.")
                continue
            
            # Enhance the extracted text using the local LLaMA model via Ollama
            final_text = enhance_text_with_llama(extracted_text)
            
            # Create destination file path (change extension to .txt)
            dest_file = dest_dir / file.with_suffix(".txt").name
            
            with open(dest_file, "w", encoding="utf-8") as f:
                f.write(final_text)

            print(f"Processed {file.name} and saved to {dest_file}")
    except Exception as e:
        print("Error:", e)
        
source_dir = "../static/docs/acts"
dest_dir = "../static/docs/text"
process_pdf_and_save_text(source_dir, dest_dir)
