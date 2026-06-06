import streamlit as st
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from v1_qa.retriever import build_qa_chain, ask_question

# Page config
st.set_page_config(
    page_title="MedAI - Textbook Q&A",
    page_icon="🩺",
    layout="wide"
)

st.title("🩺 MedAI — Textbook Q&A")
st.caption("Ask anything from your uploaded MBBS textbooks")

# Load chain once per session
@st.cache_resource
def load_chain():
    return build_qa_chain()

# Check if DB exists
if not os.path.exists("./chroma_db"):
    st.error("⚠️ No textbook database found. Run `python v1_qa/ingest.py` first.")
    st.stop()

chain = load_chain()

# Chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat history
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])
        if msg.get("sources"):
            with st.expander("📚 Sources"):
                for src in msg["sources"]:
                    st.caption(f"• {src}")

# Input box
if question := st.chat_input("Ask a question from your textbooks..."):
    # Show user message
    with st.chat_message("user"):
        st.write(question)

    st.session_state.messages.append({"role": "user", "content": question})

    # Get answer
    with st.chat_message("assistant"):
        with st.spinner("Agent is thinking and searching..."):
            # Convert UI history to LangChain format
            chat_history = []
            for msg in st.session_state.messages[:-1]: # exclude the current question we just appended
                if msg["role"] == "user":
                    chat_history.append(("human", msg["content"]))
                elif msg["role"] == "assistant":
                    chat_history.append(("ai", msg["content"]))
                    
            result = ask_question(chain, question, chat_history)

        st.write(result["answer"])

        if result["sources"]:
            with st.expander(f"📚 Sources ({result['num_chunks_used']} chunks used)"):
                for src in result["sources"]:
                    st.caption(f"• {src}")

    st.session_state.messages.append({
        "role": "assistant",
        "content": result["answer"],
        "sources": result["sources"]
    })
