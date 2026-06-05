import os
import fitz  # PyMuPDF
import pytesseract
from PIL import Image
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from dotenv import load_dotenv
import io

load_dotenv()

CHROMA_PATH = "./chroma_db"
PDF_FOLDER = "./pdfs"  # Put your textbook PDFs here


def extract_text_from_pdf(pdf_path: str) -> str:
    """
    Extracts text from PDF.
    Falls back to OCR for scanned pages automatically.
    """
    doc = fitz.open(pdf_path)
    all_text = []

    print(f"Processing: {pdf_path} ({len(doc)} pages)")

    for page_num, page in enumerate(doc):
        # Try direct text extraction first
        text = page.get_text("text")

        if len(text.strip()) < 50:
            # Page is likely scanned — use OCR
            print(f"  Page {page_num + 1}: Scanned, using OCR...")
            pix = page.get_pixmap(dpi=300)
            img_bytes = pix.tobytes("png")
            img = Image.open(io.BytesIO(img_bytes))
            text = pytesseract.image_to_string(img, lang="eng")
        else:
            print(f"  Page {page_num + 1}: Text extracted directly")

        # Add page metadata to text
        all_text.append(f"[Page {page_num + 1}]\n{text}\n")

    doc.close()
    return "\n".join(all_text)


def chunk_text(text: str, source_name: str) -> list:
    """
    Splits text into overlapping chunks.
    Medical content is dense — keep chunks smaller with more overlap.
    """
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=600,       # ~400–600 tokens is sweet spot for medical text
        chunk_overlap=120,    # Overlap ensures context isn't cut mid-topic
        separators=["\n\n", "\n", ". ", "! ", "? ", " ", ""],
        length_function=len,
    )
    chunks = splitter.create_documents(
        texts=[text],
        metadatas=[{"source": source_name}]
    )
    print(f"  Created {len(chunks)} chunks from {source_name}")
    return chunks


def ingest_all_pdfs():
    """
    Main function: reads all PDFs, embeds, stores in ChromaDB.
    Run once, then reuse the database.
    """
    if not os.path.exists(PDF_FOLDER):
        os.makedirs(PDF_FOLDER)
        print(f"Created {PDF_FOLDER}/ folder. Add your PDF textbooks there and re-run.")
        return

    pdf_files = [f for f in os.listdir(PDF_FOLDER) if f.endswith(".pdf")]

    if not pdf_files:
        print(f"No PDFs found in {PDF_FOLDER}/")
        return

    all_chunks = []

    for pdf_file in pdf_files:
        pdf_path = os.path.join(PDF_FOLDER, pdf_file)
        print(f"\n{'='*50}")
        print(f"Ingesting: {pdf_file}")
        print(f"{'='*50}")

        raw_text = extract_text_from_pdf(pdf_path)
        chunks = chunk_text(raw_text, source_name=pdf_file)
        all_chunks.extend(chunks)

    print(f"\nTotal chunks to embed: {len(all_chunks)}")
    print("Embedding... (this takes time + costs money, do it once)")

    embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

    # Store in Chroma — creates local folder
    vectorstore = Chroma.from_documents(
        documents=all_chunks,
        embedding=embeddings,
        persist_directory=CHROMA_PATH,
    )

    print(f"\nDone! Vector DB saved to {CHROMA_PATH}/")
    print(f"Total documents stored: {vectorstore._collection.count()}")


if __name__ == "__main__":
    ingest_all_pdfs()
