import os
import ssl
import httpx
import streamlit as st

from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain.chains import RetrievalQA
from langchain_community.vectorstores import FAISS
from langchain_core.prompts import PromptTemplate


# ===== CONFIG =====
DB_FAISS_PATH = "vectorstore/db_faiss"

# Disable SSL verification (GenAI Lab self-signed cert fix)
ssl._create_default_https_context = ssl._create_unverified_context
http_client = httpx.Client(verify=False)

# API & Endpoint (GenAI Lab)
os.environ["OPENAI_API_KEY"] = "sk-RjlpxvtRwxM6-Z-XNJ5t4g"
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
BASE_URL = "https://genailab.tcs.in"  # ✅ GenAI Lab base endpoint


# ===== UTILS =====
@st.cache_resource
def get_vectorstore():
    """Load FAISS vector store with GenAI Lab embeddings."""
    embedding_model = OpenAIEmbeddings(
        model="azure/genailab-maas-text-embedding-3-large",
        openai_api_key=OPENAI_API_KEY,
        base_url=BASE_URL,
        http_client=http_client,
    )
    db = FAISS.load_local(DB_FAISS_PATH, embedding_model, allow_dangerous_deserialization=True)
    return db


def set_custom_prompt():
    """Set structured triage-oriented prompt."""
    custom_prompt = """
You are a medical triage assistant designed to help patients understand the severity of their symptoms and decide whether to seek immediate care or manage their condition at home.

Your responses must be based ONLY on the provided context. 
Do NOT use outside medical knowledge or make assumptions beyond the context.

Respond in this exact format:

SUMMARY:
[A clear, concise summary of the condition]

ASSESSMENT:
Triage Level: [Emergency/Urgent Care/Primary Care/Self-Care]
Severity: [High/Medium/Low]

EXPLANATION:
[Detailed explanation broken into clear points]

RECOMMENDATIONS:
1. [First recommendation]
2. [Second recommendation]
3. [Additional recommendations if needed]

RED FLAGS - Seek immediate care if:
- [List any warning signs]
- [Additional warning signs if applicable]

HOME CARE:
- [Self-care instruction]
- [Additional instructions if applicable]

TIMELINE:
[When to seek care, e.g., "Within 24 hours", "Immediately", etc.]

CONFIDENCE: [High/Medium/Low]

If the context is insufficient, ask for clarification.

---
Context:
{context}

Patient Question or Symptom Description:
{question}

---
Respond in this structured format:

HUMAN_SUMMARY:
A short, patient-friendly triage explanation.

JSON:
{{
  "triage_level": "Emergency | Urgent | Primary care | Self-care | Unclear",
  "explanation": "Reasoning for the triage level.",
  "immediate_red_flags": ["if any"],
  "recommended_action": "Emergency Department / Urgent Care / Primary Care / Self-care",
  "recommended_timeline": "immediate | within 24 hours | within 48 hours | within 7 days | routine",
  "suggested_next_steps": ["2–5 short, actionable steps"],
  "home_care_advice": ["brief self-care advice if applicable"],
  "confidence": "low | moderate | high",
  "notes": "uncertainties or missing information"
}}

Start with HUMAN_SUMMARY.
"""
    return PromptTemplate(template=custom_prompt, input_variables=["context", "question"])


# ===== MAIN APP =====
def main():
    st.title("🩺 MediTriage – AI Health Assistant")

    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Display conversation
    for message in st.session_state.messages:
        st.chat_message(message["role"]).markdown(message["content"])

    # User input
    user_query = st.chat_input("Describe your symptoms or ask a health question...")
    if not user_query:
        return

    # Display user message
    st.chat_message("user").markdown(user_query)
    st.session_state.messages.append({"role": "user", "content": user_query})

    try:
        # Load FAISS DB
        vectorstore = get_vectorstore()
        if vectorstore is None:
            st.error("Failed to load vector store.")
            return

        # Build QA chain using GenAI Lab LLM
        qa_chain = RetrievalQA.from_chain_type(
            llm=ChatOpenAI(
                model="azure/genailab-maas-gpt-4o",
                temperature=0.3,
                openai_api_key=OPENAI_API_KEY,
                base_url=BASE_URL,
                http_client=http_client,
            ),
            chain_type="stuff",
            retriever=vectorstore.as_retriever(search_kwargs={"k": 3}),
            return_source_documents=True,
            chain_type_kwargs={"prompt": set_custom_prompt()},
        )

        # Query model
  
        if "chat_history" not in st.session_state:
            st.session_state.chat_history = []

        # Build a short conversation summary for context
        history_text = "\n".join(
            [f"User: {h['user']}\nAssistant: {h['assistant']}" for h in st.session_state.chat_history[-5:]]
        )

        # Combine history with the new user query
        combined_query = f"{history_text}\nUser: {user_query}"

        # Query the model
        response = qa_chain.invoke({"query": combined_query})

        # Extract answer
        result = response["result"]
        source_docs = response["source_documents"]

        # Store this turn in history
        st.session_state.chat_history.append({"user": user_query, "assistant": result})


        response = qa_chain.invoke({"query": user_query})
        result = response["result"]
        source_docs = response["source_documents"]

        # Format response
        result_to_show = f"**AI Response:**\n{result}\n\n**Sources:** {len(source_docs)} document(s) used."
        st.chat_message("assistant").markdown(result_to_show)
        st.session_state.messages.append({"role": "assistant", "content": result_to_show})

    except Exception as e:
        st.error(f"❌ Error: {str(e)}")


if __name__ == "__main__":
    main()
