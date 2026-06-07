import streamlit as st
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from v1_qa.retriever import build_qa_chain, ask_question

# Page config
st.set_page_config(
    page_title="MedAI - Textbook Q&A",
    page_icon="🩺",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS for Modern UI
st.markdown("""
<style>
    /* Header Gradient Text */
    .gradient-text {
        background: -webkit-linear-gradient(45deg, #6366f1, #a855f7, #ec4899);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 3.5em;
        font-weight: 800;
        margin-bottom: 0px;
        padding-bottom: 0px;
    }
    .sub-text {
        color: #94a3b8;
        font-size: 1.2em;
        margin-top: -10px;
        margin-bottom: 30px;
    }
    
    /* Hide top header and footer */
    header {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* Chat bubbles styling */
    .stChatMessage {
        background-color: #1e293b !important;
        border-radius: 20px;
        padding: 20px;
        border: 1px solid #334155;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
        margin-bottom: 15px;
    }
    
    /* Input box styling */
    .stChatInputContainer {
        border-radius: 25px !important;
        border: 1px solid #6366f1 !important;
        box-shadow: 0 10px 15px -3px rgba(99, 102, 241, 0.2) !important;
    }
</style>
""", unsafe_allow_html=True)

st.markdown('<h1 class="gradient-text">🩺 MedAI</h1>', unsafe_allow_html=True)
st.markdown('<p class="sub-text">Intelligent Q&A powered by your MBBS textbooks</p>', unsafe_allow_html=True)

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
