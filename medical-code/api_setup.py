from langchain_openai import ChatOpenAI
import httpx

client = httpx.Client(verify=False)
llm = ChatOpenAI (
    base_url= "https://genailab.tcs.in",
    model= "azure/genailab-maas-gpt-4o",
    api_key= "sk-RjlpxvtRwxM6-Z-XNJ5t4g",
    http_client = client
)

response =llm.invoke("hello")
print(response)