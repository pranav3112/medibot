import os
import ssl
import httpx
from langchain_community.vectorstores import FAISS
from langchain_core.prompts import PromptTemplate
from langchain.chains import RetrievalQA
from langchain_openai import ChatOpenAI, OpenAIEmbeddings

# -------------------------------
# 0️⃣ SSL + API Setup
# -------------------------------
ssl._create_default_https_context = ssl._create_unverified_context
os.environ["OPENAI_API_KEY"] = "sk-RjlpxvtRwxM6-Z-XNJ5t4g"   # 🔒 your API key

# disable SSL verification for GenAI Lab endpoint
http_client = httpx.Client(verify=False)

# -------------------------------
# 1️⃣ Custom Prompt Template
# -------------------------------
CUSTOM_PROMPT_TEMPLATE = """
You are a medical triage assistant designed to help patients understand the severity of their symptoms and decide whether to seek immediate care or manage their condition at home.

Your responses must be based ONLY on the information provided in the context. 
Do NOT use outside medical knowledge, and do NOT make assumptions beyond what’s in the context.

Your goals:
1. Assess the likely urgency of the patient's condition.
2. Provide a clear triage recommendation (e.g., Emergency, Urgent Care, Primary Care, or Self-Care).
3. Offer a short, compassionate explanation in plain English.
4. Suggest safe and actionable next steps for the patient.

If the context does not contain enough information, say so clearly and request clarification — do not invent or guess.

---

Context:
{context}

Question:
{question}

---

Respond in the following structured format:

HUMAN_SUMMARY:
A short, patient-friendly explanation that includes the triage level and key reasoning.

JSON:
{{
  "triage_level": "Emergency | Urgent | Primary care | Self-care | Unclear",
  "explanation": "Brief reason for this triage level based only on the provided context.",
  "immediate_red_flags": ["list of red-flag symptoms if present, else empty list"],
  "recommended_action": "Emergency Department / Urgent Care / Primary Care / Self-care at home / Need more details",
  "recommended_timeline": "immediate | within 24 hours | within 48 hours | within 7 days | routine follow-up | unclear",
  "suggested_next_steps": ["list of 2–5 short actionable recommendations for the patient"],
  "home_care_advice": ["brief self-care guidance if appropriate, otherwise empty"],
  "confidence": "low | moderate | high",
  "notes": "add any missing information or assumptions that limit confidence"
}}

Guidelines:
- Be concise and clinically cautious.
- If any red flag symptoms are mentioned, choose "Emergency".
- If symptoms are moderate or worsening, choose "Urgent" or "Primary care soon".
- If mild or self-limiting symptoms are described, choose "Self-care".
- If context is missing, respond with "Unclear" and briefly state what information is needed.
- Never prescribe medication or dosages.

Start directly with the HUMAN_SUMMARY.
"""

def set_custom_prompt(custom_prompt_template):
    return PromptTemplate(template=custom_prompt_template, input_variables=["context", "question"])

# -------------------------------
# 2️⃣ Load Embeddings (GenAI Lab OpenAI)
# -------------------------------
embedding_model = OpenAIEmbeddings(
    model="azure/genailab-maas-text-embedding-3-large",
    api_key=os.environ["OPENAI_API_KEY"],
    base_url="https://genailab.tcs.in",
    http_client=http_client
)

# -------------------------------
# 3️⃣ Load FAISS Vectorstore
# -------------------------------
DB_FAISS_PATH = "vectorstore/db_faiss"
db = FAISS.load_local(DB_FAISS_PATH, embedding_model, allow_dangerous_deserialization=True)
print(f"✅ FAISS vector database loaded from: {DB_FAISS_PATH}")

# -------------------------------
# 4️⃣ Load LLM (ChatGPT / GPT-4o)
# -------------------------------
llm = ChatOpenAI(
    base_url="https://genailab.tcs.in",
    model="azure/genailab-maas-gpt-4o",   # 🔁 OpenAI's GPT-4o (Mistral alternative)
    api_key=os.environ["OPENAI_API_KEY"],
    temperature=0.3,
    http_client=http_client
)

# -------------------------------
# 5️⃣ Build Retrieval QA Chain
# -------------------------------
qa_chain = RetrievalQA.from_chain_type(
    llm=llm,
    chain_type="stuff",
    retriever=db.as_retriever(search_kwargs={'k': 5}),
    return_source_documents=True,
    chain_type_kwargs={'prompt': set_custom_prompt(CUSTOM_PROMPT_TEMPLATE)}
)

# -------------------------------
# 6️⃣ Ask Query
# -------------------------------
user_query = input("💬 Enter your question: ")
response = qa_chain.invoke({'query': user_query})

print("\n✅ RESULT:\n", response["result"])
print("\n📄 SOURCE DOCUMENTS:")
for i, doc in enumerate(response["source_documents"], 1):
    print(f"--- Source {i} ---\n{doc.metadata}\n")
