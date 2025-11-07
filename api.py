import os
import ssl
import httpx
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

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

app = FastAPI()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # React dev server default port
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ===== Models =====
class ChatRequest(BaseModel):
    message: str

# ===== UTILS =====
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

Goals:
1. Assess the likely urgency of the patient's condition.
2. Provide a clear triage recommendation (Emergency, Urgent Care, Primary Care, or Self-Care).
3. Offer a short, patient-friendly explanation.

Context: {context}
Question: {question}

Please provide:
1) Your assessment of the situation
2) Your triage recommendation
3) A brief explanation of your reasoning
"""
    return PromptTemplate(template=custom_prompt, input_variables=["context", "question"])

# Initialize QA chain
vectorstore = get_vectorstore()
llm = ChatOpenAI(
    model="azure/genailab-maas-gpt-35-turbo",
    temperature=0,
    openai_api_key=OPENAI_API_KEY,
    base_url=BASE_URL,
    http_client=http_client,
)

qa_chain = RetrievalQA.from_chain_type(
    llm=llm,
    chain_type="stuff",
    retriever=vectorstore.as_retriever(search_kwargs={"k": 3}),
    return_source_documents=True,
    chain_type_kwargs={"prompt": set_custom_prompt()},
)

# ===== API Endpoints =====
@app.post("/api/chat")
async def chat(request: ChatRequest):
    try:
        result = qa_chain(request.message)
        return {
            "answer": result["result"],
            "source_documents": [
                {"page_content": doc.page_content, "metadata": doc.metadata}
                for doc in result["source_documents"]
            ]
        }
    except Exception as e:
        return {"error": str(e)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)