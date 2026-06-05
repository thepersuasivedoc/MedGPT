from langchain_huggingface import HuggingFaceEmbeddings
from langchain_ollama import ChatOllama
from langchain_community.vectorstores import Chroma
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate
from dotenv import load_dotenv

load_dotenv()

CHROMA_PATH = "./chroma_db"

MEDICAL_QA_PROMPT = PromptTemplate(
    input_variables=["context", "question"],
    template="""
You are a medical education assistant helping an MBBS student understand concepts from their textbooks.

RULES:
- Answer ONLY from the provided context
- If the answer is not in the context, say "This specific information is not in your uploaded textbooks"
- Include the page number or source when possible
- Be concise but complete
- For drug dosages or critical clinical info, always add: "Verify this in your official textbook before clinical use"

CONTEXT FROM TEXTBOOKS:
{context}

STUDENT QUESTION:
{question}

ANSWER:
"""
)


def build_qa_chain():
    """Build the RAG chain. Call once and reuse."""
    embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

    vectorstore = Chroma(
        persist_directory=CHROMA_PATH,
        embedding_function=embeddings,
    )

    retriever = vectorstore.as_retriever(
        search_type="mmr",          # MMR avoids returning duplicate chunks
        search_kwargs={
            "k": 6,                 # Retrieve 6 chunks
            "fetch_k": 20,          # Consider top 20 before diversity filtering
        }
    )

    llm = ChatOllama(
        model="llama3",             # Local, free model running via Ollama
        temperature=0,              # 0 = deterministic, critical for factual medical content
    )

    chain = RetrievalQA.from_chain_type(
        llm=llm,
        chain_type="stuff",
        retriever=retriever,
        return_source_documents=True,
        chain_type_kwargs={"prompt": MEDICAL_QA_PROMPT},
    )

    return chain


def ask_question(chain, question: str) -> dict:
    """Ask a question and return answer + sources."""
    result = chain.invoke({"query": question})

    answer = result["result"]
    sources = list(set([
        doc.metadata.get("source", "Unknown")
        for doc in result["source_documents"]
    ]))

    return {
        "answer": answer,
        "sources": sources,
        "num_chunks_used": len(result["source_documents"])
    }
