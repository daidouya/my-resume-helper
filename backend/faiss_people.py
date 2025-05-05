from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain.schema import Document
import os

example_resumes = [
    {
        "user_id": "alice",
        "summary": "Software engineer with experience in backend development, Python, and AWS. Worked at Amazon and built scalable APIs."
    },
    {
        "user_id": "bob",
        "summary": "Data scientist with a focus on NLP, Python, and deep learning. Interned at Google and published in ICML."
    },
    {
        "user_id": "charlie",
        "summary": "Frontend developer with React, TypeScript, and UX design experience. Built web apps for e-commerce startups."
    },
    {
        "user_id": "dana",
        "summary": "AI researcher with robotics and reinforcement learning background. PhD in Computer Science from Stanford."
    }
]

def build_resume_vectorstore(index_path="backend/faiss_index_people"):
    embedding_model = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")

    documents = [
        Document(page_content=entry["summary"], metadata={"user_id": entry["user_id"]})
        for entry in example_resumes
    ]

    vectorstore = FAISS.from_documents(documents, embedding_model)
    vectorstore.save_local(index_path)
    return vectorstore

people_vectorstore_path = "backend/faiss_index_people"
embedding_model = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")

# Check if FAISS index exists
def faiss_index_exists(path):
    return os.path.exists(os.path.join(path, "index.faiss")) and os.path.exists(os.path.join(path, "index.pkl"))

# Load or build
if faiss_index_exists(people_vectorstore_path):
    people_vectorstore = FAISS.load_local(people_vectorstore_path, 
                                          embeddings=embedding_model,
                                          allow_dangerous_deserialization=True)
else:
    people_vectorstore = build_resume_vectorstore(index_path=people_vectorstore_path)