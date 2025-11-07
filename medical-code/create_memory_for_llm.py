import os
import ssl
import httpx
from langchain_community.document_loaders import PyPDFLoader, DirectoryLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_community.vectorstores import FAISS

# -------------------------------
# 0️⃣ SSL + API Setup
# -------------------------------
ssl._create_default_https_context = ssl._create_unverified_context
os.environ["OPENAI_API_KEY"] = "sk-RjlpxvtRwxM6-Z-XNJ5t4g"

# custom httpx client with SSL disabled
http_client = httpx.Client(verify=False)

# -------------------------------
# 1️⃣ Load PDFs
# -------------------------------
DATA_PATH = "data/"

def load_pdf_files(data_path):
    loader = DirectoryLoader(data_path, glob="*.pdf", loader_cls=PyPDFLoader)
    return loader.load()

documents = load_pdf_files(DATA_PATH)
print("✅ PDF pages loaded:", len(documents))

# -------------------------------
# 2️⃣ Split into chunks
# -------------------------------
text_splitter = RecursiveCharacterTextSplitter(chunk_size=800, chunk_overlap=100)
text_chunks = text_splitter.split_documents(documents)
print("✅ Text chunks created:", len(text_chunks))

# -------------------------------
# 3️⃣ Create Embeddings (GenAI Lab)
# -------------------------------
embedding_model = OpenAIEmbeddings(
    model="azure/genailab-maas-text-embedding-3-large",
    api_key=os.environ["OPENAI_API_KEY"],
    base_url="https://genailab.tcs.in",
    http_client=http_client,   # ✅ correct param name
)

# -------------------------------
# 4️⃣ Store embeddings in FAISS
# -------------------------------
DB_FAISS_PATH = "vectorstore/db_faiss"
db = FAISS.from_documents(text_chunks, embedding_model)
db.save_local(DB_FAISS_PATH)

print("✅ Embeddings created and saved successfully at:", DB_FAISS_PATH)

# -------------------------------
# 5️⃣ Test LLM Connection
# -------------------------------
llm = ChatOpenAI(
    base_url="https://genailab.tcs.in",
    model="azure/genailab-maas-gpt-4o",
    api_key=os.environ["OPENAI_API_KEY"],
    http_client=http_client
)

response = llm.invoke("Embeddings created successfully using azure/genailab-maas-text-embedding-3-large.")
print("💬 LLM Test Response:", response)
