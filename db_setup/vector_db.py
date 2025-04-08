import chromadb
from sentence_transformers import SentenceTransformer
from typing import List, Dict

class VectorDB:
    def __init__(self, collection_name: str = 'doc_embeddings', model_name: str = 'all-MiniLM-L6-v2'):
        self.client = chromadb.Client()
        self.collection = self.client.get_or_create_collection(collection_name)
        self.model = SentenceTransformer(model_name)

    def add_documents(self, docs: List[str], ids: List[str]):
        embeddings = self.model.encode(docs).tolist()
        self.collection.add(documents=docs, embeddings=embeddings, ids=ids)

    def query(self, query_text: str, n_results: int = 2) -> Dict:
        query_embedding = self.model.encode([query_text]).tolist()
        return self.collection.query(query_embeddings=query_embedding, n_results=n_results)

    def get_embeddings(self, ids: List[str]) -> List[List[float]]:
        data = self.collection.get(ids=ids, include=['embeddings'])
        return data['embeddings']

    def count_documents(self) -> int:
        return self.collection.count()

    def get_all_ids(self) -> List[str]:
        data = self.collection.get(include=[])
        return data['ids']