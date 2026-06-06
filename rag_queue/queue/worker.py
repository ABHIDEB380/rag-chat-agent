from openai import OpenAI
import dotenv
import os


from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_qdrant import QdrantVectorStore
from qdrant_client import QdrantClient

dotenv.load_dotenv()

client = OpenAI(
api_key= os.getenv("GEMINI_API_KEY"),
base_url="https://generativelanguage.googleapis.com/v1beta/openai/"
)

embeddings = GoogleGenerativeAIEmbeddings(
    model="models/gemini-embedding-2",
    )

q_client = QdrantClient(url="http://localhost:6333/")

vector_store = QdrantVectorStore.from_existing_collection(
    url="http://localhost:6333/",
    collection_name="demo_collection",
    embedding=embeddings,
)

def process_query(user_input:str):
    results = vector_store.similarity_search(
        user_input, k=2
    )

    SYSTEM_PROMPT = f"""
    You are an helpfull AI assistent who works only on Natual Disaster.
    If user asks anything not related to "Natual Disaster" you should prompt explicitly "Please ask questions only related to Natual Disaster."
    Your only source of information is avilable on {results} variable you should get the data from here before anserwing user query.
    You have to provide the resulted details as well like below in JSON format:
    User Question: "What is natual disaster?"

    Output: "<Explaination on Natual Disaster>",
    page: <Page number from the document>


    """
    response = client.chat.completions.create(
        model="gemini-3.5-flash",
        messages=[
            {
                "role": "system",
                "content": SYSTEM_PROMPT,
            },
            {
                "role": "user",
                "content": user_input,
            },
        ]
    )

    print(f"AI: {response.choices[0].message.content}")
    return response.choices[0].message.content
