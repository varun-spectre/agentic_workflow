import os
import json
from typing import List, Dict, Any
from qdrant_client import QdrantClient
from qdrant_client.models import VectorParams, Distance, PointStruct
from sentence_transformers import SentenceTransformer

# Load Qdrant credentials from keys.json (assumes file is one level up from this script)
key_path = os.path.join(os.path.dirname(__file__), '..', 'keys.json')
with open(key_path, 'r') as f:
    config = json.load(f)
qdrant_cfg = config["qdrant"]


class VectorDB:
    def __init__(self, collection_name: str = 'doc_embeddings', model_name: str = 'all-MiniLM-L6-v2'):
        self.client = QdrantClient(url=qdrant_cfg["url"], api_key=qdrant_cfg["api_key"])
        self.collection_name = collection_name
        self.model = SentenceTransformer(model_name)

        # Ensure collection exists
        self.client.recreate_collection(
            collection_name=self.collection_name,
            vectors_config=VectorParams(size=self.model.get_sentence_embedding_dimension(), distance=Distance.COSINE)
        )

    def add_documents(self, docs: List[str], ids: List[str], metadata: List[Dict[str, Any]] = None):
        vectors = self.model.encode(docs).tolist()
        payloads = metadata if metadata else [{} for _ in docs]
        points = [PointStruct(id=ids[i], vector=vectors[i], payload=payloads[i]) for i in range(len(docs))]
        self.client.upsert(collection_name=self.collection_name, points=points)

    def query(self, query_text: str, n_results: int = 2) -> List[Dict]:
        query_vector = self.model.encode([query_text])[0].tolist()
        results = self.client.search(
            collection_name=self.collection_name,
            query_vector=query_vector,
            limit=n_results
        )
        return [{"id": res.id, "score": res.score, "payload": res.payload} for res in results]

    def count_documents(self) -> int:
        return self.client.count(self.collection_name).count

    def get_all_ids(self) -> List[str]:
        points = self.client.scroll(self.collection_name, limit=10000, with_payload=False)
        return [point.id for point in points[0]]
